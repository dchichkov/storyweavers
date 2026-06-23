#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035136Z_seed1855084837_n10/occupy_tennis_friendship_happy_ending_fable.py
==========================================================================================================================

A small, fable-style storyworld about friendship, a shared place, and a happy
ending. The story uses the words "occupy" and "tennis" in a child-facing way and
builds a compact simulation around who wants the space, why, and how friends
find a fair solution.

This file is standalone and uses only the standard library plus the shared
storyworld result containers, with an inline ASP twin for parity checks.
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

# Robust path setup: walk upward until we find storyworlds/results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_CUR = _HERE
while True:
    candidate = os.path.join(_CUR, "results.py")
    if os.path.exists(candidate):
        if _CUR not in sys.path:
            sys.path.insert(0, _CUR)
        break
    parent = os.path.dirname(_CUR)
    if parent == _CUR:
        break
    _CUR = parent

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: str = ""
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)
    style: str = "meadow"
    moral: str = "sharing"


@dataclass
class TennisKit:
    id: str
    label: str
    phrase: str
    phrase2: str
    reason: str = "tennis"
    occupies: bool = False


@dataclass
class StoryParams:
    place: str
    desired: str
    hero: str
    friend: str
    hero_type: str
    friend_type: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["warmth"] >= THRESHOLD and friend.memes["warmth"] >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["trust"] += 1
            friend.memes["trust"] += 1
            out.append("__trust__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["share"] >= THRESHOLD or friend.memes["share"] >= THRESHOLD:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.place.affords.add("shared")
            out.append("__shared__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_friendship, _r_share):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_use_tennis(place: Place) -> bool:
    return "tennis" in place.affords


def can_occupy(place: Place) -> bool:
    return "occupy" in place.affords


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        if can_use_tennis(place) and can_occupy(place):
            for desire in ("tennis", "occupy"):
                combos.append((pid, desire))
    return combos


def _setup(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["warmth"] = 1.0
    friend.memes["warmth"] = 1.0
    hero.memes["share"] = 0.0
    friend.memes["share"] = 0.0
    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0


def tell(place: Place, desired: str, hero_name: str, friend_name: str, hero_type: str, friend_type: str, helper: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper, label="the helper", role="helper"))
    net = world.add(Entity(id="net", kind="thing", type="thing", label="the tennis net", phrase="the tennis net"))
    ball = world.add(Entity(id="ball", kind="thing", type="thing", label="a tennis ball", phrase="a tennis ball"))
    bench = world.add(Entity(id="bench", kind="thing", type="thing", label="a bench", phrase="a small bench"))

    _setup(world)
    world.facts["place"] = place
    world.facts["desired"] = desired
    world.facts["helper_ent"] = helper_ent
    world.facts["net"] = net
    world.facts["ball"] = ball
    world.facts["bench"] = bench

    world.say(f"In {place.label}, {hero_name} and {friend_name} met like two bright birds in a fable.")
    world.say(f"Their favorite game was tennis, because the court rang with quick feet, a bouncing ball, and cheerful laughter.")

    world.para()
    if desired == "occupy":
        hero.memes["share"] += 1
        world.say(f"{hero_name} wanted to occupy the court with a blanket and keep it all to {hero.pronoun('object')}self.")
        world.say(f"{friend_name} wanted to play tennis, so {friend_name} frowned and held the ball close.")
    else:
        friend.memes["share"] += 1
        world.say(f"{friend_name} wanted to occupy the court with cones and a towel, while {hero_name} kept thinking about tennis.")
        world.say(f"Their wishes bumped together like two balls at once.")
    world.say(f"{helper_ent.label.capitalize()} watched the quarrel and reminded them that a good field is happiest when it is shared.")

    world.para()
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    propagate(world, narrate=False)
    world.say(f"{hero_name} looked at {friend_name}, then at the court, and remembered that friendship grows when nobody stands alone on the line.")
    world.say(f"So they moved the blanket to {bench.label}, set the {net.label} straight, and agreed to take turns.")

    world.para()
    hero.memes["share"] += 1
    friend.memes["share"] += 1
    propagate(world, narrate=False)
    world.say(f"At last they played tennis together: one served, one returned, and the ball danced back and forth like a happy heartbeat.")
    world.say(f"When the sun slid down, the court was still neat, and their friendship had become the warmest thing in {place.label}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper_ent,
        place=place,
        desired=desired,
        outcome="shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    desired = f["desired"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short fable for a child about friendship at {place.label} that includes the word "tennis".',
        f"Tell a happy ending story where {hero.label} and {friend.label} learn to share {place.label} instead of trying to occupy it alone.",
        f'Write a gentle fable where two friends argue over tennis, then solve it kindly and end together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    desired = f["desired"]
    qas = [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {hero.label} and {friend.label}. They meet in {place.label} and learn to be fair with each other.",
        ),
        QAItem(
            question=f"What did they want to do at {place.label}?",
            answer=f"One of them wanted to {desired} the court, and both of them cared about tennis. That made the little argument start, because they wanted different things in the same place.",
        ),
        QAItem(
            question=f"How did the friends solve their problem?",
            answer="They remembered that friendship is better than winning the whole space. They moved things aside, took turns, and chose to share the court so everyone could play.",
        ),
        QAItem(
            question=f"What was the happy ending?",
            answer=f"They played tennis together by the end, and the court stayed neat. Their friendship felt stronger because they chose kindness over stubbornness.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where players hit a ball back and forth with rackets over a net.",
        ),
        QAItem(
            question="What does it mean to occupy something?",
            answer="To occupy something means to take up a place or use it for a while.",
        ),
        QAItem(
            question="Why is sharing important in friendship?",
            answer="Sharing helps friends take turns, feel respected, and solve small problems without hurting feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(place: Place) -> str:
    return f"(No story: {place.label} needs to support both tennis and occupy so the friends can argue and then share.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld about friendship and a shared tennis court.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--desired", choices=["tennis", "occupy"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["boy", "girl", "fox", "rabbit", "turtle", "hen"], dest="hero_type")
    ap.add_argument("--friend-type", choices=["boy", "girl", "fox", "rabbit", "turtle", "hen"], dest="friend_type")
    ap.add_argument("--helper", choices=["boy", "girl", "fox", "rabbit", "turtle", "hen"])
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
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.desired is None or c[1] == args.desired]
    # The above list comprehension cannot have multiple ifs in this syntax; fix by loop.
    combos = []
    for pid, desire in valid_combos():
        if args.place is not None and pid != args.place:
            continue
        if args.desired is not None and desire != args.desired:
            continue
        combos.append((pid, desire))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, desired = rng.choice(sorted(combos))
    place = PLACES[place_id]
    hero_type = args.hero_type or rng.choice(["boy", "girl", "fox", "rabbit", "turtle", "hen"])
    friend_type = args.friend_type or rng.choice([t for t in ["boy", "girl", "fox", "rabbit", "turtle", "hen"] if t != hero_type])
    hero = args.hero or rng.choice(NAMES.get(hero_type, ["Aria", "Bram", "Cleo", "Dune"]))
    friend = args.friend or rng.choice(NAMES.get(friend_type, ["Ivy", "Milo", "Pip", "Fern"]))
    helper = args.helper or rng.choice(["rabbit", "turtle", "hen", "fox", "boy", "girl"])
    return StoryParams(place=place_id, desired=desired, hero=hero, friend=friend, hero_type=hero_type, friend_type=friend_type, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    place = PLACES[params.place]
    if "tennis" not in place.affords or "occupy" not in place.affords:
        raise StoryError(explain_rejection(place))
    world = tell(place, params.desired, params.hero, params.friend, params.hero_type, params.friend_type, params.helper)
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


ASP_RULES = r"""
valid(P,D) :- place(P), desired(D), supports(P, tennis), supports(P, occupy).
shared :- friendship, fair_turns.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("supports", pid, a))
    lines.append(asp.fact("friendship"))
    lines.append(asp.fact("fair_turns"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        clingo_set = set(asp_valid_combos())
        python_set = set(valid_combos())
        if clingo_set != python_set:
            print("MISMATCH between clingo and python valid_combos()")
            print("only in clingo:", sorted(clingo_set - python_set))
            print("only in python:", sorted(python_set - clingo_set))
            return 1
        sample = generate(resolve_params(argparse.Namespace(place=None, desired=None, hero=None, friend=None, hero_type=None, friend_type=None, helper=None), random.Random(777)))
        if not sample.story or "tennis" not in sample.story.lower():
            print("Smoke test failed.")
            return 1
        print(f"OK: {len(python_set)} combos and smoke test passed.")
        return 0
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1


NAMES = {
    "boy": ["Bram", "Nico", "Owen", "Levi"],
    "girl": ["Aria", "Cleo", "Mira", "Nia"],
    "fox": ["Fenn", "Rook"],
    "rabbit": ["Pip", "Bunny"],
    "turtle": ["Tess", "Toby"],
    "hen": ["Hattie", "Nell"],
}

PLACES = {
    "meadow_court": Place(id="meadow_court", label="the meadow court", affords={"tennis", "occupy"}),
    "river_path": Place(id="river_path", label="the river path", affords={"occupy"}),
    "school_yard": Place(id="school_yard", label="the school yard", affords={"tennis", "occupy"}),
}


CURATED = [
    StoryParams(place="meadow_court", desired="occupy", hero="Aria", friend="Pip", hero_type="girl", friend_type="rabbit", helper="turtle"),
    StoryParams(place="school_yard", desired="tennis", hero="Bram", friend="Nia", hero_type="boy", friend_type="girl", helper="hen"),
    StoryParams(place="meadow_court", desired="tennis", hero="Mira", friend="Tess", hero_type="girl", friend_type="turtle", helper="fox"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, desired) combos:")
        for place, desired in combos:
            print(f"  {place:14} {desired}")
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
