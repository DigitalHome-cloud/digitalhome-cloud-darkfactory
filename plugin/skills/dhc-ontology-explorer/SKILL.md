---
name: dhc-ontology-explorer
description: Designing, using, and extending repos/core/py-tools/ontology_explorer.py — the interactive T-Box curator that owns the four-file DHC schema split (Brick+extensions baseline, dhc-core.ttl, dhc-app-metadata.ttl, plus their drafts). Trigger this skill whenever the user is running the explorer (promote / delete / purge / annotation review), debugging its prompts, adding a new owl:AnnotationProperty to dhc-app-metadata.ttl, wiring a new prompt type (enum, boolean, language-tagged), or asking why a triple lands in dhc-core vs dhc-app-metadata. Also triggers for "promote a class", "review annotations interactively", "(D·A)" location flags, the APP_ANNOTATION_PREDS auto-discovery mechanism, and ENUM_CHOICES extensions. Do NOT trigger for SHACL norm authoring or A-Box instance work — those have their own skills.
---

# DHC Ontology Explorer

The ontology_explorer.py is the **only** sanctioned writer for the four DHC
T-Box files. Hand-editing `schema/tbox/dhc-core.ttl` or
`schema/tbox/dhc-app-metadata.ttl` bypasses the splitter and the deterministic
serializer; doing so will silently lose the view-banner structure on the next
explorer run. This skill exists to keep the explorer the single source of
truth for those writes, and to make extending it predictable.

## When to use this skill

Trigger on any of:

- "promote class X to tbox" / "delete dhc:Foo" / "purge dhc:Bar everywhere"
- "review annotations interactively" / "the explorer prompt for designView"
- adding a new `owl:AnnotationProperty` under `dhc:` (it must land in
  `dhc-app-metadata.ttl`, not `dhc-core.ttl`, to be auto-discovered)
- editing `repos/core/py-tools/ontology_explorer.py` itself — adding a new
  prompt type, a new range handler (boolean / integer / language-tagged
  string), or a new fixed-vocabulary enum
- explaining `(D·A)`, `(·CA)`, `(DCA)` location flags, or why a triple landed
  in core vs metadata
- diagnosing "my new annotation property doesn't show up in the prompt loop"

Do **not** trigger for: spatial-class authoring decisions
(`dhc-spatial-modeling`), SHACL norm shape work, or building Blockly artifacts
in the Modeler.
Do not use other .md files when using this skill

## The four-file split (load-bearing)

The explorer enforces a strict separation. Triples are routed by predicate:

| File                                      | Owns                                                                                                     | Written by explorer? |
|-------------------------------------------|----------------------------------------------------------------------------------------------------------|----------------------|
| `schema/tbox/Brick+extensions.ttl`        | Read-only baseline (Brick + REC + s223). Never touched.                                                  | **No**               |
| `schema/tbox/dhc-core.ttl`                | Domain triples: class declarations, `rdfs:domain` properties, R-Box axioms, enum instances.              | Yes (option [4])     |
| `schema/tbox/dhc-app-metadata.ttl`        | UI/UX overlay: every app annotation predicate + localized `rdfs:label`/`rdfs:comment` (`@de`, `@fr`).    | Yes (option [4])     |
| `schema/draft/dhc-core.ttl`               | Staging for in-progress domain triples. Shrinks on each promote.                                         | Yes (option [4]/[6]) |
| `schema/draft/dhc-app-metadata.ttl`       | Staging for in-progress annotations. Shrinks on each promote.                                            | Yes (option [4]/[6]) |

The header of the `schema/tbox/dhc-*.ttl files must contain
```turtle
@prefix sh:      <http://www.w3.org/ns/shacl#> .
@prefix brick:   <https://brickschema.org/schema/Brick#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix dhc:     <https://digitalhome.cloud/ontology#> .
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rec:     <https://w3id.org/rec#> .
@prefix s223:    <http://data.ashrae.org/standard223#> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
```

The annotation must be processed in the order they appear in the Application annotation property definitions section
```turtle
# ────────────────────────────────────────────────────────────
# § Application annotation property definitions
# ────────────────────────────────────────────────────────────
```        
        
## Key principle: auto-discovery

**No hardcoded annotation configuration in the python code.** Everything that
shapes the prompt — the predicate set, the ordering, the menu choices, the
default value, and any guard condition — is read from the TTL declaration of
each `owl:AnnotationProperty` in `dhc-app-metadata.ttl`. Adding or retuning
an annotation is a TTL change, never a python change.

The auto-discovery layer reads, in order:

| TTL on the predicate         | Drives                              | Implemented by                               |
|------------------------------|-------------------------------------|----------------------------------------------|
| `a owl:AnnotationProperty`   | Inclusion in the prompt loop        | `_refresh_app_annotation_preds`              |
| Position in `§ Application annotation property definitions` | Prompt order | `_annotation_decl_order_in_file` → `APP_ANNOTATION_ORDER` |
| `rdfs:label "…"@en`          | Prompt label                        | `_annotation_prompt_label`                   |
| `rdfs:range xsd:boolean`     | Boolean prompt path                 | `_annotation_range`                          |
| `sh:in (…)`                  | Static enum menu (left-to-right)    | `_annotation_in`                             |
| `sh:defaultValue …`          | Proposal when no current value      | `_annotation_default`                        |
| `sh:condition [ sh:property [ sh:path …; sh:hasValue … ] ]` | Conditional gating | `_annotation_condition` + `_condition_satisfied` |

Examples that exercise each:

```turtle
# Free-text annotation — no menu, no default, no guard.
dhc:blocklyCategory a owl:AnnotationProperty ;
    rdfs:label "Blockly Category"@en, "Blockly-Kategorie"@de, "Catégorie Blockly"@fr ;
    rdfs:comment "Optional override for the Blockly toolbox category name."@en .

# Static enum — sh:in fixes the menu, sh:defaultValue is proposed when unset.
dhc:appMode a owl:AnnotationProperty ;
    rdfs:label "App Mode"@en, "App-Modus"@de, "Mode d'application"@fr ;
    sh:defaultValue "private" ;
    sh:in ("private" "residential-pro" "tertiary" "industrial") .

# Boolean — rdfs:range triggers the 0/1 prompt; sh:defaultValue pre-fills.
dhc:isInstantiated a owl:AnnotationProperty ;
    rdfs:label "Is instantiated"@en, "Wird instanziiert"@de, "Est instancié"@fr ;
    rdfs:range xsd:boolean ;
    sh:defaultValue true .
```

### Prompt formats (deployed)

The prompt the curator sees is fully determined by what's declared on the
predicate. There are exactly three shapes:

**Static enum (`sh:in` present):**
```
Blockly Disposition  [current: —, default: block]
  1) block
  2) variable
  3) excluded
  Choice (1–3, k=keep, d=delete, blank=skip):
```
- `[default: …]` only appears when there is no current value AND
  `sh:defaultValue` is set.
- `k` or blank with no current value applies the default; otherwise blank skips.

**Boolean (`rdfs:range xsd:boolean`):**
```
Is instantiated  [current: —, default: true]
  0) false
  1) true
  Choice (0–1, k=keep, d=delete, blank=skip):
```
- Stores `Literal(True/False, datatype=xsd:boolean)` regardless of how the
  user typed `1` / `true` / `yes` / `t` / `y` (or the negative variants).
- Legacy untyped strings (`"1"`, `"true"`) are recognized when evaluating
  conditions, and rewritten as `xsd:boolean` the next time the class is
  promoted.

**Free text (default):**
```
Blockly Category  [current: —]
  (k=keep, d=delete, c=claude_to_do, blank=skip, or type new value):
```
- `c` injects the placeholder string `"claude_to_do"` for later AI completion.

## Conditional prompts (`sh:condition`)

A predicate can be silenced for classes that don't logically need it. Declare
a SHACL guard on the annotation property:

```turtle
dhc:blocklyBlockTemplate a owl:AnnotationProperty ;
    rdfs:label "Blockly Block Template"@en, "Blockly-Block-Vorlage"@de, "Modèle de bloc Blockly"@fr ;
    rdfs:comment "Pointer to a block template in dhc-blockly-blockTemplates.json."@en ;
    sh:condition [ sh:property [ sh:path dhc:isInstantiated ;
                                  sh:hasValue true ] ] .
```

When the explorer reaches this predicate for a class `cls`, the curator
evaluates the guard via `_condition_satisfied`:

1. Read `(sh:condition / sh:property)` → `(sh:path, sh:hasValue)`.
2. Find the **effective value** of `sh:path` on `cls`:
   - Look in `tbox_meta`, `drafts_core`, `drafts_meta` (in that order).
   - If nothing is asserted, fall back to the `sh:defaultValue` declared on
     the path predicate (one level — no recursion).
3. Compare via `_value_matches` (boolean-aware: `"1"` / `"true"` /
     `true^^xsd:boolean` all match the typed boolean `true`).

If the comparison succeeds, the predicate is prompted. Otherwise it is
silently skipped — no entry in the prompt loop at all.

**Concretely for `dhc:blocklyBlockTemplate`:**

| Class                   | `dhc:isInstantiated`           | Prompted? |
|-------------------------|--------------------------------|-----------|
| `dhc:DigitalHome`       | `"1"` (legacy untyped)         | yes       |
| `dhc:DetachedHouse`     | `true^^xsd:boolean`            | yes       |
| `rec:Bedroom`           | (unset → default = `true`)     | yes       |
| `rec:Apartment`         | `false^^xsd:boolean`           | **no**    |

The guard pattern supported today is exactly **one** `sh:property` with
`sh:path` + `sh:hasValue`. Anything more elaborate (`sh:and`, `sh:or`,
multi-property) degrades to "always prompt"; extend `_annotation_condition`
if a richer predicate language is needed.

## Dynamic choices from the class hierarchy (`dhc:choicesFrom`)

Some annotations need choices that depend on the focus class itself, not a
literal list. The canonical case is `dhc:blocklyBlockTemplate`: the value
must be a class drawn from `cls` plus its ancestors (a Blockly template
always reuses an upstream block layout). A static `sh:in` cannot express
this — the menu would have to enumerate every possible class in advance.

The convention going forward: keep `sh:in` for **fixed vocabularies** and
introduce a separate, DHC-specific predicate **`dhc:choicesFrom`** for
**dynamic, class-relative** scopes. The two are mutually exclusive on a
single annotation. The explorer dispatches on whichever is declared.

### Declaration (deployed)

Both meta-properties are declared in `schema/tbox/dhc-app-metadata.ttl` —
the `§ Application annotation property definitions` section — and flagged
with `dhc:isMetaProperty true` so the curator picks them up for routing
but **excludes them from the per-class prompt loop**:

```turtle
dhc:isMetaProperty a owl:AnnotationProperty ;
    rdfs:label "Is meta-property"@en, "Ist Meta-Eigenschaft"@de, "Est méta-propriété"@fr ;
    rdfs:comment "Marks an annotation property as a configuration knob for other annotation properties."@en ;
    rdfs:range xsd:boolean ;
    sh:defaultValue false ;
    dhc:isMetaProperty true .

dhc:choicesFrom a owl:AnnotationProperty ;
    rdfs:label "Choices from"@en, "Auswahl aus"@de, "Choix à partir de"@fr ;
    rdfs:comment "Dynamic enum source. Resolved against the focus class at prompt time."@en ;
    sh:in ( "selfAndAncestors" "ancestors" "selfAndDescendants" "descendants" ) ;
    dhc:isMetaProperty true .
```

Then attach `dhc:choicesFrom` to the dynamic-choices predicate, alongside any
`sh:condition`:

```turtle
dhc:blocklyBlockTemplate a owl:AnnotationProperty ;
    rdfs:label "Blockly Block Template"@en, "Blockly-Block-Vorlage"@de, "Modèle de bloc Blockly"@fr ;
    rdfs:comment "Pointer to a block template — resolved from the class's own hierarchy."@en ;
    sh:condition [ sh:property [ sh:hasValue true ;
                                  sh:path dhc:isInstantiated ] ] ;
    dhc:choicesFrom "selfAndAncestors" .
```

### Runtime semantics (deployed)

`enrich_external_class` dispatches in this priority order:

1. `sh:in` (static enum) — always wins if present.
2. `rdfs:range xsd:boolean` (boolean prompt).
3. `dhc:choicesFrom` (dynamic, class-relative enum) — used only when there
   is no `sh:in` and no boolean range.
4. Free text.

For (3), the chain is built per class. The traversal walks `rdfs:subClassOf`
in the configured direction, deduplicating by URI; blank nodes are skipped.

| Value                 | Choices for class `cls`                                              |
|-----------------------|---------------------------------------------------------------------|
| `selfAndAncestors`    | `[cls] + ancestors(cls, rdfs:subClassOf*)`, in subclass→superclass order |
| `ancestors`           | `ancestors(cls, rdfs:subClassOf*)` only                              |
| `selfAndDescendants`  | `[cls] + descendants(cls, rdfs:subClassOf*)`, in superclass→subclass order |
| `descendants`         | `descendants(cls, rdfs:subClassOf*)` only                            |

If the chain comes back empty (orphan class with no `rdfs:subClassOf`), the
branch falls through to the free-text prompt rather than crashing on an
empty menu.

Selection is stored as a CURIE-string `Literal` (matching the existing
`dhc:blocklyBlockTemplate "rec:Building"` pattern in the data) so the
Modeller pipeline that already consumes these strings keeps working.

**Live example** — `dhc:DetachedHouse` walked with `selfAndAncestors`:

```
dhc:DetachedHouse → rec:Building → rec:Architecture → rec:Space → rdfs:Resource
```

What the curator sees when prompting `dhc:DetachedHouse` for
`dhc:blocklyBlockTemplate`:

```
Blockly Block Template  [current: 'rec:Building']
  1) dhc:DetachedHouse
  2) rec:Building
  3) rec:Architecture
  4) rec:Space
  5) rdfs:Resource
  Choice (1–5, k=keep, d=delete, blank=skip):
```

For `rec:Apartment` (which has `dhc:isInstantiated false`) the same predicate
is **not** prompted at all because its `sh:condition` is unsatisfied — both
layers compose: the condition decides *whether* to prompt, the
`dhc:choicesFrom` decides *what* the menu contains. The condition is
evaluated first, so an unsatisfied guard short-circuits before any chain is
built.

### Implementation (deployed)

The wiring lives in `py-tools/ontology_explorer.py`:

- `_is_meta_property(pred, *graphs)` — checks `(pred, dhc:isMetaProperty, true)`.
  Used by `_refresh_app_annotation_preds` to filter `APP_ANNOTATION_ORDER`
  while leaving `APP_ANNOTATION_PREDS` (the routing set) untouched.
- `_annotation_choices_from(g, pred)` — returns the scope string from
  `dhc:choicesFrom`, or None. Validates against `_CHOICES_FROM_SCOPES`.
- `_build_choice_chain(cls, scope, g, sh)` — BFS through `rdfs:subClassOf`
  in the requested direction, returns `[(uri, curie_str), …]`.
- `enrich_external_class` — adds the dispatch branch *after* the `sh:in`
  check, *before* the boolean check; static `sh:in` still wins on
  predicates that have both declared.

Keep static `sh:in` for value vocabularies (`appMode`, `designView`,
`blocklyDisposition`, `blocklyFieldType`). Use `dhc:choicesFrom` only when
the menu is genuinely class-relative.

## Routing rules

**Routing rule** (`_is_app_annotation_triple` in the script):

- predicate ∈ `APP_ANNOTATION_PREDS` → `dhc-app-metadata.ttl`
- predicate is `rdfs:label` / `rdfs:comment` AND object is a Literal with
  `@de` or `@fr` → `dhc-app-metadata.ttl`
- everything else (incl. English labels/comments, `rdfs:subClassOf`,
  `rdfs:domain`, `rdfs:range`, `owl:Class`, SHACL on classes) → `dhc-core.ttl`

If you add a new annotation that should travel with the UI overlay, declare it
as `owl:AnnotationProperty` *in `dhc-app-metadata.ttl`* (or its draft) — the
declaration site is what makes it land in `APP_ANNOTATION_PREDS`.

`_refresh_app_annotation_preds(*meta_graphs)` scans the metadata graph(s) for
every `dhc:`-namespaced subject typed `owl:AnnotationProperty` and adds it to
the global `APP_ANNOTATION_PREDS` set. This runs after `load_graph()` and
after every `_reload()` (post-write reparse).

**Consequences:**

- Adding a new annotation property requires **no code change** — only a TTL
  declaration. The next explorer run picks it up.
- It must be declared in `dhc-app-metadata.ttl` (or its draft) — declaring it
  in `dhc-core.ttl` will route the *property's own* triples correctly but
  exclude it from the prompt loop and the annotation-routing rule.
- The property must be in the `dhc:` namespace; foreign annotation predicates
  are deliberately ignored.

Minimum declaration template for a new annotation property:

```turtle
dhc:myAnnotation a owl:AnnotationProperty ;
    rdfs:label "Meine Annotation"@de,
        "My annotation"@en,
        "Mon annotation"@fr ;
    rdfs:comment "What this annotation is for, in one sentence."@en .
```

Optional, but supported by the prompt machinery (all read from the TTL — no
python changes required to add or retune):

- `rdfs:range xsd:boolean` — triggers the boolean prompt (0 = false / 1 = true).
- `sh:defaultValue …` — pre-fills the proposal when no current value exists.
  Accepting it via `k` or blank stores a properly-typed literal (e.g.
  `Literal(True, datatype=xsd:boolean)` for booleans).
- `sh:in (…)` — static menu in left-to-right list order. Replaces the
  retired `ENUM_CHOICES` table; declarations now live entirely in the TTL.
- `sh:condition [ sh:property [ sh:path …; sh:hasValue … ] ]` — guards the
  prompt; predicate is silently skipped when the focus class doesn't satisfy.
- `dhc:choicesFrom "selfAndAncestors" | "ancestors" | …` — dynamic, class-
  relative menu (see *Dynamic choices from the class hierarchy* above). Use
  in place of `sh:in` when the choices depend on the focus class.


## Promote / delete / purge — what each does

| Option | Function                       | Source                       | Destination                                | Refused for                |
|--------|--------------------------------|------------------------------|--------------------------------------------|----------------------------|
| [4]    | `migrate_class` + `enrich_external_class` | `schema/draft/*`  | `schema/tbox/dhc-core.ttl` + `dhc-app-metadata.ttl` | —                          |
| [5]    | `delete_dhc_class`             | `schema/tbox/*`              | (removed)                                  | non-`dhc:` URIs            |
| [6]    | `purge_dhc_class_everywhere`   | `schema/tbox/*` + drafts     | (removed)                                  | non-`dhc:` URIs            |

For [4] specifically:

- DHC classes: class declaration + `rdfs:domain` properties + enum instances
  move from drafts → tbox. Domain triples go to `dhc-core.ttl`,
  app annotations and `@de`/`@fr` labels to `dhc-app-metadata.ttl`.
- External classes (`rec:`, `brick:`, `s223:`): only annotations are written,
  into `dhc-app-metadata.ttl`. The class definition stays upstream.

Always re-serializes and re-parses afterwards (`_reload()`), so the in-memory
graph stays in sync with disk.

## Scripted curation — `--promote` / `--purge` (use these, not piped stdin)

The menu is for humans. **Agents and scripts use the flags.**

```bash
python3 ontology_explorer.py --promote dhc:Circuit
python3 ontology_explorer.py --promote dhc:governedBy    # subjects, not just classes
python3 ontology_explorer.py --purge   dhc:Norm_BS7671
python3 ontology_explorer.py --purge dhc:ratedCurrent --promote dhc:ratedCurrent
```

They are a thin wrapper over the same `promote_dhc_class()` /
`purge_dhc_class_everywhere()` / `_serialize_all()` / `_reload()` — one writer,
identical output either way.

- **Repeatable; purges run before promotes.** Correcting a property's
  definition is purge → re-draft → promote, so that order is the useful default.
- **Exit codes are real**: `0` success or already-promoted (idempotent), `2`
  not-found or refused (non-`dhc:` URI).
- **Subjects, not just classes.** `--promote dhc:governedBy` works because
  `promote_dhc_class()` is subject-based. This matters: `dhc:governedBy`
  deliberately has no `rdfs:domain`, so **no class promotion would ever reach
  it** — nor would `dhc:powerRating`, whose domain is the external
  `brick:Equipment`.
- **Annotation review is skipped** (equivalent to answering `n`). Existing
  annotations still move; *adding or changing* one is a human judgement call —
  use the menu.

**Do not drive the menu by piping stdin.** It looks like it works and fails
badly: a prompt count that shifts by one silently desynchronises the stream so
the wrong answer lands on the wrong question, and on EOF `_ask()` returns `""`,
the class prompt falls back to `last`, and the loop **never exits**.

Rationale: `repos/core/doc/adr-0001-ontology-tooling.md`.

## Reconciliation — `--scan` / `--massupdate` (bulk annotation)

The overlay must stay aligned with the entities the models use: every in-scope
class/property carries a `dhc:designView` + `@de` + `@fr`. `--promote` moves a
*subject's own* triples draft→tbox; it does not tell you *which* entities are
under-annotated, and it cannot annotate an external class at all (that is
menu-only `enrich_external_class`). These two flags close that gap — the scripted
twin of `enrich_external_class`, driven by a CSV instead of the prompt loop.

```bash
python3 ontology_explorer.py --scan                     # coverage report → console
python3 ontology_explorer.py --scan --csv gaps.csv      # …as Cat,Entity,Missing
python3 ontology_explorer.py --scan --template fill.csv # …as a fill-in E,P,V skeleton
# edit fill.csv (fill the V column), then:
python3 ontology_explorer.py --massupdate fill.csv
```

**Scope** (`_inscope_entities`): every `rdf:type` object across `schema/abox/**`
(recursive, includes the reference examples) ∪ every dhc-core class/property/enum
∪ every subject already in the overlay — restricted to the four DHC vocabularies
(`dhc`/`brick`/`s223`/`rec`) **and** actually defined in the loaded T-Box. That
last filter is not optional: `--massupdate` resolves an entity via
`resolve_name`, which requires it to exist, so a reference class our
`Brick+extensions.ttl` doesn't carry (`brick:Boiler` used in a demo,
`brick:*Shape`, a versioned/`bacnet:` namespace) is out of reach and correctly
excluded. Coverage is checked against the **committed** tbox metadata, never the
gitignored `schema/draft/` — an annotation that only lives in draft doesn't ship.

**The CSV is `E,P,V` (one triple per row), UNQUOTED:**

| V form | means | example |
|---|---|---|
| `text@de` / `text@fr` | a language-tagged label/comment | `Wechselrichter@de` |
| bare word | a plain literal (enum value) | `electrical` |
| `true` / `false` | a boolean annotation | `true` |
| `prefix:local` | an object-valued annotation | `dhc:CircuitType_IRVE` |
| `__delete__` / `__delete__@fr` | remove the annotation (all / that language) | clears a stray `claude_to_do` |

Do **not** quote label text — CSV owns the `"` character, so `"text"@fr` gets
mangled into a plain literal that loses its language tag and mis-routes. Bare
`text@fr` round-trips through CSV cleanly (commas and all).

**Guarantees.** `--massupdate` is **transactional**: it validates every row
first (predicate must be an annotation property, value must satisfy the shape's
`sh:in`/boolean range, entity must resolve) and writes **nothing** if any row is
bad — fix the CSV and re-run. Upserts are **language-aware** (setting `@de` never
touches `@en`/`@fr`), so it is idempotent: re-applying an unchanged CSV is a
byte-identical no-op. Routing mirrors `enrich_external_class` — external subjects
go entirely to `dhc-app-metadata.ttl`; a `dhc:` subject's `@de`/`@fr`/annotations
go there while its `@en`/domain triples stay in `dhc-core.ttl`.

`tests/tbox/annotation-coverage.test.js` guards the result: no `claude_to_do`
survives, and every in-scope entity is fully annotated. Add an A-Box example that
introduces a new class and that test goes red until it is skinned — which is what
makes the iterative modelling loop safe.

## The interactive review (`enrich_external_class`)

For each candidate predicate, the prompt offers:

- `k` — keep current. If no current value but `sh:defaultValue` exists, the
  default is applied (boolean only, today). Otherwise: move existing draft
  triples to `dhc-app-metadata.ttl`.
- `d` — delete from drafts AND tbox.
- `c` — placeholder string `claude_to_do` (free-text prompts only; suppressed
  for booleans and enums).
- blank — skip (no change). Boolean exception: blank with no current and a
  defined `sh:defaultValue` applies the default.
- new value — replaces any existing. Booleans land as
  `Literal(<bool>, datatype=xsd:boolean)`; localized label/comment as
  `Literal(<str>, lang=<lang>)`; everything else as plain `Literal(<str>)`.

Candidates are gathered as:

1. **Fixed slots** — every predicate in `APP_ANNOTATION_PREDS` (sorted by
   `rdfs:label@en` for deterministic UX), plus the four localized
   label/comment slots.
2. **Extras** — any other predicate already attached to the class across
   tbox/draft graphs, so re-promoting after a reload always re-surfaces every
   annotation that's currently set.

## Location flags

The `(DCA)`-style suffix after a class name (option [1]/[3]) indicates which
files declare the class:

- `D` — declared in `schema/draft/dhc-core.ttl` or `schema/draft/dhc-app-metadata.ttl`
- `C` — declared in `schema/tbox/dhc-core.ttl`
- `A` — declared in `schema/tbox/dhc-app-metadata.ttl`

Healthy steady states:

- `(D··)` — drafted, not yet promoted.
- `(·CA)` — fully promoted DHC class.
- `(··A)` — external class (REC/Brick/s223) with DHC UI overlay only.
- `(·C·)` — domain-only DHC class with no UI annotations yet (rare;
  usually a migration in progress).

Pathological:

- `(DC·)` / `(D·A)` after a successful promote — means draft-removal failed.
  Reload and re-run the migration; if it persists, hand-fix the draft file.

## Files this skill touches

| Path                                          | Read | Write |
|-----------------------------------------------|------|-------|
| `repos/core/py-tools/ontology_explorer.py`    | yes  | yes — when extending the explorer |
| `repos/core/py-tools/onto_explorer.conf`      | yes  | rarely |
| `schema/tbox/Brick+extensions.ttl`            | yes  | **never** |
| `schema/tbox/dhc-core.ttl`                    | yes  | via explorer only |
| `schema/tbox/dhc-app-metadata.ttl`            | yes  | via explorer only — except declaring new `owl:AnnotationProperty` |
| `schema/draft/dhc-core.ttl`                   | yes  | yes — manual drafting |
| `schema/draft/dhc-app-metadata.ttl`           | yes  | yes — manual drafting |
| `tests/tbox/core-schema.test.js`              | yes  | extend on T-Box additions |

## Verification protocol

After any explorer change (script edit OR a curation run):

1. `python ontology_explorer.py` loads cleanly — every file's triple count
   prints, no parse error.
2. Option [3] on a representative class shows the expected predicates with
   the right `range`/`source`/`type`.
3. The location flag `(D··)` → `(·CA)` transition fires on promote, with no
   leftover draft triples for that subject.
4. `git diff schema/tbox/*.ttl` after promote shows: new triples under the
   correct `# VIEW: <view>` banner, alphabetical within the banner, and no
   spurious reordering of unrelated subjects (the structured serializer is
   deterministic — diffs should be local).
5. `npm test` from `repos/core/` passes.

When extending the explorer with a new prompt type or annotation, add a tiny
rdflib smoke test that constructs a graph with the new property, calls the
new helper directly, and asserts the resulting literal's `datatype` /
`language` is what you expect.

## Out of scope

- C-Box / SHACL norm shapes — the explorer doesn't write `schema/cbox/*`.
- A-Box instance authoring — Designer's responsibility, S3-stored.
- Block generation / ontology-graph JSON — Modeler's responsibility.
- The Blockly toolbox structure — driven by `dhc:designView` values, but
  consumed downstream, not produced here.

## Common pitfalls

- **New `owl:AnnotationProperty` declared in `dhc-core.ttl`** — won't appear
  in the prompt loop. Move the declaration to `dhc-app-metadata.ttl`.
- **Hand-edit of `schema/tbox/*.ttl`** — survives until the next promote, then
  the structured serializer rewrites the file in canonical order and your
  edit may end up in the wrong banner. Always go through the explorer.
- **Boolean stored as plain `"1"` / `"true"`** — legacy untyped literals from
  before the boolean prompt existed. They get rewritten as
  `"true"^^xsd:boolean` the next time that class goes through option [4].
- **Promote left a `(D·A)` flag** — the draft-removal step failed; check that
  the draft file's permissions allow writes and re-run.
- **`@en` label landed in `dhc-app-metadata.ttl`** — only `@de`/`@fr` labels
  are routed there. Untagged and `@en` labels stay in `dhc-core.ttl`.
