# Living Jarvis Animations — Design Spec

_Date: 2026-06-06 · Status: Design (approved) · Owner: Matteo_

Builds on the Phase 3 Jarvis layer ([2026-06-05-jarvis-voice-layer-design.md](2026-06-05-jarvis-voice-layer-design.md)).

## Goal

Make the Jarvis tab feel alive: a real-time **brain constellation** that visualizes the
agent reading the brain / thinking / drafting, with a central **CORE** that doubles as
the voice visualizer — rippling to the user's mic while they dictate and to Jarvis's TTS
while it speaks.

## Concept

A hero element above the existing transcript: one node per brain unit
(`founder · brand · voice · audience · strategy · content · social · viral-format · apps`
plus `analytics` and `draft`) orbiting a central CORE (Jarvis). State, driven entirely by
the SSE events the backend already streams (plus one small enrichment):

| Phase | Trigger | Visual |
|---|---|---|
| idle | no turn, no mic, not speaking | CORE slow blue breathing; nodes dim |
| listening | mic amplitude above threshold | CORE ripples to live mic level |
| reading | `tool` event for Read/Grep/Glob | matching node flares red; tracer line node→CORE |
| thinking | assistant text streaming, no active tool | CORE gold pulse, particles orbit |
| drafting | `tool` event for save_reel_draft | `draft` node bursts; CORE flash |
| speaking | TTS utterance active | CORE ripples to a per-word envelope |

## Components

**Backend (one small change):** the `tool` SSE event currently carries only the tool
*name*. Enrich it with a `target` (the file path for Read/Grep/Glob, the tool name for
the MCP draft tool) so the right node can flare. Touches `JarvisEvent` (`sse.ts`) and the
tool-block mapping in `agent.ts`. Existing unit tests stay green (new field is optional).

**Frontend (all in `dashboard/src`):**
- `lib/brainNodes.ts` — the fixed node list + `targetToNode(path)` pure mapping
  (e.g. `context/social.md → "social"`, `analytics/... → "analytics"`,
  `save_reel_draft → "draft"`). Plain, obvious, covered by typecheck + manual smoke.
- `lib/useJarvisState.ts` — reduces the chat events + mic level + speaking flag into a
  single `{ phase, activeNode, level }`.
- `lib/useMicLevel.ts` — Web Audio `AnalyserNode` hook; requests mic once, exposes a
  0–1 amplitude; on denial returns 0 (degrades to the calm "listening glow", no error).
- `components/BrainConstellation.tsx` — the visual. SVG/CSS for nodes + tracer lines;
  a Canvas 2D CORE for the ripple/particles. Dark fight-poster palette (red/black/gold),
  consistent with the existing dashboard.
- Speaking envelope: extend the existing TTS path so `speechSynthesis` `start`/`boundary`/
  `end` events drive a transient amplitude (see constraint below) and the speaking flag.
- Wire the constellation as a hero above the transcript in the Jarvis view.

## Data flow

SSE event → `useChat` (already streams text + tool + done) → `useJarvisState` derives
`{phase, activeNode, level}` ← also fed by `useMicLevel` (mic) and the TTS envelope →
`BrainConstellation` renders. ~60fps via `requestAnimationFrame`; React state holds only
phase/activeNode, while per-frame amplitude is read from a ref to avoid re-render churn.

## Honest constraint

The browser `speechSynthesis` API does not expose an audio stream, so the *speaking*
ripple is driven by word-boundary events (a synthetic envelope), not literal TTS
waveform data. The *mic* ripple (user voice) is real amplitude. Documented so the
half-synthetic half is not a surprise.

## Out of scope

- A `rendering` phase for the Remotion engine (next cycle) — but the state machine is
  written open so adding it later is a one-line enum addition.
- Premium/3D visuals (no three.js); Canvas 2D + SVG + CSS only.

## Done when

- Asking Jarvis a question lights the brain: nodes flare as it reads, CORE pulses gold
  while thinking, `draft` bursts when it saves a reel.
- Dictating ripples the CORE to your voice; the speak-replies toggle ripples it to Jarvis.
- Dashboard typechecks, builds clean, and the whole thing comes up via `start-jarvis.cmd`.
