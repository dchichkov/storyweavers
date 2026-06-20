#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bury_kindness_whodunit.py
=========================================================

A standalone story world for a tiny whodunit-style kindness mystery:
someone notices a missing keepsake, everyone searches, clues reveal that a
child buried the object in a garden patch to keep it safe, and the ending
proves the act was kind rather than cruel.

The domain is deliberately small: one household, one missing object, a short
search, a reveal, and a warm resolution. The prose is driven from simulated
state, not from a frozen paragraph template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/bury_kindness_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/bury_kindness_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/bury_kindness_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/bury_kindness_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/bury_kindness_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"buried": 0.0, "found": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "kindness": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    hiding_spot: str
    ground: str
    weather: str = "mild"


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    precious: bool = True
    small: bool = True


@dataclass
class ClueCfg:
    id: str
    label: str
    phrase: str
    points_to: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PEOPLE = {
    "child": [("Mina", "girl"), ("Eli", "boy"), ("Nora", "girl"), ("Theo", "boy"), ("Luna", "girl")],
    "helper": [("Mom", "mother"), ("Dad", "father"), ("Aunt Bea", "woman"), ("Uncle Ray", "man")],
}

PLACES = {
    "garden": Place("garden", "the garden", "under the bean patch", "soft dirt"),
    "yard": Place("yard", "the yard", "beside the rose bush", "cool soil"),
    "shed": Place("shed", "the shed", "under an old flower pot", "dusty boards"),
}

OBJECTS = {
    "ring": ObjectCfg("ring", "silver ring", "a silver ring", precious=True, small=True),
    "button": ObjectCfg("button", "blue button", "a blue button", precious=True, small=True),
    "note": ObjectCfg("note", "folded note", "a folded note", precious=True, small=True),
}

CLUES = {
    "dirt": ClueCfg("dirt", "a little dirt pile", "a little dirt pile with tiny finger lines", "buried"),
    "shovel": ClueCfg("shovel", "small shovel", "a toy shovel near the bean patch", "buried"),
    "leaf": ClueCfg("leaf", "leaf trail", "a line of bent leaves leading to the patch", "buried"),
}

BURIED_SPOTS = ["under the bean patch", "near the fence", "beside the rose bush", "under the old swing"]
KIND_ACTS = [
    "kept it safe for later",
    "hid it so nobody would lose it",
    "made a little treasure spot and planned to return it",
]

NAME_POOL = [n for n, _ in PEOPLE["child"]]
HELPER_POOL = [n for n, _ in PEOPLE["helper"]]


@dataclass
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    place: str
    object: str
    clue: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit-style kindness mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            for clue in CLUES:
                combos.append((place, obj, clue))
    return combos


def explain_rejection() -> str:
    return "(No story: this combination does not support a buried-object mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, clue = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAME_POOL)
    helper = args.helper or rng.choice(HELPER_POOL)
    if helper == child:
        helper = rng.choice([n for n in HELPER_POOL if n != child])
    child_gender = next(g for n, g in PEOPLE["child"] if n == child)
    helper_gender = next(g for n, g in PEOPLE["helper"] if n == helper)
    return StoryParams(child, child_gender, helper, helper_gender, place, obj, clue)


def _make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    obj = world.add(Entity("object", kind="thing", type="object", label=OBJECTS[params.object].label))
    clue = world.add(Entity("clue", kind="thing", type="clue", label=CLUES[params.clue].label))
    world.facts.update(child=child, helper=helper, object=obj, clue=clue)
    return world


def _bury(world: World, child: Entity, obj: Entity, place: Place) -> None:
    child.memes["kindness"] += 1
    obj.meters["buried"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} walked through {place.label} with a small secret."
    )
    world.say(
        f"{child.id} found a good hiding spot {place.hiding_spot} and tucked away {OBJECTS[obj.label.split()[0]] .phrase if False else obj.label}."
    )


def generate_story_lines(world: World, params: StoryParams) -> None:
    child = world.get(params.child)
    helper = world.get(params.helper)
    obj = world.get("object")
    clue = world.get("clue")
    place = world.place

    world.say(
        f"{child.id} loved being gentle with little things, and {helper.id} knew that about {child.pronoun('object')}."
    )
    world.say(
        f"One morning, {child.id} noticed {OBJECTS[params.object].phrase} missing from the windowsill."
    )
    world.para()
    world.say(
        f"{helper.id} frowned and looked around {place.label}. 'Where could it be?' {helper.id} asked."
    )
    world.say(
        f"{child.id} stood very still, then stared at {place.hiding_spot}. There was {clue.phrase} there, and that felt like a clue."
    )
    child.memes["worry"] += 1
    clue.meters["found"] += 1
    world.para()
    world.say(
        f"{child.id} pointed to the dirt and said, 'I remember now. I buried it there so it would stay safe.'"
    )
    child.memes["kindness"] += 1
    obj.meters["buried"] = 1.0
    world.say(
        f"{helper.id} blinked, then smiled. 'Oh,' {helper.pronoun()} said softly, 'you did not hide it to be sneaky. You hid it to be kind.'"
    )
    world.say(
        f"{child.id} nodded. The little object was dug up carefully, brushed clean, and placed on the windowsill again."
    )
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.para()
    world.say(
        f"By evening, the mystery was solved: the missing {OBJECTS[params.object].label} had been buried, and the only thing hurt was the dirt."
    )
    world.say(
        f"{child.id} smiled at the safe, bright windowsill, glad that {child.pronoun('possessive')} kind idea had been understood."
    )
    world.facts.update(outcome="revealed", buried=True, resolved=True, object_label=OBJECTS[params.object].label)


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    generate_story_lines(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a whodunit-style story for a young child where {f['child'].id} buried a missing keepsake to keep it safe.",
        f"Tell a gentle mystery where the clue is {f['clue'].label} and the word bury appears.",
        f"Write a short kindness mystery with a missing {f['object'].label} and a warm reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj = f["object"]
    clue = f["clue"]
    return [
        ("What was missing?",
         f"The missing thing was {OBJECTS[world.facts['object'].label if False else obj.label].phrase if False else obj.label}, the little keepsake that started the mystery."),
        ("What did the clue show?",
         f"The clue was {clue.label}, and it showed that something had been buried in the garden. That made the search turn toward the dirt instead of the house."),
        ("Why did {child} bury the object?".format(child=child.id),
         f"{child.id} buried it because {child.id} wanted to keep it safe. It was a kind idea, even though it confused everyone at first."),
        ("How did the story end?",
         f"The object was dug up, cleaned off, and returned to the windowsill. Everyone understood that {child.id} had been kind, not mean."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does bury mean?",
         "To bury something means to put it under dirt or sand so it is covered up. People sometimes bury things to keep them safe."),
        ("Why can clues help solve a mystery?",
         "Clues are little bits of information that point toward the answer. A clue can show where to look next."),
        ("What is kindness?",
         "Kindness means doing something gentle and caring for someone else. A kind choice helps instead of hurts."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place, object, clue) :- place(place), object(object), clue(clue).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mina", "girl", "Mom", "mother", "garden", "ring", "dirt"),
    StoryParams("Eli", "boy", "Dad", "father", "yard", "button", "leaf"),
    StoryParams("Nora", "girl", "Aunt Bea", "woman", "shed", "note", "shovel"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
