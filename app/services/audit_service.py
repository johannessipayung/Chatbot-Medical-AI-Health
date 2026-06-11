import os
import json
from datetime import datetime
from typing import Any, Dict, List

from app.services.pii_service import PIIService

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "audit.log")


class AuditService:

    @staticmethod
    def _ensure_dir() -> None:
        os.makedirs(LOG_DIR, exist_ok=True)

    @staticmethod
    def _redact_payload(payload: Any) -> Any:
        payload_str = json.dumps(payload, ensure_ascii=False, default=str)
        redacted_str = PIIService.redact_all(payload_str)
        try:
            return json.loads(redacted_str)
        except Exception:
            return {"redacted": redacted_str}

    @staticmethod
    def log_event(event_type: str, payload: Any) -> None:
        """Write a JSONL audit log with PII redacted (best-effort, never raises)."""
        try:
            AuditService._ensure_dir()

            entry: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event": event_type,
                "payload": AuditService._redact_payload(payload),
            }

            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            # Best-effort: do not raise in request path
            try:
                AuditService._ensure_dir()
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "event": "audit_error",
                                "error": str(e),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            except Exception:
                pass

    @staticmethod
    def read_logs(limit: int = 100) -> List[Dict[str, Any]]:
        AuditService._ensure_dir()
        if not os.path.exists(LOG_FILE):
            return []
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        out: List[Dict[str, Any]] = []
        for l in lines:
            try:
                out.append(json.loads(l))
            except Exception:
                continue
        return out
