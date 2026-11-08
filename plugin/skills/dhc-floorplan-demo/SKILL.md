---
name: dhc-floorplan-demo
description: Run a narrated, recorded screencast that builds a French "T4" home from scratch in the unified Blockly + Floor-plan designer (repos/core/blockly/preview.html) — open the tool in Chrome, hit New, author the Spatial model one block at a time (DigitalHome → detached house → level → seven rooms → sensor points), then switch to the Floor plan tab and lay out walls (incl. thick stone walls), doors, windows and Arcada furniture, narrating each step and capturing a GIF. Trigger on "run the floor-plan demo", "build the T4 from scratch", "record the designer walkthrough", "demo the floor designer", "make the screencast of the Blockly + floor plan". Drives the browser via the mcp__claude-in-chrome tools and the generic window.DHC_DEMO seam in preview.html. Do NOT trigger for authoring the block JSON (use dhc-build-blockly-elements-for-spatial-modeling) or ontology work. Confined to repos/core/blockly/ (the tracked builder lives in blockly/floorplan/demo/; this SKILL.md is the local orchestration layer).
---

# DHC Floor-plan Demo — "build the T4 from scratch"

A **guided, narrated screencast**: open the unified designer, start blank, and
build a "dream **T4**" (a French 4-principal-room home) end to end — Spatial
Blockly model **and** the Floor-plan sketch — narrating every step and recording
a GIF. Voice-over is **phase 2** (see the end); the narration is already emitted
as `blockly/floorplan/demo/narration.srt` so a later TTS pass can dub the recording.

## What drives it

Two lanes, both reliable and repeatable:

- **Spatial (Blockly) lane** — driven through the generic **`window.DHC_DEMO`**
  seam in `preview.html` (`loadSpatial`, `seedSpatial`, `showView`). The demo
  pushes an ordered list of serializations so blocks appear **one narrated step
  at a time**. No fragile toolbox drag-drop.
- **Floor-plan lane** — geometry pushed via `DHC_DEMO.setFloorplan(fp)`
  (walls, doors/windows, furniture, anchor in one shot), with a few **real
  clicks/drags** for the headline "wow" beats (pick the Wall tool and click an
  edge; drag the amber anchor; drop a furniture glyph from the palette).

The **single source of truth** is `blockly/floorplan/demo/t4-spec.mjs`. `blockly/floorplan/demo/demo-driver.mjs`
turns it into the staged serializations + the floor-plan layer. Run it in node:

```bash
node blockly/floorplan/demo/demo-driver.mjs          # → JSON { stages, floorplan, meter }
node blockly/floorplan/demo/demo-driver.mjs --srt    # → narration.srt (phase-2 voice seam)
```

`repos/core/tests/blockly/floorplan-demo.test.js` guards the builder: every
floor-plan room key must bind to a room the Spatial parser produces, the reveal
must be additive, and openings/furniture must be well-formed. Run `npm test`
before relying on the demo after any block-schema change.

## Preconditions

- The harness needs the network (Blockly + React load from unpkg).
- Chrome reachable via `mcp__claude-in-chrome`; load the tools first (see below).

## Run procedure

### 0. Load browser tools + serve the harness

```
ToolSearch select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__gif_creator,mcp__claude-in-chrome__read_console_messages
```

Start a static server rooted at `repos/core` (any free port), e.g.
`python3 -m http.server 8821` (run it backgrounded; stop it in teardown).

### 1. Build the payloads

`node blockly/floorplan/demo/demo-driver.mjs > <scratchpad>/t4-build.json`. Read that file; it
has `stages[]` (each `{id,label,narration,spatial}`) and `floorplan`.

### 2. Open the tool + start recording

- `tabs_context_mcp{createIfEmpty:true}` → new tab; `navigate` to
  `http://localhost:8821/blockly/preview.html?ws=spatial`.
- Start `gif_creator` with a meaningful name (e.g. `t4-build-from-scratch.gif`).
  Capture a few extra frames before/after each action for smooth playback.
- Confirm the seam: `javascript_tool` → `!!window.DHC_DEMO` (spatial engine is
  ready immediately; the floor-plan React engine lazy-loads on first view switch).

### 3. Spatial reveal (narrate each stage)

Seed blank, then walk the stages in order. For each stage: **print the
narration line to the user**, then push it:

```js
window.DHC_DEMO.seedSpatial();                 // once, == New (spatial only)
// then per stage:
window.DHC_DEMO.loadSpatial(<stage.spatial>);  // blocks appear
```

Give each step a beat (~1–1.5 s) so the GIF reads. The stages are: blank home →
detached house → level → the 7 rooms one by one → sensor points room by room.
Screenshot occasionally; the workspace should end at 19 blocks, no console
errors (check `read_console_messages` with `onlyErrors:true`).

### 4. Floor plan (headline clicks + bulk inject)

- `window.DHC_DEMO.showView('floorplan')` — narrate: *"switching to the floor
  plan; the rooms auto-lay-out from the model."* Wait ~1.5 s for the React
  engine's first mount.
- **Headline live interactions** (screenshot each — these sell the tool):
  - Drag the amber **⌖ anchor** crosshair to a new spot (narrate it as the drop
    reference for new items).
  - Click the **Wall** tool, then click a room edge — a wall band appears.
  - Click the **Furniture** tool, type in the palette search (e.g. "sofa"),
    click a glyph — it drops at the anchor.
- **Bulk fast-forward** the full layout so it stays snappy and complete:
  `window.DHC_DEMO.setFloorplan(<floorplan>)` — narrate the **20 cm standard walls**
  (thickness is configurable **and uncapped** — mention you *could* type 90 cm for
  a real stone wall), the doors/windows, and the furnished rooms. Then
  `showView('floorplan')` again (re-mount) if you injected after the first mount.
- Screenshot the finished, furnished T4. (If `computer screenshot` times out on
  the heavy furniture render, wait 2 s and retry, or verify via the DOM:
  `document.querySelectorAll('#floorplan-root svg path,rect,text').length`.)

### 5. Prove persistence + finish

- Narrate + click **Save** (downloads the combined file) to show the T4 —
  spatial + floor-plan layer — is a real, reloadable artifact.
- Stop `gif_creator`; **report the saved GIF path to the user** (the recording is
  the deliverable — the user does not see the tool output otherwise).

### 6. Teardown

Stop the http server. Close the tab only if you created it this session.

## Narration

Keep it warm and explanatory — say *what* each block is and *why* it matters
(the SmartHome ID as the tenant key; a room's sensor points; that a wall's
thickness is configurable and uncapped, so a real French stone wall can be 90 cm).
The exact lines live in `blockly/floorplan/demo/narration.srt` (regenerate with
`--srt` if the spec changes) so the voice pass and the on-screen narration never
drift.

## Phase 2 — voice + recording (BUILT)

Two ways to get a narrated video; both offline, no cloud TTS.

### A. Deterministic render (recommended — no MCP browser)

One command produces a narrated MP4 without Claude-in-Chrome at all. It serves the
harness, uses **headless google-chrome + `?load=`** to screenshot the T4 at three
stages (blank model → full Spatial model → furnished floor plan), synthesises the
SRT with the offline **espeak-ng** engine, and muxes with **ffmpeg**:

```bash
blockly/floorplan/demo/voice/render-narrated-demo.sh  out.mp4
```

Reliable and repeatable — this is the "way to record this" the demo was asked for.
Deps (all on the workstation): `google-chrome`, `ffmpeg`/`ffprobe`, `python3`,
`node`, and `libespeak-ng` (used via `tts_espeakng.py`, no install/sudo).

### B. Live screencast + voice-over (the animated build)

For the full animated reveal (blocks appearing one by one, live wall/furniture
clicks), record the run with `gif_creator` (§2–§5 above), then dub it:

```bash
# 1) voice track from the narration (offline espeak-ng → timed WAV)
python3 blockly/floorplan/demo/voice/build-voiceover.py \
        blockly/floorplan/demo/narration.srt --out narration.wav
# 2) mux the voice over the recording (GIF or MP4) → narrated MP4
blockly/floorplan/demo/voice/build-narrated-video.sh recording.gif narration.wav out.mp4
```

**Report the output MP4 path to the user** — the video is the deliverable.

### Voice engine

`tts_espeakng.py` drives the installed `libespeak-ng.so.1` via ctypes (22050 Hz
mono, no binary/package install). `build-voiceover.py` lays each SRT cue at its
start time onto one track. Swap in a nicer TTS later by replacing `synth()` — the
SRT contract and the mux step are unchanged.

## Files

| Path | Role |
|---|---|
| `blockly/floorplan/demo/t4-spec.mjs` (tracked) | The "dream T4" as data — rooms, geometry, walls, openings, furniture, anchor. Edit here to change the demo. |
| `blockly/floorplan/demo/demo-driver.mjs` (tracked) | Pure builder: `spatialStages()`, `buildFloorplan()`, `buildAll()`, `--srt`. |
| `blockly/floorplan/demo/narration.srt` (tracked) | Timestamped narration (regenerate with `--srt`). |
| `blockly/floorplan/demo/voice/render-narrated-demo.sh` (tracked) | **Phase 2A** — one-command offline narrated MP4 (headless chrome + espeak-ng + ffmpeg). |
| `blockly/floorplan/demo/voice/tts_espeakng.py` (tracked) | Offline TTS → WAV via libespeak-ng ctypes. |
| `blockly/floorplan/demo/voice/build-voiceover.py` (tracked) | SRT → timed voice-over WAV. |
| `blockly/floorplan/demo/voice/build-narrated-video.sh` (tracked) | **Phase 2B** — mux a voice track onto a gif_creator recording. |
| `../../blockly/preview.html` | Hosts the generic `window.DHC_DEMO` seam the demo drives. |
| `../../tests/blockly/floorplan-demo.test.js` | Guards the builder (binding, additive reveal, shapes). |
