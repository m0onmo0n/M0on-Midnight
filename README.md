# m0on Midnight

> **This repository ([M0on-Midnight](https://github.com/m0onmo0n/M0on-Midnight)) is the evolution of
> [zelk_moon](https://github.com/m0onmo0n/zelk_moon) and
> [Moon-midnight](https://github.com/m0onmo0n/Moon-midnight).** It replaces both: the Zelk look lives on as an
> optional palette and look here, and the midnight theme is rebuilt on selectors that survive Discord updates.

A customised [midnight-discord](https://github.com/refact0r/midnight-discord) theme with
hash-free selectors (they keep working when Discord renames its generated class names),
an optional horizontal server list, and an optional Zelk colour palette / look.

## Pick a file from `dist/`

| | Midnight colours | Zelk colours | Zelk colours + look |
|---|---|---|---|
| **Vertical server list** | `midnight.theme.css` | `midnight-zelk-colors.theme.css` | `midnight-zelk.theme.css` |
| **Horizontal server list** | `midnight-hsl.theme.css` | `midnight-zelk-colors-hsl.theme.css` | `midnight-zelk-hsl.theme.css` |

- **Zelk colours**: only the palette (Zelk's blue-green hue, midnight's darker lightness steps).
- **Zelk colours + look**: the palette plus Zelk's 10px gaps, Inter font, rounded toolbar buttons,
  hidden scrollbars / profile notes / profile message box, and the light-blue selected-channel pill.
- **Horizontal server list**: adds [Gibbu's Horizontal Server List](https://github.com/DiscordStyles/HorizontalServerList),
  imported live so it keeps updating.

Load **one** file. Copy it to your client's themes folder (BetterDiscord / Vencord / Equicord).

## Layout

```
src/midnight.theme.css      the full theme (source of truth)
palettes/zelk.css           Zelk colour palette only
palettes/zelk-look.css      Zelk gaps, extras and selected-channel pill
build.py                    builds the six files in dist/
dist/                       generated themes (committed so they can be downloaded directly)
```

## Editing

Edit `src/midnight.theme.css` (or the files in `palettes/`), then rebuild:

```bash
python build.py
```

Never edit files in `dist/` by hand; the next build overwrites them. Needs only Python 3.

## Options

Everything is a variable in `src/midnight.theme.css`. A few useful ones:

| Variable | What it does |
|---|---|
| `--small-avatars: on` | 28px avatars in Default (or Compact + "show avatars") message display |
| `--avatar-small` / `--avatar-small-left` | avatar size / left spacing |
| `--zelk-toolbar`, `--hide-scrollbars`, `--hide-profile-notes`, `--hide-profile-message-box` | Zelk extras, off by default (on in the Zelk look) |
| `--HSL-server-direction`, `--HSL-server-alignment` | horizontal server list layout (hsl files only) |

## Notes

- The theme imports a few external stylesheets (Google Fonts, the horizontal server list, Inter in the
  Zelk look). Equicord/Vencord may warn about external imports; that is expected.
- Rainbow VC avatars (rainbowglow-avatars) is commented out at the top of the source (speaking ring uses the accent colour). To enable it, uncomment the jsDelivr import. jsDelivr serves
  the stylesheet as `text/css`; `raw.githubusercontent.com` serves `text/plain`, which browsers refuse to apply.
  An `@import` only works before any other rule, so all imports stay at the top (`build.py` keeps them there).

## Credits

- [refact0r/midnight-discord](https://github.com/refact0r/midnight-discord) — the base theme.
- [schnensch0/zelk](https://github.com/schnensch0/zelk) — the original Zelk theme the palette comes from.
- [Gibbu / DiscordStyles](https://github.com/DiscordStyles/HorizontalServerList) — Horizontal Server List.
- [MEWPASCO/rainbowglow-avatars](https://github.com/MEWPASCO/rainbowglow-avatars) and the
  "Unread msg and selected channel snippet" by Amnissya — snippets bundled in the source.
