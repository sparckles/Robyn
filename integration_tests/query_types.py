from dataclasses import dataclass

@dataclass
class Nested:
    c: int
    d: str

@dataclass
class TestQueryType:
    a: int
    b: Nested