#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/congestion_physics_coal_surprise_happy_ending_transformation.py
================================================================================================

A standalone story world for a heartwarming TinyStories-style tale built from
the seed words:

- congestion
- physics
- coal

The world models a small museum workshop where a blocked hallway causes
congestion, a child learns a simple physics idea, and a surprising fix turns a
messy coal delivery into a happy transformation.

The story shape is intentionally simple:
- setup: a cozy place is busy and blocked
- tension: congestion makes everyone stuck
- turn: a child notices a physics trick
- resolution: the block is transformed into something helpful
- ending image: the place feels warm, calm, and proud

Run it:
    python storyworlds/worlds/gpt-5.4-mini/congestion_physics_coal_surprise_happy_ending_transformation.py
    python storyworlds/worlds/gpt-5.4-mini/congestion_physics_coal_surprise_happy_ending_transformation.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/congestion_physics_coal_surprise_happy_ending_transformation.py --verify
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
    cozy: str
    blocked_spot: str
    is_indoor: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    material: str
    heavy: bool = False
    messy: bool = False
    warm: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class KidPlan:
    id: str
    label: str
    surprise: str
    physics: str
    transformation: str
    ending: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        self.objects: dict[str, ObjectThing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

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
        clone.objects = copy.deepcopy(self.objects)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def congestion_risk(blocker: ObjectThing, place: Place) -> bool:
    return blocker.heavy and blocker.movable and place.is_indoor


def physics_help(blocker: ObjectThing, helper: Entity) -> bool:
    return blocker.material in {"coal", "cart"} and "curious" in helper.traits


def transformable(blocker: ObjectThing) -> bool:
    return blocker.heavy and blocker.messy


def default_resolve(blocker: ObjectThing) -> str:
    return "rolled it onto a ramp"


@dataclass
class Rule:
    name: str
    apply: callable

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_congestion(world: World) -> list[str]:
    out: list[str] = []
    hall = world.facts["place_id"]
    blocker = world.objects["coal_cart"]
    if blocker.meters["blocked"] < THRESHOLD:
        return out
    sig = ("congestion", blocker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["congestion"] += 1
    world.get("helper").memes["worry"] += 1
    world.get("adult").memes["patience"] += 1
    out.append(f"The {hall} grew crowded, and everyone had to slow down.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["idea"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("helper").memes["hope"] += 1
    out.append("__idea__")
    return out


CAUSAL_RULES = [Rule("congestion", _r_congestion), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _block(world: World, blocker: ObjectThing) -> None:
    blocker.meters["blocked"] += 1
    propagate(world, narrate=False)


def predict_transform(world: World) -> dict:
    sim = world.copy()
    sim.get("helper").memes["idea"] += 1
    _block(sim, sim.objects["coal_cart"])
    return {
        "congestion": sim.get("room").meters["congestion"],
        "idea": sim.get("helper").memes["idea"],
    }


def setup(world: World, place: Place, child: Entity, adult: Entity, blocker: ObjectThing) -> None:
    child.memes["joy"] += 1
    adult.memes["care"] += 1
    world.say(
        f"At {place.label}, {child.id} and {adult.label_word} were doing a small job "
        f"together in a cozy morning. The air smelled like dust, tea, and a little coal."
    )
    world.say(
        f"Near {place.blocked_spot}, a {blocker.label} sat in the way and made the hallway feel narrow."
    )


def build_congestion(world: World, child: Entity, blocker: ObjectThing, place: Place) -> None:
    child.memes["anxiety"] += 1
    world.say(
        f"People tried to pass, but the {blocker.label} caused congestion. "
        f"{child.id} looked up at the stuck line and frowned."
    )
    world.say(
        f'"It is all jammed up," {child.id} whispered. "We can hardly move."'
    )


def surprise(world: World, child: Entity, adult: Entity, blocker: ObjectThing) -> None:
    pred = predict_transform(world)
    child.memes["curiosity"] += 1
    child.memes["idea"] += 1
    world.facts["predicted_congestion"] = pred["congestion"]
    world.say(
        f"Then {child.id} spotted something surprising: the {blocker.label} was resting on a slanted board."
    )
    world.say(
        f'"Wait," {child.id} said, "that is physics! If we roll it the right way, it can move without a fight."'
    )


def transform(world: World, child: Entity, adult: Entity, blocker: ObjectThing, place: Place) -> None:
    blocker.meters["blocked"] = 0
    blocker.meters["moved"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} smiled and helped {child.id} guide the coal cart down a ramp."
    )
    world.say(
        f"The heavy cart moved at last, and the block turned into a neat stack of coal beside the stove."
    )


def happy_end(world: World, child: Entity, adult: Entity, place: Place) -> None:
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say("At once, the hallway opened again.")
    world.say(
        f"Now {place.label} felt bright and easy, and the little coal stove gave off a soft warm glow."
    )
    world.say(
        f"{child.id} beamed at {adult.label_word}. " + f'"We fixed it together," {child.id} said, and it felt true.'
    )


def tell(place: Place, plan: KidPlan) -> World:
    world = World()
    child = world.add_entity(Entity(id="Mina", kind="character", type="girl", role="helper", traits=["curious", "kind"]))
    adult = world.add_entity(Entity(id="Grandpa", kind="character", type="man", role="adult", label="grandpa", traits=["patient", "warm"]))
    room = world.add_entity(Entity(id="room", type="room", label=place.label))
    blocker = world.add_object(ObjectThing(id="coal_cart", label="coal cart", phrase="a coal cart", material="coal", heavy=True, messy=True))
    blocker.meters["blocked"] = 1

    world.facts.update(place_id=place.label, place=place, child=child, adult=adult, blocker=blocker, plan=plan)

    setup(world, place, child, adult, blocker)
    world.para()
    build_congestion(world, child, blocker, place)
    world.para()
    surprise(world, child, adult, blocker)
    world.para()
    transform(world, child, adult, blocker, place)
    world.para()
    happy_end(world, child, adult, place)

    world.facts["outcome"] = "happy"
    return world


PLACES = {
    "museum": Place("museum", "the little museum", "cozy benches", "the narrow hallway", True),
    "station": Place("station", "the old station", "warm brick walls", "the ticket hall", True),
    "workshop": Place("workshop", "grandpa's workshop", "bright shelves", "the front path", True),
}

PLANS = {
    "museum": KidPlan("museum", "museum helper", "a surprise in the hallway", "physics", "turning the block into a neat display", "happy"),
    "station": KidPlan("station", "station helper", "a surprise on the ramp", "physics", "rolling the cart into place", "happy"),
    "workshop": KidPlan("workshop", "workshop helper", "a surprise by the stove", "physics", "making a useful corner", "happy"),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str]]:
    return [(pid,) for pid in PLACES]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    return [
        f'Write a heartwarming story set at {place.label} that includes the words "congestion", "physics", and "coal".',
        f"Tell a gentle story where a child notices congestion, learns a bit of physics, and helps with coal.",
        f"Write a story with a surprise, a happy ending, and a transformation from blockage to warmth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = world.facts["place"]
    child = world.facts["child"]
    adult = world.facts["adult"]
    blocker = world.facts["blocker"]
    return [
        QAItem(
            question="What problem was happening in the story?",
            answer=f"The {blocker.label} caused congestion in the hallway, so people had trouble moving through {place.label}.",
        ),
        QAItem(
            question="What surprising thing did the child notice?",
            answer=f"{child.id} noticed that the coal cart was already on a slanted board, which meant physics could help move it safely. That small idea changed the whole problem.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the blockage transformed into a neat stack of coal and the hallway open again. Everyone could move freely, and the place felt warm and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is coal?",
            answer="Coal is a black rock that can be burned for heat. It is heavy and dusty, so people often move it carefully.",
        ),
        QAItem(
            question="What is physics?",
            answer="Physics is about how things move and why they do. It can help people understand ramps, pushes, and balance.",
        ),
        QAItem(
            question="What does congestion mean?",
            answer="Congestion means too many things or people are in one place, so it gets crowded and hard to move.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    for o in world.objects.values():
        lines.append(f"  {o.id}: meters={dict(o.meters)} material={o.material}")
    return "\n".join(lines)


ASP_RULES = r"""
blocked(H) :- coal_cart(H).
congested :- blocked(H).
idea :- curious(kid).
happy_end :- congested, idea.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("coal_cart", "hall"))
    lines.append(asp.fact("curious", "kid"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show congested/0.\n#show happy_end/0."))
    atoms = set(asp.atoms(model, "congested"))
    if not atoms:
        print("MISMATCH: ASP did not derive congestion.")
        return 1
    sample = generate(StoryParams(place="museum"))
    if "congestion" not in sample.story:
        print("MISMATCH: sample story did not render correctly.")
        return 1
    print("OK: verification passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming congestion/physics/coal story world.")
    ap.add_argument("--place", choices=PLACES)
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
    combo = args.place or rng.choice(sorted(PLACES))
    if combo not in PLACES:
        raise StoryError("Unknown place.")
    return StoryParams(place=combo)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = tell(place, PLANS[params.place])
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
        print(asp_program("", "#show congested/0.\n#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("asp mode not expanded in this simple world")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p)) for p in sorted(PLACES)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
