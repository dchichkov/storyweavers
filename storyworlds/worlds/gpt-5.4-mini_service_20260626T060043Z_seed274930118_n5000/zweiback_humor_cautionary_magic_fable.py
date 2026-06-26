#!/usr/bin/env python3
"""
A standalone storyworld for a tiny fable about zweiback, a little bit of magic,
and a cautionary lesson with a humorous turn.

Seed premise:
- In a small burrow village, a young fox loves crisp zweiback.
- A moon-spell can make one loaf deliciously magical, but only if it is shared.
- If the fox hoards it, the magic backfires in a funny but cautionary way.
- The fable ends with generosity restoring the best result.

The world is intentionally small and constraint-checked:
- One magical food, one risky choice, one lesson.
- The simulated state drives the narration and the Q&A.
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
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "he", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hare", "rabbit", "she", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moonlit clearing"
    magic: bool = True


@dataclass
class Treasure:
    label: str
    phrase: str
    magic_word: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    treasure: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "clearing": Setting(place="the moonlit clearing", magic=True),
    "village": Setting(place="the small village lane", magic=True),
    "orchard": Setting(place="the apple orchard edge", magic=True),
}

TREASURES = {
    "zweiback": Treasure(
        label="zweiback",
        phrase="a plate of crisp zweiback",
        magic_word="zweiback",
        lesson="share the crisp loaf before it turns to dust",
    ),
    "honey_zweiback": Treasure(
        label="honey zweiback",
        phrase="a warm tray of honey zweiback",
        magic_word="zweiback",
        lesson="share the sweet slices before the bees notice",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Pippa"]
BOY_NAMES = ["Otto", "Finn", "Puck", "Rudi", "Bram"]
FRIEND_GIRL_NAMES = ["Mira", "Tilly", "Elsa", "June"]
FRIEND_BOY_NAMES = ["Bert", "Ollie", "Piet", "Jaro"]
TRAITS = ["merry", "curious", "proud", "bouncy", "clever"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the hero can meet the friend and the treasure's magic
% is available in the chosen place.
valid_story(P, T) :- setting(P), treasure(T), offers(P, T).

% The cautionary branch is the one where the hero keeps the treasure instead of
% sharing it.
greedy_outcome(T) :- treasure(T), magic_word(T, W), W = zweiback.

% The happy ending needs the hero to share.
good_outcome(T) :- treasure(T), magic_word(T, W), W = zweiback.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.magic:
            lines.append(asp.fact("magic_place", sid))
        lines.append(asp.fact("offers", sid, "zweiback"))
        lines.append(asp.fact("offers", sid, "honey_zweiback"))
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("magic_word", tid, treasure.magic_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_pairs = {(p, t) for p in SETTINGS for t in TREASURES if p in SETTINGS}
    clingo_pairs = set(asp_valid_pairs())
    if clingo_pairs == python_pairs:
        print(f"OK: clingo gate matches python gate ({len(clingo_pairs)} pairs).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_pairs - python_pairs:
        print("  only in clingo:", sorted(clingo_pairs - python_pairs))
    if python_pairs - clingo_pairs:
        print("  only in python:", sorted(python_pairs - clingo_pairs))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict(world: World, hero: Entity, treasure: Entity, shared: bool) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["greed"] = 1.0 if not shared else 0.0
    sim.get(treasure.id).meters["magic"] = 1.0
    if not shared:
        sim.get(hero.id).memes["trouble"] = 1.0
        sim.get(treasure.id).meters["crumbled"] = 1.0
    return {
        "crumbled": bool(sim.get(treasure.id).meters.get("crumbled", 0) >= THRESHOLD),
        "trouble": bool(sim.get(hero.id).memes.get("trouble", 0) >= THRESHOLD),
    }


def tell(setting: Setting, treasure: Treasure, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "proud"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["little", "kind"]))
    loaf = world.add(Entity(
        id="treasure",
        type="thing",
        label=treasure.label,
        phrase=treasure.phrase,
        owner=hero.id,
    ))

    # Act 1: the setting and the magical food
    world.say(
        f"Once in {setting.place}, a little {hero.type} named {hero.id} found {treasure.phrase}."
    )
    world.say(
        f"{hero.id} called it the best {treasure.label} in the whole lane, because it was crisp enough to sing."
    )
    world.say(
        f"A moonbeam touched the loaf, and the crust gave a tiny sparkle like a wink."
    )

    # Act 2: the temptation to keep it all
    world.para()
    world.say(
        f"{friend.id} came by and smelled the warm bread."
    )
    world.say(
        f"{friend.id} asked for a slice, and {hero.id} hugged the plate a little tighter."
    )
    hero.memes["greed"] = 1.0
    loaf.meters["magic"] = 1.0

    pred = predict(world, hero, loaf, shared=False)
    if pred["crumbled"]:
        world.say(
            f"{hero.id} tried to hide the {treasure.label}, but magic bread does not like a tight-fisted paw."
        )
        loaf.meters["crumbled"] = 1.0
        hero.memes["trouble"] = 1.0
        world.say(
            f"With a pop and a puff, the loaf turned into a shower of toasted crumbs that bounced on the stones."
        )
        world.say(
            f"{friend.id} blinked, then laughed so hard a pebble nearly rolled away with the joke."
        )

    # Act 3: the lesson
    world.para()
    hero.memes["greed"] = 0.0
    hero.memes["kindness"] = 1.0
    loaf.meters["crumbled"] = 0.0
    loaf.meters["magic"] = 1.0
    world.say(
        f"{hero.id} saw the crumbs and remembered the old lesson: {treasure.lesson}."
    )
    world.say(
        f"So {hero.id} gathered the last warm pieces and shared them with {friend.id}."
    )
    world.say(
        f"The moonbeam shone again, and the crumbs turned back into a bright, neat loaf."
    )
    world.say(
        f"That night, {hero.id} and {friend.id} ate together, and the village lane felt kinder for it."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        treasure=loaf,
        treasure_cfg=treasure,
        setting=setting,
        shared=True,
        caution=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure_cfg"]
    return [
        f'Write a short fable for children about a {hero.type} who finds {treasure.phrase} and must choose whether to share it.',
        f"Tell a magical cautionary story where {hero.id} learns what happens when {treasure.label} is kept too tightly.",
        f'Write a humorous fable that includes the word "{treasure.magic_word}" and ends with a sharing lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    treasure = f["treasure"]
    treasure_cfg = f["treasure_cfg"]

    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {treasure_cfg.phrase}, and the bread shimmered in a moonbeam.",
        ),
        QAItem(
            question=f"Why did the bread turn into crumbs?",
            answer=f"It turned into crumbs because {hero.id} tried to keep the magic {treasure.label} only for {hero.pronoun('object')}, and the spell punished the greedy choice.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} shared the warm pieces with {friend.id}, and the loaf became whole again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is zweiback?",
            answer="Zweiback is a crisp twice-baked bread, often dry and crunchy, that can be sweet or plain.",
        ),
        QAItem(
            question="Why is sharing good in a fable?",
            answer="Sharing is good because it helps others, and fables often teach that kindness brings better results than selfishness.",
        ),
        QAItem(
            question="What makes moonlight feel magical in stories?",
            answer="Moonlight feels magical in stories because it is soft, silver, and often shines on secret or wonderful events.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: zweiback, humor, caution, and magic in a fable.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        hero_name = args.name or rng.choice(GIRL_NAMES)
        friend_name = args.friend or rng.choice(FRIEND_GIRL_NAMES)
        hero_type = "hare"
        friend_type = "rabbit"
    else:
        hero_name = args.name or rng.choice(BOY_NAMES)
        friend_name = args.friend or rng.choice(FRIEND_BOY_NAMES)
        hero_type = "fox"
        friend_type = "badger"
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        treasure=treasure,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TREASURES[params.treasure],
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
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


CURATED = [
    StoryParams(place="clearing", hero_name="Mina", hero_type="hare", friend_name="Bert", friend_type="rabbit", treasure="zweiback"),
    StoryParams(place="village", hero_name="Otto", hero_type="fox", friend_name="Mira", friend_type="rabbit", treasure="honey_zweiback"),
    StoryParams(place="orchard", hero_name="Nora", hero_type="hare", friend_name="Ollie", friend_type="badger", treasure="zweiback"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible story pairs:")
        for p, t in pairs:
            print(f"  {p:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
