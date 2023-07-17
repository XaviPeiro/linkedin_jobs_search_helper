from abc import ABC


# TODO P1: Enable to notify different messages to different endpoints. Apply Open-Close principle. It does not apply
#  here, so it is an interface.
class Notificator(ABC):
    def notify(self, message: str) -> None:
        ...
