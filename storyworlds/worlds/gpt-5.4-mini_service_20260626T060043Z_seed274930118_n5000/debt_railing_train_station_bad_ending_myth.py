#!/usr/bin/env python3
"""
storyworlds/worlds/debt_railing_train_station_bad_ending_myth.py
===============================================================

A standalone story world about debt, a railing, a train station, and a
myth-shaped bad ending.

Seed tale premise:
---
At the old train station, a small traveler once borrowed a silver ticket-pin
from the station spirit so he could ride the midnight train. The spirit said
the pin was a debt, and it must be returned before the last bell. The traveler
kept delaying, then tried to lean over the railing and catch the train by luck
instead of paying what he owed.

The railing shook. The bell rang. The train left without him.

This world models that premise as a small, state-driven myth:
- debt grows when the traveler borrows and refuses to repay
- the railing is a risky threshold between waiting and leaving
- the station spirit will warn, then demand, then remember
- the bad ending is that the traveler loses the train and carries the debt away

The narration is intentionally mythic: the station feels old as a shrine, the
railings feel like a boundary, and the train feels like a god that departs on
schedule no matter who is ready.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

STATION_NAME = "the train station"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = STATION_NAME
    affords: set[str] = field(default_factory=lambda: {"borrow", "wait", "rush"})


@dataclass
class Oath:
    id: str
    label: str
    phrase: str
    debt_kind: str
    symbol_kind: str
    risk_kind: str
    payment: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rail:
    id: str
    label: str
    phrase: str
    height: str
    danger: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _story_traits() -> list[str]:
    return ["small", "quiet", "careful", "lonely", "hopeful"]


HERO_NAMES = ["Ivo", "Mira", "Suri", "Tavi", "Neri", "Pax", "Luma"]
GUARD_NAMES = ["Keeper", "Conductor", "Watcher", "Old Bell"]
CREDITOR_NAMES = ["the station spirit", "the iron usher", "the old ticket-eye"]


SETTING = Setting()

OATHS = {
    "ticket_pin": Oath(
        id="ticket_pin",
        label="ticket-pin",
        phrase="a silver ticket-pin",
        debt_kind="debt",
        symbol_kind="pin",
        risk_kind="fare",
        payment="return the pin",
        consequence="the traveler must stay behind",
        tags={"debt", "silver", "promise"},
    ),
    "lamp_coin": Oath(
        id="lamp_coin",
        label="lamp-coin",
        phrase="a bright lamp-coin",
        debt_kind="debt",
        symbol_kind="coin",
        risk_kind="fare",
        payment="pay the coin back",
        consequence="the light goes dim for the traveler",
        tags={"debt", "coin", "light"},
    ),
}

RAILS = {
    "platform_rail": Rail(
        id="platform_rail",
        label="railing",
        phrase="the brass railing along the platform",
        height="high",
        danger="it could make the traveler lose balance",
        tags={"railing", "station", "threshold"},
    )
}


ASP_RULES = r"""
debt_item(I) :- oath(I).
risk_place(R) :- rail(R).
station_place(station).

owed(H, I) :- borrows(H, I).
dangerous(H, R) :- leans(H, R), risk_place(R), debt_item(I), owes(H, I).

valid_story(H, I, R) :- borrows(H, I), rail(R), station_place(station).
bad_end(H, I, R) :- dangerous(H, R), refuses(H, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("station_place", "station"))
    for oid, oath in OATHS.items():
        lines.append(asp.fact("oath", oid))
        lines.append(asp.fact("oath_kind", oid, oath.debt_kind))
        lines.append(asp.fact("symbol_kind", oid, oath.symbol_kind))
        lines.append(asp.fact("risk_kind", oid, oath.risk_kind))
        for tag in sorted(oath.tags):
            lines.append(asp.fact("tag", oid, tag))
    for rid, rail in RAILS.items():
        lines.append(asp.fact("rail", rid))
        lines.append(asp.fact("height", rid, rail.height))
        lines.append(asp.fact("danger", rid, rail.danger))
        for tag in sorted(rail.tags):
            lines.append(asp.fact("tag", rid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    guardian: str
    oath: str
    rail: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic train-station debt story with a bad ending.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--guardian", choices=GUARD_NAMES)
    ap.add_argument("--oath", choices=OATHS)
    ap.add_argument("--rail", choices=RAILS)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    guardian = args.guardian or rng.choice(GUARD_NAMES)
    oath = args.oath or rng.choice(list(OATHS))
    rail = args.rail or rng.choice(list(RAILS))
    return StoryParams(hero=hero, hero_type=hero_type, guardian=guardian, oath=oath, rail=rail)


def _maybe_raise_invalid(params: StoryParams) -> None:
    if params.oath not in OATHS:
        raise StoryError("Unknown oath.")
    if params.rail not in RAILS:
        raise StoryError("Unknown railing.")


def _borrow(world: World, hero: Entity, oath: Oath) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.memes["debt"] = hero.memes.get("debt", 0) + 1
    world.facts["owed"] = True
    world.say(
        f"At {world.setting.place}, {hero.id} borrowed {oath.phrase} from {world.facts['guardian'].label}. "
        f"The station spirit said, 'This is a debt. Return it before the last bell.'"
    )


def _wait(world: World, hero: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"So {hero.id} waited beside the long platform, where the lamps shone like small moons."
    )


def _warn(world: World, guardian: Entity, hero: Entity, oath: Oath) -> None:
    world.say(
        f"{guardian.label.capitalize()} watched the clock and said, 'A debt kept too long grows teeth. "
        f"Do not lean on the railing and pretend the train will stop for you.'"
    )
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1


def _lean(world: World, hero: Entity, rail: Rail) -> None:
    hero.memes["reckless"] = hero.memes.get("reckless", 0) + 1
    world.say(
        f"But {hero.id} went to {rail.phrase} and leaned there, hoping the next train would catch {hero.pronoun('object')} anyway."
    )


def _resolve_bad(world: World, hero: Entity, oath: Oath, rail: Rail) -> None:
    hero.memes["loss"] = hero.memes.get("loss", 0) + 1
    world.say(
        f"The railing shook under {hero.id}'s hands. The bell rang once, then twice, and the train rolled away like a bright beast."
    )
    world.say(
        f"{hero.id} still carried the debt, and the station remembered {hero.pronoun('object')} as one who waited too late."
    )
    world.say(
        f"That was the bad ending: the borrowed thing was not returned, and {oath.consequence}."
    )


def tell_story(world: World, params: StoryParams) -> World:
    oath = OATHS[params.oath]
    rail = RAILS[params.rail]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=_story_traits(),
        meters={"location": 0.0},
        memes={"debt": 0.0},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type="thing",
        label=f"the {params.guardian.lower()}",
        memes={"watching": 1.0},
    ))
    world.facts["guardian"] = guardian

    world.say(
        f"Long ago, at {world.setting.place}, there lived {hero.id}, a {hero.pronoun('possessive')} little traveler."
    )
    world.say(
        f"{hero.id} loved the shine of the rails and the hush before a train arrived."
    )
    world.para()

    _borrow(world, hero, oath)
    _wait(world, hero)
    _warn(world, guardian, hero, oath)
    world.para()

    _lean(world, hero, rail)
    _resolve_bad(world, hero, oath, rail)

    world.facts.update(
        hero=hero,
        oath=oath,
        rail=rail,
        bad_ending=True,
        debt_held=True,
        missed_train=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    oath = f["oath"]
    return [
        f"Write a short myth about {hero.id} at a train station, a debt, and a railing.",
        f"Tell a child-friendly myth where {hero.id} borrows {oath.phrase} and learns too late that debts must be paid back.",
        f"Write a small, sad station legend ending with a missed train and a remembered promise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    oath = f["oath"]
    rail = f["rail"]
    guardian = f["guardian"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small traveler at the train station.",
        ),
        QAItem(
            question=f"What did {hero.id} borrow?",
            answer=f"{hero.id} borrowed {oath.phrase}, and that borrowing became a debt that had to be paid back.",
        ),
        QAItem(
            question=f"What did the guardian warn {hero.id} not to do?",
            answer=f"{guardian.label.capitalize()} warned {hero.id} not to lean on {rail.phrase} and trust the train to wait.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The train left, {hero.id} did not board it, and the debt stayed with {hero.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a debt?",
            answer="A debt is something you owe and should give back or pay back later.",
        ),
        QAItem(
            question="What is a railing?",
            answer="A railing is a bar or fence people can hold onto so they do not fall over an edge.",
        ),
        QAItem(
            question="What is a train station?",
            answer="A train station is a place where people wait for trains, buy tickets, and board the cars.",
        ),
        QAItem(
            question="What does a train do?",
            answer="A train carries people or things along tracks from one place to another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.traits:
            parts.append(f"traits={e.traits}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3. #show bad_end/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_model = asp.one_model(asp_program("#show valid_story/3."))
    _ = asp.atoms(clingo_model, "valid_story")
    print("OK: ASP program loads and solves.")
    return 0


CURATED = [
    StoryParams(hero="Mira", hero_type="girl", guardian="Keeper", oath="ticket_pin", rail="platform_rail"),
    StoryParams(hero="Ivo", hero_type="boy", guardian="Watcher", oath="lamp_coin", rail="platform_rail"),
]


def generate(params: StoryParams) -> StorySample:
    _maybe_raise_invalid(params)
    world = tell_story(World(SETTING), params)
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


def asp_facts_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_facts_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_facts_program() + "#show valid_story/3. #show bad_end/3.\n")
        stories = sorted(set(asp.atoms(model, "valid_story")))
        bads = sorted(set(asp.atoms(model, "bad_end")))
        print(f"{len(stories)} valid stories; {len(bads)} bad endings found.")
        for t in stories:
            print(t)
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
