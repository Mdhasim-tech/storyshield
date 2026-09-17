import importlib
import os

import app.extensions as extensions
import app.config as config_module
from app import create_app


class FakeCollection:
    def __init__(self):
        self.items = []

    def find_one(self, query):
        for item in self.items:
            if all(item.get(k) == v for k, v in query.items()):
                return item
        return None

    def insert_one(self, document):
        document = dict(document)
        document["_id"] = str(len(self.items) + 1)
        self.items.append(document)
        return type("InsertResult", (), {"inserted_id": document["_id"]})()

    def find(self, query=None):
        if query is None:
            query = {}
        return [item for item in self.items if all(item.get(k) == v for k, v in query.items())]

    def update_one(self, query, update):
        for item in self.items:
            if all(item.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    item.update(update["$set"])
                return True
        return False


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.books = FakeCollection()


def test_register_and_login(monkeypatch):
    fake_db = FakeDB()

    monkeypatch.setattr(extensions, "init_mongo", lambda app: None)
    monkeypatch.setattr(extensions, "init_chroma", lambda app: None)
    monkeypatch.setattr(extensions, "get_db", lambda: fake_db)

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.post(
        "/api/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "secret123"},
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["user"]["email"] == "alice@example.com"
    assert payload["token"]

    response = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["user"]["email"] == "alice@example.com"
    assert payload["token"]


def test_uploaded_pdf_can_be_served(tmp_path, monkeypatch):
    fake_db = FakeDB()

    monkeypatch.setattr(extensions, "init_mongo", lambda app: None)
    monkeypatch.setattr(extensions, "init_chroma", lambda app: None)
    monkeypatch.setattr(extensions, "get_db", lambda: fake_db)

    app = create_app()
    app.config.update(TESTING=True, UPLOAD_FOLDER=str(tmp_path))
    client = app.test_client()

    pdf_path = tmp_path / "book-42.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nfake-pdf-content")

    response = client.get("/uploads/book-42.pdf")

    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert response.mimetype == "application/pdf"


def test_upload_folder_resolves_to_absolute_path(monkeypatch):
    monkeypatch.setenv("UPLOAD_FOLDER", "./uploads")
    importlib.reload(config_module)
    assert os.path.isabs(config_module.Config.UPLOAD_FOLDER)
    assert os.path.basename(config_module.Config.UPLOAD_FOLDER) == "uploads"
