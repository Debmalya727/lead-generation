"""
Model Benchmark Registry for Phase 12.7B AI Gateway.
Defines benchmark suites and runs them across multiple providers.
"""
import uuid
import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.database.mongodb.collections.ai_gateway_extended import (
    ModelBenchmarkDocument,
    BenchmarkHistoryDocument,
)

logger = logging.getLogger("backend.ai.benchmarks.registry")


class BenchmarkRegistry:
    """Manages benchmark suite definitions."""

    async def create(
        self,
        name: str,
        test_prompts: List[str],
        target_providers: List[str],
        target_models: List[str],
        metrics: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> ModelBenchmarkDocument:
        """Create a new benchmark suite definition."""
        benchmark_id = f"bench_{uuid.uuid4().hex[:12]}"
        doc = ModelBenchmarkDocument(
            benchmark_id=benchmark_id,
            name=name,
            description=description,
            test_prompts=test_prompts,
            target_providers=target_providers,
            target_models=target_models,
            metrics=metrics or ["latency_ms", "tokens", "cost", "json_validity", "quality_score"],
        )
        await doc.insert()
        return doc

    async def list_all(self) -> List[ModelBenchmarkDocument]:
        """Return all benchmark suites."""
        return await ModelBenchmarkDocument.find_all().to_list()

    async def get(self, benchmark_id: str) -> Optional[ModelBenchmarkDocument]:
        """Get a specific benchmark by ID."""
        return await ModelBenchmarkDocument.find_one(
            ModelBenchmarkDocument.benchmark_id == benchmark_id
        )

    async def get_history(
        self,
        benchmark_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 50,
    ) -> List[BenchmarkHistoryDocument]:
        """Return benchmark run history with optional filters."""
        query = {}
        if benchmark_id:
            query[BenchmarkHistoryDocument.benchmark_id] = benchmark_id
        if provider:
            query[BenchmarkHistoryDocument.provider] = provider
        if model:
            query[BenchmarkHistoryDocument.model] = model

        return await BenchmarkHistoryDocument.find_all().sort("-run_at").limit(limit).to_list()

    async def get_leaderboard(self, benchmark_id: str) -> List[Dict[str, Any]]:
        """Compute model leaderboard for a given benchmark suite."""
        history = await BenchmarkHistoryDocument.find(
            BenchmarkHistoryDocument.benchmark_id == benchmark_id
        ).to_list()

        if not history:
            return []

        # Aggregate by provider/model
        aggregated: Dict[str, Dict[str, Any]] = {}
        for entry in history:
            key = f"{entry.provider}/{entry.model}"
            if key not in aggregated:
                aggregated[key] = {
                    "provider": entry.provider,
                    "model": entry.model,
                    "runs": 0,
                    "total_latency": 0.0,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_quality": 0.0,
                    "json_valid_count": 0,
                }
            agg = aggregated[key]
            agg["runs"] += 1
            agg["total_latency"] += entry.latency_ms
            agg["total_cost"] += entry.estimated_cost
            agg["total_tokens"] += entry.prompt_tokens + entry.completion_tokens
            agg["total_quality"] += entry.quality_score
            if entry.json_valid:
                agg["json_valid_count"] += 1

        # Compute averages and composite score
        leaderboard = []
        for key, agg in aggregated.items():
            runs = agg["runs"]
            avg_latency = agg["total_latency"] / runs
            avg_cost = agg["total_cost"] / runs
            avg_quality = agg["total_quality"] / runs
            json_rate = agg["json_valid_count"] / runs

            # Composite score (lower latency, lower cost, higher quality = better)
            # Normalize: quality (0-1), json_rate (0-1) are positive; latency/cost are negative
            # Simple formula: composite = 0.4*quality + 0.2*json_rate - 0.2*(latency/10000) - 0.2*(cost*100)
            composite = (
                0.4 * avg_quality
                + 0.2 * json_rate
                - min(0.2, 0.2 * (avg_latency / 10000))
                - min(0.2, 0.2 * (avg_cost * 100))
            )

            leaderboard.append({
                "provider": agg["provider"],
                "model": agg["model"],
                "runs": runs,
                "avg_latency_ms": round(avg_latency, 1),
                "avg_cost_usd": round(avg_cost, 6),
                "avg_quality_score": round(avg_quality, 3),
                "json_valid_rate": round(json_rate, 3),
                "composite_score": round(composite, 4),
            })

        return sorted(leaderboard, key=lambda x: x["composite_score"], reverse=True)


class BenchmarkRunner:
    """Executes benchmark suites across multiple providers concurrently."""

    async def run(
        self,
        benchmark_id: str,
        test_prompts: List[str],
        target_models: List[str],
    ) -> str:
        """Run all test prompts against all target models. Returns run_id."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        logger.info(f"BenchmarkRunner: Starting run '{run_id}' for benchmark '{benchmark_id}'")

        # Lazy import to avoid circular dependency
        from app.ai.gateway.gateway import ai_gateway
        from app.ai.registry.model_registry import ModelRegistry

        async def run_single(prompt: str, model_id: str) -> None:
            model_info = ModelRegistry.get_model_info(model_id)
            if not model_info:
                logger.warning(f"BenchmarkRunner: Unknown model '{model_id}', skipping.")
                return
            provider = model_info["provider"]
            start = datetime.now(timezone.utc).timestamp()
            try:
                result = await ai_gateway.generate_completion(
                    prompt=prompt,
                    provider=provider,
                    model=model_id,
                    bypass_cache=True,
                )
                latency = (datetime.now(timezone.utc).timestamp() - start) * 1000
                response_text = result.get("response", "")

                # Quality score: simple heuristic based on response length
                quality = min(1.0, len(response_text) / 500)

                # JSON validity check
                import json
                try:
                    json.loads(response_text)
                    json_valid = True
                except Exception:
                    json_valid = False

                record = BenchmarkHistoryDocument(
                    run_id=run_id,
                    benchmark_id=benchmark_id,
                    provider=provider,
                    model=model_id,
                    prompt=prompt,
                    response_text=response_text[:2000],
                    latency_ms=latency,
                    prompt_tokens=result.get("prompt_tokens", 0),
                    completion_tokens=result.get("completion_tokens", 0),
                    estimated_cost=result.get("cost", 0.0),
                    json_valid=json_valid,
                    quality_score=quality,
                )
                await record.insert()
            except Exception as e:
                logger.warning(f"BenchmarkRunner: Failed for model '{model_id}': {str(e)}")

        # Run all combinations concurrently
        tasks = []
        for prompt in test_prompts:
            for model_id in target_models:
                tasks.append(run_single(prompt, model_id))

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"BenchmarkRunner: Run '{run_id}' completed.")
        return run_id


benchmark_registry = BenchmarkRegistry()
benchmark_runner = BenchmarkRunner()
