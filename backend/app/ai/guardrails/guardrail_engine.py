"""
Guardrail Engine for Phase 12.7B AI Gateway.
Runs all validators against each AI response before returning to caller.
"""
import uuid
import json
import re
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.ai.guardrails.validators import (
    BaseValidator, ValidationResult, GuardrailResult
)
from app.database.mongodb.collections.ai_gateway_extended import GuardrailLogDocument

logger = logging.getLogger("backend.ai.guardrails.engine")

# ─── Individual Validators ─────────────────────────────────────────────────────

class JSONValidator(BaseValidator):
    name = "json_validator"

    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        if not config.get("require_json", False):
            return ValidationResult(validator_name=self.name, passed=True, message="JSON not required")
        try:
            json.loads(response_text.strip())
            return ValidationResult(validator_name=self.name, passed=True, score=1.0)
        except json.JSONDecodeError as e:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.0,
                flags=["invalid_json"], message=str(e)
            )


class PIIDetector(BaseValidator):
    name = "pii_detector"

    PII_PATTERNS = [
        (r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "email", re.IGNORECASE),
        (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone_number", 0),
        (r"\b\d{3}-\d{2}-\d{4}\b", "ssn", 0),
        (r"\b4[0-9]{12}(?:[0-9]{3})?\b", "credit_card_visa", 0),
    ]

    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        if not config.get("detect_pii", True):
            return ValidationResult(validator_name=self.name, passed=True, message="PII detection disabled")
        found = []
        for pattern, label, flags in self.PII_PATTERNS:
            if re.search(pattern, response_text, flags):
                found.append(label)
        if found:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.0,
                flags=[f"pii:{t}" for t in found],
                message=f"PII detected: {found}",
                details={"pii_types": found}
            )
        return ValidationResult(validator_name=self.name, passed=True, score=1.0)


class ProfanityDetector(BaseValidator):
    name = "profanity_detector"

    # Configurable via config["blocked_words"] list
    DEFAULT_BLOCKED = {"damn", "hell", "crap", "idiot", "moron"}

    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        if not config.get("detect_profanity", True):
            return ValidationResult(validator_name=self.name, passed=True, message="Profanity detection disabled")
        blocked = set(config.get("blocked_words", [])) | self.DEFAULT_BLOCKED
        words = set(re.sub(r"[^\w\s]", "", response_text.lower()).split())
        found = words & blocked
        if found:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.0,
                flags=["profanity_detected"],
                message=f"Profanity found: {list(found)[:5]}"
            )
        return ValidationResult(validator_name=self.name, passed=True, score=1.0)


class LengthValidator(BaseValidator):
    name = "length_validator"

    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        length = len(response_text)
        min_len = config.get("min_length", 0)
        max_len = config.get("max_length", 100000)
        if length < min_len:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.0,
                flags=["response_too_short"],
                message=f"Response length {length} < min {min_len}",
                details={"length": length, "min": min_len}
            )
        if length > max_len:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.5,
                flags=["response_too_long"],
                message=f"Response length {length} > max {max_len}",
                details={"length": length, "max": max_len}
            )
        return ValidationResult(validator_name=self.name, passed=True, score=1.0, details={"length": length})


class HallucinationChecker(BaseValidator):
    """
    Heuristic hallucination risk scorer.
    Checks for high-risk phrases that suggest unsupported claims.
    Production systems should use a dedicated fact-verification LLM call.
    """
    name = "hallucination_checker"

    HIGH_RISK_PATTERNS = [
        r"\baccording to .{0,30}study\b",
        r"\bproven by science\b",
        r"\bscientists have confirmed\b",
        r"\bI am 100% certain\b",
        r"\bguaranteed fact\b",
        r"\bstatistically proven\b",
    ]

    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        if not config.get("check_hallucination", True):
            return ValidationResult(validator_name=self.name, passed=True, score=1.0)
        risk_count = sum(
            1 for p in self.HIGH_RISK_PATTERNS
            if re.search(p, response_text, re.IGNORECASE)
        )
        score = max(0.0, 1.0 - (risk_count * 0.25))
        flags = ["hallucination_risk"] if risk_count > 0 else []
        return ValidationResult(
            validator_name=self.name, passed=risk_count < 3,
            score=score, flags=flags,
            details={"risk_count": risk_count},
            message=f"Hallucination risk patterns found: {risk_count}"
        )


class SchemaValidator(BaseValidator):
    """Validates that JSON response matches a provided JSON Schema definition."""
    name = "schema_validator"

    def validate(self, response_text: str, config: Dict[str, Any]) -> ValidationResult:
        required_schema = config.get("json_schema")
        if not required_schema:
            return ValidationResult(validator_name=self.name, passed=True, message="No schema configured")
        try:
            import jsonschema
            data = json.loads(response_text.strip())
            jsonschema.validate(instance=data, schema=required_schema)
            return ValidationResult(validator_name=self.name, passed=True, score=1.0)
        except json.JSONDecodeError:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.0,
                flags=["schema_invalid_json"]
            )
        except Exception as e:
            return ValidationResult(
                validator_name=self.name, passed=False, score=0.0,
                flags=["schema_violation"], message=str(e)[:200]
            )


# ─── Guardrail Engine ──────────────────────────────────────────────────────────

class GuardrailEngine:
    """
    Orchestrates all validators and aggregates their results.
    Every AI response must pass through this engine before returning to callers.
    """

    VALIDATORS: List[BaseValidator] = [
        JSONValidator(),
        PIIDetector(),
        ProfanityDetector(),
        LengthValidator(),
        HallucinationChecker(),
        SchemaValidator(),
    ]

    def validate(
        self,
        response_text: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> GuardrailResult:
        """
        Run all validators synchronously and return aggregated GuardrailResult.
        config can include: require_json, detect_pii, detect_profanity,
                            min_length, max_length, check_hallucination, json_schema
        """
        config = config or {}
        results: List[ValidationResult] = []

        for validator in self.VALIDATORS:
            try:
                result = validator.validate(response_text, config)
                results.append(result)
            except Exception as e:
                logger.warning(f"GuardrailEngine: Validator '{validator.name}' raised exception: {str(e)}")
                results.append(ValidationResult(
                    validator_name=validator.name, passed=True,
                    message=f"Validator error (non-blocking): {str(e)}"
                ))

        # Aggregate results
        all_flags = []
        for r in results:
            all_flags.extend(r.flags)

        overall_passed = all(r.passed for r in results)
        overall_confidence = sum(r.score for r in results) / len(results) if results else 1.0

        # Extract specific values from named validators
        pii_result = next((r for r in results if r.validator_name == "pii_detector"), None)
        profanity_result = next((r for r in results if r.validator_name == "profanity_detector"), None)
        json_result = next((r for r in results if r.validator_name == "json_validator"), None)
        length_result = next((r for r in results if r.validator_name == "length_validator"), None)
        hallucination_result = next((r for r in results if r.validator_name == "hallucination_checker"), None)
        schema_result = next((r for r in results if r.validator_name == "schema_validator"), None)

        return GuardrailResult(
            passed=overall_passed,
            overall_confidence=round(overall_confidence, 3),
            hallucination_score=round(1.0 - (hallucination_result.score if hallucination_result else 1.0), 3),
            pii_detected=pii_result is not None and not pii_result.passed,
            profanity_detected=profanity_result is not None and not profanity_result.passed,
            json_valid=json_result.passed if json_result else None,
            length_valid=length_result.passed if length_result else None,
            schema_valid=schema_result.passed if schema_result else None,
            flags=all_flags,
            validator_results=results,
            response_length=len(response_text),
        )

    async def validate_and_log(
        self,
        response_text: str,
        correlation_id: str,
        session_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> GuardrailResult:
        """Validate response and persist guardrail log to MongoDB."""
        result = self.validate(response_text, config)

        try:
            log = GuardrailLogDocument(
                log_id=f"grd_{uuid.uuid4().hex[:12]}",
                correlation_id=correlation_id,
                session_id=session_id,
                passed=result.passed,
                json_valid=result.json_valid,
                pii_detected=result.pii_detected,
                profanity_detected=result.profanity_detected,
                length_valid=result.length_valid,
                schema_valid=result.schema_valid,
                hallucination_score=result.hallucination_score,
                confidence_score=result.overall_confidence,
                flags=result.flags,
                details={v.validator_name: v.details for v in result.validator_results},
                response_length=result.response_length,
            )
            await log.insert()
        except Exception as e:
            logger.warning(f"GuardrailEngine: Failed to persist guardrail log: {str(e)}")

        return result


guardrail_engine = GuardrailEngine()
