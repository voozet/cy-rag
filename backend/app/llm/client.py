import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 1500

_openrouter_client = (
    OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.openrouter_timeout,
        max_retries=1,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": settings.app_name,
        },
    )
    if settings.openrouter_api_key
    else None
)

_hf_client = (
    OpenAI(
        api_key=settings.hf_api_key,
        base_url=settings.hf_base_url,
        timeout=settings.hf_timeout,
        max_retries=1,
    )
    if settings.hf_api_key
    else None
)


def chat(system: str, user: str, *, json_mode: bool = False) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    kwargs = {
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": DEFAULT_MAX_TOKENS,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    errors: list[str] = []

    if _openrouter_client and settings.openrouter_model:
        try:
            logger.info("Routing request to OpenRouter model: %s", settings.openrouter_model)
            response = _openrouter_client.chat.completions.create(
                model=settings.openrouter_model,
                **kwargs,
            )
            content = response.choices[0].message.content
            if content:
                logger.info("OpenRouter request successful")
                return content
            raise ValueError("OpenRouter returned empty response")
        except Exception as e:
            logger.warning("OpenRouter failed: %s", e)
            errors.append(f"OpenRouter ({settings.openrouter_model}): {e}")

    if _hf_client:
        try:
            logger.info("Routing request to Hugging Face model: %s", settings.hf_model)
            hf_kwargs = dict(kwargs)
            try:
                response = _hf_client.chat.completions.create(
                    model=settings.hf_model,
                    **hf_kwargs,
                )
            except Exception as hf_err:
                if json_mode and "response_format" in str(hf_err).lower():
                    logger.info("Hugging Face rejected response_format; retrying without it")
                    hf_kwargs.pop("response_format", None)
                    response = _hf_client.chat.completions.create(
                        model=settings.hf_model,
                        **hf_kwargs,
                    )
                else:
                    raise hf_err

            content = response.choices[0].message.content
            if content:
                logger.info("Hugging Face request successful")
                return content
            raise ValueError("Hugging Face returned empty response")
        except Exception as e:
            logger.error("Hugging Face failed: %s", e)
            errors.append(f"Hugging Face ({settings.hf_model}): {e}")

    logger.critical("All LLM providers failed")
    raise RuntimeError("All LLM providers failed: " + " | ".join(errors))