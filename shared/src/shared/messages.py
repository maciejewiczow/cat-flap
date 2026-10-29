from dataclasses import field, dataclass
from datetime import datetime
from PIL.Image import Image
import numpy as np

from shared.state import CatFlapStateMachine


@dataclass
class Message:
    timestamp: datetime = field(default_factory=lambda: datetime.now(), init=False)


@dataclass
class EngageLockMessage(Message):
    pass


@dataclass
class DisengageLockMessage(Message):
    pass


@dataclass
class MotionDetectedMessage(Message):
    pass


@dataclass
class MotionEndedMessage(Message):
    pass


@dataclass
class DoorOpenedMessage(Message):
    pass


@dataclass
class DoorClosedMessage(Message):
    pass


@dataclass
class StartCaptureMessage(Message):
    pass


@dataclass
class ImageCapturedMessage(Message):
    image: Image = field(repr=False)


@dataclass
class InferenceCompleteMessage(Message):
    detected_classes: list[tuple[str, float]]
    image_with_overlays: np.ndarray = field(repr=False)
    result_json: str


@dataclass
class MainButtonPressedMessage(Message):
    pass


@dataclass
class StateUpdate(Message):
    new_state: CatFlapStateMachine


@dataclass
class ServiceActivated(Message):
    pass
