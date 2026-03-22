from __future__ import annotations

import os
import time

import httpx

from literature_screening.core.exceptions import ModelRequestError
from literature_screening.core.models import ModelConfig


class ChatCompletionClient:
    def __init__(self, config: ModelConfig, timeout_seconds: int) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self._last_request_finished_at = 0.0

    def chat(self, prompt: str) -> str:
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise ModelRequestError(f"Missing API key in environment variable: {self.config.api_key_env}")

        self._respect_min_request_interval()

        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict structured-output assistant. When the user asks for JSON, reply with valid JSON only and no extra prose.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if self.config.provider == "deepseek":
            payload["response_format"] = {"type": "json_object"}

        url = f"{self.config.api_base_url.rstrip('/')}/chat/completions"

        try:
            with self._client() as client:
                response = client.post(url, headers=self._build_headers(api_key), json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            response_text = exc.response.text
            provider_name = self.config.provider
            raise ModelRequestError(
                f"{provider_name} API request failed with status {exc.response.status_code}: {response_text}"
            ) from exc
        except httpx.HTTPError as exc:
            provider_name = self.config.provider
            raise ModelRequestError(f"{provider_name} API request failed: {exc}") from exc

        data = response.json()
        self._last_request_finished_at = time.monotonic()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelRequestError(f"{self.config.provider} API response did not contain a valid assistant message.") from exc

    def _build_headers(self, api_key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout_seconds)

    def _respect_min_request_interval(self) -> None:
        min_interval = self.config.min_request_interval_seconds
        if min_interval <= 0:
            return

        elapsed = time.monotonic() - self._last_request_finished_at
        if 0 < elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    @staticmethod
    def extract_retry_after_seconds(error: Exception) -> int | None:
        if not isinstance(error, ModelRequestError):
            return None

        text = str(error)
        if "status 429" not in text:
            if "incomplete chunked read" in text or "peer closed connection" in text:
                return 10
            return None
        if "engine_overloaded_error" in text or "overloaded" in text:
            return 30
        return 20
