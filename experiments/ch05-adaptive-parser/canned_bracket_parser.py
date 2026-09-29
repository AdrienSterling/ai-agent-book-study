import re


def parse(line: str) -> dict | None:
    pattern = (
        r"\[(?P<timestamp>.*?)\] \((?P<level>.*?)\) <tool=(?P<tool>.*?)> "
        r"\{latency_ms=(?P<latency_ms>\d+) status=(?P<status>\w+)\} :: (?P<message>.*)"
    )
    match = re.match(pattern, line.strip())
    if match:
        return match.groupdict()
    return None
