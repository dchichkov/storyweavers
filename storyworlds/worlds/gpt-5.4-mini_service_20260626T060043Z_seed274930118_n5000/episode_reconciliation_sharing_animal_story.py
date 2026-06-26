#!/usr/bin/env python3
"""
A small standalone storyworld: an animal episode about sharing and reconciliation.

Premise:
- Two animal friends want the same pleasant thing.
- One takes it first, which causes hurt feelings.
- A grown helper guides them into sharing.
- The friends reconcile and end the episode together, happier than before.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str = "meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    activity: str
    comfort: str
    value: str


@dataclass
class StoryParams:
    place: str
    treat: str
    hero1: str
    hero2: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_broken_mood(world: World) -> list[str]:
    out = []
    for a in world.entities.values():
        if a.kind != "character":
            continue
        if a.memes.get("hurt", 0.0) < THRESHOLD:
            continue
        sig = ("hurt", a.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        a.memes["sad"] = a.memes.get("sad", 0.0) + 1
        out.append(f"{a.id} felt sad and quiet.")
    return out


def _r_reconcile(world: World) -> list[str]:
    a = world.entities["hero1"]
    b = world.entities["hero2"]
    if a.memes.get("sad", 0.0) < THRESHOLD or b.memes.get("sad", 0.0) < THRESHOLD:
        return []
    if a.memes.get("share", 0.0) < THRESHOLD or b.memes.get("share", 0.0) < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["sad"] = 0.0
    b.memes["sad"] = 0.0
    a.memes["warm"] = a.memes.get("warm", 0.0) + 1
    b.memes["warm"] = b.memes.get("warm", 0.0) + 1
    return ["__reconcile__"]


RULES = [
    _r_broken_mood,
    _r_reconcile,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__reconcile__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(place: Place, treat: Treat, p: StoryParams) -> World:
    world = World(place)
    hero1 = world.add(Entity(id="hero1", kind="character", type="rabbit", label=p.hero1))
    hero2 = world.add(Entity(id="hero2", kind="character", type="fox", label=p.hero2))
    helper = world.add(Entity(id="helper", kind="character", type="deer", label=p.helper))
    item = world.add(Entity(id="treat", type="thing", label=treat.label, phrase=treat.phrase, owner="hero1"))

    hero1.memes["want"] = 1
    hero2.memes["want"] = 1

    world.say(f"{hero1.label} the rabbit and {hero2.label} the fox lived near the {place.name}.")
    world.say(f"They both loved the {treat.label} basket, because it smelled sweet and warm.")
    world.say(f"One bright episode began when {hero1.label} found {treat.phrase} first.")

    world.para()
    world.say(f"{hero1.label} tucked the {treat.label} close and turned away.")
    world.say(f"{hero2.label} reached out too, but there was only one {treat.label}.")
    hero2.memes["hurt"] = 1
    hero1.memes["stubborn"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{helper.label} the deer came over with soft steps and a gentle voice.")
    world.say(f'"Friends can share," {helper.label.lower()} said. "Sharing makes a small treat feel bigger."')
    hero1.memes["share"] = 1
    hero2.memes["share"] = 1
    world.say(f"{hero1.label} broke the {treat.label} in half, and {hero2.label} accepted the smaller piece with a smile.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"In the end, the two friends sat together under a leafy branch.")
    world.say(f"They ate side by side, and the episode ended with warm noses, full bellies, and no hard feelings.")
    world.facts.update(hero1=hero1, hero2=hero2, helper=helper, treat=item, treat_cfg=treat, place=place)
    return world


SETTINGS = {
    "meadow": Place(name="the meadow", kind="meadow", affords={"sharing"}),
    "riverbank": Place(name="the riverbank", kind="bank", affords={"sharing"}),
    "garden": Place(name="the garden", kind="garden", affords={"sharing"}),
}

TREATS = {
    "berries": Treat(
        id="berries",
        label="berry cake",
        phrase="a little berry cake",
        activity="sharing",
        comfort="sweet",
        value="cake",
    ),
    "apples": Treat(
        id="apples",
        label="apple slices",
        phrase="a bowl of apple slices",
        activity="sharing",
        comfort="juicy",
        value="fruit",
    ),
    "carrots": Treat(
        id="carrots",
        label="carrot sticks",
        phrase="a plate of carrot sticks",
        activity="sharing",
        comfort="crisp",
        value="snack",
    ),
}

NAMES_RABBIT = ["Milo", "Bunny", "Pip", "Toto", "Luna"]
NAMES_FOX = ["Ruby", "Finn", "Penny", "Cleo", "Tansy"]
NAMES_DEER = ["Mara", "Dawn", "Willow", "Hazel", "June"]


@dataclass
class Registry:
    places: dict[str, Place]
    treats: dict[str, Treat]


REGISTRY = Registry(places=SETTINGS, treats=TREATS)


def explain_invalid(place: str, treat: str) -> str:
    if place not in SETTINGS:
        return "(No story: unknown place.)"
    if treat not in TREATS:
        return "(No story: unknown treat.)"
    if "sharing" not in SETTINGS[place].affords:
        return "(No story: this place does not support the sharing episode.)"
    return "(No story: this combination is not reasonable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("(No story: unknown place.)")
    if args.treat and args.treat not in TREATS:
        raise StoryError("(No story: unknown treat.)")

    place = args.place or rng.choice(list(SETTINGS))
    treat = args.treat or rng.choice(list(TREATS))
    if "sharing" not in SETTINGS[place].affords:
        raise StoryError(explain_invalid(place, treat))

    hero1 = args.hero1 or rng.choice(NAMES_RABBIT)
    hero2 = args.hero2 or rng.choice([n for n in NAMES_FOX if n != hero1])
    helper = args.helper or rng.choice(NAMES_DEER)
    return StoryParams(place=place, treat=treat, hero1=hero1, hero2=hero2, helper=helper)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    treat = TREATS[params.treat]
    world = build_world(place, treat, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about an episode at {f["place"].name} where two friends learn to share {f["treat_cfg"].phrase}.',
        f"Tell a gentle reconciliation story with a rabbit, a fox, and a deer, ending in sharing.",
        f'Write a simple story about animals who want the same snack and become friends again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h1, h2, helper = f["hero1"], f["hero2"], f["helper"]
    treat = f["treat_cfg"]
    place = f["place"].name
    return [
        QAItem(
            question=f"Who was the story mainly about at {place}?",
            answer=f"It was about {h1.label}, a rabbit, and {h2.label}, a fox, who both wanted {treat.phrase}.",
        ),
        QAItem(
            question=f"What caused the upset in the episode?",
            answer=f"The upset started because {h1.label} found the {treat.label} first and {h2.label} wanted some too.",
        ),
        QAItem(
            question=f"How did the friends fix the problem?",
            answer=f"{helper.label} helped them calm down, and then the two friends shared the {treat.label} so nobody was left out.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the friends sitting together, eating side by side, and feeling warm and happy again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people or animals use or enjoy something too.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a disagreement so friends feel close again.",
        ),
        QAItem(
            question="Why can a kind helper matter in a story?",
            answer="A kind helper can calm feelings, explain a better choice, and help everyone agree on what to do next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when two animals can share a treat and end reconciled.
valid_place(P) :- place(P), affords(P, sharing).
valid_story(P, T) :- valid_place(P), treat(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: sharing and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(p, t) for p in SETTINGS for t in TREATS if "sharing" in SETTINGS[p].affords}
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(atoms - py))
    print("only in Python:", sorted(py - atoms))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} valid story combinations:")
        for p, t in pairs:
            print(f"  {p:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for treat in TREATS:
                if "sharing" in SETTINGS[place].affords:
                    params = StoryParams(place=place, treat=treat, hero1="Milo", hero2="Ruby", helper="Mara")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
