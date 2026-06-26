#!/usr/bin/env python3
"""
storyworlds/worlds/laxative_glower_concerted_quest_friendship_myth.py
=====================================================================

A tiny myth-style storyworld about a quest that can only succeed when friends
act together.

Seed premise:
- A hero is sent on a small mythic quest.
- A friend may glower when the first plan is delayed.
- A healer may offer a laxative herb or tea when someone's belly is too full
  and a pause is needed before travel.
- The ending turns on concerted friendship: the companions choose a shared,
  careful way forward.

This world keeps the prose child-facing and concrete while using mythic
images: gates, hills, shrines, rivers, torches, vows, and old songs.
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
        female = {"girl", "woman", "mother", "sister", "queen", "heroine"}
        male = {"boy", "man", "father", "brother", "king", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    image: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    outcome: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    location: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    gives: str
    reason: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "hill": Place("the hill shrine", "The hill shrine stood under old pines.", {"quest", "gift"}),
    "ford": Place("the river ford", "The river ford flashed with bright water.", {"quest"}),
    "grove": Place("the moonlit grove", "The moonlit grove hummed with crickets.", {"quest", "gift"}),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        verb="bring back the silver bell",
        gerund="bringing back the silver bell",
        rush="run to the hidden gate",
        outcome="shone again at the shrine",
        risk="the bell could be lost in the dark",
        keyword="quest",
        tags={"quest", "silver"},
    ),
    "seed": Quest(
        id="seed",
        verb="deliver the star-seed",
        gerund="delivering the star-seed",
        rush="hurry over the stones",
        outcome="woke the sleeping garden",
        risk="the seed could be cracked",
        keyword="quest",
        tags={"quest", "star"},
    ),
}

TREASURES = {
    "bell": Treasure("bell", "a silver bell", "bell", "shrine"),
    "seed": Treasure("seed", "a star-seed in a leaf bowl", "seed", "grove"),
}

GIFTS = {
    "laxative_tea": Gift(
        id="laxative_tea",
        label="laxative tea",
        phrase="a warm cup of laxative tea",
        gives="help the belly move along",
        reason="the old healer said the traveler would feel lighter after the long road",
    ),
    "laxative_herb": Gift(
        id="laxative_herb",
        label="laxative herb",
        phrase="a small bundle of laxative herb",
        gives="settle a cramped belly",
        reason="the healer said the root would help before the road home",
    ),
}

NAMES = ["Ari", "Mira", "Toma", "Sela", "Ivo", "Nara"]
FRIEND_NAMES = ["Pip", "Lina", "Bram", "Kira", "Soren", "Noa"]
TYPES = ["hero", "heroine", "boy", "girl"]
FRIEND_TYPES = ["friend", "sister", "brother", "companion"]
TRAITS = ["brave", "kind", "steady", "curious", "bold"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    treasure: str
    gift: str
    name: str
    friend: str
    gender: str
    friend_gender: str
    trait: str
    friend_trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic quest about friendship and a careful remedy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--friend-gender", choices=["boy", "girl"])
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


def reasonableness_gate(setting: str, quest: str, treasure: str, gift: str) -> bool:
    return setting in SETTINGS and quest in QUESTS and treasure in TREASURES and gift in GIFTS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    treasure = args.treasure or quest
    gift = args.gift or rng.choice(list(GIFTS))
    if not reasonableness_gate(setting, quest, treasure, gift):
        raise StoryError("The chosen myth pieces do not fit together.")
    gender = args.gender or rng.choice(["boy", "girl"])
    friend_gender = args.friend_gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(
        setting=setting,
        quest=quest,
        treasure=treasure,
        gift=gift,
        name=name,
        friend=friend,
        gender=gender,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def _hero_type(gender: str) -> str:
    return "heroine" if gender == "girl" else "hero"


def _friend_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    treasure = TREASURES[params.treasure]
    gift = GIFTS[params.gift]

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=_hero_type(params.gender), traits=[params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type=_friend_type(params.friend_gender), traits=[params.friend_trait]))
    healer = world.add(Entity(id="Healer", kind="character", type="old woman", label="the old healer"))

    hero.memes["hope"] = 1
    friend.memes["love"] = 1

    world.say(
        f"Long ago, {hero.id} was a {params.trait} {hero.type} who listened for old songs and hidden doors."
    )
    world.say(
        f"{hero.id} and {friend.id} were bound by friendship, and together they dreamed of a small quest: "
        f"{quest.verb}."
    )

    world.para()
    world.say(
        f"One dawn they climbed to {place.name}. {place.image} The air felt still, and the way ahead waited like a question."
    )
    world.say(
        f"{hero.id} wanted to {quest.rush}, because the treasure they sought was {treasure.phrase}."
    )
    world.say(
        f"But the old tale warned that {quest.risk}."
    )

    if params.gift == "laxative_tea":
        world.say(
            f"At the gate, {healer.id} offered {hero.id} {gift.phrase}. "
            f"{healer.id} said it would {gift.gives}, because {gift.reason}."
        )
    else:
        world.say(
            f"At the gate, {healer.id} placed {gift.phrase} in {hero.id}'s hands. "
            f"{healer.id} said it would {gift.gives}, because {gift.reason}."
        )
    hero.meters["gift"] = 1
    hero.memes["delay"] = 1
    friend.memes["glower"] = 1

    world.say(
        f"{friend.id} gave a dark glower at the delay. {friend.id} wanted the quest to begin at once."
    )
    world.say(
        f"Still, {hero.id} trusted the healer's wise word and held the remedy close."
    )

    world.para()
    hero.meters["calm"] = 1
    friend.memes["glower"] = 0
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    world.say(
        f"After a quiet pause, the remedy did its gentle work, and the tight feeling faded."
    )
    world.say(
        f"Then {hero.id} and {friend.id} looked at one another and chose a concerted plan."
    )
    world.say(
        f"Side by side, they crossed the stones with careful steps, carrying the treasure together."
    )
    world.say(
        f"At last, {quest.verb} felt possible, and the treasure {quest.outcome}."
    )

    world.facts.update(hero=hero, friend=friend, healer=healer, quest=quest, treasure=treasure, gift=gift, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth about {f["hero"].id} and {f["friend"].id} on a quest where the word "concerted" matters.',
        f"Tell a child-friendly legend in which a {f['hero'].type} and a friend face a delay, a glower, and a shared plan.",
        f'Write a simple mythic story that includes the words "laxative", "glower", and "concerted".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, quest, treasure, gift, place = f["hero"], f["friend"], f["quest"], f["treasure"], f["gift"], f["place"]
    return [
        QAItem(
            question=f"Who went on the quest at {place.name}?",
            answer=f"{hero.id} and {friend.id} went together. They were friends, and they chose the quest side by side.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the quest?",
            answer=f"{hero.id} wanted to {quest.verb}. The friends hoped to bring home {treasure.phrase}.",
        ),
        QAItem(
            question=f"Why did {friend.id} glower at the gate?",
            answer=f"{friend.id} glowered because the journey had to pause for the healer's remedy before the quest could begin safely.",
        ),
        QAItem(
            question=f"How did the friends finally move forward?",
            answer=f"They used a concerted plan: they waited for the gentle remedy, then walked and carried the treasure together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, like finding something important or helping someone in need.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay together.",
        ),
        QAItem(
            question="What does glower mean?",
            answer="To glower means to look at something with a dark, unhappy face.",
        ),
        QAItem(
            question="What does concerted mean?",
            answer="Concerted means done together on purpose, with everyone working as one team.",
        ),
        QAItem(
            question="What is a laxative?",
            answer="A laxative is a medicine or herb that helps the body move along when someone is uncomfortable and needs relief.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hill", quest="bell", treasure="bell", gift="laxative_tea", name="Ari", friend="Pip", gender="boy", friend_gender="girl", trait="brave", friend_trait="steady"),
    StoryParams(setting="grove", quest="seed", treasure="seed", gift="laxative_herb", name="Mira", friend="Bram", gender="girl", friend_gender="boy", trait="kind", friend_trait="bold"),
]


ASP_RULES = r"""
quest_story(S,Q,T,G) :- setting(S), quest(Q), treasure(T), gift(G).
valid(S,Q,T,G) :- quest_story(S,Q,T,G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = {(s, q, t, g) for s in SETTINGS for q in QUESTS for t in TREASURES for g in GIFTS}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_all() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in resolve_all()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
