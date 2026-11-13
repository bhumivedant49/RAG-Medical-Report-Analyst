from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SAFETY_INSTRUCTIONS = """
You explain the wording and information contained in medical documents.
You are not a doctor and must not diagnose, prescribe, recommend treatment, or infer
a condition from isolated values. Do not invent values, units, reference ranges, or
medical history. If the document does not contain the answer, say so clearly.
Explain technical terms in plain language. Encourage the user to discuss decisions
and concerning results with a qualified healthcare professional.
"""

def _client(api_key: str) -> Groq:
    if not api_key or not api_key.strip():
        raise ValueError("A Groq API key is required.")
    return Groq(api_key=api_key.strip())

def answer_question(api_key: str, question: str, passages: list[dict]) -> str:
    if not passages:
        return "I couldn't find relevant information in the uploaded report."
    context_parts = []
    for item in passages:
        context_parts.append(
            f"[Source: {item['source']}, page {item['page']}]\n{item['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)
    prompt = f"""
Use only the report excerpts below to answer the user's question.
Cite supporting statements with the exact source and page, e.g. [report.pdf, p. 2].
If the excerpts do not support an answer, say that the report does not provide enough
information. Do not treat a reference range as a diagnosis.

REPORT EXCERPTS:
{context}

USER QUESTION:
{question}
"""
    result = _client(api_key).chat.completions.create(
        model=MODEL,
        temperature=0.1,
        max_tokens=700,
        messages=[
            {"role": "system", "content": SAFETY_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ],
    )
    return result.choices[0].message.content.strip()

def summarize_report(api_key: str, report_text: str) -> str:
    # Bound prompt size; this is a concise orientation, not a complete clinical review.
    excerpt = report_text[:22000]
    prompt = f"""
Create a concise, plain-language orientation to this medical document.
Use these headings:
1. What kind of document this appears to be
2. Main information stated in the document
3. Values or findings explicitly marked high/low/abnormal in the document
4. Terms the reader may want explained by their clinician
Do not diagnose, infer missing information, or recommend treatment. Do not call a
value abnormal unless the report itself marks it that way or provides a range that
clearly places it outside range. Mention that only part of the document may be included
if the excerpt appears truncated.

DOCUMENT TEXT:
{excerpt}
"""
    result = _client(api_key).chat.completions.create(
        model=MODEL,
        temperature=0.1,
        max_tokens=900,
        messages=[
            {"role": "system", "content": SAFETY_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ],
    )
    return result.choices[0].message.content.strip()
