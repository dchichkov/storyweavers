#!/usr/bin/env python3
"""
Space-adventure storyworld: a crew, a tight fit, a flashback, teamwork, and a
small conflict that ends in a safe launch.

The seed premise:
- A child or young astronaut wants to join a space mission.
- A suit or seat must fit correctly.
- A flashback reminds someone why the fit matters.
- Teamwork solves a conflict so the mission can continue.

This file follows the Storyweavers storyworld contract with a tiny simulated
world model, grounded story generation, QA, and a matching ASP twin.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "pilot"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Station:
    place: str = "the launch bay"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Suit:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback = False
        self.mode = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.station)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.flashback = self.flashback
        clone.mode = self.mode
        return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.memes.get("conflict", 0.0) >= THRESHOLD and actor.memes.get("tension", 0.0) < THRESHOLD:
                sig = ("tension", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.memes["tension"] = 1.0
                    out.append(f"The room felt tight with worry.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def fit_check(activity: Activity, suit: Suit) -> bool:
    return activity.mess in suit.guards and bool(activity.zone & suit.covers)


def select_suit(activity: Activity, suit: Suit) -> Optional[Suit]:
    for s in SUITS:
        if fit_check(activity, s):
            return s
    return None


def story_flashback(world: World, hero: Entity, suit: Entity) -> None:
    world.flashback = True
    world.say(
        f"Flashback: {hero.id} remembered the last launch, when {hero.pronoun('possessive')} "
        f"{suit.label} had been too loose and the strap slipped."
    )
    world.say(
        f"That old moment explained why the fit mattered now."
    )


def introduce(world: World, hero: Entity, mentor: Entity, suit: Entity, act: Activity) -> None:
    world.say(
        f"{hero.id} was a young {hero.type} who loved {act.gerund} and listening to the radio hum."
    )
    world.say(
        f"{hero.id}'s {mentor.label} had brought a {suit.phrase} for the mission."
    )
    hero.memes["want"] = 1.0
    suit.worn_by = hero.id


def arrive(world: World, hero: Entity, mentor: Entity, act: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {mentor.label} went to {world.station.place}."
    )
    world.say(
        f"{hero.id} wanted to {act.verb} right away."
    )


def conflict(world: World, hero: Entity, mentor: Entity, act: Activity, suit: Entity) -> None:
    hero.memes["conflict"] = 1.0
    world.say(
        f"Then {hero.pronoun('possessive')} {mentor.label} frowned and said the {suit.label} had to fit just right."
    )
    world.say(
        f"{hero.id} tried to {act.rush}, but the idea of waiting made {hero.pronoun('object')} cross."
    )


def teamwork(world: World, hero: Entity, mentor: Entity, act: Activity, suit: Entity, fit_suit: Suit) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = 1.0
    world.say(
        f"Then they worked together."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {mentor.label} held the suit open, and {hero.id} helped pull the straps snug."
    )
    world.say(
        f"With that teamwork, the {fit_suit.label} fit well, and {hero.id} could {act.verb} safely."
    )


def tell(station: Station, activity: Activity, suit_cfg: Suit, hero_name: str, hero_type: str, mentor_label: str) -> World:
    world = World(station)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["curious", "brave"]))
    mentor = world.add(Entity(id="Mentor", kind="character", type="captain", label=mentor_label))
    suit = world.add(Entity(
        id=suit_cfg.id,
        type="thing",
        label=suit_cfg.label,
        phrase=suit_cfg.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        plural=suit_cfg.plural,
    ))
    introduce(world, hero, mentor, suit, activity)
    story_flashback(world, hero, suit)
    world.para()
    arrive(world, hero, mentor, activity)
    conflict(world, hero, mentor, activity, suit)
    world.para()
    fit_suit = select_suit(activity, suit_cfg)
    if fit_suit is None:
        raise StoryError("No safe suit fits this space mission.")
    teamwork(world, hero, mentor, activity, suit, fit_suit)
    world.facts.update(hero=hero, mentor=mentor, suit=suit, activity=activity, station=station, fit_suit=fit_suit)
    return world


@dataclass
class StoryParams:
    place: str
    activity: str
    suit: str
    name: str
    type: str
    mentor_label: str
    seed: Optional[int] = None


STATIONS = {
    "launch_bay": Station(place="the launch bay", affords={"launch"}),
    "moon_dock": Station(place="the moon dock", affords={"launch"}),
}

ACTIVITIES = {
    "launch": Activity(
        id="launch",
        verb="join the launch",
        gerund="helping with launches",
        rush="dash toward the hatch",
        mess="space_dust",
        soil="dusty",
        zone={"torso", "arms"},
        keyword="fit",
        tags={"fit", "space", "teamwork", "conflict"},
    ),
    "repair": Activity(
        id="repair",
        verb="fix the rover",
        gerund="repairing rover parts",
        rush="grab the tool tray",
        mess="grease",
        soil="greasy",
        zone={"hands", "torso"},
        keyword="fit",
        tags={"fit", "space", "teamwork", "conflict"},
    ),
}

SUITS = [
    Suit(
        id="seal_suit",
        label="seal suit",
        phrase="a seal suit with soft cuffs",
        covers={"torso", "arms"},
        guards={"space_dust"},
        prep="tighten the cuffs",
        tail="checked every buckle together",
    ),
    Suit(
        id="tool_vest",
        label="tool vest",
        phrase="a tool vest with neat pockets",
        covers={"torso"},
        guards={"grease"},
        prep="zip it up",
        tail="checked the pockets together",
    ),
]

HERO_NAMES = ["Nova", "Mika", "Rin", "Tara", "Zed", "Pip"]
HERO_TYPES = ["girl", "boy"]
MENTOR_LABELS = ["captain", "pilot"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, station in STATIONS.items():
        for act_id in station.affords:
            act = ACTIVITIES[act_id]
            for suit_id, suit in {s.id: s for s in SUITS}.items():
                if fit_check(act, suit):
                    out.append((place, act_id, suit_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short space adventure story for a young child that includes the word "fit".',
        f"Tell a story where {hero.id} wants to {act.verb}, but a grown-up worries about the suit fit, and they solve it by working together.",
        f"Write a simple space story with a flashback, a small conflict, and teamwork that ends with a safe launch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    suit = f["suit"]
    act = f["activity"]
    fit_suit = f["fit_suit"]
    return [
        QAItem(
            question=f"Why did {mentor.label} worry about the {suit.label}?",
            answer=f"{mentor.label.capitalize()} worried because the {suit.label} had to fit just right before {hero.id} could {act.verb} safely.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.id} about?",
            answer=f"The flashback reminded {hero.id} that a loose suit had slipped on the last launch, so the fit mattered now.",
        ),
        QAItem(
            question=f"How did {hero.id} and the {mentor.label} solve the problem?",
            answer=f"They solved it by working together to make the {fit_suit.label} fit well, which let {hero.id} {act.verb}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with teamwork, a safe fit, and {hero.id} ready for the mission at {world.station.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fit mean when talking about clothes or gear?",
            answer="Fit means that clothes or gear are the right size and shape for the person using them.",
        ),
        QAItem(
            question="Why do astronauts check their gear before launch?",
            answer="Astronauts check their gear before launch so everything stays safe and works the way it should.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other do a job together.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback: {world.flashback}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="launch_bay", activity="launch", suit="seal_suit", name="Nova", type="girl", mentor_label="captain"),
    StoryParams(place="moon_dock", activity="launch", suit="seal_suit", name="Mika", type="boy", mentor_label="pilot"),
]


def explain_rejection(activity: Activity, suit: Suit) -> str:
    return (
        f"(No story: the {suit.label} does not properly fit the needs of {activity.verb}. "
        f"Try a different suit or activity.)"
    )


ASP_RULES = r"""
fit_combo(P,A,S) :- affords(P,A), activity(A), suit(S), need(A,R), covers(S,R), guards(S,M), mess_of(A,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, st in STATIONS.items():
        lines.append(asp.fact("station", pid))
        for a in sorted(st.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("need", aid, r))
    for sid, s in {s.id: s for s in SUITS}.items():
        lines.append(asp.fact("suit", sid))
        for r in sorted(s.covers):
            lines.append(asp.fact("covers", sid, r))
        for m in sorted(s.guards):
            lines.append(asp.fact("guards", sid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fit_combo/3."))
    return sorted(set(asp.atoms(model, "fit_combo")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with fit, flashback, teamwork, and conflict.")
    ap.add_argument("--place", choices=STATIONS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--suit", choices={s.id: s for s in SUITS})
    ap.add_argument("--name")
    ap.add_argument("--type", choices=HERO_TYPES)
    ap.add_argument("--mentor-label", choices=MENTOR_LABELS)
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.suit is None or c[2] == args.suit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, suit = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        suit=suit,
        name=args.name or rng.choice(HERO_NAMES),
        type=args.type or rng.choice(HERO_TYPES),
        mentor_label=args.mentor_label or rng.choice(MENTOR_LABELS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(STATIONS[params.place], ACTIVITIES[params.activity], next(s for s in SUITS if s.id == params.suit), params.name, params.type, params.mentor_label)
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
        print(asp_program("#show fit_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} fit-compatible combos:\n")
        for place, act, suit in combos:
            print(f"  {place:10} {act:8} {suit}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (suit: {p.suit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
