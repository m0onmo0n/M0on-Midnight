#!/usr/bin/env python3
"""Clean build: upstream midnight (vendored in upstream/) + our additions in addons/m0on.css.

    python build_clean.py

Writes into clean/:
  m0on-midnight-hsl.theme.css         THE THEME FILE (horizontal server list): upstream's variable file with our values,
  m0on-midnight.theme.css             our additions, and an @import of upstream's hosted build for everything else
  midnight-zelk-colors-hsl.theme.css  the same thing inlined: upstream's whole source plus our additions in one big file
  midnight-zelk-colors.theme.css      (vertical)
  m0on-midnight-single-hsl.theme.css  ONE FILE: upstream source + the horizontal server list inlined + our additions (no @import of either, no small user panel)
  m0on-midnight-variables.theme.css   just the settings + an @import of the one-file theme above (this is the file to enable)
  zelk-hsl-additions.theme.css        ONLY our additions (load it after upstream midnight)

addons/m0on.css is the one file that holds everything we add on top of upstream: settings, the Zelk palette, snippets.
addons/_dropped.css is what was tried and thrown out on purpose; addons/_old/ is the previous split of the same files.
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
 * @author m0onmo0n
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


def additions(hsl):
    css = read('addons/m0on.css')
    if not hsl:
        css = HSL_VARS.sub('', HSL_IMPORT.sub('', css))
    return css


# ---------- the inlined single-file build ----------

def build_inlined(hsl):
    imports, body = [], [upstream_variables()]
    for m in UPSTREAM_MODULES:
        got, rest = take_imports(read(f'upstream/{m}.css'))
        imports += got
        body.append(rest.strip())
    got, rest = take_imports(additions(hsl))
    imports += got
    body.append(rest.strip())

    name = 'M0on Midnight Zelk palette, inlined' + (' HSL' if hsl else '')
    description = 'Upstream midnight (whole source) with the Zelk palette and a few additions, in one file'
    out = HEADER.format(name=name, description=description) + '\n\n' + '\n'.join(unique(imports)) + '\n\n' + '\n\n'.join(body) + '\n'
    dest = ROOT / 'clean' / f"midnight-zelk-colors{'-hsl' if hsl else ''}.theme.css"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out, encoding='utf8')
    return dest


# ---------- the theme file: variables + additions, upstream's build imported ----------

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


def build_theme(hsl):
    """The theme file: upstream's variable file with our values, our additions, and @imports for the rest."""
    theme = upstream_variables()
    overrides, rest = split_overrides(additions(hsl), theme_variable_names(theme))
    theme, changed = apply_values(theme, overrides)
    not_applied = sorted(set(overrides) - set(changed))  # same value as upstream's, or not found
    got, rest = take_imports(rest)
    imports = [UPSTREAM_IMPORT] + got
    name = 'M0on Midnight Zelk palette' + (' HSL' if hsl else '')
    out = (HEADER.format(name=name, description='Upstream midnight (imported) with our variable values and a few additions')
           + '\n\n/* upstream midnight, loaded from its own site */\n' + '\n'.join(unique(imports))
           + "\n\n/* ===== variables: upstream's file with our values (the old value is noted after each change) ===== */\n"
           + theme + '\n\n/* ===== our additions ===== */\n' + rest.strip() + '\n')
    dest = ROOT / 'clean' / f"m0on-midnight{'-hsl' if hsl else ''}.theme.css"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(out, encoding='utf8')
    return dest, len(changed), not_applied


# ---------- one big file: upstream midnight + the horizontal server list + our additions, no imports of either ----------

SINGLE_VALUES = {'--small-user-panel': 'off'}  # values for this build only


def build_single():
    theme, changed = apply_values(upstream_variables(), SINGLE_VALUES)
    imports, body = [], [theme]
    for m in UPSTREAM_MODULES:
        got, rest = take_imports(read(f'upstream/{m}.css'))
        imports += got
        body.append(rest.strip())
    # the horizontal server list goes after upstream's rules, like the @import in the Quick CSS did
    body.append('/* ===== horizontal server list (DiscordStyles/HorizontalServerList, src/main.css) ===== */\n' + read('upstream/hsl.css').strip())
    got, rest = take_imports(additions(True))
    imports += [i for i in got if 'HorizontalServerList' not in i]
    body.append(rest.strip())
    name = 'M0on Midnight Zelk palette, one file HSL'
    out = (HEADER.format(name=name, description='Upstream midnight and the horizontal server list inlined, plus our additions. No small user panel.')
           + '\n\n' + '\n'.join(unique(imports)) + '\n\n' + '\n\n'.join(body) + '\n')
    dest = ROOT / 'clean' / 'm0on-midnight-single-hsl.theme.css'
    dest.write_text(out, encoding='utf8')
    return dest, changed


# ---------- the variables file: just the settings, and an @import of the one-file theme ----------

# where the one-file theme is served from. jsDelivr serves it as text/css; a branch is cached for about 12 hours, so for a
# change to show at once replace the branch name with a commit id.
MEGA_URL = 'https://cdn.jsdelivr.net/gh/m0onmo0n/M0on-Midnight@clean-build/clean/m0on-midnight-single-hsl.theme.css'

EXTRA_SETTINGS = """/* more settings from our additions */
:root {
    --HSL-server-direction: column; /* column, column-reverse */
    --HSL-server-alignment: flex-start; /* flex-start, center, flex-end */
    --ping-colour: var(--yellow-2); /* colour of channels and DMs where you were pinged */
    --server-pill-unread: #cd664c; /* server pill: unread */
    --server-pill-ping: #e0b64f; /* server pill: ping */
    --server-pill-selected: #89b482; /* server pill: the open server */
}
body {
    --fancy-unread-pills: on; /* on: yellow pings and coloured server pills (needs the ServerPillColorizer plugin for the pills), off: the old behaviour */
}"""


def build_variables():
    """A small theme file: the settings you can change, with our values, and an @import of the one-file theme.

    The settings come after the import, so they win over the same settings inside the one-file theme."""
    overrides, _ = split_overrides(additions(True), theme_variable_names(upstream_variables()))
    overrides.update(SINGLE_VALUES)  # the one-file theme has the small user panel off
    theme, changed = apply_values(upstream_variables(), overrides)
    out = (HEADER.format(name='M0on Midnight variables',
                         description='The settings for the M0on Midnight one-file theme. Change a value here; the theme itself is imported.')
           + "\n\n/* the theme: upstream midnight + the horizontal server list + our additions, all in one file */\n@import url('"
           + MEGA_URL + "');\n\n/* ===== settings: upstream's variables with our values (the old value is noted after each change) ===== */\n"
           + theme + '\n\n' + EXTRA_SETTINGS + '\n')
    dest = ROOT / 'clean' / 'm0on-midnight-variables.theme.css'
    dest.write_text(out, encoding='utf8')
    return dest, len(changed)


# ---------- additions only ----------

ADDITIONS_HEADER = """/**
 * @name M0on additions on top of midnight (Zelk palette + HSL)
 * @description Everything our Zelk HSL theme adds to refact0r's midnight theme, as one file. Load it AFTER midnight.
 * @author m0onmo0n
 * @version 2
 * @website https://github.com/m0onmo0n/M0on-Midnight
*/

/* Enable the upstream midnight theme, then this file after it (or paste the body into Quick CSS, which always loads
   last). It relies on midnight's own variables and its `container-name: body`, so it does nothing on its own. */
"""


def build_additions():
    dest = ROOT / 'clean' / 'zelk-hsl-additions.theme.css'
    dest.write_text(ADDITIONS_HEADER + '\n' + additions(True), encoding='utf8')
    return dest


if __name__ == '__main__':
    for hsl in (True, False):
        d, n, not_applied = build_theme(hsl)
        print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes), {n} values changed')
        if not_applied:
            print(f'   left alone (same as upstream or not in its file): {", ".join(not_applied)}')
    for hsl in (True, False):
        d = build_inlined(hsl)
        print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes)')
    d, n = build_variables()
    print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes), {n} values changed')
    d, changed = build_single()
    print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes), values changed here: {", ".join(changed)}')
    d = build_additions()
    print(f'wrote {d.relative_to(ROOT)} ({d.stat().st_size} bytes)')
