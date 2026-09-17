from datetime import datetime, timezone
from functools import wraps

import bcrypt
from flask import Blueprint, current_app, g, jsonify, request
from itsdangerous import URLSafeTimedSerializer
from bson import ObjectId

from app.extensions import get_db


auth_bp = Blueprint("auth", __name__)


def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="storyshield-token")


def generate_token(user_id):
    return get_serializer().dumps({"user_id": str(user_id)})


def verify_token(token):
    try:
        payload = get_serializer().loads(token, max_age=60 * 60 * 24 * 7)
        return payload
    except Exception:
        return None


def get_current_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if not payload or "user_id" not in payload:
        return None

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(payload["user_id"])})
    if user is None:
        return None

    user["_id"] = str(user["_id"])
    return user


def require_auth(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({"error": "Authentication required"}), 401

        g.user = user
        return view_func(*args, **kwargs)

    return wrapped


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400

    db = get_db()
    if db.users.find_one({"email": email}):
        return jsonify({"error": "An account with this email already exists"}), 409

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }

    result = db.users.insert_one(user)
    created_user = db.users.find_one({"_id": result.inserted_id})
    response_user = dict(created_user)
    response_user["_id"] = str(response_user["_id"])
    response_user.pop("password", None)

    token = generate_token(result.inserted_id)
    return jsonify({"token": token, "user": response_user}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = get_db()
    user = db.users.find_one({"email": email})
    if user is None:
        return jsonify({"error": "Invalid email or password"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    response_user = dict(user)
    response_user["_id"] = str(response_user["_id"])
    response_user.pop("password", None)

    token = generate_token(response_user["_id"])
    return jsonify({"token": token, "user": response_user})


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": g.user})
