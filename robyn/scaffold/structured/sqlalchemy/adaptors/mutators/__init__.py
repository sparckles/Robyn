from abc import ABC, abstractmethod

from pydantic import BaseModel


class Mutator(ABC):
    @abstractmethod
    def create(self, model: BaseModel):
        ...

    @abstractmethod
    def update(self, **kwargs):
        ...

    @abstractmethod
    def delete(self, **kwargs):
        ...
