import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class."""
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    CHROMA_DB_DIR = os.environ.get('CHROMA_DB_DIR', '/app/data/chromadb')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig
)
