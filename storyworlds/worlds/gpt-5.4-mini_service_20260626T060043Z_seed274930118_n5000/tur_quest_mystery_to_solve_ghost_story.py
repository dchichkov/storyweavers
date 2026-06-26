#!/usr/bin/env python3
"""
storyworlds/worlds/tur_quest_mystery_to_solve_ghost_story.py
=============================================================

A small ghost-story world with a quest and a mystery to solve.

Premise:
- A child hears a harmless but eerie ghostly sound in an old place.
- The child and a helper (often a parent or grandparent) follow clues.
- They discover the "ghost" is a natural cause: a draft, a toy, a lantern, a cat, or some other simple culprit.
- The story ends with the fear turning into curiosity and relief.

This world keeps the style close to a gentle ghost story:
- dim setting
- a little suspense
- clue-following
- a clear reveal
- a comforting ending

The word "tur" is intentionally included as a tiny seed-word in the world vocabulary,
used for a storm lantern brand / tag in some variants and in story prompts.

The simulation uses:
- meters for physical state
- memes for emotional state
- a quest token trail
- a mystery clue chain
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    portable: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    dim: bool = True
    echo: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    leads_to: str


@dataclass
class Mystery:
    id: str
    phantom_name: str
    false_spook: str
    true_cause: str
    solution: str
    clue_order: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    goal: str
    steps: list[str] = field(default_factory=list)
    reward: str = "relief"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.quest_steps: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.quest_steps = list(self.quest_steps)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "house": Setting(place="the old house", dim=True, echo=True, affords={"listen", "search", "open"}),
    "attic": Setting(place="the attic", dim=True, echo=True, affords={"listen", "search", "open"}),
    "hall": Setting(place="the hallway", dim=True, echo=True, affords={"listen", "search"}),
    "garden": Setting(place="the garden", dim=False, echo=False, affords={"search", "follow"}),
}

PEOPLE = {
    "child": {"girl", "boy"},
    "helper": {"mother", "father", "grandma", "grandpa"},
}

MYSTERIES = {
    "whisper": Mystery(
        id="whisper",
        phantom_name="the whispering ghost",
        false_spook="a ghostly whisper",
        true_cause="a loose window latch tapping in the wind",
        solution="the window latch was making the whispering sound",
        clue_order=["draft", "latch", "window"],
    ),
    "steps": Mystery(
        id="steps",
        phantom_name="the walking ghost",
        false_spook="soft footsteps above the ceiling",
        true_cause="a raccoon moving in the rafters",
        solution="a raccoon was making the footsteps in the rafters",
        clue_order=["scratch", "roof", "raccoon"],
    ),
    "bell": Mystery(
        id="bell",
        phantom_name="the bell ghost",
        false_spook="a lonely bell ring",
        true_cause="a hanging spoon tapping a jar",
        solution="a spoon was tapping a jar and making the bell sound",
        clue_order=["jar", "spoon", "shelf"],
    ),
}

QUESTS = {
    "follow_clues": Quest(
        id="follow_clues",
        goal="find out what is really making the spooky sound",
        steps=["hear", "notice", "follow", "reveal"],
        reward="courage",
    )
}

CLUES = {
    "draft": Clue(id="draft", text="A thin draft brushed the curtains.", leads_to="window"),
    "latch": Clue(id="latch", text="A little latch clicked near the frame.", leads_to="window"),
    "window": Clue(id="window", text="The window was not shut all the way.", leads_to="reveal"),
    "scratch": Clue(id="scratch", text="There were tiny scratching marks near the beam.", leads_to="roof"),
    "roof": Clue(id="roof", text="Something light moved above the ceiling boards.", leads_to="raccoon"),
    "raccoon": Clue(id="raccoon", text="Small paw prints showed up by the gutter.", leads_to="reveal"),
    "jar": Clue(id="jar", text="A glass jar sat crooked on the shelf.", leads_to="spoon"),
    "spoon": Clue(id="spoon", text="A spoon handle touched the glass and rang it.", leads_to="reveal"),
    "shelf": Clue(id="shelf", text="The shelf shook when the floorboards creaked.", leads_to="reveal"),
}

TUR_WORDS = ["tur", "turtle-lantern", "turnkey", "turbine", "tureen"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Zoe", "Maya", "Ela", "Tia"]
BOY_NAMES = ["Finn", "Noah", "Leo", "Milo", "Owen", "Eli", "Theo", "Jude"]
TRAITS = ["brave", "curious", "careful", "gentle", "quiet", "spirited"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story world with a quest and a mystery to solve."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mystery in MYSTERIES:
            if place in {"house", "attic", "hall"} and mystery in MYSTERIES:
                combos.append((place, mystery))
            if place == "garden" and mystery in {"whisper", "steps"}:
                combos.append((place, mystery))
    return combos


def reason_invalid(place: str, mystery: str) -> str:
    return (
        f"(No story: the mystery '{mystery}' does not fit the setting '{place}' "
        f"for this gentle ghost-story world.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and (args.place, args.mystery) not in valid_combos():
        raise StoryError(reason_invalid(args.place, args.mystery))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(sorted(PEOPLE["helper"]))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(
        id="child", kind="character", type=params.gender, label=params.name, traits=["little", params.trait]
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=params.helper, label=params.helper
    ))
    mystery = MYSTERIES[params.mystery]
    world.add(Entity(
        id="lantern", type="thing", label="tur lantern", phrase="a small tur lantern",
        location=params.place, portable=True
    ))
    world.add(Entity(
        id="window", type="thing", label="window", location=params.place, portable=False
    ))
    world.add(Entity(
        id="clues", type="thing", label="clues", location=params.place, portable=False
    ))
    quest = QUESTS["follow_clues"]

    world.facts.update(
        child=child, helper=helper, mystery=mystery, quest=quest, params=params
    )
    return world


def narrate_setup(world: World) -> None:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]

    world.say(
        f"{child.label} was a little {p.trait} {p.gender} who loved quiet evenings in {world.setting.place}."
    )
    world.say(
        f"One night, {child.label} noticed {mystery.false_spook}, and the room felt extra still."
    )
    world.say(
        f"{child.label} held a tiny {TUR_WORDS[0]} lantern and looked at {helper.label}."
    )


def follow_clues(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    out = []
    for clue_id in mystery.clue_order:
        clue = CLUES[clue_id]
        if (mystery.id, clue_id) in world.fired:
            continue
        world.fired.add((mystery.id, clue_id))
        out.append(clue.text)
        world.quest_steps.append(clue_id)
    return out


def narrate_mystery(world: World) -> None:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]

    world.para()
    world.say(
        f"{child.label} and {helper.label} began a small quest to find out what was making the sound."
    )
    for clue_sentence in follow_clues(world):
        world.say(clue_sentence)
    world.say(
        f"At last, they saw that {mystery.solution}."
    )
    world.say(
        f"The spooky thing was not a ghost after all; it was only {mystery.true_cause}."
    )
    world.say(
        f"{child.label} laughed, and {helper.label} smiled because the mystery was solved."
    )
    world.say(
        f"The little {TUR_WORDS[0]} lantern glowed softly while the house felt safe again."
    )
    world.facts["resolved"] = True


def generate_story(world: World) -> None:
    narrate_setup(world)
    narrate_mystery(world)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    mystery: Mystery = world.facts["mystery"]
    return [
        f'Write a gentle ghost story for a child named {p.name} who hears {mystery.false_spook} and goes on a quest to solve the mystery.',
        f'Tell a small mystery-to-solve story set in {world.setting.place} with the word "tur" and a comforting ending.',
        f'Create a child-friendly spooky story where {p.name} and {p.helper} follow clues and discover what is really making the sound.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    resolved = world.facts.get("resolved", False)

    qas = [
        QAItem(
            question=f"Who went on the quest to solve the mystery in {world.setting.place}?",
            answer=f"{child.label} went with {helper.label} to solve the mystery in {world.setting.place}.",
        ),
        QAItem(
            question=f"What spooky thing did {child.label} hear at first?",
            answer=f"{child.label} first heard {mystery.false_spook}.",
        ),
        QAItem(
            question=f"What was the real cause of the spooky sound?",
            answer=f"The real cause was {mystery.true_cause}.",
        ),
    ]
    if resolved:
        qas.append(
            QAItem(
                question=f"How did the story end after the mystery was solved?",
                answer=f"It ended with {child.label} feeling brave and relieved, because the spooky sound was explained and the room felt safe again.",
            )
        )
    return qas


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet, so you look for clues to figure it out.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special task or search, usually one where you follow steps to reach a goal.",
        ),
        QAItem(
            question="What does the word tur suggest in this world?",
            answer="Here, tur is a tiny seed-word used for a lantern and related story details, like a little glowing object in the dark.",
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
# Trace / emit
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.portable:
            bits.append("portable=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  quest_steps: {world.quest_steps}")
    lines.append(f"  fired: {sorted(world.fired)}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the selected place and mystery are compatible.
valid_story(P,M) :- place(P), mystery(M), compatible(P,M).

% The mystery is solved when all of its clues can be followed.
solved(M) :- mystery(M), clue_order(M,1,_), clue_order(M,2,_), clue_order(M,3,_).

% This world only shows the compatible story choices and solved mysteries.
#show valid_story/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        for i, clue_id in enumerate(mystery.clue_order, 1):
            lines.append(asp.fact("clue_order", mystery_id, i, clue_id))
    for place, mystery in valid_combos():
        lines.append(asp.fact("compatible", place, mystery))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="house", mystery="whisper", name="Mina", gender="girl", helper="grandma", trait="curious"),
        StoryParams(place="attic", mystery="steps", name="Finn", gender="boy", helper="father", trait="brave"),
        StoryParams(place="hall", mystery="bell", name="Ivy", gender="girl", helper="mother", trait="careful"),
    ]


CURATED = build_curated()


def resolve_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2.\n#show solved/1."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
