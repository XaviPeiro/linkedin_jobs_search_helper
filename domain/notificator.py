from abc import ABC


class Notificator(ABC):
    def notify(self, message: str) -> None:
        ...
