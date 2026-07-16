#!/usr/bin/env python3

import re
import unicodedata


class DocumentCleaner:

    def clean_text(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)

        # Remove invisible unicode characters
        text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

        # Normalize spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize excessive new lines
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Remove spaces before punctuation
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)

        return text.strip()
