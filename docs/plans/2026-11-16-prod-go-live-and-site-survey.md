# Plan: production go-live and a phone survey for the site visit

**Date:** 2026-11-16 · **Status:** in progress (step 1)
**Builds on:** ADR 0018 (home configurations), ADR 0019 (home vault)

## Why

The first real job, an as-is survey and two planning options for a
modernisation, runs on stage. The site visit that finishes the survey should
run on production, with the pro edge's chat on the laptop and a phone for
photos and notes while walking through the house.

## Where production stands

- **Core:** the `main` branch was first deployed on 2026-11-15. It has its own
  Cognito pool and storage bucket, and is 35 commits behind `stage`. It has no
  configurations or vault yet.
- **Portal:** `main` is 47 commits behind `stage` and predates Gen 2: it has no
  `amplify_outputs.json`. `stage` commits the **stage** backend's outputs, so
  promoting it unchanged would point production at the stage backend.
- **Designer and Modeler:** production still points at the retired Gen 1
  backend. They are out of scope here.

## 1. Storage hardening (core, every branch)

The bucket (`dhcStorage`, one per environment) is currently created with
Amplify's sandbox defaults: `RemovalPolicy.DESTROY` plus an auto-delete
custom resource, no versioning, and CORS open to every origin. Its encryption
and public-access block are S3's defaults, not stated in code.

In `backend.ts`, the same for every branch so stage and prod are identical:

- **Retain:** `RemovalPolicy.RETAIN`, and the auto-delete custom resource
  removed. Removing the stack, or the branch, leaves the bucket and its files.
- **Versioning:** on, with a lifecycle rule that expires non-current versions
  after 90 days and aborts incomplete multipart uploads after 7.
- **Encryption:** SSE-S3 (S3-managed keys), stated, plus `enforceSSL`. No
  customer-managed KMS key: with it, a disabled or deleted key would make
  every file unreadable, and nothing asks for it yet.
- **Public access:** Block Public Access, all four settings on. Public reads
  of `public/*` go through the Cognito guest role, not a bucket policy, so
  they keep working.
- **Object ownership:** bucket owner enforced (no ACLs).
- **CORS:** only the platform's own origins (the three apps on stage and prod,
  `localhost:8000–8002` for development). It is not an access control, since
  every request needs a signed URL or Cognito credentials, but nothing else
  needs it.

**Sandboxes keep the old behaviour** (`AWS_BRANCH` unset): a personal sandbox
should clean up after itself.

**Verify on stage:** the synthesized template shows the settings; after the
deploy the stack's bucket resource has `DeletionPolicy: Retain`, and the
vault, the Portal pages and an edge upload still work.

Follow-ups, separate:
- `public/*` is writable and deletable by every signed-in user (only
  `public/market`, `public/weather` and `public/catalogue` are narrowed);
- `dhcDesignStorageProxy` may read and write every object in the bucket;
  narrow it to the design paths it serves;
- S3 server access logging, into a separate log bucket.

## 2. Production promotion

1. Core: promotion PR `stage` → `main`; the production backend gains the
   configurations, the vault and the hardened bucket.
2. Portal: each branch fetches its own backend's outputs in `preBuild`
   (`npx ampx generate outputs --branch <backend branch> --app-id <core app>`),
   instead of a committed file that names one backend. Then a promotion PR
   `stage` → `main`.
3. Accounts: production has a new, empty user pool. People sign up again; an
   administrator adds the `dhc-admins` group in the console.

## 3. A phone survey page (Portal) and its chat tool (pro edge)

The pro edge listens on the laptop only, by design, and the laptop is not
part of the house's network. So the phone works through the cloud, not
through the edge:

- **QR:** the workspace on the edge shows a code that opens the Portal's
  survey page for its home and option on the phone; the person signs in once.
- **Survey screen (as-is):** room (from the option's graph, or a new one),
  circuit (unidentified ones first), kind of point (socket, switch, light,
  appliance), a photo from the camera, a note (dictation works).
- **Saved as** a vault item under the option, with its room, circuit, kind
  and note; a note without a photo is allowed. The phone makes the
  thumbnail.
- **Backend:** as built, the subject is in vault tags (`survey`, `item:`,
  `kind:`, `room:`) and the note is the caption; a note alone is a small
  Markdown file. Blank QR tags, bound on site, are ADR 0018 point 10.
- **Starting from a label:** a QR label already opens an item's ID card
  (`/id/`, ADR 0018 point 9). The survey screen opens from the same card,
  with that item as its subject.
- **Pro edge chat:** a tool lists new observations; the chat proposes the
  changes they imply (a point on a circuit in a room, what a circuit feeds),
  and the person confirms each. The phone never changes a design.

## 4. Moving the first job to production

- The home is created in the production Portal (a new homeId).
- The pro edge is linked to production; both workspaces move there.
  **Edge fix needed:** moving a workspace to another connection must clear
  its cloud link (`dhp:homeId`, `dhp:option`, `dhp:basedOn`,
  `dhp:optionVersion`).
- The as-is baseline is published as the first live configuration, the two
  options are created again from their workspaces, and the vault files are
  uploaded from the edge. The stage copy stays as test data.

## 5. The site visit

With the phone page and the chat, on production.
