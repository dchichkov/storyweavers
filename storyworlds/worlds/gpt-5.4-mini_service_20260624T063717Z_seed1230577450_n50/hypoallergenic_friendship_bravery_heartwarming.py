#!/usr/bin/env python3
"""
storyworlds/worlds/hypoallergenic_friendship_bravery_heartwarming.py
===================================================================

A small storyworld about a child, a new friend, and a brave choice that keeps
everyone comfortable. The core premise is heartwarming: someone wants a close
friendship, a gentle problem appears because of allergies, and the characters
find a kind, brave way to stay together.

Seed-tale sketch:
---
A child brings home a fluffy new friend. The friend is sweet, but the child has
sneezes and itchy eyes around fur. The child feels sad at first, then brave
enough to ask for help. Together, they choose a hypoallergenic pet bed, a soft
brush, and a better way to visit so the friendship can stay warm and safe.
---

The simulated world tracks:
- physical meters: fluff, dander, distance, comfort, cleanliness, safety
- emotional memes: worry, bravery, friendship, relief, trust

The story is intentionally small and constraint-driven:
- the friend must be a hypoallergenic animal or toy-animal companion
- the child may only adopt a friend that matches the family's allergy bounds
- the resolution must genuinely lower exposure and raise comfort
- bravery is shown as asking for a sensible change, not reckless exposure
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    friendly: bool = False
    hypoallergenic: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Home:
    place: str = "the cozy house"
    supports: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    phrase: str
    kind: str
    hypoallergenic: bool
    fluff: float
    needs_brush: bool = False


@dataclass
class StoryParams:
    place: str
    companion: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, home: Home) -> None:
        self.home = home
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.home)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _deepcopy_entities(entities: dict[str, Entity]) -> dict[str, Entity]:
    import copy
    return copy.deepcopy(entities)


World.copy = lambda self: (lambda w: (setattr(w, "entities", _deepcopy_entities(self.entities)), setattr(w, "paragraphs", [[]]), setattr(w, "facts", dict(self.facts)), setattr(w, "fired", set(self.fired)), w)[-1])(World(self.home))  # type: ignore


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ella", "Maya", "Ruby", "Zoe"]
BOY_NAMES = ["Theo", "Noah", "Finn", "Eli", "Leo", "Owen", "Ben", "Max"]
TRAITS = ["kind", "gentle", "curious", "careful", "brave", "soft-spoken"]

HOMES = {
    "house": Home(place="the cozy house", supports={"visit", "care", "brush"}),
    "garden": Home(place="the sunny garden", supports={"visit", "care", "brush"}),
    "porch": Home(place="the little porch", supports={"visit", "care"}),
}

COMPANIONS = {
    "poodle": Companion(
        id="poodle",
        label="poodle",
        phrase="a fluffy hypoallergenic poodle",
        kind="dog",
        hypoallergenic=True,
        fluff=2.0,
        needs_brush=True,
    ),
    "cat": Companion(
        id="cat",
        label="cat",
        phrase="a sleek hypoallergenic cat",
        kind="cat",
        hypoallergenic=True,
        fluff=1.0,
        needs_brush=True,
    ),
    "rabbit": Companion(
        id="rabbit",
        label="rabbit",
        phrase="a tiny hypoallergenic rabbit",
        kind="rabbit",
        hypoallergenic=True,
        fluff=1.5,
        needs_brush=False,
    ),
    "plush": Companion(
        id="plush",
        label="plush friend",
        phrase="a soft hypoallergenic plush friend",
        kind="toy",
        hypoallergenic=True,
        fluff=0.5,
        needs_brush=False,
    ),
}

CURATED = [
    StoryParams(place="house", companion="poodle", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="garden", companion="rabbit", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="porch", companion="plush", name="Luna", gender="girl", parent="mother", trait="curious"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, comp) for place in HOMES for comp in COMPANIONS if COMPANIONS[comp].hypoallergenic]


def story_reasonable(place: str, companion: str) -> bool:
    return place in HOMES and companion in COMPANIONS and COMPANIONS[companion].hypoallergenic


def explain_rejection(place: str, companion: str) -> str:
    if companion not in COMPANIONS:
        return "(No story: the chosen companion is not in this world.)"
    if not COMPANIONS[companion].hypoallergenic:
        return "(No story: this world only tells stories about hypoallergenic companions.)"
    if place not in HOMES:
        return "(No story: the chosen place is not in this world.)"
    return "(No story: that combination is not supported.)"


ASP_RULES = r"""
valid(Place, Companion) :- home(Place), hypoallergenic(Companion).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in HOMES:
        lines.append(asp.fact("home", pid))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        if c.hypoallergenic:
            lines.append(asp.fact("hypoallergenic", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming friendship/bravery storyworld with a hypoallergenic companion.")
    ap.add_argument("--place", choices=HOMES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.companion and not story_reasonable(args.place, args.companion):
        raise StoryError(explain_rejection(args.place, args.companion))
    place = args.place or rng.choice(list(HOMES))
    companion = args.companion or rng.choice(list(COMPANIONS))
    if not story_reasonable(place, companion):
        raise StoryError(explain_rejection(place, companion))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _choose_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, companion=companion, name=name, gender=gender, parent=parent, trait=trait)


def _build_world(params: StoryParams) -> World:
    world = World(HOMES[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    comp_cfg = COMPANIONS[params.companion]
    comp = world.add(Entity(
        id=comp_cfg.id,
        kind="thing",
        type=comp_cfg.kind,
        label=comp_cfg.label,
        phrase=comp_cfg.phrase,
        friendly=True,
        hypoallergenic=comp_cfg.hypoallergenic,
        meters={"fluff": comp_cfg.fluff, "distance": 2.0, "comfort": 0.5, "safety": 0.5},
        memes={"worry": 0.0, "bravery": 0.0, "friendship": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    child.meters.update({"sneeze": 0.0, "comfort": 0.5})
    child.memes.update({"worry": 0.0, "bravery": 0.0, "friendship": 0.0, "relief": 0.0, "trust": 0.0})
    parent.memes.update({"worry": 0.0, "bravery": 0.0, "friendship": 0.0, "relief": 0.0, "trust": 0.0})
    world.facts.update(child=child, parent=parent, companion=comp, companion_cfg=comp_cfg, params=params)
    return world


def _air_quality_penalty(comp: Entity, child: Entity) -> None:
    if not comp.hypoallergenic:
        child.meters["sneeze"] += 2.0
        child.memes["worry"] += 1.0


def _resolve_with_grooming(world: World) -> None:
    child = world.facts["child"]
    comp = world.facts["companion"]
    if comp.hypoallergenic:
        comp.meters["distance"] = 1.0
        comp.meters["safety"] = 1.0
        child.meters["comfort"] += 1.0
        child.memes["relief"] += 1.0


def generate_story(world: World) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    comp = world.facts["companion"]
    params = world.facts["params"]

    world.say(f"{child.id} lived in {world.home.place} and had a {params.trait} heart.")
    world.say(f"One day, {child.id} met {comp.phrase}, and the little friend wagged, curled, or nuzzled close with a warm hello.")
    world.say(f"{child.id} wanted to stay near the new friend, because friendship already felt bright and full of promise.")
    world.para()

    child.memes["worry"] += 1.0
    _air_quality_penalty(comp, child)
    world.say(f"But there was one tricky thing: {child.id} sneezed around fuzzy animals, and {child.pronoun('possessive')} nose felt tingly.")
    world.say(f"{parent.pronoun().capitalize()} noticed the worry and said, \"Let's be brave and choose a safer way to be friends.\"")
    child.memes["bravery"] += 1.0
    world.say(f"{child.id} took a deep breath. That was brave, because speaking up when you are disappointed can feel very big.")
    world.para()

    world.say(f"Together they picked a hypoallergenic bed, a gentle brush, and a calm spot in {world.home.place}.")
    _resolve_with_grooming(world)
    child.memes["friendship"] += 2.0
    comp.memes["friendship"] += 2.0
    child.memes["trust"] += 1.0
    parent.memes["relief"] += 1.0
    world.say(f"With the soft bed ready, {child.id} could sit close without sneezing, and the friend stayed clean and comfortable.")
    world.say(f"By bedtime, {child.id} was smiling, {comp.label} was cozy, and the whole room felt peaceful and kind.")

    world.facts["resolved"] = True
    world.facts["hypoallergenic"] = comp.hypoallergenic
    world.facts["brave_choice"] = True


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    comp = world.facts["companion"]
    parent = world.facts["parent"]
    params = world.facts["params"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a {params.trait} child who met {comp.label} in {world.home.place}.",
        ),
        QAItem(
            question=f"Why did {child.id} need a careful plan with {comp.label}?",
            answer=f"{child.id} sneezed around fuzzy animals, so the family chose a hypoallergenic plan that kept the friendship gentle and safe.",
        ),
        QAItem(
            question=f"What brave thing did {child.id} do?",
            answer=f"{child.id} spoke up about the sneezing and helped choose a safer way to stay close to {comp.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with {child.id} smiling beside {comp.label}, with comfort, trust, and friendship all growing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hypoallergenic mean?",
            answer="Hypoallergenic means something is less likely to cause an allergic reaction, like sneezing or itchy eyes.",
        ),
        QAItem(
            question="Why can brushing help a fluffy pet?",
            answer="Brushing can remove loose fur and dust, which helps keep the pet cleaner and can make the air gentler for sensitive people.",
        ),
        QAItem(
            question="What is bravery in a heartwarming story?",
            answer="Bravery can mean speaking up kindly, asking for help, or choosing a safe solution even when you feel disappointed.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    comp = world.facts["companion"]
    return [
        f"Write a heartwarming story about {child.id} and a hypoallergenic {comp.label} becoming friends.",
        f"Tell a gentle story where a child is brave about allergies and still makes a new friend.",
        f"Write a simple friendship story that includes a safe, hypoallergenic choice and a happy ending.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, comp) for place in HOMES for comp in COMPANIONS if COMPANIONS[comp].hypoallergenic)


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: ASP matches python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only asp:", sorted(clingo_set - py_set))
    print("only python:", sorted(py_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser_compat() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, companion in combos:
            print(f"  {place:12} {companion}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
