# Node-RED Adaptation

Guidelines for applying the DHC design language to Node-RED dashboards and custom nodes.

## General Principles

1. **Dark theme**: Configure Node-RED Dashboard 2.0 to use a dark theme with DHC surface colors
2. **Same color tokens**: Use the exact hex values from `tokens/colors.json` for backgrounds, text, and accents
3. **Design view colors**: Map chart series, status indicators, and category groups to the 8 design view colors
4. **Consistent typography**: Use the system font stack where configurable

## Surface Mapping

| DHC Surface | Node-RED Element |
|-------------|-----------------|
| `surface.primary` (#0f172a) | Dashboard page background |
| `surface.deep` (#020617) | Widget input backgrounds, chart areas |
| `surface.elevated` (#1e293b) | Widget card backgrounds, group headers |

## Widget Styling

### Buttons
- Primary actions: Green tint matching `action.primary` (#22c55e)
- Danger actions: Red tint matching `danger.base` (#ef4444)
- Use pill shape where possible (high border-radius)

### Gauges and Charts
- Background: `surface.deep`
- Grid lines: `rgba(148, 163, 184, 0.2)` (border.subtle)
- Data series: Assign design view colors in order of relevance
- Text labels: `text.secondary` (#9ca3af)

### Status Indicators
- Use the standard severity colors:
  - OK/active: `#22c55e` (green)
  - Warning: `#f59e0b` (amber)
  - Error/alarm: `#ef4444` (red)
  - Info: `#3b82f6` (blue)
  - Offline/unknown: `#64748b` (muted)

### Text and Labels
- Primary text: `#e5e7eb`
- Secondary text: `#9ca3af`
- Section headers: Uppercase, letter-spacing 0.05em, `#94a3b8`

## Design View in Dashboards

When building dashboards organized by smart-home domain:

| Dashboard Tab/Group | View Color |
|--------------------|------------|
| Rooms & Zones | `#22c55e` (spatial green) |
| Electrical Monitoring | `#3b82f6` (electrical blue) |
| Heating & HVAC | `#ef4444` (heating red) |
| Network Status | `#a855f7` (network purple) |
| Automation Rules | `#ec4899` (automation pink) |

Use the view color as group header accent or tab indicator.

## Borders and Edges

- Widget borders: `1px solid rgba(148, 163, 184, 0.3)`
- Use `border-radius: 0.75rem` for widget cards where supported
- Avoid sharp corners (0px radius) — they don't match the DHC aesthetic

## Limitations

Node-RED Dashboard 2.0 has limited CSS customization compared to a React app. Focus on:
- Colors (most configurable)
- Basic typography (font family, size)
- Status indicators (direct color mapping)

Accept that pixel-perfect parity with the Gatsby apps is not the goal — visual coherence and color consistency are.
