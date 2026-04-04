# Layout Principles

## Page Types

The platform uses three page layout patterns:

### 1. Content Page

Simple centered content with max-width container. Used for: Portal home, about, blog, sign-in, Modeler library.

```
Header (sticky, glass)
Main (max-width: 1280px, centered)
  └── Content sections
Footer
```

### 2. Two-Column Workspace

Flexible main area + fixed right panel. Used for: Designer manager, Designer viewer.

```
Header (sticky, glass)
Workspace Grid (2 columns: flex | 280px, gap: 1rem)
  ├── Main area (flexible)
  └── Right panel (280px inspector)
Footer
```

### 3. Three-Column Workspace

Fixed sidebar + flexible center + fixed inspector. Used for: Designer builder, Modeler ontology viewer.

```
Header (sticky, glass)
Workspace Grid (3 columns: 240px | flex | 280px, gap: 0)
  ├── Left sidebar (240px, scrollable)
  ├── Center canvas (flexible, min-height: 500px)
  └── Right inspector (280px, scrollable)
Footer (hidden or minimal)
```

## Flexbox vs Grid

- **Flexbox**: Header layout, button groups, sidebar items, form fields, single-axis alignment
- **CSS Grid**: Page layouts, workspace columns, tile/card grids, dashboard layouts

## Responsive Strategy

**Desktop-first** with a single breakpoint:

| Breakpoint | Behavior |
|------------|----------|
| > 1024px | Full layout as designed |
| <= 1024px | Columns stack vertically, sidebar collapses to 300px max-height |

### Stacking Order (below 1024px)

Three-column workspace becomes:
1. Sidebar (full-width, max-height 300px, scrollable)
2. Center canvas (full-width)
3. Inspector panel (full-width)

### Auto-fit Grids

Tile and card grids are inherently responsive via `repeat(auto-fit, minmax(...))`:
- `minmax(220px, 1fr)` — tiles reflow from 5 columns to 1 as viewport shrinks
- `minmax(280px, 1fr)` — cards reflow similarly

No media queries needed for these grids.

## Centering and Containment

All content pages use this pattern:

```css
max-width: 1280px;
margin: 0 auto;
padding: 2rem 1.25rem 3rem;
```

## Z-Index Scale

| Z-index | Element |
|---------|---------|
| 20 | Header (sticky) |
| 40 | Fullscreen workspace |
| 50 | Modal backdrop (future) |

## Overflow

- **Sidebar body**: `overflow-y: auto` — scrolls independently
- **Inspector body**: `overflow-y: auto` — scrolls independently
- **Validation panel**: `max-height: 200px; overflow-y: auto`
- **Main content**: No overflow restriction (page scrolls naturally)

## Platform Notes

- **Mobile**: Always use single-column layout. Sidebar becomes a slide-out drawer. Inspector becomes a bottom sheet.
- **Node-RED**: Dashboard grids handle layout. Apply container max-width and spacing tokens to custom widgets.
- **IoT**: Fixed layouts sized to the display resolution. No responsive reflow.
