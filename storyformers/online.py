"""One causal observation -> weight backward pass -> teacher patch -> replay gate.

The teacher is an injected async function. This module never calls an API and
never feeds a target into its own context. Multi-neuron revisions commit atomically.
"""

from copy import deepcopy
import math
import re

from .grammar import GrammarNeuron, MatchBudgetExceeded, canonical, positive
from .learning import LearningBatch
from .neuron_review import _validate_model, complexity, model_fingerprint
from .neuron_spec import TYPES, check_value, encode, neuron_spec, parse_neuron, registry_for
from .transformer import GrammarHead, semantic


VERSION = "storyformers-online-v1"


def empty_patch(model):
    return dict(format=VERSION, base_model_sha256=model_fingerprint(model),
                feature_definitions={}, heads=[], outputs=[], rationale="No structural revision needed.")


def stage_patch(model, patch):
    """Decode bounded data-only edits against one immutable model revision."""
    if not isinstance(patch, dict) or set(patch) != set(empty_patch(model)) or patch["format"] != VERSION:
        raise ValueError("invalid online patch contract")
    if patch["base_model_sha256"] != model_fingerprint(model):
        raise ValueError("stale patch: obtain evidence from the current model")
    if not isinstance(patch["rationale"], str) or not patch["rationale"].strip():
        raise ValueError("a patch needs a rationale")
    candidate = deepcopy(model)
    registry = registry_for(candidate)
    definitions = patch["feature_definitions"]
    if not isinstance(definitions, dict) or len(definitions) > 4:
        raise ValueError("at most four typed feature definitions per observation")
    for name, definition in definitions.items():
        if (not re.fullmatch(r"[a-z_][a-z0-9_]*", name) or not isinstance(definition, dict)
                or set(definition) != {"type", "description"} or definition["type"] not in TYPES
                or not isinstance(definition["description"], str) or not definition["description"].strip()):
            raise ValueError("invalid typed feature definition")
        if name in registry and any(registry[name][key] != definition[key] for key in definition):
            raise ValueError("reuse existing feature meanings and types; do not redefine them")
        registry.setdefault(name, dict(**definition, origin="learned"))
    if not isinstance(patch["heads"], list) or len(patch["heads"]) > 2:
        raise ValueError("at most two head edits")
    touched = set()
    for edit in patch["heads"]:
        if set(edit) != {"layer", "slot", "operation", "neuron"}:
            raise ValueError("head edit needs layer, slot, operation, neuron")
        layer, slot = edit["layer"], edit["slot"]
        if (type(layer) is not int or type(slot) is not int or not 0 <= layer < len(candidate.layers)
                or not 0 <= slot < candidate.layers[layer].num_heads or (layer, slot) in touched):
            raise ValueError("invalid or duplicated head address")
        touched.add((layer, slot))
        heads = list(candidate.layers[layer].heads)
        bound = heads[slot].neuron.max_states if heads[slot] else 20000
        neuron = parse_neuron(edit["neuron"], context_size=model.context_size, max_states=bound)
        heads[slot] = GrammarHead(neuron, operation=edit["operation"])
        candidate.layers[layer].heads = tuple(heads)
    if not isinstance(patch["outputs"], list) or len(patch["outputs"]) > 8:
        raise ValueError("at most eight output-root edits")
    touched = set()
    for edit in patch["outputs"]:
        if set(edit) != {"token", "append", "scale"}:
            raise ValueError("output edit needs token, append, scale")
        word = edit["token"]
        if word not in candidate.projection.neurons or word in touched:
            raise ValueError("unknown or duplicated vocabulary root")
        touched.add(word)
        root = candidate.projection.neurons[word]
        if not isinstance(edit["append"], list) or len(edit["append"]) > 4:
            raise ValueError("at most four new rules per root")
        # Vocabulary roots may be literal whitespace (e.g. "\n\n"). The
        # temporary parsed fragment needs a descriptive nonblank neuron name;
        # its name is not installed or used as the vocabulary token.
        additions = parse_neuron(dict(name="output_rule_fragment", rules=edit["append"], tables=root.tables,
                                      max_states=root.max_states), context_size=model.context_size,
                                 max_states=root.max_states)
        if len(root.rules) + len(additions.rules) > 128:
            raise ValueError("output root rule budget exceeded")
        scaled = set()
        if not isinstance(edit["scale"], list) or len(edit["scale"]) > 8:
            raise ValueError("at most eight weight changes per root")
        for change in edit["scale"]:
            if set(change) != {"rule", "factor"}:
                raise ValueError("weight change needs rule and factor")
            index, factor = change["rule"], change["factor"]
            positive(factor, "scale factor")
            if type(index) is not int or not 0 <= index < len(root.rules) or index in scaled or not .05 <= factor <= 20:
                raise ValueError("invalid weight change")
            scaled.add(index)
            root.rules[index].weight *= factor
            positive(root.rules[index].weight, "scaled rule weight")
        root.rules = (*root.rules, *additions.rules)
        for rule in root.rules:
            if "token" in rule.emit and rule.emit["token"] != word:
                raise ValueError("an output root cannot change its token")
    candidate.features = registry
    _validate_model(candidate, registry)
    if complexity(candidate) - complexity(model) > 400:
        raise ValueError("one observation cannot add more than 400 grammar nodes")
    return candidate


def observe(model, pair):
    context, target = pair
    history, stream, trace = model._run(context)
    views = [row.view() for row in stream]
    prediction = model.projection.read(views, model.top_k, position_context=history)
    registry, conflicts = registry_for(model), 0
    for source, residual in zip(history[-model.context_size:], views):
        for key, value in semantic(source).items():
            if value is not None and canonical(residual.get(key)) != canonical(value):
                conflicts += 1
    for row in views + [item["latent"] for item in prediction.joint]:
        for key, value in row.items():
            if key not in registry:
                raise ValueError(f"undeclared runtime feature: {key}")
            check_value(value, registry[key])
    probability = prediction.probability(target)
    best = max(prediction.joint, key=lambda item: item["probability"], default=None)
    return dict(probability=probability, nll=-math.log(probability) if probability else None,
                correct=bool(best and LearningBatch.matches(best["latent"], semantic(target))),
                conflicts=conflicts,
                top_joint=sorted(prediction.joint, key=lambda item: -item["probability"])[:10],
                residual=views, last_head_trace=[item for item in trace if history and
                    item["query"] == history[-1]["position"]["token"]])


def score(model, pairs):
    rows = [observe(model, pair) for pair in pairs]
    count = len(rows)
    covered = sum(row["nll"] is not None for row in rows)
    return dict(targets=count, coverage=covered / count if count else 1.,
                joint_nll=sum(row["nll"] or 0. for row in rows) / count if count and covered == count else (0. if not count else None),
                accuracy=sum(row["correct"] for row in rows) / count if count else None,
                conflicts=sum(row["conflicts"] for row in rows))


def backward(model, pair, *, learning_rate=.2):
    return backward_batch(model, [pair], learning_rate=learning_rate)


def backward_batch(model, pairs, *, learning_rate=.2):
    """One averaged gradient over all revealed causal targets in a batch."""
    updated = deepcopy(model)
    batch = LearningBatch(updated, pairs=pairs)
    weights = [rule.weight for rule in batch.rules]
    fit = batch.fit(steps=1, learning_rate=learning_rate)
    changes = {id(rule): math.log(rule.weight / old) for rule, old in zip(batch.rules, weights)}
    deltas = [dict(token=word, rule=index, log_weight_delta=changes[id(rule)])
              for word, neuron in updated.projection.neurons.items() for index, rule in enumerate(neuron.rules)]
    return updated, dict(**fit, largest_weight_changes=sorted(deltas, key=lambda row: -abs(row["log_weight_delta"]))[:16])


def packet(model, pair, before, gradient, replay, previous=None):
    """Only the revealed target and previously observed replay enter teacher input."""
    after = observe(model, pair)
    words = {pair[1]["token"], *(item["latent"]["token"] for item in after["top_joint"][:3])}
    return dict(format=VERSION, base_model_sha256=model_fingerprint(model), context_size=model.context_size,
                context=pair[0], target=pair[1], prediction_before_update=before,
                prediction_after_gradient=after, backward=gradient, replay_examples=replay[-8:],
                previous_decision=previous, registry=registry_for(model),
                heads=[dict(layer=i, slot=j, operation=head.operation, neuron=neuron_spec(head.neuron))
                       for i, layer in enumerate(model.layers) for j, head in enumerate(layer.heads) if head],
                empty_head_slots=[dict(layer=i, slot=j) for i, layer in enumerate(model.layers)
                                  for j, head in enumerate(layer.heads) if head is None],
                output_roots={word: neuron_spec(model.projection.neurons[word]) for word in sorted(words)},
                output_weight_totals={word: sum(rule.weight for rule in root.rules)
                                      for word, root in model.projection.neurons.items()},
                patch_template=empty_patch(model))


def choose(original, weighted, patch, pair, replay, *, replay_tolerance=.02, current_pairs=None):
    """One-observation improvement is provisional; replay bounds forgetting.

    No validation/test examples are used here. Both fitted weights and teacher
    edits must preserve the pre-update anchor; rejected edits leave no mutation.
    """
    models = dict(unchanged=original, weights_only=weighted)
    reason = None
    try:
        models["teacher"] = stage_patch(weighted, patch)
    except (ValueError, KeyError, TypeError, IndexError, ArithmeticError) as error:
        reason = f"{type(error).__name__}: {error}"
    reports = {}
    for name, model in list(models.items()):
        try:
            reports[name] = dict(current=score(model, [pair] if current_pairs is None else current_pairs),
                                 replay=score(model, replay), complexity=complexity(model))
        except (ValueError, KeyError, TypeError, ArithmeticError, MatchBudgetExceeded) as error:
            if name == "unchanged":
                raise
            reason = f"{name}: {type(error).__name__}: {error}"
            del models[name]
    anchor = reports["unchanged"]
    eligible = ["unchanged"]
    for name, report in reports.items():
        if name == "unchanged":
            continue
        current, retained = report["current"], report["replay"]
        if (current["joint_nll"] is not None and retained["joint_nll"] is not None
                and current["joint_nll"] < (anchor["current"]["joint_nll"] if anchor["current"]["joint_nll"] is not None else math.inf) - 1e-9
                and retained["joint_nll"] <= (anchor["replay"]["joint_nll"] if anchor["replay"]["joint_nll"] is not None else math.inf) + replay_tolerance
                and retained["coverage"] >= anchor["replay"]["coverage"]
                and current["conflicts"] <= anchor["current"]["conflicts"]
                and retained["conflicts"] <= anchor["replay"]["conflicts"]):
            eligible.append(name)
    # Penalize extra syntax mildly, and preserve unchanged on ties.
    winner = min(eligible, key=lambda name: (reports[name]["current"]["joint_nll"]
                 if reports[name]["current"]["joint_nll"] is not None else math.inf) +
                 .001 * max(0, reports[name]["complexity"] - anchor["complexity"]))
    return models[winner], dict(adopted=winner, provisional=True, scores=reports, error=reason,
                                replay_tolerance=replay_tolerance,
                                selected_model_sha256=model_fingerprint(models[winner]))
