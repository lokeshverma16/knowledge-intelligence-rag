from marshmallow import Schema, ValidationError, fields, validates


class IngestRequestSchema(Schema):
    s3_url = fields.String(required=True)

    @validates("s3_url")
    def _looks_like_s3(self, value: str, **_) -> None:
        if not value.startswith("s3://") or "/" not in value[5:]:
            raise ValidationError("Must be of the form s3://<bucket>/<key>")


class QueryRequestSchema(Schema):
    query = fields.String(required=True)

    @validates("query")
    def _non_empty(self, value: str, **_) -> None:
        if not value.strip():
            raise ValidationError("Query must not be empty.")
        if len(value) > 2000:
            raise ValidationError("Query too long (max 2000 chars).")
