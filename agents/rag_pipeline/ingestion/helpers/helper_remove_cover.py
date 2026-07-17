import re
from haystack import Document

MAX_PAGE_CHARS = 2000

# matches table-of-contents index lines, e.g. "Graph of linear motion...........1"
TOC_DOT_LEADER_PATTERN = re.compile(r"\.{4,}\s*\d+\s*$", re.MULTILINE)
TOC_LINE_RATIO_THRESHOLD = 0.2


def is_front_matter(page: Document) -> bool:
    """Cover page or table-of-contents page, neither useful for quiz/RAG content."""
    if page.meta.get("page_number") == 1:
        return True

    lines = [line for line in page.content.splitlines() if line.strip()]
    if not lines:
        return False

    toc_line_count = len(TOC_DOT_LEADER_PATTERN.findall(page.content))
    return (toc_line_count / len(lines)) >= TOC_LINE_RATIO_THRESHOLD
