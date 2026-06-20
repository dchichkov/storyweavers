#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/departure_summary_roam_twist_sharing_fable.py
=============================================================================

A small fable-style story world about a creature's roam, a twist, and a shared
solution after a departure. The domain is intentionally tiny: a few characters,
a path, a found item, a decision to share, and a final summary that closes the
tale with a clear change in the world.

The seed words are woven into the story and the Q&A:
- departure
- summary
- roam

Style: fable
Features: Twist, Sharing
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Trail:
    id: str
    place: str
    winding: str
    roaming: str
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
class Find:
    id: str
    label: str
    phrase: str
    good_for: str
    can_share: bool = True
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
    reveal: str
    reason: str
    resolution: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    giver = world.entities.get("Friend")
    seeker = world.entities.get("Hero")
    if not giver or not seeker:
        return out
    if seeker.meters["hungry"] < THRESHOLD:
        return out
    if giver.meters["kindness"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["relief"] += 1
    giver.memes["joy"] += 1
    out.append("__share__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _r_share(world):
            changed = True
            if s != "__share__":
                produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def roam(world: World, hero: Entity, trail: Trail) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["distance"] += 1
    world.say(
        f"On a bright morning, {hero.id} went to {trail.place} to {trail.roaming}. "
        f"The path was {trail.winding}, and the little traveler felt brave enough to roam."
    )


def meet_friend(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["hope"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"There {hero.id} met {friend.id}, a gentle {friend.type} who liked quiet help and kind words."
    )


def find_item(world: World, hero: Entity, item: Find) -> None:
    hero.meters["surprise"] += 1
    world.say(
        f"Near the old stone bench, {hero.id} found {item.phrase}. "
        f"It seemed perfect for {item.good_for}."
    )


def twist(world: World, hero: Entity, friend: Entity, item: Find, twist_cfg: Twist) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Then came the twist: {twist_cfg.reveal}. {twist_cfg.reason}."
    )
    world.say(
        f"{hero.id} had wanted to keep it all, but {friend.id} looked at it with gentle eyes."
    )


def share(world: World, hero: Entity, friend: Entity, item: Find) -> None:
    hero.memes["generosity"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'"Let us share it," said {hero.id}. So {hero.id} and {friend.id} split {item.phrase} between them.'
    )
    world.say(
        f"That choice made the day feel lighter, and both children walked on with happier hearts."
    )


def departure(world: World, hero: Entity, friend: Entity, trail: Trail) -> None:
    friend.meters["departed"] += 1
    world.say(
        f"At sunset came a small departure: {friend.id} had to go home before the stars came out."
    )
    world.say(
        f"{hero.id} watched {friend.pronoun('object')} leave down {trail.place}, but the shared kindness stayed behind."
    )


def summary(world: World, hero: Entity, friend: Entity, item: Find) -> None:
    world.say(
        f"Summary: {hero.id} went roaming, found something useful, faced a twist, and chose sharing."
    )
    world.say(
        f"In the end, {hero.id} kept a warm memory, {friend.id} kept a happy promise, and {item.label} became a sign of friendship."
    )


def tell(trail: Trail, item: Find, twist_cfg: Twist, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    hero.memes["curiosity"] = 1.0
    friend.memes["kindness"] = 1.0
    find_item(world, hero, item)
    world.para()
    roam(world, hero, trail)
    meet_friend(world, hero, friend)
    twist(world, hero, friend, item, twist_cfg)
    world.para()
    share(world, hero, friend, item)
    propagate(world, narrate=False)
    world.para()
    departure(world, hero, friend, trail)
    summary(world, hero, friend, item)
    world.facts.update(hero=hero, friend=friend, trail=trail, item=item, twist=twist_cfg)
    return world


TRAILS = {
    "meadow": Trail("meadow", "the meadow", "soft and winding", "wander and roam", {"roam"}),
    "river": Trail("river", "the river path", "curving under willow trees", "wander and roam", {"roam"}),
    "orchard": Trail("orchard", "the orchard lane", "narrow between apple trees", "roam and explore", {"roam"}),
}

FINDS = {
    "bread": Find("bread", "a little loaf of bread", "a little loaf of bread", "share with a hungry friend", True, {"sharing"}),
    "apples": Find("apples", "a basket of red apples", "a basket of red apples", "share with a hungry friend", True, {"sharing"}),
    "jam": Find("jam", "a jar of berry jam", "a jar of berry jam", "share at a picnic", True, {"sharing"}),
}

TWISTS = {
    "hungry_friend": Twist("hungry_friend", "the friend was hungry too", "The treasure was not only a prize; it was a needed lunch.", "The best choice was to share it." , {"twist"}),
    "lost_basket": Twist("lost_basket", "the basket had fallen from a cart", "It had been dropped by someone in a hurry.", "Returning part of it was the kind thing to do.", {"twist"}),
    "half_hidden": Twist("half_hidden", "half of it was hidden under leaves", "The day was not as simple as it first looked.", "Sharing made the little surprise feel bigger.", {"twist"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Tess", "Nora", "Elia"]
BOY_NAMES = ["Noel", "Finn", "Bram", "Otto", "Eli", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TRAILS:
        for f in FINDS:
            for w in TWISTS:
                combos.append((t, f, w))
    return combos


@dataclass
@dataclass
class StoryParams:
    trail: str
    find: str
    twist: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
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


KNOWLEDGE = {
    "roam": [("What does roam mean?",
              "To roam means to walk around in a free, wandering way without a strict plan.")],
    "sharing": [("Why is sharing nice?",
                 "Sharing is nice because it lets more than one person enjoy something, and it shows care.")],
    "departure": [("What is a departure?",
                    "A departure is when someone leaves a place and goes away for a while.")],
    "twist": [("What is a twist in a story?",
                "A twist is a surprise that changes how the reader understands what is happening.")],
    "fable": [("What is a fable?",
               "A fable is a short story that teaches a lesson, often with simple animals or people.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story that includes the words "roam", "twist", "sharing", and "departure".',
        f"Tell a small moral story about {f['hero'].id} and {f['friend'].id} that begins with roaming, turns with a twist, and ends with sharing.",
        f"Write a child-friendly fable with a final summary sentence that shows how sharing changed the ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, item = f["hero"], f["friend"], f["item"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two little travelers in a fable about kindness."),
        ("What did {0} do at the start?".format(hero.id),
         f"{hero.id} went to {f['trail'].place} to roam and explore the path."),
        ("What was the twist?",
         f"The twist was that {f['twist'].reveal.lower()}, so what looked like a prize was also a need."),
        ("How did they solve the problem?",
         f"They chose sharing. They split {item.phrase} between them, so both could enjoy it."),
        ("What happened at the end?",
         f"There was a departure when {friend.id} went home, and the story ended with a summary of roaming, twist, and sharing."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["trail"].tags) | set(world.facts["item"].tags) | set(world.facts["twist"].tags)
    out: list[tuple[str, str]] = []
    for key, qas in KNOWLEDGE.items():
        if key in tags:
            out.extend(qas)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "bread", "hungry_friend", "Pip", "boy", "Mina", "girl"),
    StoryParams("river", "apples", "lost_basket", "Lina", "girl", "Otto", "boy"),
    StoryParams("orchard", "jam", "half_hidden", "Bram", "boy", "Ivy", "girl"),
]


def explain_rejection() -> str:
    return "(No story: this world only tells fables where roaming leads to a real twist and a shared ending.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    trail, find, twist = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    friend_type = "girl" if hero_type == "boy" else "boy"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    if friend == hero:
        friend = (friend + "a") if friend.endswith("a") else (friend + "y")
    return StoryParams(trail, find, twist, hero, hero_type, friend, friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(TRAILS[params.trail], FINDS[params.find], TWISTS[params.twist],
                 params.hero, params.hero_type, params.friend, params.friend_type)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about roaming, a twist, sharing, and departure.")
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--friend")
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


ASP_RULES = r"""
valid(T,F,W) :- trail(T), find(F), twist(W).
shared :- find(F), can_share(F).
ending_ok :- shared.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in TRAILS:
        lines.append(asp.fact("trail", t))
    for f in FINDS:
        lines.append(asp.fact("find", f))
        lines.append(asp.fact("can_share", f))
    for w in TWISTS:
        lines.append(asp.fact("twist", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        print("MISMATCH in valid combos:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
        rc = 1
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for t, f, w in combos:
            print(f"  {t} {f} {w}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
