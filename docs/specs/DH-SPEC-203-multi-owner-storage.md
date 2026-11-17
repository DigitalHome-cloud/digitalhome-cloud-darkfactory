# DH-SPEC-203 — Multi-owner SmartHome storage via AppSync-mediated signed URLs

**Status**: Designed; awaiting implementation (this spec is the runbook).
**Closes audit finding**: C-2 multi-owner variant.
**Date**: 2026-05-07

## Why

The interim C-2 fix routed real-tenant design data through `private/{cognito-identity-id}/smarthomes/{id}/...`. That works for a single owner per SmartHome but breaks the multi-owner model the AppSync schema (`SmartHome.owners: [String]`) supports: only the originating Cognito identity can read or write the path.

ADR-0010 originally said *"access control is enforced by AppSync resolvers and application logic"* — meaning the design was always to mediate S3 access through AppSync, with bucket policy denying direct tenant prefix access. This spec implements that.

## End-state architecture

```
   Designer (browser)
        │
        │ 1. mutation requestDesignReadUrl(smartHomeId, fileName)
        ▼
   AppSync (Cognito User Pool auth)
        │
        │ 2. resolver invokes Lambda dhcDesignStorageProxy
        ▼
   Lambda
        │ 3. checks identity.username ∈ SmartHomeDesign.owners
        │    OR identity.groups ⊇ {dhc-admins}
        │
        │ 4. getSignedUrl(GetObject, key=tenant/{id}/{file}, expiresIn=300s)
        ▼
   AppSync ← {url, expiresAt}
        │
        │ 5. Designer fetch(url) — direct to S3
        ▼
   S3 (bucket policy: DENY tenant/* to auth+unauth roles; ALLOW Lambda role)
```

Demo SmartHomes (`DE-DEMO-01`, `FR-DEMO-01`, `BE-DEMO-01`) keep using `public/smarthomes/{demoId}/...` — direct Amplify Storage. Only real homes go through the new flow.

## Step-by-step runbook

### Phase 1 — Backend (you run, I prepare)

#### 1a. Add the Lambda function

```bash
cd repos/portal
amplify add function
```

Answer the prompts:
- **? Select which capability you want to add** → `Lambda function (serverless function)`
- **? Provide an AWS Lambda function name** → `dhcDesignStorageProxy`
- **? Choose the runtime** → `NodeJS`
- **? Choose the function template** → `Hello World`
- **? Do you want to configure advanced settings?** → `Yes`
- **? Do you want to access other resources in this project from your Lambda function?** → `Yes`
  - **? Select the categories** → `[storage, api]` (toggle both with space)
  - **? Storage has 1 resources in this project. Select the one you would like your Lambda to access** → `dhcStorage`
  - **? Select the operations you want to permit on dhcStorage** → `[read, create and update, delete]`
  - **? Api has 1 resources in this project. Select the one you would like your Lambda to access** → `digitalhomecloudback`
  - **? Select the operations you want to permit on SmartHomeDesign** → `[read]` (this also exposes the table-name env var)
- **? Do you want to invoke this function on a recurring schedule?** → `No`
- **? Do you want to enable Lambda layers for this function?** → `No`
- **? Do you want to configure environment variables for this function?** → `No`
- **? Do you want to configure secret values this function can access?** → `No`
- **? Do you want to edit the local lambda function now?** → `No`

This generates `amplify/backend/function/dhcDesignStorageProxy/` with the right CFN wiring.

#### 1b. Replace the generated Lambda source with the prepared version

```bash
cd /home/frankuwe/digitalhomeCloud/digitalhome-cloud-darkfactory
cp docs/specs/DH-SPEC-203-multi-owner-storage/lambda/index.js \
   repos/portal/amplify/backend/function/dhcDesignStorageProxy/src/index.js
cp docs/specs/DH-SPEC-203-multi-owner-storage/lambda/package.json \
   repos/portal/amplify/backend/function/dhcDesignStorageProxy/src/package.json
cd repos/portal/amplify/backend/function/dhcDesignStorageProxy/src
npm install
```

#### 1c. Add the AppSync mutations to the schema

Edit `repos/portal/amplify/backend/api/digitalhomecloudback/schema.graphql` and append at the bottom (after the existing `SmartHomeDesign` type):

```graphql

# Multi-owner-safe S3 access. The Lambda dhcDesignStorageProxy verifies
# the caller is in SmartHomeDesign.owners (or the dhc-admins group) and
# returns a 5-min pre-signed S3 URL pointing at tenant/{smartHomeId}/{fileName}.
type DesignStorageUrl {
  url: String!
  expiresAt: AWSDateTime!
  contentType: String
}

type Mutation {
  requestDesignReadUrl(
    smartHomeId: ID!
    fileName: String!
  ): DesignStorageUrl
    @function(name: "dhcDesignStorageProxy-${env}")
    @auth(rules: [{ allow: private }])

  requestDesignWriteUrl(
    smartHomeId: ID!
    fileName: String!
    contentType: String
  ): DesignStorageUrl
    @function(name: "dhcDesignStorageProxy-${env}")
    @auth(rules: [{ allow: private }])
}
```

#### 1d. Push to AWS

```bash
cd repos/portal
amplify push --yes
```

Expected output: CloudFormation updates `apidigitalhomecloudback`, creates `functiondhcDesignStorageProxy`, regenerates GraphQL operations (`src/graphql/mutations.js` will gain `requestDesignReadUrl` and `requestDesignWriteUrl`).

#### 1e. Tighten the bucket policy (manual — needs CFN edit + push)

The Lambda has S3 access automatically. We also need to **deny** all other roles from accessing `tenant/*` so direct S3 calls bypassing AppSync are blocked.

Edit `repos/portal/amplify/backend/storage/dhcStorage/cli-inputs.json` is NOT enough — the `cli-inputs.json` doesn't expose deny statements. Instead, edit the storage CFN override:

Run:
```bash
cd repos/portal/amplify/backend/storage/dhcStorage
amplify override storage
```

Or if `amplify override storage` isn't supported in this Amplify version, manually add a `Deny` statement to the existing `S3AuthPublicPolicy` and `S3GuestReadPolicy` policies in `cloudformation-template.json` to scope out `tenant/*`. **Do not modify `tenant/` access on the Lambda role** — keep that allowed.

The simplest deny statement to add to each authenticated/unauth role policy:

```json
{
  "Effect": "Deny",
  "Action": "s3:*",
  "Resource": [
    { "Fn::Join": ["", ["arn:aws:s3:::", { "Ref": "S3Bucket" }, "/tenant/*"]] }
  ]
}
```

Then `amplify push --yes` again.

> **If you hit a CFN circular dependency** between Storage and the Lambda's role: skip 1e for now. The Lambda is the only code that knows to write to `tenant/*`. Defense-in-depth is preferable but not strictly needed if no other code path uses that prefix. We can do this in a follow-up via a custom CDK override.

### Phase 2 — Frontend (I run, after Phase 1 succeeds)

#### 2a. Update Designer's `s3.js` to call new mutations for real homes

Demo path stays at `public/smarthomes/{demoId}/...`. Real-home reads/writes route through the new mutations.

I'll prepare the patched `repos/designer/src/utils/s3.js` once Phase 1 is deployed and the regenerated `repos/portal/src/graphql/mutations.js` is committed (the Designer needs the new mutation strings).

#### 2b. Sync regenerated GraphQL files to Designer

After Phase 1d's `amplify push`, Portal's `src/graphql/{mutations,queries,subscriptions}.js` will include the new `requestDesignReadUrl` and `requestDesignWriteUrl`. Copy those into Designer's `src/graphql/`:

```bash
cp repos/portal/src/graphql/mutations.js repos/designer/src/graphql/mutations.js
cp repos/portal/src/graphql/queries.js   repos/designer/src/graphql/queries.js
```

#### 2c. Build + verify + commit

I'll run `yarn build` in Designer, commit, and push.

### Phase 3 — Cleanup

```bash
# wipe the orphaned data the interim C-2 fix put under private/
aws s3 rm --recursive s3://digitalhome-cloudec099-main/private/
# also wipe any leftovers under public/smarthomes/ (safe — not live)
aws s3 rm --recursive s3://digitalhome-cloudec099-main/public/smarthomes/
```

Then rebuild demo homes through the Designer (re-creates `public/smarthomes/{DEMO-ID}/...`).

## Verification

1. **Lambda smoke test** (after Phase 1d). In the AWS Lambda console, invoke `dhcDesignStorageProxy-main` with this test event:
   ```json
   {
     "fieldName": "requestDesignReadUrl",
     "identity": { "username": "TEST_USER_SUB", "groups": [] },
     "arguments": { "smartHomeId": "DE-80331-MAR12-01", "fileName": "abox.json" }
   }
   ```
   Should return `Not authorized` (because TEST_USER_SUB isn't in any owners list).
2. **AppSync console test**. Sign in as a real Cognito user who created a SmartHome. Run:
   ```graphql
   mutation {
     requestDesignReadUrl(smartHomeId: "<real-home-id>", fileName: "abox.json") {
       url
       expiresAt
     }
   }
   ```
   Should return a signed S3 URL.
3. **Cross-tenant denial**. Sign in as User B (not in owners). Same mutation with User A's smartHomeId should return `Not authorized`.
4. **End-to-end browser test** (after Phase 2). User A and User B both in `SmartHome.owners`. Both can save and load designs. Edit lock (DDB) prevents concurrent writes; both can read.

## Open follow-ups

- **GSI on `smartHomeId`** — replace the Lambda's DDB scan with a Query against a GSI. Add `@index(name: "bySmartHomeId", queryField: "smartHomeDesignsBySmartHomeId")` to `SmartHomeDesign.smartHomeId`. Performance fix when the platform has > a few hundred designs.
- **Bucket policy override** (Phase 1e) — if circular dependency blocks the override path, write a one-off CDK construct or manual S3 bucket policy in the AWS Console.
- **Cache control on signed URLs** — set `ResponseCacheControl: "private, max-age=60"` on `GetObjectCommand` so the browser doesn't re-fetch within a session.
- **Audit logging** — log every `requestDesignReadUrl/WriteUrl` call to CloudWatch with userId, smartHomeId, fileName.
