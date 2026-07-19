from typing import List
from haystack import Document


REMOVE = {
    "Viola.pdf", "Viola (1).pdf", "Viola (2).pdf", "Every_breath_you_take.pdf",
    "Stuff to check for buying a used car to flip.pdf",
}

OVERRIDES = {
    "Entrep s4SB for ACC proofread(Final)1 experimental version.pdf": ("Entrepreneurship", "Senior 6"),

    "Financial Accounting S4 SB Experimental Version.pdf": ("Accounting", "Senior 4"),
    "Mathematcs for Accounting Option S4 SB.pdf": ("Accounting", "Senior 4"),
    "ICT in Accounting S4 SB.pdf": ("Accounting", "Senior 4"),
    "MANAGEMENT ACCOUNTING_STUDENT BOOK22.pdf": ("Accounting", "Senior 4"),
    "Taxation S4 SB Experimental Version.pdf": ("Accounting", "Senior 4"),
    "PES TG in Accounting Experimental Version.pdf": ("Accounting", "Senior 4"),

    "Ego Is the Enemy (Ryan Holiday) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "Start with Why (Simon Sinek) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "Surrounded By Psychopaths (Thomas Erikson) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "Surrounded by Idiots The Four Types of Human Behavior and How to Effectively Communicate with Each in Business (and in Life) (Thomas Erikson) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "Surrounded by bad bosses (and lazy employees)  how to stop struggling, start succeeding, and deal with idiots at work (Erikson, Thomas, 1965- author) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "The 48 Laws of Power (Greene, Robert) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "The Let Them Theory (Mel Robbins) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "The Power of Now A Guide to Spiritual Enlightenment (Eckhart Tolle) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "The Power of Now A Guide to Spiritual Enlightenment (Eckhart Tolle) (z-library.sk, 1lib.sk, z-lib.sk) (1).pdf": ("Leadership and Self-Development", "general"),
    "The Way Forward (Yung Pueblo) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "Thinking, Fast and Slow (Daniel Kahneman) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "Win Your Inner Battles Defeat The Enemy Within and Live With Purpose (Darius Foroux) (z-library.sk, 1lib.sk, z-lib.sk).pdf": ("Leadership and Self-Development", "general"),
    "See-You-At-The-Top_compressed_compressed_compressed (1).pdf": ("Leadership and Self-Development", "general"),

    "Finanacial-Freedom-A-proven-path-to-all-the-money-you-will-ever-need-pdf.pdf": ("Finance", "general"),
    "MONEY_ Making Money For Beginners (Online Business, YouTube, Fiverr, Craigslist, Financial Freedom, Successful People) ( PDFDrive ).pdf": ("Finance", "general"),
    "Retire-Young-Retire-Rich.pdf": ("Finance", "general"),
    "Rich Dad Poor Dad ( PDFDrive ( PDFDrive.com ).pdf": ("Finance", "general"),
    "Rich Dad's Rich Kid, Smart Kid_ Giving Your Child a Financial Head Start ( PDFDrive.com ).pdf": ("Finance", "general"),
    "Rich Dads Guide to Investing_ What the Rich Invest in That the Poor and Middle Class Do Not! ( PDFDrive.com ).pdf": ("Finance", "general"),
    "The Richest Man In Babylon ( PDFDrive ).pdf": ("Finance", "general"),

    "automatetheboringstuffwithpython_new.pdf": ("Backend Engineering", "general"),
    "dokumen.pub_fastapi-modern-python-web-development-1nbsped-1098135504-9781098135508.pdf": ("Backend Engineering", "general"),
    "fastapi_tutorial.pdf": ("Backend Engineering", "general"),

    "learning-langchain-for-true-epub-9781098167288.pdf": ("Agentic AI (LangChain)", "general"),
}

GRADE_ONLY_OVERRIDES = {
    "Dark Psychology Secret The Essential Guide to Persuasion, Emotional Manipulation, Deception, Mind Control, Human Behavior, NLP… (Daniel James Hollins) (z-library.sk, 1lib.sk, z-lib.sk).pdf": "general",
    "Games People Play The Psychology of Human Relationships (Eric Berne) (z-library.sk, 1lib.sk, z-lib.sk).pdf": "general",
}

PAST_PAPER_NAMES = {
    "2021 Computer Science Past Paper.pdf", "2017 Computer Science Past Paper.pdf",
    "2015 Computer Science Past Paper.pdf", "2022 Computer Science Past Paper.pdf",
    "2016 Computer Science Past Paper.pdf", "2018 Computer Science Past Paper.pdf",
    "2019 Computer Science Past Paper.pdf", "2023 Computer Science Past Paper.pdf",
    "2019 Entrepreneurship Past Paper.pdf", "2023 Entrepreneurship II Past Paper.pdf",
    "2022 Entrepreneurship Past Paper.pdf", "2015 Entrepreneurship Past Paper.pdf",
    "2021 Entrepreneurship Past Paper.pdf", "2016 Entrepreneurship Past Paper.pdf",
    "2014 Entrepreneurship Memo.pdf",
    "2014 Physics II Past Paper.pdf", "2013 Physics III Past Paper.pdf",
    "2015 Physics II Past Paper.pdf", "2022 Physics III Past Paper.pdf",
    "2021 Physics III Past Paper.pdf", "2022 Physics II Past Paper.pdf",
    "2019 Physics III Past Paper.pdf", "2019 Physics II Past Paper.pdf",
    "2016 Physics II Past Paper.pdf", "2014 Physics III Past Paper.pdf",
    "2012 Physics III Past Paper.pdf", "2016 Physics III Past Paper.pdf",
    "2021 Physics II Past Paper.pdf", "2023 Physics III Past Paper.pdf",
    "2023 Physics II Past Paper.pdf",
    "2015 Mathematics II Past Paper.pdf", "2019 Mathematics II Past Paper.pdf",
    "2016 Mathematics II Past Paper.pdf", "2023 Mathematics II Past Paper.pdf",
    "2014 Mathematics II Past Paper.pdf", "2021 Mathematics II Past Paper.pdf",
    "2022 Mathematics II Past Paper.pdf",
}


def fix_naming(chunk_dicts: List[Document]):
    """
    This function replaces unknown subject/grade fields with proper naming,
    and drops chunks belonging to excluded (non-curriculum, mis-scoped) files.
    """
    fixed_chunks = []
    for chunk in chunk_dicts:
        name = chunk.get("file_name")
        if name in REMOVE:
            continue

        if name in PAST_PAPER_NAMES:
            chunk["subject"], chunk["grade"] = "Past Exams", "All Grades"
        elif name in OVERRIDES:
            chunk["subject"], chunk["grade"] = OVERRIDES[name]
        elif name in GRADE_ONLY_OVERRIDES:
            chunk["grade"] = GRADE_ONLY_OVERRIDES[name]

        fixed_chunks.append(chunk)
    return fixed_chunks

if __name__ == "__main__":
    print("Fix naming")
