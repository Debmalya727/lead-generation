"""
AI Guardrails — base Validator ABC and ValidationResult schema.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result from a single guardrail validator."""
    validator_name: str
    passed: bool
    score: float = 1.0           # 0.0-1.0 (higher is better / safer)
    flags: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


class GuardrailResult(BaseModel):
    """Aggregated result from the full guardrail pipeline."""
    passed: bool
    overall_confidence: float = 1.0
    hallucination_score: float = 0.0   # 0.0-1.0 (lower is better)
    pii_detected: bool = False
    profanity_detected: bool = False
    json_valid: Optional[bool] = None
    length_valid: Optional[bool] = None
    citations_valid: Optional[bool] = None
    schema_valid: Optional[bool] = None
    flags: List[str] = Field(default_factory=list)
    validator_results: List[ValidationResult] = Field(default_factory=list)
    response_length: int = 0


class BaseValidator(ABC):
    """Abstract base class for all guardrail validators."""

    name: str = "base"

    @abstractmethod
    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        """Validate response text against configured rules."""
        ...
