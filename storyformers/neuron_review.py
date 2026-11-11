"""Collect evidence, stage neuron revisions, and gate them on held-out data.

No API dependency: proposals can come from a person, an LLM, or search. The
optional LLM entry point lives in refine.py. Generation never calls an LLM.
"""

from collections import Counter, defaultdict
from copy import deepcopy
import json
import math
import re

from .annotation import fingerprint
from .grammar import Lookup, MatchBudgetExceeded, OneOf, Ref, canonical, pack
from .neuron_spec import (TYPES, check_value, encode, neuron_spec, neurons, parse_neuron,
                          rebind_feature, registry_for)
from .transformer import Residual, semantic


VERSION = "storyformers-neuron-review-v1"


def model_fingerprint(model):
    return fingerprint(dict(context_size=model.context_size, top_k=model.top_k, features=model.features,
                            definition=pack(dict(projection=model.projection, layers=model.layers))))


def locate(model, address):
    if not isinstance(address, dict):
        raise ValueError("neuron address must be an object")
    if address.get("kind") == "head" and set(address) == {"kind", "layer", "head"}:
        layer, slot = address["layer"], address["head"]
        if (type(layer) is not int or type(slot) is not int or not 0 <= layer < len(model.layers)
                or not 0 <= slot < len(model.layers[layer].heads) or model.layers[layer].heads[slot] is None):
            raise ValueError("head address is not populated")
        return model.layers[layer].heads[slot].neuron
    if address.get("kind") == "output" and set(address) == {"kind", "token"}:
        if address["token"] not in model.projection.neurons:
            raise ValueError("output token has no grammar root")
        return model.projection.neurons[address["token"]]
    raise ValueError("use a head layer/slot or an output token address")


def _input(model, context, address):
    rows = model._prepare(context)[-model.context_size:]
    stream = [Residual.from_latent(row) for row in rows]
    stop = address["layer"] if address["kind"] == "head" else len(model.layers)
    for layer in model.layers[:stop]:
        stream, _ = layer.forward(stream)
    return [row.view() for row in stream]


def metrics(model, documents, registry=None):
    """Full next-latent probabilities, not top-k-renormalized token scores."""
    cache, total, supported, losses, conflicts = {}, 0, 0, [], 0
    for context, target in model.examples(documents):
        key = canonical(context)
        if key not in cache:
            history, stream, trace = model._run(context)
            views = [row.view() for row in stream]
            distribution = model.projection.read(views, model.top_k, position_context=history)
            if registry is not None:
                for row in views + [candidate["latent"] for candidate in distribution.joint]:
                    for name, value in row.items():
                        if name not in registry:
                            raise ValueError(f"undeclared feature: {name}")
                        check_value(value, registry[name])
                observed = {row["position"]["token"]: row for row in history}
                for update in trace:
                    head = model.layers[update["layer"]].heads[update["head"]]
                    for name, value in update["values"].items():
                        check_value(value, registry[name])
                        gold = observed[update["query"]].get(name)
                        conflicts += (head.operation == "add" and gold is not None
                                      and canonical(gold) != canonical(value))
            cache[key] = distribution
        probability = cache[key].probability(target)
        total += 1
        supported += probability > 0
        if probability:
            losses.append(-math.log(probability))
    if not total:
        raise ValueError("evaluation requires at least one target")
    return dict(targets=total, coverage=supported / total,
                joint_nll=math.fsum(losses) / total if supported == total else None,
                observed_attribute_conflicts=conflicts)


def collect(model, documents, address, *, max_examples=4, context_tail=16):
    """Profile only training data; expose helpful/harmful matches and missed cases."""
    if type(max_examples) is not int or max_examples < 1 or type(context_tail) is not int or context_tail < 1:
        raise ValueError("example and context-tail bounds must be positive integers")
    documents = list(documents)
    neuron = locate(model, address)
    ablated = deepcopy(model)
    locate(ablated, address).rules = ()  # Ablate all references to this shared neuron.
    grouped, contexts = defaultdict(Counter), {}
    for context, target in model.examples(documents):
        key = canonical(context)
        grouped[key][canonical(semantic(target))] += 1
        contexts[key] = context
    if not grouped:
        raise ValueError("profiling requires training targets")
    cases, outcomes, emitted, rules = [], Counter(), Counter(), Counter()
    matched, total, derivations = 0, 0, 0
    for key in sorted(grouped):
        context = contexts[key]
        inputs = _input(model, context, address)
        matches = [] if address["kind"] == "head" and not inputs else neuron.activate(inputs)
        actual, without = model.predict(context), ablated.predict(context)
        for target_key, count in grouped[key].items():
            target = json.loads(target_key)
            probability, removed = actual.probability(target), without.probability(target)
            delta = math.log(probability / removed) if probability and removed else None
            total += count
            if matches:
                matched += count
                outcomes[target_key] += count
                derivations += count * len(matches)
                for match in matches:
                    rules[match.rule] += count
                    emitted[canonical(match.value)] += count
            cases.append(dict(context_tail=context[-context_tail:], neuron_input_tail=inputs[-context_tail:],
                              omitted_context=max(0, len(context) - context_tail), target=target, count=count,
                              probability=probability, ablated_probability=removed,
                              delta_log_probability=delta,
                              activations=[dict(rule=match.rule, mass=match.mass, emit=match.value,
                                                sources=match.sources) for match in matches]))
    def helpful(case):
        if case["probability"] and not case["ablated_probability"]:
            return math.inf
        return case["delta_log_probability"] or 0.
    matched_cases = [case for case in cases if case["activations"]]
    missed = [case for case in cases if not case["activations"]]
    packet = dict(format=VERSION, base_model_sha256=model_fingerprint(model), address=deepcopy(address),
                  training_data_sha256=fingerprint(documents), context_size=model.context_size,
                  neuron=neuron_spec(neuron), registry=registry_for(model, documents),
                  stats=dict(targets=total, matched_targets=matched, derivations=derivations,
                             unique_prefixes=len(grouped), rule_support={str(key): value for key, value in rules.items()},
                             outcomes=[dict(target=json.loads(value), count=count)
                                       for value, count in outcomes.most_common(20)],
                             projections=[dict(emit=json.loads(value), count=count)
                                          for value, count in emitted.most_common(20)]),
                  examples=dict(matched_examples=sorted(matched_cases, key=lambda case: -case["count"])[:max_examples],
                                helpful_matches=sorted([case for case in matched_cases if helpful(case) > 0],
                                                       key=helpful, reverse=True)[:max_examples],
                                harmful_matches=sorted([case for case in matched_cases if helpful(case) < 0],
                                                       key=helpful)[:max_examples],
                                unmatched_high_loss=sorted(missed, key=lambda case: case["probability"])[:max_examples]),
                  evidence_scope="Training prefixes and next targets only. No validation or test examples.")
    if address["kind"] == "head":
        head = model.layers[address["layer"]].heads[address["head"]]
        packet["head_controls"] = dict(operation=head.operation, strength=head.strength, null_mass=head.null_mass)
    packet["sharing"] = dict(
        instances=[dict(kind="head", layer=layer, head=slot) for layer, block in enumerate(model.layers)
                   for slot, head in enumerate(block.heads) if head and head.neuron is neuron] +
                  [dict(kind="output", token=word) for word, root in model.projection.neurons.items() if root is neuron],
        rules=[dict(rule=index, other_neurons=[other.name for other in neurons(model) if other is not neuron
                                              and any(shared is rule for shared in other.rules)])
               for index, rule in enumerate(neuron.rules)])
    packet["feature_consumers"] = {}
    for feature in {name for rule in neuron.rules for name in rule.emit}:
        readers, writers = [], []
        def uses(value):
            if isinstance(value, Ref):
                parts = value.path.split(".")
                return len(parts) > 1 and parts[1] == feature
            if isinstance(value, Lookup):
                return uses(value.key)
            if isinstance(value, OneOf):
                return uses(value.values)
            if isinstance(value, dict):
                return any(uses(item) for item in value.values())
            if isinstance(value, (list, tuple)):
                return any(uses(item) for item in value)
            return False
        def reads(pattern):
            return (any(path.split(".")[0] == feature for path in pattern.tests) or uses(pattern.tests)
                    or any(reads(child) for child in pattern.children))
        for other in neurons(model):
            for index, rule in enumerate(other.rules):
                if reads(rule.pattern) or uses(rule.emit):
                    readers.append(dict(neuron=other.name, rule=index))
                if feature in rule.emit:
                    writers.append(dict(neuron=other.name, rule=index))
        packet["feature_consumers"][feature] = dict(readers=readers, writers=writers)
    packet["packet_sha256"] = fingerprint(packet)
    return packet


def proposal_template(packet):
    return dict(format=VERSION, base_model_sha256=packet["base_model_sha256"], address=deepcopy(packet["address"]),
                neuron=deepcopy(packet["neuron"]), feature_definitions={}, bindings=[],
                rationale="Explain the evidence and intended effect of this revision.")


def _validate_model(model, registry):
    def dynamic(value):
        if isinstance(value, (Ref, Lookup)):
            return True
        if isinstance(value, dict):
            return any(dynamic(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(dynamic(item) for item in value)
        return False

    def pattern(value):
        for path in value.tests:
            if path.split(".")[0] not in registry:
                raise ValueError(f"grammar reads an undeclared feature: {path}")
        for child in value.children:
            pattern(child)
    for neuron in neurons(model):
        for rule in neuron.rules:
            pattern(rule.pattern)
            for name, value in rule.emit.items():
                if name not in registry:
                    raise ValueError(f"grammar writes an undeclared feature: {name}")
                if not dynamic(value):
                    check_value(value, registry[name])
    for layer in model.layers:
        for head in layer.heads:
            if head:
                head.__post_init__()  # Recheck protected fields after a revision.


def stage(model, proposal, registry):
    required = {"format", "base_model_sha256", "address", "neuron", "feature_definitions", "bindings", "rationale"}
    if not isinstance(proposal, dict) or set(proposal) != required or proposal["format"] != VERSION:
        raise ValueError("proposal does not match the versioned revision contract")
    if proposal["base_model_sha256"] != model_fingerprint(model):
        raise ValueError("stale proposal: base model differs")
    if not isinstance(proposal["rationale"], str) or not proposal["rationale"].strip():
        raise ValueError("proposal requires an explanation")
    candidate, registry = deepcopy(model), deepcopy(registry)
    definitions = proposal["feature_definitions"]
    if not isinstance(definitions, dict) or len(definitions) > 64:
        raise ValueError("feature definitions must be a bounded object")
    for name, definition in definitions.items():
        if (not re.fullmatch(r"[a-z_][a-z0-9_]*", name) or not isinstance(definition, dict)
                or set(definition) != {"type", "description"} or definition["type"] not in TYPES
                or not isinstance(definition["description"], str) or not definition["description"].strip()):
            raise ValueError("feature requires a canonical name, type and definition")
        if name in registry:
            if registry[name]["type"] != definition["type"]:
                raise ValueError("cannot change an existing feature's type")
            if registry[name]["origin"] != "learned" and registry[name]["description"] != definition["description"]:
                raise ValueError("existing corpus/schema feature meanings are fixed")
        registry[name] = dict(**definition, origin=registry.get(name, {}).get("origin", "learned"))
    old = locate(candidate, proposal["address"])
    revised = parse_neuron(proposal["neuron"], context_size=model.context_size, max_states=old.max_states)
    tied = {index for index, rule in enumerate(old.rules) if sum(shared is rule for shared in old.rules) > 1 or
            any(other is not old and any(shared is rule for shared in other.rules) for other in neurons(candidate))}
    if tied and len(old.rules) != len(revised.rules):
        raise ValueError("cannot change the rule count while rules are tied across neurons")
    replacements = list(revised.rules)
    revised_ties = {}
    for index in tied:
        shared, replacement = old.rules[index], replacements[index]
        signature = canonical(dict(pattern=encode(replacement.pattern), emit=encode(replacement.emit), weight=replacement.weight))
        if id(shared) in revised_ties and revised_ties[id(shared)] != signature:
            raise ValueError("proposal assigns conflicting definitions to tied rules")
        revised_ties[id(shared)] = signature
        shared.pattern, shared.emit, shared.weight = replacement.pattern, replacement.emit, replacement.weight
        replacements[index] = shared
    revised.rules = tuple(replacements)
    old.name, old.rules, old.tables, old.max_states = revised.name, revised.rules, revised.tables, revised.max_states
    if not isinstance(proposal["bindings"], list) or len(proposal["bindings"]) > 64:
        raise ValueError("bindings must be a bounded list")
    sources = set()
    for binding in proposal["bindings"]:
        if not isinstance(binding, dict) or set(binding) != {"source", "target", "value"} or binding["source"] in sources:
            raise ValueError("binding requires a unique source, target and value")
        sources.add(binding["source"])
        rebind_feature(candidate, binding["source"], binding["target"], binding["value"], registry)
    _validate_model(candidate, registry)
    candidate.features = registry
    return candidate


def complexity(model):
    def nodes(pattern):
        return 1 + len(pattern.tests) + sum(nodes(child) for child in pattern.children)
    return sum(sum(nodes(rule.pattern) + len(rule.emit) + 1 for rule in neuron.rules)
               + sum(len(table) for table in neuron.tables.values()) for neuron in neurons(model))


def evaluate_proposal(model, proposal, training, validation, *, fit_epochs=0, learning_rate=.1):
    """Return a staged model/report; never mutate the supplied model or data."""
    training, validation = list(training), list(validation)
    report = dict(format=VERSION, accepted=False, base_model_sha256=model_fingerprint(model),
                  training_data_sha256=fingerprint(training), validation_data_sha256=fingerprint(validation))
    candidate = None
    try:
        if type(fit_epochs) is not int or fit_epochs < 0:
            raise ValueError("fit_epochs must be a nonnegative integer")
        registry = registry_for(model, training)
        candidate = stage(model, proposal, registry)
        report["revision_kind"] = ("revision" if proposal["bindings"] or proposal["feature_definitions"] or
                                   canonical(proposal["neuron"]) != canonical(neuron_spec(locate(model, proposal["address"])))
                                   else "unchanged")
        baseline = deepcopy(model)
        unchanged = metrics(model, validation, registry) if fit_epochs else None
        if fit_epochs:
            # Give both models the same weight-fitting opportunity.
            baseline.fit(training, epochs=fit_epochs, learning_rate=learning_rate)
            candidate.fit(training, epochs=fit_epochs, learning_rate=learning_rate)
        before = metrics(baseline, validation, registry)
        after = metrics(candidate, validation, candidate.features)
        report.update(before=before, after=after, complexity_before=complexity(baseline),
                      complexity_after=complexity(candidate), fit_epochs=fit_epochs,
                      candidate_model_sha256=model_fingerprint(candidate))
        report["unchanged"] = unchanged or before
        old_loss, new_loss = before["joint_nll"], after["joint_nll"]
        improved = new_loss is not None and (old_loss is None or new_loss < old_loss - 1e-9)
        equal_and_compact = (new_loss is not None and old_loss is not None and abs(new_loss - old_loss) <= 1e-9
                             and report["complexity_after"] <= report["complexity_before"])
        anchor = report["unchanged"]
        preserves_anchor = (new_loss is not None and
                            (anchor["joint_nll"] is None or new_loss <= anchor["joint_nll"] + 1e-9) and
                            after["coverage"] >= anchor["coverage"] and
                            after["observed_attribute_conflicts"] <= anchor["observed_attribute_conflicts"])
        report["accepted"] = ((improved or equal_and_compact) and preserves_anchor and
                              after["observed_attribute_conflicts"] <= before["observed_attribute_conflicts"])
        report["reason"] = ("Improves validation likelihood or preserves it without extra grammar complexity."
                            if report["accepted"] else "Validation likelihood, coverage, complexity or observed-attribute consistency regressed against the fitted control or unchanged model.")
        if report["accepted"] and report["revision_kind"] == "unchanged":
            report["reason"] = "No revision proposed; predictions preserved."
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, MatchBudgetExceeded) as error:
        report["reason"] = f"{type(error).__name__}: {error}"
    return candidate, report
