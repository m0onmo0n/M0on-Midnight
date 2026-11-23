#!/usr/bin/env python3
"""Makes the feel-test files in clean/feel-tests/: the one-file theme with one thing taken out, to find what makes Discord feel slower.

    python tools/feel.py

Each file is deliberately incomplete (it looks wrong in places). They are only for hovering over servers and seeing which one feels fast.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import build_clean as b  # noqa: E402
from classlib import COMMENT  # noqa: E402

BACKSLASH = chr(92)


def remove_blocks(css, pred):
    """Remove every {...} block whose selector text satisfies pred. Strings and comments are skipped properly."""
    cuts, stack, seg, i, n = [], [], 0, 0, len(css)
    while i < n:
        c = css[i]
        if css.startswith('/*', i):
            j = css.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        if c in '"\'':
            j = i + 1
            while j < n and css[j] != c:
                j += 2 if css[j] == BACKSLASH else 1
            i = j + 1
            continue
        if c == '{':
            stack.append((seg, COMMENT.sub('', css[seg:i]).strip()))
            seg = i + 1
        elif c == '}':
            start, prelude = stack.pop()
            if pred(prelude):
                cuts.append((start, i + 1))
            seg = i + 1
        elif c == ';':
            seg = i + 1
        i += 1
    cuts.sort()
    out, pos = [], 0
    for a, e in cuts:
        if a < pos:
            continue  # inside a block that is already cut
        out.append(css[pos:a])
        pos = e
    out.append(css[pos:])
    return ''.join(out)


def assemble(skip=None, strip_upstream_has=False, strip_our_has=None):
    theme, _ = b.apply_values(b.upstream_variables(), b.SINGLE_VALUES)
    imports, body = [], [theme]
    for m in b.UPSTREAM_MODULES:
        if m == skip:
            continue
        got, rest = b.take_imports(b.read(f'upstream/{m}.css'))
        imports += got
        if strip_upstream_has:
            rest = remove_blocks(rest, lambda p: ':has(' in p and not p.startswith('@'))
        body.append(rest.strip())
    body.append(b.read('upstream/hsl.css').strip())
    got, rest = b.take_imports(b.additions(True))
    if strip_our_has:
        rest = remove_blocks(rest, strip_our_has)
    imports += [i for i in got if 'HorizontalServerList' not in i]
    body.append(rest.strip())
    return '\n'.join(b.unique(imports)) + '\n\n' + '\n\n'.join(body) + '\n'


def main():
    out = ROOT / 'clean' / 'feel-tests'
    out.mkdir(parents=True, exist_ok=True)
    full = assemble()
    files = {'feel-0-control': full,
             'feel-1-no-has': remove_blocks(full, lambda p: ':has(' in p and not p.startswith('@'))}
    for i, m in enumerate(['colors', 'main', 'top-bar', 'chatbar', 'animations', 'transparency-blur',
                           'dms-button', 'user-panel', 'window-controls', 'background-image'], start=2):
        files[f'feel-{i}-minus-{m}'] = assemble(m)
    ours_all = lambda p: ':has(' in p and not p.startswith('@')  # noqa: E731
    files = {
        'feel-A-no-our-has': assemble(strip_our_has=ours_all),
        'feel-B-no-upstream-has': assemble(strip_upstream_has=True),
        'feel-C-no-selected-pill-has': assemble(strip_our_has=lambda p: 'aria-selected' in p and ':has(' in p),
        'feel-D-no-ping-colour-has': assemble(strip_our_has=lambda p: ':has(' in p and 'aria-selected' not in p and not p.startswith('@')),
    }
    for name, css in files.items():
        (out / f'{name}.theme.css').write_text(css, encoding='utf8')
        t = COMMENT.sub('', css)
        print(f'{name:40}{len(css):>8} bytes  braces {t.count("{")}/{t.count("}")}  :has( {t.count(":has(")}')


if __name__ == '__main__':
    main()
