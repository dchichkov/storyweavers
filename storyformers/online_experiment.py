"""Run an online Luna grammar-learning pilot without modifying prior experiments."""

import argparse
import asyncio
from copy import deepcopy
from dataclasses import replace
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from time import perf_counter

from .grammar import Gap, GrammarNeuron, Rule, canonical
from .neuron_review import model_fingerprint
from .online import backward, choose, empty_patch, observe, packet, score
from .online_teacher import Teacher, TeacherResponseError, atomic_json
from .presentation import framing_checks, render
from .refine import load_documents
from .transformer import Storyformer


ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / "runs/learning_emulation_20261109/replay/final_model.json"
DATA = ROOT / "runs/presentation_20261110"


def bootstrap(checkpoint, vocabulary, context_size=32):
    """Known lexical inventory, uniform tiny mass for new words; no new counts."""
    model = Storyformer.load(checkpoint)
    previous_size = model.context_size
    def widen(pattern):
        children = tuple(widen(child) for child in pattern.children)
        maximum = pattern.maximum
        if (pattern.kind == "repeat" and maximum == previous_size and len(children) == 1
                and children[0].kind == "token" and not children[0].tests):
            maximum = context_size
        return replace(pattern, children=children, maximum=maximum)
    for neuron in [*(head.neuron for layer in model.layers for head in layer.heads if head),
                   *model.projection.neurons.values()]:
        for rule in neuron.rules:
            rule.pattern = widen(rule.pattern)
    model.context_size = context_size
    for row in vocabulary:
        root = model.projection.neurons.setdefault(row["token"], GrammarNeuron(row["token"]))
        if not any(rule.emit.get("pos") == row["pos"] for rule in root.rules):
            root.rules = (*root.rules, Rule(Gap(context_size), {"pos": row["pos"]}, .01))
    return model


def cases(documents, context_size=32):
    return [(deepcopy(doc[max(0, index - context_size):index]), deepcopy(target))
            for doc in documents for index, target in enumerate(doc)]


def curriculum_cases(path, documents, context_size=32):
    """An explicit observation schedule, verified against source causal prefixes."""
    plan = json.loads(Path(path).read_text())
    result = []
    for row in plan["observations"]:
        doc, index = row["document"], row["position"]
        if (type(doc) is not int or not 0 <= doc < len(documents) or type(index) is not int
                or not 0 <= index < len(documents[doc])):
            raise ValueError("invalid curriculum source position")
        expected = (documents[doc][max(0, index - context_size):index], documents[doc][index])
        if canonical([row["context"], row["target"]]) != canonical(expected):
            raise ValueError("curriculum does not match its causal source prefix/target")
        result.append(deepcopy(expected))
    if not result:
        raise ValueError("empty curriculum")
    return result


async def train(out, model, stream, anchors, teacher, *, steps, replay_size=16):
    initial = deepcopy(model)
    control, decisions, prequential, previous = deepcopy(model), [], [], None
    for index, pair in enumerate(stream[:steps]):
        directory = out / f"step_{index:03d}"
        directory.mkdir(exist_ok=True)
        replay = anchors + stream[max(0, index - replay_size):index]
        if (directory / "decision.json").exists():
            saved = json.loads((directory / "decision.json").read_text())
            if saved["before_model_sha256"] != model_fingerprint(model) or canonical(saved["example"]) != canonical(pair):
                raise ValueError("resume checkpoint/example mismatch")
            model, control = Storyformer.load(directory / "model.json"), Storyformer.load(directory / "control.json")
            if model_fingerprint(model) != saved["selected_model_sha256"]:
                raise ValueError("resume checkpoint fingerprint mismatch")
            prequential.append(saved["prediction_before_update"])
            decisions.append(saved)
            previous = dict(adopted=saved["adopted"], error=saved["error"])
            continue
        before_hash = model_fingerprint(model)
        before = observe(model, pair)
        weighted, gradient = backward(model, pair)
        evidence = packet(weighted, pair, before, gradient, replay, previous)
        atomic_json(directory / "evidence.json", evidence)
        print(f"Step {index + 1}/{steps}: target={pair[1]['token']!r}, p_before={before['probability']:.5f}; asking teacher...", flush=True)
        error = None
        try:
            revision = await teacher(evidence, directory)
        except TeacherResponseError as exc:
            # Completed malformed/truncated output is a failed hypothesis, never
            # a reason to inject a hand-written replacement or retry invisibly.
            error = str(exc)
            revision = empty_patch(weighted)
        selected, decision = choose(model, weighted, revision, pair, replay)
        if error:
            decision["teacher_error"] = error
        # Independent continual weight-only control, same observed examples and gate.
        control_weighted, _ = backward(control, pair)
        control, control_decision = choose(control, control_weighted, empty_patch(control_weighted), pair, replay)
        decision.update(before_model_sha256=before_hash, example=pair, prediction_before_update=before,
                        backward=gradient, weight_control=control_decision["adopted"])
        model = selected
        model.save(directory / "model.json")
        control.save(directory / "control.json")
        atomic_json(directory / "decision.json", decision)  # Commit marker, written last.
        decisions.append(decision)
        prequential.append(before)
        previous = dict(adopted=decision["adopted"], error=decision.get("teacher_error") or decision["error"])
        print(f"  adopted={decision['adopted']}, p_after={math.exp(-decision['scores'][decision['adopted']]['current']['joint_nll']):.5f}", flush=True)
    model.save(out / "final_model.json")
    control.save(out / "weights_only_model.json")
    return model, control, dict(observations=len(prequential),
        prequential_nll=sum(row["nll"] for row in prequential) / len(prequential),
        prequential_accuracy=sum(row["correct"] for row in prequential) / len(prequential),
        teacher_adoptions=sum(row["adopted"] == "teacher" for row in decisions),
        weight_adoptions=sum(row["adopted"] == "weights_only" for row in decisions),
        initial_model_sha256=model_fingerprint(initial), final_model_sha256=model_fingerprint(model))


async def run(args):
    args.out.mkdir(parents=True, exist_ok=True)
    # Protect the journal and budget from multiple processes. Async teacher
    # requests can share a process; model commits remain serial and versioned.
    with (args.out / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not (args.out / "manifest.json").exists() and any(path.name != ".lock" for path in args.out.iterdir()):
            raise ValueError("new experiments require an empty directory")
        if any(int(path.parent.name.removeprefix("step_")) >= args.steps for path in args.out.glob("step_*/decision.json")):
            raise ValueError("cannot resume with fewer steps than already committed")
        paths = [CHECKPOINT, DATA / "train.jsonl", ROOT / "runs/induction_baseline/train.jsonl"]
        if args.curriculum:
            paths.append(args.curriculum.resolve())
        hashes = {str(path): sha256(path.read_bytes()).hexdigest() for path in paths}
        training = load_documents(DATA / "train.jsonl")
        vocabulary = sorted({(row["token"], row["pos"]) for doc in training for row in doc})
        vocabulary = [dict(token=word, pos=pos) for word, pos in vocabulary]
        initial = bootstrap(CHECKPOINT, vocabulary)
        stream = curriculum_cases(args.curriculum, training) if args.curriculum else cases(training)
        anchors = cases(load_documents(ROOT / "runs/induction_baseline/train.jsonl")[:2])
        if not 1 <= args.steps <= len(stream):
            raise ValueError("steps must select at least one available observation")
        manifest = dict(model=args.model, budget_usd=args.budget, source_sha256=hashes,
                        initial_model_sha256=model_fingerprint(initial), vocabulary=vocabulary,
                        replay_anchor_count=len(anchors), replay_recent_count=16,
                        max_output_tokens=args.max_output_tokens,
                        curriculum=str(args.curriculum.resolve()) if args.curriculum else None,
                        policy="One prefix/target at a time, one gradient step, one teacher call, then replay gate. "
                               "Prior sentence model is warm-started; new token/POS inventory has uniform .01 mass. "
                               "No presentation outcome counts, future targets, validation or test examples enter learning.")
        manifest_path = args.out / "manifest.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
            raise ValueError("run settings changed; use a separate directory")
        atomic_json(manifest_path, manifest)
        initial.save(args.out / "initial_model.json")
        atomic_json(args.out / "replay_anchors.json", anchors)
        if args.prepare_only:
            teacher = Teacher(None, args.out, args.model, vocabulary, budget=args.budget,
                              max_output_tokens=args.max_output_tokens)
            weighted, gradient = backward(initial, stream[0])
            body = teacher.request(packet(weighted, stream[0], observe(initial, stream[0]), gradient, anchors))
            atomic_json(args.out / "prepared_request.json", body)
            print("Prepared first causal request; no API calls or budget reservations.")
            return
        if args.model != "gpt-6-luna":
            raise ValueError("live cost profile is verified only for gpt-6-luna; no automatic model substitution")
        from openai import AsyncOpenAI
        key = os.environ.get("OPENAI_API_KEY") or (ROOT.parent / ".API_KEY").read_text().strip()
        started = perf_counter()
        async with AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1", timeout=300, max_retries=0) as client:
            teacher = Teacher(client, args.out, args.model, vocabulary, budget=args.budget,
                              max_output_tokens=args.max_output_tokens)
            model, control, report = await train(args.out, initial, stream, anchors, teacher, steps=args.steps)
        report.update(training_seconds=perf_counter() - started, budget=teacher.budget.data)
        atomic_json(args.out / "training_report.json", report)
        # Frozen before any held-out evaluation. No suffix caching: teacher
        # grammars can now inspect the entire available context.
        frozen = model_fingerprint(model)
        evaluation = {}
        for split in ("validation", "test"):
            documents = load_documents(DATA / f"{split}.jsonl")[:args.eval_stories]
            pairs = cases(documents)
            evaluation[split] = {}
            for name, candidate in (("initial", initial), ("weights_only", control), ("teacher", model)):
                print(f"Evaluating frozen {name} on {split}: {len(pairs)} targets...", flush=True)
                evaluation[split][name] = score(candidate, pairs)
            atomic_json(args.out / "evaluation.json", evaluation)
        samples = []
        for name, candidate in (("initial", initial), ("weights_only", control), ("teacher", model)):
            for seed in range(3):
                rows = candidate.generate([], 40, seed=seed)
                samples.append(dict(model=name, seed=seed, records=rows, text=render(rows), **framing_checks(rows)))
        atomic_json(args.out / "samples.json", samples)
        assert model_fingerprint(model) == frozen
        assert all(sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in hashes.items())
        print(json.dumps({key: report[key] for key in ("observations", "prequential_nll", "teacher_adoptions",
                                                     "weight_adoptions", "training_seconds")}, indent=2))
        print(f"API cost estimate including unsettled reservations: ${sum(row['accounted_usd'] for row in teacher.budget.data['calls'].values()):.6f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--budget", type=float, default=10.)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--eval-stories", type=int, default=8)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--curriculum", type=Path, help="explicit causal observation schedule from training data")
    args = parser.parse_args()
    if args.eval_stories < 1:
        parser.error("eval-stories must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
