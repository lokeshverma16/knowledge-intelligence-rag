import pytest

from app.services.ingestion import ingestion_service


def test_chunking_text_file(app, tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text(
        "Paragraph one. " * 50 + "\n\n" + "Paragraph two. " * 50,
        encoding="utf-8",
    )

    with app.app_context():
        chunks = ingestion_service.process_and_chunk(
            str(sample), source_url="s3://fake/sample.txt"
        )

    assert len(chunks) >= 1
    assert all(c.metadata["source_url"] == "s3://fake/sample.txt" for c in chunks)
    assert all(c.metadata["source_type"] == ".txt" for c in chunks)


def test_unsupported_extension_raises(app, tmp_path):
    f = tmp_path / "sample.docx"
    f.write_bytes(b"not really a docx")

    with app.app_context(), pytest.raises(ValueError):
        ingestion_service.load_document(str(f))
