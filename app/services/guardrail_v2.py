import codecs
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


LEET_TABLE = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "6": "g",
        "7": "t",
        "8": "b",
        "9": "g",
        "@": "a",
        "$": "s",
    }
)


INJECTION_KEYWORDS = [
    "ignore previous",
    "ignore all",
    "ignore guardrails",
    "system prompt",
    "developer message",
    "jailbreak",
    "disable safety",
    "bypass safety",
    "do anything now",
    "dan mode",
    "prompt injection",
]


HARMFUL_PATTERNS = [
    r"over\s*dose",
    r"overdosis",
    r"lethal\s*dose",
    r"dosis\s*mematikan",
    r"bunuh\s*diri",
    r"kill\s*myself",
    r"cara\s*membunuh",
    r"racun",
    r"how\s*to\s*die",
    r"suicide",
]


CRITICAL_URGENT_PATTERNS = [
    r"nyeri\s*dada.*sesak\s*napas",
    r"sesak\s*napas.*nyeri\s*dada",
    r"dada.*nyeri.*sesak\s*napas",
    r"sesak\s*napas.*dada.*nyeri",
    r"tidak\s*sadar",
    r"perdarahan\s*hebat",
]


URGENT_PATTERNS = [
    r"nyeri\s*dada",
    r"sesak\s*napas",
    r"sulit\s*bernapas",
    r"stroke",
    r"kejang",
    r"pingsan",
    r"tidak\s*sadar",
    r"perdarahan\s*hebat",
    r"muntah\s*darah",
    r"tiba\s*[- ]?tiba\s*lemas",
    r"wajah\s*mencong",
    r"bicara\s*pelo",
]


OUTPUT_UNSAFE_PATTERNS = [
    r"dosis\s*(mematikan|fatal)",
    r"lethal\s*dose",
    r"cara\s*membunuh",
    r"how\s*to\s*(kill|die)",
]


@dataclass
class GuardrailResult:
    action: str  # PASS | BLOCK | URGENT | CLARIFY
    sanitized_text: str
    flags: Dict[str, object]
    reason: str
    clarification_questions: List[str]


class GuardrailV2:
    @staticmethod
    def _safe_unicode_unescape(text: str) -> str:
        # Decode common \uXXXX sequences without executing escapes broadly
        def _repl(m: re.Match) -> str:
            try:
                return chr(int(m.group(1), 16))
            except Exception:
                return m.group(0)

        return re.sub(r"\\u([0-9a-fA-F]{4})", _repl, text)

    @staticmethod
    def _normalize(text: str) -> str:
        t = text or ""
        t = ZERO_WIDTH_RE.sub("", t)
        t = GuardrailV2._safe_unicode_unescape(t)
        t = t.lower()
        
        # PERBAIKAN: Hanya mereduksi spasi horizontal/tab, menjaga baris baru (\n) tetap utuh
        t = re.sub(r"[ \t]+", " ", t).strip() 
        return t

    @staticmethod
    def _leet_normalize(text: str) -> str:
        return (text or "").translate(LEET_TABLE)

    @staticmethod
    def _rot13(text: str) -> str:
        try:
            return codecs.decode(text, "rot_13")
        except Exception:
            return text

    @staticmethod
    def _variants(text: str) -> List[str]:
        base = GuardrailV2._normalize(text)
        leet = GuardrailV2._normalize(GuardrailV2._leet_normalize(base))
        rot = GuardrailV2._normalize(GuardrailV2._rot13(base))
        return list(dict.fromkeys([base, leet, rot]))

    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        for v in GuardrailV2._variants(text):
            if any(k in v for k in INJECTION_KEYWORDS):
                return True
        return False

    @staticmethod
    def detect_harmful(text: str) -> bool:
        for v in GuardrailV2._variants(text):
            for p in HARMFUL_PATTERNS:
                if re.search(p, v):
                    return True
        return False

    @staticmethod
    def detect_urgent(text: str) -> bool:
        for v in GuardrailV2._variants(text):
            for p in URGENT_PATTERNS:
                if re.search(p, v):
                    return True
        return False

    @staticmethod
    def urgent_severity(text: str) -> Optional[str]:
        for v in GuardrailV2._variants(text):
            for p in CRITICAL_URGENT_PATTERNS:
                if re.search(p, v):
                    return "CRITICAL"
        return "URGENT" if GuardrailV2.detect_urgent(text) else None

    @staticmethod
    def needs_clarification(text: str) -> Tuple[bool, List[str]]:
        t = GuardrailV2._normalize(text)
        questions: List[str] = []

        # =========================================================
        # EXPANDED KEYWORDS (Lebih Umum & Mencakup Bahasa Sehari-hari)
        # =========================================================
        # Kategori 1: Interaksi & Kombinasi Obats
        interaction_signals = [
            "interaksi", "interaction", "kombinasi", "combine", "dan", "+",
            "campur", "mencampur", "bareng", "bersamaan", "digabung", "minum dua"
        ]
        
        # Kategori 2: Pertanyaan Dosis/Aturan Pakai yang Menggantung
        dosage_signals = [
            "dosis", "aturan pakai", "berapa kali", "sehari berapa", "minumnya", 
            "kapan minum", "sebelum atau sesudah", "efek samping"
        ]
        
        # Kategori 3: Keluhan Gejala Umum Tanpa Detail
        symptom_signals = [
            "sakit", "nyeri", "batuk", "demam", "pusing", "mual", "muntah", 
            "gatal", "alergi", "bengkak", "luka"
        ]

        # =========================================================
        # HEURISTIC LOGIC (Aturan Pemicu Klarifikasi)
        # =========================================================
        
        # Kasus A: Deteksi pertanyaan interaksi obat (Butuh minimal 2 sinyal kombinasi)
        hit_interactions = sum(1 for s in interaction_signals if s in t)
        
        # Kasus B: Deteksi pertanyaan dosis obat atau gejala yang terlalu singkat/umum
        hit_dosage = any(d in t for d in dosage_signals)
        hit_symptom = any(s in t for s in symptom_signals)

        # Kondisi Pemicu:
        # 1. Menanyakan kombinasi obat secara ambigu, ATAU
        # 2. Menanyakan dosis/gejala umum secara acak tetapi teksnya relatif pendek/kurang detail (< 80 karakter)
        if (hit_interactions >= 2 and len(t) > 50) or ((hit_dosage or hit_symptom) and len(t) < 80):
            
            # Buat daftar pertanyaan klarifikasi yang dinamis & kontekstual
            if "obat" in t or hit_interactions >= 1 or hit_dosage:
                questions.append("Apakah Anda sedang mengonsumsi obat/suplemen tertentu saat ini? Mohon sebutkan obat, dosis, dan frekuensinya.")
            
            questions.append("Berapa usia Anda sekarang dan berapa lama gejala tersebut sudah dirasakan?")
            questions.append("Apakah Anda memiliki kondisi medis khusus seperti riwayat alergi obat, gangguan ginjal/hati, atau sedang hamil/menyusui?")
            
            return True, questions

        return False, []

    @staticmethod
    def decide(text: str) -> GuardrailResult:
        urgent = GuardrailV2.detect_urgent(text)
        flags: Dict[str, object] = {
            "prompt_injection": GuardrailV2.detect_prompt_injection(text),
            "harmful": GuardrailV2.detect_harmful(text),
            "urgent": urgent,
            "urgent_severity": GuardrailV2.urgent_severity(text) if urgent else None,
        }

        needs_clarify, clar_qs = GuardrailV2.needs_clarification(text)

        action = "PASS"
        reason = "ok"
        if flags["prompt_injection"]:
            action = "BLOCK"
            reason = "prompt_injection_detected"
        elif flags["harmful"]:
            action = "BLOCK"
            reason = "harmful_request"
        elif flags["urgent"]:
            action = "URGENT"
            reason = "urgent_symptom"
        elif needs_clarify:
            action = "CLARIFY"
            reason = "needs_clarification"

        return GuardrailResult(
            action=action,
            sanitized_text=GuardrailV2._normalize(text),
            flags=flags,
            reason=reason,
            clarification_questions=clar_qs,
        )

    @staticmethod
    def filter_output(answer: str) -> Tuple[str, bool, str]:
        t = GuardrailV2._normalize(answer)
        for p in OUTPUT_UNSAFE_PATTERNS:
            if re.search(p, t):
                return (
                    "Maaf, saya tidak bisa membantu permintaan yang berpotensi membahayakan. "
                    "Jika Anda atau orang lain berada dalam bahaya atau kondisi darurat, segera hubungi 119 atau IGD terdekat.",
                    True,
                    "unsafe_output_filtered",
                )
        return answer, False, "ok"
