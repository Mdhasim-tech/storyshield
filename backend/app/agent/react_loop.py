from app.extensions import get_book_collection
from app.agent.retriever import get_safe_chunks
from app.agent.llm_client import call_llm

# Chroma's default embedding uses cosine distance — lower is more similar.
# This threshold is a starting point; we'll tune it once we see real numbers.
DISTANCE_THRESHOLD = 1.0

SYSTEM_PROMPT = """You are a spoiler-safe reading companion. You only know what
the reader has read so far, based on the context provided below. If the context
doesn't actually contain enough information to answer the question, say clearly
that you don't have enough information yet and that it may be revealed later in
the book. Never guess, infer, or fill in plot details that aren't in the context."""


def is_summary_question(question):
    normalized = (question or "").lower()
    summary_triggers = [
        "what happens", "what happened", "what is happening", "summary",
        "summarize", "so far", "uptil now", "until now", "what has happened",
        "what happens so far", "what happened so far", "give me a summary",
        "brief summary", "overview"
    ]
    return any(trigger in normalized for trigger in summary_triggers)


def answer_question(book_id, question, chapter_order, page):
    collection = get_book_collection(book_id)
    results = get_safe_chunks(collection, chapter_order, page, question)

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    summary_mode = is_summary_question(question)

    # Summary questions should be answered from the available context, not blocked as if
    # the user is asking for future plot points.
    if not documents or not distances:
        if summary_mode:
            return {
                "answer": "I can summarize what has been read so far, but the current chapter/page context is still too limited to give a reliable answer yet.",
                "blocked": False,
                "best_distance": None
            }
        return {
            "answer": "I don't have enough context from what you've read so far to answer that — it may be revealed later in the book.",
            "blocked": True,
            "best_distance": None
        }

    if min(distances) > DISTANCE_THRESHOLD and not summary_mode:
        return {
            "answer": "I don't have enough context from what you've read so far to answer that — it may be revealed later in the book.",
            "blocked": True,
            "best_distance": min(distances)
        }

    # Layer 2: LLM double-checks relevance and answers or declines in its own words
    context = "\n\n".join(documents)
    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    answer = call_llm(SYSTEM_PROMPT, user_message)

    return {
        "answer": answer,
        "blocked": False,
        "best_distance": min(distances)
    }