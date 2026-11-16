# ADR 0017: Board templates are cloud content, one graph per norm edition

Status: Accepted · 2026-11-16

## Context

The pro edge's first feature is to create and modernise a distribution
board (*tableau principal*) against NF C 15-100. A new board starts from a
**template**: one dwelling case (T1 … T6, with or without electric heating)
under one norm edition, with its RCDs and circuits.

The first plan put the templates in `repos/core/schema/` beside the norm
shapes. That makes every corrected template a commit, a review and a backend
deploy. It also gives every instance the same templates, and nothing records
who checked one. Templates are content that people curate. They are not
rules about what a valid template is.

The marketplace (ADR 0016) already keeps curated content in the cloud. Each
graph is versioned, validated on save, and refused on a stale version.

## Decision

1. **The content is in the cloud, per instance.** Each norm edition has one
   Turtle graph of templates, with the graph id matching the edition
   (`nfc15100-2024` ↔ `dhc:NormEdition_NFC15100_2024`).
   - Storage: the `NormTemplates` table holds the version, and S3 holds
     `templates/graphs/<edition>/v<n>-<token>.ttl`.
   - Stage and prod each have their own templates. `scripts/templates.mjs
     copy` promotes them from stage to prod.
2. **The rules are in the repo.** `repos/core/schema/templates/` holds the
   `dht:` vocabulary and closed shapes. Templates reuse the T-Box terms
   `dhc:RCD`, `dhc:Circuit`, `dhc:ratedCurrent` and so on.
3. **A template must meet its own edition.** A save is checked against the
   template shapes and the edition's effective norm shapes: the edition's
   own `dhc:shapesFile` plus every file down `dhc:supersedes`. These are the
   same shapes a design is checked against. A template that breaks its
   edition is refused. Only editions with shapes can hold templates.
4. **Verification is a person's act.**
   - `dht:verified`, `dht:checkedBy` and `dht:checkedAt` are never taken
     from an upload.
   - `verifyTemplate` sets them, with the signed-in caller's e-mail address
     and the time.
   - Any change to a template's content makes it unverified again.
   - Copying to another instance keeps a template's verification only if that
     instance holds the same content, verified.
5. **Who.**
   - Read: every signed-in user, through AppSync `templateEditions` and
     `templateGraph`; and every linked edge, through `POST
     /edge/v1/templates/editions` and `/get`.
   - Write and verify: the new Cognito group `dhc-template-editors` and
     `dhc-admins`, with an authenticator app (`adminMfaGate` protects the
     group).
   - Edges never write templates.
6. **One store for versioned graphs.** `amplify/functions/graph-store/` holds
   the code that was in the marketplace's store: the conditional version
   update, one object per version, and the two-step save. The marketplace
   and the templates both use it.

## Consequences

- A template is corrected without a commit or a deploy. Each instance shows
  who checked what, and when.
- The first drafts, T1 to T5 with and without electric heating for NF C
  15-100:2024, are **unverified**. The 2024 norm shapes they are checked
  against are themselves illustrative (core CLAUDE.md). The drafts are a seed,
  `repos/core/schema/templates/seed/`, written to stage once. From then on the
  cloud holds the real copy.
- Changing a norm shapes file or the T-Box now also means running
  `node scripts/sync-template-shapes.mjs`. The template validator carries a
  copy, and a test fails when that copy drifts.
- The template validator gives the norm shapes decimals in their shortest
  form. The EV-charging (IRVE) guards compare `"32"^^xsd:decimal` as a term,
  so a template written with `32.0` was not checked at all. The same trap
  applies to designs that write `32.0`. Recorded in core CLAUDE.md.
- A Portal editor is still to come, beside the Marketplace. Until then,
  `scripts/templates.mjs` covers listing, reading, saving, verifying and
  promoting templates.
