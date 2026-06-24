#!/usr/bin/env python3
"""
storyworlds/worlds/bccbccb_roll_tangerine_twist_mystery.py
===========================================================

A small mystery storyworld about a missing tangerine, a rolling clue, and a
twist that re-frames the case.

Premise:
- A child detective notices a tangerine has gone missing.
- A few ordinary objects become clues in a quiet, child-friendly mystery.
- The ending reveals a harmless twist: the "missing" thing was moved, not lost.

The world is intentionally tiny and constraint-checked. It supports a few
carefully selected variants, each with a complete beginning, middle turn, and
resolution image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    hidden: bool = False
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
    indoor: bool
    mood: str


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    can_roll: bool = False
    can_hide: bool = False
    can_be_moved: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    clue: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, mood="quiet"),
    "hall": Setting(place="the hall", indoor=True, mood="still"),
    "garden_room": Setting(place="the garden room", indoor=True, mood="soft"),
}

CLUES = {
    "tangerine": Clue(
        id="tangerine",
        label="tangerine",
        phrase="a bright tangerine in a small dish",
        kind="fruit",
        can_roll=False,
        can_hide=True,
        can_be_moved=True,
        tags={"fruit", "orange", "tangerine"},
    ),
    "tangerine_peel": Clue(
        id="tangerine_peel",
        label="tangerine peel",
        phrase="a strip of tangerine peel",
        kind="peel",
        can_roll=True,
        can_hide=False,
        can_be_moved=True,
        tags={"fruit", "orange", "tangerine", "roll"},
    ),
    "button": Clue(
        id="button",
        label="button",
        phrase="a little blue button",
        kind="button",
        can_roll=True,
        can_hide=False,
        can_be_moved=True,
        tags={"roll", "small"},
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Tess", "Lina", "Pia", "Sage"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Noah", "Luca"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue can roll if it is marked rollable.
rollable(C) :- clue(C), can_roll(C).

% A clue can be a plausible moving clue if it can be moved.
movable(C) :- clue(C), can_be_moved(C).

% A mystery twist is valid if a clue rolls and another clue about the same
% theme exists; this captures the "rolling clue" + tangerine set.
twist_valid(C) :- roll_clue(C), theme(tangerine, C).

% A story is reasonable if the chosen clue is movable and the setting is indoor.
valid_story(Place, Clue) :- setting(Place), indoor(Place), clue(Clue), movable(Clue).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.can_roll:
            lines.append(asp.fact("can_roll", cid))
            lines.append(asp.fact("roll_clue", cid))
        if c.can_hide:
            lines.append(asp.fact("can_hide", cid))
        if c.can_be_moved:
            lines.append(asp.fact("can_be_moved", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("theme", t, cid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        if not setting.indoor:
            continue
        for clue_id, clue in CLUES.items():
            if clue.can_be_moved:
                combos.append((place, clue_id))
    return combos


def explain_rejection(place: str, clue_id: str) -> str:
    clue = CLUES[clue_id]
    if not SETTINGS[place].indoor:
        return f"(No story: this mystery is meant for an indoor room, not {SETTINGS[place].place}.)"
    if not clue.can_be_moved:
        return f"(No story: the {clue.label} is not a good moving clue for this mystery.)"
    return "(No story: that combination is not available.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def pronoun_name(name: str, gender: str) -> str:
    return name

def is_tangerine_related(clue: Clue) -> bool:
    return "tangerine" in clue.tags or clue.id == "tangerine"

def scene_opening(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    world.say(
        f"{detective.id} was a small detective who noticed every quiet thing in {world.setting.place}."
    )
    world.say(
        f"{detective.pronoun().capitalize()} and {helper.id} liked simple mysteries, especially ones with one bright clue."
    )
    if clue.id == "tangerine":
        world.say(
            f"On the table sat a tangerine in a dish, round and orange, like a tiny sun."
        )
    else:
        world.say(
            f"On the table lay a tangerine peel, and nearby a little note that read bccbccb."
        )

def clue_loss(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    detective.memes["worry"] = detective.memes.get("worry", 0) + 1
    world.para()
    world.say(
        f"Then the tangerine was not where it had been before, and {detective.id} frowned."
    )
    world.say(
        f"'{clue.label.capitalize()}?' {detective.id} whispered. 'That does not belong there anymore.'"
    )

def follow_roll(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    world.say(
        f"{helper.id} bent down and pointed to a small trail near the rug."
    )
    world.say(
        f"It looked like something had rolled softly under the table, as if the room had rolled the clue on purpose."
    )

def twist_reveal(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    world.para()
    world.say(
        f"{detective.id} looked under the table and found the tangerine in a bowl beside a napkin."
    )
    world.say(
        f"It had not been stolen at all; {helper.id} had moved it there so it would not bruise."
    )
    world.say(
        f"The little note bccbccb was only {helper.id}'s reminder to 'bring the bowl, close the cabinet, and clean the crumb board.'"
    )
    world.say(
        f"{detective.id} smiled at the twist: the missing tangerine was safe, and the rolling clue was just a helper's nudge."
    )

def ending_image(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    world.para()
    world.say(
        f"At the end, the tangerine sat safely in its bowl, the note was folded away, and the room was calm again."
    )
    world.say(
        f"{detective.id} and {helper.id} shared the orange fruit, and the mystery felt small and solved."
    )

def tell(setting: Setting, clue_cfg: Clue, detective_name: str, detective_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender))
    clue = world.add(Entity(id=clue_cfg.id, type=clue_cfg.kind, label=clue_cfg.label, phrase=clue_cfg.phrase))

    world.facts.update(detective=detective, helper=helper, clue=clue, clue_cfg=clue_cfg, setting=setting)

    scene_opening(world, detective, helper, clue)
    clue_loss(world, detective, helper, clue)
    follow_roll(world, detective, helper, clue)
    twist_reveal(world, detective, helper, clue)
    ending_image(world, detective, helper, clue)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    clue = f["clue_cfg"]
    return [
        f'Write a short mystery story for a child that includes the word "tangerine" and the note bccbccb.',
        f"Tell a gentle indoor mystery where {detective.id} notices a clue that seems to roll, and {helper.id} helps reveal the twist.",
        f"Write a simple story about a missing tangerine, a rolling clue, and a kind twist in {world.setting.place}.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    clue = f["clue_cfg"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was trying to solve the mystery in {place}?",
            answer=f"{detective.id} was the small detective, and {helper.id} was helping with the mystery in {place}.",
        ),
        QAItem(
            question=f"What was the important missing thing in the story?",
            answer="The important missing thing was a tangerine. It looked missing at first, but the story later showed it was only moved.",
        ),
        QAItem(
            question=f"What was the clue that seemed to roll?",
            answer=f"The clue that seemed to roll was the {clue.label}, because the room gave a soft moving hint before the twist was revealed.",
        ),
        QAItem(
            question=f"What did the note bccbccb mean?",
            answer="It was a reminder to bring the bowl, close the cabinet, and clean the crumb board. It was not a secret code for danger.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that the tangerine was not stolen. {helper.id} had simply moved it to a bowl so it would not bruise.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tangerine?",
            answer="A tangerine is a small orange fruit that is easy to peel and eat.",
        ),
        QAItem(
            question="What does it mean for a clue to roll?",
            answer="In a story, a rolling clue is something that seems to move or lead attention along, like a tiny hint that points to the answer.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="kitchen", detective_name="Mira", detective_gender="girl", helper_name="Theo", helper_gender="boy", clue="tangerine"),
    StoryParams(place="hall", detective_name="Tess", detective_gender="girl", helper_name="Finn", helper_gender="boy", clue="tangerine_peel"),
    StoryParams(place="garden_room", detective_name="Owen", detective_gender="boy", helper_name="Lina", helper_gender="girl", clue="button"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about a tangerine, a roll, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.place and not SETTINGS[args.place].indoor:
        raise StoryError(explain_rejection(args.place, args.clue or "tangerine"))
    if args.clue and not CLUES[args.clue].can_be_moved:
        raise StoryError(explain_rejection(args.place or "kitchen", args.clue))

    combos = valid_stories()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue_id = rng.choice(sorted(combos))
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        clue=clue_id,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        params.detective_name,
        params.detective_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, clue) stories:\n")
        for place, clue in stories:
            print(f"  {place:12} {clue}")
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
            header = f"### {p.detective_name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
