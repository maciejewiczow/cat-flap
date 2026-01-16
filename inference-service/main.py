import asyncio
from concurrent.futures import ProcessPoolExecutor
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from ultralytics import YOLO  # pyright: ignore[reportPrivateImportUsage]
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage
from shared.main_fn import worker_main

log = get_logger("inference")

model: YOLO | None = None


def init_worker():
    global model
    model = YOLO("weights_ncnn_model")
    model.predict("dummy.jpg", verbose=False)


def worker_predict(image):
    global model

    if model is None:
        log.error("Tried to use model which was not initialized")
        raise RuntimeError("Model not initialized for prediction")

    return model.predict(image)


class ModelProcessor:
    """Manages process pool with initialized workers."""

    def __init__(self):
        self.executor = ProcessPoolExecutor(max_workers=1, initializer=init_worker)

    async def predict(self, image):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, worker_predict, image)

    def shutdown(self):
        self.executor.shutdown()


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the inference service")
    processor = ModelProcessor()

    async for message in hub.receive():
        match message:
            case ImageCapturedMessage(image=image):
                log.info("Received a message, starting inference")

                results = await processor.predict(image)

                log.info("Prediction ready")

                await hub.send(
                    InferenceCompleteMessage(
                        detected_classes=[
                            (item["name"], item["confidence"])
                            for item in results[0].summary()
                        ],
                        image_with_overlays=results[0].plot(),
                        result_json=results[0].to_json(),
                    )
                )


if __name__ == "__main__":
    worker_main(log, handle_messages)
