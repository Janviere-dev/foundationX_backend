from pathlib import Path

SUBJECT_KEYWORDS = {
    "Biology": ["biology"],
    "Chemistry": ["chemistry"],
    "Physics": ["physics"],
    "Mathematics": ["math"],
    "Computer Science": ["computer science", "ict"],
    "Entrepreneurship": ["entrepreneurship"],
    "Economics": ["economics"],
    "English": ["english"],
    "Kinyarwanda": ["kinyarwanda"],
    "French": ["french"],
    "Geography": ["geography"],
    "History": ["history", "citizenship"],
    "Literature": ["literature"],
    "Psychology": ["psychology"],
    "Accounting": ["accounting"],
}


def infer_subject(file_path: Path) -> str:
    """Guess the school subject from the file's parent folder name or file name."""
    haystack_text = f"{file_path.parent.name} {file_path.stem}".lower()
    for subject, keywords in SUBJECT_KEYWORDS.items():
        if any(keyword in haystack_text for keyword in keywords):
            return subject
    return "Unknown"
