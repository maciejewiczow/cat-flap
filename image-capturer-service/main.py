import asyncio
from os import environ
from shared.hub import WorkerMessageHub
from shared.logging import get_logger
from shared.main_fn import worker_main
from shared.messages import ImageCapturedMessage, StartCaptureMessage
import picamera  # pyright: ignore[reportMissingImports]
import numpy as np
from PIL import Image

log = get_logger("image-capturer-service")

camera_res = (
    int(environ.get("CAMERA_RESOLUTION_HEIGHT", 1920)),
    int(environ.get("CAMERA_RESOLUTION_HEIGHT", 1080)),
)


async def handle_messages(hub: WorkerMessageHub):
    log.info("Starting the image capture service")

    with picamera.PiCamera() as camera:
        camera.resolution = camera_res
        await asyncio.sleep(2)
        log.info("Initialized the camera")

        async for message in hub.receive():
            match message:
                case StartCaptureMessage():
                    try:
                        image = np.empty((*camera_res, 3), dtype=np.uint8)

                        camera.capture(image, "rgb")

                        await hub.send(
                            ImageCapturedMessage(image=Image.fromarray(image))
                        )
                    except:  # noqa: E722
                        log.exception(
                            "An exception happened while trying to capture the image"
                        )


if __name__ == "__main__":
    worker_main(log, handle_messages)
