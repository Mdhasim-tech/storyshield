from types import SimpleNamespace

import pytest

import app.agent.llm_client as llm_client


class FakeCompletions:
    def __init__(self, response):
        self.response = response
        self.options = None

    def create(self, **options):
        self.options = options
        return self.response


def test_call_llm_returns_final_text_with_reasoning_safe_options(monkeypatch):
    completions = FakeCompletions(
        SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  A clear answer.  "))]
        )
    )
    monkeypatch.setattr(
        llm_client,
        "client",
        SimpleNamespace(chat=SimpleNamespace(completions=completions)),
    )

    answer = llm_client.call_llm("system", "question")

    assert answer == "A clear answer."
    assert completions.options["max_completion_tokens"] == 1024
    assert completions.options["reasoning_effort"] == "low"
    assert completions.options["reasoning_format"] == "hidden"


@pytest.mark.parametrize(
    "choices",
    [
        [],
        [SimpleNamespace(message=SimpleNamespace(content=None))],
        [SimpleNamespace(message=SimpleNamespace(content="  "))],
    ],
)
def test_call_llm_rejects_empty_response(monkeypatch, choices):
    completions = FakeCompletions(SimpleNamespace(choices=choices))
    monkeypatch.setattr(
        llm_client,
        "client",
        SimpleNamespace(chat=SimpleNamespace(completions=completions)),
    )

    with pytest.raises(llm_client.EmptyAssistantResponseError, match="empty response"):
        llm_client.call_llm("system", "question")
