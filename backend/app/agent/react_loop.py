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

SPOILER_PROMPT = """You are a reading companion. The reader has explicitly
allowed future plot details. Answer using the provided book context, including
future events when relevant. Do not invent details that aren't in the context."""


def is_summary_question(question):
    normalized = (question or "").lower()
    summary_triggers = [
        "what happens", "what happened", "what is happening", "summary",
        "summarize", "so far", "uptil now", "until now", "what has happened",
        "what happens so far", "what happened so far", "give me a summary",
        "brief summary", "overview"
    ]
    return any(trigger in normalized for trigger in summary_triggers)


def answer_question(book_id, question, chapter_order, page, allow_future=False):
    collection = get_book_collection(book_id)
    summary_mode = is_summary_question(question)
    results = get_safe_chunks(
        collection,
        chapter_order,
        page,
        question,
        k=20 if summary_mode else 5,
        allow_future=allow_future
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

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
            "answer": (
                "I couldn't find enough relevant information in the indexed book text to answer that."
                if allow_future else
                "I don't have enough context from what you've read so far to answer that — it may be revealed later in the book."
            ),
            "blocked": not allow_future,
            "best_distance": None
        }

    if min(distances) > DISTANCE_THRESHOLD and not summary_mode and not allow_future:
        return {
            "answer": "I don't have enough context from what you've read so far to answer that — it may be revealed later in the book.",
            "blocked": True,
            "best_distance": min(distances)
        }

    # Layer 2: LLM double-checks relevance and answers or declines in its own words
    context = "\n\n".join(documents)
    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    system_prompt = SPOILER_PROMPT if allow_future else SYSTEM_PROMPT
    answer = call_llm(system_prompt, user_message)

    return {
        "answer": answer,
        "blocked": False,
        "best_distance": min(distances)
    }