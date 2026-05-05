import argparse
import json
from pathlib import Path
from pydantic import BaseModel

class Filter(BaseModel):
    language: str

    def evaluate(self, d: dict):


def main(input_path: Path, jobs_filter: Filter, output_file_path: Path|None = None,):
    if output_file_path is None:
        base_of = input_path.parent if input_path.is_file() else input_path
        output_file_path = base_of / 'final_jobs_to_evaluate'

    if output_file_path.exists():
        raise Exception(f"Output filepath already exists: {output_file_path}")

    with open(input_path, 'r') as inf, open(output_file_path, 'w') as ouf:

        while line := inf.readline():
            if line in ('\n', ' '):
                continue

            j: dict = json.loads(inf.readline())


            ouf.write(inf.readline())



if __name__ == '__main__':
    main()