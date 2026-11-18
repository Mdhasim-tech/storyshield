import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class EmptyAssistantResponseError(RuntimeError):
    pass


def call_llm(system_prompt, user_message):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        reasoning_effort="low",
        reasoning_format="hidden",
        max_completion_tokens=1024,
        temperature=0.3
    )

    if not response.choices:
        raise EmptyAssistantResponseError(
            "The assistant returned an empty response. Please try again."
        )

    content = response.choices[0].message.content
    if not isinstance(content, str) or not content.strip():
        raise EmptyAssistantResponseError(
            "The assistant returned an empty response. Please try again."
        )

    return content.strip()