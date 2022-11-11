from enum import Enum


class FunctionType(Enum):
    SyncFunction = "sync_function"
    AsyncFunction = "async_function"
    SyncGenerator = "sync_generator"


