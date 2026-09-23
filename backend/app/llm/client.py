import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Primary Client (GapGPT / OpenAI compatible)
_primary_client = (
    OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    if settings.llm_api_key
    else None
)

# Fallback Client (OpenRouter)
_fallback_client = (
    OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": settings.app_name,
        },
    )
    if settings.openrouter_api_key
    else None
)

def chat(system: str, user: str, *, json_mode: bool = False) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    kwargs = {
        "messages": messages,
        "temperature": 0,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    # 1. Try Primary LLM (GapGPT)
    if _primary_client:
        try:
            response = _primary_client.chat.completions.create(
                model=settings.llm_model,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Primary LLM request failed: {e}. Attempting fallback...")
            if not settings.fallback_enabled or not _fallback_client:
                raise e
    elif not (_fallback_client and settings.fallback_enabled):
        raise RuntimeError("No valid LLM client configured (both Primary and OpenRouter keys are missing)")

    # 2. Try Fallback LLM (OpenRouter)
    if settings.fallback_enabled and _fallback_client:
        try:
            logger.info(f"Routing request to OpenRouter (model: {settings.openrouter_model})")
            response = _fallback_client.chat.completions.create(
                model=settings.openrouter_model,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as fallback_err:
            logger.error(f"Fallback to OpenRouter also failed: {fallback_err}")
            raise fallback_err

    raise RuntimeError("LLM request failed and no fallback available.")
