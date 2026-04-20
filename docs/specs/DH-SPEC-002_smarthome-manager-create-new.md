# DH-SPEC-002 — SmartHome Manager: Create New Digital Home (Real Estate step)

| Field | Value |
|---|---|
| Spec ID | `DH-SPEC-002` |
| Title | SmartHome Manager — Create New Digital Home (Real Estate step) |
| Status | **Draft** — awaiting review |
| Version | **0.2.0** — tier model integrated |
| Author | D-LAB-5 / DigitalHome.Cloud |
| Date | 2026-04-16 |
| Related ontology | `dhc-core` v1.1.0 → proposed bump to **v1.2.0** (see §7) |
| Related specs | **DH-SPEC-000 Access Tiers & Capability Matrix** (required prerequisite); DH-SPEC-003 Define Spaces (downstream, not in this spec) |
| Scope | Entry flow only — up to a persisted `RealEstate` A-BOX. Space definition is the next step and out of scope. |

### Changelog
- **0.2.0** — Replaced simple auth/ownership state matrix with tier-based matrix bound to Cognito groups (DH-SPEC-000). Added Welcome-tier local flow (IndexedDB + export bundle). Added bundle format, re-import flow, upgrade-to-cloud path. Reworked S3 / IAM.
- **0.1.0** — Initial draft (superseded).

---

## 1. Overview & goals

Enable the creation of a new Digital Home (DH) from the SmartHome Manager by picking the real estate location on a map. The flow must serve three distinct audiences defined in **DH-SPEC-000**:

- **Guests** browse DEMO homes only.
- **Welcome** users (`dhc-welcome`) can run the full Create-New flow locally, explore, and export a bundle — **no cloud persistence**.
- **Standard** users (`dhc-standard`) can create persistent DHs within the Standard capability envelope (spatial + electrical, generic components only).
- **Professional** users (`dhc-professional`) get the same creation flow with broader downstream scope.

All tiers produce A-BOX data conformant to the same ontology (§7). The only difference is **where it is stored** and **what can be added to it after creation** (governed by DH-SPEC-000 §3).

**Primary goals**
- Eliminate address typos by sourcing the address from a map provider (authoritative geocoded result).
- Produce a canonical `smartHomeId` (§8): human-readable, collision-safe, identical algorithm across tiers.
- Provide a dual-pane SmartHome Manager (list + map) adapting to tier.
- Let Welcome users experience the full creation flow without requiring cloud allocation.
- Generate an A-BOX + S3 skeleton (Standard+) or a downloadable bundle (Welcome) ready for Define Spaces.

**Non-goals**
- Authentication / signup / billing / upgrade UX (assumed: Cognito + existing billing flow).
- Defining Areas, Floors, Spaces, Zones — see DH-SPEC-003.
- Tier matrix itself — see DH-SPEC-000.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| DH | Digital Home — the digital twin of a real estate property. |
| T-BOX | Terminology box — the ontology schema. Files: `dhc-core_schema.ttl`, `dhc-roles.ttl`. |
| A-BOX | Assertion box — instance data, serialized as JSON-LD against `context.jsonld`. |
| SHM | SmartHome Manager — the landing UI for listing and creating DHs. |
| `smartHomeId` | Tenant partition key, format defined in §8. |
| DEMO home | Sample DH owned by the platform, `dhc:isDemo = true`, read-only. |
| Bundle | `.zip` artefact representing a DH outside the cloud (§9.4). |
| Tier | One of Guest / Welcome / Standard / Professional — see DH-SPEC-000. |

---

## 3. User stories

| ID | As a … | I want to … | So that … |
|---|---|---|---|
| US-01 | Guest | browse demo DHs on map + list, read-only | I can evaluate the product before signing up |
| US-02 | Welcome user | create a DH locally using the full map-pick flow | I can try the experience end-to-end before paying |
| US-03 | Welcome user | export my in-progress DH as a bundle | I don't lose work when switching browsers/devices |
| US-04 | Welcome user | re-import a previously exported bundle | I can continue working where I left off |
| US-05 | Welcome user | one-click "upgrade & save to cloud" | my local work becomes a real cloud DH the moment I upgrade |
| US-06 | Standard user | create a DH by picking location on a map with cloud save | I have a correct, persistent DH to design against |
| US-07 | Standard user with ≥1 DH | see only my homes by default, with toggle to include demos | I'm not distracted by demos once I'm productive |
| US-08 | Any authenticated user | resume a `draft` creation | I can abandon and come back without losing entry data |

---

## 4. Tier state matrix

The SHM behaviour is fully determined by the user's **tier** (DH-SPEC-000 §2). The legacy "auth state + owned count" model is replaced.

| Tier | Default demo toggle | List shows | Map shows | "Create New" | Save path |
|---|---|---|---|---|---|
| Guest | ON (forced) | Demo homes | Demo homes | Hidden (CTA: "Sign up to try") | — |
| Welcome (0 local DHs) | ON (forced) | Demo homes + empty-state banner | Demo homes | Visible | **Local only** (IndexedDB + export bundle) |
| Welcome (≥1 local DH) | OFF (default, toggleable) | Local DHs from IndexedDB (badge "LOCAL") | Local DHs | Visible | Local only |
| Standard, 0 cloud DHs | ON (default) | Demo homes + empty-state banner | Demo homes | Visible, prominent | Cloud (S3) |
| Standard/Pro, ≥1 cloud DH | OFF (default, toggleable) | Owned cloud DHs | Owned cloud DHs | Visible | Cloud (S3) |
| Standard/Pro, toggle ON | ON | Owned + Demo (demos visually differentiated) | Owned + Demo | Visible | Cloud (S3) |

**Demo differentiation when mixed**: demo DHs show a "DEMO" badge and muted map marker; not editable.
**Local differentiation for Welcome**: local DHs show a "LOCAL" badge and a warning icon ("not saved to cloud").
**Upgrade prompt**: Welcome user opening a local DH sees a persistent "Upgrade to save to cloud" button (§11.3).

**"Ownership"** at Standard+ is resolved via the SPARQL contract in §7.3. At Welcome, "ownership" is implicit — the DH is on this browser's IndexedDB.

---

## 5. UI / UX

### 5.1 Layout (all tiers)

Two stacked regions — identical structural layout across tiers, content varies per §4.

```
┌─────────────────────────────────────────────────────────┐
│  SmartHome Manager                  [+ Create New]*     │
│  ┌─ Toggle: [ ] Show demo homes (per-tier rules) ──────┐│
│                                                          │
│  UPPER — LIST                                            │
│  ┌────────────┬──────────────┬─────────────┬─────────┐  │
│  │ smartHomeId│ name         │ city, ctry  │ badge   │  │
│  │ DE-80331…  │ Haus Marien… │ München, DE │ LOCAL   │  │
│  │ FR-75011…  │ DEMO Paris   │ Paris, FR   │ DEMO    │  │
│  └────────────┴──────────────┴─────────────┴─────────┘  │
│                                                          │
│  LOWER — MAP                                             │
│  ┌───────────────────────────────────────────────┐      │
│  │  ◉  ◉                          ◉              │      │
│  │        ◉       (markers synced with list)     │      │
│  └───────────────────────────────────────────────┘      │
│                                                          │
│  Welcome tier only: [ Import bundle (.zip) ]             │
└─────────────────────────────────────────────────────────┘

* Button visibility per tier (§4).
```

**Synchronization rules**
- Selecting a list row pans/zooms the map to the corresponding marker.
- Clicking a marker highlights the list row.
- Filters (search, demo toggle) apply to both panes simultaneously.

### 5.2 Create-New — step 1: location picker (Standard / Pro, cloud path)

1. User clicks **+ Create New** → wizard opens at Step 1/N.
2. Map-backed search, centered on browser geolocation → last country → `lat=50.85, lng=4.35` (Brussels) default.
3. User can type an address (autocomplete), click the map, or drag the pin — reverse geocoding updates the address card.
4. Resolved address card displays authoritative fields (read-only). Editable: `name` (defaults to street+number), `preferredLanguage` (defaults to browser lang, filtered to en/de/fr).
5. **Confirm location** → backend:
   - Computes `smartHomeId` (§8)
   - Creates A-BOX (§9.1) + RoleAssignment (§9.2)
   - Provisions S3 skeleton (§10.1)
   - Writes `manifest.json`
   - Returns `201 { smartHomeId, nextStep: "spaces" }`
6. UI transitions to DH-SPEC-003 (Define Spaces).

### 5.3 Create-New — Welcome tier (local path)

Same map picker, same UX, different persistence.

1. User clicks **+ Create New** → wizard opens.
2. Map-pick flow identical to §5.2 steps 2–4.
3. **Confirm location** → **client-side**:
   - Client computes `smartHomeId` using the same algorithm (§8). No backend call.
   - Client constructs A-BOX (§9.1) + RoleAssignment (§9.2) — `createdBy` = `urn:agent:cognito:sub:{sub}`, `creationStatus = "draft"`, `isDemo = false`.
   - Writes to IndexedDB under object store `dh-local` (§10.4).
   - Auto-save triggers on every field change after this point.
4. UI transitions to DH-SPEC-003 (Define Spaces), running in local mode.
5. A persistent banner: **"This DH lives in your browser only. [Export bundle] [Upgrade to save to cloud]."**

### 5.4 Re-import (Welcome tier)

1. User clicks **Import bundle (.zip)** on the SHM.
2. File picker → user selects a `.zip` produced earlier (§9.4).
3. Client validates:
   - `manifest.json` present, `aboxVersion >= 1.2.0`
   - `realestate.jsonld` present and parses against context
   - `smartHomeId` matches `realestate.jsonld.smartHomeId` and recomputes correctly from the address fields
4. On conflict with an existing local DH of the same `smartHomeId`: prompt "Replace", "Keep both (auto-suffix `-nn`)", "Cancel".
5. On success: DH appears in SHM with "LOCAL" badge.

### 5.5 Error / edge cases

| Case | Behaviour |
|---|---|
| Guest clicks a DEMO home | Read-only viewer; no Create New. |
| Welcome user exceeds local quota (DH-SPEC-000 §3.6) | Block creation; prompt to export/delete or upgrade. |
| Provider fails / offline | Fallback to manual address form; `geocodeVerified=false`. |
| Address outside supported countries | Create anyway with `geoCoverage="unsupported"` flag. |
| `smartHomeId` collision (Standard/Pro) | Server increments `-nn` until unique within tenant. |
| `smartHomeId` collision (Welcome, local IndexedDB) | Client increments `-nn` within IndexedDB scope. |
| Duplicate at same address (user-owned) | Warn before creation; allow override. |
| User abandons wizard post step-1 | A-BOX persisted with `creationStatus="draft"`. "Resume" prompt on next session. |
| Welcome user clears browser storage | Local DHs lost; an exported bundle is the only recovery. Warning surfaced in SHM. |

---

## 6. Map provider comparison

Both providers deliver autocomplete, tiles, reverse geocoding, place ID. Choice drives cost, AWS integration depth, data residency.

| Criterion | **Google Maps Platform** | **AWS Amplify Geo / Amazon Location** |
|---|---|---|
| Map tiles | Google proprietary — high quality | Esri / HERE (configurable) |
| Autocomplete | Places Autocomplete — benchmark | Amazon Location Places — solid, uneven in some regions |
| Reverse geocoding | Excellent | Good (HERE better than Esri for EU) |
| Place ID | Google `place_id` — widely portable | Amazon Location `PlaceId` — provider-scoped |
| Pricing | Pay-per-request, free credit | Pay-per-request, typically lower |
| AWS integration | External API, separate billing | Native IAM, Amplify SDK, consolidated billing |
| Data residency (EU) | Routed globally | Pinnable to `eu-central-1` |
| Multilingual (de/fr/en) | Excellent | Backend-dependent |

**Recommendation: Amazon Location as primary, Google as selectable fallback.**
- DH platform is AWS-native → consolidation, IAM, billing.
- EU data residency: addresses are PII.
- `dhc:placeId` + `dhc:placeIdProvider` pair prevents vendor lock-in.
- Per-tenant override to Google where autocomplete underperforms.

**Provider abstraction contract** (backend-side):

```
interface GeoProvider {
  autocomplete(query, biasCenter?, lang) -> Suggestion[]
  geocode(placeId) -> ResolvedAddress
  reverseGeocode(lat, lng, lang) -> ResolvedAddress
}
type ResolvedAddress = {
  country, postalCode, streetName, streetNumber, locality, adminRegion,
  latitude, longitude, formattedAddress, placeId, placeIdProvider
}
```

**Welcome-tier note.** Client-side `smartHomeId` computation still requires a provider call for autocomplete/reverse geocoding. Welcome users hit the geo provider through the same backend proxy (to keep API keys server-side and allow rate limiting per tier).

---

## 7. Ontology impact — proposed v1.2.0 delta

The current T-BOX (v1.1.0) has no geographic or postal-address properties on `dhc:RealEstate`, and no DH-level lifecycle/flag properties. Additions below are non-breaking.

### 7.1 New datatype properties on `dhc:RealEstate`

```turtle
# Postal address (from map provider)
dhc:country           a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "ISO 3166-1 alpha-2 country code."@en ; dhc:designView "spatial" .
dhc:postalCode        a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  dhc:designView "spatial" .
dhc:streetName        a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  dhc:designView "spatial" .
dhc:streetNumber      a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "String to accommodate '12a', '12-14', etc."@en ; dhc:designView "spatial" .
dhc:locality          a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "City / town."@en ; dhc:designView "spatial" .
dhc:adminRegion       a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "State, canton, Land, région."@en ; dhc:designView "spatial" .
dhc:formattedAddress  a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "Provider-canonical single-line address for display."@en ; dhc:designView "spatial" .

# Geocoordinates (WGS84)
dhc:latitude          a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:decimal ;
  dhc:designView "spatial" .
dhc:longitude         a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:decimal ;
  dhc:designView "spatial" .

# Provider-scoped external reference
dhc:placeId           a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "Map provider's stable place identifier."@en ; dhc:designView "spatial" .
dhc:placeIdProvider   a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "Provider: 'google' | 'amazon-location' | 'manual'."@en ; dhc:designView "spatial" .
dhc:geocodeVerified   a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:boolean ;
  rdfs:comment "True if lat/lng come from a provider geocode call."@en ; dhc:designView "spatial" .
```

### 7.2 Lifecycle / flag properties on `dhc:RealEstate`

```turtle
dhc:isDemo            a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:boolean .
dhc:creationStatus    a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "One of: draft | active | archived."@en .
dhc:createdAt         a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:dateTime .
dhc:updatedAt         a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:dateTime .
dhc:createdBy         a owl:ObjectProperty ;  rdfs:domain dhc:RealEstate ; rdfs:range dhc:Agent .
dhc:preferredLanguage a owl:DatatypeProperty ; rdfs:domain dhc:RealEstate ; rdfs:range xsd:string ;
  rdfs:comment "BCP-47 tag: 'en', 'de', 'fr'."@en .
```

### 7.3 Ownership query contract (Standard/Pro only)

A DH is owned by the current user iff:
- `?user dhc:owns <realEstate>` exists, **OR**
- `dhc:RoleAssignment` with `assignedAgent = ?user`, `assignmentContext = <realEstate>`, `assignedRole ∈ { Role_Owner, Role_MaitreOuvrage }`, `assignmentStatus = "active"`.

Welcome tier does not execute SPARQL — list comes from IndexedDB directly.

### 7.4 Context file delta (`context.jsonld` v1.2.0)

```json
"country":           "dhc:country",
"postalCode":        "dhc:postalCode",
"streetName":        "dhc:streetName",
"streetNumber":      "dhc:streetNumber",
"locality":          "dhc:locality",
"adminRegion":       "dhc:adminRegion",
"formattedAddress":  "dhc:formattedAddress",
"latitude":          { "@id": "dhc:latitude",  "@type": "xsd:decimal" },
"longitude":         { "@id": "dhc:longitude", "@type": "xsd:decimal" },
"placeId":           "dhc:placeId",
"placeIdProvider":   "dhc:placeIdProvider",
"geocodeVerified":   { "@id": "dhc:geocodeVerified", "@type": "xsd:boolean" },
"isDemo":            { "@id": "dhc:isDemo",          "@type": "xsd:boolean" },
"creationStatus":    "dhc:creationStatus",
"createdAt":         { "@id": "dhc:createdAt", "@type": "xsd:dateTime" },
"updatedAt":         { "@id": "dhc:updatedAt", "@type": "xsd:dateTime" },
"createdBy":         { "@id": "dhc:createdBy", "@type": "@id" },
"preferredLanguage": "dhc:preferredLanguage"
```

### 7.5 Version bump

- `dhc-core_schema.ttl` → `owl:versionInfo "1.2.0"`
- `context.jsonld` published at `/context/v1.2.0/context.jsonld`
- All additions are optional → **backward compatible**.

---

## 8. `smartHomeId` generation

Canonical format from T-BOX: `{country}-{zip}-{street3}{number}-{nn}` — e.g. `DE-80331-MAR12-01`.

**Same algorithm executes client-side (Welcome) and server-side (Standard/Pro).** A shared library (`@dhc/smarthome-id`) is the single implementation, consumed by both runtimes.

### 8.1 Computation rules

| Token | Source | Rule |
|---|---|---|
| `{country}` | `dhc:country` | ISO 3166-1 alpha-2, upper-case. |
| `{zip}` | `dhc:postalCode` | Alphanumeric, strip spaces, upper-case. Transliterate non-Latin (ICU). Truncate to 10 chars. |
| `{street3}` | `dhc:streetName` | First 3 ASCII letters of the first significant word (strip leading articles: "Rue", "Av.", "La", "Der", "Die", "Das", "Straße" suffix). Upper-case. Transliterate non-Latin. |
| `{number}` | `dhc:streetNumber` | Numeric part only (strip letter suffixes for token; full value retained in property). |
| `{nn}` | collision counter | Start `01`, increment per collision **in scope**. Scope = tenant (Standard/Pro) or IndexedDB (Welcome). |

### 8.2 Deterministic examples

| Address | `smartHomeId` |
|---|---|
| Marienplatz 12, 80331 München, DE | `DE-80331-MAR12-01` |
| 15 Rue de la Paix, 75002 Paris, FR | `FR-75002-PAI15-01` |
| Bahnhofstrasse 1, 8001 Zürich, CH | `CH-8001-BAH1-01` |
| Rue Neuve 12a, 1000 Brussels, BE | `BE-1000-NEU12-01` (letter suffix dropped from token, retained in `streetNumber`) |

### 8.3 Collision handling

Within scope (tenant or local IndexedDB), existing ID → `-nn` increments until free. Across tenants, IDs may repeat — physical uniqueness guaranteed by S3 prefix (§10.3) or origin browser.

### 8.4 Immutability

Immutable once `creationStatus: draft → active`. Prior to activation, address corrections recompute the ID. After activation, correction creates a new DH and archives the old one.

**Upgrade path note (§11.3):** when a Welcome local DH is promoted to cloud, its `smartHomeId` may collide with an existing Standard/Pro tenant ID. If so, the upgrade reassigns `-nn` before cloud write. The original local ID is preserved in `dhc:description` as a migration trace.

---

## 9. A-BOX generation

Identical shape regardless of tier.

### 9.1 Minimal A-BOX (JSON-LD)

```json
{
  "@context": "https://digitalhome.cloud/context/v1.2.0/context.jsonld",
  "@id": "urn:dh:DE-80331-MAR12-01",
  "@type": "RealEstate",
  "smartHomeId": "DE-80331-MAR12-01",
  "name": "Marienplatz 12",
  "preferredLanguage": "de",

  "country": "DE",
  "postalCode": "80331",
  "streetName": "Marienplatz",
  "streetNumber": "12",
  "locality": "München",
  "adminRegion": "Bayern",
  "formattedAddress": "Marienplatz 12, 80331 München, Germany",
  "latitude": 48.1374,
  "longitude": 11.5755,
  "placeId": "ChIJxxx...",
  "placeIdProvider": "amazon-location",
  "geocodeVerified": true,

  "isDemo": false,
  "creationStatus": "draft",
  "createdAt": "2026-04-16T10:23:11Z",
  "updatedAt": "2026-04-16T10:23:11Z",
  "createdBy": { "@id": "urn:agent:cognito:sub:abc-123" }
}
```

### 9.2 Companion RoleAssignment

```json
{
  "@context": "https://digitalhome.cloud/context/v1.2.0/context.jsonld",
  "@id": "urn:dh:DE-80331-MAR12-01:roleassign:owner:01",
  "@type": "dhc:RoleAssignment",
  "assignedAgent":   { "@id": "urn:agent:cognito:sub:abc-123" },
  "assignedRole":    { "@id": "dhc:Role_Owner" },
  "assignmentContext": { "@id": "urn:dh:DE-80331-MAR12-01" },
  "assignmentStatus": "active",
  "validFrom": "2026-04-16T10:23:11Z"
}
```

### 9.3 URI scheme

| Entity | URI pattern |
|---|---|
| RealEstate | `urn:dh:{smartHomeId}` |
| RoleAssignment | `urn:dh:{smartHomeId}:roleassign:{roleSlug}:{nn}` |
| Agent (Person) | `urn:agent:cognito:sub:{cognitoSub}` |
| Area / Space (downstream) | `urn:dh:{smartHomeId}:area:{slug}` |

### 9.4 Export bundle format (Welcome tier + backup)

A **`.zip`** file with a canonical internal layout — matches the S3 structure so re-import and upgrade-to-cloud are a straight copy.

```
{smartHomeId}.dh.zip
├── bundle.json                      # bundle-level metadata (see below)
├── abox/
│   ├── realestate.jsonld
│   ├── roleassignments/
│   │   └── owner-01.jsonld
│   ├── areas/            (empty .gitkeep)
│   ├── spaces/           (empty .gitkeep)
│   └── equipment/        (empty .gitkeep)
├── plans/                (empty .gitkeep)
├── documents/            (empty .gitkeep)
├── exports/              (empty .gitkeep)
├── manifest.json                     # §10.2
└── context/
    └── context.jsonld                # embedded for offline re-import
```

`bundle.json`:

```json
{
  "bundleFormat": "dhc-bundle/1",
  "smartHomeId": "DE-80331-MAR12-01",
  "aboxVersion": "1.2.0",
  "exportedAt": "2026-04-16T11:02:00Z",
  "exportedByTier": "welcome",
  "checksum": "sha256:..."
}
```

**Rationale for full skeleton + context embed:**
- Import and cloud-upgrade become `unzip → copy to S3 prefix`.
- Bundle is self-contained for offline opening / archiving.
- Checksum enables integrity check on re-import.

---

## 10. Storage

### 10.1 S3 structure (Standard / Pro)

```
s3://dhc-{env}/
├── tenants/
│   └── {ownerCognitoSub}/
│       └── homes/
│           └── {smartHomeId}/
│               ├── abox/
│               │   ├── realestate.jsonld
│               │   ├── roleassignments/owner-01.jsonld
│               │   ├── areas/     (DH-SPEC-003)
│               │   ├── spaces/    (DH-SPEC-003)
│               │   └── equipment/
│               ├── plans/
│               ├── documents/
│               ├── exports/
│               └── manifest.json
└── demo/
    └── homes/
        └── {smartHomeId}/...
```

### 10.2 `manifest.json` (all tiers — same shape)

Small sidecar powering SHM list pane. Stored in S3 (Standard/Pro), in IndexedDB (Welcome), and inside the bundle (export).

```json
{
  "smartHomeId": "DE-80331-MAR12-01",
  "name": "Marienplatz 12",
  "locality": "München",
  "country": "DE",
  "latitude": 48.1374,
  "longitude": 11.5755,
  "isDemo": false,
  "creationStatus": "draft",
  "tier": "standard",
  "storage": "cloud",
  "createdAt": "2026-04-16T10:23:11Z",
  "updatedAt": "2026-04-16T10:23:11Z",
  "ownerSub": "abc-123",
  "aboxVersion": "1.2.0"
}
```

Added fields vs v0.1.0: `tier`, `storage ∈ { cloud | local | bundle }`.

### 10.3 IAM boundaries (Standard / Pro)

| Principal | `tenants/{sub}/...` | `demo/...` |
|---|---|---|
| Owner user | R/W own `{sub}` only | Read-only |
| Welcome user | — (no S3 access) | Read-only |
| Guest | — | Read-only (via CloudFront signed URLs or public read) |
| Platform service role | Full | Full |

### 10.4 IndexedDB layout (Welcome)

Client-side store powering local-only creation.

**Database**: `dhc-local`
**Version**: `1`

| Object store | Key | Value |
|---|---|---|
| `manifests` | `smartHomeId` | §10.2 `manifest.json` (with `storage: "local"`) |
| `aboxes` | `urn` (full `@id`) | JSON-LD object (RealEstate, RoleAssignment, …) |
| `bundles-cache` | `smartHomeId` | optional, last-exported bundle metadata for quick re-export |
| `settings` | key | user prefs (demo toggle state, last language, etc.) |

**Auto-save triggers**: every form change in the wizard commits to `aboxes` + updates `manifests.updatedAt`. Debounced 500ms.

**Quota awareness**: before any write, check `navigator.storage.estimate()`. If <10MB remaining, warn user and suggest export.

**Clear / wipe recovery**: if `dhc-local` is gone but the user has a bundle, §5.4 re-import restores everything.

### 10.5 SHM listing strategy

- Standard/Pro: `ListObjectsV2` on `tenants/{sub}/homes/` → load `manifest.json` objects only. For scale >1k DHs/owner, mirror to DynamoDB (out of scope — §13).
- Welcome: scan `manifests` object store in IndexedDB.
- Demo overlay: `ListObjectsV2` on `demo/homes/` when toggle ON (or backed by public CDN in practice).

---

## 11. End-to-end flow (sequences)

### 11.1 Standard / Pro — cloud creation

```
User → SHM UI:       click "+ Create New"
UI   → UI:           open wizard step 1 (map picker)
User → UI:           search / click / drag pin
UI   → GeoProxy:     autocomplete / reverseGeocode
GeoProxy → Amazon Location:  provider call
Amazon Location → GeoProxy → UI:  ResolvedAddress
User → UI:           confirm location
UI   → API:          POST /homes { ResolvedAddress, name, lang }
API  → Capabilities: can(tier, "create.new_home")  → true (Standard)
API  → IDSvc:        computeSmartHomeId(addr, ownerSub)  → "DE-80331-MAR12-01"
API  → S3:           PUT tenants/{sub}/homes/{id}/abox/realestate.jsonld
API  → S3:           PUT tenants/{sub}/homes/{id}/abox/roleassignments/owner-01.jsonld
API  → S3:           PUT tenants/{sub}/homes/{id}/manifest.json
API  → UI:           201 { smartHomeId, nextStep: "spaces" }
UI   → UI:           transition to DH-SPEC-003
```

### 11.2 Welcome — local creation

```
User → SHM UI:       click "+ Create New"
UI   → Capabilities: can(tier, "create.new_home")  → true (local)
UI   → UI:           open wizard step 1 (map picker)
User → UI:           search / click / drag pin
UI   → GeoProxy:     autocomplete / reverseGeocode  (rate-limited per tier)
GeoProxy → Amazon Location → UI:  ResolvedAddress
User → UI:           confirm location
UI   → @dhc/smarthome-id:   computeSmartHomeId(addr, scope=IndexedDB)  → "DE-80331-MAR12-01"
UI   → IndexedDB:    put manifests[id], aboxes[urn:dh:id], aboxes[urn:...:owner:01]
UI   → UI:           show "Local DH" banner; transition to DH-SPEC-003 (local mode)
User → UI:           click "Export bundle"
UI   → UI:           build .zip per §9.4, trigger browser download
```

### 11.3 Welcome → Standard/Pro upgrade & save to cloud

Assumes user has just upgraded their tier (billing flow completed, Cognito group updated, new JWT issued).

```
User → SHM UI:       click "Upgrade & save to cloud" on a local DH
UI   → API:          POST /homes/upgrade { bundle | smartHomeId+local-payload }
API  → Capabilities: can(tier, "create.new_home") → true (Standard/Pro)
API  → IDSvc:        checkCollision(smartHomeId, ownerSub)
                     → if collision: reassign -nn, record previous in dhc:description
API  → S3:           copy bundle contents to tenants/{sub}/homes/{newId}/
API  → S3:           write manifest.json with storage="cloud", tier=<new>
API  → UI:           201 { smartHomeId, nextStep: "spaces" }
UI   → IndexedDB:    mark local manifest as migrated (or delete per user pref)
UI   → UI:           transition to cloud-mode designer
```

---

## 12. Outcome — exit criteria

### 12.1 Standard / Pro (cloud)
- ✅ `realestate.jsonld` valid against `context.jsonld` v1.2.0
- ✅ Deterministic `smartHomeId` per §8
- ✅ `RoleAssignment` granting `Role_Owner`
- ✅ S3 folder skeleton (`abox/areas/`, `abox/spaces/`, `abox/equipment/`, `plans/`, `documents/`, `exports/`)
- ✅ `manifest.json` with `storage="cloud"`
- ✅ `creationStatus = "draft"` — resumable
- ✅ Handoff to DH-SPEC-003: `{ smartHomeId, realEstateUri, s3Prefix, preferredLanguage }`

### 12.2 Welcome (local)
- ✅ Same A-BOX shape in IndexedDB
- ✅ `manifest.json` with `storage="local"`
- ✅ Export bundle downloadable at any time (§9.4)
- ✅ `creationStatus = "draft"`
- ✅ Handoff to DH-SPEC-003 local mode: `{ smartHomeId, realEstateUri, indexedDbRef, preferredLanguage }`

### 12.3 Upgrade path (§11.3)
- ✅ Local DH fully materialised in cloud under the new tier
- ✅ `smartHomeId` preserved or re-suffixed (collision) with trace in `dhc:description`
- ✅ Local copy optionally retained or purged per user choice

---

## 13. Non-functional & open items

### 13.1 Internationalization
- UI labels in en/de/fr. Entity labels sourced from `rdfs:label@lang`.
- `preferredLanguage` on `RealEstate` = DH-scoped default, separate from session UI lang.

### 13.2 Privacy / PII
- Address + coordinates are PII.
- Standard/Pro: IAM-isolated per owner prefix.
- Welcome: stays in user's browser; never transmitted to platform (geo proxy calls are stateless, no persistence).
- Bundle is user-controlled; warn on export that addresses leave the browser.
- GDPR DSAR (Standard/Pro): export = tenant prefix copy; deletion = prefix eviction + manifest purge.
- Welcome deletion = IndexedDB clear (trivial).

### 13.3 Open items

| # | Item | Owner | Blocker? |
|---|---|---|---|
| O-1 | Confirm Amazon Location vs Google primary | Architecture | No |
| O-2 | DynamoDB manifest index for scale | Architecture | No |
| O-3 | Country list supported at launch | Product | No |
| O-4 | Draft-DH TTL (auto-archive) | Product | No |
| O-5 | Ratify this spec structure as template | Product + Architecture | No |
| O-6 | Accept ontology bump to v1.2.0 | Ontology owner | **Yes — blocks A-BOX generation** |
| O-7 | Create `dhc-standard`, `dhc-professional` Cognito groups | Platform | **Yes (for cloud path) — Welcome path unblocked** |
| O-8 | Publish `capabilities.json` (DH-SPEC-000) | Architecture | **Yes — blocks tier enforcement** |
| O-9 | Geo-proxy rate limits per tier | Architecture | No — but needed before Welcome launch |
| O-10 | `@dhc/smarthome-id` shared library published to internal npm | Platform | **Yes — both runtimes need it** |

### 13.4 Ontology improvements surfaced (not required here)

1. `dhc:RealEstate` has no subclass distinguishing `House`, `Apartment`, `Land`, `Commercial`. Recommendations need it. Propose `dhc:PropertyType` enum.
2. `dhc:owns` range unrestricted — suggest explicit `range (RealEstate ⊔ Equipment)` + SHACL.
3. `dhc-roles.ttl` lacks `rdfs:label@en/de/fr` — align with core schema.
4. No `dhc:Tenant` concept distinct from `Agent` — relevant for org-level accounts.
5. `dhc:smartHomeId` uniqueness not enforced — add SHACL shape.

---

*End of DH-SPEC-002 v0.2.0*
