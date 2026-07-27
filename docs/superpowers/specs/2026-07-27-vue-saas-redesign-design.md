# vue-saas-redesign — Design

**Date:** 2026-07-27
**Status:** Approved
**Scope:** A project-specific Claude Code skill that converts this app's top-nav layout into a modern SaaS interface with a left sidebar, design tokens, and consistent spacing.

## Problem

The Factory Inventory Management client uses a 70px sticky top nav (`App.vue`) with six router-links, a language switcher and a profile menu, plus a full-width `FilterBar` strip beneath it. Styling is a mix of global CSS in `App.vue` and scoped blocks across 22 components, with 50 distinct hardcoded hex colors and ad-hoc `rem` spacing. There are no design tokens.

The goal is a repeatable skill — not a one-off edit — because this repo is a demo that resets to `main` (`/demo-branch`, `/reset-branch`). The redesign needs to be re-runnable on a fresh branch.

## Key finding that shapes the design

Styling is more centralized than it appears. Six primitives live in `App.vue`'s **unscoped** `<style>` block and are used across 4–7 view files:

`.card`, `.page-header`, `.stat-card`, `.stats-grid`, `.badge`, `.table-container`

Restyling those six classes propagates to every view without editing it. Only three files override them in scoped blocks:

| File | Overrides |
|---|---|
| `views/Reports.vue` | `.card`, `.stat-card`, `.stats-grid`, `.badge` |
| `views/Dashboard.vue` | `.page-header` |
| `views/Inventory.vue` | `.page-header` |

The 50 hex colors are dominated by 13 values, all coherent slate. A ~16-token palette covers effectively all of them.

**Consequence:** "shell + shared surfaces" is a ~12-file change, not a 22-file one.

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Skill scope | Project-specific (`.claude/skills/`) | Can name exact files and reuse the existing palette; more reliable than a generic skill |
| Skill behavior | Executes the redesign | Repeatable against the demo-branch workflow |
| Redesign depth | Shell + shared surfaces | Highest polish-per-risk; views inherit via cascade |
| Layout | Fixed 240px sidebar; filters in a page toolbar | Most conventional SaaS layout; simplest migration |
| Execution strategy | Hybrid — extract shell components, cascade primitives | Shell is genuinely new markup; rewriting 7 view templates to use `<BaseCard>` is a large diff for the same visual result |
| Page titles | Route `meta`, read by `PageToolbar` | Keeps a single `FilterBar` instance while matching title-above-filters ordering |

## Architecture

```
.claude/skills/vue-saas-redesign/
├── SKILL.md                     # 6-phase workflow + constraints
└── references/
    └── design-tokens.css        # the exact :root block to insert
```

### Target layout

```
┌────────────┬──────────────────────────────────┐
│ CATALYST   │  Page title                      │
│ Components │  Subtitle                        │
│            │  ┌ Period ┐┌ Loc ┐┌ Cat ┐┌ Stat ┐│
│ ▎Overview  │  └───────┘└─────┘└─────┘└──────┘│
│  Inventory │  ────────────────────────────────│
│  Orders    │  ┌─────┐┌─────┐┌─────┐┌─────┐   │
│  Finance   │  │ stat││ stat││ stat││ stat│   │
│  Demand    │  └─────┘└─────┘└─────┘└─────┘   │
│  Reports   │  ┌──────────────┐┌────────────┐ │
│ ─────────  │  │    chart     ││   table    │ │
│ JD  ⚙ EN   │  └──────────────┘└────────────┘ │
└────────────┴──────────────────────────────────┘
   240px fixed          scrolling content column
```

`App.vue`'s `.app` becomes `display: grid; grid-template-columns: var(--sidebar-w) 1fr`. The sidebar is fixed and full-height; the content column scrolls independently.

### New components

**`AppSidebar.vue`** — brand block (company name + subtitle), six `router-link` nav items with a left accent bar denoting the active route, and a footer holding `ProfileMenu` and `LanguageSwitcher`.

**`PageToolbar.vue`** — reads `$route.meta.titleKey` / `$route.meta.subtitleKey` through `t()`, renders the title and subtitle, and hosts the existing `FilterBar` inline beneath them.

### Files touched

| File | Change |
|---|---|
| `components/AppSidebar.vue` | new |
| `components/PageToolbar.vue` | new |
| `App.vue` | grid shell; delete `.top-nav`/`.nav-tabs`/`.nav-container`; insert token block; restyle 6 primitives |
| `main.js` | add `meta: { titleKey, subtitleKey }` to all 6 routes |
| `locales/en.js`, `locales/ja.js` | title/subtitle keys for all 6 pages |
| `views/*.vue` (7) | delete now-duplicate `.page-header` markup |
| `views/Reports.vue` | remove 4 scoped overrides |
| `views/Dashboard.vue`, `views/Inventory.vue` | remove `.page-header` override |

## Workflow (the six phases)

**Phase 0 — Preflight.** Refuse to run on `main`. Start servers via `scripts/start.sh` if not already up. Capture Playwright baseline screenshots of all 6 routes.

**Phase 1 — Tokens.** Insert the `:root` block from `references/design-tokens.css` into `App.vue`'s global style. Color tokens map from the 13 dominant hexes already in use — this preserves the slate identity. The redesign is structural, not a rebrand.

**Phase 2 — Shell.** Create `AppSidebar.vue` and `PageToolbar.vue`; convert `App.vue` to the grid layout; add route meta; add locale keys; delete duplicate `.page-header` markup from views.

**Phase 3 — Primitives.** Restyle the six global classes against tokens: 10px radius, 1px borders replacing heavy shadows, consistent 20–24px padding, stat cards with label-above-value hierarchy. Ad-hoc `rem` margins become spacing tokens.

**Phase 4 — Reconcile overrides.** Strip the duplicate declarations from `Reports.vue`, `Dashboard.vue` and `Inventory.vue` so they inherit the cascade. Screenshot-diff each against the phase 0 baseline — some overrides may be intentional, and this is where that surfaces.

**Phase 5 — Verify.** Playwright across 6 routes × {1440px, 1024px} × {en, ja}. Assertions:
- no horizontal page scroll
- sidebar active state matches the current route
- changing a filter still changes displayed numbers
- every modal still opens

## Constraints the skill enforces

- **Delegate every `.vue` create/modify to `vue-expert`** — mandated by `CLAUDE.md`
- No emojis in UI; keep the slate palette
- Never touch `server/`, `api.js`, or filter semantics — pure presentation change
- Every new string goes through `t()` and lands in **both** `locales/en.js` and `locales/ja.js`
- Unique `v-for` keys (never index)

## Known gotchas (called out explicitly in SKILL.md)

1. **Popover direction.** `ProfileMenu` and `TasksModal` anchor to the top-right of the top nav and open downward. In a sidebar footer they must open *upward and rightward*, or they render off-screen.
2. **Japanese label width.** `ja` nav strings are longer than `en`. A 240px sidebar must be verified in Japanese or labels wrap.
3. **`Reports.vue` overrides may be intentional.** Removing them is a visual change, not just a cleanup — the baseline diff is the check.

## Out of scope

- Restyling the 8 detail modals individually (they inherit tokens only)
- Any backend change
- Dark mode
- Collapsible / icon-rail sidebar
- Replacing the hand-written SVG charts
