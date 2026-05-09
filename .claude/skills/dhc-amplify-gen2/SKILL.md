---
name: dhc-amplify-gen2
description: Use when authoring or editing the AWS Amplify Gen 2 backend (auth, data, storage, functions, custom CDK), running the sandbox, or troubleshooting Amplify Hosting builds. Triggers on phrases like "add a Lambda", "update the schema", "add an @auth rule", "amplify gen2", "deploy backend change", "amplify sandbox", "pipeline-deploy".
---

# DHC Amplify Gen 2 — backend authoring & deployment

The DHC platform runs on **AWS Amplify Gen 2**. The backend is defined as TypeScript at the **umbrella repo root** (`digitalhome-cloud-darkfactory/amplify/`). Submodules (`portal`, `designer`, `modeler`) are frontend-only consumers — they read `src/amplify_outputs.json` to talk to the deployed backend.

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
digitalhome-cloud-darkfactory/                    ← umbrella, owns the backend
  amplify/
    backend.ts                                    ← top-level defineBackend({...}) + CDK overrides
    auth/resource.ts                              ← defineAuth: email + 5 groups + postConfirmation trigger
    data/resource.ts                              ← defineData: 4 models + 2 custom mutations
    storage/resource.ts                           ← defineStorage: public/protected/private prefixes (tenant/* deliberately omitted)
    functions/
      dhcDesignStorageProxy/                      ← signed-URL Lambda for tenant data (DH-SPEC-203)
        resource.ts
        handler.ts
      postConfirmation/                           ← Cognito trigger: add new users to dhc-welcome
        resource.ts
        handler.ts
  package.json                                    ← @aws-amplify/backend, aws-cdk-lib, typescript
  tsconfig.json                                   ← target es2022, module es2022, moduleResolution bundler
  amplify_outputs.json                            ← gitignored (per-developer sandbox output)
  amplify_outputs.d.ts                            ← gitignored
  .amplify/                                       ← gitignored (sandbox state cache)

repos/portal/    src/amplify_outputs.json         ← committed (deployed-stack public IDs)
repos/designer/  src/amplify_outputs.json         ← committed
repos/modeler/   src/amplify_outputs.json         ← committed
```

**Hard rules:**
- The Gen 2 backend lives at the **umbrella root**, not inside any submodule. Don't create `repos/portal/amplify/` or similar — that was the Gen 1 layout and is gone.
- Each app's `src/amplify_outputs.json` IS committed. It contains public Cognito User Pool IDs, AppSync endpoints, and the S3 bucket name — needed at build time.
- The umbrella's root `amplify_outputs.json` is **gitignored** because `npx ampx sandbox` writes it per-developer. Copy from there into each app's `src/amplify_outputs.json` after sandbox redeploy.

---

## 2. Sandbox workflow

```bash
cd ~/digitalhomeCloud/digitalhome-cloud-darkfactory     # umbrella root
npm install                                             # once

# Deploy your personal sandbox stack (idempotent; cheap to re-run).
# Watches amplify/ and redeploys on save by default.
npx ampx sandbox                                        # foreground watch mode
npx ampx sandbox --once                                 # one-shot deploy then exit
npx ampx sandbox delete                                 # tear it down when finished

# After a sandbox redeploy, propagate outputs to each app:
cp amplify_outputs.json repos/portal/src/
cp amplify_outputs.json repos/designer/src/
cp amplify_outputs.json repos/modeler/src/
```

**Stack name:** `amplify-digitalhomeclouddarkfactory-dhc-gen2-init-sandbox-...` (auto-generated, includes a developer hash). One stack per developer per checkout — fully isolated.

**Frontend dev:** each app's `gatsby-browser.js` and `gatsby-ssr.js` import the local `src/amplify_outputs.json`. Run `yarn develop` (in the app dir) and the running sandbox is what you'll hit.

**Don't** run `npx ampx sandbox` from inside a submodule — there's no `amplify/` directory there. It will fail or, worse, create one.

---

## 3. Authoring patterns

### 3a. Adding / changing a data model (`amplify/data/resource.ts`)

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

**`amplify/functions/<fnName>/resource.ts`:**
```ts
import { defineFunction } from "@aws-amplify/backend";

export const myFunction = defineFunction({
  name: "myFunction",
  entry: "./handler.ts",
  timeoutSeconds: 30,
  runtime: 20,                   // Node 20
});
```

**`amplify/functions/<fnName>/handler.ts`:**
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

**Then wire it in `backend.ts`:**
```ts
import { myFunction } from "./functions/myFunction/resource";

const backend = defineBackend({
  auth, data, storage,
  myFunction,            // ← add here
});
```

If the function needs IAM beyond the default (e.g., DDB access, S3 access, Cognito admin) — see section 4.

### 3d. Adding a Cognito group

Edit `amplify/auth/resource.ts`:
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

Edit `amplify/storage/resource.ts`:
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

When the high-level Amplify API doesn't expose a knob, drop into CDK in `amplify/backend.ts`. All examples are real patterns from this repo.

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
| `repos/portal/amplify/` (per-app backend dirs) | Single umbrella `amplify/` |
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
Initial sandbox deploy failed because TypeScript was emitting CommonJS but the imports use bare `./auth/resource` (no `.js` extension). **Fix:** add `"type": "module"` to umbrella `package.json` and ensure `tsconfig.json` has `"module": "es2022"` and `"moduleResolution": "bundler"` (lowercase, exact strings).

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
It only deletes the env you're currently in. **Fix:** delete the staging stack manually:
```bash
aws cloudformation delete-stack --stack-name amplify-digitalhomecloudback-staging-...
```

### 6f. AWS account / IAM perms for `npx ampx`
The `dlab5_devops` IAM user used in this repo has gaps — for example, no `dynamodb:DescribeContinuousBackups`. That blocks **verification CLI calls** but not deployments. When verifying a CDK setting, **read the synthesized CFN template** in `.amplify/artifacts/cdk.out/` rather than relying on `aws <service> describe-...`.

### 6g. `requestDesignReadUrl` returns AccessDenied at runtime
Symptom: the Lambda is invoked but S3 / DDB calls 403. Cause: the IAM grants in `backend.ts` weren't reapplied after a code-only change to `handler.ts`. **Fix:** trigger a redeploy by editing any file under `amplify/` (or run `npx ampx sandbox --once`). Code-only changes to handler bodies sometimes don't redeploy resource policies.

### 6h. `target=_blank` audit grep false-positive
Audit recipe `grep -v "noopener\|noreferrer"` only sees one line at a time, but JSX usually splits attributes across lines. The `dhc-security-audit` skill's recipe uses a 2-line window now — match the same pattern in any new audit grepping.

---

## Verifying a backend change end-to-end

1. **Author** the change in `amplify/`.
2. `npx ampx sandbox --once` — confirm green deploy.
3. `cp amplify_outputs.json repos/<app>/src/` for any frontend that needs the new config.
4. `cd repos/<app> && yarn build` — confirm the frontend still builds.
5. **For a security-sensitive change** (auth rule, IAM, storage path): run the `dhc-security-audit` skill afterward to confirm no new findings.
6. Inspect synthesized CFN if a knob's effect isn't visible: `.amplify/artifacts/cdk.out/<stack>/<resource>.nested.template.json`.
7. Commit. The Amplify Hosting build (`amplify.yml` per app) runs `npx ampx pipeline-deploy --branch $AWS_BRANCH --app-id $AWS_APP_ID` automatically when you push.

---

## Reference: minimum `package.json` + `tsconfig.json`

```json
// package.json (umbrella root)
{
  "name": "digitalhome-cloud-darkfactory",
  "type": "module",
  "scripts": {
    "sandbox": "npx ampx sandbox",
    "sandbox:once": "npx ampx sandbox --once",
    "sandbox:delete": "npx ampx sandbox delete"
  },
  "devDependencies": {
    "@aws-amplify/backend": "^1.16.0",
    "@aws-amplify/backend-cli": "^1.7.0",
    "@types/aws-lambda": "^8.10.0",
    "aws-cdk-lib": "^2.158.0",
    "typescript": "^5.6.0"
  },
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.658.0",
    "@aws-sdk/client-s3": "^3.658.0",
    "@aws-sdk/s3-request-presigner": "^3.658.0"
  }
}
```

```json
// tsconfig.json (umbrella root)
{
  "compilerOptions": {
    "target": "es2022",
    "module": "es2022",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "paths": { "$amplify/*": ["./.amplify/generated/*"] }
  }
}
```
