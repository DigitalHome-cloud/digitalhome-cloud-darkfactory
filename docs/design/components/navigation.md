# Navigation

## Header

The header is the primary navigation element across all apps.

| Property | Value |
|----------|-------|
| Position | `sticky`, `top: 0`, `z-index: 20` |
| Background | `rgba(15, 23, 42, 0.9)` (glass) |
| Backdrop filter | `blur(10px)` |
| Border bottom | `1px solid rgba(148, 163, 184, 0.3)` |
| Inner max-width | 1280px, centered |
| Padding | `0.75rem 1.25rem` |

### Header Layout

Three sections in a flex row with `justify-content: space-between`:

1. **Logo Group**: Logo mark (32x32, rounded, gradient background) + title + subtitle
2. **Navigation**: Horizontal links with `gap: 0.75rem`
3. **Auth Section**: User state, SmartHome selector, language switcher

## Navigation Links

Pill-shaped links used in the header nav.

| Property | Value |
|----------|-------|
| Font size | `md` (0.85rem) |
| Color | `#cbd5f5` (text.nav) |
| Padding | `0.35rem 0.75rem` |
| Border radius | `full` (999px) |
| Border | `1px solid transparent` |
| Text decoration | none |

### States

| State | Behavior |
|-------|----------|
| Default | Transparent background, transparent border |
| Hover | `border-color: rgba(148, 163, 184, 0.7)`, `background: rgba(15, 23, 42, 0.7)` |
| Active page | No special indicator (consider adding in future) |

## Tab Bar

Used for view switching (Designer tabs: Spatial, Electrical, Shared, All).

| Property | Value |
|----------|-------|
| Font size | `sm` (0.75rem) |
| Font weight | `medium` (500) when active |
| Padding | `0.5rem 0.75rem` |
| Border bottom | `2px solid transparent` (default), `2px solid #22c55e` (active) |
| Color | `text.muted` (default), `text.primary` (active) |
| Transition | `color 0.15s, border-color 0.15s` |

## Language Switcher

Small button group in the header, typically EN / DE / FR.

| Property | Value |
|----------|-------|
| Font size | `xs` (0.7rem) |
| Font weight | `semibold` (600) |
| Padding | `0.15rem 0.45rem` |
| Border radius | `full` (999px) |
| Background (default) | transparent |
| Background (active) | `rgba(34, 197, 94, 0.2)` |
| Border (active) | `1px solid rgba(34, 197, 94, 0.5)` |
| Color (active) | `#4ade80` |

## SmartHome Selector

Native `<select>` dropdown in the header for choosing the active SmartHome.

| Property | Value |
|----------|-------|
| Background | `#1e293b` |
| Border | `1px solid rgba(148, 163, 184, 0.35)` |
| Border radius | `full` (999px) |
| Font size | `sm` (0.75rem) |
| Padding | `0.3rem 0.5rem` |

Uses `<optgroup>` to separate "Demo Homes" from "Your Homes".

## Cross-App Navigation

Apps link to each other using environment-variable URLs:
- Portal → Designer: passes `?home={smartHomeId}` query parameter
- Designer → Portal: back-link in header nav
- Modeler → Portal: back-link in header nav

The active SmartHome ID persists in `localStorage` and is passed between apps via the `?home=` query param.

## Platform Notes

- **Mobile**: Replace horizontal header nav with bottom tab bar. Keep the same color tokens. SmartHome selector moves to a settings or drawer view.
- **Node-RED**: Use Node-RED's built-in navigation. Apply the dark glass-morphism header style to the dashboard header if customizable.
- **IoT**: Simplified navigation — direct links or physical button mapping.
