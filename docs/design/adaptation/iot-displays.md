# IoT Display Adaptation

Guidelines for applying the DHC design language to constrained IoT displays (smart panels, e-ink screens, LED indicators).

## Display Categories

### Category A: Full-Color LCD/OLED (e.g., wall-mounted touch panels)

Apply the full DHC dark theme:
- Background: `#0f172a` (LCD) or `#020617` (OLED — saves power with true black)
- Text: `#e5e7eb` primary, `#9ca3af` secondary
- Accents: Full design view color palette
- Touch targets: Minimum 48px for finger interaction
- Gradients: Simplify to solid colors if rendering performance is limited

### Category B: Low-Color / Segment Displays

Reduce the palette to essential contrasts:
- Background: Black (#000000)
- Primary text: White (#ffffff)
- Status OK: Green approximation
- Status Error: Red approximation
- Status Warning: Amber/yellow approximation
- No gradients, no semi-transparency

### Category C: LED Indicators

Map status and design views to LED colors:

| Meaning | LED Color |
|---------|-----------|
| OK / Active / Spatial | Green |
| Warning / Building | Amber/Yellow |
| Error / Heating | Red |
| Info / Electrical | Blue |
| Network | Purple (if available) or blue blink |
| Automation | Pink (if available) or green blink |
| Offline | Off or dim white |

### Category D: E-ink Displays

Dark theme **does not apply** to e-ink:
- Use high-contrast black-on-white
- No gradients, no color
- Bold text for emphasis (no color-based hierarchy)
- Simple line borders (1px solid black)

## Typography on Constrained Displays

- Use the largest legible font for the display resolution
- Prefer bold weight for readability at small sizes
- Limit text to essential information (status, values, labels)
- No uppercase transforms on very small displays (harder to read)

## Layout on Fixed Displays

- No responsive reflow — design for the exact resolution
- Use simple grid layouts (2x2, 3x1, etc.)
- Prioritize the most important information in the top-left
- Status indicators and values are more important than labels

## Interaction

- **Touch panels**: Follow mobile touch target guidelines (48px minimum)
- **Physical buttons**: Map to clear actions (up/down, select, back)
- **No hover states**: Remove all hover-based interactions
- **Immediate feedback**: Use color change for press acknowledgment

## Connectivity Indicators

On IoT displays, always show connection status:
- Cloud connected: Green dot or icon
- Cloud disconnected: Red dot or icon
- Local only: Amber dot

Use the standard severity color mapping from the design tokens.
