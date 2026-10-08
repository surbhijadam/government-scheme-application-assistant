"""
AI assistant layer, built around three hard constraints from the SRS:

1. The AI explains; it NEVER makes the final eligibility decision. That
   stays entirely with the deterministic engine (eligibility_engine.py).
2. The AI only ever receives verified SCHEME data as context - never the
   user's personal profile - so it can't leak sensitive information even
   if asked to.
3. If Groq is unavailable for any reason, this returns a clear error
   instead of raising, so the rest of the app is unaffected.
"""
import os

from groq import Groq

GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are an assistant for a government scheme application demo project.

STRICT RULES YOU MUST FOLLOW:
- You are an AI assistant, NOT an official government authority. Say so if asked who/what you are.
- You explain scheme details, eligibility CRITERIA, and required documents in plain language.
- You NEVER state whether a specific person is or is not eligible. That decision is made ONLY
  by the project's separate rule-based eligibility engine. If asked "am I eligible", direct the
  person to the Eligibility Check page instead of guessing.
- You NEVER invent scheme details, benefits, or eligibility rules that are not given to you in
  the "Verified scheme context" below. If information isn't provided, say you don't have it.
- You NEVER ask for or discuss sensitive personal data (Aadhaar numbers, bank details, etc).
- This is demo/sample data for a learning project, not an official government service. If asked
  for official guidance, tell the person to consult the actual government website for that scheme.
"""


def _call_groq(messages):
    """
    The actual network call to Groq, isolated in its own function so it can
    be mocked in tests without needing real network access.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content


def build_scheme_context(scheme):
    """Build a plain-text context block from VERIFIED scheme data only."""
    lines = [
        f"Scheme name: {scheme.name}",
        f"Category: {scheme.category or 'Not specified'}",
        f"Description: {scheme.description or 'Not specified'}",
        f"Benefits: {scheme.benefits or 'Not specified'}",
    ]

    if scheme.eligibility_rules:
        lines.append("Eligibility criteria:")
        for rule in scheme.eligibility_rules:
            lines.append(f"  - {rule.field_name} {rule.operator} {rule.expected_value}")

    if scheme.required_documents:
        lines.append("Required documents:")
        for doc in scheme.required_documents:
            tag = "mandatory" if doc.mandatory else "optional"
            lines.append(f"  - {doc.document_name} ({tag})")

    return "\n".join(lines)


def ask_assistant(user_message, scheme_context=None):
    """
    Returns (reply, error). Exactly one is not None.
    Never raises - any failure becomes a graceful error message.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if scheme_context:
        messages.append(
            {"role": "system", "content": f"Verified scheme context:\n{scheme_context}"}
        )

    messages.append({"role": "user", "content": user_message})

    try:
        reply = _call_groq(messages)
        return reply, None
    except Exception:
        # Any Groq failure (missing key, network error, rate limit, bad
        # response) degrades gracefully - the rest of the app is unaffected.
        return None, "The AI assistant is temporarily unavailable. Please try again later."