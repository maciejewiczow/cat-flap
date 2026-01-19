import asyncio
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.utils.str_to_timedelta import timedelta_to_str
from ultralytics import YOLO  # pyright: ignore[reportMissingImports]
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage
from shared.main_fn import worker_main
from PIL.Image import Image

log = get_logger("inference")

model: YOLO | None = None


def init_worker():
    global model
    global log
    try:
        log.info("Initializing the model")
        model = YOLO("weights_ncnn_model")
        log.info("Initializied the model")
    except:
        log.exception("Error while trying to init the model")
        raise


def worker_predict(image: Image | None):
    global model
    global log

    if model is None:
        log.error("Tried to use model which was not initialized")
        raise RuntimeError("Model not initialized for prediction")

    try:
        if image is None:
            log.info("Warming up the worker")
            start = datetime.now()
            res = model.predict("inference-service/dummy.jpg", verbose=False)
            log.info(
                f"Warmup completed, took {timedelta_to_str(datetime.now() - start)}"
            )
            return res

        log.info("Running the inference")
        start = datetime.now()
        result = model.predict(image)
        log.info(f"Inference took {timedelta_to_str(datetime.now() - start)}")

        return result
    except:
        log.exception("An exception has occurred during warmup/prediction")
        raise


class ModelProcessor:
    """Manages process pool with initialized workers."""

    def __init__(self):
        self.executor = ProcessPoolExecutor(max_workers=1, initializer=init_worker)

    async def warmup(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, worker_predict, None)

    async def predict(self, image: Image):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, worker_predict, image)


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the inference service")
    processor = ModelProcessor()
    log.info("Model processor initialized")
    await processor.warmup()
    log.info("Model processor warmed up")

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
