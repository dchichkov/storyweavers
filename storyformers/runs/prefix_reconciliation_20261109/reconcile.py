"""Explicit agent review patches, applied only to the 17 diagnostic prefixes.

No API calls. Provider records and the original full story stay unchanged.
Each reviewed example is validated against its own visible prefix.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from storyformers import catalog_prefix_v3 as contract
from storyformers.annotation import story_tokens
from storyformers.prefix_annotation import request_prefix
from storyformers.prefix_review import ROOT, score

OUT = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def replace(value, old, new):
    if isinstance(value, dict):
        return {new if k == old else k: replace(v, old, new) for k, v in value.items()}
    if isinstance(value, list):
        return [replace(v, old, new) for v in value]
    return new if value == old else value


def plot(role, stage, evidence, **extra):
    return dict(plot_id="plot271", role=role, stage=stage, basis="prefix_interpretation",
                scope="observed_prefix", status="candidate", evidence_indices=evidence, **extra)


def entity(name, kind="person", **extra):
    return dict(name=name, type=kind, **extra)


def event(label, kind="other", scope="s0", factuality="asserted", **extra):
    return dict(event=label, event_type=kind, scope_id=scope, factuality=factuality, **extra)


def reconcile(index, source):
    row = deepcopy(source)
    note = "Accepted for this focused review; not an exhaustive annotation of every possible field."
    if index == 151:
        row.update(event="ask for help", event_id="ev148", event_type="speak", role="patient",
                   factuality="negated", event_bindings=[dict(event_id="ev148", role="patient", scope_id="s146")],
                   goal_scope_bundle=dict(owner_id="e30", intention_event_id="ev130", scope_id="s0", assertion_status="asserted"))
        row["_references"]["events"]["ev148"]["patients"] = ["e152"]
        row["_references"]["propositions"].pop("p148", None)
        row["_references"]["propositions"]["p148_negative"] = dict(
            content="Nia does not ask for help", polarity="negative", scope_id="s130")
        note = "Keep the asking event locally negated inside desire, with its patient; distinguish the complete negative proposition from a positive asking target."
    elif index == 278:
        row = dict(index=index, token="her", pos="pron", lemma="she", scope_id="s271",
                   entity="person", entity_id="e193", entity_name="Leni", antecedent_id="e193",
                   grammatical_case="objective", role="prepositional_object",
                   event="keep beside person", event_id="ev275", event_type="state", factuality="desired",
                   promise_content_id="p275", plan_commitment_status="promised",
                   obligation_debtor_id="e265", obligation_content_id="p275", obligation_status="promised",
                   plot=plot("promise", "setup", [192, 264, 268, 270, 274, 278]),
                   _references={
                       "entities": {"e30": entity("Nia"), "e155": entity("Felix"), "e193": entity("Leni"),
                                    "e265": entity("Nia and Felix", "group", members=["e30", "e155"])},
                       "events": {"ev271": event("promise", "speak", actor_id="e265"),
                                  "ev275": event("keep beside person", "state", "s271", "desired", actor_id="e265", companion_id="e193")},
                       "scopes": {"s271": dict(kind="promised", parent="s0", holder_id="e265")},
                       "propositions": {"p275": dict(content="Nia and Felix keep beside Leni", polarity="positive", scope_id="s271")}})
        note = "Her is Leni, not Nia. The jointly named promisers are Nia and Felix; preserve their group and the promised content, without claiming compliance."
    elif index == 522:
        row = replace(row, "e494", "e155")
        note = "Felix's first named anchor is e155, not the recent watch-checking mention. Available forty minutes is correctly temporal_remaining."
    elif index == 641:
        row = replace(replace(row, "e191", "e193"), "e448", "e450")
        row["_references"]["propositions"]["p634_negative"]["content"] = "Leni cannot do the Fern Loop at a sprint"
        row["_references"]["propositions"]["p634_negative"]["scope_id"] = "q627"
        row["_references"]["propositions"]["p634"]["scope_id"] = "s632"
        note = "Keep negated ability under q627; correct Leni and Loop head anchors. Cannot is inability, not merely non-occurrence. Put the complete negative claim in its quotation."
    elif index == 773:
        row = replace(row, "e448", "e450")
        row["plot"] = plot("choice", "development", [270, 631, 641, 765, 773],
                           goal="Keep the group together on an accessible route",
                           roles={"protagonist": ["e30", "e155", "e193"]},
                           incoming_links=[dict(source_event="ev271", relation="responds_to", basis="prefix_interpretation", mechanically_verified=False)])
        row["_references"]["events"]["ev271"] = event("promise to keep beside Leni", "speak")
        note = "Turning onto the selected loop is a supported choice after the accessibility discussion; it does not establish arrival or success. Correct the route's noun-head anchor."
    elif index == 876:
        row = replace(row, "e13", "e450")
        row["entity_name"] = "Fern Loop"
        row["_references"]["entities"]["e450"]["name"] = "Fern Loop"
        row["plot"] = plot("setback", "complication", [765, 773, 868, 870, 872, 876],
                           goal="Keep the group together on an accessible route",
                           incoming_links=[dict(source_event="ev766", relation="obstructs", basis="prefix_interpretation", mechanically_verified=False)])
        row["_references"]["events"]["ev766"] = event("turn onto Fern Loop", "move")
        note = "The birch obstructs the route the group is following; add the locally evidenced setback, without predicting defeat or the future detour."
    elif index == 961:
        row.update(utterance_content_id="p962_negative", assertion_status="attributed_claim",
                   quote_mode="direct", speech_act_kind="safety_objection")
        row["_references"]["propositions"] = {"p962_negative": dict(
            content="Climbing over the fallen birch is not safe", polarity="negative", scope_id="q959")}
        note = "Resolve the negative elliptical safety objection against the proposed climb. Keep speaker unresolved; q959 is the current opening quote, not q958."
    elif index == 1112:
        row = replace(row, "q1061", "q1083")
        row.update(speaker_id="e30", quote_mode="direct", utterance_content_id="p1107")
        row["_references"]["entities"]["e30"] = entity("Nia")
        row["_references"]["scopes"]["q1083"]["speaker_id"] = "e30"
        row["_references"]["propositions"]["p1107"]["content"] = "The group can look for the detour if they go back to the last blue marker"
        row["_references"]["propositions"]["p1107"]["scope_id"] = "q1083"
        note = "The earlier quotation has closed. This conditional belongs to q1083; Nia is supported by the preceding she-said attribution and continuing subject. No detour search has happened yet."
    elif index == 1518:
        row["_references"]["scopes"] = {"s157": dict(kind="desired", parent="s0", holder_id="e155")}
        row["_references"]["propositions"]["p157"].update(
            content="Felix obtains the last copper-acorn stamp on his discovery card", scope_id="s157")
        row["plot"]["goal"] = "Obtain the last copper-acorn stamp on Felix's discovery card"
        row["goal_scope_bundle"] = dict(owner_id="e155", intention_event_id="ev157", scope_id="s0", assertion_status="asserted")
        note = "The payoff is supported, but its goal content is obtaining the stamp, not the fact that Felix wants it. Retain desired-content identity and cite the actual stamping as fulfillment."
    elif index == 1659:
        row["_references"]["scopes"]["s206"] = dict(kind="desired", parent="s0", holder_id="e193")
        row["_references"]["propositions"]["p210"]["scope_id"] = "s206"
        row["narrative_resolution_evidence"] = dict(problem="p210", outcome="ev1411", status="explicitly_closed")
        note = "The new output correctly separates desired-kind, physical salamander and drawing. Preserve the original goal's desired scope and bind the actual drawing as fulfillment evidence."
    elif index == 1671:
        row["_references"]["entities"].update({"e30": entity("Nia"), "e155": entity("Felix"), "e193": entity("Leni")})
        row["plot"] = plot("final_image", "aftermath", [1518, 1523, 1557, 1631, 1646, 1659, 1671],
                           roles={"protagonist": ["e30", "e155", "e193"]},
                           local_pattern="group_still_together_with_card_map_and_drawing")
        note = "The visible image gathers the group's changed objects after the stamp and drawing outcomes. Add only a candidate ending-image reading; no future text or end-of-file fact is used."
    if row != source:
        # Replace stale model explanations instead of leaving notes that describe
        # a corrected wrong identity or quote as evidence for the new record.
        supporting = {278: [192, 264, 268, 270, 274], 522: [154, 493, 502, 520],
                      641: [192, 447, 449, 626, 631], 773: [270, 765, 773],
                      1112: [29, 1077, 1079, 1082, 1083], 1671: [1518, 1523, 1557, 1631, 1646, 1659]}
        indices = sorted({i for item in source.get("_evidence", []) for i in item["indices"]} |
                         {index} | set(supporting.get(index, [])))
        row["_evidence"] = [dict(indices=indices, note=note)]
    return row, note


def main():
    spec = read(OUT / "cases.json")
    story = (ROOT / spec["story_file"]).read_text()
    spans = story_tokens(story)
    baseline = ROOT / spec["baseline_directory"]
    runs = {"baseline": baseline, "v3_initial": OUT / "luna_v3", "v3_refined": OUT / "luna_v3_refined"}
    records, evaluation = {}, {}
    for name, folder in runs.items():
        records[name] = {case["index"]: read(folder / f"prefixes/{case['index']:06d}/annotation.json") for case in spec["cases"]}
        evaluation[name] = score(spec["cases"], records[name])
    reconciled, examples, changes = {}, [], []
    for case in spec["cases"]:
        index = case["index"]
        prefix = story[:spans[index]["end"]]
        row, note = reconcile(index, records["v3_refined"][index])
        contract.validate_record(prefix, row)
        source = records["v3_refined"][index]
        fields = sorted(k for k in set(row) | set(source) if row.get(k) != source.get(k))
        reconciled[index] = row
        examples.append(dict(prefix=prefix, response=row, review_note=note, source=f"luna_v3_refined/prefixes/{index:06d}/annotation.json"))
        changes.append(dict(index=index, token=row["token"], changed_fields=fields, note=note))
        request = read(OUT / f"luna_v3_refined/prefixes/{index:06d}/request.json")
        assert request_prefix(request) == prefix
    evaluation["agent_reconciled"] = score(spec["cases"], reconciled)
    evaluation["caveat"] = "Diagnostic checks selected and refined during review, not held-out accuracy. Raw model output and explicit agent corrections remain separate. A passing case is not proof of complete semantics."
    save("evaluation.json", evaluation)
    save("reconciled_records.json", list(reconciled.values()))
    save("reviewed_examples.json", examples)
    save("changes.json", changes)

    usage_report = {}
    rates = read(ROOT / "storyformers/runs/prefix_catalog_full_story_20261108/measured_metrics.json")["pricing"]["usd_per_million"]
    for name in ("v3_initial", "v3_refined"):
        folder = runs[name]
        usages = [read(p)["usage"] for p in folder.glob("prefixes/**/response.json")]
        total = sum(u["input_tokens"] for u in usages)
        cached = sum(u.get("input_tokens_details", {}).get("cached_tokens", 0) for u in usages)
        writes = sum(u.get("input_tokens_details", {}).get("cache_write_tokens", 0) for u in usages)
        output = sum(u["output_tokens"] for u in usages)
        keys = Counter(k for r in records[name].values() for k in r if k not in contract.META | {"index", "token"})
        cost = ((total-cached-writes)*rates["input"] + cached*rates["cached_input"] + writes*rates["cache_write_30m"] + output*rates["output"])/1e6
        usage_report[name] = dict(words=17, responses=len(usages), input_tokens=total, cached_tokens=cached,
                                 cache_write_tokens=writes, output_tokens=output, cache_read_fraction=cached/total,
                                 estimated_cost_usd=cost, fields=dict(occurrences=sum(keys.values()), distinct=len(keys), mean=sum(keys.values())/17))
    usage_report["pricing_basis"] = "Archived Luna/Flex rate snapshot checked 2026-11-08; calculated estimate, not an invoice. Includes all correction responses."
    save("usage.json", usage_report)
    print(json.dumps({k: {f: v for f, v in value.items() if f != "cases"} for k, value in evaluation.items() if isinstance(value, dict)}, indent=2))


if __name__ == "__main__":
    main()
