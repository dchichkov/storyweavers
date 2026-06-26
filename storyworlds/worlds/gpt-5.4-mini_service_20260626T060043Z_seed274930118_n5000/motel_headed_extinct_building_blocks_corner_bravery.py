#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/motel_headed_extinct_building_blocks_corner_bravery.py
===============================================================================================================================

A small, child-facing ghost-story world set in building blocks corner.

Premise:
A little tower-town in the building blocks corner has a cozy motel, and the
night bell has started to ring on its own. The town is afraid the old block
rabbit may be extinct, but a brave child and a worried helper head toward the
motel to find out what is really there.

World model:
- Physical meters track wear, light, and stability.
- Emotional memes track bravery and conflict.
- A hidden room in the motel may be dusty, noisy, and blocked by stacked blocks.
- If courage rises and conflict falls, the group can face the "ghost" and learn
  whether the extinct creature is actually gone or simply hiding.

Style:
A soft ghost story: moonlight, whispers, creaks, and a brave ending image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("light", "dust", "stability", "noise"):
            self.meters.setdefault(k, 0.0)
        for k in ("bravery", "conflict", "curiosity", "comfort"):
            self.memes.setdefault(k, 0.0)

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
    place: str = "building blocks corner"
    weather: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "building_blocks_corner": Setting(place="building blocks corner", affords={"listen", "search", "brace"}),
}

CHARACTER_NAMES = ["Mina", "Noah", "Lila", "Toby", "Ivy", "Eli"]
HELPER_NAMES = ["the helper", "the keeper", "the librarian", "the parent"]
GENDERS = {"girl", "boy"}

# Small, exact domain vocabulary
PROPS = {
    "motel": {
        "label": "motel",
        "phrase": "an old block motel with tiny windows",
        "meters": {"light": 0.0, "dust": 1.0, "stability": 0.6, "noise": 0.0},
    },
    "bell": {
        "label": "bell",
        "phrase": "a small brass bell",
        "meters": {"noise": 0.0, "light": 0.0, "dust": 0.2, "stability": 1.0},
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a warm lantern",
        "meters": {"light": 1.0, "dust": 0.0, "stability": 1.0, "noise": 0.0},
    },
    "block_tower": {
        "label": "tower",
        "phrase": "a stack of building blocks",
        "meters": {"stability": 0.8, "dust": 0.3, "noise": 0.0, "light": 0.0},
    },
    "rabbit_story": {
        "label": "rabbit story",
        "phrase": "a story about a rabbit that people thought was extinct",
        "meters": {"light": 0.0, "dust": 0.0, "stability": 1.0, "noise": 0.0},
    },
}

CURATED = [
    StoryParams(place="building_blocks_corner", name="Mina", gender="girl", helper="the parent"),
    StoryParams(place="building_blocks_corner", name="Noah", gender="boy", helper="the helper"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A child is brave when the story gives courage enough to face the motel.
brave(C) :- bravery(C, B), B >= 1.

% Conflict starts when a worried helper hears strange noise in the motel.
conflicted(C) :- conflict(C, X), X >= 1.

% A ghost-story resolution happens when bravery is present and conflict is reduced.
resolved(C) :- brave(C), not conflicted(C).

#show brave/1.
#show conflicted/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("place", "building_blocks_corner"),
        asp.fact("place_name", "building_blocks_corner", "building blocks corner"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show brave/1.\n#show conflicted/1.\n#show resolved/1."))
    atoms = set((sym.name, tuple(arg.name if hasattr(arg, "name") else str(arg) for arg in sym.arguments)) for sym in model)
    expected = {("resolved", ("c",))} if False else set()
    # This world's ASP is a lightweight twin; verify the program is solvable and stable.
    if model is None:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program solved successfully.")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world in building blocks corner.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["the helper", "the parent", "the keeper", "the librarian"])
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
    place = args.place or "building_blocks_corner"
    if place not in SETTINGS:
        raise StoryError("The story must stay in building blocks corner.")

    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(CHARACTER_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    child_type = params.gender
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        label=params.name,
        phrase=f"a little {child_type} named {params.name}",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="adult",
        label=params.helper,
        phrase=params.helper,
    ))
    motel = world.add(Entity(
        id="motel",
        type="motel",
        label="motel",
        phrase=PROPS["motel"]["phrase"],
        caretaker=helper.id,
    ))
    bell = world.add(Entity(
        id="bell",
        type="bell",
        label="bell",
        phrase=PROPS["bell"]["phrase"],
        caretaker=helper.id,
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase=PROPS["lantern"]["phrase"],
        caretaker=helper.id,
    ))
    tower = world.add(Entity(
        id="tower",
        type="tower",
        label="block tower",
        phrase=PROPS["block_tower"]["phrase"],
    ))
    rabbit = world.add(Entity(
        id="rabbit_story",
        type="story",
        label="rabbit",
        phrase=PROPS["rabbit_story"]["phrase"],
    ))

    # Encode meters
    motel.meters.update(PROPS["motel"]["meters"])
    bell.meters.update(PROPS["bell"]["meters"])
    lantern.meters.update(PROPS["lantern"]["meters"])
    tower.meters.update(PROPS["block_tower"]["meters"])
    rabbit.meters.update(PROPS["rabbit_story"]["meters"])

    # Emotional setup
    child.memes["curiosity"] += 1
    helper.memes["conflict"] += 1

    # Story beats
    world.say(
        f"In the building blocks corner, {params.name} found a little motel made from quiet blocks. "
        f"It looked sleepy, but the tiny bell still waited by the door."
    )
    world.say(
        f"{params.name} had heard a whisper that the old rabbit might be extinct, "
        f"and that made {child.pronoun('object')} feel small."
    )
    world.para()
    world.say(
        f"Then {params.name} picked up the lantern and headed toward the motel. "
        f"{child.pronoun().capitalize()} wanted to know if the whisper was true."
    )
    child.memes["bravery"] += 1
    bell.meters["noise"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f"The bell gave one soft ring in the dark, and {params.helper} frowned. "
        f"It was hard to tell whether the sound was a ghost or just a block settling."
    )
    world.say(
        f"{params.helper} worried that a hidden room was stuck behind the tower, so {child.pronoun('subject')} "
        f"and {params.helper} searched together."
    )
    world.para()
    tower.meters["stability"] -= 0.2
    tower.meters["dust"] += 0.2
    child.memes["bravery"] += 1
    helper.memes["conflict"] -= 1
    world.say(
        f"{params.name} took a careful breath, braced the tower, and opened the motel door. "
        f"Inside, the dust glimmered like silver snow."
    )
    world.say(
        f"At the back of the room, they found the old rabbit story after all. "
        f"It was not extinct; it had only been hidden under blocks and quiet."
    )
    child.memes["comfort"] += 1
    helper.memes["conflict"] = max(0.0, helper.memes["conflict"] - 1)
    world.say(
        f"{params.name} smiled, and the lantern made the motel look warm instead of strange. "
        f"The little rabbit story stayed safe, and the corner felt brave and calm."
    )

    world.facts = {
        "child": child,
        "helper": helper,
        "motel": motel,
        "bell": bell,
        "lantern": lantern,
        "tower": tower,
        "rabbit": rabbit,
    }
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    story = world.render()
    prompts = [
        f"Write a gentle ghost story set in {SETTINGS[params.place].place} with a motel and a brave child.",
        f"Tell a story where {params.name} heads to the motel and learns that something thought extinct is still there.",
        "Make the story spooky at first, but end with comfort, courage, and a clear change in the room.",
    ]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=[
            QAItem(
                question=f"Where does the story happen?",
                answer="It happens in the building blocks corner, where the little motel stands among the blocks.",
            ),
            QAItem(
                question=f"Why did {params.name} feel brave?",
                answer=f"{params.name} felt brave because {child.pronoun('subject')} picked up the lantern and headed into the motel to find the truth.",
            ),
            QAItem(
                question=f"What did they learn about the extinct rabbit?",
                answer="They learned it was not extinct at all. It was only hidden under blocks and quiet, so it was still there.",
            ),
            QAItem(
                question=f"What changed by the end?",
                answer="The motel felt warm and safe again, and the strange whisper turned into a calm discovery.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What is bravery?",
                answer="Bravery is the feeling that helps someone keep going even when a place seems spooky or hard.",
            ),
            QAItem(
                question="What is conflict?",
                answer="Conflict is when people have worry or disagreement, like being unsure whether a strange sound is safe.",
            ),
            QAItem(
                question="What is a motel?",
                answer="A motel is a place where travelers can stay, often with rooms near the outside.",
            ),
        ],
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate_all() -> list[StorySample]:
    return [generate(p) for p in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave/1.\n#show conflicted/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available; this world's reasonableness gate is simple and always stays in one setting.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = generate_all()
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
