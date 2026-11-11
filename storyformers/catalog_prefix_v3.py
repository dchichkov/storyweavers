"""Reconciled causal catalog: explicit plot readings and depicted referents.

The v2 contract remains available for frozen runs. New bundles are annotation
evidence, not engine traces or executable plot-planning state.
"""

from functools import lru_cache
import json
import re

from . import catalog_prefix_annotation as base
from .annotation import MODEL, fingerprint, story_tokens

ROOT, META = base.ROOT, base.META
VERSION = "storyformers-prefix-catalog-v3"
PROMPT = ROOT / "prompts/annotate_prefix_catalog_v3.txt"
EXAMPLES = ROOT / "data/prefix_catalog_examples_v3.json"
EXTENSIONS = ROOT / "data/prefix_extensions_v3.json"
CHECKLIST = ROOT / "prompts/prefix_catalog_v3_checklist.txt"
PLOT_ROLES = set("desire lack promise setback failed_attempt threat conflict clue discovery choice revision help attempt decisive_action payoff final_image supporting_action".split())
STAGES = set("setup complication development resolution aftermath support".split())
ARCHETYPES = set("overcoming_the_monster rags_to_riches quest voyage_and_return comedy tragedy rebirth mystery rebellion".split())


@lru_cache(maxsize=1)
def registry():
    result = {key: dict(value) for key, value in base.registry().items()}
    result["modal_auxiliary_class"]["values"] = ["can", "may", "must", "shall", "will", "ought", "need", "dare"]
    for definition in json.loads(EXTENSIONS.read_text()):
        if definition["key"] in result:
            raise ValueError("extension must not redefine an existing field")
        result[definition["key"]] = definition
    return result


def validate_record(text, row):
    row = base.validate_record(text, row, definitions=registry())
    spans = story_tokens(text)
    scopes = row.get("_references", {}).get("scopes", {})
    for identifier in scopes:
        if identifier.startswith("q") and spans[int(base.ID.fullmatch(identifier)[2]) - 1]["token"] not in {'"', "“", "‘", "'", "«"}:
            raise ValueError("quotation ID must anchor to an opening quote span, counting index plus one")
        current, seen = identifier, set()
        while current in scopes:
            if current in seen:
                raise ValueError("scope ancestry must not contain cycles")
            seen.add(current)
            current = scopes[current].get("parent")
            if current is not None and not isinstance(current, str):
                raise ValueError("scope parent must be a scope ID")
    if "plot" in row:
        plot = row["plot"]
        required = {"plot_id", "role", "stage", "basis", "scope", "status", "evidence_indices"}
        optional = {"archetypes", "local_pattern", "goal", "roles", "unbound_roles", "stakes", "incoming_links"}
        if not isinstance(plot, dict) or not required <= plot.keys() or plot.keys() - required - optional:
            raise ValueError("plot needs the declared prefix interpretation fields; engine trace fields are not annotations")
        match = re.fullmatch(r"plot([1-9]\d*)", plot["plot_id"]) if isinstance(plot["plot_id"], str) else None
        if not match or int(match[1]) > len(spans) or spans[int(match[1]) - 1]["kind"] != "word":
            raise ValueError("plot_id must anchor to an already visible issue/goal word")
        if (not isinstance(plot["role"], str) or plot["role"] not in PLOT_ROLES or
                not isinstance(plot["stage"], str) or plot["stage"] not in STAGES):
            raise ValueError("unsupported plot role/stage")
        if (not isinstance(plot["basis"], str) or plot["basis"] not in {"prefix_interpretation", "neutral_default"} or
                plot["scope"] != "observed_prefix" or plot["status"] != "candidate"):
            raise ValueError("plot readings must remain prefix-grounded interpretation candidates")
        evidence = plot["evidence_indices"]
        if not isinstance(evidence, list) or not evidence or any(type(i) is not int or not 0 <= i < len(spans) for i in evidence):
            raise ValueError("plot needs nonempty prefix-local evidence_indices")
        for field in ("goal", "local_pattern"):
            if field in plot and (not isinstance(plot[field], str) or not plot[field].strip()):
                raise ValueError(f"plot.{field} must be a nonempty string")
        roles = plot.get("roles", {})
        if not isinstance(roles, dict) or any(not isinstance(ids, list) or any(not isinstance(i, str) or not re.fullmatch(r"e[1-9]\d*", i) for i in ids) for ids in roles.values()):
            raise ValueError("plot.roles maps cast roles to entity ID arrays")
        unbound = plot.get("unbound_roles", [])
        if not isinstance(unbound, list) or any(not isinstance(v, str) for v in unbound):
            raise ValueError("plot.unbound_roles must be strings")
        if "stakes" in plot and (not isinstance(plot["stakes"], dict) or
                set(plot["stakes"]) != {"description", "basis"} or
                any(not isinstance(v, str) or not v.strip() for v in plot["stakes"].values())):
            raise ValueError("plot.stakes needs description and basis strings")
        archetypes = plot.get("archetypes", [])
        if not isinstance(archetypes, list):
            raise ValueError("plot.archetypes must be a list")
        for item in archetypes:
            if (not isinstance(item, dict) or set(item) != {"name", "fit", "basis"} or
                    not isinstance(item["name"], str) or item["name"] not in ARCHETYPES or
                    item["fit"] != "partial" or item["basis"] != "prefix_interpretation"):
                raise ValueError("archetypes must be partial prefix interpretations, not completed arc predictions")
        links = plot.get("incoming_links", [])
        if not isinstance(links, list):
            raise ValueError("plot.incoming_links must be a list")
        for link in links:
            if not isinstance(link, dict) or set(link) != {"source_event", "relation", "basis", "mechanically_verified"}:
                raise ValueError("plot link needs source_event, relation, basis and mechanically_verified")
            anchor = base.ID.fullmatch(link["source_event"]) if isinstance(link["source_event"], str) else None
            if (not anchor or anchor[1] != "ev" or int(anchor[2]) - 1 >= row["index"] or
                    link["mechanically_verified"] is not False or link["basis"] != "prefix_interpretation" or
                    not isinstance(link["relation"], str) or not link["relation"].strip()):
                raise ValueError("plot links need an earlier event and must not claim mechanical verification")
    if "depiction" in row:
        depiction = row["depiction"]
        required = {"carrier_id", "image_entity_id", "medium", "scope_id"}
        if not isinstance(depiction, dict) or not required <= depiction.keys() or depiction.keys() - required - {"referent_id"}:
            raise ValueError("depiction needs carrier_id, image_entity_id, medium and scope_id")
        for key in ("carrier_id", "image_entity_id", "referent_id"):
            if key in depiction and (not isinstance(depiction[key], str) or not re.fullmatch(r"e[1-9]\d*", depiction[key])):
                raise ValueError("depiction participants must be entity references")
        if (depiction["image_entity_id"] != row.get("entity_id") or
                depiction["image_entity_id"] in {depiction["carrier_id"], depiction.get("referent_id")} or
                depiction["scope_id"] != row["scope_id"] or
                not isinstance(depiction["medium"], str) or
                depiction["medium"] not in {"drawing", "reflection", "photograph", "sculpture", "other"}):
            raise ValueError("depicted entity, carrier and physical referent must stay distinct and scoped")
    return row


def shared_prefix(prompt_file=PROMPT, examples_file=EXAMPLES):
    prefix = base.shared_prefix(prompt_file, examples_file, validator=validate_record,
                                definitions=registry(), extra_definitions=json.loads(EXTENSIONS.read_text()))
    # Keep the compact coverage reminder after the large catalog, still inside
    # the shared cached instructions and before any variable story text.
    return prefix + "\n" + CHECKLIST.read_text().strip() + "\n"


def prefix_request(story, index, *, prefix=None, reasoning="low", max_output_tokens=4096):
    prefix = shared_prefix() if prefix is None else prefix
    body = base.prefix_request(story, index, prefix=prefix, reasoning=reasoning, max_output_tokens=max_output_tokens)
    body["prompt_cache_key"] = VERSION + ":" + fingerprint([prefix, MODEL, body["reasoning"], body["text"]])[:24]
    return body


def assemble(story, records):
    return base.assemble(story, records, validator=validate_record)
