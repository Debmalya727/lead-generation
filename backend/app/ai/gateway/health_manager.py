"""
Enterprise Provider Health Manager for Phase 12.7 Enterprise AI Platform.
Continuously monitors latency, uptime, success rate, quota, failures, timeouts,
429 errors, 500 errors, and calculates rolling statistics per provider.
"""
import time
import logging
from typing import Dict, Any, List
from collections import deque

logger = logging.getLogger("backend.ai.gateway.health_manager")


class ProviderHealthRecord:
    def __init__(self, provider: str):
        self.provider = provider
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.consecutive_failures = 0
        self.timeout_count = 0
        self.rate_limit_429_count = 0
        self.server_error_500_count = 0
        self.total_tokens_processed = 0
        self.latencies_ms = deque(maxlen=100)  # Rolling window of last 100 requests
        self.last_status_change = time.time()
        self.status = "HEALTHY"  # HEALTHY | DEGRADED | UNAVAILABLE

    def record_success(self, latency_ms: float, tokens: int = 0) -> None:
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.latencies_ms.append(latency_ms)
        self.total_tokens_processed += tokens
        self._reevaluate_status()

    def record_failure(self, error: Exception, latency_ms: float = 0.0) -> None:
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        if latency_ms > 0:
            self.latencies_ms.append(latency_ms)

        err_str = str(error).lower()
        if "timeout" in err_str:
            self.timeout_count += 1
        if "429" in err_str or "rate limit" in err_str:
            self.rate_limit_429_count += 1
        if "500" in err_str or "502" in err_str or "503" in err_str:
            self.server_error_500_count += 1

        self._reevaluate_status()

    def _reevaluate_status(self) -> None:
        prev_status = self.status
        success_rate = (self.successful_requests / max(1, self.total_requests)) * 100

        if self.consecutive_failures >= 5 or success_rate < 30:
            self.status = "UNAVAILABLE"
        elif self.consecutive_failures >= 2 or success_rate < 80:
            self.status = "DEGRADED"
        else:
            self.status = "HEALTHY"

        if prev_status != self.status:
            self.last_status_change = time.time()
            logger.warning(f"[ProviderHealthManager] Provider '{self.provider}' status changed: {prev_status} -> {self.status}")

    def get_stats(self) -> Dict[str, Any]:
        lats = list(self.latencies_ms)
        avg_latency = sum(lats) / max(1, len(lats)) if lats else 0.0
        sorted_lats = sorted(lats)
        p95_latency = sorted_lats[int(len(sorted_lats) * 0.95)] if sorted_lats else 0.0
        success_rate = (self.successful_requests / max(1, self.total_requests)) * 100 if self.total_requests > 0 else 100.0

        return {
            "provider": self.provider,
            "status": self.status,
            "availability": self.status != "UNAVAILABLE",
            "uptime_percent": round(success_rate, 2),
            "success_rate_percent": round(success_rate, 2),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "consecutive_failures": self.consecutive_failures,
            "timeout_count": self.timeout_count,
            "rate_limit_429_count": self.rate_limit_429_count,
            "server_error_500_count": self.server_error_500_count,
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "total_tokens_processed": self.total_tokens_processed,
        }


class ProviderHealthManager:
    """Manager tracking rolling statistics and health across all AI providers."""

    def __init__(self):
        self._records: Dict[str, ProviderHealthRecord] = {}

    def get_record(self, provider: str) -> ProviderHealthRecord:
        key = provider.lower().strip()
        if key not in self._records:
            self._records[key] = ProviderHealthRecord(key)
        return self._records[key]

    def record_success(self, provider: str, latency_ms: float, tokens: int = 0) -> None:
        rec = self.get_record(provider)
        rec.record_success(latency_ms, tokens)

    def record_failure(self, provider: str, error: Exception, latency_ms: float = 0.0) -> None:
        rec = self.get_record(provider)
        rec.record_failure(error, latency_ms)

    def get_health(self, provider: str) -> Dict[str, Any]:
        return self.get_record(provider).get_stats()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        providers = ["gemini", "groq", "mistral", "openrouter", "openai", "claude", "deepseek", "ollama", "vllm"]
        for p in providers:
            self.get_record(p)
        return {p: rec.get_stats() for p, rec in self._records.items()}


provider_health_manager = ProviderHealthManager()
