---
version: 2.0
name: Yojana Mitra Light
status: supersedes frontend/design.md v1 (beta)
description: A crisis-support interface, not a productivity tool. Every decision below serves one job — tell a stressed citizen within 5 seconds whether they're in serious trouble, in 30 seconds what to do about it, and never let AI uncertainty put them at risk.
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
  # NEW — escalation gets its own visual identity, distinct from generic
  # warning/danger, so repeat users pattern-match "this is a different kind
  # of alert" rather than reading it as just a redder version of an error.
  escalate-bg: "#FEF2F2"
  escalate-border: "#DC2626"
  escalate-accent: "#7F1D1D"
typography:
  fontFamily: "'Noto Sans', 'Inter', system-ui, sans-serif"
  note: "Noto Sans renders Devanagari matras correctly; Hindi/Marathi text runs 1.15x larger. Devanagari also needs +0.1em extra line-height over the Latin default — matras need vertical room Latin text doesn't."
rounded:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  2xl: 24px
spacing:
  touch-min: 48px
iconography:
  policy: "One consistent icon set (Lucide, already available via lucide-react — see frontend/package.json). No emoji as icon. Emoji reads as playful/casual; a legal-notice product needs to read as competent and calm from the first frame."
  stroke-width: 1.75
  size-default: 20px
  exception: "Emoji is acceptable ONLY inside translated body text the user reads as prose (e.g. a suggested question chip), never as a standalone functional icon (button glyphs, status indicators, section headers)."
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
    backgroundColor: "{colors.escalate-bg}"
    border: "2px solid {colors.escalate-border}"
  verdict-safe:
    backgroundColor: "{colors.success-bg}"
    border: "1px solid {colors.success-border}"
    # NOTE: deliberately a thinner border + no accent bar than verdict-danger.
    # The safe state should read as quieter, not as a green mirror of danger.
---

# Yojana Mitra Light — v2

## What changed since v1, and why

v1 got the color system, touch targets, and "safety loud / everything calm"
principle right. What it didn't yet enforce: **ordering**. A calm color
palette on a page that still makes a stressed user scroll past five cards
to find out if they're in trouble isn't calm — it's just quiet-colored
anxiety. v2 is the same visual language with the information architecture
tightened around one thesis:

> Every other government-notice tool makes you read a form. Yojana Mitra
> makes you feel safe in five seconds, understood in thirty, and never
> lets an AI's uncertainty put you at risk.

If a change below doesn't serve "5 seconds to safety, 30 seconds to
understanding," it doesn't belong on the result screen.

---

## 1. Screen-order contract (result screen)

This is now a hard contract, not a suggestion — `App.tsx`'s terminal
result section must render in exactly this order:

1. **Verdict banner** — renders the instant `escalation.flagged` is known,
   before the rest of the explanation has necessarily streamed in. This is
   already correctly first in `App.tsx`; keep it first when adding
   anything new.
2. **AI-disclosure line** — NEW, one line, directly under the verdict,
   before the explanation: *"AI-generated explanation from your photo —
   reviewed by a human for serious cases."* (translate per language). This
   is the single highest-leverage trust addition in this doc. See §4.
3. **Progressive explanation** (the 3-beat stepper) — unchanged structure,
   visual polish in §3.
4. **Key facts** (amount / deadline / authority) — already locale-formatted
   correctly as of the current build (`lib/format.ts`); no data change
   needed, only see §5 for the confidence-disclosure fix.
5. **Follow-up Q&A**
6. **Voice playback**
7. Everything else (collapsed "details" section) stays collapsed by default.

Rationale for Q&A appearing *before* voice, not after: a user who wants to
ask "what happens if I ignore this" shouldn't have to scroll past an audio
player to find the question box.

---

## 2. Trust and disclaimer placement

**Problem:** the disclaimer is currently the last DOM element on the page,
reachable only after a full scroll — contradicts v1's own stated principle
("don't hide the disclaimer behind a scroll").

**Fix:** make `.disclaimer` a `position: sticky; bottom: 0` element with a
solid (non-transparent) background, always visible above the fold once any
result has rendered. It does not need to be sticky on the pre-upload hero
screen — only from the moment a job is submitted onward, so it doesn't
compete with the camera CTA on first load.

```css
.disclaimer-sticky {
  position: sticky;
  bottom: 0;
  z-index: 10;
  /* existing .disclaimer visual styles unchanged */
}
```

Apply `.disclaimer-sticky` in `App.tsx` only when `jobId` is set; keep the
plain `.disclaimer` (non-sticky) class on the hero screen.

---

## 3. Verdict banner — give escalation its own visual language

**Problem:** `verdict-danger` and `verdict-safe` in `VerdictBanner.tsx` are
currently the same layout with swapped colors. A repeat user's eye can't
tell "different kind of alert" from "same alert, different color" at a
glance — and the safe-state copy ("आपका ध्यान चाहिए" / "needs your
attention") still reads as a warning, undercutting the calm you're going for.

**Fixes:**
- Give `verdict-danger` a left accent bar (`border-left: 4px solid
  {colors.escalate-accent}`) and a slightly heavier icon treatment (already
  🚨 in emoji form — replace with a Lucide `AlertTriangle` at 28px, filled
  background circle). `verdict-safe` gets no accent bar, and a Lucide
  `CheckCircle2` outline-only, no filled circle — visually *quieter*, not
  just green.
- Reword the safe-state title. New copy direction: reassurance, not alert.
  - hi: `"यहाँ बताया गया है क्या करना है"` ("here's what to do") instead of
    `"आपका ध्यान चाहिए"`.
  - mr: `"हे बघा काय करायचं आहे"` (mirror the same reassurance framing).
  - Update `STRINGS.verdictSafe` in `i18n/strings.ts` accordingly; keep
    `verdictSafeSub` as-is ("समय पर कार्रवाई करें" is fine as a sub-line).
- The escalated state additionally gets a **distinct label above the
  title**, not just louder color: a small chip reading "वकील से सलाह लें"
  (see a lawyer) in `escalate-accent` text on white, so it's recognizable
  as a category, not just an intensity.

---

## 4. Name the AI, once, where it matters

**Problem:** nothing on the result screen currently tells the user an AI
wrote the explanation, versus e.g. a government official. For a legal
notice this is both a trust issue and an honesty-in-AI-disclosure issue.

**Fix:** add one line, directly under the verdict banner (see §1, step 2),
non-dismissible, low-visual-weight (text-secondary, no card/border):

- hi: `🤖 यह व्याख्या AI ने आपकी फोटो से बनाई है — गंभीर मामलों में इंसान द्वारा जांची जाती है।`
- mr: `🤖 हे स्पष्टीकरण AI ने तुमच्या फोटोवरून तयार केले आहे — गंभीर प्रकरणांत माणसाकडून तपासले जाते.`

This is one new string in `i18n/strings.ts` (`aiDisclosureLine`) and one
new paragraph in `App.tsx`, no component needed.

---

## 5. Confidence disclosure — show your work, don't hide it

**Problem:** `FieldRow.tsx` hides the confidence signal behind a tap, and
reveals a raw percentage ("confidence 87%") when expanded — meaningless to
a user unfamiliar with ML confidence scores, and it's hidden by default
right when it would build the most trust.

**Fix:**
- Keep the colored dot (🟢🟡🔴 → replace with a small filled circle using
  `{colors.success}` / `{colors.warning}` / `{colors.error}` so it's not
  another emoji), but make it **always visible**, not behind expand.
- Replace the expanded percentage with plain language, no numbers:
  - high → "AI इसे लेकर पूरी तरह आश्वस्त है" (AI is confident about this)
  - medium → "AI को इसमें थोड़ा संदेह है" (AI is somewhat unsure)
  - low → "कृपया मूल नोटिस में इसकी जांच करें" (please check the original notice) —
    and this state should link/scroll to a "view extracted text" affordance
    if one exists, otherwise just flag it as worth double-checking.
- Keep the tap-to-expand only for the *explanatory sentence*, not for the
  dot itself — the dot is the always-visible trust signal, the sentence is
  the optional detail.

---

## 6. Verdict-first also means voice-first parity

No change needed to `VoiceRecorder.tsx`'s current pointer-event
implementation (already correct) — but per the original design intent
("voice is equal to text, not a fallback"), the **hold-to-speak button
should visually match the primary camera CTA's prominence** on the home
screen, not sit below a divider labeled "or" as a secondary option. Treat
it as a true peer: same card size, same button weight, side-by-side or
stacked with equal visual mass, not camera-card-then-smaller-voice-card.

---

## 7. Reviewer dashboard — this is an internal tool, redesign it as one

**Problem:** `ReviewQueue.tsx` currently reads like a debug view: raw
`job_xxxxx` IDs, JSON-stringified audit blobs truncated at 200 chars, and
— critically — the "edit" decision has no textarea, so a reviewer cannot
actually edit text from the UI even though the backend
(`update_explanation_text`) supports it.

This screen has a completely different audience (a lawyer/ops reviewer,
not a citizen) and should look like an internal tool, not a citizen-facing
card. Reference: Linear's issue list, a moderation queue — information
density is good here, calm/whitespace is not the goal.

**Fixes:**
- Audit entries: render as a simple two-column key→value list per stage,
  not raw `JSON.stringify().slice(0,200)`. At minimum, format known keys
  (`confidence`, `documentType`, `escalate`, `rules`) as readable labels;
  fall back to raw JSON only for unrecognized stages.
  ```
  stage_name         escalation_pre
  escalate            true
  matched rules        R-001, R-004
  rules version         3
  ```
- Add a `<textarea>` bound to a new `finalText` state, shown only when the
  reviewer selects "edit" (not "approve"/"reject") — pre-filled with
  `result.explanation` so they're editing, not writing from scratch. Wire
  it to the existing `resolveReview(jobId, 'edit', finalText)` call in
  `lib/review.ts` (the parameter already exists, just isn't populated from
  the UI).
- Job IDs: keep monospace (correct for an internal tool) but add the
  `documentType` and `routedReason` as visible chips in the list row, not
  just on open — a reviewer triaging a queue should not have to open every
  item to see why it's there.
- Add keyboard shortcuts (`A` approve, `E` edit, `R` reject) once the above
  ships — genuinely useful for a reviewer processing volume, low priority
  versus the textarea fix above.

---

## 8. Small persistence/locale fixes (quick wins)

- **Language selector doesn't persist.** `useState<Lang>('hi')` in
  `App.tsx` resets on reload. Read/write `localStorage.getItem('ym_lang')`
  on mount/change; fall back to `navigator.language` starting with `'mr'`
  → default Marathi, else Hindi.
- **`<html lang="hi">` is hardcoded** in `index.html` and never updated.
  Set `document.documentElement.lang = lang` in a `useEffect` in `App.tsx`
  whenever `lang` changes — matters for screen readers and font-rendering
  hints, and costs three lines.
- **Q&A question limit isn't previewed.** `FollowUpQA.tsx` doesn't show the
  10-question cap until the 400 fires. Add a small counter under the input
  once ≥1 question has been asked this session: `"3/10 सवाल पूछे गए"`. Track
  count client-side (increment on successful `askQuestion` call); no new
  API needed.
- **Polling has no timeout.** `useJobPoll.ts` recurses forever if a job
  never reaches a terminal state. Add a max-attempts cap (e.g. 60 attempts
  ≈ 90s at 1.5s intervals) and a distinct "this is taking longer than
  usual" card state distinguishable from a hard error, with a retry button.

---

## 9. Layout (unchanged from v1, restated for clarity)

- Home: compact hero, camera CTA and voice CTA as equal-weight peers (§6),
  AI-disclosure line does not appear here (only appears once a result
  exists — see §4), non-sticky disclaimer visible without scrolling.
- Result: strict hierarchy per §1's screen-order contract.
- Public nav is citizen-only (Explain). How it works / FAQ live in the
  footer; Review is a separate reviewer surface linked from the footer,
  now visually distinct as an internal tool per §7.

## 10. Do's and don'ts (updated)

- Do keep the verdict the first thing rendered, full stop — not the
  fourth card in a scroll.
- Do disclose that an explanation is AI-generated, once, without burying it.
- Do show confidence as a visible, plain-language signal, not a hidden
  percentage.
- Do treat voice as an equal peer to the camera on the home screen.
- Do design the reviewer dashboard as an internal tool, not a citizen card.
- Don't use emoji as functional iconography — one consistent icon set only.
- Don't make the safe-state verdict a green mirror of the danger state —
  it should read as visibly quieter.
- Don't hide the disclaimer behind a scroll once a job exists (sticky it).
- Don't ship a decision button ("edit") that has no way to actually submit
  the thing it names.

---

## Implementation checklist (maps directly to files)

| # | Change | File(s) |
|---|---|---|
| 1 | Confirm/lock screen order | `frontend/src/App.tsx` |
| 2 | Sticky disclaimer post-submit | `App.tsx`, `index.css` |
| 3 | Verdict visual split + safe-state copy | `VerdictBanner.tsx`, `i18n/strings.ts` |
| 4 | AI-disclosure line | `App.tsx`, `i18n/strings.ts` |
| 5 | Confidence dot always-visible + plain language | `FieldRow.tsx`, `i18n/strings.ts` |
| 6 | Voice CTA visual parity with camera | `App.tsx`, `index.css` |
| 7 | Reviewer audit formatting + edit textarea | `ReviewQueue.tsx`, `lib/review.ts` |
| 8 | Lang persistence + `<html lang>` + Q&A counter + poll timeout | `App.tsx`, `FollowUpQA.tsx`, `hooks/useJobPoll.ts` |
| — | Swap emoji icons → Lucide across the above | all touched components |

Ship in this order — §1–4 are the ones that change how the product *feels*
on first use (the "5 seconds to safety" thesis); §5–8 are trust and
craft polish that compound on repeat use and for the reviewer role.