# Amplify Gen 2 Backend Integration

This document describes how the DigitalHome.Cloud platform provisions and
consumes its shared **AWS Amplify Gen 2** backend.

> Historical note: the platform previously ran an Amplify **Gen 1** backend
> with an `aws-exports.js` / `aws-exports.deployment.js` env-var bridge (see
> ADR 0003). That model — `amplify pull`, `sync-env.sh`,
> `generate-aws-config-from-master.js` — is **gone**. If you see it referenced
> anywhere, it is stale.

---

## Where the backend lives

The Gen 2 backend is defined in TypeScript inside the **`repos/core`
submodule**:

```
repos/core/
  amplify/
    backend.ts            defineBackend({...}) + CDK overrides
    auth/resource.ts      Cognito (email login, groups, postConfirmation trigger)
    data/resource.ts      AppSync models + custom mutations
    storage/resource.ts   S3 prefixes (tenant/* via proxy Lambda only)
    functions/            createDigitalHome, dhcDesignStorageProxy, postConfirmation
  amplify.yml             backend-only Amplify Hosting build
  package.json            dual-purpose: ontology vitest harness + Amplify toolchain
  tsconfig.json
```

It was moved out of the umbrella root because having an `amplify/` directory at
the umbrella *and* in a submodule that Amplify Hosting builds caused conflicts
("amplify on two levels of a repo"). There is now exactly one `amplify/` level,
owned by `core`. The umbrella root has no `amplify/`, `package.json`, or
`tsconfig.json`.

Portal, Designer, and Modeler are **frontend-only consumers**. Each commits its
own `src/amplify_outputs.json` (public Cognito User Pool / AppSync endpoint / S3
bucket IDs) and configures Amplify JS v6 with it in `gatsby-browser.js` /
`gatsby-ssr.js`:

```js
import outputs from "./src/amplify_outputs.json";
Amplify.configure(outputs);
```

`amplify_outputs.json` holds only public identifiers — it is safe to commit and
needed at build time. There are no API keys; AppSync uses Cognito/IAM auth.

---

## Local development

```bash
cd repos/core
npm install
npx ampx sandbox            # personal stack; one per developer (--once for one-shot)
# writes repos/core/amplify_outputs.json (gitignored)

# propagate into each app (scripts/dev-start-all.sh does this automatically):
cp amplify_outputs.json ../portal/src/
cp amplify_outputs.json ../designer/src/
cp amplify_outputs.json ../modeler/src/
```

Each app then runs `yarn develop` and talks to your running sandbox stack.
`repos/core/amplify_outputs.json`, `amplify_outputs.d.ts`, and `.amplify/` are
gitignored (per-developer sandbox state).

---

## CI / deployment

Two kinds of Amplify Hosting app:

1. **Backend deployer** — `repos/core` itself. On push, `repos/core/amplify.yml`
   runs `npm install` then
   `npx ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID`,
   deploying the CloudFormation stack (Cognito, AppSync, DynamoDB, S3, Lambdas).
   Its `frontend` phase only emits a stub `index.html` (Amplify Hosting requires
   a non-empty artifact tree). It uses `npm install`, not `npm ci`, because the
   single `package.json` serves both the ontology test harness and the Amplify
   backend and the committed lockfile is not regenerated on every dep change.

2. **Frontend apps** — Portal / Designer / Modeler. Each app's own `amplify.yml`
   `preBuild` pulls the deployed backend config with
   `npx ampx generate outputs --branch $AMPLIFY_BACKEND_APP_BRANCH --app-id $AMPLIFY_BACKEND_APP_ID --out-dir ./src`,
   then runs the Gatsby build. The committed `src/amplify_outputs.json` is the
   fallback / local-dev copy.

Branch mapping (all repos): `stage` → staging, `main` → production.

---

## Stage status (May 2026)

- `repos/core` branch `stage` → the live **stage backend**.
- The **stage Designer** is wired to it and **operational**
  (Cognito User Pool `eu-central-1_THCQaPWiv`).
- Portal and Modeler still commit `amplify_outputs.json` pointing at the
  previous pool (`eu-central-1_QTq7NVm2M`). Re-pointing them at the stage
  backend is **pending** — do not assume all three apps share one stack yet.

---

## See also

- `dhc-amplify-gen2` skill (`.claude/skills/dhc-amplify-gen2/SKILL.md`) —
  authoring patterns, sandbox workflow, CDK escape hatches, migration gotchas.
- ADR 0003 — Amplify backend generation decision (Gen 1 → Gen 2 history).
- ADR 0008 — umbrella repo with submodules (records the backend relocation).
- `repos/core/CLAUDE.md` — backend ownership from the core repo's perspective.
