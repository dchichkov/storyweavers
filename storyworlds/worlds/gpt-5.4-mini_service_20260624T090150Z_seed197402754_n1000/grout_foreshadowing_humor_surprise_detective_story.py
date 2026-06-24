#!/usr/bin/env python3
"""
storyworlds/worlds/grout_foreshadowing_humor_surprise_detective_story.py
========================================================================

A small detective-style storyworld about grout, with foreshadowing, humor,
and a surprise ending.

Premise:
- A child notices a strange crack and some dusty grout in a tiled room.
- A careful little investigation reveals a harmless cause, a comic clue, and a
  hidden surprise: the "mystery" is really a loose toy hiding behind the sink.

The world is simulation-driven: clues, observations, and emotional beats are
tracked in state, then narrated from those state changes.

This file follows the Storyweavers contract:
- standalone stdlib script
- eager import of results.py for QAItem, StoryError, StorySample
- lazy import of asp.py inside ASP helpers only
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "woman", "detective"}
        masculine = {"boy", "father", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old bathroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    hero_name: str
    hero_gender: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bathroom": Setting(place="the old bathroom", affords={"grout"}),
    "kitchen": Setting(place="the small kitchen", affords={"grout"}),
}

CLUES = {
    "grout": {
        "label": "grout",
        "phrase": "the cracked grout between the tiles",
        "smudge": "dusty",
    }
}

CULPRITS = {
    "toy": {
        "label": "toy frog",
        "hide": "behind the sink",
        "surprise": "a tiny green toy frog",
        "reason": "it had rolled away during playtime",
    },
    "marble": {
        "label": "glass marble",
        "hide": "under the cabinet",
        "surprise": "a shiny blue marble",
        "reason": "it had slipped from a pocket",
    },
}

GIRL_NAMES = ["Mina", "Ruby", "Ella", "Nora", "Lena", "Tia"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Milo", "Eli", "Noah"]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def detect_reasonable(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.culprit not in CULPRITS:
        raise StoryError("Unknown culprit.")


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="girl" if params.hero_gender == "girl" else "boy",
        label=params.hero_name,
        meters={"curiosity": 0.0},
        memes={"wonder": 0.0, "worry": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="mother",
        label=params.helper_name,
        meters={"patience": 1.0},
        memes={"calm": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=CLUES[params.clue]["label"],
        phrase=CLUES[params.clue]["phrase"],
        meters={"seen": 0.0, "dust": 1.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="thing",
        type="thing",
        label=CULPRITS[params.culprit]["label"],
        phrase=CULPRITS[params.culprit]["surprise"],
        meters={"hidden": 1.0},
    ))

    # Act 1: setup + foreshadowing.
    world.say(
        f"{hero.id} was a little detective who loved finding clues in quiet places."
    )
    world.say(
        f"One afternoon, {hero.id} noticed {clue.phrase} in {setting.place}."
    )
    world.say(
        f"The dust around it looked like a tiny gray cloud, which felt like a clue "
        f"that wanted to be noticed."
    )
    hero.meters["curiosity"] += 1.0
    hero.memes["wonder"] += 1.0
    clue.meters["seen"] += 1.0
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["clue"] = clue
    world.facts["culprit"] = culprit

    # Act 2: investigation with humor.
    world.para()
    world.say(
        f"{hero.id} whispered, 'This case smells like grout,' because the crack ran "
        f"along the tiles like a wiggly little road."
    )
    world.say(
        f"{helper.label} knelt down and said, 'If the grout could talk, it would probably "
        f"complain about being stepped on all day.'"
    )
    hero.memes["worry"] += 0.5
    helper.memes["calm"] += 0.5
    world.facts["foreshadow"] = "grout crack"

    # Surprise turn.
    world.para()
    world.say(
        f"When {hero.id} peeked behind the sink, the mystery gave a cheerful surprise: "
        f"{culprit.phrase}."
    )
    world.say(
        f"It had been hiding {CULPRITS[params.culprit]['hide']} the whole time."
    )
    world.say(
        f"{hero.id} laughed and said, 'I thought the grout was hiding a giant secret, "
        f"but it was only a small runaway thing!'"
    )
    hero.memes["joy"] += 1.0
    hero.memes["worry"] = 0.0
    culprit.meters["hidden"] = 0.0
    world.facts["surprise"] = culprit.phrase

    # Resolution.
    world.para()
    world.say(
        f"{helper.label} smiled and explained that the crack was just old grout, "
        f"not a danger, and the lost {CULPRITS[params.culprit]['label']} had simply "
        f"{CULPRITS[params.culprit]['reason']}."
    )
    world.say(
        f"{hero.id} put the little toy on the counter, and the bathroom felt neat and "
        f"friendly again, with the grout still there and the mystery solved."
    )
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Entity = f["clue"]
    culprit: Entity = f["culprit"]
    return [
        f"Write a short detective story for a young child about {hero.id} and {clue.label}.",
        f"Tell a story where a child notices {clue.phrase} and discovers a funny surprise.",
        f"Write a gentle mystery about grout, a hidden toy, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue: Entity = f["clue"]
    culprit: Entity = f["culprit"]
    return [
        QAItem(
            question=f"What clue did {hero.id} notice?",
            answer=f"{hero.id} noticed {clue.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} think the case was important?",
            answer=(
                f"{hero.id} thought it was important because the cracked grout looked "
                f"like a real mystery, even though it turned out to be harmless."
            ),
        ),
        QAItem(
            question=f"What was the surprise behind the sink?",
            answer=f"The surprise was {culprit.phrase}, hiding {CULPRITS[world.facts['culprit'].id]['hide']}.",
        ),
        QAItem(
            question=f"How did {helper.id} help solve the mystery?",
            answer=(
                f"{helper.label} helped by staying calm, making a funny remark about grout, "
                f"and helping {hero.id} look in the right place."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is grout?",
            answer="Grout is the material that fills the little spaces between tiles.",
        ),
        QAItem(
            question="Why do people look carefully for clues in a mystery?",
            answer="People look carefully because clues can show what really happened.",
        ),
        QAItem(
            question="Why can a hidden toy cause a surprise?",
            answer="A hidden toy can cause a surprise because it may look like something mysterious before you find it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
story_ok(P, C, U) :- place(P), clue(C), culprit(U).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for uid in CULPRITS:
        lines.append(asp.fact("culprit", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_ok() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {(p, c, u) for p in SETTINGS for c in CLUES for u in CULPRITS}
    cl = set(asp_ok())
    if cl == py:
        print(f"OK: ASP matches Python ({len(cl)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("Only in ASP:", sorted(cl - py))
    print("Only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective storyworld about grout, clues, and a surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.culprit and args.culprit not in CULPRITS:
        raise StoryError("Unknown culprit.")

    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or "grout"
    culprit = args.culprit or rng.choice(list(CULPRITS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or choose_name(gender, rng)
    helper_name = args.helper_name or rng.choice(["Mom", "Dad"])
    return StoryParams(
        place=place,
        clue=clue,
        culprit=culprit,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    detect_reasonable(params)
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


CURATED = [
    StoryParams(place="bathroom", clue="grout", culprit="toy", hero_name="Mina", hero_gender="girl", helper_name="Mom"),
    StoryParams(place="kitchen", clue="grout", culprit="marble", hero_name="Leo", hero_gender="boy", helper_name="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/3."))
        combos = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(combos)} compatible story combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
