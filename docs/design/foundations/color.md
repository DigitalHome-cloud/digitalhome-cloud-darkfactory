# Color System

> Token file: [`tokens/colors.json`](../tokens/colors.json)

## Philosophy

DigitalHome.Cloud uses a **dark-only** theme. This is a deliberate choice:

- **Smart-home context** — dashboards and control panels are often viewed in dim rooms
- **Reduced eye strain** — extended sessions reviewing floor plans, 3D graphs, and data tables
- **Visual hierarchy** — colored accents (design views, status indicators) stand out better on dark surfaces
- **Consistency** — one theme across all surfaces, no dual-maintenance

There is no light theme and no toggle. All design work assumes dark backgrounds.

## Surface Hierarchy

Surfaces use a 4-level depth system, from deepest to most elevated:

| Level | Token | Value | Use |
|-------|-------|-------|-----|
| Deep | `surface.deep` | `#020617` | Footer, form inputs, graph canvas, code blocks |
| Primary | `surface.primary` | `#0f172a` | Main page background |
| Elevated | `surface.elevated` | `#1e293b` | Cards, panels, sidebar, header fill |
| Glass | `surface.glass` | `rgba(15,23,42,0.9)` | Header backdrop (with blur) |

Cards and panels use a **radial gradient** from elevated to deep: `radial-gradient(circle at top left, #1e293b, #020617)`. This creates subtle depth without hard edges.

## Text Hierarchy

| Level | Token | Value | WCAG on `#0f172a` | Use |
|-------|-------|-------|-------------------|-----|
| Primary | `text.primary` | `#e5e7eb` | 12.4:1 (AAA) | Body text, values |
| Heading | `text.heading` | `#e2e8f0` | 12.0:1 (AAA) | Page and section titles |
| Secondary | `text.secondary` | `#9ca3af` | 4.6:1 (AA) | Descriptions, timestamps |
| Slate | `text.slate` | `#94a3b8` | 4.3:1 (AA) | Labels, inspector text |
| Nav | `text.nav` | `#cbd5f5` | 9.5:1 (AAA) | Navigation links |
| Muted | `text.muted` | `#64748b` | 3.2:1 (AA-large) | Placeholder, tertiary info only |

**Important:** `text.muted` only passes WCAG AA for large text (18px+ or 14px bold). Use it only for decorative or secondary content, never for actionable text.

## Accent Colors

| Purpose | Token | Value | When to use |
|---------|-------|-------|-------------|
| Cyan (links) | `accent.cyan` | `#0ea5e9` | Focus rings, selected states |
| Link | `accent.link` | `#38bdf8` | Hyperlink text |
| Action (green) | `action.primary` | `#22c55e` | Primary buttons, success, active states |
| Danger (red) | `danger.base` | `#ef4444` | Delete, error, destructive actions |
| Warning (amber) | `warning.base` | `#f59e0b` | Warnings, caution indicators |
| Info (blue) | `info.base` | `#3b82f6` | Informational messages |

## State Modification Pattern

Interactive elements use a consistent pattern for hover/active/disabled states:

- **Hover**: Increase background opacity by ~5-10% (e.g., `rgba(22, 163, 74, 0.2)` → `rgba(22, 163, 74, 0.3)`)
- **Active/Selected**: Use the base color at ~12-15% opacity as background
- **Disabled**: Apply `opacity: 0.5` to the entire element
- **Focus**: Change border to `accent.cyan` (#0ea5e9) or `action.primary` (#22c55e)

Borders follow the same pattern: semi-transparent at rest, increased opacity on hover.

## Design View Colors

The 8+1 design view color system maps to ontology domains. These colors are used consistently for sidebar section headers, graph nodes, view indicator dots, and category badges.

| View | Color | Hex |
|------|-------|-----|
| Spatial | Green | `#22c55e` |
| Building | Amber | `#f59e0b` |
| Electrical | Blue | `#3b82f6` |
| Plumbing | Cyan | `#06b6d4` |
| Heating | Red | `#ef4444` |
| Network | Purple | `#a855f7` |
| Governance | Orange | `#f97316` |
| Automation | Pink | `#ec4899` |
| Shared | Light gray | `#e5e7eb` |

Always pair design view colors with a text label — never rely on color alone.

## Gradients

| Name | Value | Use |
|------|-------|-----|
| Hero | `linear-gradient(135deg, #22c55e, #0ea5e9)` | Hero accent, logo mark, primary CTA button |
| Card | `radial-gradient(circle at top left, #1e293b, #020617)` | Panel/card background |

## Capability Colors

Device capability badges use distinct colors:

| Capability | Color | Hex |
|------------|-------|-----|
| Sensor | Green | `#22c55e` |
| Actor | Purple | `#a855f7` |
| Controller | Blue | `#3b82f6` |
