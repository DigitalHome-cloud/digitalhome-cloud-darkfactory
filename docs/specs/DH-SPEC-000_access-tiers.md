# DH-SPEC-000 — Access Tiers & Capability Matrix

| Field | Value |
|---|---|
| Spec ID | `DH-SPEC-000` |
| Title | Access Tiers & Capability Matrix |
| Status | **Draft** — awaiting review |
| Version | 0.2.0 |
| Author | D-LAB-5 / DigitalHome.Cloud |
| Date | 2026-04-16 |
| Scope | Cross-cutting. Defines the tiers, their Cognito group bindings, and the capability matrix referenced by all feature specs. |
| Referenced by | DH-SPEC-002 (SHM Create New) and all subsequent feature specs |

---

## 1. Purpose

Every feature spec needs to answer "who can do what". Duplicating that logic per spec leads to drift. This document is the **single source of truth** for:

1. The tier ladder.
2. The mapping from Cognito groups → tiers.
3. The capability matrix: for each (tier × feature), what is allowed.
4. The tier-gating contract that backend and frontend must follow.

Feature specs cite this document rather than redefining tier logic.

---

## 2. Tier ladder

| # | Tier | Cognito group | Status | Meaning |
|---|---|---|---|---|
| 0 | **Guest** | — (no auth) | live | Unauthenticated visitor. |
| 1 | **Welcome** | `dhc-welcome` | live (exists) | Signed-up but not upgraded. Free exploration tier. |
| 2 | **Standard** | `dhc-standard` | **to create** | Paid entry plan. Persistent DHs with bounded scope. |
| 3 | **Professional** | `dhc-professional` | **to create** | Paid advanced plan. Full scope. Details TBD. |

Ladder is monotonically increasing: each tier inherits the capabilities of the tier below unless explicitly restricted.

### Functional groups (orthogonal to tiers)

| Cognito group | Status | Purpose |
|---|---|---|
| `dhc-modelers` | live | Access to Modeler app — ontology viewing and T-Box editing |
| `dhc-admins` | live | Platform administration — Modeler editing, library management |

Functional groups grant app-level access and are independent of the tier ladder. A user can be `dhc-welcome` (tier) and `dhc-modelers` (functional) simultaneously.

**Group-to-tier resolution rule** (backend):
- If JWT contains `dhc-professional` → Professional.
- Else if `dhc-standard` → Standard.
- Else if `dhc-welcome` → Welcome.
- Else → Guest.
Higher group wins. A user in multiple groups resolves to the highest. New tiers inserted in the future keep this ordering convention.

---

## 3. Capability matrix

"Capability" = a single, atomic right the platform can grant or deny. The matrix is authoritative; any mismatch between code and matrix is a bug in the code.

Legend: ✅ allowed · ❌ denied · 🟡 allowed with constraint (footnote)

### 3.1 Platform-wide capabilities

| Capability | Guest | Welcome | Standard | Pro |
|---|:--:|:--:|:--:|:--:|
| Browse DEMO homes (read-only) | ✅ | ✅ | ✅ | ✅ |
| Toggle "show demo homes" | — | ✅ | ✅ | ✅ |
| See own DHs in SHM list/map | — | 🟡¹ | ✅ | ✅ |
| Persistent cloud save | ❌ | ❌ | ✅ | ✅ |
| Local save (browser IndexedDB) | ❌ | ✅ | ✅² | ✅² |
| Export DH as bundle (.zip) | ❌ | ✅ | ✅ | ✅ |
| Import DH bundle | ❌ | ✅ | ✅ | ✅ |
| "Upgrade & save to cloud" from imported local DH | — | ✅³ | ✅ | ✅ |

¹ Welcome tier has no cloud-persisted DHs. "Own DHs" for Welcome means locally-stored drafts only, listed from IndexedDB.
² Standard/Pro get cloud save by default; local save remains available for offline drafts.
³ The upgrade path requires the user to be — or become — Standard or Pro at the moment of save.

### 3.2 Create-new-DH capabilities

| Capability | Guest | Welcome | Standard | Pro |
|---|:--:|:--:|:--:|:--:|
| Access "Create New" button | ❌ | ✅ | ✅ | ✅ |
| Pick location on map (geocoded) | — | ✅ | ✅ | ✅ |
| Generate `smartHomeId` | — | ✅ (local) | ✅ (cloud) | ✅ (cloud) |
| Receive companion `RoleAssignment` (Owner) | — | ✅ (in bundle) | ✅ (in S3) | ✅ (in S3) |

### 3.3 Design-view capabilities

"Design views" are the ontology's `dhc:designView` annotation values. Each row maps to classes carrying that annotation.

| Design view | Guest (DEMO) | Welcome (local) | Standard | Pro |
|---|:--:|:--:|:--:|:--:|
| Spatial (Area, Floor, Space, Zone) | 👁 | ✅ | ✅ | ✅ |
| Building envelope (walls, windows, roof, insulation) | 👁 | ❌ | ❌⁴ | ✅ |
| Electrical (circuits, distribution, protection) | 👁 | ✅ | ✅ (generic only) | ✅ (generic + custom) |
| Plumbing | 👁 | ❌ | ❌⁴ | ✅ |
| Heating / HVAC | 👁 | ❌ | ❌⁴ | ✅ |
| Network (LAN, WiFi, ZigBee, etc.) | 👁 | ❌ | ❌⁴ | ✅ |
| Automation (Groups, Scenarios, Sensors, Actors) | 👁 | ❌ | ❌⁴ | ✅ |
| E-Mobility (EVs, charging stations) | 👁 | ❌ | ❌⁴ | ✅ |
| Governance (role assignments beyond Owner) | 👁 | ❌ | ❌⁴ | ✅ |

👁 = read-only view within DEMO homes.
⁴ Standard tier is intentionally limited to **spatial + electrical**. Attempting to edit other views surfaces the upgrade prompt.

### 3.4 Component capabilities

| Capability | Guest | Welcome | Standard | Pro |
|---|:--:|:--:|:--:|:--:|
| Place generic components (platform catalog) | 👁 | ✅ | ✅ | ✅ |
| Define custom components / equipment types | ❌ | ❌ | ❌ | ✅ |
| Import 3rd-party catalog | ❌ | ❌ | ❌ | ✅ |
| Attach ontology `Guideline`s to own content | 👁 | ❌ | ❌ | ✅ |

### 3.5 Collaboration & governance

| Capability | Guest | Welcome | Standard | Pro |
|---|:--:|:--:|:--:|:--:|
| Assign roles to other agents (Designer, Installer, …) | ❌ | ❌ | ❌ | ✅ |
| Share DH read-only link | ❌ | ❌ | ✅ | ✅ |
| Share DH for co-editing | ❌ | ❌ | ❌ | ✅ |
| Project-scoped work (`dhc:Project`) | ❌ | ❌ | ❌ | ✅ |

### 3.6 Quotas (indicative — ratify at launch)

| Quota | Welcome | Standard | Pro |
|---|:--:|:--:|:--:|
| Max DHs (local, for Welcome) | 1 | — | — |
| Max DHs (cloud) | — | 3 | unlimited |
| Max Spaces per DH | — | 25 | unlimited |
| Max Circuits per DH | — | 40 | unlimited |
| Bundle import size cap | 5 MB | 20 MB | 100 MB |

Quotas are enforced server-side at Standard+ and client-side for Welcome (best-effort, since Welcome never hits the backend for writes).

---

## 4. Tier-gating contract

The matrix is encoded once and consumed by both frontend and backend. The contract has three parts.

### 4.1 Capability registry (canonical JSON)

A single artefact `capabilities.json` is published alongside the ontology. Each entry:

```json
{
  "id": "create.new_home",
  "description": "Access the Create New Digital Home flow",
  "tiers": ["welcome", "standard", "professional"],
  "constraints": { "welcome": { "persistence": "local" } }
}
```

Feature specs reference capabilities by `id`. A PR that adds a feature must add (or reuse) entries in `capabilities.json`.

### 4.2 Backend enforcement

- API Gateway authorizer resolves Cognito groups → tier.
- Service layer calls `capabilities.can(tier, "capability.id", context)` → boolean.
- Denied calls return `403 Forbidden` with body `{ "error": "tier_insufficient", "required": "standard", "current": "welcome", "upgradeHint": "..." }`.

### 4.3 Frontend enforcement

- Same `capabilities.json` shipped to the client.
- UI elements for capabilities not granted: **hidden** for Guest, **visible but disabled with upgrade prompt** for Welcome/Standard attempting higher-tier actions.
- The upgrade prompt is a standardised component taking `{required, current}` and pointing to the billing / upgrade flow.

### 4.4 Source of truth

`capabilities.json` is generated from this document's §3 matrix. If the two disagree, this document wins and `capabilities.json` is regenerated.

---

## 5. Relationship to ontology

- **Tiers are not modelled in the ontology.** They are platform concerns, not domain concerns. A `RealEstate` A-BOX is the same whether it was created by a Welcome or a Pro user.
- **Two platform-level properties on `RealEstate`** (already proposed in DH-SPEC-002 §7) carry the relevant runtime flags: `dhc:isDemo` and `dhc:creationStatus`. No further ontology changes are required here.
- The Cognito group membership lives in the IdP, not in the A-BOX. `dhc:Person` retains `dhc:externalId` as the link; tier is resolved from the JWT at request time.

---

## 6. Open items

| # | Item | Blocker? |
|---|---|---|
| O-1 | Create `dhc-standard` and `dhc-professional` Cognito groups | Yes — blocks tier resolution |
| O-2 | Publish initial `capabilities.json` in the repo | Yes — blocks enforcement code |
| O-3 | Ratify §3.6 quotas at launch | No — can be tuned post-launch |
| O-4 | Billing / upgrade flow spec (DH-SPEC-00?) | No — out of scope here |
| O-5 | Decide whether "Building envelope" rises to Standard at some point | No |

---

*End of DH-SPEC-000 v0.2.0*
