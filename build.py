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

# Theme header (name, description) for every (flavor, horizontal) variant. Everything else in the
# header is shared, see HEADER below.
HEADERS = {
    ('midnight',    False): ('M0on Midnight',                  'Custom Midnight theme'),
    ('midnight',    True):  ('M0on Midnight HSL',              'Custom Midnight theme + HSL'),
    ('zelk-colors', False): ('M0on Midnight Zelk palette',     'Custom Midnight theme with Zelk Palette'),
    ('zelk-colors', True):  ('M0on Midnight Zelk palette HSL', 'Custom Midnight theme with Zelk Palette + HSL'),
    ('zelk',        False): ('M0on Zelk Midnight',             'Custom Midnight theme with Zelk theme features'),
    ('zelk',        True):  ('M0on Zelk Midnight HSL',         'Custom Midnight theme with Zelk theme features + HSL'),
    ('cards',       False): ('M0on Midnight Cards',            'Discord+ inspired cards with M0on midnight theme features'),
    ('cards',       True):  ('M0on Midnight Cards HSL',        'Discord+ inspired cards with M0on midnight theme features and HSL'),
}
HEADER = """/**
 * @name {name}
 * @description {description}
 * @author m0onmo0n
 * @version 1
 * @website https://github.com/m0onmo0n/M0on-Midnight
*/"""

# overlay files appended (in order) after the source for each flavor
OVERLAYS = {
    'midnight':    [],
    'zelk-colors': ['overlays/zelk.css'],
    'zelk':        ['overlays/zelk.css', 'overlays/zelk-look.css'],
    'cards':       ['overlays/cards.css'],
}

# extra overlay files appended only to the horizontal-server-list builds
OVERLAYS_HSL = {
    'cards':       ['overlays/cards-hsl.css'],
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

    file_suffix, _ = FLAVORS[flavor]
    name, description = HEADERS[(flavor, hsl)]
    header = HEADER.format(name=name, description=description)
    src = header + src[src.index('*/') + 2:]  # swap the source's leading header comment

    out = src.rstrip() + '\n'
    for overlay in OVERLAYS[flavor] + (OVERLAYS_HSL.get(flavor, []) if hsl else []):
        out += '\n' + read(overlay).strip() + '\n'

    name = f"midnight{file_suffix}{'-hsl' if hsl else ''}.theme.css"
    (ROOT / 'dist').mkdir(exist_ok=True)
    (ROOT / 'dist' / name).write_text(out, encoding='utf8')
    return name


if __name__ == '__main__':
    for flavor in FLAVORS:
        for hsl in (False, True):
            print('wrote dist/' + build(flavor, hsl))
