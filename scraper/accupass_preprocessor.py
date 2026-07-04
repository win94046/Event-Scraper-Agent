from __future__ import annotations

import re


DATE_LINE_RE = re.compile(
    r"^\s*(?:20\d{2}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}/\d{1,2})\b"
)
PURE_NUMBER_RE = re.compile(r"^\d[\d,]*$")
EVENT_SEPARATOR = "\n\n--- ACCUPASS_EVENT ---\n\n"


def preprocess_accupass_text(raw_text: str) -> str:
    lines = _clean_lines(raw_text)
    blocks = _split_blocks_by_date(lines)
    event_blocks = [_format_event_block(block) for block in blocks if _looks_like_event(block)]
    return EVENT_SEPARATOR.join(block for block in event_blocks if block)


def _clean_lines(raw_text: str) -> list[str]:
    previous_line: str | None = None
    cleaned: list[str] = []

    for raw_line in raw_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line or _is_noise_line(line):
            continue
        if line == previous_line:
            continue

        cleaned.append(line)
        previous_line = line

    return cleaned


def _is_noise_line(line: str) -> bool:
    if line == "--- ACCUPASS_EVENT ---":
        return True
    if PURE_NUMBER_RE.match(line):
        return True
    if len(line) == 1 and not line.isalnum():
        return True
    return False


def _split_blocks_by_date(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if DATE_LINE_RE.match(line):
            if current:
                blocks.append(current)
            current = [line]
            continue

        if current:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def _looks_like_event(block: list[str]) -> bool:
    if not block or not DATE_LINE_RE.match(block[0]):
        return False

    content_lines = [line for line in block[1:] if not line.startswith("#")]
    has_title = any(len(line) >= 8 for line in content_lines)
    has_topic = any("#" in line or _contains_ascii_topic(line) for line in block)
    return has_title and has_topic


def _contains_ascii_topic(line: str) -> bool:
    lowered = line.lower()
    return bool(re.search(r"\b(ai|python|gemini|claude|agent)\b", lowered))


def _format_event_block(block: list[str]) -> str:
    date_line = block[0]
    body = block[1:9]
    return "\n".join([date_line, *body])
