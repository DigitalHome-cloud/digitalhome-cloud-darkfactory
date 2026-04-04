# Feedback & Validation

## Validation Item

Used in the Designer's NF C 15-100 validation panel to display circuit check results.

### Structure

```
Validation Item
├── Left accent border (3px, color-coded by severity)
├── Severity icon (text: "!!" / "!" / "i")
└── Message text
```

### Severity Levels

| Severity | Border color | Icon color | Icon text |
|----------|-------------|------------|-----------|
| Error | `#ef4444` | `#ef4444` | `!!` |
| Warning | `#f59e0b` | `#f59e0b` | `!` |
| Info | `#3b82f6` | `#3b82f6` | `i` |

### Item Styling

| Property | Value |
|----------|-------|
| Padding | `0.4rem 0.5rem` |
| Border left | `3px solid {severity-color}` |
| Background | transparent |
| Background (hover) | `rgba(148, 163, 184, 0.1)` |
| Font size | `sm` (0.75rem) |
| Border radius | `sm` (0.35rem) on right side |

### Validation Panel

| Property | Value |
|----------|-------|
| Max height | 200px |
| Overflow | `overflow-y: auto` |
| Layout | Vertical list with `gap: 0.15rem` |

## Alert / Notice

General-purpose alert for informational messages.

| Property | Value |
|----------|-------|
| Background | `rgba(15, 23, 42, 0.6)` |
| Border | `1px solid rgba(148, 163, 184, 0.3)` |
| Border radius | `base` (0.5rem) |
| Padding | `0.75rem 1rem` |
| Font size | `sm` (0.75rem) |
| Color | `#94a3b8` |

Can be color-coded by prepending a colored left border (same as validation items).

## Success State

After a successful action (save, create):
- Brief green text confirmation
- Color: `#4ade80` (action.primaryLight)
- No modal — inline or toast-like

## Error State

Form validation errors:
- Red text below the field
- Color: `#fca5a5` (danger.light)
- Font size: `xs` (0.7rem)
- Input border changes to `danger.border`

## Platform Notes

- **Mobile**: Use native toast/snackbar for transient feedback. Keep color coding for severity.
- **Node-RED**: Map to Node-RED notification nodes using the same color scheme.
- **IoT**: LED color indicators can map severity colors: green (ok), amber (warning), red (error).
