# Classes for testing
from typing import Optional
class Test():
    f: int
    g: int

class NestedCls():
    f: Test
    special: Optional[str] = "Nice"

class TestCtor:
    a: int
    b: str

    def __init__(self, a: int, b: str = "Nice"):
        self.a = a
        self.b = b

class Nested:
    c: int
    d: str

class TestQueryType:
    a: int
    b: str

class TestForwardRef:
    a: 'Ref'

class Ref:
    a: int
    b: str