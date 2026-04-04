# Tables

## Overview

Data tables are used in the Modeler library list and Designer manager views.

## Styling

| Property | Value |
|----------|-------|
| Width | 100% |
| Border collapse | collapse |
| Font size | `sm` (0.75rem) |

### Header Row

| Property | Value |
|----------|-------|
| Background | transparent |
| Text color | `#94a3b8` (text.slate) |
| Font weight | `semibold` (600) |
| Text transform | uppercase |
| Letter spacing | `wide` (0.05em) |
| Font size | `xs` (0.7rem) |
| Padding | `0.4rem 0.6rem` |
| Border bottom | `1px solid rgba(148, 163, 184, 0.3)` |
| Text align | left |

### Body Row

| Property | Value |
|----------|-------|
| Background | transparent |
| Background (hover) | `rgba(148, 163, 184, 0.05)` |
| Text color | `#cbd5e1` |
| Padding | `0.4rem 0.6rem` |
| Border bottom | `1px solid rgba(148, 163, 184, 0.1)` |

### Cell Variants

- **Monospace value**: Uses mono font for URIs, IDs, technical strings
- **Action cell**: Contains small ghost/danger buttons, right-aligned
- **Badge cell**: Contains one or more capability/status badges

## Empty State

When the table has no data:
- Center-aligned message: "No items found" or similar
- Color: `text.muted` (#64748b)
- Font style: italic (optional)

## Platform Notes

- **Mobile**: Tables become card-based lists on narrow screens. Each row renders as a stacked card with label-value pairs.
- **Node-RED**: Use Node-RED's `ui-table` widget with dark theme colors applied.
