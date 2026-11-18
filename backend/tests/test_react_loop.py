from app.agent import react_loop


def test_spoiler_opt_in_uses_future_context_and_prompt(monkeypatch):
    seen = {}

    monkeypatch.setattr(react_loop, "get_book_collection", lambda book_id: object())

    def fake_get_safe_chunks(collection, chapter_order, page, question, **kwargs):
        seen["allow_future"] = kwargs["allow_future"]
        return {"documents": [["The final chapter reveals the mystery."]], "distances": [[0.4]]}

    def fake_call_llm(system_prompt, user_message):
        seen["system_prompt"] = system_prompt
        seen["user_message"] = user_message
        return "The mystery is revealed in the final chapter."

    monkeypatch.setattr(react_loop, "get_safe_chunks", fake_get_safe_chunks)
    monkeypatch.setattr(react_loop, "call_llm", fake_call_llm)

    result = react_loop.answer_question(
        book_id="book-1",
        question="What is the mystery?",
        chapter_order=1,
        page=1,
        allow_future=True,
    )

    assert seen["allow_future"] is True
    assert seen["system_prompt"] == react_loop.SPOILER_PROMPT
    assert "The final chapter reveals the mystery." in seen["user_message"]
    assert result["answer"] == "The mystery is revealed in the final chapter."
