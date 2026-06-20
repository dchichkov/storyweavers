#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/waltz_domain_tiresome_sharing_twist_animal_story.py
===================================================================================

A standalone story world for a tiny animal tale about a shared dance space,
a tiresome muddle, and a twist that turns fuss into a friendlier ending.

Seed words and instruments:
- waltz
- domain
- tiresome
- Sharing
- Twist
- Style: Animal Story

The world models a small animal community in a meadow domain where one animal
wants the dance space to itself, another wants to share, and a small twist in
the situation changes the mood and the ending. The story is state-driven:
physical space and emotional memes change over time and the prose follows that
state instead of swapping nouns into a frozen paragraph.
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
from typing import Callable, Optional

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
        female = {"girl", "mother", "cow", "ewe"}
        male = {"boy", "father", "bull", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    domain_word: str
    stage: str
    floor: str
    has_bandstand: bool = True
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
class Animal:
    id: str
    type: str
    label: str
    dance: str
    sharing_style: str
    domain_role: str
    region: str = "meadow"
    likes_music: bool = True
    sharing: bool = True
    twisty: bool = False
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
class Twist:
    id: str
    label: str
    reveal: str
    effect: str
    resolves_tension: bool = True
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if "host" not in world.entities or "guest" not in world.entities:
        return out
    host = world.get("host")
    guest = world.get("guest")
    if host.memes["grumpy"] < THRESHOLD or guest.memes["hope"] < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    host.memes["stiff"] += 1
    guest.memes["worry"] += 1
    out.append("__tension__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if "twist" not in world.entities:
        return out
    twist = world.get("twist")
    if twist.meters["revealed"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "host" in world.entities:
        world.get("host").memes["surprise"] += 1
    if "guest" in world.entities:
        world.get("guest").memes["relief"] += 1
    out.append("__twist__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if "host" not in world.entities or "guest" not in world.entities:
        return out
    host = world.get("host")
    guest = world.get("guest")
    if host.memes["share"] < THRESHOLD or guest.memes["share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    host.meters["space"] -= 1
    guest.meters["space"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("tension", "social", _r_tension),
    Rule("twist", "social", _r_twist),
    Rule("share", "physical", _r_share),
]


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


def predict_twist(world: World) -> dict:
    sim = world.copy()
    if "twist" in sim.entities:
        sim.get("twist").meters["revealed"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get("guest").meters["space"] > 0 if "guest" in sim.entities else False,
        "relief": sim.get("guest").memes["relief"] if "guest" in sim.entities else 0,
    }


def setup(world: World, host: Entity, guest: Entity, place: Place) -> None:
    host.meters["space"] += 2
    guest.meters["space"] += 1
    host.memes["joy"] += 1
    guest.memes["joy"] += 1
    world.say(
        f"At {place.name}, the animals kept their {place.domain_word} nice and bright. "
        f"The little waltz stage sat on the {place.floor}, and everyone knew it as the best place to dance."
    )
    world.say(
        f"{host.id} loved to waltz there in neat steps, while {guest.id} loved to come near and watch."
    )


def conflict(world: World, host: Entity, guest: Entity) -> None:
    host.memes["grumpy"] += 1
    guest.memes["hope"] += 1
    world.say(
        f"But {host.id} grew tiresome and said the dance ring was only for {host.pronoun('object')}. "
        f"{guest.id} looked down, because the best part of the {host.pronoun('possessive')} day was being shared."
    )


def reveal_twist(world: World, guest: Entity, twist: Twist) -> None:
    guest.meters["listen"] += 1
    twist_ent = world.get("twist")
    twist_ent.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {guest.id} noticed the twist: the wind had carried a whole line of tiny beetles "
        f"onto the grass, and they were marching in a neat circle right beside the stage."
    )
    world.say(
        f'{guest.id} blinked. "{twist.reveal}" {guest.pronoun()} whispered, and the animals all leaned closer.'
    )


def share_the_domain(world: World, host: Entity, guest: Entity, place: Place, twist: Twist) -> None:
    host.memes["share"] += 1
    guest.memes["share"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{guest.id} showed {host.id} how to make room for everyone: one step for the waltz, one step for the beetles, "
        f"and a careful hop so nobody was stepped on."
    )
    world.say(
        f"That changed everything. {host.id} laughed, scooted over, and let {guest.id} take a turn in the middle."
    )
    world.say(
        f"Soon the whole meadow felt less tiresome and more like a song, with {host.id} and {guest.id} sharing the domain of the stage."
    )


def ending(world: World, host: Entity, guest: Entity, place: Place) -> None:
    host.memes["joy"] += 1
    guest.memes["joy"] += 1
    world.say(
        f"By sunset, {host.id} was waltzing again, and {guest.id} was beside {host.pronoun('object')}, smiling in the warm grass."
    )
    world.say(
        f"The beetles marched safely under the clover, the stage stayed tidy, and the little animal domain sounded happy at last."
    )


def tell(place: Place, host_cfg: Animal, guest_cfg: Animal, twist_cfg: Twist) -> World:
    world = World()
    host = world.add(Entity(id=host_cfg.id, kind="character", type=host_cfg.type, label=host_cfg.label, role="host"))
    guest = world.add(Entity(id=guest_cfg.id, kind="character", type=guest_cfg.type, label=guest_cfg.label, role="guest"))
    twist = world.add(Entity(id=twist_cfg.id, kind="thing", type="twist", label=twist_cfg.label))

    setup(world, host, guest, place)
    world.para()
    conflict(world, host, guest)
    world.para()
    reveal_twist(world, guest, twist_cfg)
    world.para()
    share_the_domain(world, host, guest, place, twist_cfg)
    world.para()
    ending(world, host, guest, place)

    world.facts.update(
        place=place,
        host=host,
        guest=guest,
        twist=twist_cfg,
        shared=True,
        tired=host.memes["grumpy"] >= THRESHOLD,
        revealed=twist.meters["revealed"] >= THRESHOLD,
    )
    return world


PLACES = {
    "meadow": Place("meadow", "the meadow domain", "domain", "waltz stage", "soft grass", True, {"meadow", "domain"}),
    "orchard": Place("orchard", "the orchard domain", "domain", "waltz circle", "clover dust", True, {"orchard", "domain"}),
    "riverbank": Place("riverbank", "the riverbank domain", "domain", "waltz patch", "flat stones", True, {"riverbank", "domain"}),
}

ANIMALS = {
    "rabbit": Animal("Pip", "rabbit", "a rabbit", "waltz", "sharing", "host", tags={"rabbit", "sharing"}),
    "fox": Animal("Fenn", "fox", "a fox", "waltz", "sharing", "guest", tags={"fox", "sharing"}),
    "deer": Animal("Dina", "deer", "a deer", "waltz", "sharing", "guest", tags={"deer", "sharing"}),
    "bear": Animal("Milo", "bear", "a bear", "waltz", "sharing", "host", tags={"bear", "sharing"}),
}

TWISTS = {
    "beetles": Twist("beetles", "beetles", "Oh! We can share the stage.", "The tiny beetles make a second circle beside the dancers.", True, {"twist", "beetles"}),
    "drum": Twist("drum", "drum", "Oh! We can dance to the beat.", "A grasshopper is tapping a tiny drum from a mushroom stump.", True, {"twist", "drum"}),
    "rainbow": Twist("rainbow", "rainbow", "Oh! The whole domain can join in.", "A bright rainbow has appeared over the meadow, and everyone wants a turn.", True, {"twist", "rainbow"}),
}


@dataclass
class StoryParams:
    place: str
    host: str
    guest: str
    twist: str
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

CURATED = [
    dataclass(type("StoryParams", (), {}))
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for h in ANIMALS:
            for g in ANIMALS:
                if h != g:
                    combos.append((p, h, g))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story that includes the words "waltz", "domain", and "tiresome".',
        f"Tell a gentle story where {f['host'].id} wants the little waltz domain, but {f['guest'].id} helps by sharing it.",
        f"Write a story with a twist that turns a tiresome argument into sharing and dancing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    guest = f["guest"]
    place = f["place"]
    twist = f["twist"]
    return [
        ("Who are the story's animals?",
         f"It is about {host.id} and {guest.id}, two animals in a small meadow story."),
        ("Why was the middle of the story tiresome?",
         f"{host.id} wanted the waltz stage for {host.pronoun('object')}, so {guest.id} felt left out. That made the sharing problem feel tiresome until the twist appeared."),
        ("What was the twist?",
         f"The twist was that tiny beetles were marching in a circle near the stage. Their little parade showed a new way to share the domain, and it changed the mood fast."),
        ("How did the story end?",
         f"It ended with {host.id} and {guest.id} sharing the {place.name} and waltzing happily together. The domain felt friendly instead of cramped."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a waltz?",
         "A waltz is a gentle dance with smooth turning steps. Dancers move in a flowing pattern together."),
        ("What does domain mean here?",
         "Here, a domain means a place that belongs to a group or animal, like the meadow where they play. It is the area they care for and use."),
        ("What does sharing mean?",
         "Sharing means letting someone else use or enjoy something too. It helps a group stay kind and fair."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about waltz, domain, tiresome, sharing, and twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--host", choices=ANIMALS)
    ap.add_argument("--guest", choices=ANIMALS)
    ap.add_argument("--twist", choices=TWISTS)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    if args.host and args.guest and args.host == args.guest:
        raise StoryError("The host and guest must be different animals.")
    place = args.place or rng.choice(sorted(PLACES))
    host = args.host or rng.choice(sorted(ANIMALS))
    guest = args.guest or rng.choice(sorted([k for k in ANIMALS if k != host]))
    twist = args.twist or rng.choice(sorted(TWISTS))
    return StoryParams(place, host, guest, twist)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ANIMALS[params.host], ANIMALS[params.guest], TWISTS[params.twist])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
share_story(P,H,G) :- place(P), host(H), guest(G), H != G.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("host", a))
        lines.append(asp.fact("guest", a))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show share_story/3."))
    return sorted(set(asp.atoms(model, "share_story")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set((p, h, g) for p, h, g in valid_combos()) else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show share_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(p, h, g, t)) for p, h, g in valid_combos()[:5] for t in list(TWISTS)[:1]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
