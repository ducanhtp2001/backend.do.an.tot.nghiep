from enum import Enum

class collection(Enum):
    USER = 1
    FILE = 2
    COMMENT = 3
    LIKE = 4

class notify_type(Enum):
    NEW_FILE = 0
    COMMENT = 1
    REPLY = 2
    LIKE_FILE = 3
    LIKE_CMT = 4