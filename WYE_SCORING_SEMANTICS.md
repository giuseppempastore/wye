# WYE — Scientific Scoring Semantic Charter

## Status and authority

This document is the canonical semantic contract for Phase 7. Terms such as
MUST, MUST NOT, SHOULD and MAY are normative architecture requirements.

Status:

```text
architecture: defined and frozen by Phase 7.0.1
scientific method: requires external domain review
numeric scoring: not defined
```

This charter does not convert Phase 6 evidence into a score. It defines what a
future protocol is allowed to mean and the conditions under which a result must
remain unavailable.

## Core invariants

```text
scientific evidence != scientific scoring
AI != scientific source of truth
absence of evidence != evidence of danger
hazard != exposure != risk
confidence != safety
evidence quality != source prestige
missing evidence != negative evidence
```

A conclusion MUST be scoped to a declared scientific question. Evidence that is
valid for one endpoint, population, route or scenario MUST NOT silently support a
different question.

## Semantic charter

### Scientific evidence

- **Definition:** a source-derived assessment, finding or other scientific record
  whose identity, content and provenance are preserved.
- **Represents:** what a source reported, within a specific dataset release and
  ingestion interpretation.
- **Does not represent:** a WYE judgement, source endorsement, hazard ranking,
  risk estimate or product score.
- **Minimum inputs:** source, dataset, release, successful ingestion run,
  assessment/finding identity and traceable raw artifact or explicit legacy
  provenance.
- **Available when:** the record is readable and its provenance is sufficient for
  the intended question.
- **Unavailable/non-computable when:** identity or provenance is insufficient to
  establish what was reported and how it entered WYE.

### Evidence line

- **Definition:** one or more dependent evidence records grouped because they
  support the same scientific proposition through the same underlying study,
  assessment or source-native lineage.
- **Represents:** the unit that may be appraised and integrated without counting
  dependent copies as independent corroboration.
- **Does not represent:** one database row, one provider, one citation count or an
  automatic vote.
- **Minimum inputs:** scientific question, lineage/dependency identity, endpoint
  and relevant context.
- **Available when:** dependencies and the proposition addressed by the line can
  be identified.
- **Unavailable when:** records cannot be separated into scientifically meaningful
  or dependency-aware units.

### Evidence quality

- **Definition:** the degree to which the methods, conduct, reporting and data
  integrity of an evidence line support correct use for its stated purpose.
- **Represents:** protocol-specific appraisal of reliability and limitations.
- **Does not represent:** source prestige, regulatory authority, publication count
  or confidence that a product is safe.
- **Minimum inputs:** evidence type, study/assessment design information,
  provenance and quality criteria declared by the protocol.
- **Available when:** enough methodological information exists to apply the
  declared criteria.
- **Unavailable when:** quality-critical metadata are absent; the protocol MUST
  record `quality_not_assessable` rather than invent a grade.

### Relevance

- **Definition:** the contribution an evidence line could make to the declared
  question if the evidence were correct.
- **Represents:** correspondence to endpoint, population/species, route, duration,
  dose/scenario, substance form and assessment purpose.
- **Does not represent:** quality, truth, source authority or general importance.
- **Minimum inputs:** explicit scientific question and enough evidence context to
  compare it with that question.
- **Available when:** the comparison can be performed deterministically or by a
  governed scientific review.
- **Unavailable when:** question or context is under-specified.

### Applicability

- **Definition:** whether a relevant conclusion can be transferred to the exact
  WYE target context under explicit assumptions.
- **Represents:** fitness for use in the target population, product domain, route,
  conditions and jurisdiction where applicable.
- **Does not represent:** a claim that the evidence is universally valid.
- **Minimum inputs:** relevance appraisal, target context and transfer assumptions.
- **Available when:** assumptions are explicit and permitted by the protocol.
- **Unavailable when:** transfer would require an unapproved scientific inference.

### Hazard

- **Definition:** an agent or condition with the potential to cause an adverse
  effect.
- **Represents:** potential for harm under some conditions.
- **Does not represent:** likelihood of harm in a product, actual exposure,
  consumer risk or product unsafety.
- **Minimum inputs:** identified substance/agent and evidence supporting an
  adverse endpoint.
- **Available when:** eligible evidence supports hazard identification for the
  declared endpoint.
- **Unavailable when:** identity is unresolved, evidence is ineligible or the
  endpoint cannot be interpreted.

### Hazard characterisation

- **Definition:** qualitative or quantitative characterisation of the nature and,
  where supportable, dose-response/severity of an adverse effect.
- **Represents:** endpoint-specific properties and conditions of the hazard.
- **Does not represent:** exposure or risk for a product/population.
- **Minimum inputs:** hazard identification plus endpoint, dose/value and context
  adequate for the protocol.
- **Available when:** eligible evidence supports the declared characterisation.
- **Unavailable when:** evidence supports only identification or lacks critical
  endpoint/context information.

### Exposure

- **Definition:** amount or concentration reaching a target over a stated
  frequency, duration and route for a defined population/scenario.
- **Represents:** a measured or modelled contact/intake scenario with uncertainty.
- **Does not represent:** ingredient presence, ingredient-list order or hazard.
- **Minimum inputs:** substance concentration or justified proxy, amount used or
  consumed, frequency, duration, route, target population and conditions of use.
- **Available when:** inputs and assumptions satisfy a domain-specific exposure
  protocol.
- **Unavailable when:** critical quantities or scenario fields are missing;
  worst-case values MUST NOT be silently assumed.

### Risk

- **Definition:** a qualitative or quantitative characterisation of the
  likelihood and severity of adverse effects for a defined population under a
  defined exposure scenario, including uncertainty.
- **Represents:** the result of combining compatible hazard and exposure
  characterisation.
- **Does not represent:** hazard alone, evidence count, source prestige or a
  context-free property of an ingredient/product.
- **Minimum inputs:** compatible hazard characterisation, exposure assessment,
  population, scenario, endpoint and uncertainty analysis.
- **Available when:** a validated risk protocol declares all required inputs
  sufficient.
- **Unavailable when:** exposure is missing/incompatible or the hazard basis is
  insufficient/conflicting beyond the protocol's resolution policy.

### Uncertainty

- **Definition:** limitations in knowledge that affect the answer to the declared
  question.
- **Represents:** identified doubt about inputs, evidence, mapping, methods,
  assumptions or conclusions.
- **Does not represent:** variability itself, evidence quality alone or a penalty.
- **Minimum inputs:** a question and systematic examination of relevant inputs and
  methods.
- **Available when:** sources and effects can at least be described.
- **Unavailable:** never by default; a protocol MUST state if uncertainty could
  not be adequately characterised.

### Confidence

- **Definition:** degree of confidence in a precisely stated WYE conclusion after
  considering evidence, mappings, coverage, consistency and uncertainty.
- **Represents:** support for the conclusion as worded and scoped.
- **Does not represent:** probability that a product is safe, product quality or
  absence of hazard.
- **Minimum inputs:** conclusion, evidence synthesis and uncertainty account.
- **Available when:** the protocol defines how confidence is reached and reports
  its basis.
- **Unavailable when:** the conclusion is not well-defined or supporting
  dimensions cannot be appraised. It MUST NOT be fabricated as a default number.

### Evidence synthesis

- **Definition:** deterministic and/or governed integration of eligible evidence
  lines for one declared question.
- **Represents:** included/excluded evidence, appraisal, consistency, conflicts,
  uncertainties and a scoped conclusion.
- **Does not represent:** a generic average across findings or endpoints.
- **Minimum inputs:** protocol version, evidence snapshot, eligibility decisions,
  evidence lines and conflict policy.
- **Available when:** minimum completeness is met or a protocol permits a partial
  synthesis with explicit limitations.
- **Unavailable when:** no eligible evidence, unresolved identity or an unresolved
  conflict blocks the question.

### Substance assessment

- **Definition:** collection of endpoint-specific syntheses for one canonical
  substance at an as-of state.
- **Represents:** a multidimensional evidence/hazard profile with status per
  endpoint.
- **Does not represent:** a single inherent risk score or every possible form and
  use of the substance.
- **Minimum inputs:** active canonical substance, eligible identity, snapshot and
  one or more endpoint questions.
- **Available when:** at least one endpoint can be assessed; unavailable endpoints
  remain explicit.
- **Unavailable when:** substance identity is unresolved or no endpoint can reach
  an allowed partial status.

### Ingredient projection

- **Definition:** protocol-controlled projection of a substance assessment onto a
  WYE ingredient through an accepted, temporally valid relationship.
- **Represents:** which substance conclusions are applicable to the ingredient and
  under what relationship assumptions.
- **Does not represent:** proof of concentration, exposure or risk merely because a
  relationship exists.
- **Minimum inputs:** ingredient identity, historical mapping state, relationship
  type, substance assessment and applicability rules.
- **Available when:** the relationship type permits the requested projection and
  required composition/presence information exists.
- **Unavailable when:** mapping is not accepted/as-of valid or the relationship
  lacks data required by the requested conclusion.

### Product assessment

- **Definition:** domain-specific integration of eligible ingredient projections
  and, only where required and sufficient, product/exposure information.
- **Represents:** a conclusion for a defined product, population, use and protocol.
- **Does not represent:** universal safety, medical advice or a context-free health
  ranking.
- **Minimum inputs:** canonical product state, accepted product-ingredient
  mappings, domain protocol and all inputs required for its claim.
- **Available when:** the protocol's completeness criteria are met. A partial
  hazard summary may be available while risk remains unavailable.
- **Unavailable when:** identity, mapping, domain or exposure gaps block the claim.

### WYE score

- **Definition:** a future protocol-defined representation of a declared construct.
  Phase 7.0 does not define that construct numerically.
- **Represents:** only what a published, validated scoring protocol explicitly
  states.
- **Does not represent by default:** percentage of safety, probability of harm,
  percentage of healthiness, medical suitability or regulatory approval.
- **Minimum inputs:** validated intended use, measurable construct, calibrated and
  validated protocol, complete input contract, uncertainty/explainability and
  communication validation.
- **Available when:** a future published protocol satisfies those requirements.
- **Unavailable now:** the first Phase 7 protocol MUST NOT emit a numeric WYE
  score.

## Intended Use & Claims Matrix

`Supported now` means supported by the consolidated Phase 6 architecture, not
that a Phase 7 presentation feature already exists.

| Capability or claim | Classification | Permitted interpretation / condition |
|---|---|---|
| Evidence availability | supported now | WYE may state which versioned evidence is linked to an accepted substance identity and show provenance |
| Hazard identification | possible with additional data | Requires endpoint eligibility/synthesis protocol and scientific review; evidence presence alone is insufficient |
| Hazard profile | possible with additional data | First recommended protocol; multidimensional and endpoint-specific, without product-risk claims |
| Exposure assessment | possible with additional data | Requires concentration, use/intake, frequency, duration, route, population and uncertainty |
| Risk estimate | possible with additional data | Requires validated compatible hazard and exposure protocols; otherwise `risk_not_computable` |
| Allergen assessment | requires separate protocol | Must separate declared presence, cross-contact, individual susceptibility and emergency/medical guidance |
| Nutrition assessment | requires separate protocol | Requires validated category, reference basis, quantities and public-health method; not derived from toxicology |
| Generic health score | not scientifically justified | No single construct or data basis currently justifies it |
| Consumer comparison | requires separate protocol | Only comparable under the same domain, question, input completeness, protocol version and communication rules |
| Cosmetic assessment | requires separate protocol | Route, concentration, formulation and use conditions differ from food |
| Supplement assessment | requires separate protocol | Dose, regimen, bioavailability and target population are essential |
| Consumer preference | out of scope | Preference is not scientific hazard/risk and must not alter scientific conclusions |

Mandatory claim boundaries:

```text
hazard evidence available != product unsafe
no eligible evidence != no hazard
missing exposure → risk_not_computable
missing exposure != assume worst case
regulatory record != universal approval for every use
```

## Quality, confidence and uncertainty framework

The following dimensions MUST remain separately inspectable:

| Dimension | Subject | Required output |
|---|---|---|
| Product → ingredient mapping confidence | label identity resolution | method, status, confidence basis and review provenance |
| Ingredient → substance mapping confidence | scientific identity bridge | relationship, status, as-of validity, method and review provenance |
| Evidence quality | individual evidence line | criteria met, limitations and `not_assessable` where necessary |
| Evidence relevance | evidence versus question | endpoint/population/route/duration/scenario correspondence |
| Cross-evidence consistency | lines addressing the same question | concordant, apparent conflict, context-resolved or unresolved conflict |
| Endpoint coverage | requested assessment space | assessed, partial, missing and inapplicable endpoints |
| Exposure uncertainty | exposure inputs/model | sources, range/direction where supportable and impact |
| Model uncertainty | synthesis/projection/risk method | assumptions, structural alternatives and impact |
| Final conclusion confidence | exact conclusion | confidence basis and limiting dimensions |

No architecture component may compress these into a single value before a
protocol has scientifically justified the loss of information. Legacy confidence
or evidence-level fields are not substitutes for this framework.

Every uncertainty record MUST describe:

- source/cause;
- affected input, step or conclusion;
- direction, when known;
- potential impact;
- reducibility and what data/action could reduce it;
- effect on the conclusion, including whether it blocks or qualifies it.

Confidence language MUST attach to a precise conclusion. It MUST NOT be rendered
as `probability the product is safe` unless a future probabilistic risk protocol
has explicitly defined and validated that quantity.

## Missing Evidence Policy

The states below are semantic results, not numeric inputs. None receives an
automatic penalty.

Legend: **blocks** means the requested level cannot produce a complete
conclusion; **conditional** means a narrower partial conclusion may continue.

| State | Meaning and trigger | Substance assessment | Ingredient projection | Product assessment | User-facing requirement | Forbidden inference |
|---|---|---|---|---|---|---|
| `sufficient` | Protocol completeness met for the exact question | permitted | permitted if mapping permits | permitted if product/domain inputs also suffice | Scope and supporting evidence | “safe in every context” |
| `insufficient_evidence` | Eligible evidence exists but cannot support the requested conclusion | blocks requested endpoint; partial profile allowed | conditional on narrower supported endpoints | blocks claims depending on missing endpoint | “Evidence is insufficient for this question” plus gap | danger or safety |
| `no_eligible_evidence` | Snapshot contains no evidence satisfying eligibility | blocks requested endpoint | blocks that endpoint projection | blocks dependent claim | “No eligible evidence found under this protocol” | no hazard, danger or provider absence |
| `unresolved_identity` | Substance or bridge identity is unresolved/ambiguous | blocks affected substance | blocks | blocks affected ingredient contribution; other ingredients may remain visible | Identity requires review | treat candidates as equivalent |
| `missing_exposure` | Hazard may be characterised but critical exposure inputs are absent | does not block hazard profile | does not block hazard-only projection | blocks exposure/risk; hazard summary may remain | “Risk cannot be computed because exposure is missing” | worst case or zero exposure |
| `conflicting_evidence` | True unresolved conflict remains for the same question | blocks definitive endpoint conclusion unless protocol permits explicit conflict conclusion | projects only conflict status | blocks dependent definitive claim; partial profile allowed | Show both lines, scope and uncertainty | average, majority vote or hidden precedence |
| `not_applicable` | Question/endpoint does not apply to the entity or domain | not an assessed endpoint | no projection for that question | excluded from completeness denominator only if protocol declared | “Not applicable” with reason | safe, missing or negative |
| `stale_evidence` | Evidence falls outside freshness/current policy without explicit withdrawal | blocks current-mode conclusion; historical as-of may remain valid | conditional in matching historical mode | blocks current claim; historical result retained | Show cutoff and newer data requirement | withdrawn, false or superseded |

The presentation layer MUST distinguish unavailable, not applicable, conflicting
and sufficient results. It MUST NOT coerce them to zero, neutral, low risk or a
fallback score.

## Aggregation specification

Canonical pipeline:

```text
evidence snapshot
→ evidence selection
→ endpoint-specific synthesis
→ substance assessment
→ ingredient projection
→ product assessment
→ presentation
```

### Substance level

- Evidence is grouped by a declared question and dependency-aware evidence line.
- Different endpoints remain separate result components.
- Different populations, routes, durations, substance forms or scenarios remain
  separate unless an approved applicability rule connects them.
- Evidence counts are descriptive and MUST NOT act as weights.
- A substance assessment is a profile of endpoint results and statuses, not an
  average.
- Conflict and uncertainty remain attached to the affected endpoint.

### Ingredient level

Only mappings that are `accepted`, temporally valid for the execution's as-of
date and connected to an active substance are eligible.

| Relationship | Permitted semantic projection | Required limitation |
|---|---|---|
| `represents` | Direct hazard/evidence projection MAY occur when identity scope and substance form match | Does not establish product exposure |
| `equivalent_to` | Direct projection MAY occur only when the accepted equivalence covers the protocol question | Equivalence MUST NOT be broadened beyond its reviewed rationale |
| `contains` | Presence-aware evidence linkage MAY occur when actual presence is established | Risk or dose projection requires composition/concentration |
| `mixture_component` | Component evidence MAY be listed as conditional | Component fraction, mixture behaviour and interactions are not assumed |
| `derived_from` | Provenance/derivation relationship MAY be shown | Does not prove that the source substance remains present or at what dose |

Mapping confidence does not override relationship semantics. A high-confidence
`derived_from` relationship still does not establish presence.

### Product level

- Only accepted product → ingredient mappings from the selected historical state
  are eligible.
- `position_in_list != concentration`.
- Presence of an ingredient is not a dose.
- Unknown concentration blocks concentration-dependent projection.
- A hazard profile MAY be summarised without exposure only if it is clearly named
  and cannot be mistaken for product risk.
- Quantitative product risk requires sufficient concentration, amount, frequency,
  duration, route, target population, conditions of use and compatible hazard
  characterisation.
- Missing inputs remain explicit; no worst-case or neutral defaults are allowed.
- Cross-substance/mixture effects require a separate validated method.

## Data Gap Matrix

Status meanings:

- `available now`: structured in the consolidated repository for at least the
  validated Phase 6 traversal;
- `partially available`: present for some records/providers or not normalised
  enough for general use;
- `missing`: no adequate canonical field/model in the current product-to-evidence
  path;
- `derivable only with assumptions`: a proxy could be guessed but is not evidence;
- `must never be assumed`: inference would change the scientific meaning.

| Information | Current status | Repository reality | Consequence |
|---|---|---|---|
| Ingredient identity | available now | Canonical ingredient plus accepted product mapping and review history | Enables ingredient traversal; unresolved mappings remain blocking |
| Substance identity | available now | Active substances, versioned namespaces, verified identifiers and review/materialisation | Enables substance linkage for resolved identities |
| Relationship semantics | available now | Accepted temporal N:M bridge with explicit relationship type | Enables relationship-aware projection, not concentration inference |
| Assessment provenance | available now | Source → dataset → release → artifact → run → assessment → finding | Enables audit, snapshot and replay design |
| Endpoint | partially available | QPS endpoints and OpenFoodTox/IUCLID endpoint text are stored but not a universal controlled ontology | Endpoint-specific synthesis requires protocol mapping/review |
| Value | partially available | Numeric/text values depend on source and finding | Some hazard characterisation possible; not universally comparable |
| Unit | partially available | Present for applicable OpenFoodTox findings, absent/not applicable elsewhere | Unit-aware normalisation required before quantitative use |
| Species/population | partially available | OpenFoodTox population context may contain species; QPS is taxonomic/regulatory context | Human applicability cannot be assumed |
| Sex | partially available | Preserved for some OpenFoodTox studies | Sex-specific relevance may be unavailable |
| Route | partially available | Preserved for some studies in population context/raw payload | Missing route blocks route-specific transfer |
| Study duration | partially available | May exist in raw payload but is not consistently normalised | Duration-specific synthesis may require parser/schema work |
| Ingredient concentration | missing | Ingredient list stores presence/order, not quantity | Blocks concentration-dependent ingredient/product assessment |
| Substance concentration | missing | Relationship does not carry product-specific composition | Blocks substance exposure and product risk |
| Serving size | partially available | Nutrition facts has a free-text serving size; not substance-specific exposure | Insufficient alone for exposure |
| Consumed amount | missing | No validated consumption amount tied to product/substance | Blocks dietary exposure |
| Frequency | missing | No canonical consumption/use frequency | Blocks chronic/acute scenario estimation |
| Exposure duration | missing | No product-use duration | Blocks duration-matched risk characterisation |
| Target population | missing | No assessment execution population contract; user profiles are legacy/general | Blocks population-specific risk claims |
| Preparation/use conditions | missing | No canonical preparation, dilution or application context | Blocks context-specific exposure |

Additional forbidden assumptions:

| Candidate inference | Classification | Rule |
|---|---|---|
| Ingredient order as exact concentration | must never be assumed | Order may be descriptive only |
| Unknown concentration as zero | must never be assumed | Produces false absence of exposure |
| Unknown concentration as worst case | must never be assumed | Risk-management scenario requires explicit approved protocol |
| `derived_from` as current presence | must never be assumed | Requires evidence of residual presence |
| One finding as universal substance conclusion | must never be assumed | Endpoint/context synthesis is required |
| Newest release as automatic scientific supersession | must never be assumed | Supersession/correction must be explicit or protocol-governed |
| Multiple rows as independent corroboration | derivable only with assumptions | Dependency handling must identify the underlying evidence line |

### Gap impact by assessment level

| Assessment level | Minimum currently plausible | Principal blockers |
|---|---|---|
| Hazard synthesis | Endpoint-specific synthesis for records with sufficient identity, context and quality metadata | Endpoint ontology, heterogeneous context, quality criteria and scientific review |
| Ingredient projection | Hazard/evidence projection through `represents` or scoped `equivalent_to` mappings | Unresolved mapping, relationship semantics, substance form and composition |
| Exposure assessment | Not generally computable | Concentrations, amount, frequency, duration, population and conditions |
| Risk characterisation | Not generally computable | Compatible hazard characterisation plus exposure and uncertainty |
| Product-level risk | Not currently justified | Ingredient/substance concentration and complete exposure scenario |

## Scientific reference frame

Protocol-specific scientific review should use primary methodological guidance
appropriate to the domain. The architecture is aligned with, but does not claim
certification by:

- Codex Alimentarius, *Working Principles for Risk Analysis*;
- EFSA, *Guidance on uncertainty analysis in scientific assessments*;
- EFSA, *Guidance on the use of the weight of evidence approach in scientific
  assessments*;
- WHO/IPCS guidance on uncertainty in hazard and exposure assessment.

These references guide terminology and review. They do not supply hidden WYE
weights, thresholds or formulas.
