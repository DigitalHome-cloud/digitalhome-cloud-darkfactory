
# DHC Modeler Ontology Block Design – Summary

## Purpose
The DHC Modeler enables visual creation of ontology schema modules (TTL files) that define:
- Core DigitalHome ontology (`dhc-core.ttl`)
- Electrical domain ontologies (`dhc-core-electrical.ttl`, `dhc-core-electrical-breakers.ttl`, templates)

These are later used by the DHC SmartHome Designer to create actual smart home instances.

---

## Modeling Flow
1. **Ontology modeling stage (Modeler)**  
   Output: `.ttl` ontology modules.

2. **Design stage (SmartHome Designer)**  
   Input: ontology; Output: house/instance `.ttl`.

---

## Core Elements as Blockly Blocks

### 1. Ontology Module Block
Represents a `.ttl` file. Contains:
- Base IRI
- Prefixes
- Statement area for definition blocks

### 2. OWL:Thing Block
Represents the top-level class.

### 3. ClassDefinition Block
Defines an OWL Class with:
- Label
- IRI
- Comment
- SubClassOf stack

### 4. ObjectPropertyDefinition Block
OWL ObjectProperty with:
- Label, IRI, comment
- Domain class
- Range class

### 5. DataPropertyDefinition Block
OWL DatatypeProperty with:
- Label, IRI, comment
- Domain class
- Datatype range

### 6. EquipmentType Blocks
Specialized classes representing device types.

---

## Electrical Domain Blocks

### CircuitBreakerType Definition Block
Fields:
- Rated current
- Curve type (B/C/D)
- Poles
- Standard compliance

### PanelTemplate Block
Contains PanelSlot blocks:
- Slot position
- Allowed types
- Default breaker

### CircuitTemplate Block
Represents reusable circuit archetypes.

---

## Example Mappings

### A. RealEstate (Core)
TTL:
```
dhc:RealEstate a owl:Class ;
  rdfs:subClassOf owl:Thing ;
  rdfs:label "RealEstate"@en .
```

Blocks:
- OntologyModule
  - OWL:Thing
  - ClassDefinition(RealEstate)
    - SubClassOfRef(owl:Thing)

### B. Equipment & EquipmentType
TTL:
```
dhc:EquipmentType rdfs:subClassOf dhc:Equipment .
```

Blocks:
- Class(Equipment)
- Class(EquipmentType)
  - SubClassOfRef(dhc:Equipment)

### C. Breaker Type B16A
TTL:
```
dhc:B16A
  rdfs:subClassOf dhc:CircuitBreakerType ;
  dhc:ratedCurrent "16"^^xsd:integer ;
  dhc:curveType "B" ;
  dhc:numberOfPoles "1"^^xsd:integer .
```

Blocks:
- ClassDefinition(B16A)
  - SubClassOfRef(CircuitBreakerType)
  - DataPropertyUses (ratedCurrent, curveType, poles)

### D. PanelTemplate
TTL:
```
dhc:NF_Main a dhc:PanelTemplate ;
  dhc:hasSlot [
    dhc:position "1" ;
    dhc:allowedType dhc:CircuitBreakerType ;
    dhc:defaultBreaker dhc:B16A
  ] .
```

Blocks:
- PanelTemplate(NF_Main)
  - PanelSlot(1, allowedType=CircuitBreakerType, default=B16A)

---

## Result
This block language fully represents all elements in:
- `dhc-core.ttl`
- `dhc-core-electrical.ttl`
- `dhc-core-electrical-breakers.ttl`
- `dhc-core-electrical-templates.ttl`
