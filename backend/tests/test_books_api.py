from io import BytesIO

from bson import ObjectId

import app.extensions as extensions
from app import create_app


class FakeBooks:
    def __init__(self):
        self.documents = {}

    def insert_one(self, document):
        book_id = ObjectId("64b000000000000000000001")
        self.documents[book_id] = dict(document, _id=book_id)
        return type("InsertResult", (), {"inserted_id": book_id})()

    def find_one(self, query):
        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None

    def find(self, query):
        return [
            document for document in self.documents.values()
            if all(document.get(key) == value for key, value in query.items())
        ]

    def update_one(self, query, update):
        document = self.find_one(query)
        if document:
            document.update(update["$set"])


class FakeDB:
    def __init__(self):
        self.books = FakeBooks()


def test_upload_without_extractable_text_returns_error(tmp_path, monkeypatch):
    import app.routes.auth as auth_routes
    import app.routes.books as books_routes

    fake_db = FakeDB()
    user_id = str(ObjectId("64b000000000000000000002"))

    monkeypatch.setattr(extensions, "init_mongo", lambda app: None)
    monkeypatch.setattr(extensions, "init_chroma", lambda app: None)
    monkeypatch.setattr(auth_routes, "get_current_user", lambda: {"_id": user_id})
    monkeypatch.setattr(books_routes, "get_db", lambda: fake_db)
    monkeypatch.setattr(books_routes, "extract_pages", lambda path: [])

    def fail_if_chroma_is_used(book_id):
        raise AssertionError("Chroma must not be called for an empty PDF")

    monkeypatch.setattr(
        books_routes,
        "get_book_collection",
        fail_if_chroma_is_used,
    )

    app = create_app()
    app.config.update(TESTING=True, UPLOAD_FOLDER=str(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/books/upload",
        data={"file": (BytesIO(b"%PDF-1.4"), "empty.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert response.get_json()["error"] == (
        "No extractable text found in the uploaded PDF. Ensure it contains selectable text."
    )
    saved_book = next(iter(fake_db.books.documents.values()))
    assert saved_book["status"] == "failed"


def test_reading_status_can_be_changed_by_book_owner(tmp_path, monkeypatch):
    import app.routes.auth as auth_routes
    import app.routes.books as books_routes

    fake_db = FakeDB()
    book_id = ObjectId("64b000000000000000000001")
    user_id = ObjectId("64b000000000000000000002")
    fake_db.books.documents[book_id] = {
        "_id": book_id,
        "user_id": user_id,
        "reading_status": "pending",
    }
    legacy_book_id = ObjectId("64b000000000000000000003")
    fake_db.books.documents[legacy_book_id] = {
        "_id": legacy_book_id,
        "user_id": user_id,
        "status": "ready",
    }

    monkeypatch.setattr(extensions, "init_mongo", lambda app: None)
    monkeypatch.setattr(extensions, "init_chroma", lambda app: None)
    monkeypatch.setattr(auth_routes, "get_current_user", lambda: {"_id": str(user_id)})
    monkeypatch.setattr(books_routes, "get_db", lambda: fake_db)

    app = create_app()
    app.config.update(TESTING=True, UPLOAD_FOLDER=str(tmp_path))
    client = app.test_client()

    invalid_response = client.put(
        f"/api/books/{book_id}/reading-status",
        json={"reading_status": "finished"},
    )
    assert invalid_response.status_code == 400

    response = client.put(
        f"/api/books/{book_id}/reading-status",
        json={"reading_status": "read"},
    )

    assert response.status_code == 200
    assert response.get_json()["reading_status"] == "read"
    assert fake_db.books.documents[book_id]["reading_status"] == "read"

    list_response = client.get("/api/books")
    listed_books = {book["_id"]: book for book in list_response.get_json()}
    assert listed_books[str(book_id)]["reading_status"] == "read"
    assert listed_books[str(legacy_book_id)]["reading_status"] == "pending"


def test_ask_route_requires_explicit_boolean_to_enable_future_spoilers(tmp_path, monkeypatch):
    import app.routes.auth as auth_routes
    import app.routes.books as books_routes

    user_id = str(ObjectId("64b000000000000000000002"))
    received_options = []

    monkeypatch.setattr(extensions, "init_mongo", lambda app: None)
    monkeypatch.setattr(extensions, "init_chroma", lambda app: None)
    monkeypatch.setattr(auth_routes, "get_current_user", lambda: {"_id": user_id})
    monkeypatch.setattr(
        books_routes,
        "answer_question",
        lambda **kwargs: received_options.append(kwargs["allow_future"]) or {
            "answer": "Answer",
            "blocked": False,
        },
    )

    app = create_app()
    app.config.update(TESTING=True, UPLOAD_FOLDER=str(tmp_path))
    client = app.test_client()
    ask_url = "/api/books/64b000000000000000000001/ask"

    safe_response = client.post(
        ask_url,
        json={"question": "What happens?", "chapter_order": 1, "page": 1},
    )
    spoiler_response = client.post(
        ask_url,
        json={
            "question": "What happens?",
            "chapter_order": 1,
            "page": 1,
            "allow_future": True,
        },
    )

    assert safe_response.status_code == 200
    assert spoiler_response.status_code == 200
    assert received_options == [False, True]


def test_ask_route_returns_a_clear_error_for_empty_assistant_response(tmp_path, monkeypatch):
    import app.routes.auth as auth_routes
    import app.routes.books as books_routes

    from app.agent.llm_client import EmptyAssistantResponseError

    monkeypatch.setattr(extensions, "init_mongo", lambda app: None)
    monkeypatch.setattr(extensions, "init_chroma", lambda app: None)
    monkeypatch.setattr(
        auth_routes,
        "get_current_user",
        lambda: {"_id": str(ObjectId("64b000000000000000000002"))},
    )

    def empty_answer(**kwargs):
        raise EmptyAssistantResponseError(
            "The assistant returned an empty response. Please try again."
        )

    monkeypatch.setattr(books_routes, "answer_question", empty_answer)

    app = create_app()
    app.config.update(TESTING=True, UPLOAD_FOLDER=str(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/books/64b000000000000000000001/ask",
        json={"question": "What happened?", "chapter_order": 1, "page": 1},
    )

    assert response.status_code == 502
    assert response.get_json()["error"] == (
        "The assistant returned an empty response. Please try again."
    )
