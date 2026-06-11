import re
from typing import Dict, Optional


class DocumentMetaService:
    @staticmethod
    def infer_year(source: str) -> Optional[int]:
        if not source:
            return None
        years = re.findall(r"(19\d{2}|20\d{2})", source)
        if not years:
            return None
        try:
            return max(int(y) for y in years)
        except Exception:
            return None

    @staticmethod
    def infer_authority(source: str) -> str:
        s = (source or "").lower()
        if "who" in s or "world health" in s:
            return "WHO"
        if "cdc" in s:
            return "CDC"
        if "fda" in s:
            return "FDA"
        if "nih" in s:
            return "NIH"
        if "guideline" in s:
            return "GUIDELINE"
        return "UNKNOWN"

    @staticmethod
    def enrich(metadata: Dict) -> Dict:
        meta = dict(metadata or {})
        src = meta.get("source", "")
        meta.setdefault("year", DocumentMetaService.infer_year(src))
        # normalize page: treat 0 or falsy page as unknown
        page = meta.get("page")
        if page == 0:
            meta["page"] = None
        meta.setdefault("authority", DocumentMetaService.infer_authority(src))
        return meta
