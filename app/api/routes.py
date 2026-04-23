import os
import traceback

from flask import current_app, jsonify, request
from marshmallow import ValidationError

from app.api import api_bp
from app.api.schemas import IngestRequestSchema, QueryRequestSchema
from app.services.ingestion import ingestion_service
from app.services.rag_engine import rag_engine
from app.services.s3_service import s3_service
from app.services.vector_db import vector_db_service


def _json_error(message: str, status: int, **extra):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status


@api_bp.route("/ingest", methods=["POST"])
def ingest_document():
    """
    Pull a document from S3, chunk it, embed it, and persist to Chroma.

    Payload: {"s3_url": "s3://bucket/key.pdf"}
    """
    try:
        data = IngestRequestSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return _json_error("Invalid payload", 400, fields=err.messages)

    s3_url = data["s3_url"]
    temp_file_path: str | None = None

    try:
        temp_file_path = s3_service.download_file(s3_url)
        chunks = ingestion_service.process_and_chunk(temp_file_path, source_url=s3_url)
        vector_db_service.store_documents(chunks)

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Ingested {len(chunks)} chunks from {s3_url}",
                    "chunks": len(chunks),
                    "source": s3_url,
                }
            ),
            201,
        )

    except ValueError as e:
        # e.g. unsupported file type or malformed S3 URL
        return _json_error(str(e), 400)
    except Exception as e:
        current_app.logger.error("Ingestion failed: %s", traceback.format_exc())
        return _json_error("Failed to process document", 500, details=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:  # pragma: no cover
                current_app.logger.warning("Could not remove %s", temp_file_path)


@api_bp.route("/query", methods=["POST"])
def query_knowledge_base():
    """
    Answer a question against the ingested corpus.

    Payload: {"query": "What is the remote work policy?"}
    """
    try:
        data = QueryRequestSchema().load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return _json_error("Invalid payload", 400, fields=err.messages)

    query_text = data["query"]

    try:
        result = rag_engine.query(query_text)
        return (
            jsonify(
                {
                    "query": query_text,
                    "answer": result["answer"],
                    "citations": result["citations"],
                }
            ),
            200,
        )
    except Exception as e:
        current_app.logger.error("Query failed: %s", traceback.format_exc())
        return _json_error("Failed to query knowledge base", 500, details=str(e))


@api_bp.route("/stats", methods=["GET"])
def stats():
    """Cheap introspection endpoint. Useful for dashboards and smoke tests."""
    try:
        return jsonify(vector_db_service.collection_stats()), 200
    except Exception as e:  # pragma: no cover - depends on external service
        current_app.logger.error("Stats failed: %s", traceback.format_exc())
        return _json_error("Failed to read collection stats", 500, details=str(e))
