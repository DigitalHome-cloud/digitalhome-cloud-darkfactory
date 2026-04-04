# Mobile App Adaptation

Guidelines for applying the DHC design language to iOS and Android apps.

## Theme

- **Dark-only**: Force dark mode regardless of system preference
- iOS: Use `.dark` color assets exclusively
- Android: Set `forceDarkAllowed: false` and use dark colors directly

## Color Tokens

All color tokens from `tokens/colors.json` apply directly to mobile. Map them to platform resources:

| Token | iOS (Swift) | Android (Compose) |
|-------|-------------|-------------------|
| `surface.primary` | `Color(hex: 0x0f172a)` | `Color(0xFF0F172A)` |
| `surface.deep` | `Color(hex: 0x020617)` | `Color(0xFF020617)` |
| `surface.elevated` | `Color(hex: 0x1e293b)` | `Color(0xFF1E293B)` |
| `text.primary` | `Color(hex: 0xe5e7eb)` | `Color(0xFFE5E7EB)` |
| `action.primary` | `Color(hex: 0x22c55e)` | `Color(0xFF22C55E)` |

## Typography

- **iOS**: San Francisco (automatic via system font)
- **Android**: Roboto (automatic via system font)
- **React Native**: System default font

Maintain the same **size ratios** from `tokens/typography.json`, but adjust the base size for mobile readability:

| Web Token | Web Size | Mobile Size | Use |
|-----------|----------|-------------|-----|
| `sm` | 0.75rem (12px) | 13pt / 13sp | Small labels |
| `base` | 0.8rem (12.8px) | 15pt / 15sp | Body text |
| `md` | 0.85rem (13.6px) | 16pt / 16sp | Primary text |
| `2xl` | 1.1rem (17.6px) | 20pt / 20sp | Section headers |
| `4xl` | 1.8rem (28.8px) | 28pt / 28sp | Page titles |

Support Dynamic Type (iOS) and font scaling (Android) for accessibility.

## Navigation

| Web Pattern | Mobile Pattern |
|-------------|---------------|
| Sticky top header | Top navigation bar (platform native) |
| Horizontal nav links | Bottom tab bar |
| Language switcher | Settings screen |
| SmartHome selector | Drawer menu or settings |
| Sidebar | Slide-out drawer (left) |
| Inspector panel | Bottom sheet (pull-up) |

## Touch Targets

All interactive elements must meet minimum touch target sizes:
- **iOS**: 44pt x 44pt
- **Android**: 48dp x 48dp

Increase button padding compared to web:
- Web button: `0.3rem 0.75rem`
- Mobile button: `12pt 20pt` minimum

## Cards and Lists

- Cards go **full-width** on phones (no grid)
- Maintain gradient backgrounds and rounded corners
- **Remove hover effects** (no hover on touch) — use press/highlight state instead
- List items: Use platform-native list components with DHC color tokens

## Design View Colors

Same 8+1 view colors apply:
- Use as section header accents
- Use as chart/graph data series colors
- Use as filter chip colors (e.g., tab pills for Spatial, Electrical, etc.)

## Gestures

| Action | Gesture |
|--------|---------|
| Navigate back | Swipe from left edge (iOS) / system back (Android) |
| Open sidebar | Swipe from left edge or tap menu icon |
| Open inspector | Tap item to open bottom sheet |
| Dismiss overlay | Swipe down or tap outside |

## Platform-Specific Patterns

### iOS
- Use `UINavigationBar` with dark appearance
- `TabBarController` for bottom navigation
- `UISheetPresentationController` for inspector bottom sheets
- SF Symbols for icons (map from emoji/text-letter approach)

### Android
- Use Material 3 dark theme with DHC color overrides
- `BottomNavigationView` for bottom tabs
- `BottomSheetDialogFragment` for inspector
- Material Symbols for icons

### React Native
- Use `DarkTheme` from `@react-navigation/native` with DHC overrides
- `createBottomTabNavigator` for tabs
- `@gorhom/bottom-sheet` for inspector panels
