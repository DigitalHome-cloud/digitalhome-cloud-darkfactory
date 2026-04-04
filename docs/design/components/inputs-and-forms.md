# Inputs & Forms

## Text Input

| Property | Value |
|----------|-------|
| Background | `#020617` (surface.deep) |
| Border | `1px solid rgba(148, 163, 184, 0.4)` |
| Border (focus) | `1px solid #22c55e` (action.primary) |
| Text color | `#e5e7eb` (text.primary) |
| Placeholder color | `#64748b` (text.muted) |
| Font size | `base` (0.8rem) |
| Padding | `0.25rem 0.4rem` |
| Border radius | `md` (0.45rem) |
| Width | 100% of container |

Focus removes the default outline and uses a green border instead.

## Select / Dropdown

| Property | Value |
|----------|-------|
| Background | `#1e293b` (surface.elevated) |
| Border | `1px solid rgba(148, 163, 184, 0.35)` |
| Text color | `#e5e7eb` |
| Font size | `sm` (0.75rem) |
| Padding | `0.3rem 0.5rem` |
| Border radius | `full` (999px) — pill shape |

The SmartHome selector in the header uses `<optgroup>` to separate demo homes from user homes.

## Textarea

Same base styling as text input, plus:
- `resize: vertical`
- `min-height: 60px`
- Line height: `tight` (1.4)

## Checkbox

| Property | Value |
|----------|-------|
| Accent color | `#22c55e` (action.primary) |
| Size | 13px x 13px |
| Cursor | pointer |

Uses native checkbox with `accent-color` for green check marks.

## Search Input

Same as text input but with additional:
- `outline: none` always
- Placeholder text describing what to search
- May include a clear button (ghost variant)

## Form Layout

### Label

| Property | Value |
|----------|-------|
| Font size | `sm` (0.75rem) |
| Font weight | `medium` (500) |
| Text transform | uppercase |
| Letter spacing | `normal` (0.04em) |
| Color | `#94a3b8` (text.slate) |
| Margin bottom | `0.25rem` |

### Field Group

- Vertical stack: label above input
- Gap between label and input: `0.25rem`
- Gap between field groups: `0.75rem`–`1.25rem`

### Form Actions

Button row at bottom of form:
- `display: flex`, `gap: 0.5rem`
- Primary action first, then secondary/cancel

## Platform Notes

- **Mobile**: Increase input padding to `0.5rem 0.75rem` for touch targets. Use native pickers for selects.
- **Node-RED**: Map to dashboard form widgets. Use the same dark input background.
- **IoT**: Text inputs may not be practical — prefer selects and toggles.
