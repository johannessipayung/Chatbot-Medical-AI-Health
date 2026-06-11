from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from app.services.pii_service import PIIService

from app.services.audit_service import AuditService

router = APIRouter()


_graph = None


def get_graph():

    global _graph

    if _graph is None:

        from app.graph.graph_builder import (
            build_medical_graph
        )

        _graph = build_medical_graph()

    return _graph

class ChatRequest(BaseModel):

    question: str = Field(
        ...,
        min_length=1,
        max_length=10000
    )


def should_add_disclaimer(text: str):

    high_risk_keywords = [

        "obat",
        "dosis",
        "covid",
        "sesak",
        "nyeri dada",
        "stroke",
        "jantung",
        "darurat",
        "overdose",
        "bunuh diri",
        "racun",
    ]

    text = text.lower()

    return any(
        k in text
        for k in high_risk_keywords
    )


@router.post("/chat")
def chat(req: ChatRequest):

    try:

        # ORIGINAL INPUT

        original_question = (
            req.question.strip()
        )

        # EMPTY INPUT

        if not original_question:

            return {

                "success": False,

                "error": "Question cannot be empty"
            }

        # PII REDACTION INPUT

        sanitized_question = (
            PIIService.redact_all(
                original_question
            )
        )

        # AUDIT LOG

        AuditService.log_event(

            "pii_redacted",

            {

                "before": original_question,

                "after": sanitized_question
            }
        )

        AuditService.log_event(

            "request_received",

            {

                "question": sanitized_question
            }
        )

        # GRAPH INVOKE

        graph = get_graph()

        result = graph.invoke({

            # IMPORTANT:
            # NEVER SEND RAW QUESTION
            "question": sanitized_question,

            "triage_urgent": False,

            "blocked_by_guardrail": False,

            "needs_clarification": False,

            "retrieved_docs": [],

            "final_answer": "",

            "estimated_cost": 0.0,
        })

        # OUTPUT SANITIZATION

        final_answer = result.get(
            "final_answer",
            ""
        )

        final_answer = (
            PIIService.redact_all(
                final_answer
            )
        )

        # CONDITIONAL DISCLAIMER

        if should_add_disclaimer(
            sanitized_question
        ):

            final_answer += (
                "\n\n"
                "⚠️ Disclaimer: "
                "AI ini bukan pengganti "
                "dokter profesional. "
                "Jika kondisi darurat, "
                "segera hubungi 119 "
                "atau IGD terdekat."
            )

        # REMOVE DUPLICATE CONFIDENCE

        if "confidence_score" in result:

            result.pop("confidence_score")

        # UPDATE FINAL ANSWER

        result["final_answer"] = (
            final_answer
        )

        # SAFE RESPONSE

        return {

            "success": True,

            "question": sanitized_question,

            "answer": final_answer,

            "sources": result.get(
                "retrieved_docs",
                []
            ),

            "confidence": result.get(
                "confidence",
                "MEDIUM"
            ),

            "estimated_cost": result.get(
                "estimated_cost",
                0.0
            ),

            "triage_urgent": result.get(
                "triage_urgent",
                False
            ),

            "blocked_by_guardrail": result.get(
                "blocked_by_guardrail",
                False
            ),

            "needs_clarification": result.get(
                "needs_clarification",
                False
            ),
        }

    except Exception as e:

        AuditService.log_event(

            "server_error",

            {

                "error": str(e)
            }
        )

        raise HTTPException(

            status_code=500,

            detail="Internal medical AI error"
        )


# AUDIT LOGS

@router.get("/audit/logs")
def get_audit_logs(limit: int = 100):

    if limit < 1 or limit > 1000:

        raise HTTPException(

            status_code=400,

            detail="limit must be 1..1000"
        )

    return {

        "logs": AuditService.read_logs(
            limit=limit
        )
    }