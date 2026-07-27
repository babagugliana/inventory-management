---
name: vue-saas-redesign
description: Redesign the Factory Inventory Management client into a modern SaaS interface — left vertical sidebar replacing the top nav, design tokens, consistent spacing, polished card surfaces. Use when asked to redesign, modernize, or restyle the UI, move navigation to a sidebar, apply a design system, or make the app look like a professional SaaS product.
---

# Vue SaaS Redesign

Converts this app's top-nav layout into a modern SaaS interface: a fixed left sidebar, a page toolbar holding the global filters, design tokens, and restyled shared surfaces.

This is a **repeatable** procedure. The repo resets to `main` via `/reset-branch`, so the skill must be runnable from a clean checkout every time.

## Why this works with a small diff

Six primitives live in **`App.vue`'s unscoped `<style>` block** and are used across 4–7 view files:

`.card` · `.page-header` · `.stat-card` · `.stats-grid` · `.badge` · `.table-container`

Restyling those six propagates to every view without editing it. Only three files override them in scoped blocks, and Phase 4 reconciles exactly those. **Do not rewrite view templates to use new wrapper components** — it produces a large diff for the same visual result.

## Non-negotiable constraints

- **Delegate every `.vue` create/modify to the `vue-expert` subagent.** `CLAUDE.md` makes this mandatory. Non-`.vue` files (`main.js`, `locales/*.js`) you edit directly.
- **No emojis in UI.**
- **Keep the slate palette.** This is a structural redesign, not a rebrand. Tokens map from hexes already in the codebase.
- **Never touch `server/`, `client/src/api.js`, or filter semantics.** Pure presentation change. If a filter stops driving data, the redesign has failed.
- **Every new string goes through `t()`** and lands in **both** `locales/en.js` and `locales/ja.js`.
- **Unique `v-for` keys** — never the array index.

---

## Phase 0 — Preflight

1. **Refuse to run on `main`.** Check `git branch --show-current`. If `main`, stop and tell the user to create a branch (`/demo-branch`).
2. **Confirm the working tree is clean**, or that the user accepts mixing changes.
3. **Start the servers** if not already up: `./scripts/start.sh`. Frontend `:3000`, backend `:8001`.
4. **Capture the baseline.** With Playwright, screenshot all six routes at 1440px:
   `/` · `/inventory` · `/orders` · `/spending` · `/demand` · `/reports`
   These are the reference for Phase 4, where removing scoped overrides is a real visual change and not just cleanup.

## Phase 1 — Design tokens

Insert the full contents of `references/design-tokens.css` at the **top of `App.vue`'s global `<style>` block** (the unscoped one — `App.vue` has no `scoped` attribute, which is what makes the cascade work).

Do not invent new colors. Every token maps to a hex already present in `client/src/`.

## Phase 2 — Shell

Delegate to `vue-expert`. Three pieces:

### `components/AppSidebar.vue` (new)

- Brand block at top: `t('nav.companyName')` and `t('nav.subtitle')` stacked, not inline
- Six `router-link` nav items in order: Overview `/`, Inventory `/inventory`, Orders `/orders`, Finance `/spending`, Demand `/demand`, Reports `/reports`
- Active state: `--color-accent-bg` fill, `--color-accent` text, and a 3px left accent bar. Match on `$route.path` exactly for `/`, prefix for the rest
- Footer pinned to the bottom: `ProfileMenu` + `LanguageSwitcher`
- Fixed position, `width: var(--sidebar-width)`, full viewport height, `--color-surface` background, right hairline border

### `components/PageToolbar.vue` (new)

- Reads `$route.meta.titleKey` and `$route.meta.subtitleKey`, renders them through `t()`
- Hosts the existing `FilterBar` component inline beneath the title
- Sits at the top of the content column and scrolls with the page

### `App.vue` (rewrite shell)

- `.app` becomes `display: grid; grid-template-columns: var(--sidebar-width) 1fr;`
- Content column scrolls independently; sidebar stays fixed
- **Delete** `.top-nav`, `.nav-container`, `.nav-tabs`, `.logo`, `.subtitle` rules and the `<header class="top-nav">` markup
- `<main class="main-content">` keeps `PageToolbar` above `<router-view />`
- `ProfileMenu` and `LanguageSwitcher` move out of the header into `AppSidebar`
- `TasksModal` and `ProfileDetailsModal` stay mounted at `App.vue` level

### Route metadata (`main.js`, edit directly)

Add to each of the six routes:

```js
{ path: '/', component: Dashboard, meta: { titleKey: 'pages.overview.title', subtitleKey: 'pages.overview.subtitle' } }
```

Then add the twelve keys to **both** `locales/en.js` and `locales/ja.js`.

### Remove duplicated page headers

Each view renders its own `.page-header` block. Now that `PageToolbar` owns the title, delete that markup from all seven view files. Deletions only — do not restructure the views.

## Phase 3 — Shared surfaces

Restyle the six global primitives in `App.vue` against tokens. Target treatment:

| Primitive | Treatment |
|---|---|
| `.card` | `--radius-lg`, 1px `--color-border`, `--shadow-xs`, `--space-6` padding. Drop heavy box-shadows |
| `.stat-card` | Label above value. Label `--text-xs` uppercase `--color-ink-muted`; value `--text-2xl` `--weight-bold` `--color-ink` |
| `.stats-grid` | `repeat(auto-fit, minmax(220px, 1fr))`, `--space-4` gap |
| `.badge` | `--radius-full`, `--text-xs`, `--weight-semibold`, status token pairs (`--color-success` on `--color-success-bg`, etc.) |
| `.table-container` | Border + `--radius-lg`, sticky header row on `--color-tint`, `--space-3`/`--space-4` cell padding |
| `.page-header` | Retained for any view still using it, restyled to match `PageToolbar` |

Replace every ad-hoc `rem` margin in the global block with a spacing token.

## Phase 4 — Reconcile scoped overrides

Three files redefine primitives in their scoped blocks and will not inherit the cascade until the duplicates are removed:

| File | Remove |
|---|---|
| `views/Reports.vue` | `.card`, `.stat-card`, `.stats-grid`, `.badge` |
| `views/Dashboard.vue` | `.page-header` |
| `views/Inventory.vue` | `.page-header` |

**Screenshot-diff each against the Phase 0 baseline.** Some of those overrides may be intentional visual differences rather than drift. If a page looks worse after removal, restore the specific declaration and note it.

Then sweep remaining hardcoded hexes in those three files to tokens.

## Phase 5 — Verify

Playwright, six routes × {1440px, 1024px} × {`en`, `ja`}. All four must hold:

1. **No horizontal page scroll** at either width
2. **Sidebar active state matches the route** on every page
3. **Filters still drive data** — change Location to `Tokyo` on `/`, confirm the stat values change
4. **Modals still open** — profile menu, tasks modal, and at least one detail modal

Report failures with the screenshot, don't paper over them.

---

## Gotchas

**Popover direction.** `ProfileMenu` and `TasksModal` currently anchor to the top-right of the top nav and open **downward**. In a sidebar footer they must open **upward and to the right**, or they render off-screen. This is the single most likely thing to break and it looks obviously wrong.

**Japanese label width.** `ja` nav strings are longer than `en`. Verify the sidebar in Japanese — at 240px, labels may wrap. Fix by tightening nav padding, not by widening the sidebar.

**`Reports.vue` is the outlier.** It overrides four of the six primitives. It is the page most likely to shift unexpectedly in Phase 4.

**`Dashboard.vue` is 1,271 lines.** When delegating it, give `vue-expert` the specific selector to change rather than asking it to read and rewrite the file.

## Out of scope

Individual restyling of the 8 detail modals (they inherit tokens only) · backend changes · dark mode · collapsible icon-rail sidebar · replacing the hand-written SVG charts.
