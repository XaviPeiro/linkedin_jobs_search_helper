from domain.notificator import Notificator


class FileSystemNotificator(Notificator):
    file_path: str

    def __init__(self, filepath: str):
        self.file_path = filepath

    def notify(self, message: str):

        with open(mode="r+", file=self.file_path) as f:
            f.write(message)
