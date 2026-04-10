"""Async OpenRouter REST API client."""

from __future__ import annotations

import asyncio
import json
import logging
import time

import httpx

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Minimal async client for OpenRouter chat completions."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def complete(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request. Returns the assistant's content string."""
        client = await self._get_client()
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(3):
            try:
                resp = await client.post(url, json=payload)

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", 2 ** attempt))
                    logger.warning(f"Rate limited on {model}, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue

                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/3 failed for {model}: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"OpenRouter request failed after 3 attempts: {last_error}")

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
