# DH-SPEC-003 — Ontology v2.0.0: Multi-Box Architecture

| Field          | Value                                      |
|----------------|--------------------------------------------|
| **Spec ID**    | DH-SPEC-003                                |
| **Version**    | 0.1.0 (draft)                              |
| **Status**     | Draft                                      |
| **Author**     | D-LAB-5 / DigitalHome.Cloud                |
| **Created**    | 2026-04-18                                 |
| **Repository** | `digitalhome-cloud-core`                   |
| **Branch**     | `v2.0.0` (new major)                       |

---

## §1 — Purpose

This specification defines the architectural overhaul of the DigitalHome.Cloud core ontology from v1.2.0 to v2.0.0, adopting the Multi-Box Model (T-Box / R-Box / C-Box separation) to decouple national norms from the domain schema.

## §2 — Problem Statement

In v1.x, national electrical norms (NF C 15-100, DIN VDE 0100, AREI/RGIE, BS 7671) are implemented as **T-Box subclasses** of core concepts (e.g., `dhc-nfc15100:LightingCircuit rdfs:subClassOf dhc:Circuit`). This creates three problems:

1. **Norm overlap**: A Belgian property may be subject to AREI/RGIE *and* parts of EN 61439. Subclass inheritance cannot express "this circuit complies with norm A *and* norm B" without multiple inheritance or artificial class hierarchies.
2. **T-Box bloat**: Every norm variant creates new classes, inflating the schema layer. The T-Box should be small and stable; norm details are volatile (norm revisions, country-specific amendments).
3. **Toolbox pollution**: The DHC Modeller generates Blockly blocks from the T-Box. Norm-specific subclasses produce redundant blocks (e.g., 15+ circuit subtypes for France alone) instead of one `Circuit` block with norm-driven constraints.

## §3 — Target Architecture

### §3.1 — Multi-Box Model

| Box   | Content                                    | Volatility | Files in repo                    |
|-------|--------------------------------------------|------------|----------------------------------|
| T-Box | Domain vocabulary: classes, properties, property axioms (R-Box), CircuitType instances | Low — changes require major version bump | `schema/tbox/*.ttl` |
| C-Box | Norm profiles: SHACL shapes defining constraints, defaults, and validation rules per national standard | Medium — new norms added, existing norms revised | `schema/cbox/<domain>/*.shapes.ttl` |
| A-Box | Instance data per Digital Home              | High — user-generated | **Not in this repository.** Created by DHC Smart Home Designer → S3 |

### §3.2 — Data Flow

```
AI Agent (Claude Code)
    │  writes / maintains
    ▼
digitalhome-cloud-core [git]
    │  T-Box + C-Box (.ttl files)
    │
    ▼  consumed by
DHC Modeller
    │  parses TTL → generates Blockly elements
    │  representing T-Box + C-Box constraints
    │
    ▼  publishes to
S3 (ontology-graph.json, blockly-blocks.json, blockly-toolbox.json, cbox-registry.json)
    │
    ▼  consumed by
DHC Smart Home Designer (frontend)
    │  user designs with norm-aware Blockly blocks
    │
    ▼  produces
A-Box [S3 / IndexedDB]
```

## §4 — Repository Structure

```
digitalhome-cloud-core/
│
├── CLAUDE.md                          ← AI Agent instructions & conventions
├── README.md
├── package.json                       ← Version tracking (no build scripts)
├── LICENSE
│
├── schema/
│   ├── tbox/                          ← T-Box + R-Box (combined)
│   │   ├── dhc-core.schema.ttl        ← Classes, properties, axioms, enum instances
│   │   ├── dhc-roles.ttl              ← Role instances (Owner, Installer, …)
│   │   └── context.jsonld             ← JSON-LD context for serialization
│   │
│   └── cbox/                          ← C-Box: Norm profiles as SHACL shapes
│       ├── cbox-manifest.json         ← Registry of available norm profiles
│       ├── electrical/
│       │   ├── nfc14100.shapes.ttl    ← NF C 14-100 (FR) — energy delivery
│       │   ├── nfc15100.shapes.ttl    ← NF C 15-100 (FR) — installation
│       │   ├── din-vde-0100.shapes.ttl ← DIN VDE 0100 (DE)
│       │   ├── arei-rgie.shapes.ttl   ← AREI/RGIE (BE)
│       │   └── bs7671.shapes.ttl      ← BS 7671 (UK)
│       ├── plumbing/
│       ├── heating/
│       └── building/
│
└── tests/                             ← AI-agent generated & maintained
    ├── tbox/
    │   └── core-schema.test.js
    ├── cbox/
    │   ├── nfc15100.test.js
    │   └── din-vde-0100.test.js
    └── fixtures/
        ├── valid-fr-lighting-circuit.ttl
        └── invalid-fr-lighting-circuit.ttl
```

### §4.1 — What Was Removed vs. v1.x

| v1.x path             | v2.0.0 disposition                              |
|------------------------|--------------------------------------------------|
| `src/ontology/`        | → `schema/tbox/`                                 |
| `src/modules/`         | → `schema/cbox/<domain>/` (as SHACL shapes)      |
| `src/instances/`       | Removed. A-Box not in repo.                      |
| `scripts/`             | Removed. Build logic migrated to DHC Modeller.   |
| `build/`               | Removed. Modeller publishes directly to S3.      |

## §5 — T-Box Design (schema/tbox/)

### §5.1 — Principles

1. **Norm-agnostic**: No class or property references a specific national standard.
2. **R-Box inline**: Property axioms (transitivity, inverses, property chains) are declared alongside their property definitions in `dhc-core.schema.ttl`. No separate R-Box file.
3. **Enum instances in T-Box**: Universal domain enumerations (CircuitType, ProtectionDeviceType, etc.) are instances declared in the T-Box. These are norm-agnostic functional categories.
4. **Design views preserved**: The `dhc:designView` annotation on classes and properties is retained for Blockly toolbox grouping.
5. **Multilingual labels**: All classes and properties carry `rdfs:label` in `@en`, `@de`, `@fr`.

### §5.2 — Key Changes from v1.2.0

#### CircuitType instances replace norm subclasses

**v1.x** (T-Box pollution):
```turtle
dhc-nfc15100:LightingCircuit
    a owl:Class ;
    rdfs:subClassOf dhc:Circuit .
```

**v2.0.0** (clean T-Box):
```turtle
# In dhc-core.schema.ttl — T-Box
dhc:CircuitType_Lighting
    a dhc:CircuitType ;
    rdfs:label "Lighting"@en ;
    rdfs:label "Beleuchtung"@de ;
    rdfs:label "Éclairage"@fr .

dhc:CircuitType_Socket
    a dhc:CircuitType ;
    rdfs:label "Socket"@en ;
    rdfs:label "Steckdose"@de ;
    rdfs:label "Prise de courant"@fr .

dhc:CircuitType_DedicatedAppliance
    a dhc:CircuitType ;
    rdfs:label "Dedicated Appliance"@en ;
    rdfs:label "Spezialisiertes Gerät"@de ;
    rdfs:label "Appareil spécialisé"@fr .

dhc:CircuitType_Cooking
    a dhc:CircuitType ;
    rdfs:label "Cooking"@en ;
    rdfs:label "Kochen"@de ;
    rdfs:label "Cuisson"@fr .

dhc:CircuitType_Heating
    a dhc:CircuitType ;
    rdfs:label "Heating"@en ;
    rdfs:label "Heizung"@de ;
    rdfs:label "Chauffage"@fr .

dhc:CircuitType_WaterHeater
    a dhc:CircuitType ;
    rdfs:label "Water Heater"@en ;
    rdfs:label "Warmwasserbereiter"@de ;
    rdfs:label "Chauffe-eau"@fr .

dhc:CircuitType_IRVE
    a dhc:CircuitType ;
    rdfs:label "EV Charging (IRVE)"@en ;
    rdfs:label "Elektrofahrzeug-Ladung (IRVE)"@de ;
    rdfs:label "Recharge véhicule électrique (IRVE)"@fr .

dhc:CircuitType_FloorHeating
    a dhc:CircuitType ;
    rdfs:label "Floor Heating"@en ;
    rdfs:label "Fußbodenheizung"@de ;
    rdfs:label "Plancher chauffant"@fr .
```

#### R-Box axioms inline with properties

```turtle
# In dhc-core.schema.ttl — R-Box section
dhc:feeds
    a owl:ObjectProperty, owl:TransitiveProperty ;
    rdfs:label "feeds"@en ;
    rdfs:label "speist"@de ;
    rdfs:label "alimente"@fr ;
    rdfs:comment "Upstream-to-downstream topology link in the energy delivery chain."@en ;
    dhc:designView "electrical" .

dhc:locatedIn
    a owl:ObjectProperty ;
    owl:inverseOf dhc:contains ;
    rdfs:label "located in"@en ;
    rdfs:label "befindet sich in"@de ;
    rdfs:label "situé dans"@fr ;
    rdfs:range dhc:Space ;
    dhc:designView "electrical" .
```

#### Norm-specific classes removed from T-Box

The following classes from v1.x modules are **deleted** — their constraints move to C-Box shapes:

- `dhc-nfc14100:NF14EnergyMeter`
- `dhc-nfc14100:NF14EmergencyDisconnect`
- `dhc-nfc15100:GTL`
- `dhc-nfc15100:LightingCircuit`
- `dhc-nfc15100:SocketCircuit16A_8Sockets`
- `dhc-nfc15100:SocketCircuit20A_12Sockets`
- `dhc-nfc15100:KitchenSocketCircuit20A_6Sockets_Dedicated`
- `dhc-nfc15100:SpecializedApplianceCircuit20A_Dedicated`
- `dhc-nfc15100:WaterHeaterCircuit20A_Dedicated`
- `dhc-nfc15100:CookingCircuitMono32A_Dedicated`
- `dhc-nfc15100:CookingCircuitTri20A_Dedicated`
- All `dhc-nfc15100:HeatingWallEmitters*` classes
- All `dhc-nfc15100:FloorHeating*` classes
- All `dhc-nfc15100:IRVE*` classes

Their constraints become C-Box SHACL shapes referencing `dhc:CircuitType` instances.

## §6 — C-Box Design (schema/cbox/)

### §6.1 — Principles

1. **SHACL shapes, not subclasses**: Each norm profile defines SHACL `sh:NodeShape` and `sh:PropertyShape` constraints over T-Box classes.
2. **Composable**: Multiple C-Box profiles can be activated simultaneously on a single Digital Home. The Designer validates against the union of active shapes.
3. **Self-describing**: Each shape file declares its norm metadata (country, version, domain) via ontology-level annotations.
4. **Registry**: `cbox-manifest.json` indexes all available profiles for the Modeller and Designer.

### §6.2 — C-Box Shape Pattern

Example: NF C 15-100 lighting circuit constraints.

```turtle
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix dhc:  <https://digitalhome.cloud/ontology#> .
@prefix dhc-cbox: <https://digitalhome.cloud/cbox/nfc15100#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

# ── Norm profile metadata ──
<https://digitalhome.cloud/cbox/nfc15100>
    a owl:Ontology ;
    rdfs:label "NF C 15-100 Constraint Profile"@en ;
    rdfs:label "NF C 15-100 Constraintprofil"@de ;
    rdfs:label "Profil de contraintes NF C 15-100"@fr ;
    dcterms:description "SHACL shapes for NF C 15-100 residential electrical installation (France)."@en ;
    dhc:normId "nfc15100" ;
    dhc:normCountry "FR" ;
    dhc:normDomain "electrical" ;
    dhc:normVersion "2024" .

# ── Lighting circuit shape ──
dhc-cbox:LightingCircuitShape
    a sh:NodeShape ;
    sh:targetClass dhc:Circuit ;
    sh:condition [
        sh:property [
            sh:path dhc:hasCircuitType ;
            sh:hasValue dhc:CircuitType_Lighting ;
        ] ;
    ] ;
    rdfs:label "Lighting Circuit (NF C 15-100)"@en ;
    rdfs:label "Beleuchtungsstromkreis (NF C 15-100)"@de ;
    rdfs:label "Circuit éclairage (NF C 15-100)"@fr ;

    # Constraint: max 8 points per lighting circuit
    sh:property [
        sh:path dhc:maxPoints ;
        sh:maxInclusive 8 ;
        sh:message "NF C 15-100: Lighting circuits allow max 8 points."@en ;
        sh:message "NF C 15-100: Beleuchtungsstromkreise erlauben max. 8 Punkte."@de ;
        sh:message "NF C 15-100 : Les circuits éclairage autorisent max. 8 points."@fr ;
    ] ;

    # Constraint: 10A breaker
    sh:property [
        sh:path dhc:ratedCurrent ;
        sh:maxInclusive 10 ;
        sh:message "NF C 15-100: Lighting circuit breaker max 10A."@en ;
    ] ;

    # Constraint: 1.5mm² wiring
    sh:property [
        sh:path dhc:crossSection ;
        sh:minInclusive 1.5 ;
        sh:message "NF C 15-100: Lighting circuit min 1.5mm² wiring."@en ;
    ] ;

    # Default wiring specification
    dhc:defaultWiring "3G1.5" .
```

### §6.3 — C-Box Manifest

`schema/cbox/cbox-manifest.json`:

```json
{
  "$schema": "https://digitalhome.cloud/schemas/cbox-manifest.schema.json",
  "version": "2.0.0",
  "profiles": [
    {
      "id": "nfc14100",
      "norm": "NF C 14-100",
      "country": "FR",
      "domain": "electrical",
      "normVersion": "2021",
      "file": "electrical/nfc14100.shapes.ttl",
      "requires": [],
      "description": {
        "en": "Energy delivery from provider to main board (France)",
        "de": "Energieeinspeisung vom Versorger zum Hauptverteiler (Frankreich)",
        "fr": "Livraison d'énergie du fournisseur au tableau principal (France)"
      }
    },
    {
      "id": "nfc15100",
      "norm": "NF C 15-100",
      "country": "FR",
      "domain": "electrical",
      "normVersion": "2024",
      "file": "electrical/nfc15100.shapes.ttl",
      "requires": ["nfc14100"],
      "description": {
        "en": "Residential electrical installation (France)",
        "de": "Elektroinstallation Wohngebäude (Frankreich)",
        "fr": "Installation électrique résidentielle (France)"
      }
    },
    {
      "id": "din-vde-0100",
      "norm": "DIN VDE 0100",
      "country": "DE",
      "domain": "electrical",
      "normVersion": "2024",
      "file": "electrical/din-vde-0100.shapes.ttl",
      "requires": [],
      "description": {
        "en": "Electrical installation in buildings (Germany)",
        "de": "Errichten von Niederspannungsanlagen (Deutschland)",
        "fr": "Installation électrique dans les bâtiments (Allemagne)"
      }
    },
    {
      "id": "arei-rgie",
      "norm": "AREI/RGIE",
      "country": "BE",
      "domain": "electrical",
      "normVersion": "2023",
      "file": "electrical/arei-rgie.shapes.ttl",
      "requires": [],
      "description": {
        "en": "General regulation on electrical installations (Belgium)",
        "de": "Allgemeine Vorschriften für elektrische Anlagen (Belgien)",
        "fr": "Règlement général sur les installations électriques (Belgique)"
      }
    },
    {
      "id": "bs7671",
      "norm": "BS 7671",
      "country": "GB",
      "domain": "electrical",
      "normVersion": "2024",
      "file": "electrical/bs7671.shapes.ttl",
      "requires": [],
      "description": {
        "en": "IET Wiring Regulations (United Kingdom)",
        "de": "IET-Verdrahtungsvorschriften (Vereinigtes Königreich)",
        "fr": "Réglementation de câblage IET (Royaume-Uni)"
      }
    }
  ]
}
```

## §7 — T-Box Namespace & Versioning

### §7.1 — Namespace

The core namespace remains unchanged:

```
@prefix dhc: <https://digitalhome.cloud/ontology#> .
```

C-Box profiles use sub-namespaces:

```
@prefix dhc-cbox: <https://digitalhome.cloud/cbox/{normId}#> .
```

Examples:
- `https://digitalhome.cloud/cbox/nfc15100#`
- `https://digitalhome.cloud/cbox/din-vde-0100#`
- `https://digitalhome.cloud/cbox/arei-rgie#`

### §7.2 — Version

```turtle
<https://digitalhome.cloud/ontology>
    a owl:Ontology ;
    owl:versionInfo "2.0.0" .
```

`package.json` tracks the same version:

```json
{
  "name": "@dhc/digitalhome-cloud-core",
  "version": "2.0.0",
  "description": "DHC core ontology: T-Box + C-Box schema definitions"
}
```

## §8 — Migration from v1.x

### §8.1 — Breaking Changes

This is a **major version bump**. The following are breaking changes:

1. **Removed**: All `dhc-nfc14100:*` and `dhc-nfc15100:*` classes. Any A-Box data using these classes as `rdf:type` must be migrated to use `dhc:Circuit` + `dhc:hasCircuitType` + `dhc:governedBy`.
2. **Moved**: `src/` → `schema/`.
3. **Removed**: `src/modules/` (norm TTL files). Replaced by `schema/cbox/`.
4. **Removed**: `src/instances/` (demo A-Box data). Not in repo.
5. **Removed**: `scripts/` and `build/`. Modeller owns these.

### §8.2 — A-Box Migration Pattern

**v1.x A-Box** (uses norm subclass):
```turtle
ex:circuit-01
    a dhc-nfc15100:LightingCircuit ;
    dhc:maxPoints 8 ;
    dhc:hasProtection ex:breaker-01 .
```

**v2.0.0 A-Box** (uses T-Box class + CircuitType + norm reference):
```turtle
ex:circuit-01
    a dhc:Circuit ;
    dhc:hasCircuitType dhc:CircuitType_Lighting ;
    dhc:governedBy dhc:Norm_NFC15100 ;
    dhc:maxPoints 8 ;
    dhc:hasProtection ex:breaker-01 .
```

## §9 — Test Strategy

Tests are **AI-agent generated and maintained**. The test suite validates:

1. **T-Box consistency**: All classes have en/de/fr labels, all properties have domain/range, no orphan properties.
2. **C-Box validity**: Each SHACL shape file is syntactically valid Turtle, references only T-Box classes/properties that exist, and all `sh:message` values are multilingual.
3. **C-Box conformance**: Fixture files (minimal synthetic A-Box triples) are validated against C-Box shapes — valid fixtures pass, invalid fixtures produce expected violations.

### §9.1 — Test Tooling

```json
{
  "devDependencies": {
    "rdf-validate-shacl": "^0.6.0",
    "n3": "^1.17.0",
    "vitest": "^3.0.0"
  },
  "scripts": {
    "test": "vitest run"
  }
}
```

### §9.2 — Fixture Convention

Fixtures live in `tests/fixtures/` and follow the naming pattern:

```
{valid|invalid}-{country}-{domain}-{scenario}.ttl
```

Examples:
- `valid-fr-lighting-circuit.ttl` — A conforming French lighting circuit
- `invalid-fr-lighting-circuit-too-many-points.ttl` — 12 points on a lighting circuit (should fail NFC15100)
- `valid-de-socket-circuit.ttl` — A conforming German socket circuit

## §10 — CLAUDE.md Conventions

The `CLAUDE.md` file instructs the AI Agent on repo conventions:

1. **Schema only**: Never create A-Box instance data in this repo.
2. **T-Box changes = major version bump** unless purely additive (new class/property).
3. **C-Box additions**: New norm profile = new `.shapes.ttl` file + entry in `cbox-manifest.json`.
4. **Naming conventions**:
   - T-Box classes: PascalCase (`dhc:DistributionBoard`)
   - T-Box properties: camelCase (`dhc:hasCircuit`)
   - T-Box enum instances: `dhc:{ClassName}_{Value}` (`dhc:CircuitType_Lighting`)
   - C-Box shapes: `dhc-cbox:{Concept}Shape` (`dhc-cbox:LightingCircuitShape`)
   - C-Box files: `{norm-id}.shapes.ttl`
5. **Multilingual labels**: Every class, property, enum instance, and SHACL shape carries `rdfs:label` in `@en`, `@de`, `@fr`.
6. **Tests**: After any schema change, update or create tests. Run `yarn test` before committing.
7. **Design views**: Every class and property carries `dhc:designView` for Blockly toolbox grouping.

## §11 — Deliverables Checklist

| # | Deliverable                         | Status    |
|---|-------------------------------------|-----------|
| 1 | `schema/tbox/dhc-core.schema.ttl` (v2.0.0, norm-agnostic, with CircuitType instances and R-Box axioms) | TODO |
| 2 | `schema/tbox/dhc-roles.ttl` (unchanged) | DONE (carry forward) |
| 3 | `schema/tbox/context.jsonld` (updated for v2 namespaces) | TODO |
| 4 | `schema/cbox/cbox-manifest.json` | TODO |
| 5 | `schema/cbox/electrical/nfc14100.shapes.ttl` | TODO |
| 6 | `schema/cbox/electrical/nfc15100.shapes.ttl` | TODO |
| 7 | `schema/cbox/electrical/din-vde-0100.shapes.ttl` | TODO (stub) |
| 8 | `schema/cbox/electrical/arei-rgie.shapes.ttl` | TODO (stub) |
| 9 | `schema/cbox/electrical/bs7671.shapes.ttl` | TODO (stub) |
| 10 | `tests/tbox/core-schema.test.js` | TODO |
| 11 | `tests/cbox/nfc15100.test.js` | TODO |
| 12 | Test fixtures | TODO |
| 13 | `CLAUDE.md` (v2.0.0) | TODO |
| 14 | `README.md` (v2.0.0) | TODO |
| 15 | `package.json` (v2.0.0, test scripts only) | TODO |

## §12 — Open Items

1. **Plumbing / Heating / Building C-Box norms**: Which norms to include in v2.0.0 initial release? (DTU 60.x for FR plumbing? DIN 1988 for DE? Or electrical-only for v2.0.0?)
2. **`dhc:Guideline` class**: Keep in T-Box as-is, or refactor into a `dhc:Norm` class with richer metadata now that norms are first-class C-Box citizens?
3. **SHACL `sh:condition` support**: Verify that the DHC Modeller's SHACL parser supports `sh:condition` for conditional shape activation. If not, alternative pattern: use `sh:target` with SPARQL-based target.

## §13 — References

- Multi-Box Model: *Architectural Framework: The Multi-Box Model for Modern Metadata Environments* (D-LAB-5, 2026)
- SHACL 1.2: W3C Shapes Constraint Language
- DH-SPEC-000: Access Tiers & Capability Matrix
- DH-SPEC-002: SmartHome Manager — Create New Digital Home
