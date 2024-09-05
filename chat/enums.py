from enum import Enum, auto


class LowerStrEnum(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class MessageType(LowerStrEnum):
    CHAT_MESSAGE = auto()
    PAST_MESSAGE = auto()
    SEND_CHATROOM_LIST = auto()
    UPDATE_LATEST_MSG = auto()
    SEND_USER_COUNT = auto()
