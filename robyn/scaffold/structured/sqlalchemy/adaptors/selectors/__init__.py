from abc import ABC, abstractmethod

from pydantic import BaseModel


class Mutator(ABC):
    @abstractmethod
    def retrieve(self, **kwargs): ...

    @abstractmethod
    def list(self, **kwargs): ...
