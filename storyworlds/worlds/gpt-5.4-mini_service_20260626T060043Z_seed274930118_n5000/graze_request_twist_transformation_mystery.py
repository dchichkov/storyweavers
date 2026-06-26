#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/graze_request_twist_transformation_mystery.py
==============================================================================================================

A small mystery storyworld with a clue trail, a request, a twist, and a
transformation.

Seed image:
- A child finds a tiny graze on a garden gate.
- A folded request note is missing from the potting bench.
- The trail seems suspicious at first.
- The final reveal changes what the child thinks the place, and the suspect,
  are for.

This world keeps the prose concrete and state-driven: the story is assembled
from a simulated world model, not from a frozen paragraph.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str
    indoor: bool = False
    smells: str = ""


@dataclass
class Clue:
    id: str
    label: str
    source: str
    trail: str
    twist: str
    transformation: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, smells="green and damp"),
    "greenhouse": Setting(place="the greenhouse", indoor=True, smells="warm and leafy"),
    "porch": Setting(place="the porch", indoor=False, smells="like rain on wood"),
}

CLUES = {
    "graze": Clue(
        id="graze",
        label="a tiny graze",
        source="the gate latch had scraped the paint",
        trail="thin white scratches on the metal",
        twist="the scrape was not from a fight at all",
        transformation="the gate had been slid open carefully, not shoved",
    ),
    "request": Clue(
        id="request",
        label="a folded request note",
        source="someone had left a polite request on the bench",
        trail="the note smelled faintly of mint tea",
        twist="the request was not for treasure, but for help",
        transformation="the missing paper had not been stolen; it had been carried off for a purpose",
    ),
}

GIRL_NAMES = ["Mina", "Iris", "Nora", "Lena", "Pia", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Owen", "Eli", "Finn", "Jude"]
TRAITS = ["quiet", "curious", "careful", "brave", "patient", "sharp-eyed"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is valid in a setting when its trail can exist there.
valid_clue(P, C) :- place(P), clue(C), clue_in(P, C).

% A mystery needs both a clue trail and a request, and the twist must fit.
valid_mystery(P, C) :- valid_clue(P, C), request_present(P), twist_fits(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_in", "garden", cid))
        lines.append(asp.fact("clue_in", "greenhouse", cid))
        lines.append(asp.fact("clue_in", "porch", cid))
        lines.append(asp.fact("twist_fits", cid))
    lines.append(asp.fact("request_present", "garden"))
    lines.append(asp.fact("request_present", "greenhouse"))
    lines.append(asp.fact("request_present", "porch"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_mystery/2."))
    return sorted(set(asp.atoms(model, "valid_mystery")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            combos.append((place, clue))
    return combos


def explain_rejection(place: str, clue: str) -> str:
    return f"(No story: the mystery at {place} cannot use clue '{clue}' here.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, clue: Clue) -> dict[str, bool]:
    sim = world.copy()
    sim.facts["found"] = clue.id
    sim.facts["suspected"] = "pet"
    return {"twist": True, "transformation": True}


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    clue = CLUES[params.clue]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"curiosity": 1.0},
        memes={"calm": 1.0, "suspicion": 0.0, "relief": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={"patience": 1.0},
        memes={"worry": 0.0, "warmth": 1.0},
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="thing",
        type="goat",
        label="the goat",
        phrase="a small white goat",
        meters={"graze": 0.0},
        memes={"shy": 1.0},
    ))
    note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="the note",
        phrase="a folded request note",
        owner=params.hero_name,
    ))

    # Act 1: setup.
    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} {hero.type} who liked to notice small things."
    )
    world.say(
        f"On that day, {world.setting.place} smelled {world.setting.smells}, and {hero.id} found {clue.label} by the gate."
    )
    world.say(
        f"Near the potting bench, {hero.pronoun('possessive')} eyes also caught {note.label}, which looked like it had been waiting for someone."
    )

    # Act 2: mystery.
    world.para()
    hero.memes["suspicion"] += 1.0
    parent.memes["worry"] += 1.0
    world.say(
        f"{hero.id} followed the {clue.trail} and wondered who had moved quietly enough to leave them behind."
    )
    world.say(
        f"The {clue.source}. That made the place feel odd, as if it were hiding a secret."
    )
    world.say(
        f"{hero.id} thought the goat might be guilty, because {suspect.label} had muddy hooves and a soft, secretive way of standing still."
    )

    # Twist and transformation.
    world.para()
    world.say(f"Then came the twist: {clue.twist}.")
    suspect.meters["graze"] += 1.0
    suspect.memes["shy"] = 0.0
    suspect.memes["helpful"] = 1.0
    world.say(
        f"The goat had only grazed along the herbs while carrying the note in its ribbon collar."
    )
    world.say(
        f"That changed everything: {clue.transformation}, and the shy goat was really the gardener's messenger."
    )

    # Act 3: resolution.
    world.para()
    hero.memes["suspicion"] = 0.0
    hero.memes["relief"] += 1.0
    parent.memes["worry"] = 0.0
    world.say(
        f"{hero.id} opened the note and saw a simple request for fresh mint, because the gardener needed it for tea."
    )
    world.say(
        f"At the end, {hero.id} tucked the note into {hero.pronoun('possessive')} pocket, patted {suspect.label}, and smiled at the little mystery that had turned into a kind one."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        suspect=suspect,
        note=note,
        clue=clue,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    return [
        f"Write a short children's mystery story that includes the words '{clue.id}' and 'request'.",
        f"Tell a story about {hero.id} finding {clue.label}, following a clue, and learning a surprising truth.",
        "Write a gentle mystery with a twist and a transformation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    suspect = f["suspect"]
    return [
        QAItem(
            question=f"What did {hero.id} notice first in the story?",
            answer=f"{hero.id} first noticed {clue.label} by the gate.",
        ),
        QAItem(
            question="What made the child think the goat might be guilty?",
            answer=f"{suspect.label} had muddy hooves and stood near the clues, so it looked suspicious at first.",
        ),
        QAItem(
            question="What was the real reason for the request note?",
            answer="The note was a polite request for fresh mint for tea, not a warning or a theft note.",
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer="The twist was that the goat was not stealing anything; it was carrying the note as a messenger.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The mystery changed from suspicious to kind, and the shy goat became a helpful messenger in the child's mind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a graze?",
            answer="A graze is a small scrape or light scratch on a surface or on skin.",
        ),
        QAItem(
            question="What is a request?",
            answer="A request is a polite ask for something or for someone to do something.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes you rethink what you believed before.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state or feeling into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with graze, request, twist, and transformation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.place and args.clue:
        if (args.place, args.clue) not in combos:
            raise StoryError(explain_rejection(args.place, args.clue))
    choices = [c for c in combos
               if (not args.place or c[0] == args.place)
               and (not args.clue or c[1] == args.clue)]
    if not choices:
        raise StoryError("(No valid mystery matches the given options.)")
    place, clue = rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, clue=clue, hero_name=name, hero_type=gender, parent_type=parent)


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
        print(asp_program("#show valid_mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible mysteries:\n")
        for place, clue in combos:
            print(f"  {place:11} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, clue in valid_combos():
            params = StoryParams(
                place=place,
                clue=clue,
                hero_name="Mina",
                hero_type="girl",
                parent_type="mother",
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
