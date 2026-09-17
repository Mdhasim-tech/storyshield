import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from app.config import Config
from app.extensions import init_mongo, init_chroma, get_db, get_chroma


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["UPLOAD_FOLDER"] = os.path.abspath(app.config.get("UPLOAD_FOLDER", "./uploads"))
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app)
    init_mongo(app)
    init_chroma(app)

    from app.routes.auth import auth_bp
    from app.routes.books import books_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(books_bp, url_prefix="/api/books")

    @app.route("/")
    def health_check():
        return {"status": "StoryShield backend is running"}

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        upload_folder = os.path.abspath(app.config.get("UPLOAD_FOLDER", "./uploads"))
        return send_from_directory(upload_folder, filename)

    @app.route("/db-check")
    def db_check():
        db = get_db()
        db.command("ping")
        return {"status": "MongoDB connected"}

    @app.route("/chroma-check")
    def chroma_check():
        client = get_chroma()
        collections = client.list_collections()
        return {"status": "Chroma connected", "collections": [c.name for c in collections]}

    return app