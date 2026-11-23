#!/usr/bin/env python3
"""Finds rules that can no longer match anything in the current Discord client.

    python tools/audit.py addons/*.css upstream/*.css

Uses tools/hashes.json (made by tools/extract-hashes.js in the Discord console). A selector is dead when it
contains
  - [class*="name_"] / [class^="name_"] for a name that does not exist in the client, or
  - a hard-coded .name_HASH class that does not exist in the client.
A rule is dead when every selector in its list is dead. Nested rules inherit a dead parent.
It only reports; nothing is changed. Names are matched the way the theme means them (see classlib.classes_for).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from classlib import ATTR, COMMENT, HASHED_REF, QUOTES, classes_for, load_names, split_top  # noqa: E402


def strip_not(sel):
    """Drop :not(...) groups: a class that is missing there does not stop the selector from matching."""
    while True:
        i = sel.find(':not(')
        if i < 0:
            return sel
        depth, j = 0, i + 4
        while j < len(sel):
            if sel[j] == '(':
                depth += 1
            elif sel[j] == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        sel = sel[:i] + sel[j + 1:]


def dead_reason(selector, names, live):
    selector = strip_not(selector)
    for m in ATTR.finditer(selector):
        if not classes_for(m.group(2), names):
            return f'no class "{m.group(2)}" in the client'
    for m in HASHED_REF.finditer(selector):
        if f'{m.group(1)}_{m.group(2)}' not in live:
            return f'.{m.group(1)}_{m.group(2)} is not in the client'
    return None


def audit(path, names, live):
    css = Path(path).read_text(encoding='utf8')
    findings = []
    stack = []  # (prelude, dead_parent_reason)
    seg, i, n = 0, 0, len(css)
    line_of = lambda pos: css.count('\n', 0, pos) + 1  # noqa: E731
    while i < n:
        ch = css[i]
        if css.startswith('/*', i):
            j = css.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch in QUOTES:
            j = i + 1
            while j < n and css[j] != ch:
                j += 2 if css[j] == '\\' else 1
            i = j + 1
            continue
        if ch == '{':
            prelude = COMMENT.sub('', css[seg:i]).strip()
            parent_dead = stack[-1][1] if stack else None
            reason = parent_dead
            if prelude and not prelude.startswith('@') and not reason:
                sels = [s for s in split_top(prelude, ',') if s.strip()]
                reasons = [dead_reason(s, names, live) for s in sels]
                if sels and all(reasons):
                    reason = reasons[0]
                    findings.append((line_of(seg + (len(css[seg:i]) - len(css[seg:i].lstrip()))), prelude.replace('\n', ' ')[:110], reason))
                elif any(reasons):
                    dead_sels = [s.strip() for s, r in zip(sels, reasons) if r]
                    findings.append((line_of(seg + (len(css[seg:i]) - len(css[seg:i].lstrip()))),
                                     f'{len(dead_sels)} of {len(sels)} selectors dead: ' + dead_sels[0][:80], 'partly dead'))
            stack.append((prelude, reason))
            seg = i + 1
        elif ch == '}':
            if stack:
                stack.pop()
            seg = i + 1
        elif ch == ';':
            seg = i + 1
        i += 1
    return findings


def main():
    names = load_names(ROOT / 'tools' / 'hashes.json')
    live = {f'{n}_{h}' for n, hs in names.items() for h in hs}
    total = 0
    for path in sys.argv[1:]:
        found = audit(path, names, live)
        total += sum(1 for f in found if f[2] != 'partly dead')
        print(f'\n{path}: {len(found)} finding(s)')
        for line, prelude, reason in found:
            print(f'  line {line:>4}  [{reason}]  {prelude}')
    print(f'\n{total} fully dead rule(s)')
    # :has() cost: every :has() rule is re-checked whenever something inside its element changes, even inside a closed
    # @container. Hovering a server and switching servers felt slow because of three of them (Nov 2026). Keep our files at zero.
    has = sum(Path(f).read_text(encoding='utf8').count(':has(') for f in sys.argv[1:])
    print(f':has( used {has} time(s) in these files' + ('  <-- each costs on every DOM change; prefer a plugin-stamped attribute' if has else ''))


if __name__ == '__main__':
    main()
