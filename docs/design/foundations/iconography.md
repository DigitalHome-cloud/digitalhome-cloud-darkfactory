# Iconography

## Current Approach

DigitalHome.Cloud does **not** use an icon library (no Font Awesome, Feather, Material Icons, etc.). Icons are implemented through:

### 1. Unicode Emoji (Portal)

The Portal uses emoji for tile icons and navigation cues:
- `🏠` Home/design, `🛠️` Tools, `🎛️` Controls, `📡` Monitoring
- `🔐` Sign-in (locked), `🔓` Account (unlocked)
- `📝` Blog, `ℹ️` About, `☕` Support

### 2. Text Letters (Designer, Modeler)

The Designer and Modeler use single-character labels as icons:
- **C** — Class, **O** — Object Property, **D** — Data Property
- **A** — Actor, **S** — Sensor, **C** — Controller

Styled as small (14-16px), bold, centered in a colored circle or square.

### 3. Geometric Indicators

- **View dots**: 8px colored circles with glow shadow, representing ontology design views
- **Chevrons**: Unicode triangle `▶` rotated 90deg for expand/collapse
- **Arrows**: `→` / `←` for connection direction in inspectors

### 4. 3D Shapes (Graph visualization)

In the 3D ontology graph, node types use distinct Three.js geometries:
- Sphere — Class nodes
- Octahedron — Object Property nodes
- Box — Data Property nodes

## Guidelines

### Why No Icon Library

- **Minimal footprint** — no extra font or SVG sprite to load
- **Semantic clarity** — text labels are unambiguous; a "C" badge with the label "Class" is clearer than an abstract icon
- **Cross-platform portability** — emoji and text render everywhere without library dependencies

### When to Use Each Approach

| Context | Approach |
|---------|----------|
| Tile/card icons (user-facing, decorative) | Unicode emoji |
| Category labels (ontology types, capabilities) | Single letter in colored badge |
| Expand/collapse | Chevron character (▶) with rotation |
| Status indicators | Colored dots with optional glow |
| Direction/flow | Arrow characters (→, ←) |

### Platform Adaptation

- **Mobile**: Replace emoji with platform-native SF Symbols (iOS) or Material Symbols (Android) for better consistency. Keep text-letter badges as-is.
- **Node-RED**: Use Node-RED's built-in icon set where available. Fall back to text labels for DHC-specific concepts.
- **IoT displays**: Use text labels exclusively. Skip emoji (rendering may be inconsistent).

### Future Consideration

If an icon library is ever adopted, prefer an outline/line style that matches the UI's low-contrast, subtle aesthetic. Avoid filled/solid icon sets that would feel heavy against the dark surfaces.
