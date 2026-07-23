"""
ConsensusEngine for Multi-Agent Collaboration Engine.

Supports 5 Consensus Strategies:
1. highest_confidence: Pick proposal with highest confidence score
2. weighted_confidence: Compute weighted average or pick top weighted item
3. majority_vote: Frequency-based mode selection across agent proposals
4. llm_arbitration: Invoke LLM to synthesize conflicting proposals into a unified output
5. human_approval: Require human approval before resolving conflict

Persists consensus resolution documents into MongoDB agent_consensus collection.
"""
import uuid
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from app.ai.providers.factory import get_llm_provider
from app.database.mongodb.collections.agent_collaboration import AgentConsensusDocument

logger = logging.getLogger("backend.agents.collaboration.consensus.engine")


class ConsensusEngine:
    """Consensus Engine resolving conflicts and multi-agent proposals."""

    def __init__(self):
        self.llm_provider = get_llm_provider()

    async def resolve(
        self,
        job_id: str,
        topic: str,
        proposals: List[Dict[str, Any]],
        strategy: str = "highest_confidence",
        task_id: Optional[str] = None,
        is_conflict: bool = False,
        conflict_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a topic across proposals using the specified strategy.
        Proposals format: [{"agent": "research_agent", "proposal": {...}, "confidence": 85}, ...]
        """
        logger.info(f"ConsensusEngine resolving topic '{topic}' using strategy '{strategy}' ({len(proposals)} proposals)")

        if not proposals:
            return {"status": "failed", "reason": "No proposals supplied for consensus."}

        if strategy == "highest_confidence":
            resolved = self._highest_confidence_strategy(proposals)
        elif strategy == "weighted_confidence":
            resolved = self._weighted_confidence_strategy(proposals)
        elif strategy == "majority_vote":
            resolved = self._majority_vote_strategy(proposals)
        elif strategy == "llm_arbitration":
            resolved = await self._llm_arbitration_strategy(topic, proposals)
        elif strategy == "human_approval":
            resolved = {
                "resolved_output": {"status": "paused_for_human_approval", "topic": topic},
                "winning_agent": None,
                "confidence": 50,
            }
        else:
            resolved = self._highest_confidence_strategy(proposals)

        consensus_id = f"cons_{uuid.uuid4().hex[:12]}"
        output_payload = resolved.get("resolved_output", {})
        winning_agent = resolved.get("winning_agent")
        confidence = resolved.get("confidence", 85)

        # Persist consensus decision to MongoDB
        try:
            doc = AgentConsensusDocument(
                consensus_id=consensus_id,
                job_id=job_id,
                task_id=task_id,
                topic=topic,
                proposals=proposals,
                strategy_used=strategy,
                resolved_output=output_payload,
                winning_agent=winning_agent,
                confidence=confidence,
                is_conflict=is_conflict,
                conflict_details=conflict_details,
                resolved_at=datetime.now(timezone.utc),
            )
            await doc.insert()
            logger.info(f"ConsensusEngine persisted decision '{consensus_id}' for topic '{topic}' (winning agent: {winning_agent})")
        except Exception as e:
            logger.warning(f"Failed to persist AgentConsensusDocument: {str(e)}")

        return {
            "consensus_id": consensus_id,
            "job_id": job_id,
            "topic": topic,
            "strategy_used": strategy,
            "resolved_output": output_payload,
            "winning_agent": winning_agent,
            "confidence": confidence,
            "is_conflict": is_conflict,
        }

    def _highest_confidence_strategy(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pick proposal with highest integer confidence."""
        sorted_props = sorted(proposals, key=lambda p: p.get("confidence", 0), reverse=True)
        winner = sorted_props[0]
        return {
            "resolved_output": winner.get("proposal", {}),
            "winning_agent": winner.get("agent"),
            "confidence": winner.get("confidence", 85),
        }

    def _weighted_confidence_strategy(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute top weighted proposal."""
        total_conf = sum(p.get("confidence", 50) for p in proposals)
        sorted_props = sorted(proposals, key=lambda p: p.get("confidence", 0), reverse=True)
        winner = sorted_props[0]
        avg_conf = round(total_conf / len(proposals)) if proposals else 80
        return {
            "resolved_output": winner.get("proposal", {}),
            "winning_agent": winner.get("agent"),
            "confidence": avg_conf,
        }

    def _majority_vote_strategy(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select majority choice."""
        from collections import Counter
        votes = [json.dumps(p.get("proposal", {}), sort_keys=True) for p in proposals]
        counts = Counter(votes)
        most_common_json, vote_count = counts.most_common(1)[0]
        parsed_output = json.loads(most_common_json)

        winning_agent = next((p.get("agent") for p in proposals if json.dumps(p.get("proposal", {}), sort_keys=True) == most_common_json), None)
        confidence = int((vote_count / len(proposals)) * 100)

        return {
            "resolved_output": parsed_output,
            "winning_agent": winning_agent,
            "confidence": confidence,
        }

    async def _llm_arbitration_strategy(self, topic: str, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to arbitrate conflicting proposals."""
        prompt = f"""
YOU ARE AN AI CONSENSUS ARBITRATOR INSIDE LEADFORGEAI.
Synthesize the following conflicting proposals for topic '{topic}' into a single, unified, accurate output.

PROPOSALS:
{json.dumps(proposals, indent=2, default=str)}

Return ONLY valid JSON representing the resolved output. Include a "confidence" field (0-100) and "arbitration_notes" field.
"""
        try:
            raw = await self.llm_provider.complete(prompt=prompt, system_prompt="You are a strict, impartial AI consensus arbitrator.")
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            return {
                "resolved_output": parsed,
                "winning_agent": "llm_arbitrator",
                "confidence": parsed.get("confidence", 85),
            }
        except Exception as e:
            logger.warning(f"LLM arbitration failed, falling back to highest confidence: {str(e)}")
            return self._highest_confidence_strategy(proposals)
