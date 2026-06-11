from typing import Any, Dict, List, TypedDict


class ChatbotState(TypedDict, total=False):
    question: str
    redacted_question: str

    needs_clarification: bool

    safety_flags: Dict[str, Any]

    triage_urgent: bool
    blocked_by_guardrail: bool

    retrieved_docs: List[str]

    final_answer: str

    estimated_cost: float

    confidence_score: float
    confidence_label: str