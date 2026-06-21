#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scout_friction_tomb_moral_value_comedy.py
==========================================================================

A standalone story world about a tiny scout team, a stubborn tomb, and the
comic moral that telling the truth and helping each other makes a tricky day go
better. The seed words are present in the premise and state: scout, friction,
tomb.

This script follows the shared storyworld contract:
- stdlib-only
- StoryParams, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- Python validity gate plus inline ASP twin
- state-driven story text, grounded QA, trace, json, verify, show-asp, asp
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    echo: str
    has_tomb: bool = True
    has_wind: bool = False
    has_steps: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class FrictionThing:
    id: str
    label: str
    surface: str
    sound: str
    slow: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ValueChoice:
    id: str
    label: str
    sentence: str
    better_sentence: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    friction: str
    value: str
    scout1: str
    scout1_gender: str
    scout2: str
    scout2_gender: str
    adult: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


PLACES = {
    "sandstone": Place("sandstone", "an old sandstone tomb", "the air echoed like a spoon in a teacup"),
    "hill": Place("hill", "a little hill tomb", "the air echoed like a giggle under a blanket"),
    "museum": Place("museum", "the museum tomb room", "the air echoed like shoes in a hallway"),
}

FRICTIONS = {
    "sand": FrictionThing("sand", "sand", "the dusty floor", "scritch-scritch", True, {"sand", "friction"}),
    "stone": FrictionThing("stone", "stone steps", "the stone steps", "squeak-squeak", True, {"stone", "friction"}),
    "rope": FrictionThing("rope", "a rope ladder", "the rope ladder", "rrrrip", True, {"rope", "friction"}),
}

VALUES = {
    "honesty": ValueChoice(
        "honesty",
        "honesty",
        "tell the truth",
        "say what happened right away",
        {"honesty", "moral"},
    ),
    "sharing": ValueChoice(
        "sharing",
        "sharing",
        "share the snack",
        "hand the snack back and split it fairly",
        {"sharing", "moral"},
    ),
    "respect": ValueChoice(
        "respect",
        "respect",
        "leave the tomb alone",
        "put the shiny thing back where they found it",
        {"respect", "moral"},
    ),
}

SCOUT_NAMES = ["Pip", "Mira", "Ned", "Tia", "Oli", "Bea", "Juno", "Luz"]
ADULT_NAMES = ["Aunt May", "Coach Ren", "Ms. Dot", "Uncle Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FRICTIONS:
            for v in VALUES:
                combos.append((p, f, v))
    return combos


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in SCOUT_NAMES if n != avoid]
    return rng.choice(pool), gender


def reasonableness_check(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.friction not in FRICTIONS:
        raise StoryError("Unknown friction source.")
    if params.value not in VALUES:
        raise StoryError("Unknown moral value.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedic scout-and-tomb story with friction, a moral value, and a small turn."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--friction", choices=FRICTIONS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.friction is None or c[1] == args.friction)
              and (args.value is None or c[2] == args.value)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, friction, value = rng.choice(sorted(combos))
    scout1, g1 = _pick_name(rng)
    scout2, g2 = _pick_name(rng, avoid=scout1)
    adult = rng.choice(ADULT_NAMES)
    return StoryParams(place, friction, value, scout1, g1, scout2, g2, adult)


def predict_stuck(world: World, place: Place, friction: FrictionThing) -> bool:
    sim = world.copy()
    sim.get("cart").meters["stuck"] += 1
    sim.get("cart").meters["friction"] += 1
    return place.has_tomb and friction.slow


def tell(place: Place, friction: FrictionThing, value: ValueChoice, s1: Entity, s2: Entity, adult: Entity) -> World:
    world = World()
    scout = world.add(Entity(s1.id, "character", s1.type, role="scout", traits=["curious"]))
    scout2 = world.add(Entity(s2.id, "character", s2.type, role="scout", traits=["careful"]))
    guide = world.add(Entity(adult.id, "character", "adult", role="adult"))
    tomb = world.add(Entity("tomb", "thing", "tomb", label=place.label))
    cart = world.add(Entity("cart", "thing", "cart", label="a narrow trolley"))
    key = world.add(Entity("key", "thing", "key", label="a shiny key"))

    world.facts.update(place=place, friction=friction, value=value, scout=scout, scout2=scout2, adult=guide, tomb=tomb, cart=cart, key=key)

    scout.memes["brave"] += 1
    scout2.memes["wonder"] += 1
    world.say(f"{scout.id} and {scout2.id} arrived with a scout flag and a very serious map, right at {place.label}.")
    world.say(f"Their flashlight shone on the {tomb.label_word if hasattr(tomb, 'label_word') else 'tomb'}, and the place echoed like a joke waiting to happen.")
    world.say(f"{scout2.id} whispered, \"I heard the tomb is full of echoes and old secrets.\"")

    world.para()
    world.say(f"{scout.id} tried to push the cart across {friction.surface}, but the {friction.label} made {friction.sound} noises and the cart barely moved.")
    cart.meters["friction"] += 1
    if predict_stuck(world, place, friction):
        world.say(f"{scout2.id} pointed and laughed. \"The cart has decided to become a statue!\"")
        world.say(f"Then everyone noticed the shiny key near the tomb door, and the day turned into a tiny mystery.")

    world.para()
    if value.id == "honesty":
        world.say(f"{scout.id} admitted, \"I moved the cart because I wanted to be the hero.\"")
        world.say(f"{guide.label_word.capitalize()} smiled. \"Thanks for telling the truth. That is how a real scout keeps trust.\"")
    elif value.id == "sharing":
        world.say(f"{scout.id} admitted, \"I grabbed the snack first.\"")
        world.say(f"{guide.label_word.capitalize()} said, \"Good catch. A fair scout shares before the grumpiness grows.\"")
    else:
        world.say(f"{scout.id} admitted, \"I picked up the shiny thing from the tomb floor.\"")
        world.say(f"{guide.label_word.capitalize()} said, \"Good thing you said so. Respect means putting treasures back where they belong.\"")

    scout.memes["relief"] += 1
    scout2.memes["joy"] += 1
    guide.memes["pride"] += 1

    world.para()
    if value.id == "honesty":
        world.say(f"With the truth out, {guide.id} showed them how to tilt the cart and use a cloth under the wheel, so the friction could not win.")
        world.say(f"{scout.id} and {scout2.id} pushed together, and this time the cart rolled with a happy little wobble.")
    elif value.id == "sharing":
        world.say(f"{guide.id} cut the snack in half and handed each scout a piece, so nobody had to sulk in the tomb's silly echo chamber.")
        world.say(f"They left the cart where it was and used the lighter box of supplies instead.")
    else:
        world.say(f"{guide.id} returned the key to its hook beside the tomb door, then helped the scouts mark the spot on the map.")
        world.say(f"The three of them left the tomb with the key safe, the joke told, and the map a little tidier than before.")

    world.facts.update(outcome="solved", moral=value.id)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    friction: FrictionThing = f["friction"]
    value: ValueChoice = f["value"]
    return [
        f'Write a funny story for a young child that includes the words "scout", "{friction.id}", and "tomb".',
        f"Tell a comedy about two scouts who get stuck by {friction.label} inside {place.label} and then learn to {value.label}.",
        f"Write a warm story where a scout team in a tomb has a silly problem, tells the truth, and ends with a good moral.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    friction: FrictionThing = f["friction"]
    value: ValueChoice = f["value"]
    s1: Entity = f["scout"]
    s2: Entity = f["scout2"]
    adult: Entity = f["adult"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {s1.id} and {s2.id}, two scouts who went into {place.label} with {adult.id}. The tomb setting makes their little problem feel grand, but the comedy keeps it light.",
        ),
        QAItem(
            question="What went wrong in the tomb?",
            answer=f"The cart got stuck on {friction.label}, and that friction made it move like a grumpy snail. The scouts had to pause, laugh, and find a smarter way forward.",
        ),
        QAItem(
            question=f"What moral did the scouts learn?",
            answer=f"They learned to {value.sentence}. That mattered because telling the truth let {adult.id} help them fix the problem instead of guessing.",
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friction?",
            answer="Friction is the rubbing force that makes things slow down, stick, or squeak when they move across a surface.",
        ),
        QAItem(
            question="What is a scout?",
            answer="A scout is someone who explores, notices details, and works as part of a team.",
        ),
        QAItem(
            question="What is a tomb?",
            answer="A tomb is a place built to hold something important from long ago, so people treat it carefully and respectfully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sandstone", "sand", "honesty", "Pip", "boy", "Mira", "girl", "Ms. Dot"),
    StoryParams("hill", "stone", "respect", "Tia", "girl", "Ned", "boy", "Aunt May"),
    StoryParams("museum", "rope", "sharing", "Oli", "boy", "Luz", "girl", "Coach Ren"),
]


ASP_RULES = r"""
frictional(F) :- friction(F).
moral(V) :- value(V).

stuck(cart) :- chosen_friction(F), slow(F).
comic_turn :- stuck(cart), chosen_value(V), moral(V).

allowed(P, F, V) :- place(P), friction(F), value(V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f in FRICTIONS:
        lines.append(asp.fact("friction", f))
    for v in VALUES:
        lines.append(asp.fact("value", v))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program(show="#show allowed/3."))
    return sorted(set(asp.atoms(model, "allowed")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos parity.")
        if py - clingo:
            print("  only in python:", sorted(py - clingo))
        if clingo - py:
            print("  only in clingo:", sorted(clingo - py))
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, friction=None, value=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as e:
        print(f"FAILED: generation smoke test crashed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        FRICTIONS[params.friction],
        VALUES[params.value],
        Entity(params.scout1, "character", params.scout1_gender),
        Entity(params.scout2, "character", params.scout2_gender),
        Entity(params.adult, "character", "adult", label=params.adult, role="adult"),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show allowed/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if args.all:
            p = sample.params
            header = f"### {p.scout1} & {p.scout2}: {p.place}, {p.friction}, {p.value}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
