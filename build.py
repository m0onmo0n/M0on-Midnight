#!/usr/bin/env python3
"""Builds every theme variant into dist/.

    python build.py

Source of truth:  src/midnight.theme.css          (the full midnight theme)
Overlays:         overlays/zelk.css               (Zelk colors only)
                  overlays/zelk-look.css          (Zelk gaps, extras, selected pill)
                  overlays/cards.css              (message cards, gradient, plum panels, BetterFolders fix)

Variants (2 layouts x 4 flavors = 8 files):
    layout:  vertical server list (default) | horizontal server list (-hsl)
    flavor:  midnight (original palette)    -> midnight[-hsl].theme.css
             zelk-colors (Zelk palette)     -> midnight-zelk-colors[-hsl].theme.css
             zelk (Zelk palette + look)     -> midnight-zelk[-hsl].theme.css
             cards (cards look + plum)      -> midnight-cards[-hsl].theme.css
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent
read = lambda p: (ROOT / p).read_text(encoding='utf8')

HSL_IMPORT = "@import url('https://discordstyles.github.io/HorizontalServerList/HorizontalServerList.css');\n"
HSL_VARS = """
:root {
    --HSL-server-direction: column; /* column, column-reverse */
    --HSL-server-alignment: flex-start; /* flex-start, center, flex-end */
}
"""
INTER_IMPORT = "@import url('https://rsms.me/inter/inter.css');\n"

FLAVORS = {
    # key: (file suffix, label shown in the theme name)
    'midnight':    ('', None),
    'zelk-colors': ('-zelk-colors', 'Zelk colors'),
    'zelk':        ('-zelk', 'Zelk'),
    'cards':       ('-cards', 'Cards'),
}

# overlay files appended (in order) after the source for each flavor
OVERLAYS = {
    'midnight':    [],
    'zelk-colors': ['overlays/zelk.css'],
    'zelk':        ['overlays/zelk.css', 'overlays/zelk-look.css'],
    'cards':       ['overlays/cards.css'],
}


def build(flavor, hsl):
    src = read('src/midnight.theme.css')

    # imports must come before every other rule, so they all go at the top
    i = re.search(r'^@import', src, re.M).start()  # first real (uncommented) import line
    j = i
    while src.startswith('@import', j):  # end of that consecutive block
        j = src.index('\n', j) + 1
    imports = ''
    if hsl:
        imports += HSL_IMPORT
    if flavor == 'zelk':
        imports += INTER_IMPORT
    src = src[:i] + imports + src[i:j] + (HSL_VARS if hsl else '') + src[j:]

    if flavor == 'zelk':
        src = src.replace("--font: 'figtree';", "--font: 'Inter';", 1)

    file_suffix, label = FLAVORS[flavor]
    parts = [x for x in (label, 'horizontal server list' if hsl else None) if x]
    name_suffix = f" ({', '.join(parts)})" if parts else ''
    src = re.sub(r'(@name [^\n]*?)\s*\n', lambda m: m.group(1) + name_suffix + '\n', src, count=1)

    out = src.rstrip() + '\n'
    for overlay in OVERLAYS[flavor]:
        out += '\n' + read(overlay).strip() + '\n'

    name = f"midnight{file_suffix}{'-hsl' if hsl else ''}.theme.css"
    (ROOT / 'dist').mkdir(exist_ok=True)
    (ROOT / 'dist' / name).write_text(out, encoding='utf8')
    return name


if __name__ == '__main__':
    for flavor in FLAVORS:
        for hsl in (False, True):
            print('wrote dist/' + build(flavor, hsl))
