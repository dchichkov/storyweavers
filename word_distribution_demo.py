#!/usr/bin/env python3
"""Eight words, four explicit alternatives per word, no runtime LLM or packages.

    python word_distribution_demo.py --seed 7
    python word_distribution_demo.py --prefix 'Lily carried the' --weather mild
    python word_distribution_demo.py --attention off --samples 5
    python word_distribution_demo.py --json
    python word_distribution_demo.py --verify

This is an authored probabilistic grammar, not a trained language model. Every
slot has exactly four legal words (the complete support, not a top-four display).
Two tiny attention heads retrieve world facts and already emitted token memories.
Keys, queries, values, and lexical priors are hand-written. Weighted values add
to next-word logits; attention weights themselves are NOT word probabilities.
Only completed sentences commit events to the world. Punctuation and the fixed
eight-word stopping rule are deterministic, outside the word distribution.

North star: physical entities carry descriptive state and character magnitudes;
those magnitudes influence generation. This isolated experiment does not change
gen6/gen7. The fixed grammar and tiny ontology deliberately limit expressiveness.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass, field
import json
import math
import random


SLOTS = (
    ("actor", ("Lily", "Sam", "Nora", "Ben")),
    ("verb", ("carried", "guided", "led", "escorted")),
    ("determiner", ("the", "a", "this", "that")),
    ("description", ("frightened", "shivering", "muddy", "sleepy")),
    ("animal", ("kitten", "puppy", "duckling", "rabbit")),
    ("direction", ("into", "toward", "past", "around")),
    ("determiner", ("the", "a", "this", "that")),
    ("place", ("cottage", "cabin", "barn", "shed")),
)


@dataclass
class Entity:
    kind: str
    location: str
    traits: dict[str, float]


@dataclass
class World:
    weather: str
    entities: dict[str, Entity]
    history: list[dict] = field(default_factory=list)

    def commit(self, words: list[str]) -> dict:
        actor, verb, _, adjective, animal, direction, _, place = words
        assert self.entities[animal].traits[adjective] > 0
        before = {name: self.entities[name].location for name in (actor, animal)}
        relation = {"into": "inside", "toward": "approaching",
                    "past": "beyond", "around": "outside"}[direction]
        after = f"{relation} {place}"
        for name in (actor, animal):
            self.entities[name].location = after
        event = dict(actor=actor, action=verb, animal=animal, description=adjective,
                     direction=direction, place=place, before=before, after=after)
        self.history.append(event)
        return event


def make_world(weather: str = "cold") -> World:
    if weather not in ("cold", "mild"):
        raise ValueError("weather must be cold or mild")
    entities = {}
    # All four children can perform all four actions; these are preferences.
    for name, strength, patience in (
        ("Lily", 0.95, 0.25), ("Sam", 0.25, 0.95),
        ("Nora", 0.65, 0.75), ("Ben", 0.45, 0.55),
    ):
        entities[name] = Entity("actor", "meadow", {
            "Strength": strength, "Patience": patience, "Care": 0.8,
        })
    # All four descriptions are true of all animals, at different magnitudes.
    # That deliberately keeps all four noun choices grounded after any adjective.
    for name, fear, cold, mud, tired in (
        ("kitten", 0.95, 0.85, 0.25, 0.40),
        ("puppy", 0.25, 0.35, 0.95, 0.35),
        ("duckling", 0.55, 0.95, 0.40, 0.20),
        ("rabbit", 0.45, 0.30, 0.35, 0.95),
    ):
        entities[name] = Entity("animal", "meadow", {
            "frightened": fear, "shivering": cold, "muddy": mud, "sleepy": tired,
        })
    for name, warmth in (("cottage", 1.0), ("cabin", 0.8), ("barn", 0.5), ("shed", 0.2)):
        entities[name] = Entity("place", "meadow edge", {"Warmth": warmth})
    # Weather is grounded in the meadow; mild means now mild, not that recently
    # chilled animals have already stopped shivering.
    entities["meadow"] = Entity("weather", "outdoors", {
        "Cold": 1.0 if weather == "cold" else 0.0,
    })
    return World(weather, entities)


@dataclass
class Memory:
    label: str
    keys: dict[str, float]
    values: dict[str, float]


def world_memories(world: World) -> list[Memory]:
    memories = []
    for name, entity in world.entities.items():
        t = entity.traits
        if entity.kind == "actor":
            values = {name: t["Care"], "carried": 2 * t["Strength"],
                      "guided": 2 * t["Patience"], "led": t["Strength"],
                      "escorted": t["Care"] + t["Patience"]}
        elif entity.kind == "animal":
            values = {**t, name: max(t.values()), "into": t["shivering"],
                      "toward": t["frightened"], "past": 0.1, "around": 0.2}
        elif entity.kind == "place":
            values = {name: t["Warmth"], "into": t["Warmth"]}
        else:
            cold = t["Cold"]
            values = {"shivering": 2.5 * cold, "muddy": 0.3,
                      "into": 2.5 * cold, "around": 1.0 - cold}
        memories.append(Memory(name, {entity.kind: 1, name: 1}, values))
    return memories


def prefix_memories(world: World, prefix: list[str]) -> list[Memory]:
    by_name = {m.label: m for m in world_memories(world)}
    result = []
    for i, word in enumerate(prefix):
        role = SLOTS[i][0]
        if word in by_name:
            values = by_name[word].values
        elif role == "description":
            values = {name: 2 * e.traits[word] for name, e in world.entities.items()
                      if e.kind == "animal"}
        elif role == "verb":
            values = {"into": 1.2 if word == "carried" else 0.4,
                      "toward": 0.8, "around": 0.7 if word == "led" else 0.1}
        elif role == "direction":
            values = {name: e.traits["Warmth"] * (2 if word == "into" else 0.2)
                      for name, e in world.entities.items() if e.kind == "place"}
        else:
            values = {}
        result.append(Memory(f"{i + 1}:{word}", {role: 1}, values))
    return result


def softmax(scores: list[float], temperature: float = 1.0) -> list[float]:
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite and positive")
    maximum = max(scores)
    weights = [math.exp((score - maximum) / temperature) for score in scores]
    total = sum(weights)
    return [weight / total for weight in weights]


def attend(query: dict[str, float], memories: list[Memory]) -> tuple[dict, list]:
    """Sparse symbolic Q·K, softmax over matching memories, weighted sum of V.

    A zero-overlap mask avoids unrelated facts diluting the context. No sampling
    happens here. Prefix memories only contain words already emitted.
    """
    matches = [(m, sum(value * m.keys.get(key, 0) for key, value in query.items()))
               for m in memories]
    matches = [(m, score) for m, score in matches if score > 0]
    if not matches:
        return {}, []
    weights = softmax([score for _, score in matches])
    context, trace = {}, []
    for (memory, score), weight in zip(matches, weights):
        trace.append(dict(memory=memory.label, score=score, weight=weight))
        for word, value in memory.values.items():
            context[word] = context.get(word, 0) + weight * value
    return context, trace


def queries(prefix: list[str]) -> tuple[dict, dict]:
    step = len(prefix)
    world_query = [
        {"actor": 1}, {"actor": 1}, {}, {"animal": 1, "weather": 2},
        {"animal": 1}, {"animal": 1, "weather": 2}, {}, {"place": 1},
    ][step].copy()
    prefix_query = [
        {}, {"actor": 3}, {}, {}, {"description": 3},
        {"animal": 3, "verb": 1}, {}, {"direction": 3},
    ][step]
    if step == 1:
        world_query[prefix[0]] = 3
    if step == 5:
        world_query[prefix[4]] = 3
    return world_query, prefix_query


def validate_prefix(prefix: list[str]) -> None:
    if len(prefix) > 8:
        raise ValueError("prefix cannot exceed eight words")
    for i, word in enumerate(prefix):
        if word not in SLOTS[i][1]:
            raise ValueError(f"word {i + 1}: {word!r}; choose from {SLOTS[i][1]}")


def predict_next(world: World, prefix: list[str], *, attention: bool = True,
                 temperature: float = 1.0) -> dict:
    """Pure next-word distribution; does not sample or mutate the world."""
    validate_prefix(prefix)
    if len(prefix) == 8:
        raise ValueError("sentence is complete (fixed eight-word stop)")
    role, candidates = SLOTS[len(prefix)]
    wq, pq = queries(prefix)
    wc, wt = attend(wq, world_memories(world)) if attention else ({}, [])
    pc, pt = attend(pq, prefix_memories(world, prefix)) if attention else ({}, [])
    choices = []
    for word in candidates:
        prior = {"the": 1.4, "a": 0.3, "this": -0.2, "that": -0.2}.get(word, 0)
        world_score = 1.5 * wc.get(word, 0)
        prefix_score = 1.5 * pc.get(word, 0)
        choices.append(dict(word=word, prior=prior, world_score=world_score,
                            prefix_score=prefix_score,
                            logit=prior + world_score + prefix_score))
    probabilities = softmax([c["logit"] for c in choices], temperature)
    for choice, probability in zip(choices, probabilities):
        choice["probability"] = probability
    return dict(step=len(prefix) + 1, role=role, prefix=list(prefix),
                choices=choices, world_query=wq, prefix_query=pq,
                world_attention=wt, prefix_attention=pt)


def generate(*, seed: int = 7, weather: str = "cold", attention: bool = True,
             temperature: float = 1.0, prefix: list[str] | None = None) -> dict:
    forced = list(prefix or [])
    validate_prefix(forced)
    world, rng = make_world(weather), random.Random(seed)
    initial = asdict(world)
    words, trace = [], []
    for step in range(8):
        distribution = predict_next(world, words, attention=attention, temperature=temperature)
        choices = distribution["choices"]
        probabilities = [c["probability"] for c in choices]
        word = forced[step] if step < len(forced) else rng.choices(
            [c["word"] for c in choices], weights=probabilities, k=1)[0]
        probability = next(c["probability"] for c in choices if c["word"] == word)
        distribution.update(selected=word, selected_probability=probability,
                            forced=step < len(forced))
        trace.append(distribution)
        words.append(word)
    event = world.commit(words)
    return dict(sentence=" ".join(words) + ".", seed=seed, weather=weather,
                attention=attention, temperature=temperature, trace=trace,
                sentence_probability=math.prod(t["selected_probability"] for t in trace),
                continuation_probability=math.prod(t["selected_probability"] for t in trace
                                                  if not t["forced"]),
                world_before=initial, world_after=asdict(world), event=event)


def verify() -> None:
    """Check the probabilistic contract and causal sensitivity, not exact prose."""
    for weather in ("cold", "mild"):
        for enabled in (False, True):
            for seed in range(100):
                result = generate(seed=seed, weather=weather, attention=enabled)
                assert len(result["sentence"].split()) == 8
                assert len(result["trace"]) == 8
                assert len(result["world_after"]["history"]) == 1
                for i, step in enumerate(result["trace"]):
                    assert len({c["word"] for c in step["choices"]}) == 4
                    assert math.isclose(sum(c["probability"] for c in step["choices"]), 1)
                    assert all(0 < c["probability"] < 1 for c in step["choices"])
                    assert step["prefix"] == result["sentence"].rstrip(".").split()[:i]
                    for memory in step["prefix_attention"]:
                        assert int(memory["memory"].split(":")[0]) <= i
    assert generate(seed=42) == generate(seed=42)

    def probs(world, prefix, **kw):
        return {c["word"]: c["probability"]
                for c in predict_next(world, prefix, **kw)["choices"]}

    cold, mild = make_world("cold"), make_world("mild")
    snapshot = deepcopy(cold)
    prefix = ["Lily", "carried", "the"]
    assert probs(cold, prefix)["shivering"] > probs(mild, prefix)["shivering"]
    assert probs(cold, prefix, attention=False) == probs(mild, prefix, attention=False)
    assert probs(cold, ["Lily"])["carried"] > probs(cold, ["Sam"])["carried"]
    assert probs(cold, prefix + ["muddy"])["puppy"] > probs(cold, prefix + ["sleepy"])["puppy"]
    assert cold == snapshot  # predicting alternatives has no physical side effects
    full = generate()["sentence"].rstrip(".").split()
    assert generate(prefix=full)["continuation_probability"] == 1
    print("PASS: 400 samples; four normalized choices × eight words; grounded commits;")
    print("      reproducibility, causal prefix attention, weather/actor interventions, ablation.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--weather", choices=("cold", "mild"), default="cold")
    parser.add_argument("--attention", choices=("on", "off"), default="on")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--prefix", default="", help="force an opening, e.g. 'Lily carried the'")
    parser.add_argument("--samples", type=int, default=1, help="independent worlds; increment seed per sample")
    parser.add_argument("--json", action="store_true", help="full probabilities, contributions, and world trace")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify()
        return
    if args.samples < 1 or not math.isfinite(args.temperature) or args.temperature <= 0:
        parser.error("samples must be >= 1 and temperature must be finite and > 0")
    try:
        validate_prefix(args.prefix.split())
    except ValueError as error:
        parser.error(str(error))
    results = [generate(seed=args.seed + i, weather=args.weather,
                        attention=args.attention == "on", temperature=args.temperature,
                        prefix=args.prefix.split()) for i in range(args.samples)]
    if args.json:
        print(json.dumps(results, indent=2, allow_nan=False))
        return
    for result in results:
        print(f"\nWorld: four children and four chilly, muddy, tired, frightened animals in a meadow.")
        print(f"Four nearby buildings are reachable. Weather: {result['weather']}. Attention: {args.attention}.")
        print(f"Seed {result['seed']} | Four-word support per step; punctuation/stop fixed.\n")
        for step in result["trace"]:
            options = " | ".join(f"{c['word']} {c['probability']:.1%}" for c in step["choices"])
            forced = " (forced)" if step["forced"] else ""
            print(f"{step['step']}. {options}  -> {step['selected']}{forced}")
            for head in ("world", "prefix"):
                memories = step[f"{head}_attention"]
                if memories:
                    weights = ", ".join(f"{m['memory']} {m['weight']:.0%}" for m in memories)
                    print(f"   {head} attention: {weights}")
        print(f"\n{result['sentence']}")
        event = result["event"]
        print(f"World update: {event['actor']} and the {event['animal']} are now {event['after']}.")
        print(f"Sentence probability: {result['sentence_probability']:.6g}")
        if args.prefix:
            print(f"Continuation probability given prefix: {result['continuation_probability']:.6g}")


if __name__ == "__main__":
    main()
