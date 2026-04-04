# Semantic Design Views

## Overview

The DHC ontology organizes smart-home concepts into **8 design views** plus a "shared" category. Each view has a dedicated color used consistently across all surfaces.

These colors are a core part of the design language — they appear in sidebar headers, graph nodes, capability badges, view indicator dots, tab bars, and chart data series.

## View Color Map

| View | Hex | Domain | Examples |
|------|-----|--------|----------|
| **Spatial** | `#22c55e` (green) | Rooms, zones, areas | LivingRoom, Kitchen, Garden |
| **Building** | `#f59e0b` (amber) | Physical structure | Wall, Door, Window, Floor |
| **Electrical** | `#3b82f6` (blue) | Electrical systems | Circuit, Outlet, Panel, Breaker |
| **Plumbing** | `#06b6d4` (cyan) | Water systems | Pipe, Faucet, Drain, WaterHeater |
| **Heating** | `#ef4444` (red) | HVAC systems | Radiator, Thermostat, HeatPump |
| **Network** | `#a855f7` (purple) | Data/connectivity | Ethernet, WiFiAP, Switch, Cable |
| **Governance** | `#f97316` (orange) | Norms, compliance | NFCRule, CircuitValidator, Regulation |
| **Automation** | `#ec4899` (pink) | Smart logic | Scene, Rule, Trigger, Schedule |
| **Shared** | `#e5e7eb` (light gray) | Cross-view / unassigned | Generic properties, base classes |

## Usage Patterns

### View Indicator Dot

Small colored circle next to items in the sidebar:

- Size: 8px x 8px, `border-radius: 50%`
- Color: view hex value
- Glow: `box-shadow: 0 0 6px currentColor`
- Always paired with a text label

### Sidebar Section Header

Each view has a collapsible section in the sidebar:

- Section title in uppercase, `text.slate` color
- View dot before the title
- Chevron for expand/collapse

### 3D Graph Nodes

In the ontology and A-Box graph visualizations:

- Node color maps to design view
- Edge/link color: lighter variant or white
- Selected node: brighter glow

### Tab Bar Filters

The Designer uses tabs to filter by view:

- Tab labels: "Spatial", "Electrical", "Shared", "All"
- Active tab bottom border uses the view color
- "All" tab uses neutral styling

### Chart/Data Series

When visualizing data by category (future dashboards, analytics):

- Assign each series the view color
- Maintain consistent ordering: Spatial first, then Building, Electrical, etc.

## Ontology Alignment

These colors correspond to the `dhc:designView` annotation in the core ontology (`dhc-core.schema.ttl`). The view assignment is authoritative — the ontology defines which classes belong to which view, and the UI reflects it.

Token source: `designView` section in [`tokens/colors.json`](../tokens/colors.json)

## Accessibility

- **Never use color alone** — always pair with text labels, letter badges, or patterns
- All 8 view colors pass WCAG AA contrast against `#020617` (deep background) and `#0f172a` (primary background) for large text
- In contexts where colors appear as small dots, the glow shadow improves visibility

## Platform Notes

- **Node-RED**: Use view colors for chart series, status indicators, and categorized widgets
- **Mobile**: Same colors apply. Use them for list section headers, graph nodes, and filter chips
- **IoT**: Map to LED colors where possible: green (spatial), blue (electrical), red (heating), purple (network)
