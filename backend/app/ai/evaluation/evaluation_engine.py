"""
AI Evaluation Framework for Phase 12.7B AI Gateway.
Cross-provider prompt comparison with normalized scoring and leaderboard.
"""
import uuid
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.database.mongodb.collections.ai_gateway_extended import (
    EvaluationRunDocument,
    EvaluationScoreDocument,
)

logger = logging.getLogger("backend.ai.evaluation.engine")


class EvaluationEngine:
    """
    Orchestrates cross-provider/model evaluation runs.
    For a single prompt, executes completions across all target models concurrently,
    then scores and ranks the results.
    """

    async def run_evaluation(
        self,
        name: str,
        test_prompt: str,
        target_models: List[str],
        system_prompt: Optional[str] = None,
        initiated_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Run an evaluation across target models and return scored rankings.

        Args:
            name: Human-readable evaluation run name
            test_prompt: The prompt to test
            target_models: List of model IDs to test
            system_prompt: Optional system instruction
            initiated_by: User/agent that triggered this

        Returns:
            Dict with run_id, scores (ranked), and summary statistics
        """
        run_id = f"eval_{uuid.uuid4().hex[:12]}"

        # Create run record
        run_doc = EvaluationRunDocument(
            run_id=run_id,
            name=name,
            test_prompt=test_prompt,
            system_prompt=system_prompt,
            target_models=target_models,
            status="running",
            initiated_by=initiated_by,
        )
        await run_doc.insert()

        # Lazy import to avoid circular dependency
        from app.ai.gateway.gateway import ai_gateway
        from app.ai.registry.model_registry import ModelRegistry
        from app.ai.guardrails.guardrail_engine import guardrail_engine

        raw_results: List[Dict[str, Any]] = []

        async def run_single_model(model_id: str) -> None:
            model_info = ModelRegistry.get_model_info(model_id)
            if not model_info:
                logger.warning(f"EvaluationEngine: Unknown model '{model_id}', skipping.")
                return

            provider = model_info["provider"]
            start_ts = datetime.now(timezone.utc).timestamp()

            try:
                result = await ai_gateway.generate_completion(
                    prompt=test_prompt,
                    system_prompt=system_prompt or "",
                    provider=provider,
                    model=model_id,
                    bypass_cache=True,
                    correlation_id=f"{run_id}_{model_id}",
                )
                latency = (datetime.now(timezone.utc).timestamp() - start_ts) * 1000
                response_text = result.get("response", "")

                # Quality score heuristic
                quality_score = self._compute_quality_score(response_text, test_prompt)

                # JSON validity
                json_valid = self._check_json_valid(response_text)

                # Guardrail check
                guardrail_result = guardrail_engine.validate(response_text)
                guardrail_passed = guardrail_result.passed
                hallucination_score = guardrail_result.hallucination_score

                raw_results.append({
                    "model_id": model_id,
                    "provider": provider,
                    "response_text": response_text,
                    "latency_ms": latency,
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "estimated_cost": result.get("cost", 0.0),
                    "json_valid": json_valid,
                    "quality_score": quality_score,
                    "hallucination_score": hallucination_score,
                    "guardrail_passed": guardrail_passed,
                })

            except Exception as e:
                logger.warning(f"EvaluationEngine: Model '{model_id}' failed: {str(e)}")
                raw_results.append({
                    "model_id": model_id,
                    "provider": model_info.get("provider", "unknown"),
                    "response_text": f"ERROR: {str(e)[:200]}",
                    "latency_ms": 99999,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "estimated_cost": 0.0,
                    "json_valid": False,
                    "quality_score": 0.0,
                    "hallucination_score": 1.0,
                    "guardrail_passed": False,
                })

        # Execute all models concurrently
        await asyncio.gather(*[run_single_model(m) for m in target_models], return_exceptions=True)

        # Score and rank
        scored = self._score_results(raw_results)
        scores_docs = []
        for rank, item in enumerate(scored, start=1):
            score_doc = EvaluationScoreDocument(
                score_id=f"escore_{uuid.uuid4().hex[:12]}",
                run_id=run_id,
                provider=item["provider"],
                model=item["model_id"],
                response_text=item["response_text"][:2000],
                latency_ms=item["latency_ms"],
                prompt_tokens=item["prompt_tokens"],
                completion_tokens=item["completion_tokens"],
                estimated_cost=item["estimated_cost"],
                json_valid=item["json_valid"],
                quality_score=item["quality_score"],
                hallucination_score=item["hallucination_score"],
                guardrail_passed=item["guardrail_passed"],
                overall_score=item["overall_score"],
                rank=rank,
            )
            await score_doc.insert()
            scores_docs.append(score_doc)

        # Mark run complete
        run_doc.status = "completed"
        run_doc.completed_at = datetime.now(timezone.utc)
        await run_doc.save()

        return {
            "run_id": run_id,
            "name": name,
            "test_prompt": test_prompt,
            "total_models": len(target_models),
            "completed_models": len(raw_results),
            "rankings": scored,
        }

    def _compute_quality_score(self, response_text: str, prompt: str) -> float:
        """
        Heuristic quality score based on:
        - Response length relative to prompt
        - Keyword overlap with prompt
        """
        if not response_text:
            return 0.0
        length_score = min(1.0, len(response_text) / max(len(prompt) * 3, 300))
        prompt_words = set(prompt.lower().split())
        response_words = set(response_text.lower().split())
        overlap = len(prompt_words & response_words) / max(len(prompt_words), 1)
        return round((length_score * 0.6 + min(overlap, 1.0) * 0.4), 3)

    def _check_json_valid(self, text: str) -> bool:
        try:
            json.loads(text.strip())
            return True
        except Exception:
            return False

    def _score_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compute composite normalized scores and rank results."""
        if not results:
            return []

        max_latency = max(r["latency_ms"] for r in results) or 1
        max_cost = max(r["estimated_cost"] for r in results) or 0.001

        for r in results:
            latency_norm = 1.0 - (r["latency_ms"] / max_latency)
            cost_norm = 1.0 - (r["estimated_cost"] / max_cost)
            quality = r["quality_score"]
            json_bonus = 0.1 if r["json_valid"] else 0.0
            guardrail_bonus = 0.1 if r["guardrail_passed"] else -0.2
            hallucination_penalty = r["hallucination_score"] * 0.3

            overall = (
                quality * 0.35
                + latency_norm * 0.20
                + cost_norm * 0.15
                + json_bonus
                + guardrail_bonus
                - hallucination_penalty
            )
            r["overall_score"] = round(max(0.0, min(1.0, overall)), 4)

        return sorted(results, key=lambda x: x["overall_score"], reverse=True)

    async def get_runs(self, limit: int = 20) -> List[EvaluationRunDocument]:
        """Return recent evaluation runs."""
        return await EvaluationRunDocument.find_all().sort("-started_at").limit(limit).to_list()

    async def get_run_scores(self, run_id: str) -> List[EvaluationScoreDocument]:
        """Return scores for a specific evaluation run."""
        return await EvaluationScoreDocument.find(
            EvaluationScoreDocument.run_id == run_id
        ).sort("rank").to_list()


evaluation_engine = EvaluationEngine()
