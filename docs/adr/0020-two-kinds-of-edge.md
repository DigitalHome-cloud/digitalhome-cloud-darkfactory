# ADR 0020: Two kinds of edge — a pro edge serves a person's homes, a devops edge serves one home

Status: Accepted · 2026-11-17

## Context

An edge links to the cloud with the device flow (DH-SPEC-100). Its
registry row has one `home_id`, and the Portal's Fleet page nested every
edge under that one home, listing any edge without one as "unassigned —
assign each to one of your homes".

That fits the **devops edge**: a box in the home's cabinet, running
Node-RED for that home's devices. It does not fit the **pro edge**: an
electrician's or an owner's laptop that designs and surveys several homes,
one workspace per home. Its workspaces are attached to their homes on the
edge itself (pro edge ADR-0008), and the cloud already lets it reach every
home of the person who linked it (`configurations-shared/access.ts`:
the linked home, or any home whose owners include the linking person).
Linking a pro edge to one home in Fleet therefore changed nothing it could
reach, while Fleet asked for it and could not show which homes it works on.

## Decision

1. **An edge says what it is.** `edge_kind` is `pro` or `devops`. The edge
   sends it in `device_info` when it links and in its telemetry; the
   registry keeps it. An edge linked before it did is recognised by the
   tool name in `dhe_version` (`digitalhome-pro-edge …`); any other edge is
   a devops edge, the model Fleet always had.
2. **Access is unchanged.** An edge reaches the home it is linked to and
   every home of the person who linked it. Revoking the edge in Fleet cuts
   all of it at once. The kind only decides how the Portal shows the edge.
3. **A devops edge is dedicated to one home.** It is linked to it on the
   Portal's link page or in Fleet, and sits under that home.
4. **A pro edge is linked to no home.** The link page skips the home step
   for it. Its telemetry lists the homes its workspaces are attached to,
   as their minted `homeId`s only (ADR 0018) — never a SmartHome ID, a title
   or anything of a design. It reports at start, after a workspace is made
   or attached, and every six hours.
5. **The Portal names only the viewer's homes.** `listMyEdges` turns the
   reported homeIds into SmartHome IDs, keeping only the homes the viewer
   may use (owners, or dhc-admins). An edge can report any homeId; it
   cannot learn or show another person's home that way.
6. **Fleet shows the two kinds apart.** Devops edges as before. Pro edges
   in their own section, with the homes their workspaces use, and a line
   under each of those homes. A pro edge linked to a home before this ADR
   can be unlinked there; that takes nothing away from it.

## Consequences

- The registry gains `edge_kind`, `work_homes` (homeIds) and
  `work_homes_at`; `EdgeSummary` and `DeviceCodeInfo` gain the matching
  fields. `listMyEdges` reads the DigitalHome table (a Scan, a handful of
  rows) only when an edge reported homes.
- A pro edge's list is what it last reported: a workspace attached while
  the edge was offline shows after its next report.
- The Portal asks for the new fields and falls back to the older query
  while the backend has not deployed them, so the two can ship in either
  order.
- A third kind (a robot edge, the template's `robot`) would be added here,
  with its own rule for homes.
