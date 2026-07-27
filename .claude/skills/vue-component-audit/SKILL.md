---
name: vue-component-audit
description: Analyze Vue component structure in this app and suggest performance and code-reuse improvements — oversized components, duplicated helpers and markup, reactivity mistakes, and inconsistent API style. Use when asked to audit, analyze, review, or optimize components, find duplication, improve reuse, or investigate rendering performance.
---

# Vue Component Audit

Analyzes `client/src/` and reports ranked, concrete optimization opportunities.

**Reports by default — does not refactor.** Only make changes if the user explicitly asks. When they do, delegate every `.vue` edit to the `vue-expert` subagent (`CLAUDE.md` requires it).

## Step 1 — Measure

Run these first. Never guess at structure; the numbers drive the findings.

```bash
cd client/src

# Size — anything over ~400 lines is a splitting candidate
wc -l views/*.vue components/*.vue | sort -rn | head -12

# API style consistency
for f in views/*.vue components/*.vue; do
  if grep -q "script setup" "$f"; then s="script-setup"
  elif grep -q "setup(" "$f"; then s="composition"
  else s="OPTIONS-API"; fi
  echo "$s $f"
done | sort | uniq -c | sort -rn

# Duplicated helpers — the highest-value reuse signal
grep -rhoE "const (format[A-Za-z]+|get[A-Za-z]*Class) = " views/*.vue components/*.vue \
  | sort | uniq -c | sort -rn | awk '$1>1'

# Reactivity + correctness
grep -rn ':key="index"\|:key="i"' views/ components/
grep -rln "from 'axios'" views/ components/     # should be empty; api.js owns HTTP
grep -rn "new Date(" views/ components/ | grep -v "isNaN"   # unvalidated date parsing
```

## Step 2 — Analyze

### Performance
- **Work in methods that belongs in `computed`.** A method called from a template re-runs on every render; a computed caches until its dependencies change. Filtering, sorting, summing and chart geometry all belong in computed.
- **Chart math recomputed per element.** Look for `v-for` where each iteration calls a function doing the same aggregate work — hoist it to one computed.
- **`v-if` on frequently toggled content.** `v-if` adds/removes DOM; `v-show` flips CSS. Frequent toggles want `v-show`; rarely-shown heavy content wants `v-if`.
- **Index as `v-for` key.** Causes Vue to reuse DOM nodes incorrectly when the list reorders or filters. Use a stable id (`sku`, `id`, `month`).
- **Unnecessary deep reactivity.** Large static reference lists don't need `ref`.
- **`console.log` in render paths.** Cheap individually, but a per-row log in a 250-row table is real work and noise.

### Code reuse
- **A helper defined in more than one file** belongs in `utils/` or a composable. This is usually the single biggest win.
- **Repeated component boilerplate** (overlay + close + backdrop click) belongs in a shared composable or wrapper.
- **Repeated markup blocks** within one file are an extract-a-component signal.
- **Bypassed abstractions.** `api.js` centralizes HTTP and `utils/currency.js` centralizes money formatting — a component doing it itself is drift.
- **Mixed API styles.** This codebase uses Composition API; `<script setup>` is the modern default. Flag Options API files as inconsistent.

### Structure
- **Oversized components.** Over ~400 lines usually means several responsibilities. Suggest specific extractions by name, not "split this up."
- **Dead code.** Components imported nowhere.

## Step 3 — Report

Rank by impact-to-effort. For each finding give:

1. **What** — one sentence
2. **Where** — `file:line`
3. **Why it matters** — the actual consequence, not a principle
4. **Fix** — concrete and specific

Say plainly when something is a small win. Do not pad the list to look thorough; three real findings beat twelve trivial ones. If a metric turns out clean, say so.

## Known hot spots

Verified in this codebase as of 2026-07-27. Re-measure rather than trusting these — they may already be fixed.

| Finding | Detail |
|---|---|
| `formatDate` defined **6 times** | Across views and modals. Best reuse win — extract to `utils/date.js`. `getStockStatusClass` is duplicated twice. |
| 6 modals duplicate overlay boilerplate | `BacklogDetail`, `CostDetail`, `InventoryDetail`, `ProductDetail`, `ProfileDetails`, `Tasks`. **None handles the Escape key** — a shared `useModal` composable fixes duplication and the UX gap together. |
| `Reports.vue` is the outlier on everything | Only Options API file, only file importing `axios` directly (bypassing `api.js`), all three `:key="index"` instances, and heavy `console.log` in render — it logs per row and per chart bar across 12 months and 250 orders. |
| `Dashboard.vue` is 1,278 lines | Extraction candidates: the KPI block, the order-health donut, the category bar chart, the shortages table, the top-products table. |
| `Spending.vue` (847) and `TasksModal.vue` (621) | Next in line after Dashboard. |
| `Backlog.vue` is dead code | No route, imported nowhere. |
| Currency formatting is inconsistent | Only 2 files import `utils/currency.js`; at least one defines its own formatter. |

## Out of scope

Backend, test coverage, visual design, and accessibility beyond what surfaces incidentally.
