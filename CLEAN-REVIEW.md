# Clean build: what we add on top of upstream midnight

Upstream midnight (refact0r) is vendored in `upstream/` (see `upstream/VERSION.txt`). Everything we add lives in
**one file, `addons/m0on.css`**. `python build_clean.py` builds it into `clean/`.

What was tried and thrown out on purpose is in `addons/_dropped.css`. The earlier split of these files is in `addons/_old/`.

## What stays (addons/m0on.css)

| What | Notes |
|---|---|
| horizontal server list (Gibbu) import and layout variables | HSL builds only |
| 6px gap between panels | upstream default is 12px |
| top bar restored: `--top-bar-height: 36px`, `--top-bar-button-position: off` | upstream collapses the top bar and hides the back/forward arrows and title |
| shield-moon home icon | `--dms-icon-svg-url` |
| faint scrollbar thumb | `--scrollbar-auto-thumb` / `--scrollbar-thin-thumb` use `--bg-3`, like the old file |
| speaking ring follows the accent colour | `--status-speaking` |
| Zelk palette | text, background and accent variables |
| BOT instead of APP on bot tags | snippet by hanyuko |
| fullscreen emoji / sticker / GIF picker | centred at 90% over a dim backdrop |
| compact timestamps only on hover | Compact message layout only |
| category arrows on the left | rewritten for the current category markup |
| settings gear spins on hover | only the gear, not the other five |
| GIF favourites cleanup | snippet by MadelineMaid |
| unread channels red, open channel green, no unread dot | Amnissya's snippet |
| channels with a mention turn yellow | uses Discord's own mention badge |
| DMs with a real mention or reply turn yellow | needs the ServerPillColorizer plugin |
| server and folder pills: red unread, yellow ping, green selected | needs the ServerPillColorizer plugin |
| unclamp user bios | |

## What was dropped (addons/_dropped.css)

Zelk extras (rounded toolbar squares, hide scrollbars, hide profile note, hide profile message box), small avatars, the old collapse-icon-left
rule, hide profile reactions, bot forms, hide chatbox icons, the `pulse` animation (unused), cozy message padding, the message list
`overflow: hidden`, the Spotify margin, round user-panel buttons, the `--chatbar-padding` rule, the Twemoji flag font and the
dashless channel names, the hide-upper-badges rule, and the five other spin-on-hover buttons.

## Not in the clean build on purpose

- The `[class*="..."]` conversion of upstream's own rules (the clean build uses upstream's hashed classes as they are).
- Two edits we made inside upstream's modules: the typing-indicator `:has()` fix and `will-change: scroll-position` on every scroller.
- The commented-out rainbow voice avatars import, and `flipped-chatbar.css`, a module upstream no longer has.

## Upstream's own dead rules (inherited, harmless)

Eleven upstream rules point at classes that no longer exist in the client (`.shop_Mqg79R`, `.footerButton_YBm90d`,
`.contentHeader_3Rvb29` and others). Upstream's daily class updater uses an outdated class list, so these stay dead until it
catches up. They cost nothing. `python tools/audit.py addons/m0on.css upstream/*.css` lists them.
