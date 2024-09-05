from enum import Enum, auto


class UpperStrEnum(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.upper()


class LowerStrEnum(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class HttpMethod(UpperStrEnum):
    GET = auto()
    POST = auto()


class MessageType(LowerStrEnum):
    CHAT_MESSAGE = auto()
    PAST_MESSAGE = auto()
    LAST_MESSAGE = auto()
    SEND_CHATROOM_LIST = auto()
    UPDATE_LATEST_MSG = auto()
    SEND_USER_COUNT = auto()
