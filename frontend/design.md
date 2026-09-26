---
version: beta
name: Yojana Mitra Light
description: A light-first, calm, trustworthy citizen interface for daylight mobile use. Noto Sans + Inter, violet brand, semantic status colors.
colors:
  bg: "#FFFFFF"
  surface: "#F8F9FA"
  surface-elevated: "#FFFFFF"
  border: "#E5E7EB"
  text-primary: "#111827"
  text-secondary: "#4B5563"
  text-muted: "#6B7280"
  primary: "#613AF5"
  primary-hover: "#4F2ED4"
  primary-light: "#F3F0FF"
  success: "#16A34A"
  success-bg: "#F0FDF4"
  success-border: "#BBF7D0"
  warning: "#EA580C"
  warning-bg: "#FFF7ED"
  warning-border: "#FED7AA"
  error: "#DC2626"
  error-bg: "#FEF2F2"
  error-border: "#FECACA"
  disclaimer-bg: "#FFFBEB"
  disclaimer-border: "#FDE68A"
  disclaimer-text: "#92400E"
typography:
  fontFamily: "'Noto Sans', 'Inter', system-ui, sans-serif"
  note: "Noto Sans renders Devanagari matras correctly; Hindi/Marathi text runs 1.15x larger for visual balance."
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  2xl: 24px
spacing:
  touch-min: 48px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.lg}"
    minHeight: "48px"
  button-secondary:
    backgroundColor: "#FFFFFF"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    minHeight: "48px"
    border: "2px {colors.border}"
  button-danger:
    backgroundColor: "{colors.error}"
    textColor: "#FFFFFF"
    rounded: "{rounded.lg}"
    minHeight: "48px"
  card:
    backgroundColor: "{colors.surface-elevated}"
    rounded: "{rounded.xl}"
    padding: "20px"
  card-elevated:
    backgroundColor: "{colors.surface-elevated}"
    rounded: "{rounded.xl}"
    padding: "24px"
    shadow: "sm"
  camera-card:
    aspect: "4/3"
    rounded: "{rounded.2xl}"
    border: "2px dashed"
  verdict-danger:
    backgroundColor: "{colors.error-bg}"
    border: "{colors.error-border}"
  verdict-safe:
    backgroundColor: "{colors.success-bg}"
    border: "{colors.success-border}"
---

# Yojana Mitra Light

## Overview

Light-first, designed for daylight, mobile, non-technical citizens. The strongest signal is safety: the escalation verdict is the visual loudest thing on screen. Everything else stays calm — white surfaces, gray structure, one violet brand note.

## Colors

- **Background (#FFFFFF) / Surface (#F8F9FA):** paper-like canvas matching government portals citizens already know.
- **Text (#111827 / #4B5563 / #6B7280):** every pair hits 4.5:1 for body (GIGW 3.0).
- **Primary (#613AF5):** filled actions only. Hover deepens to `#4F2ED4`.
- **Semantic pairs:** each status color ships with its own background + border so banners read instantly (red danger, green safe, orange warning, amber disclaimer).

## Typography

Noto Sans first (Devanagari matras render correctly), Inter for Latin. Hindi/Marathi sizes run 1.15x for visual balance. Minimum 16px for Hindi body text.

## Layout

- Home: compact hero (`pt-8`), camera card as the hero action, voice card as the equal alternative, disclaimer always visible without scrolling.
- Result: strict hierarchy — 1) verdict banner, 2) explanation stepper, 3) key facts, 4) collapsed details, 5) voice, 6) disclaimer.
- Public nav is citizen-only (Explain). How it works / FAQ live in the footer; Review is a separate reviewer surface linked from the footer.

## Touch & Mobile

48px minimum touch targets everywhere (GIGW 3.0). No pill buttons (too playful for legal context) — 12px radius, filled primary, 2px-outline secondary, filled-red destructive.

## States

Every wait has progress (animated processing stages, never a bare spinner). Every error has a fix (retry + specific message). Empty review queue, offline banner, camera/mic denial, and skeleton loaders are all designed states, not afterthoughts.

## Do's and Don'ts

- Do keep safety loud and everything else calm.
- Do treat voice as equal to text, not a fallback.
- Do reveal long explanations one beat at a time with voice support.
- Don't use dark mode, gradients, or decorative interactivity.
- Don't ship a button that does nothing — every tap has a purpose.
- Don't hide the disclaimer behind a scroll.
