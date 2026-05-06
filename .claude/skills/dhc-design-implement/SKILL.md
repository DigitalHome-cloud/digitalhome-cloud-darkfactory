---
name: dhc-design-implement
description: Use when the user gives a Claude Design handoff URL (api.anthropic.com/v1/design/h/...) or pastes a design bundle and asks to implement it in one of the DHC apps (Portal, Designer, Modeler). The skill walks you through fetching the bundle, reading the chat transcripts, mapping the design to the right repo, and shipping it without re-introducing constraints the codebase has already settled.
---

# DHC Design handoff → implementation

A user mocks up new UI in Claude Design (claude.ai/design), then exports a handoff bundle. They paste the bundle URL and ask you to implement the design into the live codebase.

This skill is the playbook for that workflow.

## Step 1 — Fetch the bundle

The handoff URL looks like `https://api.anthropic.com/v1/design/h/<id>?open_file=<file>.html`.

```
WebFetch(url=<url>, prompt="...")
```

The fetch returns a **binary gzip blob**, not text. WebFetch will say something like *"binary content, saved to .../webfetch-XXXX.bin"*. **Don't treat that as failure.** Grab the `.bin` path and extract it:

```bash
mkdir -p /tmp/dhc-design-pkg && tar -xzf <bin-path> -C /tmp/dhc-design-pkg
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

## Step 2 — Read in the right order

1. **README.md** — confirms what the user wants (the file name from `?open_file=` is almost always the primary design).
2. **chats/*** — show *intent*. The final HTML is one frame; the chat is where the user explains constraints and rejects directions. Skim every transcript.
3. **The primary HTML in full.** Read it top to bottom. Note every CSS rule, every animation, every translation table, every `tweaks` block. The HTML is authoritative for visuals.
4. **Asset files** — note their dimensions/colors so you can cite them in the plan.

## Step 3 — Identify the target repo

Designs almost always target one of:

| Hint in design | Target |
|----------------|--------|
| "DHC Modeler", `Modeler`, `modeler.digitalhome.cloud` | `repos/modeler/` |
| "DHC Designer", `Designer`, Blockly, `designer.digitalhome.cloud` | `repos/designer/` |
| "DHC Portal", `Portal`, tile launchpad, `portal.digitalhome.cloud` | `repos/portal/` |
| Cross-app docs (ADRs, specs, release notes) | umbrella `docs/` |

If the design is generic and the chat doesn't pin a repo, **ask** before implementing. Don't guess.

Also read the target repo's `CLAUDE.md` (and the umbrella's `CLAUDE.md`) before planning. They list constraints that override the prototype — see the Constants list below.

## Step 4 — Hard constraints to enforce against the prototype

Claude Design doesn't know our backend. Strip or adapt these on every implementation, even when the prototype shows them:

- **Modeler is tenant-agnostic.** Don't render or wire up `SmartHome ID` selectors, `?home=` routing, or tenant-scoped data on Modeler pages. (Portal and Designer do use the SmartHome ID — keep it there.)
- **SSO/federation isn't configured.** Don't render "Continue with SSO" buttons or call `signInWithRedirect()`. If the prototype has it, hide it (don't wire to a 500-error path).
- **Amplify Authenticator stays the default for portal/designer.** If the design replaces it with a custom form, ask the user whether the scope is happy-path-only or full custom (MFA, forced-new-password, forgot-password, email verification). The state machine is large — get explicit scope before building.
- **No `tweaks` panel in production.** The design's `EDITMODE-BEGIN`/`EDITMODE-END` block + postMessage protocol are prototype-only. Drop them.
- **Static `assets/` paths → `static/<file>`.** Gatsby serves `static/*` from `/`, so `assets/dlab5-mark.svg` in the prototype becomes `/dlab5-mark.svg` in the app.
- **Inline UMD React + Babel scripts → real React components.** The prototype is a single self-contained HTML; the apps are Gatsby/React with proper imports. Recreate the visual output, not the prototype's structure.
- **CSS scoping.** Don't dump the prototype's body-level resets into `global.css`. Wrap them in a page-scoped class (e.g. `.dhc-signin-shell *`) so they don't leak.
- **i18n.** The prototype hardcodes EN/DE/FR strings inline. Move them into `repos/<app>/src/locales/{en,de,fr}/common.json` and use `useTranslation()`. The in-page lang switch (if any) wires to `useI18next().changeLanguage(lng)`.

## Step 5 — Reuse, don't reinvent

Before adding utilities, check whether they exist:

- `src/context/AuthContext.js` — `useAuth()` exposes `authState`, `isAuthenticated`, `user`, `groups`, `hasGroup()`, `signOut()`, `reloadSession()`. All three frontend apps have an equivalent file.
- `src/utils/getAppUrl.js` — environment-aware cross-app URLs (`getAppUrl("portal")` etc.). Duplicated in each app.
- `gatsby-plugin-react-i18next` — `useTranslation`, `useI18next`. Pages need a GraphQL `query SignInPageQuery($language: String!) { locales: allLocale(filter: { language: { eq: $language } }) { edges { node { ns data language } } } }` block (or equivalent) at the bottom — keep it on rewrites.
- Existing CSS class conventions: `dhc-*` prefix, plain CSS file under `src/styles/`. No CSS-in-JS framework.

## Step 6 — Plan, then implement

For non-trivial changes (anything more than a single component swap), use plan mode (`/plan`) and:

1. List every file touched (new + modified) with one sentence of purpose.
2. Call out any prototype features dropped because of Step 4 constraints — and why.
3. Ask the user up front (via AskUserQuestion) about: auth-flow scope, whether to keep dropped features as stubs, anything where the prototype contradicts `CLAUDE.md`.
4. Verification section: `yarn build` in the target repo at minimum; `yarn develop` smoke check if the user is at the machine.

Avoid implementing things outside the plan. If the prototype has a side feature you didn't list (e.g. an animation toggle), either include it in a follow-up plan or skip it.

## Step 7 — Verify before declaring done

- Run `yarn build` in the target repo. The page must SSR cleanly — Gatsby builds in Node, so anything that touches `window` outside `useEffect` will throw.
- Check the SSR HTML for the page (`public/<route>/index.html`) — confirm class names, asset paths, and translated strings appear.
- Honour `prefers-reduced-motion: reduce` for any continuous animation. The prototype won't have done this.
- For UI changes, **say explicitly that you didn't run the dev server / didn't click through the flows** if you didn't. Don't claim a UI is done off a passing build alone.

## Step 8 — Send improvements back to Claude Design (optional)

If you spot prototype patterns that consistently bite (e.g. it keeps adding SSO buttons we have to strip), ask the user whether they want to paste the prompt at `.claude/skills/dhc-design-implement/PROMPT-FOR-CLAUDE-DESIGN.md` into their next Claude Design conversation so the prototypes ship closer to reality.

## Reference: prior runs

- `2026-05-06` — DHC Modeler Login redesign. Bundle `PhYgkpL4VL77d-NpBAQVoQ`. Custom signin form replacing Amplify Authenticator, animated ontology graph background, new locale keys under `signin.*`. SmartHome ID + SSO stripped per the Modeler-is-tenant-agnostic and federation-not-configured rules. Plan: `/home/frankuwe/.claude/plans/quiet-scribbling-otter.md`.
