"""FININT OMEGA — Real LLM integration verification.

Status: BLOCKED_BY_ENVIRONMENT

OPENAI_API_KEY is not set. Real LLM integration cannot be verified.
This script documents the verification requirements and the blocked status.
"""

from __future__ import annotations

import os

# Check environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
REAL_LLM_VERIFICATION = "BLOCKED_BY_ENVIRONMENT" if not OPENAI_API_KEY else "READY"


def get_status() -> dict:
    """Return current LLM verification status."""
    return {
        "status": REAL_LLM_VERIFICATION,
        "reason": "OPENAI_API_KEY not set" if not OPENAI_API_KEY else None,
        "requirement": "Set OPENAI_API_KEY environment variable to a valid OpenAI API key",
        "verification_checklist": [
            "question → planner → retrieval → tools → quant → evidence → LLM → grounded response → persistence",
            "no hardcoded agent output",
            "structured output",
            "citation/evidence grounding",
            "timeout",
            "retry",
            "error handling",
            "model metadata",
            "token/cost tracking",
        ],
    }


if __name__ == "__main__":
    status = get_status()
    print(f"REAL_LLM_VERIFICATION = {status['status']}")
    if status["reason"]:
        print(f"Reason: {status['reason']}")
    print(f"Requirement: {status['requirement']}")
