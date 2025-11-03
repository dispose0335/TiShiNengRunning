import enum


class TiShiNengError(Exception):
    def __init__(self, message, code=10000):
        self.code = code
        self.message = message
        super().__init__(self.message)

class TsnErrorCode(enum.Enum):
    RUN_TIME_CONFLICT = 10003
