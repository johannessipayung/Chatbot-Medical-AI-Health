import re


class PIIService:


    @staticmethod
    def normalize_text(text: str) -> str:

        text = re.sub(r"\s+", " ", text)

        return text.strip()

 
    @staticmethod
    def redact_name(text: str):

        patterns = [

            r"(nama\s+saya|nama)\s*[:\-]?\s*([A-Za-z\.\']+(?:\s+[A-Za-z\.\']+){0,6})",

            r"(my\s+name\s+is)\s*([A-Za-z\.\']+(?:\s+[A-Za-z\.\']+){0,6})",
        ]

        for pattern in patterns:

            text = re.sub(
                pattern,
                "[REDACTED_NAME]",
                text,
                flags=re.IGNORECASE
            )

        return text


    @staticmethod
    def redact_nik(text: str):

        patterns = [

            # NIK: 1234567890123456
            r"(nik|no ktp|ktp)\s*[:\-]?\s*\d{15,18}",

            # standalone 16 digit
            r"\b\d{16}\b",

            # separated digits
            r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
        ]

        for pattern in patterns:

            text = re.sub(
                pattern,
                "[REDACTED_NIK]",
                text,
                flags=re.IGNORECASE
            )

        return text

    @staticmethod
    def redact_phone(text: str):

        pattern = (
            r"(\+62|62|0)"
            r"[\s\-]?"
            r"8[1-9][0-9\s\-]{6,12}"
        )

        return re.sub(
            pattern,
            "[REDACTED_PHONE]",
            text
        )



    @staticmethod
    def redact_email(text: str):

        pattern = (
            r"[a-zA-Z0-9_.+-]+"
            r"@[a-zA-Z0-9-]+"
            r"\.[a-zA-Z0-9-.]+"
        )

        return re.sub(
            pattern,
            "[REDACTED_EMAIL]",
            text
        )


    @staticmethod
    def redact_address(text: str):

        patterns = [

            r"(alamat|address)\s*[:\-]?\s*.+",

            r"jl\.?\s+[A-Za-z0-9\s\-]+",

            r"jalan\s+[A-Za-z0-9\s\-]+",
        ]

        for pattern in patterns:

            text = re.sub(
                pattern,
                "[REDACTED_ADDRESS]",
                text,
                flags=re.IGNORECASE
            )

        return text


    @staticmethod
    def redact_all(text: str):

        text = PIIService.normalize_text(text)

        text = PIIService.redact_name(text)

        text = PIIService.redact_nik(text)

        text = PIIService.redact_phone(text)

        text = PIIService.redact_email(text)

        text = PIIService.redact_address(text)

        return text