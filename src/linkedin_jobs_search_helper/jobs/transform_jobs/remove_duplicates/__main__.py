from pathlib import Path
import logging
import argparse

import json
from linkedin_jobs_search_helper.common.logger import configure_logging
from linkedin_jobs_search_helper.jobs.transform_jobs.add_language.conf import ACCEPTED_INPUT_SUFFIX
from linkedin_jobs_search_helper.jobs.transform_jobs.helpers.collected_jobs_parser import iter_collected_job_files

logger = logging.getLogger(__name__)

def main(input_path: Path, output_path: Path):
    # ! MUST FIT IN MEMORY
    s = set()
    for input_file_path in iter_collected_job_files(input_path, ACCEPTED_INPUT_SUFFIX):
        with open(input_file_path, mode='r') as file:
            while l := file.readline():
                try:
                    # Slow, no need to create an object, but no need to optimise it right now.
                    json.loads(l)
                    s.add(l.strip())
                except json.JSONDecodeError:
                    pass


    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as out:
        for l in s:
            out.write(f"{l}\n")

    logger.info(f"Job complete. You can find your file in {output_path}")
    logger.info("🤖Sayonara, baby.")

if __name__ == "__main__":
    configure_logging()

    agp = argparse.ArgumentParser()
    agp.add_argument("input_path", type=Path)
    agp.add_argument("--output_path", type=Path)
    args = agp.parse_args()

    input_fp: Path = args.input_path
    default_op = input_fp.parent if input_fp.is_file() else input_fp
    output_fp = args.output_path or default_op / 'no-duplicated' / 'jobs.jsonl'
    logger.info(f"Input path: {input_fp}")
    logger.info(f"Output path: {output_fp}")
    main(input_fp, output_fp)
