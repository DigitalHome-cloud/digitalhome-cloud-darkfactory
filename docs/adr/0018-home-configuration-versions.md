# ADR 0018: A home has one live configuration, planning options and legacy versions

Status: Accepted · 2026-11-16

## Context

The first real modernisation job is a T3 apartment with a 1986 fuse board.
It showed that a home has **one installation in service** and **one or more
plans** for it, and that the plan, once carried out, replaces the
installation. The pro edge keeps every edit of a design as a revision
(pro edge ADR-0009). That history does not say which configuration is in
service, which ones it replaced, or what is still only a plan. The cloud
knows none of this.

A home's identity is its SmartHome ID, `{country}-{zip}-{street}{number}-{nn}`
(ADR 0006). `createDigitalHome` computes it from the address, and it is the
key of `DigitalHome`, of the S3 paths, of the instance IRIs and of the edge's
link. Versions named after it would carry the address, and would break if
the address or the name were ever corrected.

## Decision

1. **A minted, meaningless home id.**
   - Every home gets a permanent `homeId`: `h-` plus ten characters, from an
     alphabet without `0`, `1`, `l`, `o` and `i`, drawn with
     `crypto.getRandomValues`. This follows the Mediathek's ADR-0003.
   - `createDigitalHome` mints it and `DigitalHome` carries it.
   - A home made before the id existed gets one the first time a function
     needs it. A conditional update sets it only once, so two functions that
     race agree on the same id. No separate backfill run is needed.
   - A home is found by its id with a filtered Scan, as `edgeHomes` already
     finds a person's homes. An index comes when the table is large enough
     to need one.
   - The SmartHome ID becomes a name: shown, searchable, and changeable
     later.
   - Everything new is keyed on `homeId`. That covers configuration
     versions, planning options, the vault (ADR 0019) and the edge routes
     for them.
   - Re-keying `DigitalHome` itself and moving the existing
     `tenant/{smartHomeId}/` and `DigitalHomes/{id}/` paths is a later
     migration.
   - Pages show names and version numbers. A full id appears only where
     someone must copy it.
2. **One live configuration per home.** The live A-Box is the configuration
   in service. A plain save never changes it. It moves in only two ways:
   - **Major:** a planning option is **promoted**. The version becomes
     `MMMM+1-0000`, and the configuration that was live becomes **legacy**.
   - **Minor:** components are **added**, for example devices found by
     discovery. The version becomes `MMMM-mmmm+1`, and the major stays live.
3. **Version ids.** A version is `<homeId>-<MMMM>-<mmmm>`, for example
   `h-7k2b9c4d3x-0001-0000`. Both numbers are running counters of four
   digits.
   - Every version is immutable and stays readable. Legacy means "no longer
     live", never "deleted".
   - **One exception, the withdrawal (amended 2026-11-16):** a live major
     whose content is the same as the version it replaced may be taken
     back. Its row and Turtle are removed, the version before it is live
     again, and the option it came from goes too. It is refused for any
     version that changed something, for a minor, for a version that is not
     live, and while a vault item is tagged with it. A promote that would
     change nothing is refused, so a withdrawal only repairs a promote made
     before that guard. The withdrawal is recorded on the home's HEAD row
     (`lastWithdrawn`), and a person confirms it.
   - A home's first live configuration is `-0001-0000`. It is made once, from
     a survey or a first design, and only while the home has no version.
4. **Planning options.** A home has zero or more options (`<homeId>-p01`,
   `-p02` …), each **based on** one version. They are edited freely: through
   the graph-store's save, and on an edge through its revisions.
   - **Promoting** an option requires it to be based on the current live
     major. Minors added since the option was taken are additions only, so
     they are merged into the option first, and that merge cannot conflict.
   - A promoted option is closed.
   - The other options stay open, based on what is now a legacy version.
     They are rebased before they can be promoted.
5. **What a minor may be.** Compared with the live graph:
   - nothing is removed;
   - every added statement is about a **new** node;
   - no new node is structural: a board, an RCD, a circuit, a protection
     device, a contactor, a surge protector, an unidentified device, or a
     space;
   - a new node may point to existing ones, for example a sensor in a room
     or on a circuit.
   Anything else is refused as "needs a planning option".
6. **Where.**
   - The live graph and the options are graph-store graphs (area
     `configurations`, one row per graph id, one S3 object per saved
     version).
   - `HomeConfigVersions` holds one row per configuration version (`homeId`,
     `version`): its kind, the graph version and S3 object it froze, what it
     was based on, the option it came from, live or legacy, who and when.
   - Promoting an option and making the first live configuration are both
     one DynamoDB transaction, conditioned on the version each writer read.
     The new row, the old row becoming legacy, and the live graph's version
     change together or not at all.
7. **Who.**
   - The home's owners (`DigitalHome.owners`) and `dhc-admins`, the same
     check as the design storage proxy.
   - A linked edge, with its device token, for its home. It reads,
     saves options and promotes for the pro edge, and adds minors for the
     devops edge.
   - A promote from an edge is a person's confirmed act: a button or a
     confirmed chat proposal, never an agent on its own.
8. **The identity A-Box stays.** `designtime/abox.ttl` is written once by
   `createDigitalHome`. The first live configuration starts from its home
   node, so the live A-Box is the whole home.
9. **An item's ID card, from a QR label.** (Amended 2026-11-16.) A QR
   code printed by an edge, on the board or as a small tag inside a
   socket's or a device's cover, opens
   `https://<portal>/id/?h=<homeId>&i=<item id>`.
   - It carries the minted homeId and item id only, never the SmartHome ID,
     which spells the address. Reading the code tells nothing about the home.
   - The card reads the graph with the owners' own queries
     (`homeConfigurations`, `homeConfigurationGraph`), so it shows nothing
     to anyone else; access rests on sign-in, not on the ids being secret.
   - It looks in the live version, then the open options ("planned"), then
     the legacy versions ("no longer live"), and says which.
   - Each label prints the address in small type, so a sticker put over it
     can be seen to point elsewhere; the card asks for nothing but the usual
     sign-in. It always says to switch off, secure and verify before work.
   - An edge prints no code for a workspace without a home on a linked
     connection: a link to the edge itself would not open on a phone.

## Consequences

- The T3's 1986 survey becomes its first live configuration, `-0001-0000`. The
  modernisation is option `p01`, based on it, and it is promoted only when
  the work is done.
- An edge's revisions stay its working history. The revision an edge pushed
  as a version is tagged on the edge with that version's id, frozen.
- The minor rule is strict on purpose. Correcting a rating read on site is
  a planning option, not a minor. If that proves too heavy, a later ADR can
  add a "correction" kind.
- Discovery from the devops edge needs its `cbox.jsonld` mapped to the
  design vocabulary before it can propose minors. That is its own piece of
  work.
