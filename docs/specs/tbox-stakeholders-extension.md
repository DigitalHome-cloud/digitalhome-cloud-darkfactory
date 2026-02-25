Specification for a T-BOX extension: People, Organizations, Roles (no code)
1) Design goals

Support design → build → operate stakeholder modeling with minimal ontology footprint.

Allow multiple people/organizations to hold multiple roles simultaneously.

Make roles contextual (per RealEstate, per Project, per Equipment/System).

Enable future linkage to identity/access-control systems without embedding IAM into the ontology.

2) New conceptual module

Create a conceptual “module” (can still live in the same TTL for now, but conceptually separate):

Module name: Stakeholders & Governance
Recommended designView value: governance (new toolbox category), analogous to your existing view pattern.

3) Core classes (minimal set)

Agent (abstract)

Meaning: something that can hold responsibility or perform actions.

Expected subclasses: Person, Organization.

Person

Natural person. Avoid storing sensitive personal data; focus on identifiers/display names.

Organization

Company, association, utility, contractor, architect office, property manager, etc.

Role

A type of role (Owner, Operator, Installer, Maintainer, Occupant, Maître d’Ouvrage…).

RoleAssignment (key class)

Represents: “Agent X plays Role Y in Context Z (optionally during time window T).”

This is what prevents brittle modeling like Owner ⊑ Person.

Project (optional but recommended)

If you want to distinguish engineering/design/build projects from the “as-operated” asset twin.

Helps capture maître d’ouvrage vs maître d’œuvre, contractors, etc.

4) Core object properties

Role assignment pattern

assignedAgent : RoleAssignment → Agent

assignedRole : RoleAssignment → Role

assignmentContext : RoleAssignment → (RealEstate OR Project OR Equipment OR System)

You can define a union-like concept “ContextEntity” (abstract) to avoid overcomplicated ranges.

Responsibility & ownership (direct shortcuts)

owns : Agent → (RealEstate OR Equipment)

operates : Agent → (RealEstate OR System OR Equipment)

maintains : Agent → (Equipment OR System)

installedBy : (Equipment OR System) → Agent

These “shortcuts” are optional but very useful for queries; they can be derived from RoleAssignment if you later add reasoning rules.

5) Core data properties (keep lean)

For Agent

name (you already have dhc:name globally usable)

externalId (string): link to your IAM / CRM / ERP identity key (Cognito subject, SAP BP, etc.)

For RoleAssignment

validFrom (dateTime, optional)

validTo (dateTime, optional)

status (planned/active/ended, optional)

6) Role catalog (controlled vocabulary)

Define a controlled set of Role individuals or Role subclasses (your choice). For MVP, treat them as instances of Role (simpler to extend without changing the schema):

Recommended starter roles:

Owner (proprietaire)

Maître d’ouvrage (client/sponsor)

ProjectManager (chef de projet)

Designer/Architect

Installer

Maintainer

Operator

Occupant/User

SafetyResponsible (nice for NF C 15-100 compliance workflows later)

7) Modeling rules / constraints (spec-level)

A RoleAssignment MUST have exactly one assignedAgent, one assignedRole, and one assignmentContext.

assignmentContext MUST be one of: RealEstate, Project, Equipment, or “System” (HVACSystem/PlumbingSystem/NetworkSegment/etc.). Your current T-BOX already has good candidates for those targets.

Avoid encoding personal sensitive attributes (DOB, address, etc.) in the ontology. Keep it referential.

8) How this plugs into your pipeline (spec)

Designer produces A-BOX:

Always create at least: Owner, Operator role assignments at the RealEstate level.

Optionally: Installer/Maintainer role assignments at Equipment/System level (if known during design).

Builder enriches A-BOX:

Adds installedBy, commissioning responsibility, and references to Inventory items (serial numbers, product SKUs) without changing the T-BOX’s conceptual separation.

Operations:

Uses RoleAssignments to drive access/permissions and to route alerts/tickets (e.g., HVAC alarm → Maintainer organization).

