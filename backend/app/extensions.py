from pymongo import MongoClient
import chromadb

_mongo_client = None
_db_name = None
_chroma_client = None

def init_mongo(app):
    global _mongo_client, _db_name
    _mongo_client = MongoClient(app.config["MONGO_URI"])
    _db_name = app.config["DB_NAME"]

def init_chroma(app):
    global _chroma_client
    _chroma_client = chromadb.PersistentClient(path=app.config["CHROMA_PATH"])

def get_db():
    return _mongo_client[_db_name]

def get_chroma():
    return _chroma_client

def get_book_collection(book_id):
    return _chroma_client.get_or_create_collection(name=f"book_{book_id}")