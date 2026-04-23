import pytest

from app.services.s3_service import s3_service


def test_parse_valid_s3_url():
    bucket, key = s3_service.parse_s3_url("s3://my-bucket/path/to/doc.pdf")
    assert bucket == "my-bucket"
    assert key == "path/to/doc.pdf"


def test_parse_invalid_scheme_raises():
    with pytest.raises(ValueError):
        s3_service.parse_s3_url("https://my-bucket/path/to/doc.pdf")
