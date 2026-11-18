import os
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from bson import ObjectId
from bson.errors import InvalidId
from app.extensions import get_db, get_book_collection
from app.ingestion.pdf_loader import extract_pages
from app.ingestion.chapter_detector import chapterize_pages, group_by_chapter
from app.ingestion.chunker import chunk_chapters
from app.agent.retriever import get_safe_chunks
from app.agent.react_loop import answer_question
from app.agent.llm_client import EmptyAssistantResponseError
from app.routes.auth import require_auth

books_bp = Blueprint("books", __name__)


@books_bp.route("/upload", methods=["POST"])
@require_auth
def upload_book():
    file = request.files.get("file")
    title = request.form.get("title", "Untitled")

    if not file:
        return jsonify({"error": "No file provided"}), 400

    db = get_db()
    book = db.books.insert_one({
        "title": title,
        "user_id": ObjectId(g.user["_id"]),
        "uploaded_at": datetime.utcnow(),
        "status": "processing",
        "reading_status": "pending",
        "reading_progress": {"chapter_order": 1, "page": 1}
    })
    book_id = str(book.inserted_id)

    upload_folder = current_app.config.get("UPLOAD_FOLDER", "./uploads")
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, f"{book_id}.pdf")
    file.save(save_path)

    pages = extract_pages(save_path)
    pages = chapterize_pages(pages)
    chapters = group_by_chapter(pages)
    chunks = chunk_chapters(chapters)

    if not chunks:
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"status": "failed", "error": "No extractable text found in the uploaded PDF"}}
        )
        return jsonify({
            "error": "No extractable text found in the uploaded PDF. Ensure it contains selectable text."
        }), 422

    collection = get_book_collection(book_id)
    collection.add(
        ids=[f"{book_id}_{c['metadata']['global_chunk_index']}" for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{**c["metadata"], "book_id": book_id} for c in chunks]
    )

    total_chapters = max((c["metadata"]["chapter_order"] for c in chunks), default=0)
    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"status": "ready", "total_chapters": total_chapters, "total_chunks": len(chunks)}}
    )

    return jsonify({"book_id": book_id, "status": "ready", "total_chunks": len(chunks)}), 201


@books_bp.route("", methods=["GET"])
@require_auth
def list_books():
    db = get_db()
    books = list(db.books.find({"user_id": ObjectId(g.user["_id"])}))
    for b in books:
        b["_id"] = str(b["_id"])
        if "user_id" in b:
            b["user_id"] = str(b["user_id"])
        b.setdefault("reading_status", "pending")
    return jsonify(books)


@books_bp.route("/<book_id>/reading-status", methods=["PUT"])
@require_auth
def update_reading_status(book_id):
    data = request.get_json(silent=True) or {}
    reading_status = data.get("reading_status")

    if reading_status not in ("pending", "read"):
        return jsonify({"error": "Reading status must be 'pending' or 'read'"}), 400

    user_id = ObjectId(g.user["_id"])
    try:
        book_object_id = ObjectId(book_id)
    except InvalidId:
        return jsonify({"error": "Book not found"}), 404

    db = get_db()
    book = db.books.find_one({"_id": book_object_id, "user_id": user_id})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    db.books.update_one(
        {"_id": book_object_id, "user_id": user_id},
        {"$set": {"reading_status": reading_status}}
    )
    return jsonify({"reading_status": reading_status})


@books_bp.route("/<book_id>/progress", methods=["GET", "PUT"])
@require_auth
def reading_progress(book_id):
    db = get_db()
    book = db.books.find_one({"_id": ObjectId(book_id), "user_id": ObjectId(g.user["_id"])})
    if not book:
        return jsonify({"error": "Book not found"}), 404

    if request.method == "GET":
        progress = book.get("reading_progress", {"chapter_order": 1, "page": 1})
        progress["chapter_order"] = max(int(progress.get("chapter_order", 1)), 1)
        progress["page"] = max(int(progress.get("page", 1)), 1)
        return jsonify(progress)

    data = request.get_json(silent=True) or {}
    chapter_order = max(int(data.get("chapter_order", 1)), 1)
    page = max(int(data.get("page", 1)), 1)

    db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"reading_progress": {"chapter_order": int(chapter_order), "page": int(page)}}}
    )

    return jsonify({"chapter_order": int(chapter_order), "page": int(page)})


@books_bp.route("/<book_id>/ask", methods=["POST"])
@require_auth
def ask_question(book_id):
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    chapter_order = max(int(data.get("chapter_order", 1)), 1)
    page = max(int(data.get("page", 1)), 1)

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        result = answer_question(
            book_id=book_id,
            question=question,
            chapter_order=chapter_order,
            page=page,
            allow_future=data.get("allow_future") is True
        )
    except EmptyAssistantResponseError as error:
        current_app.logger.warning("Assistant returned an empty response for book %s", book_id)
        return jsonify({"error": str(error)}), 502

    return jsonify(result)


@books_bp.route("/<book_id>/test-ask", methods=["POST"])
@require_auth
def test_ask(book_id):
    data = request.get_json() or {}
    result = answer_question(
        book_id=book_id,
        question=data["question"],
        chapter_order=data["chapter_order"],
        page=data["page"]
    )
    return jsonify(result)


@books_bp.route("/<book_id>/test-retrieve", methods=["POST"])
@require_auth
def test_retrieve(book_id):
    data = request.get_json() or {}
    question = data["question"]
    chapter_order = data["chapter_order"]
    page = data["page"]

    collection = get_book_collection(book_id)
    results = get_safe_chunks(collection, chapter_order, page, question)

    return jsonify({
        "documents": results.get("documents", [[]])[0],
        "metadatas": results.get("metadatas", [[]])[0]
    })