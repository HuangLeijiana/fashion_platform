from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LLMTrace:
    provider: str
    model: str
    latency_ms: int
    prompt_chars: int
    response_chars: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_total_tokens: int
    estimated_cost_usd: float
    success: bool
    timestamp: float


class LLMObservability:
    def __init__(self, log_path: str | None = None) -> None:
        self.log_path = Path(log_path or os.path.join('logs', 'llm_metrics.log'))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text) / 4))

    @staticmethod
    def estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
        if provider == 'openai-compatible':
            return round((input_tokens * 0.0000005) + (output_tokens * 0.0000015), 6)
        return 0.0

    def record(self, *, provider: str, model: str, started_at: float, prompt_text: str, response_text: str, success: bool) -> dict[str, Any]:
        latency_ms = int((time.time() - started_at) * 1000)
        input_tokens = self.estimate_tokens(prompt_text)
        output_tokens = self.estimate_tokens(response_text)
        trace = LLMTrace(
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            prompt_chars=len(prompt_text),
            response_chars=len(response_text),
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=self.estimate_cost(provider, input_tokens, output_tokens),
            success=success,
            timestamp=time.time(),
        )
        payload = asdict(trace)
        with self.log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')
        return payload


llm_observability = LLMObservability()