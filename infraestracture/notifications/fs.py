from domain.notifier import Notifier


class FileSystemNotificator(Notifier):
    file_path: str

    def __init__(self, filepath: str):
        self.file_path = filepath

    def notify(self, message: str):

        # Just use the logging...
        with open(mode="a+", file=self.file_path) as f:
            f.write(message + "\n")
