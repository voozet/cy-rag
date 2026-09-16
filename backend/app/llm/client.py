from openai import OpenAI

from ..config import settings

_client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url) if settings.llm_api_key else None


def chat(system: str, user: str, *, json_mode: bool = False) -> str:
    if _client is None:
        raise RuntimeError("LLM_API_KEY is not configured")
    kwargs = {"model": settings.llm_model,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""
