"""Replay an agent-guided learning experiment on the saved token/POS baseline.

The structural proposals here were written after inspecting training evidence.
This deliberately emulates the outer LLM loop; it is not an autonomous LLM or
new induction algorithm. Output values/counts and weights come from training.
"""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from time import perf_counter
import json
import math

from .grammar import Alt, Gap, GrammarNeuron, Lookup, OneOf, Ref, Repeat, Rule, Seq, Token, canonical
from .learning import LearningBatch
from .neuron_review import VERSION, complexity, model_fingerprint, stage
from .neuron_spec import encode, neuron_spec, registry_for
from .refine import load_documents
from .synthetic import evaluate
from .transformer import GrammarHead, Storyformer, semantic


SOURCE = Path(__file__).resolve().parent / "runs/induction_baseline"
FEATURE = "preceding_verb_surface"


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def compact_pos_copies(model):
    """Agent hypothesis: these exact private detectors duplicate observed POS."""
    candidate, proposals = deepcopy(model), []
    for layer, block in enumerate(candidate.layers):
        for slot, head in enumerate(block.heads):
            if head is None or len(head.neuron.rules) != 1:
                continue
            rule = head.neuron.rules[0]
            pattern = rule.pattern
            if (pattern.kind != "seq" or len(pattern.children) != 2
                    or canonical(encode(pattern.children[0])) != canonical(encode(Gap(maximum=candidate.context_size)))
                    or pattern.children[1].kind != "token" or pattern.children[1].bind
                    or set(pattern.children[1].tests) != {"pos"}
                    or len(rule.emit) != 1 or next(iter(rule.emit.values())) is not True
                    or head.operation != "add" or head.strength <= 0):
                continue
            feature = next(iter(rule.emit))
            spec = neuron_spec(head.neuron)
            spec.update(name=f"retired_pos_{pattern.children[1].tests['pos']}", rules=[])
            proposal = dict(format=VERSION, base_model_sha256=model_fingerprint(candidate),
                            address=dict(kind="head", layer=layer, head=slot), neuron=spec,
                            feature_definitions={}, bindings=[dict(source=feature, target="pos",
                                                                  value=pattern.children[1].tests["pos"])],
                            rationale="Training traces show an exact copy of observed POS; rewire all consumers.")
            candidate = stage(candidate, proposal, registry_for(candidate))
            proposals.append(proposal)
    for block in candidate.layers:
        block.heads = tuple(head if head and head.neuron.rules else None for head in block.heads)
    return candidate, proposals


def propose_carrier(model, training, *, compact_emit=False):
    """Agent proposes a capture; the observed continuation tables fit its consumers.

    Pattern/feature naming is an agent-authored revision, not claimed to have
    been automatically discovered by the counting code below.
    """
    candidate = deepcopy(model)
    head = GrammarNeuron("carry_preceding_verb", (Rule(
        Seq(Gap(maximum=model.context_size), Token(bind="verb", pos="v"),
            Repeat(Token(pos=OneOf(("det", "adj"))), maximum=model.context_size)),
        {FEATURE: Ref("verb.token")}),))
    slot = next((i for i, existing in enumerate(candidate.layers[0].heads)
                 if existing and existing.neuron.name == head.name), None)
    if slot is None:
        slot = next(i for i, existing in enumerate(candidate.layers[0].heads) if existing is None)
    heads = list(candidate.layers[0].heads)
    heads[slot] = GrammarHead(head)
    candidate.layers[0].heads = tuple(heads)
    candidate.features[FEATURE] = dict(type="string", origin="learned", description=
        "Surface token of the preceding verb when only determiners/adjectives follow it within this prefix; otherwise absent.")
    def consumes(pattern):
        return FEATURE in pattern.tests or any(consumes(child) for child in pattern.children)
    for root in candidate.projection.neurons.values():
        root.rules = tuple(rule for rule in root.rules if not consumes(rule.pattern))
    outcomes = defaultdict(Counter)
    for context, target in candidate.examples(training):
        matches = head.activate(context)
        if matches:
            key = matches[0].value[FEATURE], context[-1]["pos"]
            outcomes[key][canonical(semantic(target))] += 1
    additions = []
    for (verb, pos), counts in sorted(outcomes.items()):
        support = sum(counts.values())
        if support < 3:
            continue
        pattern = Seq(Gap(maximum=model.context_size), Token(**{FEATURE: verb, "pos": pos}))
        for encoded, count in sorted(counts.items()):
            target = json.loads(encoded)
            word = target.pop("token")
            if compact_emit:
                target = {key: value for key, value in target.items() if value is not None}
            rule = Rule(pattern, target, 8. * count / support)
            root = candidate.projection.neurons[word]
            root.rules = (*root.rules, rule)
            additions.append(dict(word=word, verb=verb, current_pos=pos, count=count,
                                  support=support, rule=len(root.rules) - 1))
    return candidate, dict(source="agent revision after initial_diagnostics.json", head=neuron_spec(head),
                           feature={FEATURE: candidate.features[FEATURE]}, consumer_counts=additions,
                           rationale="Carry lexical verb identity through modifiers; learn probabilistic continuations from data.")


def second_round(model, training, validation, out, *, steps=80):
    candidate, proposal = propose_carrier(model, training[:128], compact_emit=True)
    proposal["source"] = "Agent revision after round_01 and batch_02 evidence: pool two batches; omit redundant default nulls."
    save(out / "carrier_revision_02.json", proposal)
    model, report = compare(candidate, deepcopy(model), training, validation, out / "round_02_revised_carrier", steps=steps)
    model.save(out / "current_model.json")
    save(out / "batch_03_before.json", LearningBatch(model, training[128:192]).report())
    return model, report


def propose_factored_carrier(model, training):
    """Agent revision: pool noun identity across modifier positions.

    Keep the old total noun mass at each POS condition. Redistribute that mass
    using smoothed P(noun | preceding verb), estimated only from training.
    All vocabulary values and lexical preferences come from observed counts.
    """
    candidate, proposal = propose_carrier(model, [], compact_emit=True)
    head = next(h.neuron for h in candidate.layers[0].heads if h and h.neuron.name == "carry_preceding_verb")
    counts, prior, positions = defaultdict(Counter), Counter(), set()
    for context, target in candidate.examples(training):
        matches = head.activate(context)
        if matches and target["pos"] == "n":
            counts[matches[0].value[FEATURE]][target["token"]] += 1
            prior[target["token"]] += 1
            positions.add(context[-1]["pos"])
    if not prior:
        raise ValueError("no noun continuations observed")

    def suffix_pos(rule):
        p = rule.pattern
        if (p.kind == "seq" and len(p.children) == 2
                and canonical(encode(p.children[0])) == canonical(encode(Gap(model.context_size)))
                and p.children[1].kind == "token" and set(p.children[1].tests) == {"pos"}):
            return p.children[1].tests["pos"]
        return None

    total_mass = Counter()
    for word in prior:
        for rule in model.projection.neurons[word].rules:
            pos = suffix_pos(rule)
            if pos in positions and rule.emit.get("pos") == "n":
                total_mass[pos] += rule.weight
    probabilities = {verb: {word: (observed[word] + prior[word] / sum(prior.values()))
                                     / (sum(observed.values()) + 1.) for word in prior}
                     for verb, observed in sorted(counts.items())}
    replacements = []
    for word in prior:
        root = candidate.projection.neurons[word]
        rules = []
        for index, rule in enumerate(root.rules):
            pos = suffix_pos(rule)
            if pos in total_mass and rule.emit.get("pos") == "n":
                masses = [total_mass[pos] * probabilities[verb][word] for verb in probabilities]
                pattern = Seq(Gap(model.context_size), Alt(
                    *(Token(**{FEATURE: verb, "pos": pos}) for verb in probabilities), weights=masses))
                rule = Rule(pattern, deepcopy(rule.emit), sum(masses))
                replacements.append(dict(word=word, rule=index, current_pos=pos))
            rules.append(rule)
        root.rules = tuple(rules)
    proposal.update(source="Agent revision after two pooled-continuation trials and third-batch evidence.",
                    rationale="Separate noun occurrence from noun identity; pool lexical evidence across modifiers.",
                    counts={verb: dict(row) for verb, row in counts.items()}, probabilities=probabilities,
                    preserved_noun_mass=dict(total_mass), replaced_rules=replacements,
                    support_documents=len(training))
    return candidate, proposal


def third_round(model, training, validation, out, *, steps=80):
    candidate, proposal = propose_factored_carrier(model, training)
    save(out / "carrier_revision_03.json", proposal)
    model, report = compare(candidate, deepcopy(model), training, validation, out / "round_03_factored_carrier", steps=steps)
    model.save(out / "current_model.json")
    return model, report


def finalize(model, training, source, out):
    """Freeze first; test data is read here, after all adoption decisions."""
    model.save(out / "final_model.json")
    frozen = model_fingerprint(model)
    test = load_documents(source / "test.jsonl")
    initial = Storyformer.load(out / "initial_model.json")
    control = Storyformer.load(out / "round_03_factored_carrier/weights_only_model.json")
    ablated = deepcopy(model)
    for block in ablated.layers:
        block.heads = tuple(None if head and head.neuron.name == "carry_preceding_verb" else head
                            for head in block.heads)
    observed = defaultdict(set)
    for context, target in model.examples(training):
        if target["pos"] == "n":
            verbs = [row["token"] for row in context if row["pos"] == "v"]
            if verbs:
                observed[verbs[-1]].add(target["token"])
    # Preserve the head's firing/gating, but feed the readout incorrect verb
    # values. This separates use of the information from mere head presence.
    shuffled = deepcopy(model)
    verbs = sorted(observed)
    permutation = dict(zip(verbs, reversed(verbs)))
    for block in shuffled.layers:
        for head in block.heads:
            if head and head.neuron.name == "carry_preceding_verb":
                head.neuron.tables["diagnostic_permutation"] = permutation
                for rule in head.neuron.rules:
                    rule.emit[FEATURE] = Lookup("diagnostic_permutation", Ref("verb.token"))

    def nouns(candidate):
        buckets = defaultdict(lambda: [0, 0., 0., 0])
        for context, target in candidate.examples(test):
            if target["pos"] != "n":
                continue
            verb = next(row["token"] for row in reversed(context) if row["pos"] == "v")
            rows = [row for row in candidate.predict(context).joint if row["latent"]["pos"] == "n"]
            total = math.fsum(row["probability"] for row in rows)
            correct = math.fsum(row["probability"] for row in rows if row["latent"]["token"] == target["token"])
            unknown = math.fsum(row["probability"] for row in rows if row["latent"]["token"] not in observed[verb])
            best = max(rows, key=lambda row: row["probability"])["latent"]["token"]
            bucket = buckets[verb]
            bucket[0] += 1
            bucket[1] -= math.log(correct / total)
            bucket[2] += unknown / total
            bucket[3] += best == target["token"]
        return {verb: dict(targets=n, conditional_nll=loss / n,
                           noun_mass_on_pairs_absent_from_training=absent / n, noun_accuracy=right / n)
                for verb, (n, loss, absent, right) in buckets.items()}

    models = {"initial": initial, "weights_only": control, "revised": model,
              "carrier_ablated": ablated, "carrier_values_permuted": shuffled}
    report = dict(final_model_sha256=frozen, test_policy="Read once revisions were frozen; no test-based updates.",
                  test_documents=len(test), metrics={name: evaluate(candidate, test) for name, candidate in models.items()},
                  noun_diagnostics={name: nouns(candidate) for name, candidate in models.items()},
                  active_heads=sum(head is not None for layer in model.layers for head in layer.heads),
                  output_neurons=len(model.projection.neurons),
                  output_rules=sum(len(neuron.rules) for neuron in model.projection.neurons.values()),
                  final_complexity=complexity(model), diagnostic_permutation=permutation, test_samples=[])
    # Fixed selection, all retained rather than choosing attractive completions.
    for document in test[:6]:
        stop = next(i for i, row in enumerate(document) if row["pos"] == "n")
        context = document[:stop]
        report["test_samples"].append(dict(context=context, target=document[stop],
            initial=initial.predict(context).to_dict(), revised=model.predict(context).to_dict()))
    report["generated"] = [model.generate([], 12, seed=seed) for seed in range(8)]
    if model_fingerprint(model) != frozen:
        raise ValueError("evaluation modified the frozen model")
    save(out / "final_evaluation.json", report)
    print(json.dumps({key: report[key] for key in ("metrics", "active_heads", "output_neurons", "output_rules")}), flush=True)
    return report


def compare(candidate, control, training, validation, folder, *, steps=80):
    folder.mkdir()
    candidate.save(folder / "proposal_model.json")
    started = perf_counter()
    anchor = deepcopy(control)
    anchor_report = LearningBatch(anchor, validation).report()
    save(folder / "unchanged_validation.json", anchor_report)
    reports = {}
    for label, model in (("candidate", candidate), ("weights_only", control)):
        batch = LearningBatch(model, training)
        save(folder / f"{label}_before.json", batch.report())
        fit = batch.fit(steps=steps)
        save(folder / f"{label}_fit.json", fit)
        train_report = batch.report()
        validation_report = LearningBatch(model, validation).report()
        save(folder / f"{label}_train.json", train_report)
        save(folder / f"{label}_validation.json", validation_report)
        model.save(folder / f"{label}_model.json")
        reports[label] = dict(train_nll=train_report["joint_nll"], validation_nll=validation_report["joint_nll"],
                              validation_coverage=validation_report["coverage"], complexity=complexity(model))
    old, new = reports["weights_only"], reports["candidate"]
    # The small structural cost is fixed before inspecting this round's validation.
    penalty = .00001 * max(0, new["complexity"] - old["complexity"])
    anchor_loss = anchor_report["joint_nll"]
    accepted = (new["validation_nll"] is not None and new["validation_coverage"] >= old["validation_coverage"]
                and new["validation_nll"] + penalty <= min(old["validation_nll"], anchor_loss) + 1e-10)
    weights_improved = old["validation_nll"] <= anchor_loss
    adopted = "candidate" if accepted else "weights_only" if weights_improved else "unchanged"
    report = dict(accepted=accepted, models=reports, complexity_penalty_nats=penalty,
                  seconds=perf_counter() - started,
                  training_documents=len(training), validation_documents=len(validation),
                  unchanged_validation_nll=anchor_loss, adopted=adopted)
    save(folder / "decision.json", report)
    print(json.dumps({"round": folder.name, **report}), flush=True)
    selected = candidate if accepted else control if weights_improved else anchor
    selected.save(folder / "adopted_model.json")
    return selected, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    # Refuse to overwrite any experiment result; source checkpoints are read-only.
    if (args.out / "manifest.json").exists():
        raise ValueError("use a fresh output directory")
    model = Storyformer.load(args.source / "model.json")
    training = load_documents(args.source / "train.jsonl")
    validation = load_documents(args.source / "validation.jsonl")
    save(args.out / "manifest.json", dict(source=str(args.source), base_model_sha256=model_fingerprint(model),
        training_kind="Continuation of a previously induced model; it has already seen these training documents.",
        proposal_kind="Agent-guided emulation; no live Luna calls. Grammar programs are explicit, data-derived counts fit their consumers.",
        validation_policy="Validation selects revisions; examples are excluded from proposal evidence. Test read only after revisions are frozen.",
        training_documents=len(training), batches=3, batch_size=64, steps=args.steps,
        replay_policy="Fit on all previously seen training stories; candidate counts/examples initially use the current 64-story batch."))
    model.save(args.out / "initial_model.json")
    save(args.out / "batch_01_before.json", LearningBatch(model, training[:64]).report())
    compact, proposals = compact_pos_copies(model)
    save(args.out / "compact_proposals.json", proposals)
    # A semantic-equivalence check on every training and validation prefix.
    max_difference = 0.
    for document in training + validation:
        for context, target in model.examples([document]):
            before, after = model.predict(context), compact.predict(context)
            masses = {canonical(semantic(row["latent"])): row["probability"] for row in before.joint}
            others = {canonical(semantic(row["latent"])): row["probability"] for row in after.joint}
            max_difference = max(max_difference, *(abs(masses.get(key, 0.) - others.get(key, 0.))
                                                    for key in masses.keys() | others.keys()))
    if max_difference > 1e-12:
        raise ValueError("POS rewrite changed predictions")
    compact.save(args.out / "compact_model.json")
    save(args.out / "compact_evaluation.json", dict(max_probability_difference=max_difference,
        complexity_before=complexity(model), complexity_after=complexity(compact), removed_heads=len(proposals)))
    candidate, proposal = propose_carrier(compact, training[:64])
    save(args.out / "carrier_proposal.json", proposal)
    model, _ = compare(candidate, compact, training, validation, args.out / "round_01_carrier", steps=args.steps)
    model.save(args.out / "current_model.json")
    # Stop at an evidence checkpoint so the next revision follows inspection.
    save(args.out / "batch_02_before.json", LearningBatch(model, training[64:128]).report())
    model, _ = second_round(model, training, validation, args.out, steps=args.steps)
    model, _ = third_round(model, training, validation, args.out, steps=args.steps)
    finalize(model, training, args.source, args.out)
    print("Saved three reviewed revision rounds and frozen test evaluation.", flush=True)


if __name__ == "__main__":
    main()
