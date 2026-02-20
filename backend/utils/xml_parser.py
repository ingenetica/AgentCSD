from __future__ import annotations
import re


def extract_tag(text: str, tag: str) -> str:
    """Extract content from an XML-style tag. Falls back to markdown-style headers.
    Returns empty string if not found."""
    # Try XML tags first: <tag>content</tag>
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: markdown-style header like **tag:** or **tag**:\n
    md_pattern = rf"\*\*{tag}:?\*\*:?\s*\n(.*?)(?=\n\*\*\w|$)"
    match = re.search(md_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def extract_all_tags(text: str) -> dict[str, str]:
    """Extract all XML-style tags from text into a dict."""
    pattern = r"<(\w+)>(.*?)</\1>"
    matches = re.findall(pattern, text, re.DOTALL)
    return {tag: content.strip() for tag, content in matches}


def extract_m_and_c(text: str) -> dict[str, str]:
    """Extract mood and criteria from M_AND_C block."""
    m_and_c_block = extract_tag(text, "M_AND_C")
    if not m_and_c_block:
        return {"mood": "", "criteria": ""}
    return {
        "mood": extract_tag(m_and_c_block, "mood"),
        "criteria": extract_tag(m_and_c_block, "criteria"),
    }
