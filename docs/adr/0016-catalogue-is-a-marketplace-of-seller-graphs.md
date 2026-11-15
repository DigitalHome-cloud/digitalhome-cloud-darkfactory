# ADR 0016: The device catalogue is a marketplace of seller graphs

Status: Accepted · 2026-11-15 · Supersedes the `DeviceModel` catalogue and the
`/edge/v1/catalogue` routes (core 17cccc2)

## Context

The device catalogue was one DynamoDB table, `DeviceModel`, written by
dhc-admins from the Portal and, for a few days, by pro edges through
`/edge/v1/catalogue[/put]`, row by row with "last write wins".

Two things did not fit:

1. **The catalogue has no SmartHome.** It is the same for every home and is
   really what manufacturers, distributors and wholesalers offer. A pro edge
   (an electrician's workstation) already keeps one catalogue per partner.
2. **Edges edit offline.** Row-by-row writes with no base version lose
   changes when the Portal and an edge change the same article. The
   Mediathek (template-dlab5-cloud ADR-0007) has already solved this for its
   knowledge graphs, and that mechanism was asked for here.

## Decision

1. **Sellers.** The catalogue is a digitalhome.cloud *marketplace* of
   sellers. A seller has an id (`^[a-z][a-z0-9-]{1,39}$`), a name, a kind
   (platform, manufacturer, distributor, wholesaler) and one catalogue graph.
   Its editors are the Cognito group `market-<id>`, and `adminMfaGate` lets
   that group into a token only with TOTP (`PROTECTED_GROUPS` takes a
   `market-*` prefix). dhc-admins create sellers and name their editors.
   The old curated catalogue becomes the seller `digitalhome-cloud`.
2. **One graph per seller, synced like the Mediathek.**
   - The Turtle is stored in S3 (`market/graphs/<seller>/v<n>-<token>.ttl`),
     and the `MarketSeller` row holds the version.
   - A save is two-step: a presigned PUT to staging, then a commit that
     validates and moves the version forward only by a conditional update. A
     stale base gets 409 with the current version.
   - Edges merge three-way, statement by statement, against the version they
     last agreed on. They reuse the edge template's `sync.merge`.
   - A single-valued fact with two values is a conflict the person settles.
3. **Vocabulary and shapes** are in `repos/core/schema/market/`.
   - Article IRIs are `https://digitalhome.cloud/id/market/<seller>/<ref>`.
     The ref is percent-encoded like Python's `quote(safe="")`.
   - The terms use the `dhp:` vocabulary that the pro edge already wrote.
   - The SHACL shapes are closed, so nothing outside the vocabulary passes.
4. **No prices.** No price property exists, so the closed shapes reject one.
   Prices stay private on each edge (from a partner's API or file).
5. **Files by hash.** Images and datasheets are stored at
   `public/market/<seller>/sha256/<hash>.<ext>`. They are uploaded through
   presigned PUTs bound to `x-amz-checksum-sha256` and `If-None-Match: *`, so
   they are write-once. Signed-in users and guests can read them.
6. **Who reads what.** Every signed-in user and every linked edge reads every
   seller. Only a seller's editors write its graph: from the Portal with
   TOTP, or from an edge whose linker is an editor (`mayEdit`, asked of
   Cognito per call).
7. **The Portal edits JSON, not Turtle.** This differs from the first plan,
   in which the browser parsed the graph with n3.
   - The `market` Lambda offers `marketArticles` (articles as JSON, with the
     parsed graph cached by S3 key).
   - It also offers `editMarketArticle(seller, reference, before, after)`.
     The Lambda merges the person's change (the difference between `before`
     and `after`) into the current graph at fact level, then saves through
     the same validated, versioned path.
   - This keeps an RDF library out of the Portal's bundle and its lockfile,
     and it keeps the merge rules in one place.
   - The edges keep the full graph protocol, because they edit offline.
8. **DeviceModel is retired.**
   - `importDeviceCatalogue` (dhc-admins, once per environment, re-runnable)
     turns the DeviceModel rows and their `public/catalogue/devices/...` files
     into the `digitalhome-cloud` graph.
   - `DeviceInstance.article` records the article IRI. `modelNumber` stays
     for display and for older rows.
   - After the import has run in an environment, the table, its codegen and
     its env-sync handling are removed.

## Consequences

- Routes: `/edge/v1/market/{sellers,graphs/get,graphs/put,uploads}`
  (DH-SPEC-100 §3.1) replace `/edge/v1/catalogue[/put]`.
- Pro edge: a partner subscribed to a seller has the same id, and its local
  catalogue is that seller's graph (digitalhome-pro-edge ADR-0006, which
  supersedes its ADR-0005).
- The same reference can be sold by two sellers. Views that only know a
  `modelNumber` cannot tell them apart; anything new keys on the article
  IRI.
- A seller with a large catalogue is one S3 object per version. That is
  fine at catalogue sizes (the limit is 20 MB of Turtle). Old versions stay
  in S3; no lifecycle rule removes them yet.
- Backend cycle: the approval Lambda in the data stack now finds the edge
  tables through SSM parameters and table-name patterns, not references
  (core 57579fd). Data must not reference edge.
