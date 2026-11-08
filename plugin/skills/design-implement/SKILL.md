---
name: design-implement
description: Use when the user gives a Claude Design handoff URL (api.anthropic.com/v1/design/h/...), a Claude Design project URL (claude.ai/design/p/...), or pastes a design bundle and asks to implement it in a real codebase. Walks through fetching the design and its design system, reading the chat transcripts for intent, mapping it to the right repo, enforcing the constraints a prototype cannot know about (SSR safety, real routes, no CDN assets), and verifying the built site rather than trusting a green build. Covers the DHC apps (Portal, Designer, Modeler) as the worked example but applies to any repo.
---

# Design handoff → implementation

A user mocks up UI in Claude Design (claude.ai/design), then hands it over — as an exported bundle or as a live design project. They ask you to implement it in the live codebase.

This skill is the playbook for that workflow. **The prototype is authoritative for visuals and nothing else.** It does not know your backend, your routing, your rendering model, or your deployment constraints; Step 4 is where you reconcile that.

## Step 1 — Get the design

There are two handoff shapes. Identify which you have.

### 1a. Handoff bundle (a URL like `api.anthropic.com/v1/design/h/<id>?open_file=<file>.html`)

```
WebFetch(url=<url>, prompt="...")
```

The fetch returns a **binary gzip blob**, not text. WebFetch will say something like *"binary content, saved to .../webfetch-XXXX.bin"*. **Don't treat that as failure.** Grab the `.bin` path and extract it:

```bash
mkdir -p /tmp/design-pkg && tar -xzf <bin-path> -C /tmp/design-pkg
```

Bundle layout:

```
<project-name>/
  README.md                     ← short instructions for coding agents
  chats/chat1.md, chat2.md, ... ← full transcript(s) — read these
  project/<file>.html           ← the design(s)
  project/assets/*.svg|png      ← assets to bundle
  project/uploads/*             ← user-uploaded reference images (don't ship)
```

### 1b. Live design project (a URL like `claude.ai/design/p/<uuid>?file=<name>.dc.html`)

Use the **DesignSync** tool (authenticate via `/design-login` if needed). `list_files` on the project id from the URL, then `get_file` for each path you need. Read the main `.dc.html`, the `_ds/<design-system>/` bundle and its `tokens/*.css`.

Two traps here:

- **`get_file` caps responses at 256 KiB.** Binary assets over ~192 KB come back **truncated**, with `"truncated": true` in the JSON. A truncated JPEG usually loses only its last few bytes, so it still decodes — check every image before shipping it (`PIL` with `LOAD_TRUNCATED_IMAGES` will open it; re-save to produce a valid file) and tell the user the assets are re-encoded, not originals.
- **Large responses are persisted to disk** rather than returned inline. Decode binaries straight from the persisted JSON with a script — never read a base64 asset into your context.

## Step 2 — Read in the right order

1. **README.md** (bundles) — confirms what the user wants; the file from `?open_file=` / `?file=` is almost always the primary design.
2. **chats/*** (bundles) — show *intent*. The final HTML is one frame; the chat is where the user explains constraints and rejects directions. Skim every transcript.
3. **The primary HTML in full.** Top to bottom. Note every CSS rule, animation, translation table, and `tweaks` block.
4. **The design system** — tokens, then components. Tokens (colours, type scale, spacing, motion) should be copied *verbatim* so a later palette change is a file swap. Components get ported, not copied — see Step 4.
5. **Assets** — note dimensions and colours so you can cite them in the plan.

## Step 3 — Identify the target repo

Read the design for product names, URLs, and vocabulary, then match against the repos on the machine. Read the target repo's `CLAUDE.md` (and any umbrella `CLAUDE.md`) before planning — they list constraints that override the prototype.

If the design is generic and the chat doesn't pin a repo, **ask**. Don't guess.

Worked example — the DHC platform:

| Hint in design | Target |
|----------------|--------|
| "DHC Modeler", `Modeler`, `modeler.digitalhome.cloud` | `repos/modeler/` |
| "DHC Designer", `Designer`, Blockly, `designer.digitalhome.cloud` | `repos/designer/` |
| "DHC Portal", `Portal`, tile launchpad, `portal.digitalhome.cloud` | `repos/portal/` |
| Cross-app docs (ADRs, specs, release notes) | umbrella `docs/` |

## Step 4 — Hard constraints to enforce against the prototype

### 4a. Universal — apply on every implementation, in any repo

- **Prototype page-state becomes real routes.** Design canvases model a multi-page site as one component switching on a `page` variable (`pHome`, `pAbout`, …). In a static-site or SSR framework that must become one route per page. Left as-is, nothing is crawlable, linkable, or individually cacheable — which is usually the whole reason for the rebuild.
- **Responsive logic must be CSS, not measured width.** Prototypes branch on `window.innerWidth` and a resize listener. That cannot run during SSR and causes hydration mismatches. Translate to media queries at the same breakpoints, and render both variants with CSS deciding which is visible.
- **No CDN-fetched assets.** Design systems commonly mask or `<script>`-load icons and fonts from `unpkg`/`jsdelivr` at runtime, putting a third-party request on every page view and breaking offline builds. Inline the handful actually used.
- **No `tweaks` panel in production.** The `EDITMODE-BEGIN`/`EDITMODE-END` block and postMessage protocol are prototype-only. Drop them.
- **Inline UMD React + Babel → real components.** The prototype is one self-contained HTML file. Recreate its visual output, not its structure.
- **Hover/press state in CSS, not React state.** Ported design-system components often track hover with `useState`. As plain CSS they render identically without JavaScript and never re-render on pointer movement.
- **Interactive elements must be real controls.** A clickable `<div>` in the prototype becomes a `<button>` or a framework `<Link>`, or it is unreachable by keyboard.
- **One `<h1>` per page.** Prototypes reuse a generic section heading everywhere; a page that renders only `<h2>`s is an accessibility and SEO defect. Decouple heading level from visual size with a modifier class where the design needs a small `<h1>`.
- **CSS scoping.** Don't dump the prototype's body-level resets into a global stylesheet. Scope them to a page or component class so they don't leak.
- **Static asset paths.** Map the prototype's `assets/<file>` to the framework's convention (Gatsby serves `static/*` from `/`, so `assets/mark.svg` → `/mark.svg`).
- **i18n.** Prototypes hardcode strings inline. Move them to the project's locale files and translation hook.

### 4b. DHC platform only

- **Modeler is tenant-agnostic.** Don't render or wire `SmartHome ID` selectors, `?home=` routing, or tenant-scoped data on Modeler pages. Portal and Designer do use the SmartHome ID — keep it there.
- **SSO/federation isn't configured.** Don't render "Continue with SSO" buttons or call `signInWithRedirect()`. Hide it rather than wiring it to a 500.
- **Amplify Authenticator stays the default for portal/designer.** If the design replaces it with a custom form, ask whether the scope is happy-path-only or full custom (MFA, forced-new-password, forgot-password, email verification). The state machine is large — get explicit scope first.
- i18n lives in `repos/<app>/src/locales/{en,de,fr}/common.json` via `useTranslation()`; the in-page lang switch wires to `useI18next().changeLanguage(lng)`.

## Step 5 — Reuse, don't reinvent

Before adding utilities, check whether they exist. Also check the **scaffold you were given** — a placeholder repo often carries dependency versions that were never installed. On the Ātman Yoga run, the scaffold pinned `gatsby-plugin-robots-txt@^4.0.0`, a version that does not exist (max is 1.8.0), so `npm ci` failed outright; a second plugin was pinned to the previous major; and a component imported a package absent from `package.json`. **Verify every pinned version against the registry before trusting a scaffold.**

DHC specifics:

- `src/context/AuthContext.js` — `useAuth()` exposes `authState`, `isAuthenticated`, `user`, `groups`, `hasGroup()`, `signOut()`, `reloadSession()`. Present in all three frontend apps.
- `src/utils/getAppUrl.js` — environment-aware cross-app URLs (`getAppUrl("portal")`). Duplicated per app.
- `gatsby-plugin-react-i18next` — pages need the `allLocale` GraphQL block at the bottom; keep it on rewrites.
- CSS conventions: `dhc-*` prefix, plain CSS under `src/styles/`. No CSS-in-JS.

## Step 6 — Plan, then implement

For anything beyond a single component swap, use plan mode (`/plan`) and:

1. List every file touched (new + modified) with one sentence of purpose.
2. Call out every prototype feature dropped under Step 4 — and why.
3. Ask up front (AskUserQuestion) about auth-flow scope, whether dropped features stay as stubs, and anything where the prototype contradicts `CLAUDE.md`.
4. Write a verification section — see Step 7.

Avoid implementing things outside the plan. A side feature you didn't list goes in a follow-up plan or is skipped.

## Step 7 — Verify before declaring done

A green build is necessary and **not sufficient**. Both defects found on the Ātman Yoga run — a hero image that didn't fill its container, and a page with no `<h1>` — passed the build.

1. Build the target. It must render server-side cleanly; anything touching `window` outside `useEffect` throws in Node.
2. **Drive the built site with headless Chrome.** Screenshot at desktop and mobile widths, and script the interactive paths:
   ```bash
   google-chrome-stable --headless --disable-gpu --no-sandbox --hide-scrollbars \
     --virtual-time-budget=8000 --window-size=1400,1000 \
     --screenshot=/tmp/shot.png "http://localhost:<port>/<route>"
   ```
   For interaction and console capture, `puppeteer-core` against the installed Chrome is more reliable than a browser extension. Assert: every route returns 200, every page has exactly one `<h1>`, and the console is free of errors and failed requests.
3. Check the SSR HTML (`public/<route>/index.html`) for class names, asset paths, and translated strings.
4. Honour `prefers-reduced-motion: reduce` for continuous animation. The prototype won't have.
5. **Say explicitly what you did not check.** If you never clicked through a flow, say so. Don't claim a UI is done off a passing build alone.

## Step 8 — Send improvements back to Claude Design (optional)

If prototype patterns consistently bite (it keeps adding SSO buttons you strip, or CDN icon loaders), ask whether the user wants to paste `PROMPT-FOR-CLAUDE-DESIGN.md` into their next Claude Design conversation so prototypes ship closer to reality.

## Reference: prior runs

- `2026-05-06` — DHC Modeler login redesign. Bundle `PhYgkpL4VL77d-NpBAQVoQ`. Custom signin form replacing Amplify Authenticator, animated ontology graph background, new locale keys under `signin.*`. SmartHome ID + SSO stripped per the Modeler-is-tenant-agnostic and federation-not-configured rules. Plan: `~/.claude/plans/quiet-scribbling-otter.md`.
- `2026-08-10` — Ātman Yoga (`~/DLAB5/atmanyoga-fullstack`), a Wix → Gatsby 5 + Amplify migration. Live design project via DesignSync, not a bundle. Nine routes generated from a single page-state prototype; `window.innerWidth` branching converted to media queries; Lucide icons de-CDN'd; four broken dependency pins in the scaffold. Verified with puppeteer-core over the built site. Plan: `~/.claude/plans/please-create-a-skill-snappy-sedgewick.md`.

## Related

- `git-commit` — commits the result in house style and opens the PR against the right base
- `dhc-amplify-gen2` — when the design implies backend work on the DHC platform
- `dhc-security-audit` — run after any auth-touching UI change
