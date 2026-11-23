// Paste this into the Discord DevTools Console (Ctrl+Shift+I > Console).
// It collects every hashed class name (name_HASH) from Discord's own stylesheets and from the
// page, and copies them to the clipboard as JSON: { "name": ["HASH", ...], ... }
// Run it again after a Discord update to get the new hashes.
(() => {
    const re = /\.([A-Za-z][A-Za-z0-9]*)_([A-Za-z0-9_-]{6})(?![A-Za-z0-9_-])/g;
    const found = {};
    const add = (name, hash) => {
        (found[name] ??= new Set()).add(hash);
    };

    const walk = rules => {
        for (const rule of rules) {
            if (rule.selectorText) for (const m of rule.selectorText.matchAll(re)) add(m[1], m[2]);
            if (rule.cssRules) walk(rule.cssRules);
        }
    };

    let sheets = 0;
    for (const sheet of document.styleSheets) {
        // Discord's own CSS only (skip the theme / Vencord style elements)
        if (!sheet.href || !sheet.href.includes("/assets/")) continue;
        try {
            walk(sheet.cssRules);
            sheets++;
        } catch { /* cross-origin sheet */ }
    }

    // classes that are on the page right now, in case a sheet could not be read
    const dom = /^([A-Za-z][A-Za-z0-9]*)_([A-Za-z0-9_-]{6})$/;
    for (const el of document.querySelectorAll("[class]")) {
        for (const c of String(el.getAttribute("class")).split(/\s+/)) {
            const m = c.match(dom);
            if (m) add(m[1], m[2]);
        }
    }

    const out = Object.fromEntries(Object.entries(found).map(([k, v]) => [k, [...v].sort()]));
    copy(JSON.stringify(out));
    return { sheetsRead: sheets, names: Object.keys(out).length, classes: Object.values(out).reduce((n, v) => n + v.length, 0) };
})()
