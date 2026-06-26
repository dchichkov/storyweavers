#!/usr/bin/env python3
"""
A small story world for a rhyming dining-room misunderstanding with magic glimmer
and a cheerful bap.

The seed tale idea:
- A child in a dining room loves a tiny magic trick.
- A tap of the spoon makes a bright glimmer and a soft bap.
- A parent first thinks the table got messed up.
- The child shows it was only magic.
- The misunderstanding clears, and the room ends bright and tidy.

The story is intentionally compact, concrete, and state-driven.
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
ROOM = "dining room"


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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class RoomSetting:
    place: str = ROOM
    affords: set[str] = field(default_factory=lambda: {"glimmer_magic"})


@dataclass
class MagicAction:
    id: str
    verb: str
    gerund: str
    sound: str
    sparkle: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "thing"


class World:
    def __init__(self, setting: RoomSetting) -> None:
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


ACTIVITY = MagicAction(
    id="glimmer_magic",
    verb="tap the spoon and make a little rhyme",
    gerund="tapping the spoon and making a little rhyme",
    sound="bap",
    sparkle="glimmer",
    mess="sparkly crumbs",
    tags={"magic", "glimmer", "bap"},
)

PRIZE = Prize(
    label="tablecloth",
    phrase="a neat white tablecloth",
    region="table",
    type="cloth",
)

GIRL_NAMES = ["Mina", "Luna", "Pia", "Nora", "Lily"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Owen", "Ben"]
TRAITS = ["bright", "cheery", "tiny", "curious", "bouncy"]


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class StoryWorld(World):
    pass


def reasonableness_gate(params: StoryParams) -> None:
    if params.gender not in {"girl", "boy"}:
        raise StoryError("gender must be girl or boy")
    if params.parent not in {"mother", "father"}:
        raise StoryError("parent must be mother or father")


def build_world(params: StoryParams) -> World:
    world = World(RoomSetting())
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"joy": 0.0, "glimmer": 0.0, "mess": 0.0},
        memes={"delight": 0.0, "worry": 0.0, "misunderstanding": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"work": 0.0},
        memes={"worry": 0.0, "love": 1.0},
    ))
    tablecloth = world.add(Entity(
        id="cloth",
        type="cloth",
        label="tablecloth",
        phrase="a neat white tablecloth",
        caretaker=parent.id,
        meters={"clean": 1.0, "sparkles": 0.0},
    ))
    spoon = world.add(Entity(
        id="spoon",
        type="thing",
        label="spoon",
        phrase="a shiny silver spoon",
        owner=hero.id,
        meters={"shine": 1.0},
    ))
    wand = world.add(Entity(
        id="wand",
        type="thing",
        label="wand",
        phrase="a tiny wand with a star tip",
        owner=hero.id,
        meters={"magic": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, tablecloth=tablecloth, spoon=spoon, wand=wand)
    return world


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    cloth: Entity = f["tablecloth"]
    spoon: Entity = f["spoon"]
    wand: Entity = f["wand"]

    world.say(
        f"{hero.id} sat in the {ROOM}, bright and small, "
        f"with {hero.pronoun('possessive')} {spoon.label} and {wand.phrase} by the wall."
    )
    world.say(
        f"{hero.id} loved a magic game that could make a {ACTIVITY.sparkle}y glow; "
        f"every little rhyme ended with a soft {ACTIVITY.sound}."
    )

    world.para()
    hero.memes["delight"] += 1
    hero.meters["glimmer"] += 1
    cloth.meters["sparkles"] += 1
    world.say(
        f"{hero.id} whispered, 'Tick and tock, bap-bap-bap,' "
        f"and the spoon gave a merry {ACTIVITY.sound}. "
        f"A quick {ACTIVITY.sparkle} blinked across the cloth like a tiny star."
    )
    world.say(
        f"{hero.id} smiled, because the room looked like a dream and the rhyme was neat and not a scream."
    )

    world.para()
    parent.memes["worry"] += 1
    parent.memes["misunderstanding"] += 1
    world.say(
        f"The {parent.label} peered in and frowned at the {cloth.label}. "
        f"'{hero.id}, oh no—did something spill? That looks like a mess that should not sit still,' "
        f"{parent.pronoun()} said."
    )
    world.say(
        f"{hero.id} blinked. The worry was new, and the little mouth went quiet too."
    )

    hero.memes["worry"] += 1
    hero.meters["glimmer"] += 0.5
    world.say(
        f"Then {hero.id} held up the wand and gave it a twirl; "
        f"the {ACTIVITY.sparkle} danced gently and began to swirl."
    )

    world.para()
    parent.memes["misunderstanding"] = 0.0
    parent.memes["worry"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    cloth.meters["sparkles"] = 0.0
    cloth.meters["clean"] = 1.0
    world.say(
        f"'{It's not a spill,' said {hero.id}. 'It's magic and light; the bap is my rhyme, and it makes the room bright.'"
    )
    world.say(
        f"The {parent.label} laughed, then leaned close to see. "
        f"'A glimmering trick! Why, that was for me!'"
    )
    world.say(
        f"So {hero.id} tapped once more—bap, bap, bap—and the {ROOM} shone soft as a clap."
    )
    world.say(
        f"In the end, the tablecloth stayed neat and white, and the little magic sparkled warm in the night."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    cloth: Entity = f["tablecloth"]
    return [
        QAItem(
            question=f"Where does {hero.id} use the magic rhyme?",
            answer=f"{hero.id} uses it in the {ROOM}.",
        ),
        QAItem(
            question=f"What sound does {hero.id}'s little spell make?",
            answer=f"It makes a soft {ACTIVITY.sound}.",
        ),
        QAItem(
            question=f"Why does the {parent.label} first worry about the cloth?",
            answer=(
                f"The {parent.label} sees the {cloth.label} shine with {ACTIVITY.sparkle} and "
                f"thinks something messy spilled there."
            ),
        ),
        QAItem(
            question=f"What clears up the misunderstanding?",
            answer=(
                f"{hero.id} shows that the shining was only magic, not a spill, and the {parent.label} "
                f"understands."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a glimmer?",
            answer="A glimmer is a small flash of light that shines for a moment.",
        ),
        QAItem(
            question="What does the word bap sound like?",
            answer="Bap sounds like a light tap or pop, almost like a tiny drumbeat.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something impossible or surprising that can happen in a special way.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    return [
        f"Write a short rhyming story about {hero.id} in the {ROOM} with glimmer and bap.",
        f"Tell a gentle story where {hero.id} makes a magic sound and {parent.label} first thinks there is a mess.",
        f"Write a child-friendly rhyme about a small misunderstanding that turns into a happy magic moment.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: glimmer, bap, and a dining-room misunderstanding.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


ASP_RULES = r"""
hero(H) :- hero_name(H).
parent(P) :- parent_name(P).
magic_event(glimmer_magic) :- setting(dining_room), sparkle(glimmer), sound(bap).
misunderstanding(P) :- parent(P), sees(P, glimmer), not knows_magic(P).
resolved :- magic_event(glimmer_magic), explains(hero, parent), understands(parent).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "dining_room"),
        asp.fact("hero_name", "child"),
        asp.fact("parent_name", "parent"),
        asp.fact("sparkle", "glimmer"),
        asp.fact("sound", "bap"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show magic_event/1."))
        return
    if args.verify:
        print("OK: no separate ASP parity set is defined for this compact world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        seeds = [base_seed + i for i in range(3)]
    else:
        seeds = [base_seed + i for i in range(max(1, args.n))]

    for i, seed in enumerate(seeds[: args.n if not args.all else len(seeds)]):
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
        sample = generate(params)
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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
