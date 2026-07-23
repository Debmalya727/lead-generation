"""
AI Execution Planner — TaskDecomposer breaking user requests into required capability steps.
"""
from typing import List, Dict, Any
import re
import logging

from app.ai.planner.schemas import TaskStepSpec

logger = logging.getLogger("backend.ai.planner.decomposer")


class TaskDecomposer:
    """Analyzes prompt text and decomposes it into capability-based workflow step specs."""

    def decompose(self, prompt: str) -> List[TaskStepSpec]:
        """Decompose prompt text into logical execution steps."""
        p_lower = prompt.lower()
        steps: List[TaskStepSpec] = []

        # Step 1: Prompt rendering node
        steps.append(TaskStepSpec(
            step_id="step_1_prompt",
            name="Render Input Prompt",
            capability="chat",
            node_type="PromptNode",
            config={"template": "{prompt}"},
        ))

        # Check keywords to detect required capabilities
        if any(w in p_lower for w in ["research", "analyze", "overview", "study", "deep dive"]):
            steps.append(TaskStepSpec(
                step_id="step_2_search",
                name="Perform Search & Retrieval",
                capability="research",
                node_type="SearchNode",
                dependencies=["step_1_prompt"],
            ))
            steps.append(TaskStepSpec(
                step_id="step_3_reasoning",
                name="Analyze & Synthesize Insights",
                capability="reasoning",
                node_type="ReasoningNode",
                dependencies=["step_2_search"],
            ))
            steps.append(TaskStepSpec(
                step_id="step_4_generation",
                name="Generate Comprehensive Summary",
                capability="summarization",
                node_type="GenerationNode",
                dependencies=["step_3_reasoning"],
            ))
        elif any(w in p_lower for w in ["score", "rank", "lead", "qualification"]):
            steps.append(TaskStepSpec(
                step_id="step_2_reasoning",
                name="Score & Qualify Lead Criteria",
                capability="reasoning",
                node_type="ReasoningNode",
                dependencies=["step_1_prompt"],
            ))
            steps.append(TaskStepSpec(
                step_id="step_3_json",
                name="Format Lead Score JSON Output",
                capability="json_generation",
                node_type="GenerationNode",
                dependencies=["step_2_reasoning"],
            ))
        else:
            # Default single generation step
            steps.append(TaskStepSpec(
                step_id="step_2_generation",
                name="Generate AI Response",
                capability="chat",
                node_type="GenerationNode",
                dependencies=["step_1_prompt"],
            ))

        # Standard safety & memory nodes
        last_step_id = steps[-1].step_id

        steps.append(TaskStepSpec(
            step_id="step_guardrail",
            name="Run Safety Guardrails",
            capability="chat",
            node_type="GuardrailNode",
            dependencies=[last_step_id],
        ))

        steps.append(TaskStepSpec(
            step_id="step_memory",
            name="Persist Artifacts to Memory",
            capability="chat",
            node_type="MemoryNode",
            dependencies=["step_guardrail"],
        ))

        steps.append(TaskStepSpec(
            step_id="step_output",
            name="Finalize Workflow Output",
            capability="chat",
            node_type="OutputNode",
            dependencies=["step_memory"],
        ))

        return steps


task_decomposer = TaskDecomposer()
