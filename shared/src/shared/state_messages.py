from shared.messages import Message, StateUpdate
from shared.state import StateRef


def update_state(message: Message, state_ref: StateRef):
    match message:
        case StateUpdate(new_state=s):
            state_ref.state = s
