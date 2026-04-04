# Web (Gatsby) Adaptation

This document describes how the existing Gatsby apps implement the DHC design guide and recommends alignment improvements.

## Current Implementation

All three apps use plain CSS with a single `global.css` file per app:

| App | CSS File | Lines | CSS Variables |
|-----|----------|-------|---------------|
| Portal | `src/styles/global.css` + `src/styles/layout.css` | ~824 | Partial (layout.css) |
| Designer | `src/styles/global.css` | ~1274 | None |
| Modeler | `src/styles/global.css` | ~919 | None |

CSS is imported globally via `gatsby-browser.js`. No CSS frameworks, no CSS-in-JS.

## Class Naming Convention

All apps use the `.dhc-` prefix. The canonical pattern is:

```
.dhc-{component}-{variant}--{modifier}
```

Examples:
- `.dhc-button-primary` — primary button
- `.dhc-sidebar-item--selected` — selected sidebar item
- `.dhc-nav-pill--ok` — authenticated status pill
- `.dhc-tile--disabled` — disabled tile

## Known Inconsistencies to Resolve

### 1. Container Max-Width

- **Current**: Portal uses `max-width: 1120px`, Designer/Modeler use `1280px`
- **Target**: `1280px` everywhere
- **Action**: Update Portal's `.dhc-main` to `max-width: 1280px`

### 2. Button Class Naming

- **Current**: Portal has `.dhc-btn` and `.dhc-btn-primary`; Designer/Modeler have `.dhc-button-primary`
- **Target**: `.dhc-button-{variant}` everywhere
- **Action**: Rename Portal classes to match Designer/Modeler convention

### 3. CSS Custom Properties

- **Current**: Portal defines some in `layout.css`; Designer/Modeler hardcode all values
- **Target**: All apps import a shared set of CSS custom properties from the design tokens
- **Action**: Create a `dhc-tokens.css` that all three apps import (see below)

### 4. Hero Title Size

- **Current**: Portal 2.2rem, Designer 2.1rem
- **Target**: 2.25rem
- **Action**: Update both

## Recommended: Shared Token CSS

Generate a `dhc-tokens.css` file from the JSON token files and import it in each app's `gatsby-browser.js`:

```css
/* dhc-tokens.css — generated from docs/design/tokens/ */
:root {
  /* Surfaces */
  --dhc-surface-primary: #0f172a;
  --dhc-surface-deep: #020617;
  --dhc-surface-elevated: #1e293b;
  --dhc-surface-glass: rgba(15, 23, 42, 0.9);

  /* Text */
  --dhc-text-primary: #e5e7eb;
  --dhc-text-secondary: #9ca3af;
  --dhc-text-muted: #64748b;

  /* Accents */
  --dhc-accent-cyan: #0ea5e9;
  --dhc-action-primary: #22c55e;
  --dhc-danger: #ef4444;
  --dhc-warning: #f59e0b;

  /* Spacing */
  --dhc-container-max: 1280px;
  --dhc-space-4: 0.5rem;
  --dhc-space-5: 0.75rem;
  /* ... etc */
}
```

This can be a file in the umbrella repo that each sub-repo copies or symlinks, or a future `@dhc/design-tokens` npm package.

## CSS Modules

CSS Modules are acceptable for page-specific styles that don't need to be shared. The Portal uses this for `index.module.css`. Global styles for shared components should stay in `global.css` using `.dhc-` prefixed classes.

## Amplify Authenticator Theming

The sign-in page uses AWS Amplify's `<Authenticator>` with a custom theme. The theme overrides should reference the same token values:

```javascript
const dhcTheme = {
  name: "dhc-theme",
  overrides: [{
    colorMode: "light", // Amplify UI internal mode
    tokens: {
      colors: {
        brand: {
          primary: {
            10: "#0f172a",   // surface.primary
            80: "#1d4ed8",   // action blue
            90: "#1e40af",   // action blue darker
          }
        }
      },
      radii: {
        small: "0.5rem",    // radii.base
        medium: "1rem",     // radii.xl
      }
    }
  }]
};
```

## Blockly Theming (Designer)

The Designer overrides Blockly's internal styles with `!important` rules in `global.css`. These must use the design token values:

- Main background: `surface.deep` (#020617)
- Text: `text.primary` (#e5e7eb)
- Scrollbar handle: `action.primary` (#22c55e)
- Context menu: `surface.deep` background with standard border
