#!/usr/bin/env python3
"""
A small folk-tale storyworld about a madame, a friendship, and a mystery to solve.

Seed tale premise:
A careful madame in a village liked to create little gifts for everyone.
One spring morning, a bell from the old chapel went missing, and the villagers
felt worried. A shy child and a kindly fox friend noticed odd clues left by the
madame: a ribbon, a crumb path, and a lantern still warm. They followed the
foreshadowing, solved the mystery, and found that the madame had hidden the
bell to test whether the village children would help one another. Their friendship
grew stronger when they worked together and returned the bell with a smile.
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
    name: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "trust": 0.0, "joy": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the village"
    style: str = "folk tale"


@dataclass
class Clue:
    id: str
    kind: str
    phrase: str
    location: str
    points_to: str


@dataclass
class Mystery:
    id: str
    missing: str
    solved_by: str
    truth: str


@dataclass
class StoryParams:
    village: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    madame_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village_green": Setting("the village green"),
    "river_lane": Setting("the lane by the river"),
    "old_market": Setting("the old market"),
}

HERO_NAMES = ["Mina", "Anya", "Lena", "Tessa", "Nora", "Pippa"]
FRIEND_NAMES = ["Pip", "Moss", "Rue", "Tarn", "Bram", "Wren"]
MADAME_NAMES = ["Madame Brindle", "Madame Celandine", "Madame Mirelle", "Madame Rose"]

HERO_TYPES = ["girl", "boy", "child"]
FRIEND_TYPES = ["fox", "goat", "crow", "rabbit", "cat"]

# Seed words and narrative instruments
FORESHADOW_CLUES = [
    Clue("ribbon", "clue", "a red ribbon tied to a gatepost", "the gatepost", "the chapel"),
    Clue("crumbs", "clue", "a trail of crumbs by the well", "the well", "the chapel"),
    Clue("lantern", "clue", "a lantern still warm on a bench", "the bench", "the madame"),
]

MYSTERY = Mystery(
    id="bell_missing",
    missing="the chapel bell",
    solved_by="the old bell resting in Madame's basket",
    truth="Madame had hidden the bell to see whether the village children would help each other."
)


# ---------------------------------------------------------------------------
# Plot logic
# ---------------------------------------------------------------------------

class StoryWorldError(StoryError):
    pass


def introduce(world: World, hero: Entity, friend: Entity, madame: Entity) -> None:
    world.say(
        f"In {world.setting.place}, there lived {hero.name}, a small {hero.type}, "
        f"and {friend.name}, a gentle {friend.type}, who were friends from the first spring thaw."
    )
    world.say(
        f"Near them lived {madame.name}, who loved to create little gifts, warm pies, and tidy surprises for the village."
    )


def foreshadow(world: World, madame: Entity) -> None:
    world.say(
        f"One morning, Madame looked out at the square, and she left a few curious things behind without a word."
    )
    for clue in FORESHADOW_CLUES[:2]:
        world.say(
            f"There was {clue.phrase}, and it seemed to point toward {clue.points_to}."
        )
    world.facts["clues"] = [c.id for c in FORESHADOW_CLUES[:2]]


def mystery_turn(world: World, hero: Entity, friend: Entity, madame: Entity) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"By noon, the villagers gasped, for {MYSTERY.missing} was gone from the chapel."
    )
    world.say(
        f"{hero.name} wondered aloud, and {friend.name} sniffed the air as if the wind itself knew the answer."
    )
    world.say(
        f"Then they remembered the clues Madame had left, and the little signs no one else had noticed."
    )
    world.facts["missing"] = MYSTERY.missing


def solve(world: World, hero: Entity, friend: Entity, madame: Entity) -> None:
    world.say(
        f"The friends followed the ribbon, the crumbs, and the warm lantern, step by careful step."
    )
    world.say(
        f"At last, they found {MYSTERY.solved_by}, tucked safely in Madame's basket behind a stack of flour sacks."
    )
    world.say(
        f"Madame smiled, and the truth came out at once: {MYSTERY.truth}"
    )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.facts["truth"] = MYSTERY.truth


def friendship_resolution(world: World, hero: Entity, friend: Entity, madame: Entity) -> None:
    world.para()
    world.say(
        f"{hero.name} and {friend.name} carried the bell back to the chapel together."
    )
    world.say(
        f"The village heard it ring again, bright and kind, and everyone laughed because the mystery had turned into a lesson about helping."
    )
    world.say(
        f"From then on, {hero.name} and {friend.name} stayed close, and Madame always said that good friendships make the best answers."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        name=params.hero_name,
        location=setting.place,
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        name=params.friend_name,
        location=setting.place,
    ))
    madame = world.add(Entity(
        id="madame",
        kind="character",
        type="woman",
        name=params.madame_name,
        location=setting.place,
    ))

    world.facts.update(hero=hero, friend=friend, madame=madame, setting=setting)

    introduce(world, hero, friend, madame)
    world.para()
    foreshadow(world, madame)
    world.para()
    mystery_turn(world, hero, friend, madame)
    solve(world, hero, friend, madame)
    friendship_resolution(world, hero, friend, madame)
    return world


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        combos.append((place, "girl", "fox"))
        combos.append((place, "boy", "rabbit"))
        combos.append((place, "child", "cat"))
    return combos


ASP_RULES = r"""
place(village_green).
place(river_lane).
place(old_market).

hero_type(girl). hero_type(boy). hero_type(child).
friend_type(fox). friend_type(rabbit). friend_type(cat).

valid(P, H, F) :- place(P), hero_type(H), friend_type(F),
                  (H = girl, F = fox; H = boy, F = rabbit; H = child, F = cat).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h in ["girl", "boy", "child"]:
        lines.append(asp.fact("hero_type", h))
    for f in ["fox", "rabbit", "cat"]:
        lines.append(asp.fact("friend_type", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# QA and narration
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    madame: Entity = f["madame"]
    return [
        f"Write a folk-tale style story about {hero.name} and {friend.name} helping {madame.name} solve a mystery in the village.",
        f"Tell a gentle story with foreshadowing, a missing bell, and a friendship that grows stronger when the clues are followed.",
        f"Create a short tale where Madame leaves clues, a child and a friend notice them, and the mystery is solved kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    madame: Entity = f["madame"]
    return [
        QAItem(
            question=f"Who helped solve the mystery in the village?",
            answer=f"{hero.name} and {friend.name} helped solve it, and {madame.name} explained the reason at the end."
        ),
        QAItem(
            question=f"What was missing from the chapel?",
            answer=f"{MYSTERY.missing} was missing from the chapel."
        ),
        QAItem(
            question=f"What did the clues make the friends think about?",
            answer="The clues made them think someone knew more than they first said, so they followed the signs carefully."
        ),
        QAItem(
            question=f"Why did the villagers feel better at the end?",
            answer=f"They felt better because the bell came back, the mystery was solved, and the friends stayed close."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or hidden that people try to figure out."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people or animals who care about each other and help one another."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story leaves little hints that point toward what will matter later."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions -- answerable from the story text =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines += ["", "== (3) World-knowledge questions -- child level, no story needed =="]
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: a madame, a mystery, and a friendship.")
    ap.add_argument("--village", choices=SETTINGS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["fox", "goat", "crow", "rabbit", "cat"])
    ap.add_argument("--madame-name", choices=MADAME_NAMES)
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
    if args.hero_type and args.friend_type:
        ok = any(h == args.hero_type and f == args.friend_type for _, h, f in combos)
        if not ok:
            raise StoryError("No valid folk-tale pairing matches those options.")
    if args.village:
        combos = [c for c in combos if c[0] == args.village]
    if args.hero_type:
        combos = [c for c in combos if c[1] == args.hero_type]
    if args.friend_type:
        combos = [c for c in combos if c[2] == args.friend_type]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    village, hero_type, friend_type = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    madame_name = args.madame_name or rng.choice(MADAME_NAMES)
    return StoryParams(village=village, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type, madame_name=madame_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.village], params)
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
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combinations:\n")
        for row in models:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for village in SETTINGS:
            params = StoryParams(
                village=village,
                hero_name=HERO_NAMES[0],
                hero_type="child",
                friend_name=FRIEND_NAMES[0],
                friend_type="fox",
                madame_name=MADAME_NAMES[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
