import json

import pytest

from src.ingestion.load_data import load_knowledge_base, split_documents


def test_load_and_split_preserves_source_metadata(tmp_path):
    path = tmp_path / "knowledge.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "doc-1",
                "title": "Scheme guide",
                "source": "MyScheme public dataset",
                "url": "https://www.myscheme.gov.in/schemes/example",
                "official_url": "https://example.gov.in",
                "ministry": "Ministry",
                "level": "Central Government",
                "content": "A useful scheme eligibility paragraph. " * 20,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    chunks = split_documents(load_knowledge_base(path), chunk_size=100, chunk_overlap=20)

    assert len(chunks) > 1
    assert chunks[0].metadata["source"] == "MyScheme public dataset"
    assert chunks[0].metadata["official_url"] == "https://example.gov.in"
    assert chunks[0].metadata["chunk_id"].startswith("doc-1:")


def test_load_knowledge_base_reports_missing_fields(tmp_path):
    path = tmp_path / "invalid.jsonl"
    path.write_text('{"id":"missing-fields"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required fields"):
        load_knowledge_base(path)
