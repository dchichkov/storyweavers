#!/usr/bin/env python3
"""
A small rhyming story world about a plush friend, a magic quest, and a bad ending
that can happen when the wrong wish is chosen.

The world model tracks a child, a plush toy, a magical path, a quest prize, and
a troublesome spell. The generated story should feel like a tiny, complete tale
with a beginning, a turn, and an ending image that proves what changed.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "queen", "wizard"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "king", "wizard-boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    name: str
    rhyme: str
    turn: str
    ending: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    name: str
    rhyme: str
    spark: str
    cost: str
    guards: set[str] = field(default_factory=set)
    ruins: set[str] = field(default_factory=set)


@dataclass
class Plush:
    id: str
    label: str
    phrase: str
    region: str
    comfort: str
    prize: str
    plushness: str
    gendered: set[str] = field(default_factory=lambda: {"girl", "boy"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", mood="cozy", affords={"quest", "magic"}),
    "attic": Setting(place="the attic", mood="dusty", affords={"quest", "magic"}),
    "garden": Setting(place="the moonlit garden", mood="glowy", affords={"quest", "magic"}),
}

QUESTS = {
    "star-key": Quest(
        id="star-key",
        name="the star-key quest",
        rhyme="bright and slight",
        turn="the key was hidden high in the bluebell sky",
        ending="the lantern dimmed and the door stayed shut",
        risk="the plush would be left behind in the hush",
        tags={"quest", "star", "key"},
    ),
    "moon-bell": Quest(
        id="moon-bell",
        name="the moon-bell quest",
        rhyme="soft and small",
        turn="the bell was lost behind a silver wall",
        ending="the echo failed and the bell rang no more",
        risk="the plush would lose its shine on the floor",
        tags={"quest", "moon", "bell"},
    ),
    "berry-crown": Quest(
        id="berry-crown",
        name="the berry-crown quest",
        rhyme="sweet and neat",
        turn="the crown was perched on a thorny seat",
        ending="the path went dark and the berries fell flat",
        risk="the plush would get snagged and sad from that",
        tags={"quest", "berry", "crown"},
    ),
}

MAGICS = {
    "sparkle-dust": Magic(
        id="sparkle-dust",
        name="sparkle dust",
        rhyme="glow and show",
        spark="tiny stars spun in a row",
        cost="it made the room go dim and slow",
        guards=set(),
        ruins={"quiet"},
    ),
    "mirror-whisper": Magic(
        id="mirror-whisper",
        name="mirror whisper",
        rhyme="near and clear",
        spark="a mirror hummed a secret near",
        cost="it muddled the path and raised some fear",
        guards=set(),
        ruins={"steady"},
    ),
    "lullaby-lantern": Magic(
        id="lullaby lantern",
        name="lullaby lantern",
        rhyme="soft and bright",
        spark="a lantern sang a cradle light",
        cost="it made the quest feel wrong that night",
        guards=set(),
        ruins={"brave"},
    ),
}

PLUSHES = {
    "bunny": Plush(
        id="bunny",
        label="plush bunny",
        phrase="a soft plush bunny",
        region="arms",
        comfort="squishy comfort",
        prize="a silver ribbon",
        plushness="fluffy",
        gendered={"girl", "boy"},
    ),
    "bear": Plush(
        id="bear",
        label="plush bear",
        phrase="a cuddly plush bear",
        region="arms",
        comfort="warm comfort",
        prize="a shiny spoon",
        plushness="fuzzy",
        gendered={"girl", "boy"},
    ),
    "fox": Plush(
        id="fox",
        label="plush fox",
        phrase="a tiny plush fox",
        region="arms",
        comfort="brave comfort",
        prize="a gold acorn",
        plushness="velvet",
        gendered={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Luna", "Mina", "Tessa", "Nori", "Pippa", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Ezra", "Finn", "Theo", "Arlo"]
TRAITS = ["tiny", "brave", "curious", "sleepy", "cheery", "gentle"]


@dataclass
class StoryParams:
    place: str
    quest: str
    magic: str
    plush: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story_combo(place: str, quest: str, magic: str, plush: str) -> bool:
    return place in SETTINGS and quest in QUESTS and magic in MAGICS and plush in PLUSHES


def explain_rejection(place: str, quest: str, magic: str, plush: str) -> str:
    return (
        f"(No story: the requested mix of {place}, {quest}, {magic}, and {plush} "
        f"does not fit this tiny world.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(P,Q,M,L) :- place(P), quest(Q), magic(M), plush(L).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for l in PLUSHES:
        lines.append(asp.fact("plush", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, q, m, l) for p in SETTINGS for q in QUESTS for m in MAGICS for l in PLUSHES if valid_story_combo(p, q, m, l)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def rhyme_opening(hero: Entity, plush: Entity, setting: Setting, quest: Quest, magic: Magic) -> str:
    return (
        f"{hero.id} held {hero.pronoun('possessive')} {plush.label} tight at {setting.place}, "
        f"where the air felt soft and light. "
        f"{hero.pronoun().capitalize()} heard of {quest.name}, a bright little flight, "
        f"and a magic glow named {magic.name} that shimmered at night."
    )


def rhyme_turn(hero: Entity, plush: Entity, quest: Quest, magic: Magic) -> str:
    return (
        f"But the quest had a twist, and the path was unkind: "
        f"{quest.turn}. "
        f"When {magic.spark}, the room slipped out of line, "
        f"and {hero.id} felt a prickly worry twine."
    )


def rhyme_bad_ending(hero: Entity, plush: Entity, quest: Quest, magic: Magic) -> str:
    return (
        f"{magic.cost.capitalize()} {quest.ending}. "
        f"{hero.id} hugged {hero.pronoun('possessive')} {plush.label}, yet could not make it right; "
        f"the little quest ended sadly, with no shining prize in sight."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    quest = QUESTS[params.quest]
    magic = MAGICS[params.magic]
    plush = PLUSHES[params.plush]

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    toy = world.add(Entity(
        id="plush",
        type="plush",
        label=plush.label,
        phrase=plush.phrase,
        owner=hero.id,
        caretaker=hero.id,
        plural=False,
        meters={"softness": 1.0, "prize": 0.0},
        memes={"comfort": 1.0},
    ))
    hero.meters["courage"] = 1.0
    hero.memes["hope"] = 1.0
    world.facts = {
        "hero": hero,
        "plush": toy,
        "quest": quest,
        "magic": magic,
        "setting": setting,
        "plush_cfg": plush,
    }

    world.say(rhyme_opening(hero, toy, setting, quest, magic))
    world.para()
    world.say(rhyme_turn(hero, toy, quest, magic))
    world.para()
    world.say(rhyme_bad_ending(hero, toy, quest, magic))
    hero.memes["sadness"] = 1.0
    toy.meters["prize"] = 0.0
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, magic, plush = f["hero"], f["quest"], f["magic"], f["plush_cfg"]
    return [
        f'Write a short rhyming story for a young child about {hero.id}, a {plush.label}, and a magic quest.',
        f"Tell a tiny story where {hero.id} carries {plush.phrase} to {quest.name} and a strange magic makes the ending bad.",
        f"Write a simple rhyming tale that includes {magic.name}, a quest, and a plush toy, ending in a sad final image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest, magic, plush = f["hero"], f["quest"], f["magic"], f["plush_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} hold on to at the start of the story?",
            answer=f"{hero.id} held a {plush.label} tight at {world.setting.place}.",
        ),
        QAItem(
            question=f"What kind of adventure did {hero.id} want to try?",
            answer=f"{hero.id} wanted to try {quest.name}, a small magic quest.",
        ),
        QAItem(
            question=f"What made the quest go wrong?",
            answer=f"The magic called {magic.name} made the room slip out of line and turned the ending bad.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended sadly, with {hero.id} hugging the {plush.label} and no prize won.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    plush = f["plush_cfg"]
    magic = f["magic"]
    quest = f["quest"]
    return [
        QAItem(
            question="What is a plush toy?",
            answer="A plush toy is a soft stuffed toy made for hugging and comfort.",
        ),
        QAItem(
            question="What can magic mean in a story?",
            answer="Magic in a story means special events or powers that do impossible things.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something important.",
        ),
        QAItem(
            question=f"What makes {plush.label} feel nice to hold?",
            answer=f"It is soft and made for cuddling, so it gives {plush.comfort}.",
        ),
        QAItem(
            question=f"What does {magic.name} suggest in the world?",
            answer=f"It suggests a magical light or spell that changes how the quest goes.",
        ),
        QAItem(
            question=f"What does {quest.name} sound like?",
            answer=f"It sounds like a small adventure with a goal, a risk, and a result.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Required interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming story world about a plush, a quest, and magic.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--magic", choices=MAGICS.keys())
    ap.add_argument("--plush", choices=PLUSHES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    quest = args.quest or rng.choice(list(QUESTS.keys()))
    magic = args.magic or rng.choice(list(MAGICS.keys()))
    plush = args.plush or rng.choice(list(PLUSHES.keys()))
    if not valid_story_combo(place, quest, magic, plush):
        raise StoryError(explain_rejection(place, quest, magic, plush))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PLUSHES[plush].gendered:
        raise StoryError(f"(No story: this plush fits neither that gender nor that request.)")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, magic=magic, plush=plush, name=name, gender=gender, trait=trait)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="nursery", quest="star-key", magic="sparkle-dust", plush="bunny", name="Luna", gender="girl", trait="curious"),
    StoryParams(place="attic", quest="moon-bell", magic="mirror-whisper", plush="bear", name="Milo", gender="boy", trait="brave"),
    StoryParams(place="garden", quest="berry-crown", magic="lullaby-lantern", plush="fox", name="Tessa", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print(" ", t)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.quest} + {p.magic} + {p.plush}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
