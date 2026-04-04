# Motion

> Token file: [`tokens/motion.json`](../tokens/motion.json)

## Principles

- **Subtle and fast** — motion supports the interaction, never decorates it
- **No keyframe animations** — all motion uses CSS transitions
- **Consistent timing** — only three durations across the entire platform
- **Purposeful** — every transition communicates a state change

## Duration Scale

| Token | Value | Use |
|-------|-------|-----|
| `fast` | 120ms | Card hover (lift + shadow), border color changes |
| `normal` | 150ms | Button hover, input focus, tab switches, chevron rotation |
| `slow` | 250ms | Reserved for overlay fade, panel expand (future) |

## Easing

| Token | Value | Use |
|-------|-------|-----|
| `default` | ease | General transitions |
| `out` | ease-out | Card lift transforms, element departure |

## Common Transitions

| Element | Properties | Timing |
|---------|-----------|--------|
| Buttons | `background`, `border-color` | 150ms ease |
| Cards/Tiles | `transform`, `box-shadow`, `border-color`, `background` | 120ms ease-out |
| Form inputs | `border-color` | 150ms ease |
| Tab indicators | `color`, `border-color` | 150ms ease |
| Sidebar chevrons | `transform` (rotate) | 150ms ease |

## Card Hover Effect

Cards lift slightly on hover:

- `transform: translateY(-2px)` — subtle upward shift
- `box-shadow: 0 18px 40px rgba(15, 23, 42, 0.7)` — deep shadow appears
- `border-color` shifts to accent (green for active tiles)

## Guidelines for New Surfaces

- **Node-RED**: Match fast/normal durations for widget state changes
- **Mobile**: Use platform-native animation curves (iOS: spring, Android: standard easing)
- **IoT displays**: Skip transitions entirely if the display refresh rate is below 30fps
