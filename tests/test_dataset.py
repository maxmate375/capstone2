import json

from src.config import PROJECT_ROOT


def test_dataset_contains_linked_central_scheme_eligibility_records():
    dataset_path = PROJECT_ROOT / "data" / "central_schemes.jsonl"
    records = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(records) == 526
    assert all(record["level"] == "Central Government" for record in records)
    assert all(record["content"].strip() for record in records)
    assert all(
        record["url"].startswith("https://www.myscheme.gov.in/schemes/")
        for record in records
    )
    assert len({record["id"] for record in records}) == len(records)


def test_dataset_attribution_pins_the_source_snapshot():
    info = json.loads(
        (PROJECT_ROOT / "data" / "source_info.json").read_text(encoding="utf-8")
    )

    assert info["upstream_commit"] == "4ddfa18d7aa3e630cc4ae3374731e5819d7875e7"
    assert info["upstream_records"] == 2066
    assert info["central_records"] == 527
    assert info["included_records"] == 526
    assert info["primary_source"] == "https://www.myscheme.gov.in/"
