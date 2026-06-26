#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/serious_sharing_bad_ending_flashback_animal_story.py
================================================================================================

A small animal-story world about serious sharing, a flashback promise, and a
bad ending that still feels complete.

Premise:
- A small animal character has one important thing: a snack, a blanket, a lamp,
  or another simple resource.
- A friend arrives needing help.
- The hero remembers a promise from a flashback and shares.
- The sharing solves the friend's immediate need, but leaves the hero with less
  than they needed.
- The ending is serious and a little sad: the story closes with a clear image of
  what changed and what was lost.

This script follows the Storyweavers contract:
- self-contained stdlib script
- shared result containers imported eagerly
- ASP helper imported lazily only for ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp supported
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
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    resource: str
    scarce: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpRequest:
    id: str
    label: str
    verb: str
    need: str
    flashback: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    need: str
    request: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def story_line(hero: Entity, friend: Entity, need: Need, req: HelpRequest, setting: Setting) -> str:
    return f"{hero.id} was a serious little {hero.type} who lived near {setting.place}."


def _has_resource(world: World, hero: Entity, need: Need) -> bool:
    return hero.meters.get(need.resource, 0.0) >= THRESHOLD


def _share(world: World, hero: Entity, friend: Entity, need: Need, req: HelpRequest) -> None:
    hero.meters[need.resource] = max(0.0, hero.meters.get(need.resource, 0.0) - 1.0)
    friend.meters[need.resource] = friend.meters.get(need.resource, 0.0) + 1.0
    hero.memes["concern"] = hero.memes.get("concern", 0.0) + 1.0
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    world.say(
        f"{hero.id} gave {friend.id} one {need.label} so {friend.id} could {req.verb}."
    )


def _bad_end(world: World, hero: Entity, need: Need) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0.0) + 1.0
    world.say(
        f"But after the gift, {hero.id} had no {need.label} left."
    )


def _flashback(world: World, hero: Entity, need: Need, req: HelpRequest) -> None:
    world.say(
        f"{hero.id} remembered the day {req.flashback}."
    )


def _resolve(world: World, hero: Entity, friend: Entity, need: Need, req: HelpRequest) -> None:
    if _has_resource(world, hero, need):
        _share(world, hero, friend, need, req)
    else:
        raise StoryError("This story needs a hero who begins with enough to share.")


SETTINGS = {
    "riverbank": Setting(place="the riverbank", afford={"share"}),
    "meadow": Setting(place="the meadow", afford={"share"}),
    "burrow": Setting(place="the burrow", afford={"share"}),
    "oak_tree": Setting(place="the oak tree", afford={"share"}),
}

NEEDS = {
    "berries": Need(
        id="berries",
        label="berries",
        phrase="a small bundle of berries",
        resource="berries",
        tags={"food", "fruit"},
    ),
    "fish": Need(
        id="fish",
        label="fish",
        phrase="one fresh fish",
        resource="fish",
        tags={"food", "water"},
    ),
    "honey": Need(
        id="honey",
        label="honey",
        phrase="a jar of honey",
        resource="honey",
        tags={"food", "sweet"},
    ),
    "sticks": Need(
        id="sticks",
        label="sticks",
        phrase="a neat bundle of sticks",
        resource="sticks",
        tags={"nest", "wood"},
    ),
}

REQUESTS = {
    "repair_nest": HelpRequest(
        id="repair_nest",
        label="repair a nest",
        verb="repair a nest",
        need="sticks",
        flashback="the two of them promised to help each other when storms came",
        consequence="the nest stayed broken anyway",
        tags={"nest", "help"},
    ),
    "feed_chick": HelpRequest(
        id="feed_chick",
        label="feed a chick",
        verb="feed a chick",
        need="berries",
        flashback="the hero had once sworn not to ignore a hungry friend",
        consequence="the chick still cried for more",
        tags={"food", "help"},
    ),
    "warm_friend": HelpRequest(
        id="warm_friend",
        label="warm a cold friend",
        verb="warm a cold friend",
        need="honey",
        flashback="the hero remembered a winter night when a blanket was shared",
        consequence="the cold stayed in the air",
        tags={"cold", "help"},
    ),
}

TRAITS = ["quiet", "careful", "serious", "gentle", "small", "wary"]
GIRLISH = ["Luna", "Mina", "Mira", "Nori", "Tala", "Pippa"]
BOYISH = ["Otto", "Pip", "Bram", "Kito", "Moss", "Ravi"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for need_id in NEEDS:
            for req_id, req in REQUESTS.items():
                if need_id == req.need and "share" in setting.afford:
                    combos.append((place, need_id, req_id))
    return combos


@dataclass
class StoryWorldState:
    world: World
    hero: Entity
    friend: Entity
    need: Need
    request: HelpRequest


def tell(setting: Setting, need: Need, req: HelpRequest, hero_name: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="animal", traits=["little", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type="animal", traits=["small", "hungry"]))
    hero.meters[need.resource] = 1.0
    hero.memes["care"] = 1.0
    world.say(story_line(hero, friend, need, req, setting))
    world.say(
        f"{hero.id} had one {need.label}, and {hero.id} kept it close."
    )
    world.para()
    world.say(
        f"One day at {setting.place}, {friend.id} arrived and asked to {req.verb}."
    )
    _flashback(world, hero, need, req)
    world.say(
        f"So {hero.id} remembered the promise and chose to share."
    )
    _resolve(world, hero, friend, need, req)
    world.para()
    _bad_end(world, hero, need)
    world.say(
        f"{friend.id} went away helped, but {hero.id} sat by {setting.place} with empty paws."
    )
    hero.memes["sadness"] = 1.0
    world.facts = {
        "hero": hero,
        "friend": friend,
        "need": need,
        "request": req,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    need = f["need"]
    req = f["request"]
    setting = f["setting"]
    return [
        f"Write a serious animal story about {hero.id} at {setting.place} who shares {need.label} after a flashback.",
        f"Tell a short story where a small animal remembers a promise and helps a friend, even though the ending is sad.",
        f"Write an animal story with sharing, a flashback, and a bad ending at {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    need = f["need"]
    req = f["request"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What did {hero.id} share with {friend.id} at {place}?",
            answer=f"{hero.id} shared {need.label} so {friend.id} could {req.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember before choosing to help?",
            answer=f"{hero.id} remembered a flashback about a promise: {req.flashback}.",
        ),
        QAItem(
            question=f"Why is the ending bad in this story?",
            answer=f"The ending is bad because after sharing, {hero.id} had no {need.label} left.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to give some of what you have to someone else so they can use it too.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that remembers something that happened before the main part of the story.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when the story finishes in a sad or unfair way, even if something good happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(
            f"{ent.id}: meters={dict(ent.meters)} memes={dict(ent.memes)}"
        )
    return "\n".join(lines)


def explain_rejection(need: Need, req: HelpRequest) -> str:
    return f"(No story: {req.label} requires {need.label}, and this world only supports exact matches.)"


@dataclass
class StoryParamsRegistry:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Serious animal story about sharing, a flashback, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--request", choices=REQUESTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.need and args.request and REQUESTS[args.request].need != args.need:
        raise StoryError(explain_rejection(NEEDS[args.need], REQUESTS[args.request]))
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.need is None or c[1] == args.need) and (args.request is None or c[2] == args.request)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, need_id, req_id = rng.choice(sorted(combos))
    need = NEEDS[need_id]
    req = REQUESTS[req_id]
    hero = args.name or rng.choice(GIRLISH + BOYISH)
    friend = args.friend or rng.choice([n for n in GIRLISH + BOYISH if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, need=need_id, request=req_id, hero=hero, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], NEEDS[params.need], REQUESTS[params.request], params.hero, params.friend, params.trait)
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
need(berries). need(fish). need(honey). need(sticks).
request(repair_nest). request(feed_chick). request(warm_friend).
place(riverbank). place(meadow). place(burrow). place(oak_tree).

matches(repair_nest, sticks).
matches(feed_chick, berries).
matches(warm_friend, honey).

valid(P, N, R) :- place(P), need(N), request(R), matches(R, N).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for n in NEEDS:
        lines.append(asp.fact("need", n))
    for r in REQUESTS:
        lines.append(asp.fact("request", r))
    for rid, req in REQUESTS.items():
        lines.append(asp.fact("matches", rid, req.need))
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
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="meadow", need="berries", request="feed_chick", hero="Luna", friend="Pip", trait="gentle"),
    StoryParams(place="riverbank", need="sticks", request="repair_nest", hero="Moss", friend="Bram", trait="serious"),
    StoryParams(place="burrow", need="honey", request="warm_friend", hero="Tala", friend="Nori", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
