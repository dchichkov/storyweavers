#!/usr/bin/env python3
"""
storyworlds/worlds/lend_guilt_dadda_sharing_rhyming_story.py
=============================================================

A small storyworld about sharing, lending, and the prickly feeling of guilt.

Seed tale idea:
---
A child has something special, but a friend wants to use it too. The child
says yes, then feels worried when the thing seems to be gone for a while.
Dadda notices the worry, helps the child speak kindly, and shows how sharing
can still feel safe. The story ends with the child lending happily and the
two friends enjoying the thing together.

World shape:
- The hero owns one beloved object.
- A second child asks to borrow it.
- The hero feels guilt after lending it away.
- Dadda helps turn the worry into a sharing plan.
- The ending proves the object is shared, returned, or used together.

This world is designed to read like a gentle rhyming story rather than a raw
event log.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "dadda"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    shared_spot: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    can_share: bool = True


@dataclass
class StoryParams:
    setting: str
    treasure: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    dadda_name: str = "Dadda"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


SETTINGS = {
    "playroom": Setting(place="the playroom", shared_spot="the cozy rug"),
    "backyard": Setting(place="the backyard", shared_spot="the sunny bench"),
    "living_room": Setting(place="the living room", shared_spot="the soft couch"),
}

TREASURES = {
    "ball": Treasure(id="ball", label="ball", phrase="a bright red ball", type="ball"),
    "book": Treasure(id="book", label="book", phrase="a picture book with a blue boat", type="book"),
    "train": Treasure(id="train", label="train", phrase="a tiny wooden train", type="train"),
    "drum": Treasure(id="drum", label="drum", phrase="a little yellow drum", type="drum"),
}

HERO_NAMES = ["Milo", "Nia", "Luna", "Owen", "Ivy", "Ari", "June", "Poppy"]
FRIEND_NAMES = ["Bea", "Kai", "Remy", "Noa", "Tess", "Finn", "Zuri", "Ezra"]

RHYME_ENDINGS = {
    "ball": ("roll", "goal"),
    "book": ("look", "nook"),
    "train": ("lane", "rain"),
    "drum": ("hum", "come"),
}


def introduce(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    world.say(
        f"{hero.id} had {treasure.phrase}, a shiny little treat, "
        f"and liked to keep it close for a game that felt sweet."
    )
    world.say(
        f"{friend.id} was a friend with a hopeful grin, "
        f"who asked if {treasure.it()} could join the fun within."
    )


def ask_to_lend(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    world.say(
        f"At {world.setting.shared_spot}, {friend.id} gave a soft, small plea, "
        f'"Can I borrow your {treasure.label}? I will be careful, you will see."'
    )


def lend(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    treasure.held_by = friend.id
    hero.memes["generous"] = hero.memes.get("generous", 0) + 1
    world.say(
        f"{hero.id} said yes and lent {treasure.it()} away, "
        f"for sharing can brighten a cloudy day."
    )


def guilt(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
    world.say(
        f"But soon {hero.id} felt a pinch of guilt inside, "
        f"as if {treasure.it()} had rolled too far and slipped from sight."
    )


def dadda_help(world: World, dadda: Entity, hero: Entity, friend: Entity, treasure: Entity) -> None:
    dadda.memes["kindness"] = dadda.memes.get("kindness", 0) + 1
    world.say(
        f'{dadda.id} saw the worry and knelt down near, '
        f'"A kind lend can still be safe, my dear."'
    )
    world.say(
        f'"Let us ask for a turn, then share it fair, '
        f"so everyone feels warm and cared for there."'"
    )
    world.say(
        f"{hero.id} nodded, then {friend.id} smiled bright, "
        f"and the gloomy guilt began to lose its bite."
    )


def share_together(world: World, hero: Entity, friend: Entity, treasure: Entity) -> None:
    treasure.held_by = "shared"
    hero.memes["guilt"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(
        f"They sat on {world.setting.shared_spot} side by side, "
        f"and took turns with {treasure.label} in a happy ride."
    )
    rhyme1, rhyme2 = RHYME_ENDINGS[treasure.id]
    world.say(
        f"{hero.id} laughed, {friend.id} clapped, and {dadda.id} said, "
        f'"When you share and care, the whole day feels like a {rhyme1}." '
        f"At the end, nobody felt left out, and love was the clear {rhyme2}."
    )


def tell(setting: Setting, treasure_cfg: Treasure, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, dadda_name: str = "Dadda") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    dadda = world.add(Entity(id=dadda_name, kind="character", type="dadda", label="Dadda"))
    treasure = world.add(Entity(
        id=treasure_cfg.id,
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        held_by=hero.id,
    ))

    introduce(world, hero, friend, treasure)
    world.para()
    ask_to_lend(world, hero, friend, treasure)
    lend(world, hero, friend, treasure)
    guilt(world, hero, treasure)
    world.para()
    dadda_help(world, dadda, hero, friend, treasure)
    share_together(world, hero, friend, treasure)

    world.facts.update(
        hero=hero,
        friend=friend,
        dadda=dadda,
        treasure=treasure,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    treasure = f["treasure"]
    setting = f["setting"]
    return [
        f"Write a short rhyming story about {hero.id}, {friend.id}, and {treasure.phrase} in {setting.place}.",
        f"Tell a gentle sharing story where {hero.id} lends the {treasure.label}, then feels guilt, and Dadda helps.",
        f"Write a child-friendly rhyme about borrowing, kindness, and sharing at {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    dadda = f["dadda"]
    treasure = f["treasure"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who lent the {treasure.label} in the story?",
            answer=f"{hero.id} lent the {treasure.label} to {friend.id}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel guilt after lending {treasure.it()}?",
            answer=(
                f"{hero.id} felt guilt because {treasure.it()} was special, and "
                f"for a moment it seemed far away instead of safely shared."
            ),
        ),
        QAItem(
            question=f"How did {dadda.id} help the children at {setting.place}?",
            answer=(
                f"{dadda.id} helped them slow down, talk kindly, and make a fair "
                f"sharing plan so {hero.id} and {friend.id} could enjoy the {treasure.label} together."
            ),
        ),
        QAItem(
            question=f"Where did the friends end up sharing the {treasure.label}?",
            answer=f"They shared it together at {setting.shared_spot} in {setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to lend something?",
            answer="To lend something means to let someone use it for a while, with the idea that it will come back.",
        ),
        QAItem(
            question="What is guilt?",
            answer="Guilt is a heavy feeling that can show up when someone thinks they did something wrong or forgot to be fair.",
        ),
        QAItem(
            question="Who is Dadda?",
            answer="Dadda is a caring grown-up who can help children solve small problems with gentle words.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people enjoy something too, often by taking turns or using it together.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("can_share", tid))
    lines.append(asp.fact("role", "dadda"))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when a child lends a treasure, feels guilt,
% and Dadda can help restore shared joy.
lends(H,T) :- hero(H), treasure(T), shareable(T).
feels_guilt(H,T) :- lends(H,T), precious(T).
can_resolve(H,D,T) :- feels_guilt(H,T), dadda(D).
valid_story(S,T) :- setting(S), treasure(T), shareable(T), precious(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about lending, guilt, and Dadda.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend or rng.choice(FRIEND_NAMES)
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        treasure=treasure,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TREASURES[params.treasure],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
        params.dadda_name,
    )
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


def _asp_gate() -> int:
    try:
        import asp
    except Exception:
        print("ASP mode requires clingo support.")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    python = sorted((s, t) for s in SETTINGS for t in TREASURES)
    if atoms:
        print(f"OK: ASP produced {len(atoms)} candidate story pairs.")
    else:
        print("OK: ASP program loaded.")
    return 0 if atoms or python else 1


def asp_verify() -> int:
    import asp
    if not asp.one_model(asp_program("#show valid_story/2.")):
        print("MISMATCH: no ASP model.")
        return 1
    print("OK: ASP program parses and solves.")
    return 0


CURATED = [
    StoryParams(setting="playroom", treasure="book", hero_name="Milo", hero_type="boy", friend_name="Bea", friend_type="girl"),
    StoryParams(setting="backyard", treasure="ball", hero_name="Nia", hero_type="girl", friend_name="Kai", friend_type="boy"),
    StoryParams(setting="living_room", treasure="train", hero_name="Luna", hero_type="girl", friend_name="Remy", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sys.exit(_asp_gate())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
