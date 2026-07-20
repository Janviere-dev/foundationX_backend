import re
from pathlib import Path

SPELLED_OUT_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
}

# matches S3, S.5, S4_SB, S6 SB, etc. (Senior grades)
SENIOR_PATTERN = re.compile(r"\bS\.?(\d)(?=[_\s.]|$)")
# matches P3, P.5, P4_SB, etc. (Primary grades)
PRIMARY_PATTERN = re.compile(r"\bP\.?(\d)(?=[_\s.]|$)")
# matches spelled-out grades, e.g. "Senior Five"
SPELLED_SENIOR_PATTERN = re.compile(
    r"\bSenior\s+(" + "|".join(SPELLED_OUT_NUMBERS) + r")\b", re.IGNORECASE
)


def infer_grade(file_path: Path) -> str:
    """
    Guess the grade level (e.g. 'Senior 3') from the file's parent folder name or file name.
    underscores are used as word separators in some file names (e.g. 'Book_Senior Five'),
    which would otherwise defeat \b word-boundary matching since "_" counts as a word char
    """

    haystack_text = f"{file_path.parent.name} {file_path.stem}".replace("_", " ")

    spelled_match = SPELLED_SENIOR_PATTERN.search(haystack_text)
    if spelled_match:
        level = SPELLED_OUT_NUMBERS[spelled_match.group(1).lower()]
        return f"Senior {level}"

    senior_match = SENIOR_PATTERN.search(haystack_text)
    if senior_match:
        return f"Senior {senior_match.group(1)}"

    primary_match = PRIMARY_PATTERN.search(haystack_text)
    if primary_match:
        return f"Primary {primary_match.group(1)}"

    return "Unknown"
