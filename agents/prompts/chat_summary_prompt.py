chat_summary_instruction = """
You are summarizing an ongoing tutoring conversation between a {grade}
student and FoundationX's AI assistant, for the app's own internal memory -
not for the student to read.

Produce a concise summary (3-6 sentences) capturing:
- The topics and questions the student has asked about so far
- Key points or explanations already given
- Anything the student appeared to be confused about or is still working through

Do not include instructions, meta-commentary, or anything except the summary
itself.
"""

chat_summary_prompt = """
Summarize the conversation above.
"""
