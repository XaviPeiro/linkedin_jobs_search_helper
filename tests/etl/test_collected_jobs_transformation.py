import json

from etl.collected_jobs_transformation import AddDescriptionLanguage


def test_add_description_language_reads_jobs_and_persists_one_output(tmp_path):
    collected_jobs_dir = tmp_path / "collected_jobs" / "2026-04-30"
    collected_jobs_dir.mkdir(parents=True)
    (collected_jobs_dir / "execution#0.json").write_text(
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
    (collected_jobs_dir / "execution#1.json").write_text(
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
    )()

    transformed_jobs = [
        json.loads(line)
        for line in output_file.read_text().splitlines()
        if line.strip()
    ]

    assert transformed_jobs[0]["description_language"] == "en"
    assert transformed_jobs[1]["description_language"] == "pl"
    assert transformed_jobs[2]["description_language"] == "fr"


def test_add_description_language_accepts_one_input_file(tmp_path):
    input_file = tmp_path / "execution#0.json"
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
    )()

    transformed_job = json.loads(output_file.read_text())

    assert transformed_job["description_language"] == "en"
