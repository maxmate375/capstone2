import csv
import hashlib
import io
import json
from datetime import UTC, datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import get_settings

DATASET_COMMIT = "4ddfa18d7aa3e630cc4ae3374731e5819d7875e7"
DATASET_FILE_SHA = "3980e3a1648a5b239aad08f22fe3bcf951544859"
DATASET_URL = (
    "https://raw.githubusercontent.com/Aryan-Pardeshi/gov-myscheme-dataset/"
    f"{DATASET_COMMIT}/gov_myscheme_data.csv"
)


def prepare_dataset() -> int:
    settings = get_settings()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    response = session.get(DATASET_URL, timeout=90)
    response.raise_for_status()
    payload = response.content

    git_blob_header = f"blob {len(payload)}\0".encode("ascii")
    actual_blob_sha = hashlib.sha1(git_blob_header + payload).hexdigest()
    if actual_blob_sha != DATASET_FILE_SHA:
        raise ValueError(
            "The downloaded dataset does not match the pinned MyScheme snapshot."
        )

    rows = list(
        csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    )
    required_columns = {
        "Scheme Name",
        "Level",
        "State / UT / Ministry",
        "Eligibility Criteria",
        "Eligibility (General)",
        "MyScheme URL",
    }
    if not rows or not required_columns.issubset(rows[0]):
        raise ValueError("The downloaded dataset does not match the expected schema.")

    central_rows = [
        row
        for row in rows
        if row.get("Level", "").strip().casefold() == "central government"
    ]
    records = []
    for index, row in enumerate(central_rows, start=1):
        name = row.get("Scheme Name", "").strip()
        eligibility = (
            row.get("Eligibility Criteria")
            or row.get("Eligibility (General)")
            or ""
        ).strip()
        myscheme_url = row.get("MyScheme URL", "").strip()
        if (
            not name
            or not eligibility
            or not myscheme_url.startswith(
                "https://www.myscheme.gov.in/schemes/"
            )
        ):
            continue

        fields = [
            ("Scheme", name),
            ("Responsible ministry / department", row.get("State / UT / Ministry", "")),
            ("Categories", row.get("Tags / Categories", "")),
            ("Description", row.get("Description", "")),
            ("Eligibility criteria", eligibility),
            ("General eligibility", row.get("Eligibility (General)", "")),
            ("Exclusions / ineligibility", row.get("Exclusions / Ineligibility", "")),
            ("Benefits", row.get("Benefits", "")),
            ("Application process", row.get("Application Process", "")),
            ("Documents required", row.get("Documents Required", "")),
            ("Frequently asked questions", row.get("Frequently Asked Questions (FAQs)", "")),
        ]
        content = "\n".join(
            f"{label}: {value.strip()}"
            for label, value in fields
            if value and value.strip()
        )
        records.append(
            {
                "id": row.get("Scheme Slug", "").strip() or str(index),
                "title": name,
                "source": "MyScheme public scheme dataset; source page linked below",
                "url": myscheme_url,
                "official_url": row.get("Official Link", "").strip(),
                "ministry": row.get("State / UT / Ministry", "").strip(),
                "level": "Central Government",
                "content": content,
            }
        )

    if not records:
        raise ValueError("No central-government schemes with eligibility were found.")

    settings.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)
    with settings.knowledge_base_path.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    source_info = {
        "dataset": "Indian Government MyScheme Dataset",
        "upstream_repository": "https://github.com/Aryan-Pardeshi/gov-myscheme-dataset",
        "upstream_commit": DATASET_COMMIT,
        "upstream_file": "gov_myscheme_data.csv",
        "upstream_file_sha": DATASET_FILE_SHA,
        "upstream_huggingface_source": (
            "https://huggingface.co/datasets/shrijayan/gov_myscheme"
        ),
        "primary_source": "https://www.myscheme.gov.in/",
        "license": "Apache-2.0 (as stated by the dataset repository)",
        "filtered_level": "Central Government",
        "upstream_records": len(rows),
        "central_records": len(central_rows),
        "included_records": len(records),
        "retrieved_on": datetime.now(UTC).date().isoformat(),
        "limitations": (
            "Aggregated dataset snapshot; scheme details may change. Verify "
            "current rules on linked MyScheme and official ministry pages. "
            "Eligibility output is preliminary guidance, not an official determination."
        ),
    }
    info_path = settings.knowledge_base_path.parent / "source_info.json"
    info_path.write_text(
        json.dumps(source_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(records)


if __name__ == "__main__":
    count = prepare_dataset()
    print(f"Prepared {count} central government scheme records.")
