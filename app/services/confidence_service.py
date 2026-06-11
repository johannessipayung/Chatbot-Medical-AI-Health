from app.config.settings import settings


class ConfidenceService:

    @staticmethod
    def calculate_confidence(
        retrieved_docs_count: int,
        answer_length: int,
        has_citation: bool
    ):

        score = 0.0

        # RETRIEVAL QUALITY

        if retrieved_docs_count >= 5:
            score += 0.45

        elif retrieved_docs_count >= 3:
            score += 0.35

        elif retrieved_docs_count >= 1:
            score += 0.20

        # ANSWER COMPLETENESS

        if answer_length >= 500:
            score += 0.30

        elif answer_length >= 200:
            score += 0.20

        else:
            score += 0.10

        # CITATION BONUS

        if has_citation:
            score += 0.25

        # NORMALIZE

        score = min(score, 1.0)

        return round(score * 100, 2)

    @staticmethod
    def confidence_label(score: float):

        normalized = score / 100

        if normalized >= settings.HIGH_CONFIDENCE:
            return "HIGH"

        elif normalized >= settings.MEDIUM_CONFIDENCE:
            return "MEDIUM"

        return "LOW"