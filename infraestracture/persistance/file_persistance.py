from dataclasses import Field
from datetime import date
import os

from pydantic import BaseModel, AnyHttpUrl


class Job(BaseModel):
    id: int
    url: AnyHttpUrl
    description: str
    title: str

class FilePersistence:
    persistence_file_path: str
    base_path: str
    items_added: int

    def __init__(self, base_path: str):
        self.base_path = base_path
        day = str(date.today())
        number: int = self._get_file_number()

        self.persistence_file_path = f'{self.base_path}/collected_jobs/{day}/execution#{number}.txt'

    @staticmethod
    def _get_file_number() -> int:
        files = os.listdir()
        return len(files)

    def __call__(self, content: dict):
        formatted_content = self._format_content(content)
        with open(self.persistence_file_path, 'a+') as file:
            file.write(formatted_content)

        self.items_added+=1


    @staticmethod
    def _format_content(self, content:dict) -> str:
        f"""
        Item {}
        """


