import re
from datetime import datetime


def parse(line: str) -> dict | None:
    if not isinstance(line, str):
        return None

    pattern = re.compile(
        r'^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*'
        r'\((?P<level>[A-Za-z]+)\)\s*'
        r'<tool=(?P<tool>[^>\s]+)>\s*'
        r'\{(?P<kv>[^}]*)\}\s*'
        r'::\s*(?P<message>.*)$'
    )

    m = pattern.match(line)
    if not m:
        return None

    timestamp = m.group('timestamp').strip()
    level = m.group('level').strip()
    tool = m.group('tool').strip()
    message = m.group('message').strip()

    if not timestamp or not level or not tool or not message:
        return None

    try:
        datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

    result = {
        'timestamp': timestamp,
        'level': level,
        'tool': tool,
        'message': message,
    }

    kv = m.group('kv').strip()
    if kv:
        for pair in kv.split():
            if '=' in pair:
                k, v = pair.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k:
                    result[k] = v

    return result