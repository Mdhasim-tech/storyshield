import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "storyshield-dev-secret-key")
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "storyshield")
    CHROMA_PATH = os.path.abspath(os.getenv("CHROMA_PATH", os.path.join(BASE_DIR, "chroma_data")))
    UPLOAD_FOLDER = os.path.abspath(os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads")))
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")