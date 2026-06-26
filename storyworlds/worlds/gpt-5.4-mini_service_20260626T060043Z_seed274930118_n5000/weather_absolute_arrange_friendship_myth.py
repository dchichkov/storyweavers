#!/usr/bin/env python3
"""
storyworlds/worlds/weather_absolute_arrange_friendship_myth.py
==============================================================

A small mythic story world about a friendship that must arrange a changing
weather-sign. The story is driven by state: a bond grows, a sign is read, the
sky turns absolute in its demand, and the friends arrange a response that keeps
their friendship intact.

Seed words: weather, absolute, arrange
Style: Myth
Feature: Friendship
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


ABSOLUTE_LIMIT = 1.0
WEATHER_KINDS = {"clear", "wind", "rain", "storm", "snow", "fog"}
MOOD_KINDS = {"trust", "worry", "fear", "hope", "joy"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess"}
        male = {"boy", "man", "father", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class WeatherSign:
    id: str
    label: str
    kind: str
    omen: str
    stormy: bool = False
    kindly: bool = False


@dataclass
class Arrangement:
    id: str
    label: str
    verb: str
    result: str
    calms: bool = True


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.sign: Optional[WeatherSign] = None
        self.arrangement: Optional[Arrangement] = None
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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.sign = _copy.deepcopy(self.sign)
        clone.arrangement = _copy.deepcopy(self.arrangement)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_weather_turn(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("friend1")
    if not hero or not world.sign:
        return out
    if hero.memes.get("worry", 0.0) < ABSOLUTE_LIMIT:
        return out
    sig = ("weather_turn", world.sign.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.sign.kind == "storm":
        hero.meters["rain"] = hero.meters.get("rain", 0.0) + 1
        out.append("The sky answered with storm-water.")
    elif world.sign.kind == "snow":
        hero.meters["snow"] = hero.meters.get("snow", 0.0) + 1
        out.append("The sky answered with snow.")
    else:
        hero.meters["wind"] = hero.meters.get("wind", 0.0) + 1
        out.append("The sky answered with a hard wind.")
    return out


def _r_arrange_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("friend1")
    friend = world.entities.get("friend2")
    if not hero or not friend or not world.arrangement:
        return out
    sig = ("arrange", world.arrangement.id)
    if sig in world.fired:
        return out
    if hero.memes.get("trust", 0.0) < ABSOLUTE_LIMIT or friend.memes.get("trust", 0.0) < ABSOLUTE_LIMIT:
        return out
    world.fired.add(sig)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    friend.memes["hope"] = friend.memes.get("hope", 0.0) + 1
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    out.append("They arranged a gentler way, and the fear left their hands.")
    return out


CAUSAL_RULES = [
    _r_weather_turn,
    _r_arrange_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(world: World, sign: WeatherSign, arrangement: Arrangement, hero_name: str, friend_name: str) -> World:
    world.sign = sign
    world.arrangement = arrangement
    hero = world.add(Entity(id="friend1", kind="character", type="woman", label=hero_name))
    friend = world.add(Entity(id="friend2", kind="character", type="man", label=friend_name))

    hero.memes["trust"] = 1
    friend.memes["trust"] = 1
    hero.memes["worry"] = 1 if sign.stormy else 0.5
    friend.memes["worry"] = 1 if sign.stormy else 0.5

    world.say(f"Long ago, {hero.label} and {friend.label} were bound by friendship.")
    world.say(f"They watched the {sign.label}, and it promised {sign.omen}.")
    world.say(
        f"{hero.label} said the weather felt absolute, as if it would not yield."
        f" {friend.label} answered that they could still arrange a wise response."
    )

    world.para()
    if sign.stormy:
        world.say(f"The {sign.kind} rose over the hills, and the day grew fierce.")
    else:
        world.say(f"The sky stayed bright, yet the sign still felt important.")

    world.say(
        f"They chose to {arrangement.verb}, and that choice became their shared work."
    )
    propagate(world, narrate=True)

    world.para()
    if world.arrangement and hero.memes.get("hope", 0.0) >= ABSOLUTE_LIMIT:
        world.say(
            f"By evening, the {arrangement.result}. {hero.label} and {friend.label} "
            f"walked on together, and their friendship shone brighter than the weather."
        )
    else:
        world.say(
            f"By evening, they were still together, holding to each other until the sky softened."
        )

    world.facts.update(hero=hero, friend=friend, sign=sign, arrangement=arrangement)
    return world


SIGNS = {
    "clear": WeatherSign(
        id="clear",
        label="clear sign",
        kind="clear",
        omen="a calm road",
        kindly=True,
    ),
    "wind": WeatherSign(
        id="wind",
        label="wind sign",
        kind="wind",
        omen="a restless road",
    ),
    "storm": WeatherSign(
        id="storm",
        label="storm sign",
        kind="storm",
        omen="a hard trial",
        stormy=True,
    ),
    "snow": WeatherSign(
        id="snow",
        label="snow sign",
        kind="snow",
        omen="a quiet trial",
        stormy=True,
    ),
    "fog": WeatherSign(
        id="fog",
        label="fog sign",
        kind="fog",
        omen="a hidden path",
    ),
}

ARRANGEMENTS = {
    "shelter": Arrangement(
        id="shelter",
        label="shared shelter",
        verb="build a shelter together",
        result="they had a small shelter against the storm",
    ),
    "song": Arrangement(
        id="song",
        label="wind song",
        verb="sing an old song",
        result="their song steadied the night air",
    ),
    "lantern": Arrangement(
        id="lantern",
        label="lantern path",
        verb="arrange lanterns along the path",
        result="the lanterns made a bright lane through the fog",
    ),
    "harvest": Arrangement(
        id="harvest",
        label="harvest pile",
        verb="gather the fallen branches into a pile",
        result="the ground looked tidier and the storm had less to seize",
    ),
}

HERO_NAMES = ["Ari", "Mina", "Talen", "Sera", "Niko", "Iris"]
FRIEND_NAMES = ["Bram", "Luma", "Cedar", "Orin", "Juno", "Vale"]


@dataclass
class StoryParams:
    sign: str
    arrangement: str
    hero: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SIGNS.values():
        for a in ARRANGEMENTS.values():
            if s.kind == "clear" and a.id == "harvest":
                continue
            combos.append((s.id, a.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic friendship storyworld about weather and arranging a response.")
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--arrangement", choices=ARRANGEMENTS)
    ap.add_argument("--hero")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.sign:
        combos = [c for c in combos if c[0] == args.sign]
    if args.arrangement:
        combos = [c for c in combos if c[1] == args.arrangement]
    if not combos:
        raise StoryError("No valid sign/arrangement combination matches the given options.")
    sign, arrangement = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    return StoryParams(sign=sign, arrangement=arrangement, hero=hero, friend=friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth about friendship, weather, and an {f['arrangement'].label} beneath the {f['sign'].label}.",
        f"Tell a child-friendly myth where {f['hero'].label} and {f['friend'].label} face an absolute weather sign and arrange a wise response.",
        f"Write a simple legendary story that includes the words weather, absolute, and arrange, and ends with friendship holding firm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, sign, arr = f["hero"], f["friend"], f["sign"], f["arrangement"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The two friends were {hero.label} and {friend.label}. They stayed close even when the weather turned hard.",
        ),
        QAItem(
            question=f"What weather sign did they watch?",
            answer=f"They watched the {sign.label}, and it promised {sign.omen}. That made the day feel serious and absolute.",
        ),
        QAItem(
            question=f"What did they arrange together?",
            answer=f"They arranged to {arr.verb}. Their choice helped them meet the weather without losing their friendship.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} and {friend.label} walking on together while their friendship shone brighter than the weather.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is weather?",
            answer="Weather is what the sky and air are doing, like rain, snow, wind, fog, or a clear day.",
        ),
        QAItem(
            question="What does absolute mean?",
            answer="Absolute means complete or total, with nothing left out.",
        ),
        QAItem(
            question="What does arrange mean?",
            answer="Arrange means to put things in order or make a plan so something can happen well.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between friends who help, trust, and stay with one another.",
        ),
    ]


ASP_RULES = r"""
sign(S) :- sign_fact(S).
arrangement(A) :- arrangement_fact(A).
valid(S,A) :- sign(S), arrangement(A), not blocked(S,A).
blocked(clear,harvest).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SIGNS:
        lines.append(asp.fact("sign_fact", sid))
    for aid in ARRANGEMENTS:
        lines.append(asp.fact("arrangement_fact", aid))
    lines.append(asp.fact("blocked", "clear", "harvest"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def generate(params: StoryParams) -> StorySample:
    world = World()
    world.add(Entity(id="friend1", kind="character", type="woman", label=params.hero))
    world.add(Entity(id="friend2", kind="character", type="man", label=params.friend))
    sign = SIGNS[params.sign]
    arrangement = ARRANGEMENTS[params.arrangement]
    tell(world, sign, arrangement, params.hero, params.friend)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    if world.sign:
        lines.append(f"  sign: {world.sign.id}")
    if world.arrangement:
        lines.append(f"  arrangement: {world.arrangement.id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(sign="storm", arrangement="shelter", hero="Ari", friend="Bram"),
    StoryParams(sign="fog", arrangement="lantern", hero="Mina", friend="Luma"),
    StoryParams(sign="wind", arrangement="song", hero="Talen", friend="Orin"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (sign, arrangement) combos:\n")
        for s, a in triples:
            print(f"  {s:8} {a:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.sign} / {p.arrangement}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
