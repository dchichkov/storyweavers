#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about butch, sharing, teamwork, and friendship.

Seed tale:
---
In a small forest village, a sturdy fox named Butch found a bright lantern.
He wanted to keep it for himself, but his friends needed light to cross the dark path.
A squirrel, a rabbit, and Butch worked together, shared the lantern, and reached the moonlit glade.
Butch learned that a warm heart shines brighter when it is shared.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"queen", "princess", "girl", "woman", "mother"}
        male = {"king", "prince", "boy", "man", "father", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit forest"
    twilight: bool = True


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    risk: str
    source: str
    shared_with: list[str] = field(default_factory=list)


@dataclass
class Help:
    id: str
    label: str
    verb: str
    method: str
    fits: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting("the moonlit forest", twilight=True),
    "meadow": Setting("the silver meadow", twilight=False),
    "village": Setting("the little village lane", twilight=False),
}

NEEDS = {
    "lantern": Need(
        id="lantern",
        label="lantern",
        phrase="a bright lantern",
        risk="darkness",
        source="glow",
        shared_with=["path", "friends"],
    ),
    "bread": Need(
        id="bread",
        label="bread",
        phrase="a round loaf of bread",
        risk="hunger",
        source="food",
        shared_with=["friends", "travelers"],
    ),
    "cloak": Need(
        id="cloak",
        label="cloak",
        phrase="a soft traveling cloak",
        risk="cold",
        source="warmth",
        shared_with=["friends"],
    ),
}

HELPS = {
    "lantern": Help(
        id="lantern",
        label="lantern",
        verb="hold the lantern together",
        method="each friend carries a little of the light",
        fits={"lantern"},
    ),
    "bread": Help(
        id="bread",
        label="bread",
        verb="tear the bread into kind pieces",
        method="everyone gets a fair share",
        fits={"bread"},
    ),
    "cloak": Help(
        id="cloak",
        label="cloak",
        verb="wrap the cloak around the group",
        method="the warm cloth covers them all",
        fits={"cloak"},
    ),
}

HEROES = {
    "butch": {"type": "fox", "gender": "male", "traits": ["sturdy", "brave"]},
    "pippa": {"type": "rabbit", "gender": "female", "traits": ["gentle", "quick"]},
    "milo": {"type": "squirrel", "gender": "male", "traits": ["busy", "cheerful"]},
    "luna": {"type": "deer", "gender": "female", "traits": ["kind", "bright"]},
}

NAMES = ["Butch", "Pippa", "Milo", "Luna"]
TRAITS = ["sturdy", "gentle", "brave", "cheerful", "kind", "merry"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    need: str
    helper: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
need_risk(N) :- need(N), risk(N, _).
shared_need(N) :- need(N), shared(N, _).
compatible(H, N) :- help(H), need(N), fits(H, N).
valid_story(S, N, H) :- setting(S), need_risk(N), shared_need(N), compatible(H, N).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("risk", nid, need.risk))
        lines.append(asp.fact("source", nid, need.source))
        for x in need.shared_with:
            lines.append(asp.fact("shared", nid, x))
    for hid, help_ in HELPS.items():
        lines.append(asp.fact("help", hid))
        for x in help_.fits:
            lines.append(asp.fact("fits", hid, x))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, need: str, helper: str) -> bool:
    return need in NEEDS and helper in HELPS and helper == need and setting in SETTINGS

def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, n, h) for s in SETTINGS for n in NEEDS for h in HELPS if valid_combo(s, n, h)]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    hero_info = HEROES[params.hero]
    friend_info = HEROES[params.friend]

    hero = world.add(Entity(
        id=params.hero, kind="character", type=hero_info["type"], label=params.hero,
        meters={"sharing": 0.0, "teamwork": 0.0}, memes={"pride": 1.0, "joy": 1.0}
    ))
    friend = world.add(Entity(
        id=params.friend, kind="character", type=friend_info["type"], label=params.friend,
        meters={"sharing": 0.0, "teamwork": 0.0}, memes={"hope": 1.0, "joy": 1.0}
    ))
    need = world.add(Entity(
        id=params.need, kind="thing", type=params.need, label=NEEDS[params.need].label,
        phrase=NEEDS[params.need].phrase, owner=hero.id, held_by=hero.id
    ))
    help_ = world.add(Entity(
        id=params.helper, kind="thing", type=params.helper, label=HELPS[params.helper].label,
        phrase=HELPS[params.helper].method, owner=hero.id
    ))

    # Act 1
    world.say(
        f"Once upon a time in {world.setting.place}, there lived a {params.trait} fox named Butch."
        if params.hero == "butch"
        else f"Once upon a time in {world.setting.place}, there lived a {params.trait} {hero.type} named {params.hero.capitalize()}."
    )
    world.say(
        f"Butch found {need.phrase} and felt proud, because {need.label} was his alone."
    )
    world.say(
        f"His friend {friend.id.capitalize()} came along and smiled at the shiny {need.label}."
    )

    # Act 2
    world.para()
    hero.memes["pride"] += 1
    world.say(
        f"A hush fell over the path, for the forest had grown dark and the little road needed light."
    )
    world.say(
        f"Butch wanted to keep the {need.label} for himself, but {friend.id.capitalize()} said the way would be safer if they shared it."
    )
    hero.memes["stingy"] = 1.0
    friend.memes["hope"] += 1
    world.say(
        f"Then a second friend joined them, and the three of them looked at one another with thoughtful eyes."
    )

    # Act 3
    world.para()
    if params.helper == "lantern":
        hero.meters["sharing"] += 1
        friend.meters["sharing"] += 1
        hero.meters["teamwork"] += 1
        friend.meters["teamwork"] += 1
        hero.memes["pride"] = 0.0
        hero.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(
            f"Butch took a deep breath and chose to share the lantern."
        )
        world.say(
            f"Together, Butch and {friend.id.capitalize()} held the lantern high while the third friend carried the other side of the little path."
        )
        world.say(
            f"The glow lit the stones, the shadows faded, and the friends reached the moonlit glade without fear."
        )
        world.say(
            f"Butch learned that a bright thing shines best when good friends carry it together."
        )

    world.facts.update(
        hero=hero,
        friend=friend,
        need=need,
        help=help_,
        params=params,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a young child about {f["hero"].id}, sharing, teamwork, and friendship.',
        f"Tell a gentle story where {f['hero'].id.capitalize()} learns to share a {f['need'].label} with friends in {world.setting.place}.",
        f'Write a classic fairy tale that includes the word "butch" and ends with friends working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, need = f["hero"], f["friend"], f["need"]
    return [
        QAItem(
            question=f"Who found the {need.label} in the story?",
            answer=f"Butch found the {need.label} first in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did Butch need help with the {need.label}?",
            answer=f"He needed help because the path was dark, and sharing the light would help everyone get through safely.",
        ),
        QAItem(
            question=f"What did Butch and {friend.id.capitalize()} do at the end?",
            answer=f"They shared the {need.label} and worked together so they could reach the glade safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something with you instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do something they could not do as well alone.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between friends who care about one another and help one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="forest", need="lantern", helper="lantern", hero="butch", friend="milo", trait="sturdy"),
    StoryParams(setting="meadow", need="bread", helper="bread", hero="butch", friend="pippa", trait="kind"),
    StoryParams(setting="village", need="cloak", helper="cloak", hero="butch", friend="luna", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale world about butch, sharing, teamwork, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--helper", choices=HELPS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=HEROES)
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.need and args.helper:
        if not valid_combo(args.setting, args.need, args.helper):
            raise StoryError("Invalid combination: the chosen helper must match the chosen need, and the setting must exist.")
    candidates = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.need is None or c[1] == args.need)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    setting, need, helper = rng.choice(candidates)
    hero = args.hero or "butch"
    friend = args.friend or rng.choice([n for n in HEROES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, need=need, helper=helper, hero=hero, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for s, n, h in combos:
            print(f"  {s:8} {n:8} {h:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero} in {p.setting} with {p.need}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
