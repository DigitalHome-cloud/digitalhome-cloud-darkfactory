# ADR 0019: A home vault for photos and documents, grouped by configuration version

Status: Accepted · 2026-11-16

## Context

A survey arrives as photos and documents: the panel with its cover on and
off, the supplier's main breaker, the circuit list and the quote checklist.
The work that follows adds more: photos during the work, the certificate,
the single-line diagram. Until now these files stayed on the pro edge, in
the workspace's `files/` folder. Nobody else could see them, and nothing
said which configuration a photo shows.

The Mediathek (mediathek-digitalhome-shared) already keeps a family's photos
and documents safely. Its ADRs cover write-once originals by SHA-256
(0007), documents kept as their original only (0014), and albums that are
knowledge rather than folders (0018). A home's vault needs the same things
at a smaller scale.

## Decision

1. **Taken over from the Mediathek:**
   - **Originals are write-once, by fingerprint.** A file is stored once
     per home, at `tenant/{homeId}/vault/originals/sha256/<hash>.<ext>`. The
     presigned PUT carries `If-None-Match: *`, so nothing is overwritten.
   - **First a dry run, then upload.** The dry run says which fingerprints
     are new. A file over 5 GB (the single-PUT limit) is refused there.
   - **Derived files are made on the edge.** A photo's thumbnail goes to
     `tenant/{homeId}/vault/derived/<hash>/thumb.webp`.
   - **Documents and videos are kept as originals only.** They are
     downloaded with `Content-Disposition: attachment`, so an HTML or SVG
     file is never rendered in the platform's origin.
2. **Not taken over yet:**
   - the signed CloudFront CDN and video streaming. Reads are 5-minute
     presigned GETs from the vault Lambda;
   - private vaults within a home;
   - faces and similarity.
3. **Tagged with configuration versions** (amended 2026-11-16: tags, where
   there was one group).
   - Every item carries the configurations it documents as **tags**, one or
     several: versions `<homeId>-MMMM-mmmm` (ADR 0018), or planning options
     `<homeId>-p01` for photos taken while a plan is being worked on. A
     photo of a board unchanged between two versions documents both.
   - Tags are set on several items at once (a multiple selection), and the
     vault is filtered by them. A tag must be a version or option of the
     same home.
   - When an option is promoted, its tag is replaced by the new version's.
   - Older rows have one `configVersion`; it is read as their single tag
     and folded into the tags when they are next tagged.
   - This is metadata, not a folder: where a file came from is kept as its
     origin only.
4. **The catalogue.** `HomeVaultItems` holds one row per (`homeId`,
   `sha256`): kind (photo, document, video, other), name, size, when taken,
   caption, tags, and who uploaded it, when. The file is the
   source of truth for the content; the row is the source of truth for what
   the file is about.
5. **Who.**
   - The home's owners and `dhc-admins` read, upload and re-group, through
     AppSync.
   - A linked edge does the same for its home with its device token
     (`/edge/v1/vault/*`).
   - `tenant/` is granted to no Cognito role. Only the vault Lambda's role
     reads and writes it.
   - There is no delete in this version.

## Consequences

- The T3's survey package goes up under its first live configuration, and
  the pro edge keeps its local copy.
- Photos can show private details (people, papers, an address). They are
  only ever readable by the home's owners. That is why the vault is under
  `tenant/` and not `public/`.
- Streaming video, a CDN and private vaults are each a later ADR when
  needed.
