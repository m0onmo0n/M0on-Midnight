"""Helpers shared by the tools: read the client's class list and match [class*=...] tokens to real classes."""
import json
import re
from pathlib import Path

ATTR = re.compile(r'\[class([*^])="([A-Za-z0-9_]+)"\]')
COMMENT = re.compile(r'/\*.*?\*/', re.S)
HASHED_REF = re.compile(r'\.([A-Za-z][A-Za-z0-9]*)_([A-Za-z0-9_-]{6})(?![A-Za-z0-9_-])')
QUOTES = '"\''


def load_names(path):
    data = json.loads(Path(path).read_text(encoding='utf8'))
    return {name: sorted(hashes) for name, hashes in data.items()}


def classes_for(token, names):
    """The real classes a [class*=token] selector was meant to match."""
    if token.endswith('_'):
        return [f'{token[:-1]}_{h}' for h in names.get(token[:-1], [])]
    # no trailing underscore: part of one or more names (modeUnread -> modeUnreadImportant)
    out = []
    for name, hashes in names.items():
        if token in name:
            out += [f'{name}_{h}' for h in hashes]
    return out


def split_top(s, sep):
    """Split on sep outside (), [] and quotes."""
    out, depth, quote, cur = [], 0, None, []
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in QUOTES:
            quote = ch
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == sep and depth == 0:
            out.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append(''.join(cur))
    return out
