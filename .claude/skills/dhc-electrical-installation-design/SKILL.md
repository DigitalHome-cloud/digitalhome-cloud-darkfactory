---
name: dhc-electrical-installation-design
description: Designing electrical installations and power management as a semantic A-Box — turning a prose description of a home ("French detached house, 9 kVA single-phase TT, 6 kW PV + Deye hybrid, EV charger in the garage") into validated Turtle under `repos/core/schema/abox/`, wired with Brick 1.5 equipment and ASHRAE 223P connection topology, and checked against the NF C 15-100 / NF C 14-100 C-Box shapes. Trigger on "design the electrical installation", "model this home's circuits", "add a circuit / breaker / RCD / EV charger to the A-Box", "why doesn't my SHACL rule fire", "wire up L/N/PE", "single-line diagram from the A-Box", "is this installation NF C 15-100 compliant". Do NOT trigger for T-Box authoring or class promotion (use `dhc-ontology-explorer` — it is the only sanctioned writer for `schema/tbox/dhc-*.ttl`), for Blockly artifacts (`dhc-build-blockly-elements-for-*`), or for device catalogue/gateway discovery (`dhc-device-autodiscovery`).
---

# DHC Electrical Installation & Power Management Design

Turns a **prose description of a home** into a **validated electrical A-Box**.
Claude authors the Turtle directly — there is no generator script, matching the
precedent set by the Blockly skill.

The single hard rule: **the model must be joined to the real vocabulary, and the
validation must be proven to fire.** Every layer of this stack fails silently.
A namespace missing its `#`, a `subClassOf` naming a class that doesn't exist, a
`sh:targetClass` that selects nothing, a guard literal with the wrong datatype,
an A-Box term that was never promoted — each produces a green result while
validating nothing. **All five have already shipped in this repo.** See
**Common pitfalls**; they are not hypothetical.

## When to use this skill

- "design the electrical installation for …", "model the circuits of this home"
- adding a circuit, breaker, RCD, socket, luminaire, EV charger, PV array,
  inverter or meter to `schema/abox/electrical-installation-house.ttl`
- authoring or debugging a C-Box conformance check ("why doesn't my rule fire?")
- expressing conductor topology — L/N/PE, connection points, phases
- preparing an A-Box that a wiring / single-line diagram is generated from

Do **not** trigger for:

- **T-Box work** — adding/renaming a `dhc:` class or property, promoting from
  `schema/draft/`. That is `dhc-ontology-explorer`, the **only** sanctioned
  writer for `schema/tbox/dhc-core.ttl` and `dhc-app-metadata.ttl`.
  Hand-editing those files bypasses the splitter and deterministic serializer.
- **Blockly toolbox/blocks** — `dhc-build-blockly-elements-for-*`.
- **Device catalogue / gateway discovery** — `dhc-device-autodiscovery`.

## Inputs — what drives the design

1. **Prose.** Country, supply (kVA, phases, earthing regime), generation,
   storage, board, rooms, loads, automation. Anything unstated gets a
   norm-sensible default — state the default you chose, don't silently invent.
2. **The T-Box** — `repos/core/schema/tbox/`:
   `Brick+extensions.ttl` (Brick 1.5 + REC + 223P, **read-only**),
   `dhc-core.ttl` (domain), `dhc-app-metadata.ttl` (UI overlay).
3. **The C-Box** — `repos/core/schema/cbox/electrical/*.shapes.ttl` +
   `cbox-manifest.json`. The norm profile follows the country.

## The v3 layering (SPEC-V3-Redesign.md)

Model top-down and **use `dhc:` only where the standards are silent**:

| Layer | Owns | Example |
|-------|------|---------|
| **REC** | space & admin context | `rec:Room`, `rec:locatedIn`, `dhc:DigitalHome ⊑ rec:Site` |
| **Brick 1.5** | what a device *is* | `brick:Photovoltaic_Inverter`, `brick:Luminaire`, `brick:Controller` |
| **ASHRAE 223P** | how it is *connected* | `s223:Connection`, `s223:InletConnectionPoint`, media |
| **`dhc:`** | **gap filling only** | the norm layer — see below |

Every `dhc:` electrical class is a **thin specialization of a real upstream
class**, so it inherits that class's SHACL constraints:

```
dhc:Circuit             ⊑ s223:System                       (4 inherited sh:property)
dhc:ProtectionDevice    ⊑ s223:ElectricityBreaker           (2 — needs electricity in+out)
  dhc:RCD ⊑ dhc:ProtectionDevice ;  dhc:RCBO ⊑ dhc:RCD
dhc:WiringSegment       ⊑ s223:Connection                   (15 — medium compatibility)
dhc:Socket              ⊑ s223:ElectricityOutlet            (2)
dhc:Distribution        ⊑ s223:Junction                     (8)  ; dhc:BusBar likewise
dhc:DistributionBoard   ⊑ brick:Breaker_Panel
dhc:EnergyMeter         ⊑ brick:Electrical_Meter
dhc:EmergencyDisconnect ⊑ brick:Building_Disconnect_Switch  (the AGCP)
```

`dhc:EnergyMeter` is parented on `brick:Electrical_Meter`, **not**
`s223:ElectricityMeter`, because the 223P class mandates at least one contained
`VoltageSensor` and `ElectricCurrentSensor` — telemetry the design model does
not carry.

### The vocabulary that exists (verified in Brick+extensions.ttl 1.5)

| Concept | Use |
|---|---|
| Generation | `brick:PV_Generation_System`, `brick:PV_Array`, `brick:PV_Panel`, `brick:Photovoltaic_Inverter` |
| Storage | `brick:Battery` + `s223:Battery` (multi-type) |
| **Hybrid inverter** | `s223:ElectricEnergyInverter` **alongside** `brick:Photovoltaic_Inverter` — see below |
| Loads | `brick:Luminaire`, `brick:Electric_Vehicle_Charging_Station`, `s223:ElectricOven`, `s223:ElectricCooktop`, `s223:ClothesWasher`, `s223:Dishwasher`, `brick:Water_Heater` |
| Automation | `brick:Controller` + `brick:controls` |
| Topology | `s223:hasConnectionPoint`, `s223:connectsThrough`, `s223:cnx`, `brick:feeds` |
| Media | `s223:AC-230VLN-1Ph-50Hz`, `s223:Electricity-Neutral`, `s223:Electricity-Earth`, `s223:DC-48V`, `s223:DC-380V` |
| Ratings | `brick:ratedCurrentOutput`, `brick:ratedPowerOutput`, `brick:electricalPhaseCount` |

**A hybrid inverter needs the 223P type.** `brick:Photovoltaic_Inverter` has no
connection points at all, so a node typed only that way is invisible to the
conductor layer — which is how the demo's Deye sat for months as five characters
of `rdfs:label`. `s223:ElectricEnergyInverter` requires ≥1 CP on medium
`Electricity-AC` **and** ≥1 on `Electricity-DC`, which is exactly the hybrid
shape. Type it both: Brick says what it is, 223P says how it connects.

**`brick:feeds` is `owl:AsymmetricProperty` + `owl:IrreflexiveProperty`, and has
no domain or range.** So it will connect anything (board → breaker → load is
fine), but asserting *both* `battery feeds inverter` and `inverter feeds battery`
is an OWL inconsistency — and **no reasoner runs in this stack, so nothing will
ever tell you.** Assert the one direction that is the generator flow
(discharge), and express import/export and charge/discharge with
`s223:BidirectionalConnectionPoint`.

**Check what a class drags in before typing something with it.** `s223:ClothesWasher`
requires an outlet on medium `Fluid-Water` — the drain. An electrical model has
no plumbing, so `ex:washing-machine` carries that as a known gap
(`doc/parking-lot.md` § 3) rather than growing a domain to satisfy an axiom.
Nothing enforces it today: `build-abox.mjs` parses `Brick+extensions.ttl` only
for the equipment closure and never runs its ~3237 shapes. Also note
`dhc:powerRating` has `rdfs:domain brick:Equipment` — retyping a load to a 223P
class *alone* silently violates it. Multi-type.

### The irreducible `dhc:` residue — and why each exists

Absent from **both** Brick 1.5 and the full 223P (grep them before adding more):

- `dhc:crossSection` — conductor mm². Neither ontology has any conductor-size
  property, and NF C 15-100 turns on 1.5 / 2.5 / 6 / 10.
- `dhc:maxPoints` — points per circuit. The core NF C count rule.
- `dhc:hasCircuitType` + 8 `dhc:CircuitType_*` — the norm classification that
  every C-Box guard switches on.
- `dhc:governedBy` → `dhc:Norm` — the compliance link. **Deliberately has no
  `rdfs:domain`**: it applies to Circuit, EnergyMeter, EnergyDelivery,
  DistributionBoard and the GTL, which share no ancestor. A domain would
  wrongly *infer* types. `dhc:ratedCurrent` / `dhc:crossSection` are
  domain-less for the same reason — they carry design intent on the Circuit
  *and* device fact on the breaker/wire.
  **Name the norm, never the edition.** There is no `dhc:builtUnder`; it existed
  briefly and was purged. Compliance is *computed* by validating against every
  edition that has shapes and comparing the verdicts (`dhc:shapesFile` +
  `dhc:supersedes` + `dhc:latestEdition`), so an A-Box that asserted which
  edition it was built to would be stating something the C-Box derives — and
  usually stating it wrongly, since a surveyed installation rarely records its
  edition. Passing the current edition is green; passing an older one and
  failing the current is grandfathered. See `repos/core/js-tools/README.md`
  § Compliance.
- `dhc:RCD` / `dhc:RCBO` + `dhc:sensitivityMA` + `dhc:rcdType` — residual-current
  protection. Zero hits for residual-current / ground-fault / earth-leakage in
  either ontology, so the 30 mA Type A differential has nowhere else to live.
- `dhc:contractedPowerKVA`, `dhc:neutralSystem` (TT/TN/IT), `dhc:currentType`.

## The conductor convention (load-bearing)

**One `s223:Connection` per conductor**, each carrying its own medium.
`s223:Electricity-Neutral` and `s223:Electricity-Earth` are
`rdfs:subClassOf s223:Constituent-Electricity` — real, distinct media, and the
only two beyond the AC/DC/Signal enums. This is what makes L/N/PE explicit and a
true wiring diagram possible; `brick:feeds` alone only says "upstream of".

```turtle
ex:circuit-lgt-lr a dhc:Circuit ;                 # IS-A s223:System
    dhc:hasCircuitType dhc:CircuitType_Lighting ; # drives the C-Box guard
    dhc:governedBy     dhc:Norm_NFC15100 ;
    dhc:maxPoints      "6"^^xsd:integer ;
    dhc:ratedCurrent   "10"^^xsd:decimal ;        # decimal — see pitfalls
    dhc:crossSection   "1.5"^^xsd:decimal ;
    dhc:phase          "1"^^xsd:integer ;         # integer — see pitfalls
    dhc:dedicated      false ;
    dhc:hasProtection  ex:brk-lgt-lr ;
    dhc:hasWiring      ex:wire-lgt-lr-L, ex:wire-lgt-lr-N, ex:wire-lgt-lr-PE ;
    s223:hasMember     ex:brk-lgt-lr, ex:lum-lr-1 .   # Equipment|System ONLY

ex:brk-lgt-lr a dhc:ProtectionDevice ;            # IS-A s223:ElectricityBreaker
    dhc:ratedCurrent "10"^^xsd:decimal ;
    brick:ratedCurrentOutput [ brick:hasUnit unit:A ;         # blank node!
                               brick:value "10"^^xsd:decimal ] ;
    s223:hasConnectionPoint ex:brk-lgt-lr-in, ex:brk-lgt-lr-out .

ex:brk-lgt-lr-out a s223:OutletConnectionPoint ;
    s223:hasMedium       s223:AC-230VLN-1Ph-50Hz ;
    s223:connectsThrough ex:wire-lgt-lr-L .

ex:wire-lgt-lr-L  a dhc:WiringSegment ;           # IS-A s223:Connection
    s223:hasMedium s223:AC-230VLN-1Ph-50Hz ;
    dhc:crossSection "1.5"^^xsd:decimal ;
    dhc:wiring "R2V 3G1.5" .                      # NOT dhc:cableSpec — see pitfalls
ex:wire-lgt-lr-N  a dhc:WiringSegment ;
    s223:hasMedium s223:Electricity-Neutral ;     dhc:crossSection "1.5"^^xsd:decimal .
ex:wire-lgt-lr-PE a dhc:WiringSegment ;
    s223:hasMedium s223:Electricity-Earth ;       dhc:crossSection "1.5"^^xsd:decimal .

ex:lum-lr-1 a brick:Luminaire ;
    brick:hasLocation       ex:living-room ;
    s223:hasConnectionPoint ex:lum-lr-1-in .
ex:lum-lr-1-in a s223:InletConnectionPoint ;
    s223:hasMedium       s223:AC-230VLN-1Ph-50Hz ;
    s223:connectsThrough ex:wire-lgt-lr-L .
```

Chain: `Equipment –hasConnectionPoint→ CP –connectsThrough→ Connection`.
`s223:cnx` is the symmetric adjacency over Equipment-CP-Connection-CP-Equipment.

**Supply media by country** (`s223:AC-*` is self-typed — reference it directly):

| Supply | Medium |
|---|---|
| FR/EU domestic 230 V 1-phase | `s223:AC-230VLN-1Ph-50Hz` |
| FR/EU 400 V 3-phase | `s223:AC-400VLL-230VLN-3Ph-50Hz` + `s223:ElectricalPhaseIdentifier-A/-B/-C` |
| UK 230 V | `s223:AC-240VLN-1Ph-50Hz` (nearest enum) |

## Datatype convention (load-bearing)

| Property | Datatype |
|---|---|
| `ratedCurrent`, `crossSection`, `contractedPowerKVA`, `sensitivityMA` | `xsd:decimal` |
| `phase`, `maxPoints` | `xsd:integer` |
| `dedicated` | `xsd:boolean` |

`sh:hasValue` compares **RDF terms**, so a mismatched datatype silently
disables the whole shape. `sh:minInclusive` / `sh:maxInclusive` compare
numerically and are immune — prefer them. `tests/cbox/guards.test.js` enforces
this against each property's declared `rdfs:range`.

## Workflow

1. **Read the prose.** Extract: country → norm profile; supply (kVA, phases,
   earthing); generation/storage; rooms; loads; automation.
2. **Pick the norm** from `cbox-manifest.json` by `country`. FR ⇒ `nfc15100`
   (installation) + `nfc14100` (delivery).
3. **Check every term exists before you type it.** For each class/property,
   grep `schema/tbox/dhc-core.ttl`. A term that is only in `schema/draft/` is
   **not** usable — it must be promoted first, and that is
   `dhc-ontology-explorer`'s job. Never invent a term inline.
4. **Model top-down**: site/spaces (REC) → delivery → generation (Brick) →
   board + protection → circuits (`dhc:Circuit`) → conductors (223P) → loads →
   automation.
5. **Assert design intent on the Circuit.** The C-Box reads `dhc:ratedCurrent`
   / `dhc:crossSection` / `dhc:maxPoints` **directly off `dhc:Circuit`**. Device
   facts (`brick:ratedCurrentOutput` on the breaker) live on the device and must
   agree.
6. **Include at least one deliberate defect** — see below. Not optional.
7. **Validate** and confirm the defect is reported (Verification protocol).
8. **Never** hand-edit `schema/tbox/dhc-*.ttl`.

## The mandatory negative fixture

Every A-Box this skill produces carries **≥1 deliberately non-compliant
element**, documented in the file header as intentional.

This is not pedantry. `sh:targetClass` selecting zero nodes reports
**`conforms: true`**. A guard whose literal has the wrong datatype makes its
shape a permanent no-op — also **`conforms: true`**. A compliant-only A-Box
that "passes" tells you *nothing* about whether validation ran. The defect is
the only evidence the chain is alive.

The canonical one (`schema/abox/electrical-installation-house.ttl`): `ex:circuit-ev-legacy`, a 32 A
single-phase IRVE circuit wired in 1.5 mm² where NF C 15-100 demands ≥ 10 mm².

**State the bar PER EDITION.** Once more than one edition is validated a single
"violations: N" is ambiguous, and the two numbers mean opposite things — a
violation under a superseded edition is the *grandfathering* signal, not
non-compliance:

```
focus nodes (a dhc:Circuit): 7                  ← not vacuous

dhc:NormEdition_NFC15100_2015 (superseded): 1 violation
  ✗ ex:circuit-ev-legacy   nfc15100:IRVE32AMonoShape     ← the deliberate defect

dhc:NormEdition_NFC15100_2024 (in force):   3 violations
  ✗ ex:circuit-ev          nfc15100-2024:IRVE32AMono2024Shape   ← GRANDFATHERED, not broken
  ✗ ex:circuit-ev-legacy   (both shapes)

conforms: false                                 ← against the edition in force
```

Two things must hold, and they fail differently:

- **`ex:circuit-ev-legacy` must fail the OLDEST edition.** Failing only the
  current one would make it *grandfathered* — i.e. lawful — which is the
  opposite of what the file exists to demonstrate.
- **`ex:circuit-ev` must fail the CURRENT edition and pass the older one.** If
  it goes green, the 2024 delta is a no-op, yellow never appears anywhere, and
  the whole edition mechanism reports success while proving nothing.

**If electrical-installation-house.ttl ever conforms, the chain is broken — do not "fix" it by
correcting the cross-section.** This is exactly how the dead `sh:hasValue 32`
guard was found: the demo was written first, the defect was not reported, and
that silence *was* the bug.

## Files this skill touches

| Path | Read | Write |
|---|---|---|
| `repos/core/schema/abox/electrical-installation-house.ttl` | yes | **yes — the deliverable** |
| `repos/core/schema/tbox/Brick+extensions.ttl` | yes | **never** |
| `repos/core/schema/tbox/dhc-core.ttl` | yes | never — via `dhc-ontology-explorer` only |
| `repos/core/schema/tbox/dhc-app-metadata.ttl` | yes | never — via explorer only |
| `repos/core/schema/cbox/electrical/*.shapes.ttl` | yes | yes — norm rules |
| `repos/core/schema/cbox/cbox-manifest.json` | yes | yes — when adding a profile |
| `repos/core/tests/fixtures/*.ttl` | yes | yes — valid+invalid pair per shape |
| `repos/core/tests/cbox/<norm>-<year>.test.js` | yes | yes |
| `repos/core/tests/_helpers/loadGraph.js` | yes | reuse — do not reimplement |

## Verification protocol

Reuse `tests/_helpers/loadGraph.js` (`readTtl` / `parseToStore` /
`validateAgainst`, on `rdf-validate-shacl@0.6.0`). No pySHACL — the shapes were
authored against the JS validator.

1. **Parses**: `parseToStore(readTtl('schema/abox/electrical-installation-house.ttl'))`.
2. **Anti-vacuity — do this first.** Count focus nodes:
   `[...data.match(null, namedNode(RDF+'type'), namedNode(DHC+'Circuit'))].length`
   must equal the number of circuits you authored. **A shape that selects
   nothing can never fail.**
3. **Negative (load-bearing)**: `validateAgainst(shapes, tbox + abox)` →
   `conforms: false`, reporting the expected rule. **What you assert on depends
   on the shape's form** — get this wrong and a firing shape looks like a
   passing one:

   | Shape form | `sourceShape` | `path` / `message` | Assert on |
   |---|---|---|---|
   | `sh:or` guarded (`IRVE32AMonoShape`) | named shape | absent | `sourceShape` |
   | plain `sh:property` (`RCDSensitivityShape`) | blank node | present | `path` |

   See `repos/core/CLAUDE.md § SHACL activation pattern`.
4. **No false positives**: the compliant circuits produce no results.
5. **T-Box join (A-Box)**: every `dhc:` term you used resolves in
   `dhc-core.ttl`. Enforced by test; run it before believing a green result.
6. **T-Box join (shapes)**: `tests/cbox/nfc15100-2015.test.js` asserts every
   `sh:targetClass` and `dhc:` `sh:path` resolves.
7. **223P structural check** (free): validate against `Brick+extensions.ttl`'s
   own ~3237 NodeShapes — every `ElectricityBreaker` gets its electricity
   inlet+outlet checked, every `System` its `hasMember`.
8. `cd repos/core && npx vitest run`.

## Common pitfalls

Each of these has actually shipped in this repo. All fail **silently**.

- **Namespace without a trailing `#` or `/`.** `Namespace("https://digitalhome.cloud")`
  makes `DHC.Circuit` → `https://digitalhome.cloudCircuit`. Nothing joins the
  T-Box, the reasoner infers nothing, the script exits 0. Authoritative URIs:
  `https://digitalhome.cloud/ontology#`, `https://brickschema.org/schema/Brick#`,
  `https://w3id.org/rec#`, `http://data.ashrae.org/standard223#`,
  `http://example.org/…/` (trailing `/`).
- **Using a term that only exists in `schema/draft/`.** The A-Box parses, SHACL
  finds no focus nodes for it, everything looks green. `electrical-installation-house.ttl` shipped
  typing things as `dhc:RCD` / `dhc:Socket` / `dhc:BusBar` while all three were
  unpromoted. **Grep `dhc-core.ttl`, not the draft.**
- **Inventing a property name.** `dhc:cableSpec` was written into the demo; the
  real property is **`dhc:wiring`**. RDF accepts any predicate — nothing errors.
- **`rdfs:subClassOf` naming a class that doesn't exist.** The class inherits
  **nothing**, including the constraints its comment claims. The draft once said
  `s223:ElectricBreaker`, `s223:ElectricOutlet`, `s223:ElectricWire`; the real
  names are `s223:ElectricityBreaker`, `s223:ElectricityOutlet`, and — for a
  conductor — `s223:Connection`. `core-schema.test.js` now guards this.
- **`s223:Wire` does not exist.** `bricks-docs/modeling/connections.md` says it
  does. The doc is wrong — even the full 540 KB 223P has no Wire class.
  `s223:Connection` *is* the conductor ("pipe, duct, **conductor**, or free space").
- **`sh:hasValue` matches terms, not numbers.** `sh:hasValue 32` is
  `xsd:integer`; `dhc:ratedCurrent` is `xsd:decimal`, so the guard never matches
  and the whole shape becomes a permanent no-op. This killed
  `IRVE32AMonoShape`, `IRVE32ATriShape` and the BS 7671 ring-final shape. Write
  `sh:hasValue "32"^^xsd:decimal`, or prefer `sh:maxInclusive`.
- **`brick:Loop` is an HVAC fluid loop** (`Air_Loop`, `Water_Loop`). It is not
  an electrical circuit. Use `dhc:Circuit ⊑ s223:System`.
- **Entity properties are blank nodes**, never flat literals:
  `brick:ratedCurrentOutput [ brick:hasUnit unit:A ; brick:value "10"^^xsd:decimal ]`.
- **`s223:hasElectricalPhase` attaches to the *Medium***, not the Connection.
- **`s223:hasMember` takes Equipment or System only** — not Connections. Wiring
  attaches through connection points, not membership.
- **`s223:contains` is Equipment→Equipment / Space→Space** — *not*
  space→equipment. For "the board is in the GTL" use `rec:locatedIn` /
  `rec:isLocationOf`.
- **`brick:ratedApparentPower` is `property_of` Lighting_Equipment only** — not
  usable for a supply rating. Use `dhc:contractedPowerKVA`.
- **`brick:timeseries` does not exist** in this Brick build; external refs use
  `ref:hasExternalReference`.
- **Brick doc errors**: `Peak_Power_Demand_Sensor` → `brick:Peak_Demand_Sensor`;
  `brick:powerComplexity` → `brick:electricalComplexPower`.

## Residual-current protection (NF C 15-100)

Three shapes enforce it. **Every final circuit must list its differential in
`dhc:hasProtection`, alongside its own MCB** — the head-of-row RCD protects
several circuits, and that link is what makes the rule checkable:

```turtle
ex:circuit-ev a dhc:Circuit ;
    dhc:hasCircuitType dhc:CircuitType_IRVE ;
    dhc:hasProtection  ex:brk-ev, ex:rcd-main .   # MCB *and* the RCD

ex:rcd-main a dhc:RCD ;                           # ⊑ dhc:ProtectionDevice
    dhc:sensitivityMA "30"^^xsd:decimal ;         # decimal!
    dhc:rcdType       "A" .                       # AC | A | F | B
```

| Shape | Rule |
|---|---|
| `RCDSensitivityShape` | every `dhc:RCD` declares `sensitivityMA ≤ 30` |
| `CircuitRCDProtectionShape` | every `dhc:Circuit` has ≥1 `dhc:RCD` in `hasProtection` |
| `TypeARCDShape` | IRVE circuits need `rcdType` A or B — Type AC cannot detect the pulsating DC an on-board charger injects |

An `dhc:RCBO` satisfies all three for free (`RCBO ⊑ RCD ⊑ ProtectionDevice`).
When these shapes were added, four fixtures named `valid-fr-*` immediately
failed: they modelled no RCD at all. They had never been compliant — nothing
had checked. Expect the same of any A-Box written before this rule existed.

## Known gaps

- **`nfc14100` shapes carry no P3 guard** — they fire on every instance of their
  target class, so `EnergyMeterGovernanceShape` demands NF C 14-100 governance
  of any `dhc:EnergyMeter` in the graph. Safe only because profiles are selected
  per country from `cbox-manifest.json`.
- **Norm profiles are country-scoped only by which shapes file you load.**
  Nothing guards on `dhc:governedBy`; loading `bs7671.shapes.ttl` against a
  French home would apply UK rules.
- **The NF C 15-100:2024 shapes are ILLUSTRATIVE, not law.** Nobody has read the
  published text. `cbox/electrical/nfc15100-2024.shapes.ttl` encodes two
  plausible stand-ins (IRVE cross-section 10 → 16 mm²; energy storage coming
  into scope), marked `UNVERIFIED` on the header and every shape. They exist so
  the multi-edition machinery has something real to compute. Do not quote them
  and do not let them inform a real installation.
- **NF C 14-100's edition in force has no shapes.** `NormEdition_NFC14100_2008`
  implements `nfc14100-2008.shapes.ttl`; 2021 is `dhc:latestEdition` and
  implements nothing, so `ex:delivery` / `ex:meter` / `ex:agcp` come out
  green-but-ghosted — they pass what we hold and cannot be proven current.
  `tests/tbox/norm-editions.test.js` pins this as the one expected exception.

## Out of scope

- **T-Box authoring / promotion** → `dhc-ontology-explorer`.
- **Blockly blocks & toolbox** → `dhc-build-blockly-elements-for-*`.
- **Device catalogue / gateway discovery** → `dhc-device-autodiscovery`.
- **Telemetry & power analytics** — sensors, submeter hierarchies,
  `brick:electricalFlow` import/export, self-consumption. The design model is
  static topology; a deliberate MVP boundary.
- **Per-home tenant A-Box** — lives in S3 under the Designer. This repo carries
  exactly one reference A-Box (`repos/core/CLAUDE.md`).
