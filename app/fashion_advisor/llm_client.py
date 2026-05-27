from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Generator

import requests
from flask import current_app

from app.services.llm_observability import llm_observability


@dataclass(slots=True)
class LLMResult:
    provider: str
    model: str
    content: str
    metadata: dict[str, Any] | None = None


class AdvisorLLMClient:
    """Lightweight LLM client for the fashion advisor."""

    def __init__(self) -> None:
        self.provider = current_app.config.get("ADVISOR_LLM_PROVIDER", "auto")
        self.model = current_app.config.get("ADVISOR_LLM_MODEL", "qwen2.5:3b")
        self.ollama_host = current_app.config.get("ADVISOR_OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.openai_api_key = current_app.config.get("ADVISOR_OPENAI_API_KEY", "")
        self.openai_base_url = current_app.config.get("ADVISOR_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    def health(self) -> dict[str, Any]:
        provider = self._select_provider()
        if provider == "openai":
            return {
                "provider": "openai-compatible",
                "model": self.model,
                "available": bool(self.openai_api_key),
            }

        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            response.raise_for_status()
            return {"provider": "ollama", "model": self.model, "available": True}
        except requests.RequestException:
            return {"provider": "ollama", "model": self.model, "available": False}

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> LLMResult | None:
        provider = self._select_provider()
        if provider == "openai":
            return self._generate_openai(system_prompt, user_prompt, temperature)
        return self._generate_ollama(system_prompt, user_prompt, temperature)

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict[str, Any] | None:
        result = self.generate_text(system_prompt, user_prompt, temperature=temperature)
        if result is None:
            return None
        payload = self._extract_json(result.content)
        if payload is None:
            return None
        return payload

    def generate_stream(self, system_prompt: str, user_prompt: str, temperature: float = 0.5) -> Generator[str, None, None]:
        provider = self._select_provider()
        provider_name = "openai-compatible" if provider == "openai" else "ollama"
        started_at = time.time()
        prompt_text = system_prompt + "\n" + user_prompt
        chunks: list[str] = []
        success = False

        try:
            if provider == "openai":
                iterator = self._generate_openai_stream(system_prompt, user_prompt, temperature)
            else:
                iterator = self._generate_ollama_stream(system_prompt, user_prompt, temperature)

            for token in iterator:
                chunks.append(token)
                yield token
            success = True
        finally:
            llm_observability.record(
                provider=provider_name,
                model=self.model,
                started_at=started_at,
                prompt_text=prompt_text,
                response_text="".join(chunks),
                success=success,
            )

    def _select_provider(self) -> str:
        if self.provider in {"openai", "ollama"}:
            return self.provider
        if self.openai_api_key:
            return "openai"
        return "ollama"

    def _generate_ollama(self, system_prompt: str, user_prompt: str, temperature: float) -> LLMResult | None:
        started_at = time.time()
        prompt_text = system_prompt + "\n" + user_prompt
        try:
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "options": {"temperature": temperature},
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "").strip()
            if not content:
                return None
            metadata = llm_observability.record(
                provider="ollama",
                model=self.model,
                started_at=started_at,
                prompt_text=prompt_text,
                response_text=content,
                success=True,
            )
            return LLMResult(provider="ollama", model=self.model, content=content, metadata=metadata)
        except requests.RequestException:
            llm_observability.record(
                provider="ollama",
                model=self.model,
                started_at=started_at,
                prompt_text=prompt_text,
                response_text="",
                success=False,
            )
            return None

    def _generate_openai(self, system_prompt: str, user_prompt: str, temperature: float) -> LLMResult | None:
        started_at = time.time()
        prompt_text = system_prompt + "\n" + user_prompt
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            if not content:
                return None
            metadata = llm_observability.record(
                provider="openai-compatible",
                model=self.model,
                started_at=started_at,
                prompt_text=prompt_text,
                response_text=content,
                success=True,
            )
            return LLMResult(provider="openai-compatible", model=self.model, content=content, metadata=metadata)
        except (requests.RequestException, KeyError, IndexError, TypeError):
            llm_observability.record(
                provider="openai-compatible",
                model=self.model,
                started_at=started_at,
                prompt_text=prompt_text,
                response_text="",
                success=False,
            )
            return None

    def _generate_ollama_stream(self, system_prompt: str, user_prompt: str, temperature: float) -> Generator[str, None, None]:
        try:
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.model,
                    "stream": True,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "options": {"temperature": temperature},
                },
                stream=True,
                timeout=60,
            )
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done", False):
                    break
        except requests.RequestException:
            return

    def _generate_openai_stream(self, system_prompt: str, user_prompt: str, temperature: float) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                stream=True,
                timeout=60,
            )
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
        except (requests.RequestException, KeyError, IndexError, TypeError):
            return

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any] | None:
        if not content:
            return None
        fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
        candidate = fenced_match.group(1) if fenced_match else content.strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = candidate[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None