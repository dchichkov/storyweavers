#!/usr/bin/env python3
"""
A small fable world about a misunderstanding on a swollen path.

Seed premise:
A traveler tromps toward a crossing, sees a swollen river, and misunderstands
a warning. A wise helper explains what is actually happening, and the traveler
is fortunate to avoid a bad choice.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "badger", "hound", "horse", "donkey", "crow", "owl"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str = "path"
    affords: set[str] = field(default_factory=set)
    features: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    sound: str
    muck: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class WarningSign:
    id: str
    label: str
    phrase: str
    tells: str
    signals: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    sign: str
    hero: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "lane": Place(name="the forest lane", affords={"tromp"}, features={"trees", "mud"}),
    "bridge": Place(name="the old bridge", affords={"tromp"}, features={"water", "planks"}),
    "bank": Place(name="the river bank", affords={"tromp"}, features={"water", "reeds"}),
}

ACTIONS = {
    "tromp": Action(
        id="tromp",
        verb="tromp across the lane",
        gerund="tromping along the path",
        sound="thump-thump",
        muck="splash",
        zone={"feet"},
        keyword="tromp",
        tags={"tromp", "path"},
    ),
    "cross": Action(
        id="cross",
        verb="cross the bridge",
        gerund="crossing the bridge",
        sound="tap-tap",
        muck="slip",
        zone={"feet"},
        keyword="bridge",
        tags={"bridge"},
    ),
}

SIGNS = {
    "swollen": WarningSign(
        id="swollen",
        label="a swollen river",
        phrase="the river was swollen and quick",
        tells="the water is too full and swift for safe crossing",
        signals={"swollen", "water", "danger"},
    ),
    "mossy": WarningSign(
        id="mossy",
        label="a mossy stone",
        phrase="the stone was mossy and slick",
        tells="the path may be slippery",
        signals={"mossy", "slippery"},
    ),
}

HEROES = {
    "fox": "fox",
    "badger": "badger",
    "crow": "crow",
    "hare": "hare",
    "owl": "owl",
}

HELPERS = {
    "owl": "owl",
    "crow": "crow",
    "badger": "badger",
    "fox": "fox",
}

NAMES = {
    "fox": ["Fenn", "Sable", "Rusty"],
    "badger": ["Bram", "Nell", "Moss"],
    "crow": ["Corin", "Iris", "Pip"],
    "hare": ["Thistle", "Jun", "Puff"],
    "owl": ["Oren", "Wren", "Hush"],
}


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def _threat(world: World) -> bool:
    return world.facts["sign"].id == "swollen" and world.facts["action"].id in {"tromp", "cross"}


def _resolution_text(hero: Entity, helper: Entity, sign: WarningSign, action: Action) -> str:
    return (
        f"{helper.id} explained that {sign.label} meant the way was unsafe. "
        f"{hero.id} listened, and {hero.pronoun()} was fortunate to stop before trouble came."
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    sign = SIGNS[params.sign]
    hero_kind = params.hero
    helper_kind = params.helper

    world = World(place)
    hero_name = random.choice(NAMES[hero_kind])
    helper_name = random.choice(NAMES[helper_kind])

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, label=hero_kind))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_kind, label=helper_kind))
    river = world.add(Entity(id="river", kind="thing", type="river", label="river", phrase=sign.phrase))

    world.facts.update(hero=hero, helper=helper, river=river, action=action, sign=sign, place=place)

    hero.memes["curiosity"] = 1.0
    hero.memes["hope"] = 1.0

    world.say(
        f"Once, a little {hero.kind} named {hero.id} set out along {place.name}."
    )
    world.say(
        f"{hero.id} liked to {action.verb}, and {hero.pronoun()} did it with a cheerful {action.sound}."
    )
    world.say(
        f"At the crossing, {hero.id} saw {sign.label}; {sign.phrase}."
    )

    world.para()
    hero.memes["misunderstanding"] = 1.0
    hero.meters["distance"] = 1.0
    world.say(
        f"{hero.id} misunderstood the sight and thought it was only a sign to hurry faster."
    )
    world.say(
        f"{hero.id} tried to keep {hero.pronoun('possessive')} pace and tromp on."
    )

    world.para()
    helper.memes["concern"] = 1.0
    if _threat(world):
        world.say(
            f"{helper.id} called out, \"Wait! {sign.tells}.\""
        )
        world.say(
            _resolution_text(hero, helper, sign, action)
        )
        hero.memes["relief"] = 1.0
        hero.memes["wise"] = 1.0
        hero.meters["distance"] = 0.0
        world.say(
            f"So {hero.id} stayed on the safe bank, and the day ended well."
        )
    else:
        world.say(f"{helper.id} smiled, and the path stayed easy.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a character who wants to {f["action"].verb} but notices {f["sign"].label}.',
        f'Write a child-friendly story that includes the words "tromp", "fortuitous", and "swollen" and ends with a lesson.',
        f'Tell a fable about a misunderstanding on {f["place"].name} and a wise warning that keeps someone safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    action = f["action"]
    sign = f["sign"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on {world.place.name}?",
            answer=f"{hero.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} misunderstand at the crossing?",
            answer=f"{hero.id} misunderstood {sign.label} and thought it meant to hurry instead of stop.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the end?",
            answer=f"{helper.id} helped by explaining that {sign.tells}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} listened, stayed safe, and was fortunate to avoid trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does swollen mean?",
            answer="Swollen means bigger than usual because it has filled up with water or air.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the meaning wrong and acts on the wrong idea.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
action(A) :- act(A).
sign(S) :- warning(S).

misunderstanding(H) :- hero(H), sees(H,S), sign(S).
fortunate(H) :- hero(H), misunderstanding(H), helper(He), warns(He,S), sign(S).

resolved :- fortunate(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("act", aid))
    for sid in SIGNS:
        lines.append(asp.fact("warning", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    action = args.action or rng.choice(list(ACTIONS))
    sign = args.sign or "swollen"
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    if helper == hero:
        helper = "owl" if hero != "owl" else "crow"
    return StoryParams(place=place, action=action, sign=sign, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/0."))
    if model is None:
        print("ASP unavailable or no model.")
        return 1
    print("OK: ASP program parsed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(seed)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="bridge", action="cross", sign="swollen", hero="fox", helper="owl"),
            StoryParams(place="lane", action="tromp", sign="swollen", hero="hare", helper="badger"),
            StoryParams(place="bank", action="cross", sign="swollen", hero="crow", helper="owl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(seed + i))
            p.seed = seed + i
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

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
