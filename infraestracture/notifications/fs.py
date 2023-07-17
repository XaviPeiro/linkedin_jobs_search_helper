from domain.notificator import Notificator


class FileSystemNotificator(Notificator):
    file_path: str

    def __init__(self, filepath: str):
        self.file_path = filepath

    def notify(self, message: str):

        # TODO P4: Could be nice to prepend instead of append, but it is too annoying for occasion.
        with open(mode="a+", file=self.file_path) as f:
            f.write(message)
