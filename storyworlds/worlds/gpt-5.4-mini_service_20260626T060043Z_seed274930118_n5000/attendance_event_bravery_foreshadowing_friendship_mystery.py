#!/usr/bin/env python3
"""
storyworlds/worlds/attendance_event_bravery_foreshadowing_friendship_mystery.py
================================================================================

A small mystery storyworld about an attendance list, an event, brave choices,
foreshadowed clues, and friends who solve a little problem together.

Initial story premise:
---
On the night of the autumn lantern event, the hall was full of children and
parents. Mina and her friend Theo had promised to sign the attendance sheet
before the music began. But when they arrived, the sheet was missing.

The event leader worried that without the sheet, nobody would know who had come
in. Mina noticed a trail of chalk dust leading to the side table. Theo was
afraid to go there, because the side room was dark and quiet. Mina felt nervous
too, but she took a deep breath and looked under the table.

There, behind a stack of programs, she found the attendance sheet, safe but
stuck to a spilled jar of glue. Theo smiled, and together they carried it back
to the leader before the lantern song started.

Core state logic:
---
- attendance: people can be present or absent; a sheet tracks sign-ins
- event: the event has a timeline and a preparation state
- mystery: clues appear before the reveal; the final answer depends on them
- bravery: a character can overcome fear to inspect a clue or speak up
- friendship: helping a friend raises trust and resolves tension
- foreshadowing: small earlier signs become meaningful later
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "glue", "missing", "found", "signaled", "present", "fear", "brave", "joy", "trust", "worry"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hall"
    event_name: str = "the lantern event"


@dataclass
class StoryParams:
    place: str
    event_name: str
    hero: str
    friend: str
    leader: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_fear_to_brave(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["fear"] >= THRESHOLD and hero.memes["brave"] < THRESHOLD:
        sig = ("brave", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["brave"] += 1
            out.append(f"{hero.id} took a deep breath and went closer anyway.")
    return out


def _r_glue_clue(world: World) -> list[str]:
    out: list[str] = []
    sheet = world.get("sheet")
    if sheet.meters["glue"] >= THRESHOLD and sheet.meters["found"] < THRESHOLD:
        sig = ("found", sheet.id)
        if sig not in world.fired:
            world.fired.add(sig)
            sheet.meters["found"] += 1
            out.append("The sticky clue made sense at last.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["brave"] >= THRESHOLD and friend.memes["trust"] < THRESHOLD:
        sig = ("trust", friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["trust"] += 1
            hero.memes["trust"] += 1
            out.append(f"{friend.id} smiled because {hero.id} did not leave {friend.pronoun('object')} alone.")
    return out


CAUSAL_RULES = [
    Rule("fear_to_brave", _r_fear_to_brave),
    Rule("glue_clue", _r_glue_clue),
    Rule("friendship", _r_friendship),
]


def story_place(place: str) -> str:
    return {
        "hall": "the hall",
        "library": "the library",
        "gym": "the school gym",
    }.get(place, place)


def setting_detail(setting: Setting) -> str:
    return f"{story_place(setting.place)} was bright with paper lanterns and soft music."


def predict_sheet_state(world: World) -> dict:
    sim = world.copy()
    inspect_clue(sim)
    return {
        "found": sim.get("sheet").meters["found"] >= THRESHOLD,
        "hero_brave": sim.get("hero").memes["brave"] >= THRESHOLD,
    }


def inspect_clue(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    sheet = world.get("sheet")
    if hero.memes["brave"] < THRESHOLD:
        hero.memes["fear"] += 1
        world.say(f"{hero.id} noticed a trail of chalk dust, but the dark side table looked a little scary.")
    hero.meters["seen_clue"] += 1
    if sheet.meters["glue"] >= THRESHOLD:
        world.say(f"Under the programs, the attendance sheet was stuck to a sticky spill.")
        sheet.meters["found"] += 1
        world.facts["clue"] = "glue"
    else:
        world.say(f"Under the programs, the attendance sheet waited safely on the table.")
        sheet.meters["found"] += 1
    friend.memes["trust"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=False)


def begin(world: World, hero: Entity, friend: Entity, leader: Entity, setting: Setting) -> None:
    world.say(f"On the night of {setting.event_name}, {setting_detail(setting)}")
    world.say(f"{hero.id} came with {friend.id} and both promised to sign the attendance sheet before the music began.")
    world.say(f"{leader.id} checked the table and frowned because the sheet was missing.")


def tension(world: World, hero: Entity, friend: Entity, leader: Entity) -> None:
    world.para()
    world.say(f"{leader.id} worried that without it, nobody would know who had arrived.")
    world.say(f"{hero.id} spotted chalk dust near the side table, which was a tiny clue that felt important.")
    friend.memes["fear"] += 1
    world.say(f"{friend.id} hesitated, because the side room looked dark and quiet.")


def bravery_turn(world: World, hero: Entity, friend: Entity) -> None:
    world.para()
    hero.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(f"{hero.id} felt the wobble in {hero.pronoun('possessive')} knees, but {hero.id} still walked to the table.")
    inspect_clue(world)
    world.say(f"{friend.id} hurried over after {hero.id}, glad not to be left behind.")


def resolution(world: World, hero: Entity, friend: Entity, leader: Entity) -> None:
    world.para()
    world.say(f"{hero.id} carried the sheet back before the lantern song started.")
    world.say(f"{leader.id} smiled, signed the last name, and thanked both friends for finding it.")
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(f"By the end, the attendance sheet was back on the table, and the event could begin with everyone counted.")


def tell(place: str, event_name: str, hero_name: str = "Mina", friend_name: str = "Theo", leader_name: str = "Ms. Vale") -> World:
    setting = Setting(place=place, event_name=event_name)
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type="girl", label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type="boy", label=friend_name))
    leader = world.add(Entity(id="leader", kind="character", type="woman", label=leader_name))
    sheet = world.add(Entity(id="sheet", type="thing", label="attendance sheet", phrase="the attendance sheet", caretaker="leader"))
    sheet.meters["missing"] = 1.0
    sheet.meters["glue"] = 1.0
    world.facts["setting"] = setting

    begin(world, hero, friend, leader, setting)
    tension(world, hero, friend, leader)
    bravery_turn(world, hero, friend)
    resolution(world, hero, friend, leader)

    world.facts.update(hero=hero, friend=friend, leader=leader, sheet=sheet, resolved=True)
    return world


SETTINGS = {
    "hall": Setting(place="the hall", event_name="the lantern event"),
    "library": Setting(place="the library", event_name="the reading night"),
    "gym": Setting(place="the school gym", event_name="the family game night"),
}

EVENTS = {
    "lantern": "the lantern event",
    "reading": "the reading night",
    "games": "the family game night",
}

HERO_NAMES = ["Mina", "Lena", "Tia", "Nora", "Ivy"]
FRIEND_NAMES = ["Theo", "Ben", "Eli", "Sam", "Noah"]
LEADER_NAMES = ["Ms. Vale", "Mrs. Finch", "Mr. Reed"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, event) for place in SETTINGS for event in EVENTS]


@dataclass
class StoryParamsRegistry:
    place: str
    event_name: str
    hero: str
    friend: str
    leader: str
    seed: Optional[int] = None


StoryParams = StoryParamsRegistry


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about an attendance sheet at {f["setting"].place}.',
        f"Tell a brave friendship story where {f['hero'].label} and {f['friend'].label} search for the missing attendance list before {f['setting'].event_name} begins.",
        f"Write a gentle mystery with a small clue, a brave choice, and a happy event ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    leader = f["leader"]
    setting = f["setting"]
    sheet = f["sheet"]
    return [
        QAItem(
            question=f"What was missing at {setting.place} before {setting.event_name} began?",
            answer=f"The attendance sheet was missing, and that made {leader.label} worry about keeping track of who had arrived.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} know where to look?",
            answer="A little trail of chalk dust led to the side table, which made the hidden clue feel important.",
        ),
        QAItem(
            question=f"How did {hero.label} show bravery?",
            answer=f"{hero.label} felt afraid of the dark side room, but still went closer and looked under the table.",
        ),
        QAItem(
            question=f"How did the two friends help each other?",
            answer=f"{friend.label} stayed near {hero.label}, and when the sheet was found they carried it back together.",
        ),
        QAItem(
            question=f"What happened to the attendance sheet at the end?",
            answer=f"It was found stuck to a spilled jar of glue, then carried back so the event could begin with everyone counted.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is attendance?",
            answer="Attendance means keeping track of who is present at a place or event.",
        ),
        QAItem(
            question="What is an event?",
            answer="An event is a special gathering where people come together for a purpose, like music, reading, or games.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or uncertain when it is important to do it anyway.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other and help one another.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small sign that helps you figure out what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with attendance, event, bravery, foreshadowing, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", dest="event_name", choices=EVENTS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--leader")
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.event_name:
        combos = [c for c in combos if c[1] == args.event_name]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event_name = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        event_name=event_name,
        hero=args.hero or rng.choice(HERO_NAMES),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        leader=args.leader or rng.choice(LEADER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.event_name, params.hero, params.friend, params.leader)
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
present_at(E, P) :- event(E), place(P), attends(E, P).
missing_sheet(E) :- event(E), attendance_sheet(S), not found(S), at(S, E).
brave(H) :- hero(H), fear(H), clue(H), acts_anyway(H).
friendship(H, F) :- friend(H, F), helps(H, F), trusts(F, H).
foreshadowed(C) :- clue(C), before(C, reveal).
resolved(E) :- missing_sheet(E), brave(hero), friendship(hero, friend).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for event in EVENTS:
        lines.append(asp.fact("event", event))
    lines.append(asp.fact("attendance_sheet", "sheet"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("friend", "hero", "friend"))
    lines.append(asp.fact("clue", "chalk_dust"))
    lines.append(asp.fact("before", "chalk_dust", "reveal"))
    lines.append(asp.fact("fear", "hero"))
    lines.append(asp.fact("acts_anyway", "hero"))
    lines.append(asp.fact("helps", "hero", "friend"))
    lines.append(asp.fact("trusts", "friend", "hero"))
    lines.append(asp.fact("attends", "lantern", "hall"))
    lines.append(asp.fact("at", "sheet", "lantern"))
    lines.append(asp.fact("found", "sheet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="hall", event_name="lantern", hero="Mina", friend="Theo", leader="Ms. Vale"),
    StoryParams(place="library", event_name="reading", hero="Lena", friend="Ben", leader="Mrs. Finch"),
    StoryParams(place="gym", event_name="games", hero="Ivy", friend="Sam", leader="Mr. Reed"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
            header = f"### {p.hero}: {p.event_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
