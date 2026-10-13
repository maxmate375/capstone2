import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_knowledge_base(path: Path) -> list[Document]:
    documents = []
    with path.open(encoding="utf-8") as knowledge_file:
        for line_number, line in enumerate(knowledge_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}."
                ) from error

            required = ("id", "title", "source", "url", "content")
            missing = [field for field in required if not record.get(field)]
            if missing:
                raise ValueError(
                    f"Missing required fields on line {line_number}: "
                    f"{', '.join(missing)}."
                )

            documents.append(
                Document(
                    page_content=" ".join(record["content"].split()),
                    metadata={
                        "document_id": str(record["id"]),
                        "title": str(record["title"]),
                        "source": str(record["source"]),
                        "url": str(record["url"]),
                        "official_url": str(record.get("official_url", "")),
                        "ministry": str(record.get("ministry", "")),
                        "level": str(record.get("level", "")),
                    },
                )
            )

    if not documents:
        raise ValueError(f"No knowledge documents were found in {path}.")
    return documents


def split_documents(
    documents: list[Document], chunk_size: int = 700, chunk_overlap: int = 100
) -> list[Document]:
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Use chunk_size > chunk_overlap >= 0.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = (
            f"{chunk.metadata['document_id']}:{chunk.metadata['start_index']}:{index}"
        )
    return chunks
