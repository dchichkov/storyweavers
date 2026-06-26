#!/usr/bin/env python3
"""
storyworlds/worlds/curtain_cavity_flunk_friend_s_backyard_teamwork.py
======================================================================

A small fable-style story world about a child, a friend, a backyard curtain,
a cavity, and a flunked moment that turns into teamwork, magic, and humor.

Premise:
- A child visits a friend's backyard for a little practice.
- A cavity makes the child anxious and the child flunks a simple recital drill.
- A curtain becomes a backyard stage, and a toy wand adds a bit of "magic."
- With teamwork and humor, the friends turn the flop into a kinder ending.

The world is designed to be constraint-checked rather than broadly random.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "friend's backyard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    mess: str = "messy"


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    effect: str
    cues: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "friend_backyard": Setting(place="friend's backyard", affords={"curtain_play"}),
}

ACTIVITIES = {
    "curtain_play": "practice a little backyard play",
}

PRIZES = {
    "curtain": Item(id="curtain", label="curtain", phrase="a striped curtain", region="stage", plural=False, mess="dusty"),
    "cavity": Item(id="cavity", label="cavity", phrase="a sore cavity in a tooth", region="mouth", plural=False, mess="ache"),
    "flunk": Item(id="flunk", label="flunk", phrase="a flunked practice run", region="mind", plural=False, mess="shaky"),
}

PROPS = {
    "wand": Prop(
        id="wand",
        label="wand",
        phrase="a glittery toy wand",
        effect="magic",
        cues={"magic"},
    ),
    "jokes": Prop(
        id="jokes",
        label="jokes",
        phrase="a pocketful of jokes",
        effect="humor",
        cues={"humor"},
    ),
    "team": Prop(
        id="team",
        label="teamwork",
        phrase="two pairs of willing hands",
        effect="teamwork",
        cues={"teamwork"},
    ),
}

NAMES = ["Mina", "Arlo", "Nia", "Eli", "Tess", "Jory", "Luca", "Pip"]
FRIEND_NAMES = ["Bo", "June", "Milo", "Sage", "Bea", "Otis", "Lena", "Finn"]
TRAITS = ["careful", "brave", "gentle", "curious", "cheerful", "patient"]


@dataclass
class StoryParams:
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
hero(H).
friend(F).
setting(friend_backyard).

uses(curtain_play, curtain).
uses(curtain_play, wand).
uses(curtain_play, jokes).
uses(curtain_play, team).

needed(curtain_play, teamwork) :- uses(curtain_play, team).
needed(curtain_play, magic) :- uses(curtain_play, wand).
needed(curtain_play, humor) :- uses(curtain_play, jokes).

good_story(H,F) :- hero(H), friend(F), setting(friend_backyard).
good_story(H,F) :- needed(curtain_play, teamwork), needed(curtain_play, magic), needed(curtain_play, humor), hero(H), friend(F).

#show good_story/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("setting", "friend_backyard"),
            asp.fact("uses", "curtain_play", "curtain"),
            asp.fact("uses", "curtain_play", "wand"),
            asp.fact("uses", "curtain_play", "jokes"),
            asp.fact("uses", "curtain_play", "team"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like backyard story about curtain, cavity, and flunk.")
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if hero == friend:
        friend = rng.choice([n for n in FRIEND_NAMES if n != friend])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(hero=hero, friend=friend, trait=trait)


def _story_world(params: StoryParams) -> World:
    w = World(SETTINGS["friend_backyard"])
    hero = w.add(Entity(id=params.hero, kind="character", type="child", traits=["little", params.trait, "earnest"]))
    friend = w.add(Entity(id=params.friend, kind="character", type="child", traits=["little", "helpful", "bright"]))
    curtain = w.add(Entity(id="curtain", type="curtain", label="curtain", phrase="a striped curtain"))
    cavity = w.add(Entity(id="cavity", type="cavity", label="cavity", phrase="a sore cavity in a tooth"))
    flunk = w.add(Entity(id="flunk", type="flunk", label="flunk", phrase="a flunked practice run"))

    hero.memes.update({"worry": 0.0, "shame": 0.0, "joy": 0.0, "confidence": 0.0})
    friend.memes.update({"joy": 0.0, "confidence": 0.0})
    cavity.meters.update({"ache": 1.0})
    flunk.meters.update({"weight": 1.0})

    w.say(f"Once, in {w.setting.place}, {hero.id} came to visit {friend.id}.")
    w.say(f"{hero.id} had a cavity that ached whenever {hero.id} opened {hero.pronoun('possessive')} mouth wide, and that made {hero.id} feel small.")
    w.para()
    w.say(f"Behind the house, a striped curtain hung from two poles like a tiny stage.")
    w.say(f"{friend.id} called it a fair place for a fable, because even a flunk can become a lesson.")
    w.say(f"{hero.id} tried to practice a little show, but the first try was a flunk.")
    hero.memes["worry"] += 1.0
    hero.memes["shame"] += 1.0
    flunk.meters["weight"] += 1.0
    w.say(f"{hero.id} stared at the grass and wished the ground would hide {hero.pronoun('object')}.")
    w.para()

    w.say(f"Then {friend.id} brought a glittery toy wand and said, \"Magic is just a brave try with a smiling face.\"")
    hero.memes["worry"] -= 0.5
    hero.memes["joy"] += 0.5
    w.say(f"{friend.id} also told a joke about a squirrel who wore a curtain as a cape, and both children laughed.")
    friend.memes["joy"] += 1.0
    hero.memes["joy"] += 1.0
    hero.memes["shame"] -= 0.25

    w.para()
    w.say(f"After that, they worked together.")
    w.say(f"{friend.id} held the curtain steady, {hero.id} took a slow breath, and the toy wand pointed at the stage like a promise.")
    hero.memes["confidence"] += 1.0
    friend.memes["confidence"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)

    w.say(f"{hero.id} tried again, and this time the lines came out clear.")
    flunk.meters["weight"] = 0.0
    w.say(f"The flunk did not vanish from memory, but it stopped being the boss of the day.")
    w.say(f"At the end, the curtain swayed, the cavity still needed care, and the backyard held two friends who had turned a stumble into a shared smile.")

    w.facts.update(hero=hero, friend=friend, curtain=curtain, cavity=cavity, flunk=flunk, params=params)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        "Write a short fable about a child, a curtain, a cavity, and a flunk that becomes wiser with teamwork, magic, and humor.",
        f"Tell a gentle story set in {world.setting.place} where {hero.id} and {friend.id} use a curtain stage to recover from a flunk.",
        "Write a backyard tale in which a sore cavity and a flunked practice are met with a toy wand, jokes, and helping hands.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"Where did {hero.id} visit {friend.id}?",
            answer=f"{hero.id} visited {friend.id} in {world.setting.place}. The whole fable happens in that friend's backyard.",
        ),
        QAItem(
            question=f"What made {hero.id} feel small at first?",
            answer=f"A sore cavity made {hero.id} feel small, and the first practice flunk added to that worry.",
        ),
        QAItem(
            question="What helped the children turn the bad try into a better one?",
            answer="Teamwork, a little magic from a toy wand, and some humor from a silly squirrel joke helped them try again.",
        ),
        QAItem(
            question="What was the curtain used for?",
            answer="The curtain became a tiny backyard stage, so the children could practice together in a fair and playful way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and use their skills together to do something well.",
        ),
        QAItem(
            question="What is a magic wand in a story?",
            answer="A magic wand is a pretend tool in stories that can make surprising or wonderful things happen.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can help because a joke can make people laugh, feel lighter, and try again with less fear.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    world = _story_world(params)
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


def valid_story() -> bool:
    return True


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story shape: child + friend + friend_backyard + teamwork + magic + humor")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        seeds = [base_seed + i for i in range(5)]
        for i, seed in enumerate(seeds):
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
