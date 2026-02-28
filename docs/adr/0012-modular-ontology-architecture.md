# ADR 0012: Modular Ontology Architecture (Core + Norm Modules)

## Status

Accepted

## Date

2026-02

## Context

The DigitalHome.Cloud ontology (`dhc-core.schema.ttl`, ADR 0007) defines the platform's domain vocabulary. As the platform expands to support country-specific electrical regulations (e.g. NF C 14-100 and NF C 15-100 in France), placing all regulatory detail into the Core ontology would create a monolithic file that mixes universal concepts with jurisdiction-specific constraints.

The Ontology Governance Model (`docs/specs/DigitalHome-Ontology-Governance-Model.md`) mandates a **Core + Norm Module** architecture to keep the Core stable and universal while allowing normative extensions per country and domain.

We needed to decide:

1. **Option A: Monolithic Core** — add all classes (including NFC-specific circuit subtypes) directly to `dhc-core.schema.ttl`. Simple but mixes universal and regulatory concerns.
2. **Option B: Core + Norm Modules** — the Core defines abstract base classes; separate module TTL files subclass them with regulation-specific detail. More files but clean separation of concerns.

## Decision

**Option B: Core + Norm Module architecture.**

### Core (`dhc-core.schema.ttl`)

The Core ontology defines universal, regulation-agnostic classes and properties. It provides abstract base classes that modules specialize:

- `dhc:Circuit`, `dhc:DistributionBoard`, `dhc:ProtectionDevice` — generic electrical
- `dhc:EnergyDelivery`, `dhc:EnergyMeter`, `dhc:EmergencyDisconnect` — delivery chain
- `dhc:ElectricalTechnicalSpace`, `dhc:Distribution` — spatial/topological

The Core never depends on any module.

### Norm Modules (`semantic-core/modules/`)

Each module is a self-contained TTL file that:

- **Only subclasses** Core classes — no new root concepts
- **Never redefines** Core semantics — specialization only, no override
- **Covers one domain** per module (e.g. electrical delivery, electrical installation)
- **Carries all regulatory constraints** — mandated values, wiring rules, protection sizing
- Is registered in `module-manifest.json` with metadata (id, label, version, category, countries)

Example modules:
- `dhc-nfc14100-electrical.ttl` — NF C 14-100 (energy delivery for France)
- `dhc-nfc15100-electrical.ttl` — NF C 15-100 (electrical installation for France)

### Build Pipeline Composition

The build pipeline (`parse-ontology.js`, `generate-blockly-toolbox.js`) reads the Core TTL and all registered modules, merging them into unified artifacts (`ontology-graph.json`, `blockly-blocks.json`, `blockly-toolbox.json`). Module blocks inherit parent class containment and reference properties via subclass analysis.

### SmartHome Activation

When a SmartHome is created, modules are activated based on country:
- Core classes are always available
- French SmartHomes activate NFC 14-100 and NFC 15-100 modules
- Module-specific validation rules become active (e.g. delivery chain completeness)

## Consequences

### Positive

- Core remains stable and regulation-agnostic — safe to evolve independently.
- Country-specific rules are isolated in modules — adding DIN VDE (Germany) or BS 7671 (UK) later does not touch the Core or French modules.
- Module manifest enables tooling to discover, filter, and compose modules dynamically.
- Validation rules can be scoped per module — only active when the module is activated.
- Aligns with the Ontology Governance Model's five rules.

### Negative

- More files to maintain — Core TTL + N module TTLs + manifest.
- Build pipeline must handle multi-file composition and subclass property inheritance.
- Block type naming must encode the module prefix to avoid collisions.

### Mitigations

- Module manifest provides a single discovery point — no hunting for scattered files.
- Toolbox generator handles inheritance automatically via subclass analysis of the Core.
- Naming convention (`dhc_nfc15100_lighting_circuit`) is systematic and collision-free.
