# Prompt for Claude Design — DHC platform context

Paste the block below at the **start of a new Claude Design conversation** (or pin it as project context) when iterating on DigitalHome.Cloud designs. It tells Claude Design what's already shipped, what the codebase can actually support, and which prototype habits to drop so the next handoff lines up with reality.

You can edit the "Latest shipped designs" section before pasting if you want to bias toward a specific app or flow.

---

## Begin context block — paste from here

You are designing for **DigitalHome.Cloud (DHC)**, a real production platform. The handoff bundles you produce are implemented as-is by a coding agent against the live codebase. Match these constraints; don't fight them.

### Apps in the platform

| App | URL | Role |
|-----|-----|------|
| **Portal** | portal.digitalhome.cloud | Tile launchpad. The frontend that owns the shared Amplify backend. SmartHome ID is the top-level tenant key. |
| **Designer** | designer.digitalhome.cloud | Blockly-based SmartHome design app. NF C 15-100 validation, 3D A-Box viewer. SmartHome-scoped. |
| **Modeler** | modeler.digitalhome.cloud | Ontology editor and component library. **Tenant-agnostic** — no SmartHome ID. |

When you create a design, state at the top which app it targets. If the design is generic, say so.

### Visual language

- **Dark mode only.** Slate/blue base palette. Background `#020617` or `#0f172a`. Text `#e5e7eb`.
- **Accent green `#22c55e`** for primary actions and the `dhc:` namespace.
- **Ontology palette** (use these *exact* hex values when surfacing namespaces):
  - `brick:` `#f59e0b` (amber)
  - `rec:` `#3b82f6` (blue)
  - `s223:` `#a855f7` (purple)
  - `dhc:` `#22c55e` (green)
- **Fonts**: system UI for body content; `'SF Mono','Fira Code',Menlo,Consolas,monospace` for the terminal/IDE aesthetic that's been adopted on auth and other ontology-adjacent surfaces.
- **CSS class prefix**: `dhc-*`. Plain CSS, no Tailwind, no CSS-in-JS framework. Sharp corners (`border-radius: 0`) are an acceptable terminal-aesthetic choice; rounded corners (`border-radius: 0.5–999px`) are the default elsewhere.
- **Brand mark**: `assets/dlab5-mark.svg` is the canonical hexagonal D-LAB-5 mark used across all apps.

### Backend / auth — what actually exists

- **Single Amazon Cognito User Pool** shared across all three apps. Sign-in on one app carries to the others (SSO across DHC apps).
- **Cognito groups** drive feature gating: `dhc-users`, `dhc-operators`, `dhc-admins`.
- **Federation / external SSO is NOT configured.** Don't add "Continue with Google/Microsoft/SAML" buttons unless the user explicitly asks for them. They will be stripped on implementation.
- **MFA, password reset, forced-new-password, email confirmation** all run through Amplify v6 (`signIn`, `confirmSignIn`, `resetPassword`, `confirmResetPassword`, `confirmSignUp`). When you replace the default `<Authenticator>` with a custom form, design every state — the implementer will have to wire all of them.
- **Amplify backend is Gen1**, frontend imports are Gen2-style. This affects nothing visually; mention it only if relevant.

### Codebase shape — what implementations look like

- **Gatsby 5 + React 18 static sites.** Hydration matters; anything time- or window-dependent has to defer to `useEffect`.
- **i18n via `gatsby-plugin-react-i18next`.** Three languages: EN (all apps), DE + FR (Portal, Modeler). When you put a translation table in a prototype, write keys flat (`signin.execute`, `signin.identifier`, ...) so they map cleanly to JSON locale files.
- **Routing via `gatsby` `navigate()`.** Cross-app links go through a `getAppUrl(appName)` helper that picks dev/stage/prod hosts based on the current hostname. In the prototype, hardcode the prod URL; the helper substitutes at runtime.
- **`AuthContext`** exposes `{ authState, isAuthenticated, user, groups, hasGroup(name), signOut(), reloadSession() }`. After custom-form sign-in succeeds, the implementation calls `reloadSession()` and `navigate("/")`.

### Things the implementer will strip from prototypes (so don't put them in)

- **`tweaks` panels** — the postMessage edit-mode panel (`__activate_edit_mode`, `EDITMODE-BEGIN/END`) is your tooling, not part of the production surface. Keep it for your own iteration; the implementer drops it.
- **SSO buttons** — see above.
- **SmartHome ID dropdowns on the Modeler.** On Portal and Designer they're load-bearing; on the Modeler they're misleading. If a flow logically belongs on the Modeler, omit the home selector.
- **Inline `<script>` tags importing UMD React + Babel** — those are prototype scaffolding. Design the visual output; the implementer recreates the structure as React components.
- **Body-scoped CSS resets** that bleed beyond the page — scope under a single root class like `.dhc-<feature>-shell`.

### Accessibility minimums

- Provide a static-frame fallback for any continuous canvas animation (the implementer wires `prefers-reduced-motion: reduce`).
- Maintain ≥ 4.5:1 contrast on body text; the dark slate backgrounds make this easy to break with low-opacity text.
- Form inputs need a visible focus state, not just a colour shift in the border.
- Don't rely on colour alone for state (success/warning/error all need an icon, prefix, or label).

### Latest shipped designs (update this section as new ones land)

- **2026-05-06 — DHC Modeler Login.html.** Custom terminal-aesthetic sign-in (no Amplify `<Authenticator>`), animated 4-namespace ontology canvas background (`brick:`, `rec:`, `s223:`, `dhc:` clusters with horizontal scan beam), full custom auth state machine. The shipped version drops the prototype's SmartHome ID dropdown and SSO button. New locale keys live under `signin.*` in `repos/modeler/src/locales/{en,de,fr}/common.json`. New components: `SignInBackground`, `SignInHeader`, `SignInCard` under `repos/modeler/src/components/`.

When you iterate on a previously shipped design, treat the shipped version as the source of truth and propose deltas, not a from-scratch redesign.

## End context block — paste up to here

---

### When to refresh this prompt

Update the "Latest shipped designs" section every time a design lands in the codebase. Add a one-liner with the date, the file name, and the key delta vs. the prototype (what was kept, what was stripped). That keeps Claude Design from re-suggesting patterns that have already been ruled out.

If hard constraints change in the platform (federation gets configured, a new app joins the family, the palette shifts), update the relevant section here so the next iteration has the truth.
