# Dark Theme

## Design Decision

DigitalHome.Cloud uses a **permanent dark-only theme**. This is not a limitation — it is a deliberate design choice.

### Rationale

1. **Smart-home environment**: Users interact with the platform from within their homes, often in evening or low-light conditions. Dark interfaces reduce eye strain and glare.

2. **Dashboard context**: Control panels, 3D visualizations, and data-dense interfaces are more legible on dark backgrounds. Colored indicators (design views, status badges, graph nodes) have higher visual contrast against dark surfaces.

3. **Consistency**: A single theme means one set of colors to maintain, test, and document. No risk of light/dark inconsistencies across platforms.

4. **Professional aesthetic**: The slate/blue dark palette conveys a technical, tool-oriented identity consistent with the IoT/engineering domain.

## Surface Hierarchy

Dark themes require careful layering to create depth without relying on shadows (which are invisible against dark backgrounds).

The DHC surface system uses **background lightness** to indicate elevation:

```
Level 0 (deepest):  #020617  — inputs, canvas, footer
Level 1 (primary):  #0f172a  — page background
Level 2 (elevated): #1e293b  — cards, panels, header
Level 3 (glass):    rgba(15, 23, 42, 0.9) + blur — header overlay
```

Cards use a radial gradient from Level 2 to Level 0 to create subtle dimensionality without hard edges.

## Border Strategy

On dark surfaces, borders are the primary way to define regions. The DHC border system uses **slate-400 with varying opacity**:

| Context | Opacity | Result |
|---------|---------|--------|
| Subtle (sidebar sections) | 20% | Barely visible divider |
| Default (cards, header) | 30% | Clear but non-intrusive boundary |
| Focus (input rest state) | 40% | Slightly more prominent |
| Hover | 70% | Clearly visible, indicates interactivity |
| Active/Focus | 100% colored | Cyan or green, unmistakable focus |

## Text on Dark Surfaces

Light text on dark backgrounds inverts the typical contrast hierarchy:

- **Brightest text** (#e5e7eb, #e2e8f0) for primary content
- **Medium text** (#9ca3af, #94a3b8) for secondary/supporting content
- **Dimmest text** (#64748b) for placeholder/decorative only

Accent colors (cyan, green, amber, red) remain vivid against dark surfaces, making them effective for interactive elements and status indicators.

## Applying to Other Platforms

### Node-RED

Node-RED Dashboard 2.0 supports dark themes. Apply:
- Background: `#0f172a` for page, `#020617` for widget interiors
- Widget cards: `#1e293b` background
- Text: `#e5e7eb` primary, `#9ca3af` secondary

### Mobile Apps

- Set the app to always use dark mode (ignore system preference)
- iOS: Use `.dark` color set only
- Android: Force `Configuration.UI_MODE_NIGHT_YES`
- Map surface tokens to platform color resources

### IoT Displays

- OLED screens: Benefit from true black (#020617) for power savings
- LCD screens: Use `#0f172a` as minimum background (pure black can cause smearing)
- E-ink: Dark theme does not apply — use high-contrast black-on-white instead
