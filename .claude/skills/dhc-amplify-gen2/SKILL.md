---
name: dhc-amplify-gen2
description: Use when authoring or editing the AWS Amplify Gen 2 backend (auth, data, storage, functions, custom CDK), running the sandbox, or troubleshooting Amplify Hosting builds. Triggers on phrases like "add a Lambda", "update the schema", "add an @auth rule", "amplify gen2", "deploy backend change", "amplify sandbox", "pipeline-deploy".
---

# DHC Amplify Gen 2 — backend authoring & deployment

The DHC platform runs on **AWS Amplify Gen 2**. The backend is defined as
TypeScript **inside the `repos/core` submodule** (`repos/core/amplify/`). It was
moved there from the umbrella root because having an `amplify/` directory at the
umbrella *and* a submodule that Amplify Hosting builds caused "amplify on two
levels of a repo" conflicts — there is now exactly one `amplify/` level, owned
by `core`. Submodules (`portal`, `designer`, `modeler`) are frontend-only
consumers — they read `src/amplify_outputs.json` to talk to the deployed
backend.

This skill covers:
1. Repo layout — where each category lives
2. Sandbox workflow — how to deploy + iterate locally
3. Authoring patterns — schema, auth, storage, functions
4. CDK escape hatches — when the high-level API doesn't expose a knob
5. Cutover/decommission notes — what's gone since Gen 1
6. Gotchas — real bugs hit during the May 2026 migration

---

## 1. Repo layout

```
repos/core/                                         ← owns the backend
  amplify/
    backend.ts                                      ← top-level defineBackend({...}) + CDK overrides
    auth/resource.ts                                ← defineAuth: email + groups + postConfirmation trigger
    data/resource.ts                                ← defineData: models + custom mutations
    storage/resource.ts                             ← defineStorage: public/protected/private prefixes (tenant/* deliberately omitted)
    functions/
      createDigitalHome/                            ← initiate-flow Lambda (A-Box bootstrap)
      dhcDesignStorageProxy/                        ← signed-URL Lambda for tenant data (DH-SPEC-203)
      postConfirmation/                             ← Cognito trigger: add new users to dhc-welcome
  amplify.yml                                       ← Amplify Hosting CI: npm install + ampx pipeline-deploy
  package.json                                      ← @dhc/digitalhome-cloud-core: vitest harness + Amplify toolchain
  tsconfig.json                                     ← target es2022, module es2022, moduleResolution bundler
  amplify_outputs.json                              ← gitignored (per-developer sandbox output)
  amplify_outputs.d.ts                              ← gitignored
  .amplify/                                         ← gitignored (sandbox state cache)

repos/portal/    src/amplify_outputs.json           ← committed (deployed-stack public IDs)
repos/designer/  src/amplify_outputs.json           ← committed
repos/modeler/   src/amplify_outputs.json           ← committed
```

**Hard rules:**
- The Gen 2 backend lives in the **`repos/core` submodule**, not at the
  umbrella root and not inside any frontend submodule. The umbrella root has
  **no** `amplify/`, `package.json`, or `tsconfig.json` — those were removed
  when the backend moved into `core` (that was the "two `amplify/` levels"
  conflict). Don't recreate `repos/portal/amplify/` (Gen 1 layout, gone) or a
  second umbrella-root `amplify/`.
- `repos/core/package.json` serves **two roles**: the ontology vitest test
  harness *and* the Amplify backend toolchain. Don't strip either side.
- Each frontend app's `src/amplify_outputs.json` IS committed. It contains
  public Cognito User Pool IDs, AppSync endpoints, and the S3 bucket name —
  needed at build time.
- `repos/core/amplify_outputs.json` is **gitignored** because
  `npx ampx sandbox` writes it per-developer. Copy from there into each app's
  `src/amplify_outputs.json` after a sandbox redeploy.

### Stage status (as of May 2026)

- `repos/core` branch `stage` → the **stage backend** (Amplify Hosting
  backend-only app runs `npx ampx pipeline-deploy --branch stage`).
- The **stage Designer** is wired to it and **operational**: its committed
  `repos/designer/src/amplify_outputs.json` points at Cognito User Pool
  `eu-central-1_THCQaPWiv` / AppSync `jjscfn2izfhllgpo673kqvfd4e…eu-central-1`.
- **Portal and Modeler are NOT yet re-pointed** — their committed
  `amplify_outputs.json` still target the older pool
  `eu-central-1_QTq7NVm2M`. Treat Portal/Modeler ↔ stage backend as **pending**;
  don't assume all three apps share one stack until that re-point lands.

---

## 2. Sandbox workflow

```bash
cd ~/digitalhomeCloud/digitalhome-cloud-darkfactory/repos/core   # backend lives here
npm install                                             # once

# Deploy your personal sandbox stack (idempotent; cheap to re-run).
# Watches amplify/ and redeploys on save by default.
npx ampx sandbox                                        # foreground watch mode
npx ampx sandbox --once                                 # one-shot deploy then exit
npx ampx sandbox delete                                 # tear it down when finished

# After a sandbox redeploy, propagate outputs to each app (run from repos/core):
cp amplify_outputs.json ../portal/src/
cp amplify_outputs.json ../designer/src/
cp amplify_outputs.json ../modeler/src/
```

**Stack name:** auto-generated, includes a developer hash — one stack per
developer per checkout, fully isolated.

**Frontend dev:** each app's `gatsby-browser.js` and `gatsby-ssr.js` import the
local `src/amplify_outputs.json`. Run `yarn develop` (in the app dir) and the
running sandbox is what you'll hit. From the umbrella, `scripts/dev-start-all.sh`
seeds each app's `src/amplify_outputs.json` from `repos/core/amplify_outputs.json`
if it's missing.

**Run `npx ampx sandbox` from `repos/core`** — that is the submodule that owns
`amplify/`. It will fail (or worse, scaffold a stray `amplify/`) if run from the
umbrella root or a frontend submodule.

---

## 3. Authoring patterns

### 3a. Adding / changing a data model (`repos/core/amplify/data/resource.ts`)

```ts
import { type ClientSchema, a, defineData } from "@aws-amplify/backend";

const schema = a.schema({
  // owner-scoped: each item's `owner` field is auto-set to the Cognito sub
  // creating it, and only that owner (+ admins) can read/update/delete.
  UserProfile: a.model({
    email: a.email().required(),
    locale: a.string(),
    // ... fields
  })
    .authorization((allow) => [
      allow.owner(),
      allow.group("dhc-admins").to(["read"]),
    ]),

  // multi-owner: list of Cognito subs, all of whom can read/write.
  // Used by SmartHome and SmartHomeDesign to support shared homes.
  SmartHome: a.model({
    smartHomeId: a.string().required(),
    owners: a.string().array(),
    // ...
  })
    .authorization((allow) => [
      allow.ownersDefinedIn("owners"),
      allow.group("dhc-admins"),
    ])
    .secondaryIndexes((index) => [index("smartHomeId")]),

  // admin-only writes, all-authenticated reads (component library)
  LibraryItem: a.model({ ... })
    .authorization((allow) => [
      allow.authenticated().to(["read"]),
      allow.group("dhc-admins"),
    ]),
});

export type Schema = ClientSchema<typeof schema>;
export const data = defineData({ schema });
```

**Authorization rules used in DHC:**
- `allow.owner()` — single owner, set automatically from Cognito sub. Use for personal data (UserProfile).
- `allow.ownersDefinedIn("owners")` — multi-owner via a `String[]` field. The user must add owner subs explicitly. Use for shared resources (SmartHome).
- `allow.group("dhc-admins")` — full CRUD for group members.
- `allow.group("dhc-admins").to(["read"])` — admin read-only.
- `allow.authenticated()` — any signed-in user. Use sparingly.
- **Never `allow.public()` or `allow.guest()`** — was the C-3 footgun in Gen 1.

If a model has zero `.authorization()` rules, **all access is denied by default**. That's the Gen 2 default-deny we rely on.

### 3b. Custom mutations backed by a Lambda (`requestDesignReadUrl` etc.)

```ts
import { dhcDesignStorageProxy } from "../functions/dhcDesignStorageProxy/resource";

// Inside a.schema({...}):
DesignStorageUrl: a.customType({
  url: a.string().required(),
  expiresAt: a.datetime().required(),
}),

requestDesignReadUrl: a.mutation()
  .arguments({ smartHomeId: a.string().required(), key: a.string().required() })
  .returns(a.ref("DesignStorageUrl"))
  .authorization((allow) => [allow.authenticated()])
  .handler(a.handler.function(dhcDesignStorageProxy)),
```

The Lambda's `event.info.fieldName` will be `"requestDesignReadUrl"` at runtime — handler dispatches on that.

### 3c. Adding a Lambda function

Two files:

**`repos/core/amplify/functions/<fnName>/resource.ts`:**
```ts
import { defineFunction } from "@aws-amplify/backend";

export const myFunction = defineFunction({
  name: "myFunction",
  entry: "./handler.ts",
  timeoutSeconds: 30,
  runtime: 20,                   // Node 20
});
```

**`repos/core/amplify/functions/<fnName>/handler.ts`:**
```ts
import type { AppSyncResolverHandler, AppSyncIdentityCognito } from "aws-lambda";
import { env } from "$amplify/env/myFunction";

export const handler: AppSyncResolverHandler<unknown, unknown> = async (event) => {
  const identity = event.identity as AppSyncIdentityCognito;
  const userSub = identity.sub;
  // env.MY_VAR_NAME is typed and set at deploy time (see backend.ts addEnvironment)
  // ...
};
```

**Then wire it in `repos/core/amplify/backend.ts`:**
```ts
import { myFunction } from "./functions/myFunction/resource";

const backend = defineBackend({
  auth, data, storage,
  myFunction,            // ← add here
});
```

If the function needs IAM beyond the default (e.g., DDB access, S3 access, Cognito admin) — see section 4.

### 3d. Adding a Cognito group

Edit `repos/core/amplify/auth/resource.ts`:
```ts
export const auth = defineAuth({
  loginWith: { email: true },
  groups: [
    "dhc-admins",
    "dhc-modelers",
    "dhc-professional",
    "dhc-standard",
    "dhc-welcome",
    "dhc-newgroup",        // ← add here
  ],
  triggers: { postConfirmation },
});
```

The Cognito User Pool gets the new group on next deploy. **Don't add groups via the AWS console** — they'll be removed on next sandbox redeploy.

### 3e. Adding a storage path

Edit `repos/core/amplify/storage/resource.ts`:
```ts
export const storage = defineStorage({
  name: "dhcStorage",
  access: (allow) => ({
    "public/*": [
      allow.authenticated.to(["read", "write"]),
      allow.guest.to(["read"]),
    ],
    "protected/{entity_id}/*": [
      allow.authenticated.to(["read"]),
      allow.entity("identity").to(["read", "write", "delete"]),
    ],
    "private/{entity_id}/*": [
      allow.entity("identity").to(["read", "write", "delete"]),
    ],
    // tenant/* deliberately omitted.  All access is via the proxy Lambda.
    // Adding any rule here would break C-2.
  }),
});
```

---

## 4. CDK escape hatches (cross-resource IAM, DDB knobs)

When the high-level Amplify API doesn't expose a knob, drop into CDK in
`repos/core/amplify/backend.ts`. All examples are real patterns from this repo.

### 4a. Grant a function S3 + DynamoDB access

Gen 2 doesn't auto-grant cross-resource IAM when a function is wired as a custom-mutation handler. Do it explicitly:

```ts
import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";

const proxyLambda = backend.dhcDesignStorageProxy.resources.lambda;
const bucket = backend.storage.resources.bucket;
const tbl = backend.data.resources.tables.SmartHomeDesign;

proxyLambda.addToRolePolicy(
  new PolicyStatement({
    effect: Effect.ALLOW,
    actions: ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
    resources: [`${bucket.bucketArn}/*`],
  })
);

proxyLambda.addToRolePolicy(
  new PolicyStatement({
    effect: Effect.ALLOW,
    actions: ["dynamodb:GetItem", "dynamodb:Query", "dynamodb:Scan", "dynamodb:BatchGetItem"],
    resources: [tbl.tableArn, `${tbl.tableArn}/index/*`],
  })
);

backend.dhcDesignStorageProxy.addEnvironment("STORAGE_BUCKET_NAME", bucket.bucketName);
backend.dhcDesignStorageProxy.addEnvironment("SMARTHOMEDESIGN_TABLE_NAME", tbl.tableName);
```

### 4b. Grant a Cognito trigger admin permissions (and avoid CFN cycles)

Naively scoping IAM to `backend.auth.resources.userPool.userPoolArn` creates a CloudFormation **circular dependency**: the auth stack already references the trigger Lambda, and adding the Lambda's role → User Pool ARN closes the cycle.

**Fix:** use a wildcard ARN scoped to the AWS account+region. The trigger event carries `event.userPoolId` at runtime, so the Lambda can address the actual pool, while the IAM stays decoupled:

```ts
import { Stack } from "aws-cdk-lib";

const stack = Stack.of(backend.postConfirmation.resources.lambda);
const userPoolWildcardArn = `arn:aws:cognito-idp:${stack.region}:${stack.account}:userpool/*`;

backend.postConfirmation.resources.lambda.addToRolePolicy(
  new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      "cognito-idp:AdminAddUserToGroup",
      "cognito-idp:GetGroup",
      "cognito-idp:CreateGroup",
    ],
    resources: [userPoolWildcardArn],
  })
);
```

### 4c. Enable DynamoDB Point-in-Time Recovery (PITR)

The Amplify-managed DDB tables are **not standard `aws_dynamodb.Table` constructs** — they're custom `Custom::AmplifyDynamoDBTable` resources wrapped by `AmplifyDynamoDbTable`. So `(table.node.defaultChild as CfnTable).pointInTimeRecoverySpecification` does **not** work.

**Use the `cfnResources.amplifyDynamoDbTables` map:**

```ts
const tablesNeedingPITR = ["UserProfile", "LibraryItem", "SmartHome", "SmartHomeDesign"] as const;
for (const tableName of tablesNeedingPITR) {
  backend.data.resources.cfnResources.amplifyDynamoDbTables[tableName].pointInTimeRecoveryEnabled = true;
}
```

**Verify** by inspecting `.amplify/artifacts/cdk.out/<stack>/<modelName>.nested.template.json` — look for `"pointInTimeRecoverySpecification": { "pointInTimeRecoveryEnabled": true }` on the `Custom::AmplifyDynamoDBTable` resource. (The legacy `DynamoDBEnablePointInTimeRecovery` parameter near the top defaults to `"false"` and is unrelated to the L2 setter — don't be fooled.)

PITR is free up to 35 days of recovery window. Required for any model that holds non-throwaway data.

---

## 5. Cutover / decommission notes — what's gone

The migration removed these Gen 1 artifacts. **Don't recreate them:**

| Gone | Replaced by |
|---|---|
| `repos/portal/amplify/` (per-app backend dirs) | Single `repos/core/amplify/` |
| Umbrella-root `amplify/` + `package.json` + `tsconfig.json` | Moved into `repos/core` (one `amplify/` level per repo) |
| `src/aws-exports.js` (everywhere) | `src/amplify_outputs.json` |
| `src/aws-exports.deployment.js` (env-var shim) | `amplify_outputs.json` is already deploy-portable |
| `scripts/sync-env.sh` (symlinks) | Direct file copy or `npx ampx generate outputs` |
| `scripts/generate-aws-config-from-master.js` | Same as above |
| `.graphqlconfig.yml` (codegen config) | `npx ampx generate graphql-client-code` |
| `.env.development` GATSBY_* config from Amplify | Kept ONLY for cross-app URLs (`GATSBY_PORTAL_URL` etc.) |
| `amplify push`, `amplify pull`, `amplify codegen` | `npx ampx sandbox`, `npx ampx pipeline-deploy`, `npx ampx generate` |
| `amplify add function` (interactive) | Edit TypeScript directly |

If you see any of these in the codebase, it's **stale documentation** — flag it for cleanup, don't follow it.

---

## 6. Gotchas hit during the May 2026 migration

These are landmines we already stepped on. Knowing about them saves an hour each.

### 6a. `Cannot find module './auth/resource'`
Initial sandbox deploy failed because TypeScript was emitting CommonJS but the imports use bare `./auth/resource` (no `.js` extension). **Fix:** `repos/core/package.json` has `"type": "module"` and `repos/core/tsconfig.json` has `"module": "es2022"` and `"moduleResolution": "bundler"` (lowercase, exact strings). Keep them.

### 6b. `auth configuration error` after toggling globalAuthRule
Originally the Gen 1 schema had `@auth(rules: [{ allow: public, provider: apiKey }])` and we tried switching to `private` mid-flight. **Fix in Gen 2:** there is no `globalAuthRule`. Each model has its own `.authorization()`; default-deny applies if you forget. So just don't reintroduce a public rule unless you have to.

### 6c. `with { type: "json" }` import attribute syntax errors
Babel/Webpack reject ES2024 import attributes in Gatsby builds. **Fix:** import JSON without the attributes clause:
```js
// ❌ import outputs from "./src/amplify_outputs.json" with { type: "json" };
// ✅
import outputs from "./src/amplify_outputs.json";
```
Gatsby's webpack handles JSON imports natively.

### 6d. Missing `src/graphql/{queries,mutations,subscriptions}.js` after `amplify delete`
`amplify delete` from the Gen 1 directory deletes the autogen GraphQL TypeScript clients along with the backend. **Fix:** before running, copy them out (`cp -r repos/portal/src/graphql /tmp/`); restore after. Or pre-generate Gen 2 clients first via `npx ampx generate graphql-client-code --out repos/portal/src/graphql`.

### 6e. `amplify delete` doesn't delete non-default environments
It only deletes the env you're currently in. **Fix:** delete the leftover Gen 1 staging stack manually:
```bash
aws cloudformation delete-stack --stack-name amplify-digitalhomecloudback-staging-...
```

### 6f. AWS account / IAM perms for `npx ampx`
The `dlab5_devops` IAM user used in this repo has gaps — for example, no `dynamodb:DescribeContinuousBackups`. That blocks **verification CLI calls** but not deployments. When verifying a CDK setting, **read the synthesized CFN template** in `.amplify/artifacts/cdk.out/` rather than relying on `aws <service> describe-...`.

### 6g. `requestDesignReadUrl` returns AccessDenied at runtime
Symptom: the Lambda is invoked but S3 / DDB calls 403. Cause: the IAM grants in `backend.ts` weren't reapplied after a code-only change to `handler.ts`. **Fix:** trigger a redeploy by editing any file under `repos/core/amplify/` (or run `npx ampx sandbox --once`). Code-only changes to handler bodies sometimes don't redeploy resource policies.

### 6h. `target=_blank` audit grep false-positive
Audit recipe `grep -v "noopener\|noreferrer"` only sees one line at a time, but JSX usually splits attributes across lines. The `dhc-security-audit` skill's recipe uses a 2-line window now — match the same pattern in any new audit grepping.

### 6i. The "two `amplify/` levels" conflict (why the backend lives in `core`)
With `amplify/` at the umbrella root *and* `repos/core` (a submodule Amplify
Hosting builds), `ampx`/tooling resolved the wrong `amplify/` and IDE/CDK
context got confused. **Fix applied:** the backend moved into `repos/core`; the
umbrella root has no `amplify/`/`package.json`/`tsconfig.json`. The Amplify
`package.json` overwrote core's ontology-test `package.json` in the move — they
are now **merged** in `repos/core/package.json` (vitest harness + Amplify
toolchain). Don't "fix" core's package.json by dropping either half. Because
that one lockfile serves two roles, `repos/core/amplify.yml` uses
`npm install`, not `npm ci`.

---

## Verifying a backend change end-to-end

1. **Author** the change in `repos/core/amplify/`.
2. From `repos/core`: `npx ampx sandbox --once` — confirm green deploy.
3. `cp repos/core/amplify_outputs.json repos/<app>/src/` for any frontend that needs the new config.
4. `cd repos/<app> && yarn build` — confirm the frontend still builds.
5. **For a security-sensitive change** (auth rule, IAM, storage path): run the `dhc-security-audit` skill afterward to confirm no new findings.
6. Inspect synthesized CFN if a knob's effect isn't visible: `repos/core/.amplify/artifacts/cdk.out/<stack>/<resource>.nested.template.json`.
7. Commit in `repos/core`, bump the umbrella's `repos/core` submodule pointer, and push. **CI:** `repos/core/amplify.yml` runs `npm install` + `npx ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID` on push (a backend-only Amplify Hosting app). Each frontend app's own `amplify.yml` pulls the deployed config via `npx ampx generate outputs --branch $AMPLIFY_BACKEND_APP_BRANCH --app-id $AMPLIFY_BACKEND_APP_ID --out-dir ./src` in its `preBuild`.

---

## Reference: `repos/core/package.json` + `tsconfig.json`

`repos/core/package.json` is dual-purpose — the ontology vitest harness **and**
the Amplify backend toolchain live in one manifest:

```json
// repos/core/package.json
{
  "name": "@dhc/digitalhome-cloud-core",
  "version": "2.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "amplify:sandbox": "ampx sandbox",
    "amplify:sandbox:delete": "ampx sandbox delete",
    "amplify:generate": "ampx generate graphql-client-code",
    "amplify:pipeline-deploy": "ampx pipeline-deploy"
  },
  "devDependencies": {
    "@aws-amplify/backend": "^1.16.0",
    "@aws-amplify/backend-cli": "^1.7.0",
    "@types/node": "^22.7.0",
    "@zazuko/env-node": "^1.0.0",
    "aws-cdk": "^2.158.0",
    "aws-cdk-lib": "^2.158.0",
    "constructs": "^10.4.0",
    "rdf-validate-shacl": "^0.6.0",
    "typescript": "^5.6.0",
    "vitest": "^3.0.0"
  },
  "dependencies": {
    "aws-amplify": "^6.6.0",
    "@aws-sdk/client-s3": "^3.658.0",
    "@aws-sdk/s3-request-presigner": "^3.658.0",
    "@aws-sdk/client-dynamodb": "^3.658.0",
    "@aws-sdk/util-dynamodb": "^3.658.0",
    "@aws-sdk/client-cognito-identity-provider": "^3.658.0",
    "@types/aws-lambda": "^8.10.145",
    "n3": "^1.17.4",
    "@types/n3": "^1.16.4"
  }
}
```

```json
// repos/core/tsconfig.json
{
  "compilerOptions": {
    "target": "es2022",
    "module": "es2022",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "paths": { "$amplify/*": ["./.amplify/generated/*"] }
  },
  "include": ["amplify/**/*"],
  "exclude": ["node_modules", "repos", "**/.cache", "**/public", "**/build"]
}
```
