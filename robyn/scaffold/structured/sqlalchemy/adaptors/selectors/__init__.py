from abc import ABC, abstractmethod


class Mutator(ABC):
    @abstractmethod
    def retrieve(self, **kwargs): ...

    @abstractmethod
    def list(self, **kwargs): ...
