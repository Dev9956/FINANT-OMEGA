"""FININT OMEGA — Guardrails checker for input/output validation."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """A single validation issue."""

    rule: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.WARNING


class ValidationResult(BaseModel):
    """Result of a guardrails check."""

    passed: bool = True
    issues: list[ValidationIssue] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def add_issue(self, rule: str, message: str, severity: ValidationSeverity = ValidationSeverity.WARNING) -> None:
        self.issues.append(ValidationIssue(rule=rule, message=message, severity=severity))
        if severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
            self.passed = False


class GuardrailsChecker:
    """Validate inputs and outputs against configurable guardrails."""

    def __init__(self, max_length: int = 10000, blocked_patterns: list[str] | None = None) -> None:
        self._max_length = max_length
        self._blocked_patterns = [re.compile(p, re.IGNORECASE) for p in (blocked_patterns or [])]
        self._input_rules: list[callable] = []
        self._output_rules: list[callable] = []

    def add_input_rule(self, rule_fn: callable) -> None:
        self._input_rules.append(rule_fn)

    def add_output_rule(self, rule_fn: callable) -> None:
        self._output_rules.append(rule_fn)

    def check_input(self, text: str, context: dict | None = None) -> ValidationResult:
        result = ValidationResult()
        if not text or not text.strip():
            result.add_issue("empty_input", "Input is empty", ValidationSeverity.ERROR)
            return result
        if len(text) > self._max_length:
            result.add_issue("length", f"Input exceeds max length of {self._max_length}", ValidationSeverity.WARNING)
        for pattern in self._blocked_patterns:
            if pattern.search(text):
                result.add_issue("blocked_content", "Input contains blocked content", ValidationSeverity.CRITICAL)
                break
        for rule in self._input_rules:
            try:
                rule(text, context, result)
            except Exception as e:
                result.add_issue("rule_error", f"Rule failed: {e}", ValidationSeverity.WARNING)
        return result

    def check_output(self, text: str, context: dict | None = None) -> ValidationResult:
        result = ValidationResult()
        if not text or not text.strip():
            result.add_issue("empty_output", "Output is empty", ValidationSeverity.WARNING)
            return result
        for pattern in self._blocked_patterns:
            if pattern.search(text):
                result.add_issue("blocked_content", "Output contains blocked content", ValidationSeverity.CRITICAL)
                break
        for rule in self._output_rules:
            try:
                rule(text, context, result)
            except Exception as e:
                result.add_issue("rule_error", f"Rule failed: {e}", ValidationSeverity.WARNING)
        return result
