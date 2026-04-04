# Badges & Pills

## Navigation Pill

Status indicator in the header showing auth state.

| Property | Value |
|----------|-------|
| Font size | `sm` (0.75rem) |
| Font weight | `semibold` (600) |
| Padding | `0.2rem 0.6rem` |
| Border radius | `full` (999px) |
| Background (default) | `rgba(148, 163, 184, 0.12)` |
| Color (default) | `#94a3b8` |
| Border (default) | `1px solid rgba(148, 163, 184, 0.4)` |

### Variants

| Variant | Background | Color | Border |
|---------|-----------|-------|--------|
| Default (neutral) | `rgba(148, 163, 184, 0.12)` | `#94a3b8` | `rgba(148, 163, 184, 0.4)` |
| OK (authenticated) | `rgba(34, 197, 94, 0.15)` | `#4ade80` | `rgba(34, 197, 94, 0.4)` |
| Error | `rgba(239, 68, 68, 0.15)` | `#fca5a5` | `rgba(239, 68, 68, 0.4)` |
| Locked | `rgba(239, 68, 68, 0.15)` | `#fca5a5` | `rgba(239, 68, 68, 0.4)` |

## Status Badge

Small inline badge for labels and categories.

| Property | Value |
|----------|-------|
| Font size | `2xs` (0.65rem) |
| Font weight | `bold` (700) |
| Padding | `0.1rem 0.4rem` |
| Border radius | `full` (999px) |

Colored by context (green for active, slate for neutral, etc.).

## Capability Badge

Used in the Modeler library to indicate device capabilities.

| Capability | Background | Text | Border |
|------------|-----------|------|--------|
| Actor | `rgba(168, 85, 247, 0.2)` | `#c084fc` | `rgba(168, 85, 247, 0.4)` |
| Sensor | `rgba(34, 197, 94, 0.2)` | `#4ade80` | `rgba(34, 197, 94, 0.4)` |
| Controller | `rgba(59, 130, 246, 0.2)` | `#60a5fa` | `rgba(59, 130, 246, 0.4)` |

Each displays a single letter (A, S, C) in a small pill.

## View Dot

Small colored circle indicating the ontology design view of an item.

| Property | Value |
|----------|-------|
| Size | 8px x 8px |
| Border radius | 50% (circle) |
| Background | Design view color (see [semantic-views.md](../patterns/semantic-views.md)) |
| Box shadow | `0 0 6px currentColor` (subtle glow) |

Always accompanied by a text label — never use color alone.

## Badge Pattern (general)

All badges follow this formula:

1. **Background**: Base color at 10-20% opacity
2. **Text**: Lighter version of the base color
3. **Border**: Base color at 40% opacity
4. **Shape**: Fully rounded (`999px`)
5. **Size**: Small font (0.65–0.75rem), tight padding

This ensures badges are visible but don't compete with primary content.
