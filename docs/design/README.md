# DHC Design Guide

Platform-agnostic UX style and design guide for DigitalHome.Cloud.

This guide is the **single source of truth** for the DHC visual language. It applies to all surfaces: Gatsby web apps, Node-RED dashboards, mobile apps, and IoT displays.

## Design Tokens

Machine-readable JSON files defining all design values.

| File | Contents |
|------|----------|
| [tokens/colors.json](tokens/colors.json) | Surfaces, text, accents, design views, capabilities |
| [tokens/typography.json](tokens/typography.json) | Font stacks, sizes, weights, line heights |
| [tokens/spacing.json](tokens/spacing.json) | Spacing scale, containers, grid, breakpoints |
| [tokens/radii.json](tokens/radii.json) | Border radius values |
| [tokens/shadows.json](tokens/shadows.json) | Box shadows, glows, backdrop blur |
| [tokens/motion.json](tokens/motion.json) | Transition durations, easing functions |
| [tokens/borders.json](tokens/borders.json) | Border widths, styles, composite values |

## Foundations

Design principles and rationale behind the token choices.

| Document | Topic |
|----------|-------|
| [Color](foundations/color.md) | Color system, surface hierarchy, text contrast, design view colors |
| [Typography](foundations/typography.md) | Type scale, font stacks, weight and line-height usage |
| [Spacing & Layout](foundations/spacing-and-layout.md) | Spacing scale, page structure, grid systems, responsive behavior |
| [Motion](foundations/motion.md) | Animation principles, transition timing |
| [Iconography](foundations/iconography.md) | Icon strategy (text/emoji, no library) |

## Components

Specs for UI components — variants, states, sizing.

| Document | Topic |
|----------|-------|
| [Buttons](components/buttons.md) | Primary, secondary, ghost, danger variants |
| [Inputs & Forms](components/inputs-and-forms.md) | Text inputs, selects, checkboxes, form layout |
| [Cards & Panels](components/cards-and-panels.md) | Tile cards, workspace panels, auto-fit grids |
| [Navigation](components/navigation.md) | Header, nav links, tabs, language switcher, SmartHome selector |
| [Badges & Pills](components/badges-and-pills.md) | Status pills, capability badges, view dots |
| [Sidebar](components/sidebar.md) | Collapsible sidebar with sections and items |
| [Tables](components/tables.md) | Data tables with header, body, and action cells |
| [Feedback](components/feedback.md) | Validation items, alerts, error/success states |
| [Overlays](components/overlays.md) | Form overlays, fullscreen mode, modal pattern |

## Patterns

Cross-cutting design patterns.

| Document | Topic |
|----------|-------|
| [Layout Principles](patterns/layout-principles.md) | Page types, flexbox/grid usage, responsive strategy, z-index |
| [Accessibility](patterns/accessibility.md) | Contrast ratios, focus indicators, touch targets, color independence |
| [Semantic Views](patterns/semantic-views.md) | Ontology design view color mapping (8+1 views) |
| [Dark Theme](patterns/dark-theme.md) | Dark-only rationale, surface hierarchy, border strategy |

## Platform Adaptation

How to apply this guide on specific platforms.

| Document | Platform |
|----------|----------|
| [Web (Gatsby)](adaptation/web-gatsby.md) | Existing Gatsby apps — implementation status, inconsistencies, shared tokens |
| [Node-RED](adaptation/node-red.md) | Dashboard theming principles |
| [Mobile](adaptation/mobile.md) | iOS, Android, React Native — colors, typography, navigation, touch |
| [IoT Displays](adaptation/iot-displays.md) | Touch panels, LED indicators, e-ink, constrained displays |

## Quick Reference

**Theme**: Dark-only (permanent)
**Primary background**: `#0f172a`
**Primary text**: `#e5e7eb`
**Action color**: `#22c55e` (green)
**Link color**: `#38bdf8` (cyan)
**Font**: System UI (platform native)
**Container**: 1280px max-width
**Breakpoint**: 1024px (single)
**Button shape**: Pill (999px radius)
**Transitions**: 120ms (fast) / 150ms (normal)
