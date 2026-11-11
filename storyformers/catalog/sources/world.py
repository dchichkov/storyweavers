"""256 physical, spatial, event, and causal candidate triples.

These are authored hypotheses. The native subset recognizes local constructions;
it does not execute their alleged physical effects. Richer relations have explicit
parser/state/graph adapter requirements rather than fictitious matcher operators.
"""

import re

from ..schema import Catalog, alt, example, gap, neuron, one_of, present, ref, seq, tok


SOURCES = ("local.storyformer", "local.attribute_grammar", "local.head_catalog", "local.world", "local.event_lines")


def _bundle(value, entity="e1", scope="s1"):
    return {"entity_id": entity, "scope_id": scope, "assertion_status": "candidate", "value": value}


def _contrast(catalog, context, why):
    catalog.grammars[-1]["examples"].append({**example(context, {}, why), "polarity": "contrastive"})


def _copula(catalog, family, rows):
    """Finite lexical transformations of a fully visible, bound copular clause."""
    assert len(rows) in (16, 32)
    for key, description, noun, alternatives in rows:
        mapping = dict(alternatives)
        adjective, meaning = next(iter(mapping.items()))
        subject = {"token": noun, "pos": "n", "entity_id": "e1", "scope_id": "s1", "assertion_status": "asserted"}
        positive = [subject, {"token": "was", "pos": "v", "scope_id": "s1", "factuality": "asserted", "grammatical_subject_id": "e1"},
                    {"token": adjective, "pos": "adj", "lemma": adjective, "scope_id": "s1"}]
        negative = [subject, {"token": "might", "pos": "v"}, {"token": "be", "pos": "v"},
                    {"token": adjective, "pos": "adj", "lemma": adjective}]
        payload = {"entity_id": ref("subject.entity_id"), "scope_id": ref("subject.scope_id"),
                   "assertion_status": "candidate", "value": {"$lookup": {"table": "interpretations", "key": ref("query.lemma")}}}
        grammar = neuron(seq(gap(), tok("subject", entity_id=present(), scope_id=present(), assertion_status="asserted"),
                             tok(token="was", pos="v", factuality="asserted", scope_id=ref("subject.scope_id"),
                                 grammatical_subject_id=ref("subject.entity_id")),
                             tok(pos="adj", lemma=one_of(*mapping), scope_id=ref("subject.scope_id"))),
                         {key: payload}, tables={"interpretations": mapping})
        catalog.add(key, "object", description, family, value=_bundle(meaning), scope="entity_in_explicit_copular_clause",
                    head=f"interpret_{key}_copula", function=f"At a visible adjective after a bound subject and 'was', propose {description.lower()}",
                    mechanism="bound_copular_clause_then_finite_semantic_lookup", native=grammar,
                    positive=example(positive, {key: _bundle(meaning)}, "The adjective is available now and the physical referent is explicitly bound."),
                    negative=example(negative, {}, "A modal clause is outside this asserted-copula recognizer; do not turn possibility into a current state."),
                    sources=SOURCES, evidence="candidate_interpretation",
                    notes="Payload shape: entity_id, scope_id, assertion_status='candidate', value. The causal input must already bind grammatical_subject_id; adjacency alone is not subject evidence. This recognizes a candidate reading of a small construction, not a parser, latest-state resolver or physical commit. Values: " + ", ".join(sorted(set(mapping.values()))) + ".")
        mismatch = [{"token": "image", "entity_id": "e2", "scope_id": "s1"}, {"token": "of"},
                    subject, {**positive[1], "grammatical_subject_id": "e2"}, positive[2]]
        _contrast(catalog, mismatch, "The nearby entity is inside the actual subject's modifier; the copula binds e2, so its property cannot be attached to e1.")
        excluded = {"object_fill_state": "half-full", "object_corrosion_state": "rust-free",
                    "material_composition": "metallic", "material_absorbency": "waterproof"}.get(key)
        if excluded:
            words = re.findall(r"[A-Za-z]+|[^\w\s]", excluded)
            records = [{"token": word, "lemma": word, "pos": "punct" if word == "-" else "adj", "scope_id": "s1"}
                       for word in words]
            _contrast(catalog, [*positive[:2], *records],
                      "This meaning or multi-token form is outside the finite single-adjective mapping; absence of a match leaves it unknown.")


ENTITY_WORDS = set("lily ben nia omar cup box crate door key table shelf shed garden gate window rope ladder bridge jar cloth hammer nail needle spoon lantern book coat map boat river bank path road tunnel cave wall floor roof tree stone cart basket bag pouch chest apple water bread wheel engine bell lock bottle parcel board ball branch motor battery plank cloth sack glass ice fire paint seed plant oven room bird dog cat hands handle lid fence hole passage island beach hill corner rail padlock curtain net hook cable switch shelter sheet scissors screw drawer recipient librarian jun cord glue".split())


def _fixture(text, target):
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+|[^\w\s]", text)
    def base(word):
        return word.lower().removesuffix("'s")
    identities = {target.lower(): "e1"}
    for word in words:
        lower = base(word)
        if lower in ENTITY_WORDS and lower not in identities:
            identities[lower] = f"e{len(identities) + 1}"
    if target.lower() not in {base(word) for word in words}:
        raise ValueError(f"missing target {target}: {text}")
    rows, seen = [], set()
    next_identity = len(identities) + 1
    for index, word in enumerate(words):
        row = {"token": word, "scope_id": "s1"}
        if base(word) in identities:
            entity_id = identities[base(word)]
            # Explicitly contrastive demonstration mentions denote different
            # objects. Do not let convenience noun matching erase that contrast.
            if base(word) in seen and any(base(w) in {"different", "another", "replacement"} for w in words[max(0, index - 2):index]):
                entity_id = f"e{next_identity}"
                next_identity += 1
            row.update(entity_id=entity_id, pos="n")
            seen.add(base(word))
        rows.append(row)
    # A new anaphoric mention supplies the head's explicit current focus. This
    # binding is an input fixture, not a claim this catalog solved coreference.
    rows.append({"token": "It", "pos": "pron", "entity_id": "e1", "scope_id": "s1"})
    return rows, identities


def _references(value, identities):
    if isinstance(value, str) and value.startswith("@"):
        return identities[value[1:].lower()]
    if isinstance(value, dict):
        return {key: _references(item, identities) for key, item in value.items()}
    if isinstance(value, list):
        return [_references(item, identities) for item in value]
    return value


def _contracts(catalog, family, rows):
    """Rows specify distinct transformations and contrastive observed prefixes."""
    for key, description, target, value, text, contrast, algorithm, capability in rows:
        positive, identities = _fixture(text, target)
        negative, negative_ids = _fixture(contrast, target)
        expected = _bundle(_references(value, identities))
        contrast_expected = ({key: _bundle(_references(CONTRAST_VALUES[key], negative_ids))}
                             if key in CONTRAST_VALUES else {})
        requirements = ["typed_prefix_semantics", "entity_event_scope_binding", capability]
        contract = {
            "match": {
                "query": {"bind": "focus", "from": "last_visible_record", "require": ["entity_id", "scope_id"]},
                "sources": {"bind": "evidence", "from": "earlier_visible_records", "parse_as": "typed_propositions_and_events"},
                "selection": {"operation": algorithm, "focus_entity": "$focus.entity_id", "scope": "$focus.scope_id", "definition": description},
            },
            "guards": [
                {"check": "all_support_precedes_or_equals_query"},
                {"check": "entity_and_event_references_resolve_in_prefix"},
                {"check": "preserve_assertion_negation_modality_and_viewpoint_scopes"},
                {"check": "unknown_or_ambiguous_required_binding_abstains_or_returns_correlated_alternatives"},
                {"check": "validate_domain_rule", "rule": description},
                {"check": "do_not_commit_world_state_from_a_prediction"},
            ],
            "emit": {key: {"entity_id": "$focus.entity_id", "scope_id": "$focus.scope_id", "assertion_status": "candidate",
                           "value": {"derive": algorithm, "from": "$evidence"}}},
            "trace_metadata": {"provenance": "$selected_source_spans_and_event_ids"},
        }
        catalog.add(key, "object", description, family, value=expected, scope="focused_entity_and_bound_event_or_relation",
                    head=f"derive_{key}", function=description, mechanism=algorithm, contract=contract,
                    requires=requirements, reads=("token", "entity_id", "scope_id", "assertion_status", "factuality", "event_id", "attributes"),
                    positive=example(positive, {key: expected}, "The prefix supplies the named relation and its required supporting facts; the current mention focuses the bound entity."),
                    negative=example(negative, contrast_expected,
                        "The changed premise supports the contrasting value rather than the positive reading." if contrast_expected else
                        "The changed premise removes support for this projection; the available prefix does not establish its required scoped binding."),
                    sources=SOURCES, evidence="derived_hypothesis",
                    notes="Adapter contract, not executable native DSL. Payload is a correlated entity/scope/value hypothesis; selected source/event provenance belongs to trace metadata, not the residual payload. Example IDs are local bindings; input pronoun resolution is supplied. A rejected positive reading may leave a different valid interpretation.")


SPATIAL = [
    ("spatial_configuration", "Recover a typed qualitative relation between a figure and its explicitly named landmark.", "cup", {"relation": "above", "landmark": "@box"}, "The cup was above the box.", "The cup might someday be above the box.", "bind_figure_relation_landmark", "scoped_relation_interpretation"),
    ("spatial_reference_object", "Select the landmark of a spatial expression without confusing it with the located figure.", "cup", {"landmark": "@table"}, "The cup stood beside the table.", "The table stood beside a cup in a picture.", "resolve_spatial_landmark_role", "dependency_role_resolution"),
    ("spatial_frame_kind", "Identify whether a stated direction uses an intrinsic, observer-relative, or geographical frame.", "box", "observer_relative", "The box was to Lily's left from her viewpoint.", "The box was left behind by Lily.", "classify_reference_frame", "reference_frame_interpretation"),
    ("spatial_deictic_center", "Bind the perceiver or location relative to which here and there are interpreted.", "box", {"center": "@lily", "deictic": "near_speaker"}, "Lily pointed to the box beside her and said it was here.", "Lily repeated an old sentence about a box being here.", "resolve_deictic_anchor", "quotation_and_deixis_binding"),
    ("spatial_axis", "Recover the spatial axis relevant to an explicit relation while retaining its landmark.", "cup", {"axis": "vertical", "landmark": "@shelf"}, "The cup was directly below the shelf.", "The cup was discussed below the shelf entry in a list.", "classify_spatial_axis", "literal_figurative_scope_resolution"),
    ("spatial_absolute_direction", "Represent an explicitly grounded cardinal bearing rather than interpreting any directional word as geography.", "shed", {"bearing": "north", "landmark": "@garden"}, "On the map the shed was north of the garden.", "The shed belonged to a person named North in the garden.", "bind_cardinal_relation", "geographical_frame_binding"),
    ("spatial_distance_band", "Infer a qualitative distance band only from stated spatial distance evidence.", "box", {"band": "near", "landmark": "@lily"}, "The box was close beside Lily.", "The box was close to being finished by Lily.", "interpret_literal_distance", "spatial_sense_disambiguation"),
    ("spatial_orientation", "Bind an object's orientation to an explicitly supplied frame or supporting surface.", "bottle", {"orientation": "inverted", "landmark": "@table"}, "The bottle stood upside down on the table.", "Lily drew an upside down bottle on paper beside the table.", "resolve_object_orientation", "depiction_scope_resolution"),
    ("spatial_relative_bearing", "Compute relative bearing after resolving which observer supplies left and right.", "box", {"relation": "left", "observer": "@lily"}, "Facing the gate, Lily saw the box on her left.", "Lily heard that someone left the box by the gate.", "observer_relative_bearing", "oriented_frame_transform"),
    ("spatial_contact", "Distinguish physical touching from proximity using explicit contact evidence.", "cup", {"touches": "@box"}, "The cup's side touched the box.", "The cup stood near the box without touching it.", "resolve_contact_relation", "contact_relation_model"),
    ("spatial_support", "Identify the supporting carrier of a figure and retain the direction of support.", "cup", {"supported_by": "@table"}, "The table held the cup above the floor.", "The cup hung above the table on a cord.", "resolve_support_direction", "support_relation_model"),
    ("spatial_overlap", "Determine whether explicitly described physical regions overlap rather than merely touch.", "sheet", {"overlaps": "@cloth"}, "Part of the sheet lay across part of the cloth.", "The sheet and cloth touched only at their edges.", "region_overlap_test", "region_geometry"),
    ("spatial_adjacency", "Identify neighboring regions that share a boundary under the stated layout.", "garden", {"adjacent_to": "@shed"}, "The garden border met the shed's wall.", "A road separated the garden from the shed.", "shared_boundary_test", "topological_layout_graph"),
    ("spatial_separation", "Retrieve an explicit separator between two regions rather than inferring separation from distinct names.", "garden", {"separator": "@fence", "other_region": "@road"}, "A fence separated the garden from the road.", "A fence lay flat inside the garden near the road.", "bind_separating_barrier", "spatial_partition_model"),
    ("spatial_alignment", "Compare axes or edges only when the prefix supplies their shared alignment frame.", "board", {"aligned_with": "@rail"}, "The board ran parallel to the rail.", "The board crossed the rail at a right angle.", "axis_alignment_comparison", "oriented_geometry"),
    ("spatial_symmetry", "Recognize a stated mirrored layout around an identified axis or center.", "gate", {"relation": "symmetric", "axis": "center_line"}, "Two equal lamps stood at equal distances on either side of the gate.", "Two lamps stood together on the same side of the gate.", "paired_layout_symmetry", "paired_spatial_comparison"),
    ("spatial_region", "Locate a figure within an explicitly named subregion of a larger place while retaining its semantic world.", "cup", {"region": "corner", "landmark": "@table", "world": "actual"}, "The cup stood in the far corner of the table.", "Lily imagined the cup in the far corner of the table.", "bind_subregion_location", "region_part_binding"),
    ("spatial_boundary", "Identify the boundary of an occupied region separately from the region interior.", "garden", {"boundary": "@fence"}, "The fence enclosed the edge of the garden.", "A small fence lay in the middle of the garden.", "identify_region_boundary", "region_boundary_graph"),
    ("spatial_side", "Resolve inside versus outside relative to a named boundary without collapsing it into distance.", "box", {"side": "outside", "boundary": "@gate"}, "The box was outside the closed gate.", "The box was near the gate but its side was unknown.", "classify_boundary_side", "boundary_orientation_model"),
    ("spatial_level", "Resolve a stated vertical building or terrain level without treating list order as height.", "box", {"level": "upper_floor"}, "The box was on the upper floor of the shed.", "The box was the upper entry in the shed inventory.", "resolve_physical_level", "physical_level_interpretation"),
    ("spatial_topology", "Classify disconnection, contact, or inclusion for two explicit physical regions.", "garden", {"relation": "disconnected", "other_region": "@road"}, "The garden and road had a gap between them and shared no edge.", "The garden directly bordered the road.", "classify_topological_relation", "region_topology"),
    ("spatial_viewpoint", "Identify the physical observation point that licenses a described layout.", "garden", {"observer": "@lily", "vantage": "@roof"}, "From the roof Lily looked down over the garden.", "Lily remembered an old view of the garden from the roof.", "bind_current_spatial_vantage", "viewpoint_and_event_scope"),
    ("spatial_perspective_transform", "Translate a relative side between explicitly opposed observer orientations.", "box", {"lily_side": "left", "ben_side": "right"}, "Lily and Ben faced each other with the box on Lily's left and Ben's right.", "Lily and Ben faced the same direction with the box on Lily's left.", "transform_opposed_observer_sides", "coordinate_frame_transform"),
    ("spatial_extent", "Recover a figure's occupied region rather than treating its anchor point as its whole extent.", "sheet", {"covers": "whole_table"}, "The sheet covered the table from edge to edge.", "One corner of the sheet rested on the table.", "resolve_occupied_extent", "extent_geometry"),
    ("spatial_landmark_chain", "Compose stated spatial links through intermediate landmarks while preserving direction and uncertainty.", "cup", {"chain": ["@box", "@table"]}, "The cup was beside the box, and that box was on the table.", "The cup was beside one box; a different box was on the table.", "join_landmark_relations", "entity_join_and_spatial_composition"),
    ("spatial_co_location", "Compare current locations of two entities after processing relevant changes.", "cup", {"co_located_with": "@box", "location": "@shed"}, "The cup and box were both in the shed.", "The cup left the shed before the box arrived there.", "resolve_current_colocation", "state_chronology"),
    ("spatial_facing_target", "Bind the entity or region toward which a carrier is explicitly oriented.", "lily", {"faces": "@gate"}, "Lily turned until she faced the gate.", "Lily turned away from the gate.", "resolve_facing_target", "orientation_state_update"),
    ("spatial_surroundings", "Collect explicitly surrounding landmarks without treating a mention list as a layout.", "shed", {"surrounded_by": ["@garden", "@river"]}, "The garden lay on one side of the shed and the river on the other.", "A book mentioned the shed, a garden, and a river without their locations.", "collect_bound_surrounding_regions", "spatial_set_aggregation"),
    ("spatial_occlusion", "Identify an intervening object that blocks a specified sightline.", "box", {"occluder": "@curtain", "observer": "@lily"}, "The opaque curtain stood between Lily and the box, hiding the box.", "The transparent curtain stood between Lily and the visible box.", "resolve_sightline_occluder", "visibility_geometry"),
    ("spatial_ground_plane", "Bind the supporting reference plane for height and orientation descriptions.", "box", {"plane": "@floor"}, "The box rested flat on the floor and its height was measured from that floor.", "A picture of the box lay flat on the floor.", "bind_physical_ground_plane", "reference_plane_interpretation"),
    ("spatial_anchor_stability", "Determine whether a location description uses a moving or stationary landmark.", "box", {"anchor": "@cart", "anchor_moving": True}, "The box stayed on the cart while the cart rolled.", "The cart stayed still while Lily carried the box away.", "track_landmark_motion_status", "relative_motion_state"),
    ("spatial_layout_consistency", "Detect an explicit spatial relation cycle that contradicts the same frame and interval.", "box", {"conflict": "strict_vertical_cycle"}, "At one moment the box was above the cup and the cup was above that same box.", "The box was above the cup before Lily reversed their positions.", "check_same_scope_relation_cycle", "qualitative_constraint_solver"),
]


def _motion_native(catalog):
    family = "world.motion"
    actor = {"token": "Lily", "pos": "n", "entity_id": "e1", "scope_id": "s1", "assertion_status": "asserted"}
    # Four role retrieval constructions differ in the selected path component.
    rows = [
        ("motion_source", "The departure landmark of an explicitly stated movement.", "left", "leave:depart_place", [], "shed", "source", "leave:quit_employment"),
        ("motion_destination", "The destination landmark reached in an explicitly stated entry.", "entered", "enter:move_into_place", [], "shed", "destination", "enter:join_competition"),
        ("motion_waypoint", "An intermediate landmark traversed without treating it as the final destination.", "passed", "pass:move_through_place", ["through"], "tunnel", "waypoint", "pass:undergo_process"),
        ("motion_route", "The route entity followed by a moving actor, distinct from its endpoint.", "followed", "follow:move_along_route", [], "path", "route", "follow:obey_instruction"),
    ]
    for key, desc, verb, sense, middle, landmark, role, other_sense in rows:
        action = {"token": verb, "pos": "v", "event_id": "ev2", "event_type": "move", "actor_id": "e1",
                  "lexical_sense_id": sense, "scope_id": "s1", "factuality": "asserted"}
        place = {"token": landmark, "pos": "n", "entity_id": "e2", "scope_id": "s1", "event_id": "ev2", "role": "location"}
        prefix = [actor, action, *({"token": word} for word in middle), {"token": "the"}, place]
        payload = {"entity_id": ref("actor.entity_id"), "scope_id": ref("actor.scope_id"), "assertion_status": "candidate",
                   "value": {"role": role, "landmark_id": ref("query.entity_id"), "event_id": ref("action.event_id")}}
        pattern = seq(gap(), tok("actor", entity_id=present(), scope_id=present(), assertion_status="asserted"),
                      tok("action", token=verb, pos="v", event_id=present(), event_type="move", actor_id=ref("actor.entity_id"),
                          lexical_sense_id=sense, factuality="asserted", scope_id=ref("actor.scope_id")),
                      *(tok(token=word) for word in middle), tok(token="the"),
                      tok(entity_id=present(), scope_id=ref("actor.scope_id"), event_id=ref("action.event_id"), role="location"))
        expected = _bundle({"role": role, "landmark_id": "e2", "event_id": "ev2"})
        contrast = [dict(row) for row in prefix]
        contrast[1]["factuality"] = "desired"
        catalog.add(key, "object", desc, family, value=expected, scope="explicit_movement_event",
                    head=f"bind_{key}", function=desc, mechanism="local_movement_construction_and_role_copy", native=neuron(pattern, {key: payload}),
                    positive=example(prefix, {key: expected}, "Causal inputs supply the actor and selected motion sense; the final landmark binds to the same movement event."),
                    negative=example(contrast, {}, "A desired movement is not supplied to this asserted-event recognizer."), sources=SOURCES,
                    notes="This is a correlated movement-role hypothesis, not a state commit. Actor identity, event_type=move, selected lexical sense and landmark event/role bindings are supplied causal annotations, not solved by adjacency. Sense labels are authored conventions, not WordNet IDs. No omitted route or endpoint is inferred.")
        _contrast(catalog, [{"token": "Ben", "entity_id": "e3", "scope_id": "s1"}, {"token": "beside"},
                            prefix[0], {**action, "actor_id": "e3"}, *prefix[2:]],
                  "The predicate's actor is the earlier Ben/e3; nearby Lily/e1 cannot receive his movement role.")
        _contrast(catalog, [prefix[0], {**action, "lexical_sense_id": other_sense}, *prefix[2:]], "An explicitly incompatible lexical sense blocks the physical movement projection.")
        _contrast(catalog, [*prefix[:-1], {**place, "event_id": "ev3"}], "The landmark belongs to a different event and cannot fill this movement's path role.")
    for key, desc, surface, readings in [
        ("motion_manner", "Manner licensed by the selected physical movement sense, retaining its actor and trigger event.", "walked", [("walked", "walk:move_on_foot", "walking"), ("ran", "run:move_on_foot", "running"), ("crawled", "crawl:move_on_limbs", "crawling"), ("hopped", "hop:move_by_jumps", "hopping")]),
        ("motion_medium", "Medium licensed by a selected movement sense; flight or burrowing alone does not fix the medium.", "swam", [("swam", "swim:move_through_liquid", "liquid"), ("flew", "fly:move_through_air", "air"), ("burrowed", "burrow:dig_through_ground", "ground")]),
        ("motion_path_shape", "Path-shape evidence from a selected physical movement sense, without inventing coordinates or distance.", "zigzagged", [("zigzagged", "zigzag:move_in_alternating_directions", "zigzag"), ("circled", "circle:move_on_circular_path", "circular"), ("spiraled", "spiral:move_on_spiral_path", "spiral")]),
        ("motion_direction", "A selected physical movement sense's qualitative vertical direction.", "ascended", [("ascended", "ascend:move_upward", "upward"), ("descended", "descend:move_downward", "downward")]),
    ]:
        mapping = {sense: meaning for _, sense, meaning in readings}
        selected_sense = next(sense for word, sense, _ in readings if word == surface)
        action = {"token": surface, "pos": "v", "event_id": "ev2", "event_type": "move", "actor_id": "e1",
                  "lexical_sense_id": selected_sense, "scope_id": "s1", "factuality": "asserted"}
        payload = {"entity_id": ref("actor.entity_id"), "scope_id": ref("actor.scope_id"), "assertion_status": "candidate",
                   "value": {"event_id": ref("query.event_id"), "interpretation": {"$lookup": {"table": "meanings", "key": ref("query.lexical_sense_id")}}}}
        native = neuron(seq(gap(), tok("actor", entity_id=present(), scope_id=present(), assertion_status="asserted"),
                            alt(*(tok(pos="v", token=word, lexical_sense_id=sense, event_id=present(), event_type="move",
                                      actor_id=ref("actor.entity_id"), factuality="asserted", scope_id=ref("actor.scope_id"))
                                  for word, sense, _ in readings))),
                        {key: payload}, tables={"meanings": mapping})
        expected = _bundle({"event_id": "ev2", "interpretation": mapping[selected_sense]})
        catalog.add(key, "object", desc, family, value=expected, scope="lexical_movement_event_candidate",
                    head=f"interpret_{key}", function=desc, mechanism="bound_event_then_finite_motion_semantics", native=native,
                    positive=example([actor, action], {key: expected}, "The causal input already binds the actor and selected movement sense; the finite lookup supplies its semantic component."),
                    negative=example([actor, {**action, "factuality": "hypothetical"}], {}, "The hypothetical branch is outside this asserted-event candidate recognizer."),
                    sources=SOURCES, notes="Actor, move event type and lexical sense are supplied causal annotations. Authored sense labels name selected readings, not WordNet IDs; the matcher does not disambiguate words. Literal flight through space or burrowing through blankets does not match the air/ground sense. No endpoint, speed, intention, or world transition is inferred.")
        _contrast(catalog, [{"token": "Ben", "entity_id": "e2", "scope_id": "s1"}, {"token": "beside"},
                            actor, {**action, "actor_id": "e2"}],
                  "The predicate belongs to Ben/e2, not nearby Lily/e1; adjacency cannot transfer its movement properties.")
        _contrast(catalog, [actor, {**action, "lexical_sense_id": "unresolved_or_incompatible_sense"}], "An unresolved or incompatible sense cannot inherit the finite physical interpretation.")
        if key == "motion_medium":
            _contrast(catalog, [actor, {**action, "token": "flew", "lexical_sense_id": "fly:move_through_space"}], "Physical flight in space does not establish air as its medium.")
            _contrast(catalog, [actor, {**action, "token": "burrowed", "lexical_sense_id": "burrow:move_through_blankets"}], "Literal burrowing through blankets does not establish ground as its medium.")


MOTION_ADAPTERS = [
    ("motion_vehicle", "Bind a vehicle that transports the moving entity, distinct from an independently moving nearby vehicle.", "lily", {"vehicle": "@boat"}, "Lily rode across the river in the boat.", "Lily walked beside the boat as it crossed the river.", "resolve_vehicle_role", "motion_role_parser"),
    ("motion_carrier", "Identify the carrier responsible for transporting a passive physical object.", "box", {"carrier": "@lily"}, "Lily carried the box into the shed.", "Lily watched Ben carry the box into the shed.", "resolve_transporting_carrier", "agent_theme_binding"),
    ("motion_trajectory_phase", "Distinguish approaching, crossing, departing, and arrived phases from scoped movement evidence.", "lily", "approaching", "Lily walked toward the gate but had not reached it.", "Lily reached the gate and stopped there.", "infer_path_phase", "incremental_motion_state"),
    ("motion_speed_class", "Interpret explicitly stated qualitative speed relative to the described moving entity.", "cart", "fast", "The cart rolled quickly down the road.", "Lily quickly noticed the cart standing still.", "attach_speed_modifier_to_motion", "modifier_attachment"),
    ("motion_speed_change", "Determine speeding up or slowing down from an explicit speed-change event.", "cart", "decelerating", "The cart slowed as it approached the gate.", "The cart moved slowly at a steady speed near the gate.", "derive_speed_transition", "kinematic_state_change"),
    ("motion_pace_variability", "Distinguish steady motion from alternating pauses and bursts.", "lily", "intermittent", "Lily walked a little, stopped, and walked again.", "Lily walked continuously at the same pace.", "aggregate_motion_and_pause_phases", "event_sequence_aggregation"),
    ("motion_control", "Separate self-controlled motion from movement imposed by an external force.", "cart", {"controller": "@lily", "kind": "steered"}, "Lily steered the cart around the corner.", "The cart rolled away uncontrolled with nobody steering after Lily lost hold of it.", "bind_motion_controller", "control_and_force_roles"),
    ("motion_volition", "Retain explicit evidence about whether the moving actor intended the motion.", "lily", "involuntary", "Lily slipped and slid down the hill against her wishes.", "Lily chose to slide down the hill for fun.", "distinguish_intended_from_involuntary_motion", "intentionality_scope_binding"),
    ("motion_contact", "Track whether a moving object maintains contact with a named surface.", "ball", {"surface": "@floor", "contact": "continuous"}, "The ball rolled along the floor without leaving it.", "The ball bounced above the floor between brief contacts.", "resolve_motion_surface_contact", "contact_phase_tracking"),
    ("motion_support", "Identify the support carrying an object during displacement.", "box", {"support": "@cart"}, "The box stayed on the cart as it rolled.", "Lily lifted the box off the cart before moving.", "track_support_through_motion", "support_state_replay"),
    ("motion_posture", "Bind the moving actor's explicitly stated body configuration.", "lily", "crouching", "Lily crawled under the low branch while crouched.", "Lily stood upright after leaving the low branch.", "attach_posture_to_motion_phase", "body_configuration_binding"),
    ("motion_balance", "Detect loss or recovery of balance in the moving actor's current episode.", "lily", "lost", "Lily stumbled and lost her balance on the bridge.", "Lily stumbled in a story she was reading beside the bridge.", "track_motion_balance_transition", "actual_event_scope"),
    ("motion_effort", "Represent explicitly stated physical effort for the current movement rather than infer it from the actor's identity.", "lily", "high", "Lily strained with effort to drag the heavy crate.", "Lily effortlessly pulled the crate on smooth wheels.", "resolve_motion_effort_evidence", "effort_modifier_binding"),
    ("motion_collectivity", "Determine whether multiple entities move together in one explicitly shared episode.", "lily", {"companions": ["@ben"], "coordination": "together"}, "Lily and Ben walked together to the shed.", "Lily walked to the shed before Ben started.", "join_shared_motion_participants", "event_identity_join"),
    ("motion_relative_displacement", "Distinguish unchanged relative position from absolute motion of the carrier frame.", "box", {"relative_to": "@cart", "displacement": "none"}, "The box did not shift on the moving cart.", "The box slid backward across the moving cart.", "compare_relative_poses", "relative_coordinate_tracking"),
    ("motion_return_destination", "Resolve a return destination from an earlier departure of the same entity.", "lily", {"destination": "@shed"}, "Lily left the shed, visited the garden, then returned to the shed.", "Lily left the shed, visited the garden, then went to the river.", "join_return_with_departure", "motion_history_join"),
    ("motion_path_reversal", "Detect a reversal over an already traversed route rather than any later turn.", "lily", {"route": "@path", "reversed": True}, "Lily turned back and retraced the same path.", "Lily turned onto a different path ahead.", "compare_forward_and_reverse_route", "ordered_path_comparison"),
    ("motion_arrival_completion", "Mark arrival only when the prefix establishes that the intended landmark has been reached.", "lily", {"arrived_at": "@gate"}, "Lily finally reached the gate.", "Lily tried to reach the gate but stopped short.", "validate_arrival_result", "event_result_and_negation"),
    ("motion_boundary_crossing", "Determine whether a movement actually crossed the named region boundary.", "lily", {"boundary": "@gate", "crossed": True}, "Lily passed through the open gate into the garden.", "Lily walked up to the closed gate and waited outside.", "resolve_boundary_crossing", "region_transition_model"),
    ("motion_stopping_location", "Retrieve the explicitly established resting location after a motion episode ends.", "cart", {"stopped_at": "@gate"}, "The cart rolled to the gate and stopped there.", "The cart passed the gate and kept rolling.", "bind_stop_event_location", "motion_termination_binding"),
    ("motion_collision", "Identify the participants of an actual impact rather than a near miss or predicted collision.", "cart", {"collided_with": "@gate"}, "The cart struck the gate.", "The cart nearly struck the gate but stopped in time.", "resolve_actual_impact", "scope_aware_collision_binding"),
    ("motion_detour", "Identify a replacement route taken around an explicitly blocked original route.", "lily", {"avoided": "@bridge", "alternative": "@path"}, "The bridge was blocked, so Lily took the side path around it.", "Lily took the side path although the bridge remained clear.", "join_route_choice_to_blockage", "route_alternative_and_cause_join"),
    ("motion_destination_change", "Track an explicitly revised destination while preserving the earlier abandoned goal.", "lily", {"old": "@shed", "new": "@garden"}, "Lily headed for the shed, then changed course toward the garden.", "Lily went through the garden on her way to the shed.", "resolve_revised_path_goal", "goal_scoped_motion_updates"),
    ("motion_transport_constraint", "Determine a stated physical limitation on carrying an object through a route.", "crate", {"blocked_by": "@door", "reason": "insufficient_clearance"}, "The crate was wider than the doorway and could not pass through the door.", "The crate fitted easily through the wide door.", "compare_object_extent_and_route_clearance", "geometric_clearance_check"),
]


CONTAINMENT_ACCESS = [
    ("containment_direct", "Bind an immediate physical container without skipping an intervening container.", "key", {"container": "@pouch"}, "The key was inside the pouch.", "The key lay beside the pouch.", "resolve_immediate_container", "containment_relation_parser"),
    ("containment_transitive", "Derive indirect containment through explicitly nested containers.", "key", {"container": "@chest", "via": "@pouch"}, "The key was in the pouch and the pouch was in the chest.", "The key was in one pouch; a different pouch was in the chest.", "compose_containment_edges", "acyclic_containment_graph"),
    ("containment_path", "Return the ordered chain of containers joining an object to an outer region.", "key", ["@pouch", "@box", "@shed"], "The key was in a pouch inside a box in the shed.", "The key was in a pouch beside a box outside the shed.", "retrieve_ordered_container_chain", "containment_graph_traversal"),
    ("containment_depth", "Count explicit nesting edges to a declared outer container, preserving unknown links.", "key", {"outer": "@box", "edges": 2}, "The key was in the pouch, which was inside the box.", "The key was directly inside the box beside the pouch.", "count_container_edges", "graph_distance_arithmetic"),
    ("containment_relation_kind", "Distinguish enclosure, insertion, wearing, and support rather than treating every location as inside.", "key", "inserted", "The key was inserted into the lock.", "The key rested on top of the lock.", "classify_object_container_relation", "typed_spatial_relation_resolution"),
    ("containment_opening", "Identify the opening through which an enclosed object can pass.", "box", {"opening": "lid_gap"}, "The box had a gap under its raised lid.", "The box's lid was sealed shut without any gap.", "find_container_aperture", "container_boundary_geometry"),
    ("containment_boundary_state", "Retrieve the state of the boundary separating contained contents from outside.", "jar", "sealed", "The jar's lid was tightened and sealed.", "The jar had no lid.", "bind_container_boundary_state", "part_state_binding"),
    ("containment_nested_access", "Require every relevant container boundary in a nested chain to permit access.", "key", {"actor": "@lily", "reachable": False, "barrier": "@box"}, "The key was in an open pouch inside a locked box. Lily could reach the box but could not reach the key through its locked boundary.", "The key was in an open pouch inside an open box, all within Lily's reach with no other obstruction.", "conjoin_nested_boundary_access", "containment_path_guard_evaluation"),
    ("containment_escape_route", "Find an explicitly traversable route from a contained entity to outside.", "cat", {"exit": "@hole"}, "The cat was in the box and could fit through its open hole.", "The cat was in the box but the only hole was too small.", "find_valid_containment_exit", "path_and_clearance_search"),
    ("containment_spill_risk", "Propose a spill risk from unsealed movable contents and an explicitly unstable orientation.", "jar", "possible_spill", "The open jar of water tilted sharply.", "The sealed jar of water tilted sharply.", "evaluate_spill_preconditions", "conditional_physical_affordance"),
    ("containment_capacity_fit", "Check whether stated object or volume requirements fit the available container capacity.", "box", {"fits": False}, "The box held two cups at most, but Lily tried to place three cups inside.", "The box held four cups and Lily placed only three inside.", "compare_required_and_available_capacity", "typed_capacity_arithmetic"),
    ("containment_contents", "Collect currently supported contents while removing explicitly extracted items.", "box", {"contents": ["@key"]}, "A key and cup were in the box, then Lily removed the cup.", "A key and cup were in the box, then Lily removed the key.", "replay_content_additions_and_removals", "containment_set_state"),
    ("containment_hazard", "Identify an explicitly incompatible combination of contents and container conditions.", "box", {"risk": "fire", "source": "@fire"}, "A flame from the fire touched dry paper inside the box.", "Cold ashes from the extinguished fire lay in the metal box.", "evaluate_contained_hazard_conditions", "typed_hazard_rules"),
    ("containment_support_loss", "Detect a loss of support that may release contents from their container.", "basket", {"support": "bottom", "lost": True}, "The bottom of the basket tore away completely, leaving the stones inside without support.", "The handle of the empty basket tore.", "bind_failed_container_support", "part_and_load_relation"),
    ("containment_partial", "Represent partial insertion without replacing it by complete containment.", "board", {"inside_fraction": "partial", "container": "@box"}, "Only one end of the board fitted inside the box.", "The entire board fitted inside the box.", "resolve_partial_containment", "extent_and_boundary_binding"),
    ("containment_reachable_contents", "Identify which established contents are reachable from an explicit opening and actor access state.", "box", {"reachable_contents": ["@key"]}, "The open box held a key within Lily's reach.", "The sealed box held a key beyond Lily's reach.", "filter_contents_by_reachability", "containment_and_reachability_join"),
    ("access_reachability", "Determine whether an actor can physically reach a target along a stated feasible path.", "key", {"actor": "@lily", "reachable": True}, "The key lay on the low table within Lily's reach.", "The key lay beyond Lily's reach on the high shelf.", "evaluate_actor_target_reach", "capability_aware_path_search"),
    ("access_barrier", "Select the barrier actually obstructing the focused target's access path.", "key", {"barrier": "@door"}, "The key lay behind the locked door with no other entrance.", "The locked door was beside the key on the same side as Lily.", "find_active_access_barrier", "barrier_and_path_join"),
    ("access_route", "Retrieve an explicitly usable route to a target without confusing it with merely mentioned paths.", "shed", {"route": "@path"}, "The clear path led from Lily to the shed.", "The path ended at the river and never reached the shed.", "select_connected_access_route", "connectivity_search"),
    ("access_key_requirement", "Bind a lock-specific key prerequisite without assuming every key opens every lock.", "door", {"required_key": "@key"}, "The door's lock could be opened only by this key.", "The key opened another lock and did not fit the door.", "resolve_lock_key_compatibility", "typed_key_lock_relation"),
    ("access_clearance", "Check physical clearance for a particular actor or object at a passage.", "crate", {"passage": "@door", "fits": True}, "The crate was narrower and shorter than the open door.", "The crate was wider than the open door.", "compare_cross_section_clearance", "geometric_comparison"),
    ("access_tool_requirement", "Identify a tool-dependent access prerequisite from an explicit obstacle.", "key", {"tool": "@ladder"}, "The key was too high for Lily, but the ladder reached its shelf.", "The key was inside a locked drawer that the ladder could not open.", "match_access_obstacle_to_tool", "affordance_and_obstacle_matching"),
    ("access_visibility", "Check whether a target is visible to a named observer under the stated illumination and barriers.", "key", {"observer": "@lily", "visible": True}, "Lily shone the lantern directly on the uncovered key.", "Lily shone the lantern on the closed opaque box containing the key.", "combine_light_and_occlusion", "perceptual_access_model"),
    ("access_audibility", "Check whether an explicitly produced sound can reach a listener through the stated barrier.", "bell", {"listener": "@lily", "audible": False}, "The ringing bell was behind a soundproof wall, so Lily could not hear it.", "The ringing bell was beside Lily with nothing blocking the sound.", "resolve_sound_access", "auditory_path_and_barrier_model"),
    ("access_line_of_sight", "Trace a clear geometric sightline separately from whether the observer notices the target.", "box", {"observer": "@lily", "clear": True}, "Nothing stood between Lily's eyes and the box.", "An opaque board stood between Lily's eyes and the box.", "trace_geometric_sightline", "ray_occlusion_geometry"),
    ("access_touchability", "Distinguish direct physical contact access from visual access through a barrier.", "cup", {"actor": "@lily", "touchable": False}, "Lily saw the cup through a sealed glass pane but could not touch it.", "Lily reached through the open window and touched the cup.", "compare_touch_and_sight_access", "modality_specific_access"),
    ("access_mobility_requirement", "Bind the capability needed to traverse a stated route.", "ledge", {"required": "climb"}, "The ledge could be reached only by climbing the ladder.", "A level path led directly to the ledge.", "infer_route_capability_requirement", "route_capability_model"),
    ("access_support_requirement", "Identify support required for safe access to an elevated or unstable target.", "ladder", {"required": "stable_base"}, "The ladder could be used safely only with its feet on firm ground.", "The ladder lay flat on the ground and nobody needed to climb it.", "evaluate_support_prerequisite", "stability_guard_model"),
    ("access_entry_side", "Identify the side from which a one-way opening or control can be used.", "gate", {"operable_side": "garden"}, "The gate's latch could be lifted only from inside the garden.", "The gate had handles that opened it from either side.", "resolve_directional_entry_control", "oriented_access_rule"),
    ("access_exit_side", "Distinguish a permitted outward exit from a blocked reverse entry.", "door", {"allowed_direction": "outward"}, "The door could be pushed open from inside but not pulled open from outside.", "The door opened freely in both directions.", "resolve_asymmetric_exit", "directed_transition_guard"),
    ("access_bottleneck", "Find the narrowest mandatory segment of a declared route.", "crate", {"bottleneck": "@tunnel"}, "Every route carrying the crate to the shed passed through the tunnel, which was narrower than every other segment on those routes.", "A wide path bypassed the tunnel and led to the shed with the crate.", "find_mandatory_route_bottleneck", "graph_cut_and_clearance_search"),
    ("access_blocking_object", "Bind an object obstructing a passage and distinguish it from the passage itself.", "door", {"obstruction": "@crate"}, "The crate was wedged across the door and blocked it.", "The crate stood beside the clear door.", "resolve_object_as_obstruction", "object_passage_geometry"),
]


POSSESSION_TRANSFER = [
    ("possession_holder", "Resolve the current physical holder after explicit handoffs without equating holder and owner.", "cup", {"holder": "@ben"}, "Lily held the cup, then handed it to Ben.", "Lily offered the cup to Ben but kept holding it.", "replay_valid_holder_transfers", "possession_chronology"),
    ("possession_owner", "Resolve ownership from explicit ownership or gift evidence rather than mere handling.", "cup", {"owner": "@lily"}, "Lily owned the cup and lent it to Ben.", "Lily gave ownership of the cup to Ben as a gift.", "distinguish_ownership_from_custody", "typed_property_rights_state"),
    ("possession_custodian", "Bind an entrusted caretaker of an object while preserving the original owner.", "book", {"custodian": "@ben"}, "Lily asked Ben to keep her book safe until she returned. Ben accepted the responsibility and received the book from Lily.", "Ben found a book but had not been entrusted with it.", "resolve_entrusted_custody", "custody_commitment_binding"),
    ("possession_borrower", "Identify the recipient of an actual temporary loan.", "book", {"borrower": "@ben"}, "Lily lent her book to Ben until evening.", "Lily promised to lend the book to Ben tomorrow.", "bind_completed_loan_recipient", "loan_event_state"),
    ("possession_lender", "Identify the source that issued a temporary loan rather than its intermediary carrier.", "book", {"lender": "@lily"}, "Lily lent Ben the book and Nia delivered it for her.", "Nia lent Ben the book while Lily watched.", "bind_loan_source_across_delivery", "transaction_role_join"),
    ("possession_user", "Identify current use of an instrument separately from holding or owning it.", "hammer", {"user": "@ben"}, "Ben used Lily's hammer to drive the nail.", "Ben held Lily's hammer without using it.", "bind_instrument_user", "instrument_event_role"),
    ("possession_reservation", "Track an explicitly reserved object without treating reservation as completed possession.", "book", {"reserved_for": "@ben", "reserved_recipient_holds_now": False, "current_holder": "@lily"}, "The book stayed with Lily but was reserved for Ben.", "The book was available to anyone with no reservation.", "resolve_reservation_without_transfer", "reservation_state"),
    ("possession_recoverability", "Identify an explicitly established route for regaining an item after custody is lost.", "key", {"recoverable": True, "location": "@box"}, "Lily dropped the key into an open box within reach.", "Lily dropped the key into a deep sealed shaft beyond reach.", "join_loss_location_and_access", "custody_loss_and_reachability"),
    ("possession_shared", "Represent explicit joint possession without forcing a unique holder.", "crate", {"holders": ["@lily", "@ben"]}, "Lily and Ben held opposite handles of the same crate together.", "Lily held the crate while Ben watched.", "collect_simultaneous_joint_holders", "shared_participation_binding"),
    ("possession_disputed", "Retain conflicting ownership claims instead of choosing an unsupported owner.", "book", {"claimants": ["@lily", "@ben"], "resolved": False}, "Lily and Ben each claimed the same book as their own, with no decision.", "Lily and Ben agreed that the book belonged to Lily.", "collect_incompatible_ownership_claims", "claim_scope_and_conflict_tracking"),
    ("possession_claim_basis", "Record the explicitly stated basis of an ownership claim without independently validating it.", "cup", {"claimant": "@lily", "basis": "gift"}, "Lily said the cup was hers because Ben had given it to her.", "Lily said she wanted the cup although it belonged to Ben.", "attribute_claim_and_stated_basis", "reported_claim_provenance"),
    ("possession_custody_chain", "Preserve the ordered sequence of completed custody handoffs for one object.", "parcel", {"holders": ["@lily", "@ben", "@nia"]}, "Lily handed the parcel to Ben, who handed it to Nia.", "Lily handed the parcel to Ben, but Nia never received it.", "join_ordered_handoffs", "object_identity_and_event_order"),
    ("possession_return_target", "Identify the person to whom a loan or entrusted object is to be returned.", "book", {"return_to": "@lily"}, "Ben borrowed the book from Lily and agreed to return it to her.", "Lily gave the book to Ben permanently.", "bind_return_obligation_target", "loan_and_return_role_link"),
    ("possession_transfer_permission", "Separate explicitly granted permission to pass an object from mere ability to pass it.", "book", {"may_pass_to": "@nia"}, "Lily allowed Ben to pass her book to Nia.", "Lily forbade Ben to pass her book to Nia.", "resolve_object_specific_transfer_authority", "permission_scope_binding"),
    ("possession_transferability", "Check a stated physical restriction that prevents a held object from being handed over.", "cup", {"transferable": False, "reason": "fixed_to_table"}, "The cup was bolted to the table and could not be lifted.", "The loose cup could be lifted freely from the table.", "evaluate_detachment_requirement", "attachment_and_transfer_guard"),
    ("possession_unattended", "Detect an item explicitly put down and left without a current custodian.", "bag", {"unattended": True}, "Lily left the bag on the bench and everyone walked away.", "Lily left the bag on the bench while Ben stayed to watch it.", "resolve_holder_and_watcher_absence", "closed_local_cast_and_custody_state"),
    ("transfer_object", "Bind the transferred theme rather than the container, giver, or recipient.", "cup", {"theme": "@cup", "recipient": "@ben"}, "Lily gave Ben the cup from the box.", "Lily gave Ben the box while keeping the cup.", "resolve_transfer_theme", "transaction_argument_parser"),
    ("transfer_source", "Identify the source holder in a completed physical handoff.", "cup", {"source": "@lily"}, "Ben received the cup from Lily's hands.", "Ben received the cup from Nia while Lily watched.", "bind_handoff_source_holder", "source_theme_recipient_binding"),
    ("transfer_recipient", "Identify the actual recipient rather than a proposed or addressed recipient.", "cup", {"recipient": "@ben"}, "Lily placed the cup into Ben's hands.", "Lily offered the cup to Ben but Nia took it instead.", "bind_completed_handoff_recipient", "actual_recipient_resolution"),
    ("transfer_kind", "Distinguish gift, loan, return, sale, and mere delivery from explicit transaction evidence.", "book", "loan", "Lily lent the book to Ben for one day.", "Lily gave the book to Ben to keep forever.", "classify_transaction_rights", "transaction_semantics"),
    ("transfer_completion", "Mark a handoff complete only once the recipient actually receives custody.", "cup", {"completed": True, "recipient": "@ben"}, "Ben took the cup from Lily and held it.", "Ben reached for the cup but Lily pulled it back.", "check_handoff_result", "event_completion_and_custody"),
    ("transfer_failed_precondition", "Identify a stated missing prerequisite that blocks a proposed handoff.", "cup", {"missing": "source_possession"}, "Lily tried to give Ben the cup, but she did not have it.", "Lily held the cup and successfully gave it to Ben.", "diagnose_handoff_guard_failure", "transfer_guard_evaluation"),
    ("transfer_handoff_location", "Bind the physical location shared at a completed handoff rather than the object's later destination.", "cup", {"location": "@shed"}, "Lily gave Ben the cup in the shed before he carried it to the garden.", "Lily carried the cup through the shed but gave it to Ben in the garden.", "bind_location_at_transfer_event", "event_location_join"),
    ("transfer_joint_participation", "Preserve one handoff event shared by source, theme, and recipient projections.", "cup", {"participants": ["@lily", "@cup", "@ben"]}, "Lily passed the cup directly to Ben in one handoff.", "Lily put down the cup and much later Ben picked it up alone.", "join_shared_transfer_event", "shared_event_identity"),
    ("transfer_retained_ownership", "Represent custody transfer with explicitly unchanged ownership.", "book", {"owner": "@lily", "holder": "@ben"}, "Lily lent her book to Ben while keeping ownership.", "Lily transferred ownership of the book to Ben as a gift and handed him the book. Ben accepted and held it.", "separate_custody_and_title_updates", "multi_relation_transaction_state"),
    ("transfer_recipient_acceptance", "Record explicit acceptance or refusal without inventing consent from physical contact.", "cup", {"recipient": "@ben", "accepted": True}, "Ben agreed to take the cup and accepted it from Lily.", "Lily forced the cup into Ben's hands while he refused it.", "bind_acceptance_to_handoff", "consent_and_event_scope_join"),
    ("transfer_return_due", "Bind a stated return condition to the loan object without inventing a deadline.", "book", {"due_condition": "evening"}, "Ben borrowed the book and agreed to return it by evening.", "Ben received the book as a gift with no return expected.", "retrieve_loan_return_condition", "transaction_obligation_link"),
    ("transfer_exchange_counterpart", "Bind the reciprocal object in an explicit exchange rather than any nearby item.", "book", {"counterpart": "@map"}, "Lily traded the book to Ben in exchange for his map.", "Lily gave Ben the book while keeping her map.", "align_reciprocal_transfer_roles", "paired_exchange_events"),
    ("transfer_delivery_destination", "Distinguish an item's delivery destination from the courier's intermediate location.", "parcel", {"destination": "@shed"}, "Ben carried the parcel through the garden to deliver it to the shed.", "Ben carried the parcel through the shed to deliver it to the garden.", "resolve_delivery_goal", "path_and_transaction_role_join"),
    ("transfer_delivery_intermediary", "Identify a courier who temporarily carries the item between source and final recipient.", "parcel", {"intermediary": "@ben", "recipient": "@nia"}, "Lily gave Ben the parcel to carry to Nia.", "Lily gave the parcel to Ben for him to keep while Nia watched.", "bind_intermediary_and_final_recipient", "delivery_plan_role_binding"),
    ("transfer_delegated_custody", "Track an expressly authorized handoff of entrusted custody to a substitute caretaker.", "book", {"new_custodian": "@nia", "authorizer": "@lily"}, "Lily entrusted her book to Ben and allowed him to hand it to Nia for safekeeping. Ben handed the book to Nia, who accepted responsibility for it.", "Ben secretly handed Lily's book to Nia against Lily's instructions. Nia accepted and held the book.", "validate_delegated_custody_chain", "custody_authority_join"),
    ("transfer_lost_custody", "Represent loss of physical custody without falsely assigning ownership to the place of loss.", "key", {"previous_holder": "@lily", "holder": None}, "Lily dropped the key into the grass and no one picked it up.", "Lily dropped the key straight into Ben's waiting hand.", "resolve_unreceived_release", "custody_release_state"),
]


OBJECT_STATES = [
    ("object_integrity", "Structural integrity of the bound physical entity.", "cup", [("intact", "intact"), ("cracked", "cracked"), ("broken", "broken")]),
    ("object_openness", "Open or closed aperture state of the bound entity.", "door", [("open", "open"), ("closed", "closed"), ("ajar", "partly_open")]),
    ("object_lock_state", "Lock engagement state, distinct from whether the aperture is open.", "door", [("locked", "locked"), ("unlocked", "unlocked")]),
    ("object_attachment", "Attachment state of a physical part or object.", "handle", [("attached", "attached"), ("detached", "detached")]),
    ("object_cleanliness", "Explicitly described cleanliness of a physical carrier.", "cup", [("clean", "clean"), ("dirty", "dirty")]),
    ("object_moisture", "Qualitative surface or material moisture state.", "cloth", [("dry", "dry"), ("damp", "damp"), ("wet", "wet")]),
    ("object_temperature", "Qualitative thermal state without inventing a numeric temperature.", "water", [("cold", "cold"), ("warm", "warm"), ("hot", "hot")]),
    ("object_luminosity", "Active illumination state, distinct from reflecting external light.", "lantern", [("lit", "lit"), ("unlit", "unlit"), ("glowing", "glowing")]),
    ("object_sound_level", "An explicitly described audible activity state of a sound source.", "bell", [("silent", "silent"), ("noisy", "audibly_active")]),
    ("object_concealment", "Explicit covering or concealment state, distinct from observer-dependent visibility.", "key", [("exposed", "exposed"), ("concealed", "concealed")]),
    ("object_operability", "Whether a device is described as functioning, separate from surface damage.", "engine", [("operational", "operational"), ("inoperable", "inoperable")]),
    ("object_charge_state", "Qualitative stored electrical charge condition of a carrier.", "battery", [("charged", "charged"), ("discharged", "discharged")]),
    ("object_fill_state", "Qualitative fill condition of a container; this finite seed covers empty and full.", "jar", [("empty", "empty"), ("full", "full")]),
    ("object_pressure_state", "Explicit qualitative pressurization state of a vessel.", "bottle", [("pressurized", "pressurized"), ("depressurized", "depressurized")]),
    ("object_seal_state", "Whether a container boundary is explicitly sealed against passage.", "jar", [("sealed", "sealed"), ("unsealed", "unsealed")]),
    ("object_shape", "Qualitative deformation or geometric shape state of a carrier.", "board", [("flat", "flat"), ("curved", "curved"), ("bent", "bent")]),
    ("object_corrosion_state", "Explicit corrosion or absence-of-corrosion condition of a physical carrier.", "nail", [("corroded", "corroded"), ("rusty", "rusted"), ("uncorroded", "uncorroded")]),
    ("object_compression_state", "Explicit compression or expansion condition of a physical carrier.", "cloth", [("compressed", "compressed"), ("uncompressed", "uncompressed")]),
    ("object_stability", "Explicit stable or unstable support condition, distinct from balance alone.", "ladder", [("stable", "stable"), ("unstable", "unstable")]),
    ("object_tension_state", "Qualitative mechanical tension condition of a flexible carrier.", "rope", [("taut", "taut"), ("slack", "slack")]),
    ("object_edge_condition", "Sharpness condition of an edge-bearing object.", "scissors", [("sharp", "sharp"), ("blunt", "blunt")]),
    ("object_surface_condition", "Explicit tactile roughness condition of a physical surface.", "board", [("smooth", "smooth"), ("rough", "rough")]),
    ("object_freshness", "Explicit freshness or staleness of a perishable carrier.", "bread", [("fresh", "fresh"), ("stale", "stale")]),
    ("object_ripeness", "Explicit ripeness state of a fruit or comparable biological product.", "apple", [("ripe", "ripe"), ("unripe", "unripe"), ("overripe", "overripe")]),
    ("object_cooking_state", "Explicit raw, cooked, or burnt preparation condition.", "bread", [("raw", "raw"), ("cooked", "cooked"), ("burnt", "burnt")]),
    ("object_freezing_state", "Frozen or thawed phase history expressed as a current condition.", "water", [("frozen", "frozen"), ("thawed", "thawed")]),
    ("object_growth_state", "Explicit dormancy condition of a living carrier, without predicting later growth.", "plant", [("dormant", "dormant")]),
    ("object_health_state", "Explicit healthy or ill bodily condition of a living carrier.", "cat", [("healthy", "healthy"), ("sick", "ill")]),
    ("object_wakefulness", "Explicit awake or asleep bodily condition, without inferring knowledge.", "cat", [("awake", "awake"), ("asleep", "asleep")]),
    ("object_fatigue_state", "Explicit rested or tired physical condition, without inferring emotion.", "dog", [("rested", "rested"), ("tired", "tired")]),
    ("object_assembly_state", "Assembled or disassembled condition of a composite physical object.", "cart", [("assembled", "assembled"), ("disassembled", "disassembled")]),
    ("object_connection_state", "Connected or disconnected condition of a physical link.", "cable", [("connected", "connected"), ("disconnected", "disconnected")]),
]


MATERIALS = [
    ("material_composition", "A finite candidate reading of an explicitly named material, excluding metallic appearance.", "box", [("wooden", "wood"), ("plastic", "plastic")]),
    ("material_phase", "An explicitly described solid, liquid, or gaseous phase.", "water", [("solid", "solid"), ("liquid", "liquid"), ("gaseous", "gas")]),
    ("material_elasticity", "Qualitative elastic recovery behavior, distinct from simple bendability.", "rope", [("elastic", "elastic"), ("inelastic", "inelastic")]),
    ("material_flexibility", "Qualitative bendability under ordinary stated use.", "board", [("flexible", "flexible"), ("rigid", "rigid")]),
    ("material_brittleness", "Explicit tendency to fracture rather than deform under load.", "glass", [("brittle", "brittle"), ("tough", "tough")]),
    ("material_hardness", "Qualitative resistance to indentation, as explicitly described.", "stone", [("hard", "hard"), ("soft", "soft")]),
    ("material_porosity", "Explicit porous or nonporous internal structure.", "stone", [("porous", "porous"), ("nonporous", "nonporous")]),
    ("material_absorbency", "Explicit tendency to absorb liquid, distinct from permeability and surface water repellency.", "cloth", [("absorbent", "absorbent"), ("nonabsorbent", "nonabsorbent")]),
    ("material_adhesion", "Explicit sticky or nonstick surface behavior.", "sheet", [("sticky", "adhesive"), ("nonstick", "nonadhesive")]),
    ("material_friction", "Explicit high or low grip condition at a surface.", "floor", [("slippery", "low_grip"), ("grippy", "high_grip")]),
    ("material_conductivity", "Explicit conductive or insulating behavior in the given material description.", "cable", [("conductive", "conductive"), ("insulating", "insulating")]),
    ("material_transparency", "Explicit transparent, translucent, or opaque optical transmission behavior.", "glass", [("transparent", "transparent"), ("translucent", "translucent"), ("opaque", "opaque")]),
    ("material_buoyancy", "Explicit floatability description as a candidate under unspecified medium conditions.", "board", [("buoyant", "buoyant"), ("nonbuoyant", "nonbuoyant")]),
    ("material_flammability", "Explicit flammable or fire-resistant condition, without predicting ignition.", "cloth", [("flammable", "flammable"), ("fireproof", "fire_resistant")]),
    ("material_solubility", "Explicit soluble or insoluble description, retaining unresolved solvent context.", "paint", [("soluble", "soluble"), ("insoluble", "insoluble")]),
    ("material_magnetism", "Explicit magnetic or nonmagnetic material behavior.", "nail", [("magnetic", "magnetic"), ("nonmagnetic", "nonmagnetic")]),
]


AFFORDANCES = [
    ("affordance_carrying", "Evaluate carrying compatibility from actor capacity, object portability, and current attachment.", "box", {"actor": "@lily", "can_carry": True}, "The box was light, loose, and small enough for Lily to carry.", "The box was bolted to the floor beyond Lily's lifting strength.", "check_portability_load_and_attachment", "typed_action_precondition_evaluation"),
    ("affordance_grasping", "Check an explicitly available grip and actor access rather than assuming all objects can be held.", "cup", {"actor": "@lily", "graspable": True}, "The cup had a cool handle within Lily's reach.", "The cup had no safe grip and was too hot for Lily to touch.", "check_grip_access_and_contact_conditions", "grasp_affordance_model"),
    ("affordance_climbing", "Evaluate whether a stated structure can support the actor's proposed climb.", "ladder", {"actor": "@lily", "climbable": True}, "The stable ladder was strong enough to support Lily.", "The broken ladder could not support Lily's weight.", "check_climbing_support_and_integrity", "load_and_structure_guard"),
    ("affordance_sitting", "Check a body's supported sitting configuration against the explicit object conditions.", "crate", {"actor": "@lily", "sittable": True}, "The crate had a flat strong top that could support Lily sitting.", "The crate's top was broken and could not support Lily.", "check_seat_surface_and_support", "posture_support_model"),
    ("affordance_containing", "Evaluate whether a container can hold the proposed contents under its stated closure and material conditions.", "basket", {"contents": "water", "suitable": False}, "The basket had wide holes and could not hold water.", "The basket had a watertight lining that held water.", "check_content_container_compatibility", "containment_material_rules"),
    ("affordance_traversal", "Check whether a route is traversable by the stated actor under current conditions.", "bridge", {"actor": "@lily", "traversable": True}, "The bridge was intact, clear, and strong enough for Lily.", "The bridge had collapsed into the river before Lily arrived.", "check_route_support_and_continuity", "route_state_and_capacity_model"),
    ("affordance_eating", "Use explicit edible-condition evidence to propose eating suitability without inferring it from a noun alone.", "apple", {"edible": True}, "The apple was fresh, safe to eat, and washed.", "The apple was marked poisonous and unsafe to eat.", "check_explicit_food_suitability", "food_condition_guard"),
    ("affordance_drinking", "Distinguish a potable liquid from a merely liquid substance using explicit evidence.", "water", {"drinkable": True}, "The water had been tested and declared safe to drink.", "The water was contaminated and declared unsafe to drink.", "check_explicit_potability", "liquid_suitability_guard"),
    ("affordance_cutting", "Match a cutting instrument to a material and condition rather than name-based universal suitability.", "scissors", {"patient": "@cloth", "suitable": True}, "The sharp scissors were designed to cut this thin cloth.", "The blunt scissors could not cut the thick metal sheet beside the cloth.", "match_cutting_edge_to_patient_material", "tool_patient_compatibility"),
    ("affordance_fastening", "Match an available fastener and target material to the proposed joining action.", "screw", {"patient": "@board", "suitable": True}, "The screw fitted the prepared hole in the board.", "The screw was too wide for the board's prepared hole.", "check_fastener_geometry_and_material", "fastener_fit_model"),
    ("affordance_illumination", "Evaluate whether an operating light source can illuminate the specified dark target.", "lantern", {"target": "@key", "suitable": True}, "The lit lantern could shine directly onto the key in the dark.", "The lantern had no fuel and could not light the dark key.", "check_light_source_state_and_path", "illumination_affordance_model"),
    ("affordance_warming", "Evaluate an explicitly available warming means under the stated carrier and safety conditions.", "blanket", {"target": "@cat", "suitable": True}, "The dry blanket could keep the cold cat warm.", "The wet freezing blanket could not warm the cold cat.", "check_warming_source_and_target", "thermal_action_conditions"),
    ("affordance_writing", "Check writing-medium compatibility and instrument state.", "paint", {"surface": "@board", "suitable": True}, "The wet paint adhered to the dry board and could mark it.", "The dried paint could no longer mark the board.", "check_marking_medium_state", "instrument_surface_compatibility"),
    ("affordance_repair", "Match an explicitly described repair capability to the actual defect.", "needle", {"patient": "@cloth", "suitable": True}, "The threaded needle could stitch the torn cloth.", "The needle could not repair the shattered glass beside the cloth.", "match_tool_capability_to_defect", "repair_action_model"),
    ("affordance_unlocking", "Match the particular key to its lock and preserve current lock state.", "key", {"lock": "@lock", "suitable": True}, "This key matched the locked lock and could turn in it.", "This key did not fit the locked lock.", "check_specific_key_lock_fit", "key_lock_affordance_model"),
    ("affordance_sheltering", "Evaluate protection supplied by a structure against an explicitly named exposure.", "shed", {"protects_from": "rain"}, "The shed's intact roof and walls kept the rain out.", "The roofless shed let the rain fall directly inside.", "check_enclosure_against_exposure", "shelter_structure_model"),
]


def _event_native(catalog):
    rows = [
        ("event_phase", "A selected initiation sense for an event whose detailed content can remain unresolved.", "began", "begin:initiate_event", "initiated"),
        ("event_completion_evidence", "A selected event-completion sense, distinct from attempting or wanting completion.", "finished", "finish:complete_event", "completion_mentioned"),
        ("event_interruption", "A selected event-interruption sense without assuming permanent termination.", "interrupted", "interrupt:suspend_event", "interruption_mentioned"),
        ("event_resumption", "A selected resumption sense whose earlier episode still requires event binding.", "resumed", "resume:continue_event", "resumption_mentioned"),
        ("event_cancellation", "A selected event-cancellation sense without treating the cancelled event as executed.", "cancelled", "cancel:withdraw_event", "cancellation_mentioned"),
        ("event_failure", "A selected unsuccessful-attempt sense attached to the narrated predicate occurrence.", "failed", "fail:unsuccessful_attempt", "failure_mentioned"),
        ("event_success", "A selected achieve-goal sense, distinct from succession to a role or position.", "succeeded", "succeed:achieve_goal", "success_mentioned"),
        ("event_iteration", "A selected repeat-event sense without inventing how many repetitions occurred.", "repeated", "repeat:perform_event_again", "repetition_mentioned"),
    ]
    for key, desc, word, sense, meaning in rows:
        actor = {"token": "Lily", "entity_id": "e1", "scope_id": "s1", "assertion_status": "asserted"}
        action = {"token": word, "pos": "v", "event_id": "ev2", "scope_id": "s1", "factuality": "asserted",
                  "actor_id": "e1", "lexical_sense_id": sense}
        value = {"cue": meaning, "trigger_event_id": "ev2", "affected_event_id": None}
        payload = {"entity_id": ref("actor.entity_id"), "scope_id": ref("actor.scope_id"), "assertion_status": "candidate",
                   "value": {"cue": meaning, "trigger_event_id": ref("query.event_id"), "affected_event_id": None}}
        native = neuron(seq(gap(), tok("actor", entity_id=present(), scope_id=present(), assertion_status="asserted"),
                            tok(token=word, pos="v", event_id=present(), factuality="asserted", scope_id=ref("actor.scope_id"),
                                actor_id=ref("actor.entity_id"), lexical_sense_id=sense)), {key: payload})
        catalog.add(key, "object", desc, "world.event_structure", value=_bundle(value), scope="visible_event_trigger_candidate",
                    head=f"recognize_{key}_cue", function=desc, mechanism="bound_actor_and_visible_aspectual_trigger", native=native,
                    positive=example([actor, action], {key: _bundle(value)}, "The last visible verb has a causally supplied actor and selected event sense; its unseen complement remains unknown."),
                    negative=example([actor, {**action, "factuality": "negated"}], {}, "A negated cue does not support this positive event reading."), sources=SOURCES,
                    notes="Actor identity and the selected lexical sense must already be supplied by causal annotation or another evaluated producer. These authored sense labels are not WordNet IDs. The trigger is not equated with the affected event; affected_event_id stays null until resolved. The native seed does not parse roles, disambiguate senses, prove physical completion or revise past records.")
        _contrast(catalog, [{"token": "Ben", "entity_id": "e2", "scope_id": "s1"}, {"token": "beside"},
                            actor, {**action, "actor_id": "e2"}],
                  "The event belongs to Ben/e2, not nearby Lily/e1; the immediately preceding entity cannot receive its cue.")
        other_sense = "succeed:inherit_position" if key == "event_success" else "unresolved_or_incompatible_sense"
        _contrast(catalog, [actor, {**action, "lexical_sense_id": other_sense}], "The selected sense does not license this event relation; identical spelling is insufficient.")


EVENT_ADAPTERS = [
    ("event_initiator", "Identify the participant that initiates an explicitly controlled action rather than its grammatical subject alone.", "lily", {"initiator": "@lily"}, "Lily deliberately started pushing the cart.", "Lily was pushed into the cart by Ben.", "resolve_action_initiator", "causal_agent_binding"),
    ("event_causer", "Bind a physical causer independently of intention or animacy.", "cart", {"causer": "@stone"}, "The falling stone struck the cart and set it moving.", "The stone lay beside the cart while Lily pushed it.", "resolve_nonvolitional_causer", "cause_effect_argument_binding"),
    ("event_effector", "Identify the body part or mechanism directly executing an action, distinct from the whole agent.", "lily", {"effector": "@hands"}, "Lily pushed the box with her hands.", "Lily watched a motor push the box.", "bind_direct_action_effector", "part_agent_instrument_resolution"),
    ("event_affected_entity", "Identify the entity undergoing an explicit change rather than a mentioned observer.", "cup", {"change": "cracked"}, "The impact cracked the cup while Lily watched.", "Lily cracked a joke about the intact cup.", "bind_physical_patient_change", "literal_event_patient_resolution"),
    ("event_theme", "Bind the entity whose location or relation changes in a transfer or motion event.", "box", {"theme": "@box", "carrier": "@lily"}, "Lily carried the box across the garden.", "Lily crossed the garden while the box remained in the shed.", "resolve_displaced_theme", "event_theme_binding"),
    ("event_instrument_binding", "Distinguish the tool used in an event from its theme or coincidental nearby object.", "needle", {"used_on": "@cloth"}, "Lily mended the cloth with the needle.", "Lily placed the needle beside the cloth and mended it with glue.", "resolve_used_instrument_role", "instrument_attachment_parser"),
    ("event_result_entity", "Bind a newly produced entity separately from the material transformed into it.", "bowl", {"created_from": "clay"}, "Lily shaped the clay into a bowl.", "Lily placed clay inside an already existing bowl.", "resolve_created_result_role", "creation_event_entity_binding"),
    ("event_source_role", "Bind a nonmotion source such as material origin or information origin with its event kind.", "board", {"source": "@tree", "event_kind": "material_extraction"}, "The board was cut from the fallen tree.", "The board leaned beside the fallen tree.", "resolve_event_source_by_kind", "typed_source_role_parser"),
    ("event_goal_role", "Bind the result or target state toward which an action is directed without asserting achievement.", "door", {"goal_state": "open", "achieved": None}, "Lily tried to open the door.", "Lily tried to keep the door closed.", "separate_event_goal_from_result", "intention_result_scope"),
    ("event_beneficiary", "Bind the explicitly intended beneficiary, distinct from the actor or physical recipient.", "coat", {"beneficiary": "@ben", "actor": "@lily"}, "Lily repaired the coat for Ben to wear.", "Ben helped Lily repair her own coat for Lily to wear.", "resolve_beneficiary_role", "purpose_and_role_binding"),
    ("event_setting", "Identify the event's physical setting instead of a participant's unrelated home or destination.", "lily", {"setting": "@shed"}, "Lily repaired the cart in the shed before returning to the garden.", "Lily left the shed and repaired the cart in the garden.", "bind_event_location_interval", "event_location_scope"),
    ("event_progress", "Represent stated partial achievement without converting it into completion.", "bridge", {"progress": "partial", "completed": False}, "Lily repaired only half of the bridge.", "Lily finished repairing the whole bridge.", "resolve_partial_event_result", "part_whole_result_model"),
    ("event_collective_participants", "Represent a single event performed jointly by an explicitly coordinated participant set.", "crate", {"actors": ["@lily", "@ben"]}, "Lily and Ben lifted the same crate together.", "Lily lifted the crate while Ben lifted another one.", "join_collective_event_participants", "event_identity_and_plural_roles"),
    ("event_divided_labor", "Bind distinct cooperating subtasks to their actors within one shared activity.", "ladder", {"holder": "@ben", "climber": "@lily"}, "Ben held the ladder steady while Lily climbed it.", "Ben and Lily both watched the unused ladder.", "align_cooperative_subtasks", "shared_activity_role_alignment"),
    ("event_role_conflict", "Detect explicitly incompatible simultaneous roles under a declared physical action model.", "lily", {"conflict": "both_hands_unavailable"}, "Lily held the heavy crate with both hands and tried to use those hands to tie a knot at the same time.", "Lily put down the crate before using her hands to tie a knot.", "compare_simultaneous_effector_requirements", "resource_interval_conflict_check"),
    ("event_control", "Distinguish direct control, delegated control, and uncontrolled occurrence.", "cart", {"controller": "@lily", "mode": "direct"}, "Lily controlled the cart with the handle.", "The cart rolled away after its handle broke and Lily lost control.", "resolve_event_control_relation", "control_state_model"),
    ("event_volition", "Bind explicit intention to the specific action rather than to the actor in general.", "lily", {"action": "drop_cup", "intentional": False}, "Lily accidentally dropped the cup.", "Lily deliberately dropped the cup.", "attach_volition_modifier", "action_specific_intent_scope"),
    ("event_contact_mode", "Distinguish impact, sustained contact, and noncontact influence in the described event.", "door", {"mode": "impact", "effector": "@stone"}, "The stone struck the door sharply.", "The stone rested gently against the door.", "classify_event_contact_profile", "contact_event_model"),
    ("event_manner", "Attach an explicit manner description to the correct event rather than to a neighboring action.", "lily", {"event": "close_door", "manner": "careful"}, "Lily carefully closed the door after loudly calling Ben.", "Lily carefully called Ben and then slammed the door.", "resolve_event_manner_attachment", "modifier_event_dependency"),
    ("event_attempt_outcome", "Link an attempted action to its explicitly stated success or failure, preserving uncertainty otherwise.", "door", {"attempt": "open", "outcome": "failed"}, "Lily tried to open the door, but it stayed shut.", "Lily tried to open the door and it swung open.", "join_attempt_to_observed_result", "attempt_result_event_link"),
    ("event_state_change", "Represent a bound before/after transition rather than a timeless property.", "door", {"before": "closed", "after": "open"}, "The door was closed until Lily opened it.", "Lily wished the closed door would open.", "bind_actual_state_transition", "state_delta_replay"),
    ("event_creation", "Identify an explicitly newly created carrier without merging it with preexisting entities of the same type.", "bowl", {"created": True, "material": "clay"}, "Lily made a new bowl from clay.", "Lily picked up an old bowl beside the clay.", "instantiate_creation_candidate_identity", "entity_birth_and_material_tracking"),
    ("event_destruction", "Distinguish destroyed identity from temporary damage, disassembly, or hidden location.", "cup", {"destroyed": True}, "The cup shattered into pieces and no intact cup remained.", "The cup disappeared behind the curtain but stayed intact.", "resolve_object_destruction_result", "object_persistence_model"),
    ("event_role_reassignment", "Track an explicit change of participant role within the same ongoing activity.", "ladder", {"new_holder": "@lily", "previous_holder": "@ben"}, "Ben held the ladder, then Lily took over holding it while Ben climbed.", "Ben kept holding the ladder while Lily climbed.", "rebind_roles_at_handoff_boundary", "activity_role_chronology"),
]


CAUSAL = [
    ("causal_parent", "Retrieve an explicitly recorded or asserted cause of the focused entity's change, not merely the preceding event.", "door", {"cause": "stone_impact", "effect": "door_opened"}, "The stone hit the latch, causing the door to open.", "The stone fell nearby after Lily had already opened the door.", "follow_declared_cause_edge", "causal_event_graph"),
    ("causal_effect", "Retrieve an explicitly established consequence of an event on the focused carrier.", "cloth", {"cause": "water_spill", "effect": "wet"}, "Water spilled onto the cloth and soaked it.", "Water spilled beside the cloth, leaving it dry.", "follow_event_to_state_effect", "event_effect_graph"),
    ("causal_mechanism", "Retain the explicitly described physical process linking cause and effect rather than inventing one.", "door", {"mechanism": "released_latch"}, "The key turned the lock, released the latch, and allowed the door to swing.", "The door opened for a reason nobody knew.", "recover_stated_intermediate_process", "mechanistic_event_chain"),
    ("causal_enabling_condition", "Identify a condition that permits an action without treating it as the action's occurrence.", "door", {"condition": "unlocked", "enables": "opening", "occurred": None}, "Unlocking the door made it possible to open, but nobody opened it yet.", "The door remained locked and impossible to open.", "separate_enablement_from_execution", "precondition_effect_model"),
    ("causal_preventing_condition", "Bind a stated condition that blocks a specific outcome.", "door", {"condition": "bar_in_place", "blocked": "opening"}, "A bar across the door prevented Lily from opening it.", "The bar lay beside the door and did not block opening.", "resolve_preventer_and_blocked_effect", "negative_causal_relation"),
    ("causal_trigger", "Identify the initiating event in an explicitly triggered physical process.", "bell", {"trigger": "button_press"}, "Pressing the button immediately started the bell ringing.", "Lily pressed a button while an unrelated bell was already ringing.", "bind_process_trigger", "trigger_process_event_join"),
    ("causal_sustaining_condition", "Identify a condition that must continue for an ongoing effect to persist under the stated rule.", "motor", {"sustainer": "electric_power"}, "The motor ran only while electric power continued.", "The motor kept running on stored energy after power was removed.", "resolve_continuous_support_condition", "process_persistence_model"),
    ("causal_termination_condition", "Identify the event that explicitly ends an ongoing process.", "fire", {"terminator": "water_application"}, "The water extinguished the fire completely.", "The water missed the fire, which kept burning.", "bind_process_termination_cause", "process_end_event_link"),
    ("causal_mediation_chain", "Preserve intermediate events on a stated causal path instead of claiming a direct effect.", "bell", {"chain": ["rope_pull", "lever_motion", "bell_strike"]}, "Pulling the rope moved the lever, which struck the bell.", "Lily pulled the rope after Ben had independently struck the bell.", "retrieve_causal_path_with_mediators", "directed_causal_graph_traversal"),
    ("causal_joint_cause", "Represent explicitly conjunctive causes that must act together under a stated mechanism.", "door", {"required_together": ["key_turned", "handle_pressed"]}, "This door opened only when the key was turned and the handle pressed together.", "This door opened whenever either the key or the handle was used alone.", "bind_conjunctive_causal_guard", "typed_guard_logic"),
    ("causal_alternative_cause", "Represent explicitly alternative sufficient routes without conflating them into a conjunction.", "bell", {"alternatives": ["rope_pull", "button_press"]}, "Either pulling the rope or pressing the button could ring the bell.", "Both pulling the rope and pressing the button were required to ring the bell.", "bind_disjunctive_causal_routes", "typed_guard_disjunction"),
    ("causal_overdetermination", "Recognize stated multiple independently sufficient active causes without arbitrary single-cause selection.", "bell", {"active_sufficient_causes": ["rope_pull", "button_press"]}, "The rope and button each independently rang the bell, and both were used at once.", "The button alone was sufficient to ring the bell by moving the rope, which could not be operated independently. The button was pressed, the rope moved, and the bell rang.", "detect_independent_sufficient_cause_set", "counterfactual_causal_model"),
    ("causal_necessary_condition", "Record necessity only when an explicit rule or validated guard establishes it, not from one coincidence.", "door", {"necessary": "unlocked", "for": "ordinary_opening"}, "The rule for this door said it could open only if unlocked.", "The door happened to be unlocked on the one occasion it opened.", "extract_explicit_necessary_guard", "validated_action_guard_model"),
    ("causal_sufficient_condition", "Record sufficiency only within an explicitly specified complete condition set.", "bell", {"sufficient": "button_pressed_with_power"}, "The rule guaranteed that pressing the powered button rang the bell.", "Pressing the button sometimes rang the bell, depending on an unknown condition.", "extract_explicit_sufficient_guard", "validated_transition_rule"),
    ("causal_counterfactual_dependence", "Retain a stated or model-tested counterfactual dependence with its named effect and assumptions.", "door", {"without": "key_turn", "effect": {"entity": "@door", "change": "locked_to_unlocked"}, "evaluation_scope": "counterfactual", "effect_would_occur": False}, "The mechanism showed the door would have stayed locked if the key had not turned.", "The door would have unlocked through another mechanism even without the key turning.", "evaluate_scoped_counterfactual", "intervention_capable_causal_model"),
    ("causal_direction", "Preserve which event causes which rather than reversing a correlated pair.", "bell", {"from": "button_press", "to": "ringing"}, "The bell rang because Lily pressed the button.", "Lily pressed the button because the bell was already ringing.", "orient_explicit_causal_edge", "causal_connective_scope"),
    ("causal_scope", "Keep a causal claim inside its reported, hypothetical, or actual proposition scope.", "door", {"scope": "reported_belief", "holder": "@lily", "claim": "wind_opened_door"}, "Lily believed that the wind had opened the door, though nobody verified it.", "The measured trace confirmed that the wind physically opened the door.", "bind_causal_claim_epistemic_scope", "proposition_and_event_scope_graph"),
    ("causal_state_before", "Retrieve the relevant carrier state immediately before the identified event.", "door", {"before": "locked", "event": "unlocking"}, "The door was locked until Lily unlocked it.", "The door was already unlocked before Lily touched it.", "query_event_prestate", "event_snapshot_index"),
    ("causal_state_after", "Retrieve the immediate post-event state while distinguishing later overrides.", "door", {"after_opening": "open", "later": "closed"}, "Lily opened the door, then Ben closed it later.", "Lily tried to open the door but it never opened.", "query_event_poststate_not_latest", "event_snapshot_and_chronology"),
    ("causal_state_delta", "Compute the explicitly grounded changed fields between before and after the same event.", "cup", {"removed": ["empty"], "added": ["full"]}, "The cup was empty before Lily filled it and full afterward.", "The cup was full before and after Lily moved it.", "diff_bound_event_snapshots", "typed_state_difference"),
    ("causal_side_effect", "Distinguish a reported incidental physical consequence from the intended action goal.", "cloth", {"incidental_effect": "wet", "main_action": "fill_cup"}, "While filling the cup, Lily accidentally splashed water onto the cloth.", "Lily deliberately soaked the cloth as her main task.", "separate_goal_and_incidental_effect", "intent_effect_alignment"),
    ("causal_invariant", "Retain an explicitly checked property unchanged through an event rather than assuming total state persistence.", "cup", {"property": "ownership", "unchanged_owner": "@lily"}, "Lily moved her cup to the table and still owned it afterward.", "Lily gave ownership of the cup to Ben while moving it.", "compare_declared_preserved_field", "event_invariant_check"),
    ("causal_blocked_effect", "Represent a prevented predicted effect without recording that effect as actual.", "cup", {"would_be_effect": "breakage", "preventer": "soft_cloth"}, "The soft cloth caught the falling cup and prevented it from breaking.", "The cup missed the cloth and broke on the floor.", "link_intervention_to_prevented_result", "prevented_event_representation"),
    ("causal_delayed_effect", "Identify an explicitly delayed consequence without using a future outcome as a current fact.", "paint", {"expected_effect": "dry", "status": "pending"}, "The paint had just been applied and would need an hour to dry.", "The paint had already dried completely before Lily arrived.", "represent_pending_delayed_effect", "temporal_process_model"),
    ("causal_reversibility", "Determine whether a stated action model supplies a reversal of the affected state.", "door", {"change": "opening", "reversible_by": "closing"}, "The opened door could be closed again without damage.", "The door had been destroyed and could not be restored by closing it.", "check_inverse_state_transition", "reversible_action_model"),
    ("causal_inverse_action", "Retrieve an explicit inverse operation whose preconditions match the current changed state.", "sack", {"inverse": "untie", "change": "tied_shut"}, "The sack was tied shut, and untying its knot would reopen it.", "The sack was glued shut and had no knot to untie.", "match_inverse_operation_to_current_change", "inverse_transition_lookup_and_guards"),
    ("causal_compensation", "Distinguish compensating for a loss from undoing the original event.", "cup", {"compensation": "replacement", "original_restored": False}, "The broken cup could not be repaired, so Ben supplied a different replacement cup.", "Ben repaired the original cup completely without replacing it.", "separate_compensation_from_inverse", "entity_persistence_and_outcome_alignment"),
    ("causal_resource_consumption", "Link an event to a consumed resource using explicit before/after or action-model evidence.", "battery", {"resource": "charge", "direction": "decrease"}, "Running the motor used up charge from the battery.", "Charging the battery increased its stored charge.", "derive_resource_consumption_effect", "typed_resource_accounting"),
    ("causal_resource_production", "Link an event to produced material or usable energy without assuming conservation-free creation.", "fire", {"resource": "heat", "source": "burning_fuel"}, "The fire burned fuel and released heat into the room.", "The cold ashes of the extinguished fire produced no heat.", "derive_resource_output_with_source", "process_input_output_model"),
    ("causal_contact_transmission", "Bind an explicitly described effect transmitted through physical contact.", "cloth", {"transmitted": "moisture", "source": "@water"}, "Water touched the cloth and soaked into it.", "Water remained in a sealed bottle beside the dry cloth.", "follow_contact_mediated_transfer", "contact_and_material_process_model"),
    ("causal_support_removal", "Connect removal of a supporting carrier to the explicitly resulting loss of support.", "box", {"removed_support": "@board", "effect": "fell"}, "Lily pulled away the board supporting the box, and the box fell.", "Lily removed a nearby board that did not support the box.", "join_support_edge_removal_and_result", "support_dependency_graph"),
    ("causal_dependency_conflict", "Detect an action proposal whose required state is invalidated by another explicit update.", "door", {"proposal": "walk_through", "invalidated_requirement": "open"}, "Lily planned to walk through the open door, but Ben locked it shut first.", "Ben held the door open until Lily walked through.", "check_precondition_invalidation", "versioned_state_dependency_evaluation"),
]


# A contrast need not be a no-match. Generic relation/state resolvers must return
# the other grounded value where it is available, rather than selectively
# abstaining on examples that disagree with the illustrated positive answer.
CONTRAST_VALUES = {
    "spatial_configuration": {"relation": "above", "landmark": "@box", "modality": "possible", "time": "future"},
    "spatial_orientation": {"orientation": "inverted", "world": "depiction", "committed_physical_state": False},
    "spatial_contact": {"touches": None, "noncontact_landmark": "@box"},
    "spatial_support": {"supported_by": "@cord"},
    "spatial_overlap": {"overlaps": None, "boundary_contact": "@cloth"},
    "spatial_adjacency": {"adjacent_to": None, "separator": "@road"},
    "spatial_alignment": {"relative_to": "@rail", "alignment": "perpendicular"},
    "spatial_symmetry": {"relation": "not_symmetric", "axis": "gate_center_line"},
    "spatial_region": {"region": "corner", "landmark": "@table", "world": "imagined", "holder": "@lily"},
    "spatial_side": {"side": None, "boundary": "@gate"},
    "spatial_topology": {"relation": "externally_connected", "other_region": "@road"},
    "spatial_viewpoint": {"observer": "@lily", "vantage": "@roof", "scope": "remembered_view"},
    "spatial_extent": {"covers": "part_of_table"},
    "spatial_co_location": {"co_located_with": "@box", "simultaneous": False},
    "spatial_facing_target": {"faces": None, "away_from": "@gate"},
    "spatial_occlusion": {"observer": "@lily", "occluder": None},
    "spatial_anchor_stability": {"anchor": "@cart", "anchor_moving": False, "figure_detached": True},
    "spatial_layout_consistency": {"conflict": None, "reason": "different_intervals"},
    "motion_vehicle": {"vehicle": None, "nearby_vehicle": "@boat"},
    "motion_carrier": {"carrier": "@ben"},
    "motion_trajectory_phase": "arrived",
    "motion_speed_change": "constant_slow_speed",
    "motion_pace_variability": "steady",
    "motion_control": {"controller": None, "kind": "uncontrolled"},
    "motion_volition": "voluntary",
    "motion_contact": {"surface": "@floor", "contact": "intermittent"},
    "motion_support": {"support": "@lily", "previous_support": "@cart"},
    "motion_posture": "upright_after_motion",
    "motion_effort": "low",
    "motion_collectivity": {"companions": [], "coordination": "separate_episodes"},
    "motion_relative_displacement": {"relative_to": "@cart", "displacement": "backward"},
    "motion_path_reversal": {"route": "@path", "reversed": False},
    "motion_arrival_completion": {"arrived_at": None, "unreached_goal": "@gate"},
    "motion_boundary_crossing": {"boundary": "@gate", "crossed": False},
    "motion_stopping_location": {"stopped_at": None, "passed": "@gate"},
    "motion_collision": {"collided_with": None, "near_miss": "@gate"},
    "motion_destination_change": {"destination": "@shed", "waypoint": "@garden", "changed": False},
    "motion_transport_constraint": {"blocked_by": None, "clearance": "sufficient"},
    "containment_depth": {"outer": "@box", "edges": 1},
    "containment_relation_kind": "supported_on",
    "containment_opening": {"opening": None, "sealed": True},
    "containment_boundary_state": "open_no_lid",
    "containment_nested_access": {"actor": "@lily", "reachable": True, "barrier": None},
    "containment_escape_route": {"exit": None, "failed_clearance": "@hole"},
    "containment_spill_risk": "not_supported_while_seal_intact",
    "containment_capacity_fit": {"fits": True},
    "containment_contents": {"contents": ["@cup"]},
    "containment_partial": {"inside_fraction": "complete", "container": "@box"},
    "containment_reachable_contents": {"reachable_contents": []},
    "access_reachability": {"actor": "@lily", "reachable": False},
    "access_key_requirement": {"required_key": None, "incompatible_key": "@key"},
    "access_clearance": {"passage": "@door", "fits": False},
    "access_visibility": {"observer": "@lily", "visible": False},
    "access_audibility": {"listener": "@lily", "audible": True},
    "access_line_of_sight": {"observer": "@lily", "clear": False},
    "access_touchability": {"actor": "@lily", "touchable": True},
    "access_mobility_requirement": {"required": "ordinary_level_traversal"},
    "access_entry_side": {"operable_side": "either"},
    "access_exit_side": {"allowed_direction": "both"},
    "access_bottleneck": {"bottleneck": None, "bypass": "@path"},
    "access_blocking_object": {"obstruction": None},
    "possession_holder": {"holder": "@lily"},
    "possession_owner": {"owner": "@ben"},
    "possession_custodian": {"custodian": None, "finder": "@ben"},
    "possession_borrower": {"borrower": None, "planned_borrower": "@ben"},
    "possession_lender": {"lender": "@nia"},
    "possession_user": {"user": None, "holder": "@ben"},
    "possession_reservation": {"reserved_for": None},
    "possession_recoverability": {"recoverable": False, "reason": "inaccessible_sealed_shaft"},
    "possession_shared": {"holders": ["@lily"]},
    "possession_disputed": {"claimants": ["@lily"], "resolved": True},
    "possession_custody_chain": {"holders": ["@lily", "@ben"]},
    "possession_return_target": {"return_to": None, "transaction": "gift"},
    "possession_transfer_permission": {"may_pass_to": None, "forbidden_recipient": "@nia"},
    "possession_transferability": {"transferable": True},
    "possession_unattended": {"unattended": False, "watcher": "@ben"},
    "transfer_object": {"theme": "@box", "recipient": "@ben", "focused_cup_retained": True},
    "transfer_source": {"source": "@nia"},
    "transfer_recipient": {"recipient": "@nia"},
    "transfer_kind": "gift",
    "transfer_completion": {"completed": False, "proposed_recipient": "@ben"},
    "transfer_failed_precondition": {"missing": None},
    "transfer_handoff_location": {"location": "@garden"},
    "transfer_joint_participation": {"participants": ["@lily", "@cup", "@ben"], "shared_single_handoff": False},
    "transfer_retained_ownership": {"owner": "@ben", "holder": "@ben"},
    "transfer_recipient_acceptance": {"recipient": "@ben", "accepted": False},
    "transfer_return_due": {"due_condition": None, "transaction": "gift"},
    "transfer_exchange_counterpart": {"counterpart": None, "transaction": "gift"},
    "transfer_delivery_destination": {"destination": "@garden"},
    "transfer_delivery_intermediary": {"intermediary": None, "recipient": "@ben"},
    "transfer_delegated_custody": {"new_holder": "@nia", "authorized": False},
    "transfer_lost_custody": {"previous_holder": "@lily", "holder": "@ben"},
    "affordance_carrying": {"actor": "@lily", "can_carry": False},
    "affordance_grasping": {"actor": "@lily", "graspable": False},
    "affordance_climbing": {"actor": "@lily", "climbable": False},
    "affordance_sitting": {"actor": "@lily", "sittable": False},
    "affordance_containing": {"contents": "water", "suitable": True},
    "affordance_traversal": {"actor": "@lily", "traversable": False},
    "affordance_eating": {"edible": False},
    "affordance_drinking": {"drinkable": False},
    "affordance_cutting": {"patient": "@sheet", "suitable": False},
    "affordance_fastening": {"patient": "@board", "suitable": False},
    "affordance_illumination": {"target": "@key", "suitable": False},
    "affordance_warming": {"target": "@cat", "suitable": False},
    "affordance_writing": {"surface": "@board", "suitable": False},
    "affordance_repair": {"patient": "@glass", "suitable": False},
    "affordance_unlocking": {"lock": "@lock", "suitable": False},
    "affordance_sheltering": {"protects_from": None, "exposure": "rain"},
    "event_initiator": {"initiator": "@ben", "focused_entity_role": "patient"},
    "event_causer": {"causer": "@lily"},
    "event_effector": {"effector": "@motor", "focused_entity_role": "observer"},
    "event_theme": {"theme": "@lily", "focused_box_stationary": True},
    "event_instrument_binding": {"used_on": None, "other_instrument": "@glue"},
    "event_goal_role": {"goal_state": "closed", "achieved": None},
    "event_beneficiary": {"beneficiary": "@lily", "helper": "@ben"},
    "event_setting": {"setting": "@garden"},
    "event_progress": {"progress": "complete", "completed": True},
    "event_collective_participants": {"actors": ["@lily"], "joint": False},
    "event_role_conflict": {"conflict": None, "reason": "sequential_requirements"},
    "event_control": {"controller": None, "mode": "uncontrolled"},
    "event_volition": {"action": "drop_cup", "intentional": True},
    "event_contact_mode": {"mode": "sustained_gentle_contact", "effector": "@stone"},
    "event_manner": {"event": "close_door", "manner": "slamming"},
    "event_attempt_outcome": {"attempt": "open", "outcome": "succeeded"},
    "event_state_change": {"before": "closed", "after": None, "modality": "desired"},
    "event_creation": {"created": False, "preexisting": True},
    "event_destruction": {"destroyed": False, "hidden": True},
    "event_role_reassignment": {"holder": "@ben", "role_changed": False},
    "causal_preventing_condition": {"condition": "bar_beside_door", "blocked": None},
    "causal_sustaining_condition": {"sustainer": "stored_energy", "external_power_required_now": False},
    "causal_termination_condition": {"terminator": None, "process_continues": True},
    "causal_joint_cause": {"required_together": None, "alternatives": ["key_turned", "handle_pressed"]},
    "causal_alternative_cause": {"alternatives": None, "required_together": ["rope_pull", "button_press"]},
    "causal_overdetermination": {"active_sufficient_causes": ["button_press"], "mediator": "rope_motion"},
    "causal_counterfactual_dependence": {"without": "key_turn", "effect": {"entity": "@door", "change": "locked_to_unlocked"}, "evaluation_scope": "counterfactual", "effect_would_occur": True},
    "causal_direction": {"from": "ringing", "to": "button_press"},
    "causal_scope": {"scope": "verified_trace", "claim": "wind_opened_door"},
    "causal_state_before": {"before": "unlocked", "event": "touching"},
    "causal_state_after": {"after_attempt": "closed", "opening_occurred": False},
    "causal_state_delta": {"removed": [], "added": [], "property": "fill_state"},
    "causal_side_effect": {"incidental_effect": None, "main_action": "soak_cloth"},
    "causal_invariant": {"property": "ownership", "preserved": False, "new_owner": "@ben"},
    "causal_blocked_effect": {"actual_effect": "breakage", "prevented": False},
    "causal_delayed_effect": {"effect": "dry", "status": "completed"},
    "causal_reversibility": {"change": "destruction", "reversible_by_closing": False},
    "causal_inverse_action": {"inverse": None, "inapplicable": "untie", "change": "glued_shut"},
    "causal_compensation": {"compensation": None, "original_restored": True},
    "causal_resource_consumption": {"resource": "charge", "direction": "increase"},
    "causal_resource_production": {"resource": "heat", "produced": False},
    "causal_dependency_conflict": {"proposal": "walk_through", "invalidated_requirement": None},
}


def build():
    catalog = Catalog("world", 513)
    _contracts(catalog, "world.spatial", SPATIAL)
    _motion_native(catalog)
    _contracts(catalog, "world.motion", MOTION_ADAPTERS)
    _contracts(catalog, "world.containment_access", CONTAINMENT_ACCESS)
    _contracts(catalog, "world.possession_transfer", POSSESSION_TRANSFER)
    _copula(catalog, "world.object_state", OBJECT_STATES)
    _copula(catalog, "world.material_affordance", MATERIALS)
    _contracts(catalog, "world.material_affordance", AFFORDANCES)
    _event_native(catalog)
    _contracts(catalog, "world.event_structure", EVENT_ADAPTERS)
    _contracts(catalog, "world.causality", CAUSAL)
    assert len(catalog.attributes) == 256
    return catalog.records()
