# Spacing & Layout

> Token file: [`tokens/spacing.json`](../tokens/spacing.json)

## Spacing Scale

A `rem`-based scale used for margins, padding, and gaps throughout the platform.

| Token | Value | px | Typical use |
|-------|-------|----|-------------|
| `1` | 0.15rem | 2.4 | Badge vertical padding, minimal gaps |
| `2` | 0.25rem | 4 | Tight padding, small form gaps |
| `3` | 0.35rem | 5.6 | Button vertical padding, compact gaps |
| `4` | 0.5rem | 8 | Sidebar padding, panel gaps, input padding |
| `5` | 0.75rem | 12 | Header padding, navigation gaps, form gaps |
| `6` | 1.0rem | 16 | Tile padding, workspace grid gaps |
| `7` | 1.25rem | 20 | Page horizontal padding, tile grid gaps |
| `8` | 1.5rem | 24 | Section vertical spacing |
| `9` | 2.0rem | 32 | Main content top padding |
| `10` | 3.0rem | 48 | Main content bottom padding |

## Page Layout

Every page follows the same root structure:

```
Root (flex column, min-height: 100vh)
├── Header (sticky, z-index: 20, glass backdrop)
├── Content (flex: 1)
│   └── Main (max-width: 1280px, centered, padded)
└── Footer
```

- **Container max-width**: 1280px for all apps
- **Horizontal padding**: 1.25rem
- **Top padding**: 2rem
- **Bottom padding**: 3rem

## Grid Systems

### Tile Grid (Portal home, dashboard views)

Auto-filling responsive grid for cards and tiles:

```
grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))
gap: 1.25rem
```

Cards use `minmax(280px, 1fr)` for wider items (blog cards, dashboard cards).

### Three-Column Workspace (Designer builder, Modeler viewer)

Fixed sidebar + flexible center + fixed inspector:

```
grid-template-columns: 240px minmax(0, 1fr) 280px
gap: 0
```

- **Left sidebar**: 240px — navigation, tree views, filters
- **Center**: Flexible — canvas, graph, editor
- **Right inspector**: 280px — property panels, details

### Two-Column Workspace (Designer manager, viewer)

Flexible main + fixed panel:

```
grid-template-columns: minmax(0, 1fr) 280px
gap: 1rem
```

### Responsive Behavior

Single breakpoint at **1024px**:

- Below 1024px: all columns stack vertically
- Sidebar gets `max-height: 300px` with overflow scroll
- Inspector becomes full-width
- Panel borders change from side to top

## Header Layout

```
Header Inner (max-width: 1280px, flex row)
├── Logo Group (mark + title/subtitle)
├── Navigation (flex, gap: 0.75rem)
└── Auth Section (flex, gap: 0.5rem)
    ├── User pill / SmartHome selector
    ├── Sign-in/out link
    └── Language switcher
```

- Padding: `0.75rem 1.25rem`
- Glass effect: `backdrop-filter: blur(10px)` + `rgba(15, 23, 42, 0.9)` background
- Sticky: `position: sticky; top: 0`

## Footer Layout

```
Footer Inner (max-width: 1280px, flex row, space-between)
├── Copyright text
└── Tagline
```

Minimal, single-line footer with muted text.
