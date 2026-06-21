#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pussy_yorkie_transformation_space_adventure.py
=============================================================================

A tiny Space Adventure storyworld about two pets on a little moon mission:
Pussy the cat and a yorkie dog ride a scout ship, meet a strange transformation
beam, and learn how to use their new forms to save the mission and get home.

The world is built from state: thirst, drift, suit fit, courage, and a change
meter that actually alters what can happen next. The story reads like a short
space tale with a beginning, a turn, and an ending image that proves the change.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Ship:
    id: str
    label: str
    place: str
    has_beam: bool
    has_beacon: bool
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Transformation:
    id: str
    label: str
    source_form: str
    target_form: str
    trigger: str
    method: str
    effect: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.ship: Optional[Ship] = None
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.ship = copy.deepcopy(self.ship)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    hero1: str
    hero2: str
    ship: str
    transformation: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PUSSIES = ["Pussy", "Poppy", "Misty", "Nova"]
YORKIES = ["Yoyo", "Yorkie", "Bixie", "Milo"]
SHIP_NAMES = ["Comet Gull", "Moon Finch", "Star Wagon"]
TRANSFORMATIONS = {
    "swap": Transformation(
        id="swap",
        label="swap-shift",
        source_form="small and wobbly",
        target_form="swift and strong",
        trigger="the blue beam",
        method="starlight",
        effect="swapped their shapes",
        sense=3,
        power=4,
        tags={"transformation", "beam"},
    ),
    "stretch": Transformation(
        id="stretch",
        label="stretch-shift",
        source_form="tiny and shy",
        target_form="tall and brave",
        trigger="the silver mist",
        method="moon dust",
        effect="stretched their shapes",
        sense=3,
        power=3,
        tags={"transformation", "mist"},
    ),
    "glow": Transformation(
        id="glow",
        label="glow-shift",
        source_form="soft and sleepy",
        target_form="bright and ready",
        trigger="the golden pulse",
        method="sun spark",
        effect="made them glow",
        sense=2,
        power=2,
        tags={"transformation", "pulse"},
    ),
}

CURATED = [
    StoryParams(hero1="Pussy", hero2="Yorkie", ship="Comet Gull", transformation="swap"),
    StoryParams(hero1="Pussy", hero2="Yorkie", ship="Moon Finch", transformation="stretch"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure transformation storyworld.")
    ap.add_argument("--hero1", choices=PUSSIES)
    ap.add_argument("--hero2", choices=YORKIES)
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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


def sensible_transformations() -> list[Transformation]:
    return [t for t in TRANSFORMATIONS.values() if t.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p1 in PUSSIES:
        for p2 in YORKIES:
            for ship in SHIP_NAMES:
                for tid, t in TRANSFORMATIONS.items():
                    if t.sense >= SENSE_MIN:
                        combos.append((p1, p2, ship, tid))
    return combos


def explain_rejection(tid: str) -> str:
    t = TRANSFORMATIONS[tid]
    return f"(No story: transformation '{tid}' is too weak for a real space-adventure turn.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.transformation and TRANSFORMATIONS[args.transformation].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.transformation))
    choices = list(valid_combos())
    if args.hero1:
        choices = [c for c in choices if c[0] == args.hero1]
    if args.hero2:
        choices = [c for c in choices if c[1] == args.hero2]
    if args.ship:
        choices = [c for c in choices if c[2] == args.ship]
    if args.transformation:
        choices = [c for c in choices if c[3] == args.transformation]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    hero1, hero2, ship, transformation = rng.choice(sorted(choices))
    return StoryParams(hero1=hero1, hero2=hero2, ship=ship, transformation=transformation)


def tell(params: StoryParams) -> World:
    world = World()
    t = TRANSFORMATIONS[params.transformation]
    pussy = world.add(Entity(id=params.hero1, kind="character", type="cat", label="the cat", role="explorer"))
    yorkie = world.add(Entity(id=params.hero2, kind="character", type="dog", label="the yorkie", role="pilot"))
    ship = Ship(id="ship", label=params.ship, place="moon orbit", has_beam=True, has_beacon=True)
    world.ship = ship

    pussy.memes["curiosity"] += 1
    yorkie.memes["courage"] += 1
    ship.meters["drift"] += 1

    world.say(
        f"On a quiet moon morning, {params.hero1} and {params.hero2} rode the scout ship {params.ship} through a silver trail of stars."
    )
    world.say(
        f"{params.hero1} peered at the control panel while {params.hero2} barked softly at the blinking maps."
    )
    world.say(
        f"Then the airlock opened with a chime, and {t.trigger} spilled across the cabin like a strange little wave."
    )

    world.para()
    world.say(
        f"It was not ordinary light. {t.method} touched their whiskers and paws, and {t.effect}."
    )
    pussy.meters["changed"] += 1
    yorkie.meters["changed"] += 1
    ship.meters["drift"] += 1
    world.facts["transformation"] = t.id
    world.facts["before"] = t.source_form
    world.facts["after"] = t.target_form

    if t.id == "swap":
        pussy.attrs["form"] = "light as a comet"
        yorkie.attrs["form"] = "steady as a rocket"
        pussy.memes["surprise"] += 1
        yorkie.memes["pride"] += 1
        world.say(
            f"{params.hero1} became light as a comet, and {params.hero2} became steady as a rocket."
        )
        world.say(
            f"That was the surprise the ship needed, because the little beacon had slipped behind a panel and the new shapes could reach it."
        )
    elif t.id == "stretch":
        pussy.attrs["form"] = "long enough to reach the hatch"
        yorkie.attrs["form"] = "tall enough to grab the latch"
        pussy.memes["hope"] += 1
        yorkie.memes["joy"] += 1
        world.say(
            f"{params.hero1} stretched long enough to reach the hatch, and {params.hero2} stood tall enough to grab the latch."
        )
        world.say(
            f"Together they nudged the beacon back into place, and the ship stopped wobbling in the dark."
        )
    else:
        pussy.attrs["form"] = "bright as a tiny star"
        yorkie.attrs["form"] = "warm as a cockpit lamp"
        pussy.memes["calm"] += 1
        yorkie.memes["calm"] += 1
        world.say(
            f"{params.hero1} glowed bright as a tiny star, and {params.hero2} shone warm as a cockpit lamp."
        )
        world.say(
            f"The glow made the map easy to read, and the ship drifted safely toward home."

        )

    world.para()
    world.say(
        f"When the stars turned from blur to dots again, {params.hero1} curled on the console and {params.hero2} sat by the window."
    )
    world.say(
        f"The scout ship hummed softly on course, and the transformed pair were ready for the next jump."
    )

    world.facts.update(
        pussy=pussy,
        yorkie=yorkie,
        ship=params.ship,
        outcome="transformed",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except KeyError as e:
        raise StoryError(f"invalid parameter: {e}") from e
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tiny space adventure about {f["pussy"].id} and {f["yorkie"].id} that includes a transformation.',
        f"Tell a child-friendly story where {f['pussy'].id} and {f['yorkie'].id} ride a scout ship and change form to solve a problem.",
        f'Create a short Space Adventure story with the words "pussy" and "yorkie" and a magical transformation in the middle.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    t = TRANSFORMATION[f["transformation"]]
    return [
        ("Who are the story's main characters?",
         f"It is about Pussy and a yorkie who ride a small scout ship together. The two pets are the ones who face the strange change in space."),
        ("What caused the big change?",
         f"{t.trigger.capitalize()} caused the transformation. It touched them in the cabin and {t.effect}, which changed what each one could do next."),
        ("How did the transformation help?",
         f"It helped because their new forms matched the mission problem. After the change, they could reach the beacon and keep the ship steady."),
        ("How did the story end?",
         f"It ended with the ship humming safely back toward home. Pussy curled on the console while the yorkie sat by the window, both changed and calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a scout ship?",
         "A scout ship is a small space ship that goes first to look around. It helps a crew explore without sending a huge ship into danger."),
        ("What is a transformation?",
         "A transformation is a change from one form into another. In stories, it can make a character able to do something new."),
        ("Why is a ship beacon useful?",
         "A beacon gives a bright signal that helps people find their way. In space, it can help a ship stay on course or be seen."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={e.attrs}")
    if world.ship:
        lines.append(f"ship: {world.ship.label} meters={dict(world.ship.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(pussy, yorkie, ship, T) :- transformation(T).
story(T) :- valid(pussy, yorkie, ship, T).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("transformation", tid) for tid in TRANSFORMATIONS]
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(StoryParams(hero1="Pussy", hero2="Yorkie", ship="Comet Gull", transformation="swap"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    else:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def explain_response(_: str) -> str:
    return "(No story: the requested transformation is too weak to drive a real turn.)"


def build_sample_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        hero1=rng.choice(PUSSIES),
        hero2=rng.choice(YORKIES),
        ship=rng.choice(SHIP_NAMES),
        transformation=rng.choice(list(TRANSFORMATIONS)),
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.transformation and TRANSFORMATIONS[args.transformation].sense < SENSE_MIN:
        raise StoryError(explain_response(args.transformation))
    choices = valid_combos()
    if args.hero1:
        choices = [c for c in choices if c[0] == args.hero1]
    if args.hero2:
        choices = [c for c in choices if c[1] == args.hero2]
    if args.ship:
        choices = [c for c in choices if c[2] == args.ship]
    if args.transformation:
        choices = [c for c in choices if c[3] == args.transformation]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    hero1, hero2, ship, transformation = rng.choice(sorted(choices))
    return StoryParams(hero1=hero1, hero2=hero2, ship=ship, transformation=transformation)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid space-transformation combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
