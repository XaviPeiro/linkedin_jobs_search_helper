import json

from transform_jobs.add_language import AddDescriptionLanguage
from transform_jobs.language_detection import LanguageDetector


def test_add_description_language_reads_jobs_and_persists_one_output(tmp_path):
    collected_jobs_dir = tmp_path / "collected_jobs" / "2026-04-30"
    collected_jobs_dir.mkdir(parents=True)
    job_lang_map = {
        1: "en",
        2: "pl",
        3: "fr",
    }
    (collected_jobs_dir / "execution#0.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": 1,
                        "url": "https://www.linkedin.com/jobs/view/1/",
                        "description": "We are looking for a Python engineer.",
                        "title": "Python Engineer",
                    }
                ),
                json.dumps(
                    {
                        "id": 2,
                        "url": "https://www.linkedin.com/jobs/view/2/",
                        "description": "Szukamy inzyniera oprogramowania.",
                        "title": "Software Engineer",
                    }
                ),
            ]
        )
    )
    (collected_jobs_dir / "execution#1.jsonl").write_text(
        json.dumps(
            {
                "id": 3,
                "url": "https://www.linkedin.com/jobs/view/3/",
                "description": "Nous recherchons un ingenieur logiciel.",
                "title": "Software Engineer",
            }
        )
    )
    output_file = collected_jobs_dir / "transformed" / "jobs.json"

    AddDescriptionLanguage(
        input_path=collected_jobs_dir,
        output_path=output_file,
        language_detector=LanguageDetector(),
    )()

    transformed_jobs = [
        json.loads(line)
        for line in output_file.read_text().splitlines()
        if line.strip()
    ]

    for t in transformed_jobs:
        assert t['description_language'] == job_lang_map[t['id']]

def test_add_description_language_accepts_one_input_file(tmp_path):
    input_file = tmp_path / "execution#0.jsonl"
    output_file = tmp_path / "transformed" / "jobs.json"
    input_file.write_text(
        json.dumps(
            {
                "id": 1,
                "url": "https://www.linkedin.com/jobs/view/1/",
                "description": "We are looking for a Python engineer.",
                "title": "Python Engineer",
            }
        )
    )

    AddDescriptionLanguage(
        input_path=input_file,
        output_path=output_file,
        language_detector=LanguageDetector(),
    )()

    transformed_job = json.loads(output_file.read_text())

    assert transformed_job["description_language"] == "en"
