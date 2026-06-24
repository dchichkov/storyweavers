#!/usr/bin/env python3
"""
Standalone storyworld: Tragic Storm Drain Kindness Animal Story.

A small, self-contained simulation about an animal in a storm drain who faces a
tragic moment, receives kindness, and ends with a clear change in state.
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    helper: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "rabbit", "fox", "mouse", "dog", "pigeon"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the storm drain"
    damp: bool = True


@dataclass
class Hazard:
    id: str
    description: str
    mess: str
    risk: str
    rescue_need: str


@dataclass
class Kindness:
    id: str
    label: str
    action: str
    effect: str
    enables: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


@dataclass
class StoryParams:
    animal: str
    name: str
    helper: str
    hazard: str
    seed: Optional[int] = None


ANIMALS = {
    "kitten": ("kitten", "a small gray kitten"),
    "duckling": ("duckling", "a small yellow duckling"),
    "puppy": ("puppy", "a little brown puppy"),
    "bunny": ("bunny", "a tiny white bunny"),
}

HAZARDS = {
    "rising_water": Hazard(
        id="rising_water",
        description="the water was rising fast",
        mess="water",
        risk="swept away",
        rescue_need="needed a safe place above the rush",
    ),
    "broken_grate": Hazard(
        id="broken_grate",
        description="a broken grate had left sharp metal sticking out",
        mess="danger",
        risk="scratched",
        rescue_need="needed someone gentle to block the sharp edge",
    ),
    "lost_toy": Hazard(
        id="lost_toy",
        description="a favorite toy had fallen into a dark pipe",
        mess="sadness",
        risk="heartache",
        rescue_need="needed help to reach the toy",
    ),
}

KINDNESSES = {
    "warm_towel": Kindness(
        id="warm_towel",
        label="a warm towel",
        action="wrapped the shivering animal in a warm towel",
        effect="the shaking eased",
        enables="kept the animal calm and dry",
    ),
    "gentle_lift": Kindness(
        id="gentle_lift",
        label="gentle hands",
        action="lifted the animal onto a dry ledge",
        effect="the danger below was far away",
        enables="gave the animal a safe place to sit",
    ),
    "soft_voice": Kindness(
        id="soft_voice",
        label="a soft voice",
        action="spoke in a soft voice and waited patiently",
        effect="the fear slowly melted",
        enables="helped the animal trust the helper",
    ),
}

CURATED = [
    StoryParams(animal="kitten", name="Mina", helper="fox", hazard="rising_water"),
    StoryParams(animal="duckling", name="Pip", helper="dog", hazard="broken_grate"),
    StoryParams(animal="bunny", name="Luna", helper="mouse", hazard="lost_toy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tragic storm drain kindness animal storyworld.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=sorted({k for k in {"fox", "dog", "mouse"}}))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--name")
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


def reasonableness_check(params: StoryParams) -> None:
    if params.animal == "duckling" and params.hazard == "broken_grate":
        return
    if params.animal == "kitten" and params.hazard == "rising_water":
        return
    if params.animal == "bunny" and params.hazard == "lost_toy":
        return
    raise StoryError("No strong tragic-but-kind story fits that combination.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    animal = args.animal or rng.choice(sorted(ANIMALS))
    hazard = args.hazard or rng.choice(sorted(HAZARDS))
    helper = args.helper or rng.choice(["fox", "dog", "mouse"])
    name = args.name or rng.choice(["Mina", "Pip", "Luna", "Dot", "Bean"])
    params = StoryParams(animal=animal, name=name, helper=helper, hazard=hazard)
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = World(Setting())
    animal_kind, animal_phrase = ANIMALS[params.animal]
    hazard = HAZARDS[params.hazard]
    kindness = KINDNESSES["soft_voice" if params.hazard == "lost_toy" else "gentle_lift" if params.hazard == "broken_grate" else "warm_towel"]

    child = world.add(Entity(id=params.name, kind="character", type=animal_kind, label=params.name, phrase=animal_phrase))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper, label=params.helper))
    child.memes["sadness"] = 1.0
    child.memes["fear"] = 1.0
    child.meters["trapped"] = 1.0

    world.say(f"{child.label} the {animal_kind} lived near {world.setting.place}.")
    world.say(f"One day, {hazard.description}, and that was tragic for {child.label}.")
    world.say(f"{child.label} was small and frightened, because {hazard.rescue_need}.")

    world.para()
    world.say(f"Then {helper.label} found {child.label} in the drain.")
    world.say(f"{helper.label} showed kindness by {kindness.action}.")
    child.memes["trust"] = 1.0
    child.memes["sadness"] = 0.0
    child.memes["hope"] = 1.0
    child.meters["trapped"] = 0.0
    child.meters["safe"] = 1.0

    world.para()
    world.say(f"{kindness.effect}, and {child.label} stopped trembling.")
    world.say(f"In the end, {child.label} was safe in the warm light above the drain, and kindness had changed the day.")

    world.facts.update(child=child, helper=helper, hazard=hazard, kindness=kindness)
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
    child = f["child"]
    hazard = f["hazard"]
    kind = f["kindness"]
    return [
        f"Write a short Animal Story about {child.label}, a small animal in a storm drain, where {hazard.description}.",
        f"Tell a tragic little story that ends with kindness and safety for {child.label}.",
        f"Write a gentle animal story in the storm drain using the idea of {kind.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    hazard = f["hazard"]
    kind = f["kindness"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.label} the {child.type}, who lived near the storm drain.",
        ),
        QAItem(
            question=f"What made the day tragic for {child.label}?",
            answer=f"The day was tragic because {hazard.description}, and {child.label} felt scared and trapped.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} helped by showing kindness: {kind.action}. That made {child.label} feel safe again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a storm drain?",
            answer="A storm drain is a channel that carries rainwater away so streets do not flood as much.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring when someone is in trouble or feels sad.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(A,H,Z) :- animal(A), helper(H), hazard(Z).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for h in {"fox", "dog", "mouse"}:
        lines.append(asp.fact("helper", h))
    for z in HAZARDS:
        lines.append(asp.fact("hazard", z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    found = sorted(set(asp.atoms(model, "valid_story")))
    expected = sorted((a, h, z) for a in ANIMALS for h in {"fox", "dog", "mouse"} for z in HAZARDS)
    if found == expected:
        print(f"OK: ASP parity verified ({len(found)} triples).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for block, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(f"== {block} ==")
            if block == "Prompts":
                for p in items:
                    print(p)
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
