# Accessibility

## Color Contrast

All text must meet WCAG 2.1 AA minimum contrast ratios against the primary background (`#0f172a`):

| Text Token | Hex | Ratio vs #0f172a | Passes |
|------------|-----|-------------------|--------|
| `text.primary` | `#e5e7eb` | 12.4:1 | AAA |
| `text.heading` | `#e2e8f0` | 12.0:1 | AAA |
| `text.nav` | `#cbd5f5` | 9.5:1 | AAA |
| `text.secondary` | `#9ca3af` | 4.6:1 | AA (normal text) |
| `text.slate` | `#94a3b8` | 4.3:1 | AA (normal text) |
| `text.muted` | `#64748b` | 3.2:1 | AA (large text only) |

**Rule**: `text.muted` may only be used for decorative, supplementary, or large text. Never use it for labels, buttons, or links that users need to read.

### On Elevated Surfaces (#1e293b)

| Text Token | Ratio vs #1e293b | Passes |
|------------|-------------------|--------|
| `text.primary` | 8.2:1 | AAA |
| `text.secondary` | 3.2:1 | AA (large text only) |
| `text.muted` | 2.2:1 | Fails |

**Rule**: On cards and panels (elevated surface), avoid `text.muted`. Use `text.slate` or higher for all readable text.

## Focus Indicators

Every interactive element must have a visible focus indicator:

| Element | Focus style |
|---------|-------------|
| Form inputs | `border-color: #22c55e` (green) |
| Buttons | `border-color: #0ea5e9` (cyan) or browser default outline |
| Nav links | Border becomes visible (same as hover) |
| Sidebar items | Background highlight (same as hover) |
| Checkboxes | Native focus ring |

Focus indicators must not rely solely on color change — a visible border or outline change is required.

## Keyboard Navigation

- All interactive elements (links, buttons, inputs, sidebar items) must be focusable via Tab
- Enter/Space activates buttons and links
- Sidebar expand/collapse responds to Enter/Space
- Tab bar items are navigable with Tab
- Escape closes overlays and fullscreen mode

## Touch Targets

| Context | Minimum size |
|---------|-------------|
| Web (desktop) | No minimum (mouse precision) |
| Web (tablet, < 1024px) | 44px x 44px |
| Mobile apps | 44pt x 44pt (iOS) / 48dp x 48dp (Android) |

Current smallest interactive element: canvas zoom buttons at 26x26px. These are desktop-only; mobile adaptations must enlarge them.

## Color Independence

- **Design view colors** must always be paired with a text label
- **Capability badges** display both a letter (A/S/C) and color
- **Validation severity** uses icon text ("!!", "!", "i") in addition to colored borders
- **Status pills** display text ("DEMO", username) alongside color

Never rely on color alone to convey meaning.

## Screen Readers

- Use semantic HTML elements: `<nav>`, `<main>`, `<header>`, `<footer>`, `<section>`
- Add `aria-label` to icon-only buttons (expand/collapse, zoom controls)
- Add `aria-expanded` to collapsible sidebar sections
- Tables use `<th>` with `scope="col"` for column headers
- Language switcher buttons have `aria-current="true"` for active language

## Reduced Motion

Respect `prefers-reduced-motion`:
- Disable card hover lift (`transform: translateY`)
- Disable chevron rotation animation
- Keep color transitions (they don't cause motion sickness)

```css
@media (prefers-reduced-motion: reduce) {
  * { transition-duration: 0.01ms !important; }
}
```

## Platform Notes

- **Mobile**: Follow iOS/Android accessibility guidelines in addition to this document. Support Dynamic Type (iOS) and font scaling (Android).
- **Node-RED**: Ensure custom dashboard widgets pass contrast requirements.
- **IoT**: Physical buttons/controls should have tactile feedback. Display text must meet contrast requirements.
