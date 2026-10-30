import asyncio
import os

import numpy as np
from PIL import Image
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import ImageCapturedMessage, InferenceCompleteMessage
from shared.state import CatFlapStateMachine

log = get_logger("image-saver")

raw_capture_save_dir = "/data/captured"
labeled_save_dir = "/data/labeled"
results_save_dir = "/data/results"


def save_labeled_image(
    image: np.ndarray, labels: str, labels_filename: str, img_filename: str
):
    try:
        Image.fromarray(image).save(img_filename)
        log.info(f"Saved image successfully as {img_filename}")
    except Exception:
        log.exception(f"Failed to save the image as {img_filename}")

    try:
        with open(labels_filename, "w") as f:
            f.write(labels)
    except:  # noqa: E722
        log.exception("Failed to save the labels")


def save_captured_image(image: Image.Image, img_filename: str):
    try:
        image.save(img_filename)
        log.info(f"Saved image successfully as {img_filename}")
    except Exception:
        log.exception(f"Failed to save the image as {img_filename}")


async def handle_messages(hub: WorkerMessageHub, _: CatFlapStateMachine):
    log.info("Starting the image saver service")

    os.makedirs(raw_capture_save_dir, exist_ok=True)
    os.makedirs(labeled_save_dir, exist_ok=True)
    os.makedirs(results_save_dir, exist_ok=True)

    async for message in hub.receive():
        match message:
            case ImageCapturedMessage(image=image, timestamp=timestamp):
                img_filename = (
                    f"{raw_capture_save_dir}/Capture_{timestamp.isoformat()}_raw.jpeg"
                )

                log.info(f"Received an image from the camera, saving as {img_filename}")

                await asyncio.to_thread(save_captured_image, image, img_filename)

            case InferenceCompleteMessage(
                image_with_overlays=image, timestamp=timestamp, result_json=result
            ):
                base_name = f"Capture_{timestamp.isoformat()}"
                img_filename = f"{labeled_save_dir}/{base_name}_labeled.jpeg"
                labels_filename = f"{results_save_dir}/{base_name}.json"

                log.info(
                    f"Received an labeled image, saving image as {img_filename} and results as {labels_filename}"
                )

                await asyncio.to_thread(
                    save_labeled_image,
                    image,
                    result,
                    labels_filename,
                    img_filename,
                )
            case _:
                pass


if __name__ == "__main__":
    worker_main(log, handle_messages)
