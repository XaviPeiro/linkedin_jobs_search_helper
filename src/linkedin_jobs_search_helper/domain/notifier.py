from abc import ABC

class Notifier(ABC):
    def notify(self, message: str) -> None:
        ...
