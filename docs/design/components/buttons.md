# Buttons

## Variants

### Primary

The main call-to-action. Green-tinted, used for save, confirm, create actions.

| Property | Value |
|----------|-------|
| Background | `rgba(22, 163, 74, 0.2)` |
| Background (hover) | `rgba(22, 163, 74, 0.3)` |
| Border | `1px solid rgba(34, 197, 94, 0.6)` |
| Border (hover) | `1px solid rgba(34, 197, 94, 0.8)` |
| Text color | `#bbf7d0` |
| Font size | `sm` (0.75rem) — `md` (0.85rem) depending on context |
| Font weight | `medium` (500) |
| Padding | `0.3rem 0.75rem` |
| Border radius | `full` (999px) — pill shape |

For hero/landing CTAs, use the gradient background: `linear-gradient(135deg, #22c55e, #0ea5e9)` with white text.

### Secondary

Lower emphasis. Same green tint but more subtle.

| Property | Value |
|----------|-------|
| Background | `rgba(22, 163, 74, 0.12)` |
| Background (hover) | `rgba(22, 163, 74, 0.18)` |
| Border | `1px solid rgba(34, 197, 94, 0.6)` |
| Text color | `#bbf7d0` |
| Font size | `sm` (0.75rem) |
| Padding | `0.25rem 0.6rem` |
| Border radius | `full` (999px) |

### Ghost

Minimal emphasis. Transparent with subtle slate border.

| Property | Value |
|----------|-------|
| Background | transparent |
| Background (hover) | `rgba(148, 163, 184, 0.08)` |
| Border | `1px solid rgba(148, 163, 184, 0.4)` |
| Text color | `#cbd5e1` |
| Font size | `sm` (0.75rem) |
| Padding | `0.25rem 0.6rem` |
| Border radius | `full` (999px) |

### Danger

Destructive actions — delete, remove, disconnect.

| Property | Value |
|----------|-------|
| Background | `rgba(239, 68, 68, 0.1)` |
| Background (hover) | `rgba(239, 68, 68, 0.2)` |
| Border | `1px solid rgba(239, 68, 68, 0.5)` |
| Text color | `#fca5a5` |
| Font size | `sm` (0.75rem) |
| Padding | `0.25rem 0.6rem` |
| Border radius | `full` (999px) |

## States

| State | Behavior |
|-------|----------|
| Default | As specified per variant |
| Hover | Increased background opacity (+5-10%) |
| Focus | Cyan or green border ring (platform dependent) |
| Disabled | `opacity: 0.5`, `cursor: not-allowed` |
| Active/Pressed | Slightly darker background |

## Sizing

| Size | Font | Padding | Use |
|------|------|---------|-----|
| Small | 0.65–0.7rem | `0.15rem 0.4rem` | Inline actions, table row actions |
| Default | 0.75rem | `0.25rem 0.6rem` — `0.3rem 0.75rem` | Most buttons |
| Large | 0.85rem | `0.5rem 1.25rem` | Hero CTA, standalone actions |

## Shape

All action buttons use **pill shape** (`border-radius: 999px`). This distinguishes them from form inputs (which use `0.45rem` radius) and cards (which use `1rem`–`1.25rem`).

## Platform Notes

- **Mobile**: Increase padding to meet 44pt minimum touch target
- **Node-RED**: Map to dashboard button widgets using the same color tokens
- **IoT**: Use solid backgrounds (no semi-transparency) on constrained displays
