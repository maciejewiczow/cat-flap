from PIL import Image
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage
from shared.main_fn import worker_main

log = get_logger("image-saver")

raw_capture_save_dir = "/data/captured"
labeled_save_dir = "/data/labeled"
results_save_dir = "/data/results"


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the image saver service")
    await hub.subscribe()

    async for message in hub.receive():
        match message:
            case ImageCapturedMessage(image=image, timestamp=timestamp):
                img_filename = (
                    f"{raw_capture_save_dir}/Capture_{timestamp.isoformat()}_raw.jpeg"
                )

                log.info(f"Received an image from the camera, saving as {img_filename}")

                try:
                    image.save(img_filename)
                    log.info("Saved image successfuly")
                except:  # noqa: E722
                    log.exception("Failed to save the captured image")

            case InferenceCompleteMessage(
                image_with_overlays=image, timestamp=timestamp, result_json=result
            ):
                base_name = f"Capture_{timestamp.isoformat()}"
                img_filename = f"{labeled_save_dir}/{base_name}_labeled.jpeg"
                lables_filename = f"{results_save_dir}/{base_name}.json"

                log.info(
                    f"Received an labeled image, saving image as {img_filename} and results as {lables_filename}"
                )

                try:
                    with open(lables_filename, "w") as f:
                        f.write(result)
                except:  # noqa: E722
                    log.exception("Failed to save the labels")

                try:
                    Image.fromarray(image).save(img_filename)
                    log.info("Saved image successfuly")
                except:  # noqa: E722
                    log.exception("Failed to save the labeled image")


if __name__ == "__main__":
    worker_main(log, handle_messages)
