#!/usr/bin/env python3
"""
storyworlds/worlds/abcdefghijklmnop_instinct_artery_quest_tall_tale.py
======================================================================

A tiny tall-tale story world about a child-sized quest with oversized weather,
oversized courage, and one very odd map word: "artery".

The seed image:
- A cheerful traveler named Abcdefghijklmnop
- A stubborn quest across a long red canyon-river called the artery
- A helpful guide named Instinct who always points the right way
- A prize that only makes sense after the traveler listens, tries, and changes

The world is deliberately small, classical, and simulation-driven:
meters model physical things like distance, load, and danger;
memes model emotional things like worry, grit, trust, and pride.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Path:
    name: str
    miles: int
    danger: int
    barrier: bool = False


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    value: str


@dataclass
class StoryParams:
    name: str = "Abcdefghijklmnop"
    gender: str = "boy"
    parent: str = "grandmother"
    path: str = "artery"
    prize: str = "sunstone"
    seed: Optional[int] = None


class World:
    def __init__(self, path: Path) -> None:
        self.path = path
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PATHS = {
    "artery": Path(name="the artery", miles=9, danger=3, barrier=True),
    "ridge": Path(name="the long ridge", miles=6, danger=2, barrier=False),
    "marsh": Path(name="the marsh road", miles=5, danger=4, barrier=False),
}

PRIZES = {
    "sunstone": Prize(label="sunstone", phrase="a bright sunstone", type="stone", value="warm light"),
    "feather": Prize(label="feather", phrase="a silver feather", type="feather", value="sky luck"),
    "map": Prize(label="map", phrase="an old map with a gold star", type="map", value="a way home"),
}

TRAITS = ["bold", "curious", "stubborn", "cheerful", "lively"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(path: Path, prize: Prize) -> bool:
    # The prize must be something the traveler can honestly bring back after a quest.
    # The artery is the only path with enough drama for the default tale.
    if path.name == "the artery":
        return prize.label in {"sunstone", "map"}
    if path.name == "the long ridge":
        return prize.label in {"feather", "map"}
    return prize.label in {"sunstone", "feather"}


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for pid, path in PATHS.items():
        for pr in PRIZES:
            if valid_combo(path, PRIZES[pr]):
                out.append((pid, pr))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _hero_name(params: StoryParams) -> str:
    return params.name


def _hero_type(params: StoryParams) -> str:
    return params.gender


def _parent_label(params: StoryParams) -> str:
    return params.parent


def intro(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"Folks in the valley told tales about {hero.id}, a {hero.pronoun('subject')} "
        f"so {hero.memes['trait_word']} that even the wind seemed to listen."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} kept an eye on "
        f"{hero.id}, because every tall tale starts with somebody small who wants "
        f"something mighty."
    )
    world.say(
        f"And mighty enough was the prize: {prize.phrase}, the kind of treasure "
        f"that could make a homely day shine like a lantern."
    )


def choose_quest(world: World, hero: Entity, path: Path, prize: Entity) -> None:
    hero.memes["yearning"] = hero.memes.get("yearning", 0.0) + 1
    world.say(
        f"{hero.id} wanted to cross {path.name} and bring home {prize.phrase}. "
        f"{hero.pronoun().capitalize()} said it was not just a walk; it was a quest."
    )
    world.say(
        f"The road was wide as a song and long as a promise, with dust on one side "
        f"and trouble on the other."
    )


def consult_instinct(world: World, hero: Entity, guide: Entity, path: Path) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    guide.memes["wisdom"] = guide.memes.get("wisdom", 0.0) + 1
    world.say(
        f"Then came Instinct, a trail-guide with a nose for the true way. "
        f'{guide.id} tapped the ground and said, "When the path splits, listen first, '
        f"then look.""
    )
    world.say(
        f"{hero.id} liked that advice, even though the {path.name} looked mean enough "
        f"to swallow a wagon wheel."
    )


def face_obstacle(world: World, hero: Entity, path: Path, prize: Entity) -> None:
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    hero.memes["gumption"] = hero.memes.get("gumption", 0.0) + 1
    world.say(
        f"At the edge of {path.name}, the ground turned red and fast, like an artery "
        f"pumping through the earth."
    )
    if path.barrier:
        world.say(
            f"A fallen gate blocked the straight way. The breeze rattled it like a dry bone."
        )
    world.say(
        f"{hero.id} tried the hard way first, because brave hearts often do."
    )


def turn_back_and_listen(world: World, hero: Entity, guide: Entity, path: Path) -> None:
    hero.memes["humility"] = hero.memes.get("humility", 0.0) + 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1)
    world.say(
        f"But the smart part of {hero.id} finally spoke up. {hero.pronoun().capitalize()} "
        f"stopped, took a breath, and listened to Instinct."
    )
    if path.barrier:
        world.say(
            f'Instinct said, "The gate is not a wall, only a stubborn mouth. '
            f"Find the hinge and ask it kindly.""
        )
    else:
        world.say(
            f'Instinct said, "The ground is kinder near the reeds. Walk there."'
        )


def solve(world: World, hero: Entity, guide: Entity, prize: Entity, path: Path) -> None:
    hero.meters["distance"] += path.miles
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    prize.owner = hero.id
    world.say(
        f"So {hero.id} did it the clever way. {hero.pronoun().capitalize()} found the hinge, "
        f"slipped through the gate, and crossed the artery without losing a bootlace."
    )
    world.say(
        f"At the far side waited {prize.phrase}, shining like morning caught in a jar."
    )
    world.say(
        f"{hero.id} lifted the prize high, and Instinct grinned as if the whole sky had just "
        f"remembered how to cheer."
    )
    world.say(
        f"That was the end of the quest: one careful step, one stubborn road, and one bright "
        f"treasure headed home."
    )


def build_world(params: StoryParams) -> World:
    if params.path not in PATHS:
        raise StoryError(f"Unknown path: {params.path}")
    if params.prize not in PRIZES:
        raise StoryError(f"Unknown prize: {params.prize}")

    path = PATHS[params.path]
    prize_cfg = PRIZES[params.prize]
    if not valid_combo(path, prize_cfg):
        raise StoryError("That path and prize do not make a reasonable quest.")

    world = World(path=path)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            meters={"distance": 0.0},
            memes={"trait_word": random.choice(TRAITS), "worry": 0.0, "trust": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Grandmother",
            kind="character",
            type=params.parent,
            label=params.parent,
            memes={"care": 1.0},
        )
    )
    guide = world.add(
        Entity(
            id="Instinct",
            kind="character",
            type="guide",
            label="Instinct",
            memes={"wisdom": 1.0},
        )
    )
    prize = world.add(
        Entity(
            id=prize_cfg.label,
            kind="thing",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=None,
            meters={"glow": 1.0},
        )
    )

    world.facts.update(hero=hero, parent=parent, guide=guide, prize=prize, path=path)

    intro(world, hero, parent, prize)
    world.para()
    choose_quest(world, hero, path, prize)
    consult_instinct(world, hero, guide, path)
    world.para()
    face_obstacle(world, hero, path, prize)
    turn_back_and_listen(world, hero, guide, path)
    world.para()
    solve(world, hero, guide, prize, path)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    path: Path = f["path"]
    return [
        f"Write a tall tale about {hero.id} on a quest across {path.name} for {prize.phrase}.",
        f"Tell a child-friendly story where Instinct helps {hero.id} cross an artery and find treasure.",
        f"Create a short adventure with a brave traveler, a tricky road, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    guide: Entity = f["guide"]
    prize: Entity = f["prize"]
    path: Path = f["path"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do?",
            answer=f"{hero.id} was trying to cross {path.name} on a quest and bring back {prize.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} choose the right way?",
            answer=f"Instinct helped {hero.id}. Instinct was the guide who told {hero.id} to listen first and then look.",
        ),
        QAItem(
            question=f"Why did the quest feel hard?",
            answer=f"It felt hard because {path.name} was long and tricky, and a fallen gate blocked the straight way.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {hero.id} had the prize and was heading home proud and cheerful instead of worried.",
        ),
        QAItem(
            question=f"Who watched over {hero.id}?",
            answer=f"{parent.label.capitalize()} watched over {hero.id} like a careful grown-up in a tall tale.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or solve a problem.",
        ),
        QAItem(
            question="What does instinct mean?",
            answer="Instinct means a quick inner feeling that helps someone choose or react without needing a long explanation.",
        ),
        QAItem(
            question="What is an artery?",
            answer="An artery is a blood vessel in the body that carries blood away from the heart.",
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
path_ok(P, R) :- path(P), prize(R), valid(P, R).
valid(P, R) :- path(P), prize(R), allowed(P, R).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, path in PATHS.items():
        lines.append(asp.fact("path", pid))
        if path.barrier:
            lines.append(asp.fact("barrier", pid))
    for rid, prize in PRIZES.items():
        lines.append(asp.fact("prize", rid))
    for pid, rid in valid_combos():
        lines.append(asp.fact("allowed", pid, rid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="boy")
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"], default="grandmother")
    ap.add_argument("--path", choices=sorted(PATHS), default=None)
    ap.add_argument("--prize", choices=sorted(PRIZES), default=None)
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
    path = args.path or rng.choice(sorted(PATHS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    if not valid_combo(PATHS[path], PRIZES[prize]):
        raise StoryError("That path and prize do not make a reasonable quest.")
    name = args.name or "Abcdefghijklmnop"
    gender = args.gender
    parent = args.parent
    return StoryParams(name=name, gender=gender, parent=parent, path=path, prize=prize)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {ent.id:14} ({ent.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


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
    StoryParams(name="Abcdefghijklmnop", gender="boy", parent="grandmother", path="artery", prize="sunstone"),
    StoryParams(name="Mira", gender="girl", parent="mother", path="ridge", prize="feather"),
    StoryParams(name="Tobin", gender="boy", parent="grandfather", path="marsh", prize="sunstone"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid quest combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: quest on {p.path} for {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
