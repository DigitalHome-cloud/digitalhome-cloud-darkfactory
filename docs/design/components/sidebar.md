# Sidebar

## Overview

The collapsible sidebar is used in Designer (builder mode) and Modeler (ontology viewer) as the left panel in a three-column workspace.

## Dimensions

| Property | Value |
|----------|-------|
| Width | 240px (fixed) |
| Border right | `1px solid rgba(148, 163, 184, 0.2)` |
| Background | Inherits from parent (deep or gradient) |
| Padding | `0.5rem 0.75rem` |
| Overflow | `overflow-y: auto` on body |

## Structure

```
Sidebar
├── Header (optional — version badge, title)
├── Controls (expand all / collapse all buttons)
├── Body (scrollable)
│   └── Section (repeating)
│       ├── Section Header (clickable to expand/collapse)
│       │   ├── Chevron (▶, rotates 90deg when open)
│       │   ├── View Dot (colored circle)
│       │   └── Section Title (uppercase, slate text)
│       └── Section Items (visible when expanded)
│           └── Item (clickable)
│               ├── Type Icon (letter badge: C, O, D)
│               └── Item Label
└── Footer (optional)
```

## Section Header

| Property | Value |
|----------|-------|
| Font size | `xs` (0.7rem) |
| Font weight | `semibold` (600) |
| Text transform | uppercase |
| Letter spacing | `wide` (0.05em) |
| Color | `#94a3b8` (text.slate) |
| Padding | `0.3rem 0` |
| Cursor | pointer |
| Display | flex, align-items: center, gap: 0.3rem |

## Sidebar Item

| Property | Value |
|----------|-------|
| Font size | `xs` (0.7rem) |
| Color | `#cbd5e1` |
| Padding | `0.2rem 0.4rem` |
| Border radius | `sm` (0.35rem) |
| Cursor | pointer |
| Display | flex, align-items: center, gap: 0.3rem |

### States

| State | Background | Color |
|-------|-----------|-------|
| Default | transparent | `#cbd5e1` |
| Hover | `rgba(148, 163, 184, 0.08)` | `#e5e7eb` |
| Selected | `rgba(56, 189, 248, 0.12)` | `#38bdf8` |

## Chevron Animation

The expand/collapse chevron (`▶`) rotates:
- **Collapsed**: `transform: rotate(0deg)`
- **Expanded**: `transform: rotate(90deg)`
- **Transition**: `transform 0.15s`

## Responsive Behavior

Below 1024px:
- Sidebar becomes full-width (stacked above center content)
- `max-height: 300px` with `overflow-y: auto`
- Border changes from right to bottom
