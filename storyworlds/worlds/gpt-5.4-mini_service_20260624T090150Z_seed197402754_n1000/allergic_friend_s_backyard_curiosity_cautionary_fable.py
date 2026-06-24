#!/usr/bin/env python3
"""
storyworlds/worlds/allergic_friend_s_backyard_curiosity_cautionary_fable.py
============================================================================

A small fable-style story world about curiosity, caution, and an allergic friend
in a backyard.

Seed tale premise:
- A curious child visits a friend's backyard.
- A warning is given because one friend is allergic.
- Curiosity tempts the child toward a risky thing in the yard.
- Caution wins, and the friends choose a safer wonder instead.

The world model tracks:
- meters: physical exposure, distance, and safety
- memes: curiosity, caution, worry, relief, and trust

The story is generated from world state rather than from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "a friend's backyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    danger: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    fix: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _r_expose(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("Hero")
    friend = world.get("Friend")
    activity = world.facts["activity"]
    if child.meters.get("near", 0.0) < THRESHOLD:
        return out
    if activity.keyword == "flowers" and child.meters.get("pollen", 0.0) >= THRESHOLD:
        sig = ("allergy", child.id, activity.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        if friend.meters.get("allergic", 0.0) >= THRESHOLD:
            friend.meters["sneeze"] = friend.meters.get("sneeze", 0.0) + 1
        child.meters["trouble"] = child.meters.get("trouble", 0.0) + 1
        out.append("The air turned prickly for the allergic friend.")
    return out


def _r_worry(world: World) -> list[str]:
    friend = world.get("Friend")
    child = world.get("Hero")
    if child.meters.get("trouble", 0.0) < THRESHOLD:
        return []
    sig = ("worry", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1
    return ["That made the friend look worried."]


def _r_calm(world: World) -> list[str]:
    hero = world.get("Hero")
    friend = world.get("Friend")
    if friend.memes.get("worry", 0.0) < THRESHOLD:
        return []
    if hero.memes.get("caution", 0.0) < THRESHOLD:
        return []
    sig = ("calm", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1
    friend.memes["worry"] = 0.0
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_expose, _r_worry, _r_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def ask_caution(world: World) -> None:
    hero = world.get("Hero")
    friend = world.get("Friend")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    friend.memes["caution"] = friend.memes.get("caution", 0.0) + 1
    world.say(
        f"{hero.id} was a curious little {hero.type} who loved new things, "
        f"and {friend.id} was a careful little {friend.type} who knew the backyard well."
    )
    world.say(
        f"In {world.setting.place}, {friend.id} said a gentle warning: "
        f"'{friend.id} is allergic to the flowers near the fence.'"
    )


def tempt(world: World) -> None:
    hero = world.get("Hero")
    activity = world.facts["activity"]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["near"] = 1.0
    hero.meters["pollen"] = 1.0 if activity.keyword == "flowers" else 0.0
    world.say(
        f"{hero.id} wanted to {activity.verb}, because the yard looked bright and full of wonder."
    )
    world.say(
        f"{hero.id} took a step closer to the {activity.keyword}, even though the warning was still in mind."
    )


def warn(world: World) -> None:
    friend = world.get("Friend")
    activity = world.facts["activity"]
    world.say(
        f"'{friend.id} should not get too close,' said {friend.id}, "
        f"looking at the {activity.keyword} with a careful face."
    )


def choose_fix(world: World) -> Optional[Fix]:
    activity = world.facts["activity"]
    fix = FIXES[world.facts["fix"]]
    if activity.risk not in fix.guards:
        return None
    return fix


def resolve(world: World, fix: Fix) -> None:
    hero = world.get("Hero")
    friend = world.get("Friend")
    activity = world.facts["activity"]
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f"Then {hero.id} listened."
    )
    world.say(
        f"{hero.id} and {friend.id} chose to {fix.prep} instead of going near the {activity.keyword}."
    )
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    world.say(
        f"They {fix.tail}, and the worry faded like a cloud after rain."
    )


def tell(place: Setting, activity: Activity, fix: Fix, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="Hero", kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label=friend_name))
    world.facts["activity"] = activity
    world.facts["fix"] = fix.id

    ask_caution(world)
    world.para()
    warn(world)
    tempt(world)
    propagate(world, narrate=True)
    world.para()
    if hero.meters.get("trouble", 0.0) >= THRESHOLD:
        world.say(f"The friend looked nervous, because the air had become risky.")
    chosen = choose_fix(world)
    if chosen is None:
        raise StoryError("No safe fix exists for this activity and risk.")
    resolve(world, chosen)
    world.say(
        f"In the end, the two friends learned that curiosity is good, but caution keeps a friend safe."
    )
    return world


SETTINGS = {
    "backyard": Setting(place="a friend's backyard", affords={"flowers", "butterflies"}),
}

ACTIVITIES = {
    "flowers": Activity(
        id="flowers",
        verb="peek at the flowers",
        gerund="peeking at the flowers",
        rush="run to the flower bed",
        risk="pollen",
        danger="sneeze trouble",
        zone="near",
        keyword="flowers",
        tags={"allergic", "garden", "caution"},
    ),
    "butterflies": Activity(
        id="butterflies",
        verb="watch butterflies",
        gerund="watching butterflies",
        rush="run after the butterflies",
        risk="chasing",
        danger="scrapes",
        zone="near",
        keyword="butterflies",
        tags={"curiosity", "caution"},
    ),
}

FIXES = {
    "window": Fix(
        id="window",
        label="stay on the porch and watch from there",
        prep="stay on the porch and watch from there",
        tail="watched the flowers from a safe porch chair",
        guards={"pollen"},
    ),
    "path": Fix(
        id="path",
        label="follow the stone path and keep a careful distance",
        prep="follow the stone path and keep a careful distance",
        tail="walked the stone path and admired the yard without trouble",
        guards={"pollen", "chasing"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava"]
BOY_NAMES = ["Theo", "Ben", "Max", "Finn"]
TYPES = ["girl", "boy"]
TRAITS = ["curious", "cautious", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for fix_id, fix in FIXES.items():
                if act.risk in fix.guards and place == "backyard":
                    out.append((place, act_id, fix_id))
    return out


def explain_rejection(activity: Activity, fix: Fix) -> str:
    return (
        f"(No story: the fix '{fix.label}' does not honestly guard against {activity.risk}. "
        f"Choose a safer match.)"
    )


def explain_combo(place: str, act: str, fix: str) -> str:
    return f"(No story: {place}, {act}, and {fix} do not make a reasonable cautionary fable.)"


@dataclass
class StoryRegistry:
    pass


KNOWLEDGE = {
    "allergic": [(
        "What does it mean to be allergic?",
        "Being allergic means your body can react badly to some things, like pollen or certain foods, even if they seem harmless to other people."
    )],
    "pollen": [(
        "What is pollen?",
        "Pollen is a tiny powder from flowers and plants. Some people sneeze when it floats into the air."
    )],
    "curiosity": [(
        "What is curiosity?",
        "Curiosity is the wish to learn about new things and ask questions."
    )],
    "caution": [(
        "What is caution?",
        "Caution means being careful so you do not rush into something risky."
    )],
    "backyard": [(
        "What is a backyard?",
        "A backyard is the open space behind a house where people can play, plant things, and rest."
    )],
}
KNOWLEDGE_ORDER = ["allergic", "pollen", "curiosity", "caution", "backyard"]


def generation_prompts(world: World) -> list[str]:
    activity = world.facts["activity"]
    return [
        f'Write a small fable about a curious child in a friend\'s backyard where the word "{activity.keyword}" matters.',
        f"Tell a cautionary story in a friend's backyard about curiosity, safety, and an allergic reaction.",
        f"Write a gentle fable where someone listens to a warning and chooses a safer way to enjoy {activity.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("Hero")
    friend = world.get("Friend")
    activity = world.facts["activity"]
    fix = FIXES[world.facts["fix"]]
    return [
        QAItem(
            question=f"Why did {friend.id} worry in the backyard?",
            answer=f"{friend.id} worried because {friend.id} was allergic to {activity.risk}, and the {activity.keyword} could make the air unsafe."
        ),
        QAItem(
            question=f"What did {hero.id} want to do first?",
            answer=f"{hero.id} wanted to {activity.verb}, because {hero.id} was curious about the yard."
        ),
        QAItem(
            question=f"How did the friends stay safe in the end?",
            answer=f"They used caution and chose to {fix.prep}, which let them enjoy the backyard without causing trouble."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
activity_risky(A) :- activity(A), risk_of(A, R), fix(F), guards(F, R).
valid_combo(P, A, F) :- place(P), affords(P, A), activity_risky(A), fix(F), guards(F, risk_of(A)).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, act.risk))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for g in sorted(fix.guards):
            lines.append(asp.fact("guards", fid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about curiosity and an allergic friend in a backyard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=TYPES)
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
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    if not combos:
        raise StoryError(explain_combo(args.place or "?", args.activity or "?", args.fix or "?"))
    place, activity, fix = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(TYPES)
    friend_type = args.friend_type or rng.choice(TYPES)
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, activity=activity, fix=fix, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], FIXES[params.fix],
                params.hero, params.hero_type, params.friend, params.friend_type)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, activity, fix in combos:
            print(f"  {place:12} {activity:12} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("backyard", "flowers", "window", "Mina", "girl", "Lily", "girl"),
            StoryParams("backyard", "butterflies", "path", "Theo", "boy", "Finn", "boy"),
        ]:
            samples.append(generate(p))
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
            header = f"### {p.hero} and {p.friend}: {p.activity} in the backyard"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
