import logging
import os
import sys

from flask import Flask, jsonify

from app.config import config_by_name


def _configure_logging(app: Flask) -> None:
    """
    Route Flask/werkzeug/gunicorn logs through a single formatter so the
    container output stays grep-friendly.
    """
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    # Replace any default handlers Flask attached.
    app.logger.handlers = [handler]
    app.logger.setLevel(level)
    # Also align werkzeug's access log formatting.
    logging.getLogger("werkzeug").handlers = [handler]


def create_app(config_name: str | None = None) -> Flask:
    """Application factory. Selects config via `ENVIRONMENT` or explicit arg."""
    app = Flask(__name__, instance_relative_config=True)

    config_name = config_name or os.environ.get("ENVIRONMENT", "development")
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    _configure_logging(app)
    app.logger.info("Starting Enterprise RAG Platform (env=%s)", config_name)

    @app.route("/health")
    def health_check():
        return (
            jsonify(
                {
                    "status": "up",
                    "service": "Enterprise RAG Platform API",
                    "environment": config_name,
                }
            ),
            200,
        )

    from app.api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api/v1")

    return app
