# Overlays

## Form Overlay

Used for create/edit forms that appear over the main content (e.g., Library item form in Modeler).

| Property | Value |
|----------|-------|
| Background | `radial-gradient(circle at top left, #1e293b, #020617)` |
| Border | `1px solid rgba(148, 163, 184, 0.3)` |
| Border radius | `xl` (1rem) |
| Padding | `1.25rem` |
| Position | Absolute or fixed over parent |
| Z-index | Above workspace content |

Overlay forms share the same panel styling as regular panels but are positioned on top.

## Fullscreen Mode

The Designer workspace supports fullscreen editing.

| Property | Value |
|----------|-------|
| Position | `fixed` |
| Inset | `0` (fills entire viewport) |
| Z-index | 40 (above header) |
| Background | `radial-gradient(circle at top, #020617, #020617)` |
| Padding | `1rem` |
| Overflow | `auto` |

A toggle button (ghost variant) enters/exits fullscreen.

## Modal (future)

If modals are needed, follow this pattern:

### Backdrop
- `position: fixed; inset: 0`
- `background: rgba(2, 6, 23, 0.8)` — deep black overlay
- `backdrop-filter: blur(4px)`
- `z-index: 50`

### Modal Content
- Same styling as form overlay
- `max-width: 480px` for small modals, `640px` for medium
- Centered with flexbox
- Close button: ghost variant, top-right corner

## Platform Notes

- **Mobile**: Use full-screen sheets (slide up from bottom) instead of overlays. Maintain the dark background and panel styling.
- **Node-RED**: Avoid overlays — use dedicated dashboard pages or dialogs.
