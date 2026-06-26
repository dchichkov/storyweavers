#!/usr/bin/env python3
"""
A small animal story world about a charade game, a stubborn wick, and a brave
surprise resolution.

Premise:
- Forest animals are preparing a cozy evening game of charades.
- A lantern wick is needed to light the game circle.
- One animal wants to keep the game secret and guesses, another wants to help,
  causing a conflict.
- Bravery resolves the moment when the right clue is finally shown, ending in
  a surprise reveal that makes everyone laugh.

The world is intentionally tiny: only one strong plot pattern, with variation in
which animal leads, which role they play, and which object or clue becomes the
focus.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "squirrel", "mouse", "badger", "hedgehog", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the forest clearing"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    name: str
    clue: str
    act_verb: str
    mess: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "animal"
    place: str = "paws"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    reason: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "clearing": Setting(place="the forest clearing", affords={"charade"}),
    "burrow": Setting(place="the cozy burrow", indoor=True, affords={"charade"}),
    "glade": Setting(place="the moonlit glade", affords={"charade"}),
}

ACTIVITIES = {
    "charade": Activity(
        id="charade",
        name="charades",
        clue="a funny clue game",
        act_verb="act out clues",
        mess="flutter",
        risk="spoils the surprise",
        keyword="charade",
        tags={"charade", "surprise", "fun"},
    ),
    "lantern": Activity(
        id="lantern",
        name="lantern-lighting",
        clue="a warm little light",
        act_verb="light the lantern",
        mess="spark",
        risk="burns the wick too fast",
        keyword="wick",
        tags={"wick", "light"},
    ),
}

PRIZES = {
    "mask": Prize(label="mask", phrase="a painted owl mask", type="mask"),
    "card": Prize(label="card", phrase="a folded clue card", type="card"),
    "plaque": Prize(label="plaque", phrase="a tiny winner plaque", type="plaque"),
}

TOOLS = [
    Tool(
        id="match",
        label="a long match",
        phrase="a long match",
        helps="light the wick without singeing anything",
        reason="it gives a steady flame for the lantern",
    ),
    Tool(
        id="screen",
        label="a paper screen",
        phrase="a paper screen",
        helps="hide the clue until the right moment",
        reason="it keeps the surprise secret",
    ),
    Tool(
        id="stage",
        label="a blanket stage",
        phrase="a blanket stage",
        helps="make the charade circle easy to see",
        reason="it gives everyone a place to watch",
    ),
]

ANIMALS = {
    "fox": ["Pip", "Fenn", "Milo", "Tara"],
    "rabbit": ["Nina", "Poppy", "Moss", "Luna"],
    "squirrel": ["Sage", "Jasper", "Clover", "Bram"],
    "badger": ["Mina", "Otis", "Hob", "Wren"],
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_kind: str
    hero_name: str
    friend_kind: str
    friend_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, activity: str, prize: str) -> bool:
    return place in SETTINGS and activity in ACTIVITIES and prize in PRIZES and activity == "charade"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                if valid_combo(place, act, prize):
                    out.append((place, act, prize))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def noun_phrase(ent: Entity) -> str:
    return ent.label or ent.type


def setup_characters(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    hero = world.add(Entity(id="hero", kind="animal", type=params.hero_kind, label=params.hero_name))
    friend = world.add(Entity(id="friend", kind="animal", type=params.friend_kind, label=params.friend_name))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, owner=hero.id))
    prize.held_by = hero.id
    return hero, friend, prize


def open_story(world: World, hero: Entity, friend: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"{hero.label} the {hero.type} loved {act.name}, and {friend.label} the {friend.type} loved planning games."
    )
    world.say(
        f"That evening, {hero.pronoun('possessive')} {prize.label} was ready, because the animals wanted a cozy playtime."
    )


def introduce_conflict(world: World, hero: Entity, friend: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["eager"] = 1
    friend.memes["careful"] = 1
    world.para()
    world.say(
        f"But there was a problem: {friend.label} wanted to {act.act_verb} in secret, while {hero.label} kept peeking at the {prize.label}."
    )
    world.say(
        f"{friend.label} said the surprise would {act.risk}, and {hero.label} felt a small conflict in {hero.pronoun('possessive')} chest."
    )


def brave_turn(world: World, hero: Entity, friend: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["bravery"] = 1
    world.para()
    world.say(
        f"Then {hero.label} took a brave breath and said, \"I can wait.\""
    )
    world.say(
        f"That brave choice made room for the game, and {friend.label} quickly set up the {act.keyword} with a bright grin."
    )


def surprise_end(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.para()
    world.say(
        f"When the clue was finally shown, the surprise was funny and sweet: the {prize.label} was not a prize at all, but the last clue for the charade."
    )
    world.say(
        f"{hero.label} guessed it first, {friend.label} jumped with delight, and the forest clearing filled with happy laughter."
    )


# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------
def tell(setting: Setting, act: Activity, prize_key: str, hero_kind: str, hero_name: str,
         friend_kind: str, friend_name: str) -> World:
    world = World(setting)
    hero, friend, prize = setup_characters(world, StoryParams(
        place="clearing", activity=act.id, prize=prize_key,
        hero_kind=hero_kind, hero_name=hero_name,
        friend_kind=friend_kind, friend_name=friend_name,
    ))

    open_story(world, hero, friend, prize, act)
    introduce_conflict(world, hero, friend, act, prize)
    brave_turn(world, hero, friend, act, prize)
    surprise_end(world, hero, friend, prize)

    world.facts.update(
        hero=hero, friend=friend, prize=prize, activity=act,
        setting=setting, resolved=True, conflict=True, surprise=True
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    return [
        f"Write a short animal story about {hero.label} and {friend.label} playing {act.name} in the woods.",
        f"Tell a gentle story where a brave animal waits for a secret clue and then gets a surprise ending.",
        f"Write a child-friendly story using the words charade and wick, with a conflict and a happy surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label} the {hero.type} and {friend.label} the {friend.type}, who were getting ready for {act.name}.",
        ),
        QAItem(
            question=f"What problem caused the conflict?",
            answer=f"{friend.label} wanted to keep the {act.keyword} secret, but {hero.label} kept wanting to look at the {prize.label} too soon.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"{hero.label} took a brave breath, waited, and helped make room for the game until the surprise could be shown.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The {prize.label} turned out to be the last clue for the charade, which made everyone laugh.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a charade?",
            answer="A charade is a game where someone acts out a word or idea without speaking, and other players try to guess it.",
        ),
        QAItem(
            question="What is a wick?",
            answer="A wick is the string inside a candle or lantern that burns and helps make the flame.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel worried or excited.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that people do not know about until the right moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== story qa =="]
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
        lines.append(f"{e.id}: {e.type} {e.label} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(clearing). place(burrow). place(glade).
activity(charade).
prize(mask). prize(card). prize(plaque).

valid(Place, charade, Prize) :- place(Place), prize(Prize).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("activity", "charade"))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print(" only python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def explain_rejection() -> str:
    return "(No story: this tiny world only supports a charade game with a brave surprise ending.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: charade, wick, conflict, bravery, surprise.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-kind", choices=list(ANIMALS.keys()))
    ap.add_argument("--friend-kind", choices=list(ANIMALS.keys()))
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
    if args.activity and args.activity != "charade":
        raise StoryError(explain_rejection())
    place = args.place or rng.choice(list(SETTINGS.keys()))
    activity = args.activity or "charade"
    prize = args.prize or rng.choice(list(PRIZES.keys()))
    if place not in SETTINGS or activity not in ACTIVITIES or prize not in PRIZES:
        raise StoryError("(No valid combination matches the given options.)")
    hero_kind = args.hero_kind or rng.choice(list(ANIMALS.keys()))
    friend_kind = args.friend_kind or rng.choice([k for k in ANIMALS.keys() if k != hero_kind])
    hero_name = args.name or rng.choice(ANIMALS[hero_kind])
    friend_name = args.friend_name or rng.choice(ANIMALS[friend_kind])
    return StoryParams(place=place, activity=activity, prize=prize,
                       hero_kind=hero_kind, hero_name=hero_name,
                       friend_kind=friend_kind, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.prize,
                 params.hero_kind, params.hero_name, params.friend_kind, params.friend_name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:")
        for item in vals:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("clearing", "charade", "mask", "fox", "Pip", "rabbit", "Nina"),
            StoryParams("burrow", "charade", "card", "rabbit", "Luna", "squirrel", "Sage"),
            StoryParams("glade", "charade", "plaque", "squirrel", "Bram", "badger", "Wren"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
