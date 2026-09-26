---
version: alpha
name: Linear Dark
description: A minimal, high-contrast dark product system with precise typography and restrained accent color.
colors:
  primary: "#7170FF"
  secondary: "#F7F8F8"
  tertiary: "#62666D"
  neutral: "#08090A"
  surface: "#0F1011"
  on-surface: "#F7F8F8"
  muted-surface: "#151617"
  border: "#FFFFFF14"
  accent: "#7170FF"
  text-muted: "#62666D"
  success: "#2FB344"
  warning: "#F5C400"
  error: "#E5484D"
typography:
  headline-display:
    fontFamily: "Inter Variable"
    fontSize: 72px
    fontWeight: 510
    lineHeight: 86px
    letterSpacing: -1.408px
  headline-lg:
    fontFamily: "Inter Variable"
    fontSize: 49px
    fontWeight: 510
    lineHeight: 72px
    letterSpacing: -1.584px
  headline-md:
    fontFamily: "Inter Variable"
    fontSize: 33px
    fontWeight: 510
    lineHeight: 40px
    letterSpacing: -0.24px
  headline-sm:
    fontFamily: "Inter Variable"
    fontSize: 22px
    fontWeight: 510
    lineHeight: 28px
    letterSpacing: 0px
  body-lg:
    fontFamily: "Inter Variable"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: -0.165px
  body-md:
    fontFamily: "Inter Variable"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 24px
    letterSpacing: -0.165px
  body-sm:
    fontFamily: "Inter Variable"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
    letterSpacing: -0.08px
  label-lg:
    fontFamily: "Inter Variable"
    fontSize: 16px
    fontWeight: 510
    lineHeight: 24px
    letterSpacing: -0.08px
  label-md:
    fontFamily: "Inter Variable"
    fontSize: 15px
    fontWeight: 510
    lineHeight: 20px
    letterSpacing: -0.08px
  label-sm:
    fontFamily: "Inter Variable"
    fontSize: 12px
    fontWeight: 510
    lineHeight: 16px
    letterSpacing: 0.04em
  caption:
    fontFamily: "Inter Variable"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 16px
    letterSpacing: -0.02em
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 9px
  xl: 12px
  full: 9999px
spacing:
  xs: 6px
  sm: 14px
  md: 24px
  lg: 32px
  xl: 112px
components:
  button-primary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.neutral}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.full}"
    padding: "14px 20px"
    height: "44px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.full}"
    padding: "14px 20px"
    height: "44px"
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.text-muted}"
    typography: "{typography.body-lg}"
    rounded: "{rounded.none}"
    padding: "0px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "12px 16px 16px"
  input:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "12px 14px"
  chip:
    backgroundColor: "{colors.muted-surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.full}"
    padding: "6px 10px"
  nav-link:
    backgroundColor: "transparent"
    textColor: "{colors.text-muted}"
    typography: "{typography.body-sm}"
    padding: "0px"
---

# Linear Dark

## Overview
Linear presents as disciplined, fast, and quietly premium. The experience is built for product teams and technical users who value clarity, density, and efficiency over decoration. The overall tone is dark and restrained, with a single electric accent that adds energy without breaking focus.

## Colors
- **Primary (#7170FF):** A vivid indigo-violet used sparingly for active states, product markers, and emphasis. It gives the interface a modern, AI-era edge without overwhelming the neutral base.
- **Secondary (#F7F8F8):** An off-white used for primary text and the strongest button surfaces. It keeps contrast high against the near-black background while feeling softer than pure white.
- **Tertiary (#62666D):** A muted graphite gray for secondary copy, navigation links, and supporting metadata. This is the main low-emphasis text color in the system.
- **Neutral (#08090A):** The near-black foundation of the UI, used for the page background and deepest surfaces. It creates the signature dark, immersive atmosphere.
- **Surface (#0F1011):** A slightly lifted panel color for cards and embedded content. It separates content blocks from the background while staying tonal.
- **On-surface (#F7F8F8):** The default text color for dark panels and interactive content placed on surfaces. It maintains strong readability with minimal glare.
- **Muted-surface (#151617):** A subtle elevated layer used for inputs, pills, and nested controls. It helps create hierarchy without visible color shifts.
- **Border (#FFFFFF14):** A very light translucent border used to define edges, containers, and controls. The system prefers thin outlines over heavy shadows.
- **Success (#2FB344):** Reserved for positive states and confirmations where needed.
- **Warning (#F5C400):** A warm alert tone for cautionary emphasis and status indicators.
- **Error (#E5484D):** A clear error red for destructive actions and validation states.

## Typography
The system is built on Inter Variable, with a compact, highly legible feel and subtle optical tightness. Headlines use a medium-heavy 510 weight with aggressive negative tracking, which gives the brand its sharp editorial voice. Body text stays lighter and more open, while labels bridge the gap with slightly stronger weight for UI clarity.

- **headline-display, headline-lg, headline-md, headline-sm:** Large product-forward headings with tight spacing and strong hierarchy. These are used for hero statements, page titles, and prominent section headers.
- **body-lg, body-md, body-sm:** Neutral informational text for paragraphs, descriptions, and supporting content. Body text is intentionally modest in size to preserve density.
- **label-lg, label-md:** Stronger UI labels for buttons, navigation, and short control text. They should feel crisp and compact rather than expressive.
- **label-sm:** Small utility text, typically for captions, metadata, and micro-labels. Uppercase or spaced-caps treatment can be used when a more procedural tone is needed.
- **caption:** Fine-print text for supplemental notes and secondary annotations.

## Layout
The layout follows a wide, centered hero composition with a strong sense of breathing room above the fold. Content blocks are arranged in a fluid grid that becomes more dense in the application screenshot, but keeps generous outer margins and clear internal gutters. The spacing rhythm is based on a small set of steps—6px, 14px, 24px, 32px, and 112px—so gaps feel intentional rather than arbitrary.

Use large section padding for landing pages, then tighten spacing inside product panels and app chrome. Cards and embeds should retain consistent inner padding, with 12px top padding and 16px side/bottom padding as the baseline. The system favors horizontal alignment and tidy content columns over ornamental asymmetry.

## Elevation & Depth
Depth is handled with contrast, borders, and tonal layering rather than dramatic shadows. Most surfaces are nearly flat, with a subtle 1px border and occasional inset treatment to imply containment. The result feels engineered and precise instead of glossy.

Primary hierarchy comes from background step-ups: background to surface to muted-surface. Shadows are minimal and only used lightly on prominent floating elements such as dialogs or elevated cards. Avoid soft, atmospheric shadows that would dilute the sharp, technical character.

## Shapes
The shape language is restrained and modern, with rounded corners used to soften an otherwise architectural system. Buttons are fully pill-shaped, while cards and panels use small radii around 9px to 12px. Inputs and chips should feel compact and controlled, not bubbly.

Rounded full pills signal primary actions and navigation emphasis. Smaller radii should be used for content containers and embedded app modules so the interface stays efficient and modular.

## Components
### Buttons
Primary buttons use a light surface with dark text, matching `button-primary`. They are pill-shaped, 44px tall, and padded at 14px 20px. Use these for the strongest call to action, and keep the visual treatment simple and high-contrast.

Secondary buttons use transparent or dark-on-dark treatment with a subtle outline feel, matching `button-secondary`. They should look polished but less assertive than primary actions. Reserve link-style buttons for tertiary navigation and inline actions, using `button-link` with no box treatment and muted text.

Hover and active states should stay subtle: slightly increase contrast, never add loud fills or heavy motion. Avoid square buttons entirely; the rounded full shape is part of the brand signature.

### Cards
Cards use the `card` token: surface-dark background, thin border, and 9px radius. Keep card content compact and modular, with visible grouping but minimal visual weight. Nested cards or overlays may reuse the same surface family with a slightly higher contrast edge.

### Inputs
Inputs should feel like embedded controls rather than standalone fields. Use muted-surface backgrounds, thin borders, and modest padding. Focus states should rely on border and text contrast, not glowing effects.

### Chips and Tags
Chips are small, pill-shaped status tokens with muted-surface backgrounds and full rounding. They are best for labels, categories, and small state indicators. Keep chip text short and use the primary accent only when a chip denotes active or selected state.

### Navigation
Top navigation links are small, quiet, and low-emphasis. They should use muted text with no heavy underline treatment except for deliberate link styling in isolated contexts. The active state can be signaled with brighter text or a nearby accent detail rather than a filled tab.

### Panels and Overlays
Floating panels, dialogs, and side drawers should remain dark, bordered, and highly structured. Use translucent separators and restrained padding. Overlays should feel like extensions of the system, not separate design themes.

## Do's and Don'ts
- Do keep the background nearly black and reserve bright color for a single accent.
- Do use Inter Variable with tight tracking for headlines and clear weights for UI labels.
- Do prefer thin borders and tonal surfaces over deep shadows.
- Do keep primary actions pill-shaped and 44px tall.
- Do use generous whitespace in marketing pages, but preserve compact density inside app panels.
- Don't introduce saturated gradient backgrounds or glassmorphism effects.
- Don't use large corner radii on cards, modals, or content panes.
- Don't make secondary text too bright; muted gray is part of the hierarchy.