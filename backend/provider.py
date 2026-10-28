"""Small Nebius chat-completions adapter. Credentials never enter prompts/traces."""

import os
from urllib.parse import urlsplit

import httpx


class ProviderError(RuntimeError):
    pass


class ProviderNotConfigured(ProviderError):
    pass


def provider_status():
    missing = [name for name in ("NEBIUS_API_KEY", "NEBIUS_MODEL") if not os.getenv(name, "").strip()]
    return {"provider": "nebius", "live_configured": not missing, "missing_variables": missing,
            "model": os.getenv("NEBIUS_MODEL") or None, "demo_available": True}


class NebiusModel:
    provider = "nebius"

    def __init__(self):
        status = provider_status()
        if not status["live_configured"]:
            raise ProviderNotConfigured("Set NEBIUS_API_KEY and NEBIUS_MODEL to use live mode")
        self.model = status["model"]
        self._key = os.environ["NEBIUS_API_KEY"].strip()
        base = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1").rstrip("/")
        try:
            parsed = urlsplit(base)
            httpx.URL(base)
            parsed.port
        except (ValueError, httpx.InvalidURL):
            raise ProviderNotConfigured("NEBIUS_BASE_URL is not a valid HTTPS API base URL") from None
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ProviderNotConfigured("NEBIUS_BASE_URL must be an HTTPS API base URL without credentials, query, or fragment")
        self._url = base + "/chat/completions"

    def complete(self, messages, tools):
        monetary_instruction = (
            " All monetary amounts and tool arguments ending in _cents are integer USD cents, not dollars. "
            "100 cents = 1 USD; 1000000 cents = 10000 USD, not one million dollars. "
            "Keep public rationales qualitative: do not quote numeric monetary amounts in rationale fields. "
            "The backend displays exact verified amounts separately. Never invent financial facts.")
        prepared = [dict(message) for message in messages]
        for message in prepared:
            if message.get("role") == "system":
                message["content"] = (message.get("content") or "") + monetary_instruction
                break
        else:
            prepared.insert(0, {"role": "system", "content": monetary_instruction.strip()})
        payload = {"model": self.model, "messages": prepared, "tools": tools,
                   "tool_choice": "required", "temperature": 0.2, "max_tokens": 4096}
        if "nemotron" in self.model.lower():
            # Nemotron otherwise spends the bounded output on hidden thinking
            # before it reaches a function call. Public tool traces remain intact.
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        try:
            with httpx.Client(timeout=60, trust_env=False, follow_redirects=False) as client:
                response = client.post(self._url, headers={"Authorization": f"Bearer {self._key}"},
                                       json=payload)
                response.raise_for_status()
                message = response.json()["choices"][0]["message"]
                if not isinstance(message, dict) or not message.get("tool_calls"):
                    raise ProviderError("Model returned no function calls; check tool support and output/reasoning settings")
                # Do not retain hidden reasoning, provider metadata, or arbitrary fields.
                return {"role": "assistant", "content": message.get("content"), "tool_calls": message["tool_calls"]}
        except httpx.HTTPStatusError as error:
            raise ProviderError(f"Nebius request failed with HTTP {error.response.status_code}; check model access and configuration") from None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            raise ProviderError("Nebius timed out, could not be reached, or returned an invalid response") from None
