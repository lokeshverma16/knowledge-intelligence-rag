import os
from flask import Flask, jsonify

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # A simple health check route
    @app.route('/health')
    def health_check():
        return jsonify({
            "status": "up",
            "service": "Enterprise RAG Platform API"
        }), 200

    # Register blueprints (to be created next)
    # from app.api.routes import api_bp
    # app.register_blueprint(api_bp, url_prefix='/api/v1')

    return app
