import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration. Values flow in via environment variables."""

    # --- OpenAI ---
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL = os.environ.get(
        "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
    )

    # --- AWS / S3 ---
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    # --- ChromaDB ---
    # When CHROMA_HOST is set, we talk to a Chroma server over HTTP
    # (that's how docker-compose wires things up). Otherwise we fall back to
    # an embedded persistent client, so the app also runs as a single process.
    CHROMA_HOST = os.environ.get("CHROMA_HOST")
    CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
    CHROMA_DB_DIR = os.environ.get("CHROMA_DB_DIR", "./data/chromadb")
    CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "enterprise_knowledge")

    # --- Retrieval / chunking knobs (surfaced here so they're easy to tune) ---
    CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))
    RETRIEVAL_K = int(os.environ.get("RETRIEVAL_K", "5"))

    # --- App ---
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    """Used by the pytest suite; keeps everything offline."""

    DEBUG = True
    TESTING = True
    OPENAI_API_KEY = "test-key"
    CHROMA_DB_DIR = "./data/chromadb-test"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
