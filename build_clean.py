#!/usr/bin/env python3
"""Clean build: upstream midnight (vendored in upstream/) + our additions in addons/m0on.css.

    python build_clean.py

Writes:
  dev/src/m0on-midnight-single-hsl.theme.css   ONE FILE: upstream source + the horizontal server list inlined + our additions
                                      (no @import of either, no small user panel)
  dev/dist/m0on-midnight-variables.theme.css   just the settings + an @import of the one-file theme above (this is the file to enable)

addons/m0on.css is the one file that holds everything we add on top of upstream: settings, the Zelk palette, snippets.
What was tried and thrown out on purpose is in CLEAN-REVIEW.md (the code is in git history).
After a Discord update run   python tools/audit.py addons/m0on.css upstream/*.css
to see which rules stopped matching anything (needs tools/hashes.json from tools/extract-hashes.js).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'tools'))
from classlib import COMMENT, split_top  # noqa: E402

read = lambda p: (ROOT / p).read_text(encoding='utf8')  # noqa: E731

UPSTREAM_MODULES = ['main', 'animations', 'background-image', 'chatbar', 'colors', 'dms-button',
                    'top-bar', 'transparency-blur', 'user-panel', 'window-controls']

UPSTREAM_IMPORT = "@import url('https://refact0r.github.io/midnight-discord/build/midnight.css');"
HSL_IMPORT = re.compile(r"^@import url\('https://discordstyles\.github\.io/HorizontalServerList/[^\n]*\n", re.M)
HSL_VARS = re.compile(r":root \{\s*--HSL-server-direction:[^}]*\}\n", re.S)
IMPORT = re.compile(r"^@import[^\n]*\n", re.M)

HEADER = """/**
 * @name {name}
 * @description {description}
 * @author {author}
 * @version 2
 * @website https://github.com/m0onmo0n/M0on-Midnight
*/"""


def take_imports(css):
    """Pull every @import line out (they must come before any other rule) and return (imports, rest)."""
    return [i.strip() for i in IMPORT.findall(css)], IMPORT.sub('', css)


def unique(items):
    seen = []
    for i in items:
        if i not in seen:
            seen.append(i)
    return seen


def upstream_variables():
    """upstream's themes/midnight.theme.css without its header comment and the @import of the hosted build."""
    css = read('upstream/theme.css')
    css = css[css.index('*/') + 2:]
    return css.replace(UPSTREAM_IMPORT, '').strip()


def additions(flavor):
    """addons/m0on.css (shared) followed by the flavour's own files (palette, cards look)."""
    css = read('addons/m0on.css')
    if not flavor['hsl']:
        css = HSL_VARS.sub('', HSL_IMPORT.sub('', css))
    for part in flavor['parts']:
        css += '\n' + read(part)
    return css


# the flavours: the only difference between them is the colouring (and, for sky, the cards look)
CARD_SETTINGS = """    --card-radius: 10px; /* corner rounding of message cards */
    --card-gap: 10px; /* space between message groups */
    --card-bg: var(--bg-2); /* card colour */
    --chat-panel-opacity: 55%; /* how solid the chat panel behind the cards is (100% = opaque) */"""

FLAVORS = {
    'zelk': dict(title='M0on Midnight Zelk palette', hsl=True, author='m0onmo0n',
                 description='Zelk palette on upstream midnight with the horizontal server list. No small user panel.',
                 parts=['addons/palette-zelk.css'], extra=''),
    'midnight': dict(title='M0on Midnight', hsl=True, author='m0onmo0n',
                     description='The original custom midnight colours on upstream midnight with the horizontal server list. No small user panel.',
                     parts=['addons/palette-midnight.css'], extra=''),
    'sky': dict(title="Sky and M0on's Midnight Cards", hsl=False, author='m0onmo0n, Sky Guy 1',
                description="Cards look with Sky Guy 1's colours and extras on upstream midnight. Vertical server list. No small user panel.",
                parts=['addons/palette-midnight.css', 'overlays/cards.css', 'overlays/sky.css'], extra=CARD_SETTINGS),
}


# ---------- reading and changing upstream's variable file ----------

def top_level_rules(css):
    """Yield (start, brace, end, prelude) of each top-level {...} block in css; start is where its selector text begins."""
    depth, seg, i, n = 0, 0, 0, len(css)
    prelude_start = brace = 0
    while i < n:
        if css.startswith('/*', i):
            j = css.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        ch = css[i]
        if ch == '{':
            if depth == 0:
                brace, prelude_start = i, seg
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                yield prelude_start, brace, i + 1, COMMENT.sub('', css[prelude_start:brace]).strip()
                seg = i + 1
        elif ch == ';' and depth == 0:
            seg = i + 1
        i += 1


def split_overrides(css, theme_vars):
    """Take our values for variables that upstream's variable file already has out of the additions.

    Returns (overrides, rest): overrides is {--name: value}; rest is the additions without those declarations."""
    overrides, out, last = {}, [], 0
    for a, brace, b, prelude in top_level_rules(css):
        if prelude not in ('body', ':root'):
            continue
        inner = COMMENT.sub('', css[brace + 1:b - 1])
        kept = []
        for decl in split_top(inner, ';'):
            decl = decl.strip()
            if not decl:
                continue
            name, _, value = decl.partition(':')
            name, value = name.strip(), value.strip()
            if name in theme_vars:
                overrides[name] = value
            else:
                kept.append(decl)
        out.append(css[last:a])
        if kept:
            out.append(css[a:brace] + '{\n    ' + ';\n    '.join(kept) + ';\n}')
        else:
            out.append(''.join(COMMENT.findall(css[a:brace])))  # keep comments that sat in front of a rule that is now empty
        last = b
    out.append(css[last:])
    return overrides, ''.join(out)


VAR_LINE = re.compile(r'^([ \t]*)(--[A-Za-z0-9-]+):[ \t]*([^;]+);([ \t]*/\*.*?\*/)?', re.M)


def theme_variable_names(theme_css):
    return set(re.findall(r'^[ \t]*(--[A-Za-z0-9-]+):', theme_css, re.M))


def apply_values(theme_css, overrides):
    """Put our values into upstream's variable file, keeping its comments and noting what upstream had."""
    changed = []

    def repl(m):
        indent, name, old, comment = m.group(1), m.group(2), m.group(3).strip(), m.group(4) or ''
        if name not in overrides or overrides[name] == old:
            return m.group(0)
        changed.append(name)
        return f'{indent}{name}: {overrides[name]};{comment} /* upstream: {old} */'

    return VAR_LINE.sub(repl, theme_css), changed


# ---------- one big file: upstream midnight + the horizontal server list + our additions, no imports of either ----------

SINGLE_VALUES = {'--small-user-panel': 'off'}  # values for this build only


def file_names(name, flavor):
    single = f"m0on-{name}-single{'-hsl' if flavor['hsl'] else ''}.theme.css"
    return single, f'm0on-{name}-variables.theme.css'


def build_single(name):
    flavor = FLAVORS[name]
    theme, changed = apply_values(upstream_variables(), SINGLE_VALUES)
    imports, body = [], [theme]
    for m in UPSTREAM_MODULES:
        got, rest = take_imports(read(f'upstream/{m}.css'))
        imports += got
        body.append(rest.strip())
    if flavor['hsl']:
        # the horizontal server list goes after upstream's rules, like the @import in the Quick CSS did
        body.append('/* ===== horizontal server list (DiscordStyles/HorizontalServerList, src/main.css) ===== */\n' + read('upstream/hsl.css').strip())
    got, rest = take_imports(additions(flavor))
    imports += [i for i in got if 'HorizontalServerList' not in i]
    body.append(rest.strip())
    title = flavor['title'] + (', one file HSL' if flavor['hsl'] else ', one file')
    out = (HEADER.format(name=title, author=flavor['author'], description=flavor['description'])
           + '\n\n' + '\n'.join(unique(imports)) + '\n\n' + '\n\n'.join(body) + '\n')
    dest = ROOT / 'dev' / 'flavors' / name / 'src' / file_names(name, flavor)[0]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding='utf8')
    return dest, changed


# ---------- the variables file: just the settings, and an @import of the one-file theme ----------

# where the one-file themes are served from. jsDelivr serves them as text/css; a branch is cached for about 12 hours, so for a
# change to show at once replace the branch name with a commit id.
CDN = 'https://cdn.jsdelivr.net/gh/m0onmo0n/M0on-Midnight@clean-build/dev/flavors'

HSL_SETTINGS = """    --HSL-server-direction: column; /* column, column-reverse */
    --HSL-server-alignment: flex-start; /* flex-start, center, flex-end */
"""

EXTRA_SETTINGS = """/* more settings from our additions */
:root {{
{hsl}{cards}    --ping-colour: var(--yellow-2); /* colour of channels and DMs where you were pinged */
    --server-pill-unread: #cd664c; /* server pill: unread */
    --server-pill-ping: #e0b64f; /* server pill: ping */
    --server-pill-selected: #89b482; /* server pill: the open server */
}}
body {{
    --fancy-unread-pills: on; /* on: yellow pings and coloured server pills (needs the ServerPillColorizer plugin for the pills), off: the old behaviour */
}}"""


def build_variables(name):
    """A small theme file: the settings you can change, with our values, and an @import of the one-file theme.

    The settings come after the import, so they win over the same settings inside the one-file theme."""
    flavor = FLAVORS[name]
    single, variables = file_names(name, flavor)
    overrides, _ = split_overrides(additions(flavor), theme_variable_names(upstream_variables()))
    overrides.update(SINGLE_VALUES)  # the one-file theme has the small user panel off
    theme, changed = apply_values(upstream_variables(), overrides)
    extra = EXTRA_SETTINGS.format(hsl=HSL_SETTINGS if flavor['hsl'] else '',
                                  cards=(flavor['extra'] + '\n') if flavor['extra'] else '')
    out = (HEADER.format(name=flavor['title'] + ' variables', author=flavor['author'],
                         description='The settings for the ' + flavor['title'] + ' one-file theme. Change a value here; the theme itself is imported.')
           + "\n\n/* the theme: upstream midnight + our additions, all in one file */\n@import url('"
           + f'{CDN}/{name}/src/{single}' + "');\n\n/* ===== settings: upstream's variables with our values (the old value is noted after each change) ===== */\n"
           + theme + '\n\n' + extra + '\n')
    dest = ROOT / 'dev' / 'flavors' / name / 'dist' / variables
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding='utf8')
    return dest, len(changed)


if __name__ == '__main__':
    for flavor_name in FLAVORS:
        d, n = build_variables(flavor_name)
        print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes), {n} values changed')
        d, _ = build_single(flavor_name)
        print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes)')
