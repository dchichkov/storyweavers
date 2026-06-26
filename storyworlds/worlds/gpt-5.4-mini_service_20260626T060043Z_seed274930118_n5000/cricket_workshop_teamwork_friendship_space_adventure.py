#!/usr/bin/env python3
"""
A standalone storyworld for a tiny workshop space-adventure about a cricket,
teamwork, and friendship.

The seed tale:
A small cricket named Pip lived in a cozy workshop full of bright tools, loose
screws, and shiny scraps. Pip dreamed of joining a little cardboard rocket that
the friends were building for a pretend trip to the moon. But the rocket's
control panel kept wobbling, and the workshop bell kept chiming at the wrong
times.

The friends learned that the best way to launch their pretend adventure was to
work together. One friend held the frame steady, one sorted the bolts, and Pip
used his careful hops to reach tiny places no one else could. When they finished,
the rocket stood strong, and everyone cheered for their friendship.

This world models:
- a workshop with small parts
- a cricket protagonist
- a space-adventure build
- teamwork and friendship as stateful forces
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


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the workshop"
    indoors: bool = True
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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTINGS = {
    "workshop": Setting(place="the workshop", indoors=True, affords={"repair", "build", "sort"}),
}

ACTIVITIES = {
    "build": Activity(
        id="build",
        verb="build the cardboard rocket",
        gerund="building the cardboard rocket",
        rush="dash over to the rocket frame",
        mess="dusty",
        soil="covered in dust",
        zone={"hands", "torso"},
        keyword="rocket",
        tags={"space", "rocket", "teamwork"},
    ),
    "repair": Activity(
        id="repair",
        verb="fix the wobbly control panel",
        gerund="repairing the control panel",
        rush="hurry to the loose screws",
        mess="greasy",
        soil="smudged with grease",
        zone={"hands"},
        keyword="screw",
        tags={"tools", "teamwork"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the tiny parts",
        gerund="sorting tiny parts",
        rush="scurry to the parts tray",
        mess="scattered",
        soil="scattered across the floor",
        zone={"hands", "feet"},
        keyword="parts",
        tags={"parts", "friendship"},
    ),
}

PRIZES = {
    "spacesuit": Prize(
        label="spacesuit",
        phrase="a shiny pretend spacesuit",
        type="spacesuit",
        region="torso",
    ),
    "gloves": Prize(
        label="gloves",
        phrase="soft builder gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a sturdy apron",
        covers={"torso"},
        guards={"dusty"},
        prep="put on a sturdy apron first",
        tail="went to get the sturdy apron",
    ),
    Gear(
        id="mitts",
        label="work mitts",
        covers={"hands"},
        guards={"greasy"},
        prep="grab the work mitts first",
        tail="came back with the work mitts",
        plural=True,
    ),
    Gear(
        id="tray",
        label="a parts tray",
        covers={"hands", "feet"},
        guards={"scattered"},
        prep="bring over a parts tray first",
        tail="carried back the parts tray",
    ),
]

CRICKET_NAMES = ["Pip", "Tiko", "Milo", "Nim", "Bix"]
FRIEND_NAMES = ["Ada", "Bram", "Luna", "Rae", "Jules"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk when an activity touches the same region.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% A gear choice is reasonable only if it guards the mess and covers the region.
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), worn_on(P, R), covers(G, R).
has_fix(A, P) :- protects(_, A, P).

valid_story(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    cl3 = set((a, b, c) for (a, b, c) in cl)
    if py == cl3:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  python:", sorted(py))
    print("  clingo:", sorted(cl3))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, aid, pid))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        if activity.mess in {"dusty", "greasy", "scattered"}:
            item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
    if narrate:
        if activity.id == "build":
            world.say("Tiny dust sparkled in the light as the rocket frame started to take shape.")
        elif activity.id == "repair":
            world.say("The loose screws gave a little rattle before the panel settled down.")
        else:
            world.say("The little parts clicked into neat piles, like stars lined up in the sky.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a small cricket who lived in {world.setting.place} and loved the bright clink of tools.")


def friendship_setup(world: World, hero: Entity, friends: list[Entity]) -> None:
    names = ", ".join(f.id for f in friends[:-1]) + f", and {friends[-1].id}" if len(friends) > 2 else " and ".join(f.id for f in friends)
    world.say(f"{names} were {hero.id}'s friends, and they all wanted to build something wonderful together.")


def space_dream(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(f"{hero.id} dreamed of a pretend trip to the moon, so {hero.pronoun()} wanted to {activity.verb}.")


def worry(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you {activity.verb}, your {prize.label} could get messy," {parent.id} said. '
        f'"Let\'s find a way for everyone to help."'
    )
    return True


def teamwork_turn(world: World, hero: Entity, friends: list[Entity], activity: Activity) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    for friend in friends:
        friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    world.say(f"{hero.id} nodded, and the friends split the job into small pieces the way a rocket crew might.")


def compromise(world: World, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    return gear


def resolve(world: World, hero: Entity, friends: list[Entity], prize: Entity, activity: Activity, gear: Gear) -> None:
    world.say(f"They used {gear.label} and kept going together.")
    world.say(
        f"{hero.id} fixed the tiniest gap, the friends held the frame steady, and soon the cardboard rocket stood tall."
    )
    world.say(
        f"At the end, {hero.id} was still a cricket in the workshop, but now the whole crew was ready for a moon adventure."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    friend1: str
    friend2: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="cricket"))
    parent = world.add(Entity(id="Guide", kind="character", type="adult", label="the workshop guide"))
    friend1 = world.add(Entity(id=params.friend1, kind="character", type="child"))
    friend2 = world.add(Entity(id=params.friend2, kind="character", type="child"))
    prize = world.add(Entity(
        id=params.prize,
        type=params.prize,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=PRIZES[params.prize].region,
        plural=PRIZES[params.prize].plural,
    ))

    act = ACTIVITIES[params.activity]
    gear = None

    introduce(world, hero)
    friendship_setup(world, hero, [friend1, friend2])
    space_dream(world, hero, act)
    world.say(f"The friends had a cardboard rocket on the table, and {hero.id} loved its shiny window.")
    world.say(f"{hero.id} wore {prize.phrase} for the pretend launch, because the costume made the adventure feel real.")

    world.para()
    world.say(f"One afternoon in {world.setting.place}, they all gathered around the rocket.")
    world.say(f"{hero.id} wanted to {act.verb}, but the guide noticed a problem.")

    if worry(world, parent, hero, act, prize):
        world.say(f"{hero.id} looked at the rocket frame and then at the {prize.label}, feeling a little stuck.")
        teamwork_turn(world, hero, [friend1, friend2], act)
        gear = compromise(world, act, prize)
        if gear:
            world.say(f"{friend1.id} said, \"Let's use {gear.label} so we can keep the {prize.label} clean.\"")
            world.say(f"{friend2.id} smiled and added, \"Then everyone can help!\"")
            world.say(f"{hero.id} grinned and agreed.")
            resolve(world, hero, [friend1, friend2], prize, act, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        friends=[friend1, friend2],
        prize=prize,
        activity=act,
        gear=gear,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short child-friendly story about a cricket named {hero.id} in a workshop who dreams of a space adventure.',
        f'Tell a story where {hero.id} and friends use teamwork to {act.verb} without ruining a special costume.',
        'Write a gentle workshop story with friendship, tools, and a pretend rocket to the moon.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small cricket who loves the workshop and a pretend space adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}, because the rocket adventure felt exciting and new.",
        ),
        QAItem(
            question=f"Why did the guide worry about the {prize.label}?",
            answer=f"The guide worried because if {hero.id} went to {act.verb}, the {prize.label} could get messy.",
        ),
    ]
    if gear is not None:
        qa.append(QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They used {gear.label} and worked together so {hero.id} could help build the rocket while the {prize.label} stayed clean.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and proud, because friendship and teamwork helped the whole crew finish the rocket.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "cricket": [
        QAItem(
            question="What is a cricket?",
            answer="A cricket is a small insect that can jump and make a chirping sound.",
        )
    ],
    "workshop": [
        QAItem(
            question="What is a workshop?",
            answer="A workshop is a place where people build, fix, and make things with tools.",
        )
    ],
    "rocket": [
        QAItem(
            question="What is a rocket?",
            answer="A rocket is a vehicle that can fly into space when it has powerful engines.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do different jobs together to reach one goal.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care about each other and enjoy being together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["cricket"])
    out.extend(WORLD_KNOWLEDGE["workshop"])
    out.extend(WORLD_KNOWLEDGE["rocket"])
    out.extend(WORLD_KNOWLEDGE["teamwork"])
    out.extend(WORLD_KNOWLEDGE["friendship"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="workshop", activity="build", prize="spacesuit", hero="Pip", friend1="Ada", friend2="Luna"),
    StoryParams(place="workshop", activity="repair", prize="gloves", hero="Tiko", friend1="Bram", friend2="Jules"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Workshop cricket teamwork friendship space-adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
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
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    hero = args.name or rng.choice(CRICKET_NAMES)
    f1, f2 = rng.sample(FRIEND_NAMES, 2)
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, friend1=f1, friend2=f2)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
