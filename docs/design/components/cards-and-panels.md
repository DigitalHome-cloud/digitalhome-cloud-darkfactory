# Cards & Panels

## Card / Tile

Used for navigation tiles (Portal home), dashboard items, and selectable entries.

| Property | Value |
|----------|-------|
| Background | `radial-gradient(circle at top left, #1e293b, #020617)` |
| Background (hover) | `radial-gradient(circle at top left, #1f2937, #020617)` |
| Border | `1px solid rgba(148, 163, 184, 0.3)` |
| Border (hover) | `1px solid #22c55e` (green accent) |
| Border radius | `2xl` (1.25rem) for Portal tiles, `xl` (1rem) for Designer/Modeler panels |
| Padding | `1rem` |
| Layout | `display: flex; flex-direction: column` |

### Hover Effect

- `transform: translateY(-2px)` — subtle lift
- `box-shadow: 0 18px 40px rgba(15, 23, 42, 0.7)` — deep shadow
- Border color shifts to accent green
- Transition: 120ms ease-out

### Disabled State

- `opacity: 0.6`
- No hover effect
- `cursor: not-allowed`

### Card Content Structure

```
Card
├── Icon / Badge (optional)
├── Title (font-size: xl, weight: semibold)
├── Description (font-size: sm, color: text.secondary)
└── Footer / Metadata (optional)
```

## Panel

Used for sidebar panels, inspector panels, and workspace sections.

| Property | Value |
|----------|-------|
| Background | Same radial gradient as card |
| Border | `1px solid rgba(148, 163, 184, 0.3)` |
| Border radius | `xl` (1rem) |
| Padding | `0.75rem 0.85rem` |
| Layout | `display: flex; flex-direction: column` |

### Panel Structure

```
Panel
├── Panel Header (title + optional actions)
│   ├── Title (font-size: lg, weight: semibold)
│   └── Action buttons (small ghost/secondary)
├── Panel Body (flex: 1, overflow-y: auto)
└── Panel Footer (optional)
```

## Auto-fit Grid

Cards arrange in a responsive grid:

```
display: grid
grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))
gap: 1.25rem
```

Wider cards (blog, dashboard) use `minmax(280px, 1fr)`.

## Platform Notes

- **Mobile**: Cards go full-width. Maintain gradient background and rounded corners. Remove hover lift (no hover on touch).
- **Node-RED**: Map card pattern to dashboard group widgets. Use the dark gradient background.
- **IoT**: Use solid `#1e293b` background instead of gradient on low-capability displays.
