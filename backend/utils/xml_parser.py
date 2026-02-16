from __future__ import annotations
import re


def extract_tag(text: str, tag: str) -> str:
    """Extract content from an XML-style tag. Returns empty string if not found."""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


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
