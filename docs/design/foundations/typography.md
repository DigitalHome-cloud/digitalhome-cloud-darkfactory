# Typography

> Token file: [`tokens/typography.json`](../tokens/typography.json)

## Font Stacks

### Sans-serif (default)

```
system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

Uses the platform's native UI font: San Francisco on macOS/iOS, Segoe UI on Windows, Roboto on Android. No web fonts to load — instant rendering, native feel.

### Monospace

```
"SF Mono", "Fira Code", SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace
```

Used for URIs, ontology paths, code snippets, and technical values in inspectors.

## Type Scale

All sizes are `rem`-based (relative to 16px root). The scale is designed for information-dense UIs, not long-form reading.

| Token | Size | px | Typical use |
|-------|------|----|-------------|
| `2xs` | 0.65rem | 10.4 | Tiny badges, counts, icon labels |
| `xs` | 0.7rem | 11.2 | Sidebar labels, secondary captions |
| `sm` | 0.75rem | 12 | Form labels, table cells, nav pills, buttons (small) |
| `base` | 0.8rem | 12.8 | Input fields, panel titles, default UI text |
| `md` | 0.85rem | 13.6 | Navigation links, buttons, body text |
| `lg` | 0.9rem | 14.4 | Panel headers, section headings |
| `xl` | 1.0rem | 16 | Canvas controls, tile titles |
| `2xl` | 1.1rem | 17.6 | Section titles, form headings |
| `3xl` | 1.5rem | 24 | Page headings (h2) |
| `4xl` | 1.8rem | 28.8 | Page titles (h1) |
| `hero` | 2.25rem | 36 | Hero titles, landing pages |

## Weight Scale

| Token | Value | Use |
|-------|-------|-----|
| `normal` | 400 | Body text, descriptions |
| `medium` | 500 | Labels, form fields, active tabs |
| `semibold` | 600 | Section headers, nav links, buttons, tile titles |
| `bold` | 700 | Page titles, hero titles, logo text, badges |

## Line Height

| Token | Value | Use |
|-------|-------|-----|
| `dense` | 1.1 | Headings, single-line labels |
| `tight` | 1.4 | Comments, multi-line descriptions |
| `normal` | 1.5 | Body text default |
| `loose` | 1.75 | Long-form reading (articles, blog posts) |

## Letter Spacing

Uppercase labels use positive letter spacing for readability:

| Token | Value | Use |
|-------|-------|-----|
| `tight` | 0.03em | Version badges, compact labels |
| `normal` | 0.04em | Inspector labels, form labels |
| `wide` | 0.05em | Sidebar section headers |
| `wider` | 0.06em | Canvas labels, emphasis uppercase |

## Text Transform

- **Uppercase** (`text-transform: uppercase`): Sidebar section titles, form labels, table headers, canvas labels
- **Sentence case**: Everything else — body text, buttons, navigation links, descriptions

## Platform Adaptation

On mobile apps, replace the system font stack with the platform native:
- **iOS**: San Francisco (automatic via system-ui)
- **Android**: Roboto
- **Node-RED**: Inherits from the dashboard theme, typically system-ui

Keep the same size ratios and weight scale. Adjust absolute sizes if the base font size differs from 16px.
