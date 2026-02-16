import json
from datetime import datetime, timezone
from pathlib import Path


def append_jsonl(filepath: Path, data: dict):
    """Append a JSON line to a JSONL file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **data}
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_jsonl(filepath: Path) -> list[dict]:
    """Read all lines from a JSONL file."""
    if not filepath.exists():
        return []
    lines = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines
