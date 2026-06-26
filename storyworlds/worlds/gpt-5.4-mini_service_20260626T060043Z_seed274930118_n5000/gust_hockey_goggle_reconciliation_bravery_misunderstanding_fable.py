#!/usr/bin/env python3
"""
Storyworld: Gust Hockey Goggle Reconciliation Bravery Misunderstanding Fable.

A tiny fable-style simulation about a windy hockey game, a missing goggle,
a misunderstanding, brave action, and reconciliation.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"fox", "rabbit", "badger", "owl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the frosty pond"
    afforded: set[str] = field(default_factory=lambda: {"hockey"})
    windy: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    weather: str = "windy"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    owner_role: str = "friend"


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pond": Setting(place="the frosty pond", afforded={"hockey"}, windy=True),
    "field": Setting(place="the open field", afforded={"hockey"}, windy=True),
    "rink": Setting(place="the little outdoor rink", afforded={"hockey"}, windy=False),
}

ACTIVITIES = {
    "hockey": Activity(
        id="hockey",
        verb="play hockey",
        gerund="playing hockey",
        rush="dash back to the puck",
        mess="wind-blown",
        soil="blurry and cold",
        weather="windy",
        keyword="gust",
        tags={"gust", "hockey"},
    )
}

PRIZES = {
    "goggle": Prize(
        label="goggle",
        phrase="a bright blue goggle",
        type="goggle",
        plural=False,
        owner_role="hero",
    ),
    "goggles": Prize(
        label="goggles",
        phrase="a pair of clear goggles",
        type="goggles",
        plural=True,
        owner_role="hero",
    ),
}

HEROES = [
    ("Pip", "fox", "clever"),
    ("Mara", "rabbit", "brave"),
    ("Tovin", "badger", "patient"),
    ("Luma", "owl", "gentle"),
]
FRIENDS = [
    ("Sprig", "rabbit"),
    ("Nip", "fox"),
    ("Wren", "owl"),
    ("Bram", "badger"),
]
TRAITS = ["brave", "gentle", "curious", "steady", "kind"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Setting, Act, Prize) :- setting(Setting), activity(Act), prize(Prize), affords(Setting, Act),
                              risk(Act, Prize), has_fix(Act, Prize).
valid_story(Setting, Act, Prize, Hero) :- valid(Setting, Act, Prize), hero(Hero).
risk(hockey, goggle) :- true.
risk(hockey, goggles) :- true.
has_fix(hockey, goggle) :- true.
has_fix(hockey, goggles) :- true.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.afforded):
            lines.append(asp.fact("affords", sid, act))
        if setting.windy:
            lines.append(asp.fact("windy", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("verb", aid, act.verb))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for hero, _, _ in HEROES:
        lines.append(asp.fact("hero", hero))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                if a == "hockey" and p in {"goggle", "goggles"}:
                    combos.append((s, a, p))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    act = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    world = World(setting)

    hero_name, hero_type, _ = next(h for h in HEROES if h[0] == params.hero)
    friend_name, friend_type = next((f for f in FRIENDS if f[0] == params.friend), FRIENDS[0])

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    gear = world.add(Entity(id=prize.type, type=prize.type, label=prize.label, plural=prize.plural, owner=hero.id))
    gear.worn_by = hero.id

    world.facts.update(
        hero=hero,
        friend=friend,
        gear=gear,
        activity=act,
        prize=prize,
        setting=setting,
        trait=params.trait,
        misunderstanding=True,
        reconciled=True,
        bravery=True,
    )

    # Act I
    world.say(
        f"{hero.name_or_label()} was a {params.trait} little {hero.type} who loved the windy sound of hockey on ice."
    )
    world.say(
        f"Near {setting.place}, {hero.pronoun('subject')} kept {gear.name_or_label()} close, because the clear lenses helped {hero.pronoun('object')} see the puck."
    )
    world.para()

    # Act II
    world.say(
        f"One day, a strong gust swept across {setting.place} and flashed snow into the air."
    )
    world.say(
        f"{friend.name_or_label()} shouted, \"The game is too rough for that {gear.label}!\""
    )
    hero.memes["hurt"] = 1
    friend.memes["worry"] = 1
    world.say(
        f"{hero.name_or_label()} thought {friend.name_or_label()} was making fun of the {gear.label}, and a misunderstanding grew between them."
    )
    world.para()

    # Act III
    hero.memes["bravery"] = 1
    world.say(
        f"Still, {hero.name_or_label()} skated back into the gust and chased the puck bravely."
    )
    world.say(
        f"When the puck slid under the snow, {friend.name_or_label()} saw that {hero.name_or_label()} was not showing off at all, only trying to keep the game fair."
    )
    hero.memes["understood"] = 1
    friend.memes["understood"] = 1
    world.say(
        f"{friend.name_or_label()} apologized, and {hero.name_or_label()} accepted with a nod."
    )
    world.say(
        f"After that, they played side by side, and the little rink felt warm with reconciliation."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short fable about a {hero.type} and a {friend.type} at {world.setting.place} where a gust changes a hockey game.',
        f"Tell a gentle story in which {hero.id} wears {prize.label}, is misunderstood by {friend.id}, and the friends reconcile.",
        f'Write a child-friendly fable using the words "gust", "hockey", and "{prize.label}" that ends with bravery and reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    prize = f["prize"]
    setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.name_or_label()}, a {trait} little {hero.type}, and {friend.name_or_label()}, who met at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.name_or_label()} love to do?",
            answer=f"{hero.name_or_label()} loved {act.gerund} in the wind, and {prize.label} helped {hero.pronoun('object')} see clearly.",
        ),
        QAItem(
            question=f"Why did the two friends have a misunderstanding?",
            answer=f"{friend.name_or_label()} warned that the wind was rough, and {hero.name_or_label()} thought {friend.pronoun('subject')} was teasing the {prize.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.name_or_label()} skated back bravely, the friends understood each other, and they ended in reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gust?",
            answer="A gust is a sudden strong burst of wind.",
        ),
        QAItem(
            question="Why can hockey be hard on a windy day?",
            answer="Wind can push the puck around and make it harder to see and control during a hockey game.",
        ),
        QAItem(
            question="What does a goggle do?",
            answer="A goggle helps protect the eyes and can help a player see better when the weather is harsh.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop feeling upset and become friends again after a disagreement.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary while still trying your best.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks another person means one thing, but they really mean something else.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about gust, hockey, goggle, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero", choices=[h for h, _, _ in HEROES])
    ap.add_argument("--friend", choices=[f for f, _ in FRIENDS])
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
    if args.activity and args.activity != "hockey":
        raise StoryError("This world only supports hockey, gusts, and goggles.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize choice.")
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or "hockey"
    prize = args.prize or rng.choice(list(PRIZES))
    hero = args.hero or rng.choice([h for h, _, _ in HEROES])
    friend = args.friend or rng.choice([f for f, _ in FRIENDS])
    trait = args.trait or rng.choice(TRAITS)
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if activity != "hockey" or prize not in PRIZES:
        raise StoryError("No reasonable story for those choices.")
    return StoryParams(setting=setting, activity=activity, prize=prize, hero=hero, friend=friend, trait=trait)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, activity, prize) combos ({len(stories)} with hero):\n")
        for setting, act, prize in triples:
            heroes = sorted({h for (s, a, p, h) in stories if (s, a, p) == (setting, act, prize)})
            print(f"  {setting:10} {act:8} {prize:8}  [{', '.join(heroes)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for prize in PRIZES:
                params = StoryParams(setting=setting, activity="hockey", prize=prize, hero=HEROES[0][0], friend=FRIENDS[0][0], trait=TRAITS[0], seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
