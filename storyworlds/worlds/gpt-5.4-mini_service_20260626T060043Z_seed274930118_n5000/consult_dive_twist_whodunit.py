#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit-style mystery with a consult -> dive
twist.

Premise:
- A young detective hears that something small and important is missing.
- They consult a clue, then dive into a place where the answer is hidden.
- The twist is that the "suspect" is not stealing at all; they are protecting or
  returning the item in a clumsy, secretive way.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "guilt": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str]


@dataclass
class Clue:
    label: str
    detail: str
    target: str
    reveals: str


@dataclass
class Twist:
    label: str
    cause: str
    action: str
    truth: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.clue_found: bool = False
        self.dive_done: bool = False
        self.twist_done: bool = False

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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.clue_found = self.clue_found
        clone.dive_done = self.dive_done
        clone.twist_done = self.twist_done
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "study": Setting(
        place="the old study",
        detail="A brass lamp glowed beside a desk full of papers.",
        affords={"consult", "dive"},
    ),
    "dock": Setting(
        place="the foggy dock",
        detail="The water was black and still beside the boards.",
        affords={"consult", "dive"},
    ),
    "greenhouse": Setting(
        place="the greenhouse",
        detail="Warm glass walls made the air bright and damp.",
        affords={"consult", "dive"},
    ),
}

CLUES = {
    "mud": Clue(
        label="muddy print",
        detail="a small muddy print near the window",
        target="boots",
        reveals="someone had come in from outside",
    ),
    "thread": Clue(
        label="blue thread",
        detail="a blue thread caught on a nail",
        target="coat",
        reveals="someone brushed past the shelf in a hurry",
    ),
    "salt": Clue(
        label="salt smear",
        detail="a salt smear on the floorboards",
        target="dock",
        reveals="the missing item had been carried from the water",
    ),
}

TWISTS = {
    "hidden_return": Twist(
        label="hidden return",
        cause="afraid of being blamed",
        action="had hidden the missing thing for safekeeping",
        truth="the suspect was trying to return it quietly",
    ),
    "accidental_mislead": Twist(
        label="accidental mislead",
        cause="wanted to surprise everyone",
        action="had moved the item without telling anyone",
        truth="the suspect was not a thief at all",
    ),
}

CHAR_NAMES = ["Mina", "Jules", "Pip", "Nina", "Theo", "Elsie"]
ADJ = ["careful", "curious", "sharp-eyed", "patient", "brave"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    twist: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _lead_sentence(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"{detective.id} was a {random.choice(ADJ)} little detective who loved quiet clues "
        f"and careful questions."
    )
    world.say(
        f"{detective.pronoun().capitalize()} and {helper.id} were trying to solve a mystery at {world.setting.place}."
    )


def _consult(world: World, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.clue_found = True
    world.say(
        f"{detective.id} consulted the {clue.label} and bent close to study {clue.detail}."
    )
    world.say(
        f"{helper.id} whispered that {clue.reveals}, but nobody could yet say who had done what."
    )


def _dive(world: World, detective: Entity, helper: Entity, clue: Clue) -> None:
    detective.meters["distance"] += 1
    detective.memes["curiosity"] += 1
    world.dive_done = True
    world.say(
        f"Then {detective.id} decided to dive deeper into the mystery and look where the clue pointed."
    )
    if clue.target == "dock":
        world.say("The detective leaned over the dark water and peered below the boards.")
    elif clue.target == "boots":
        world.say("The detective searched the hall where muddy boots had been lined up by the door.")
    else:
        world.say("The detective slipped between the warm plants and checked the damp corners.")
    helper.memes["worry"] += 1


def _twist(world: World, detective: Entity, suspect: Entity, twist: Twist, clue: Clue) -> None:
    world.twist_done = True
    suspect.memes["guilt"] += 1
    detective.memes["relief"] += 1
    world.say(
        f"At last, the twist came: {suspect.id} had been {twist.cause} and {twist.action}."
    )
    world.say(
        f"The clue made sense now, because {twist.truth}, and the missing item was safe."
    )
    world.say(
        f"{detective.id} smiled, and the room felt lighter than before."
    )


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, clue: str, twist: str) -> bool:
    return place in SETTINGS and clue in CLUES and twist in TWISTS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, t) for p in SETTINGS for c in CLUES for t in TWISTS]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(study;dock;greenhouse).
clue(mud;thread;salt).
twist(hidden_return;accidental_mislead).

valid(P,C,T) :- place(P), clue(C), twist(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - asp_set))
    print("clingo-only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    detective = world.add(Entity(id=params.name, kind="character", type="girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy"))
    clue = CLUES[params.clue]
    suspect = world.add(Entity(id="Caretaker", kind="character", type="woman"))

    world.facts = {
        "detective": detective,
        "helper": helper,
        "suspect": suspect,
        "clue": clue,
        "twist": TWISTS[params.twist],
        "params": params,
    }

    _lead_sentence(world, detective, helper)
    world.para()
    world.say(f"One evening, a small thing went missing, and everyone at {setting.place} looked uneasy.")
    world.say(f"{helper.id} said the only sign was {clue.detail}.")
    _consult(world, detective, helper, clue)
    world.para()
    _dive(world, detective, helper, clue)
    world.para()
    _twist(world, detective, suspect, TWISTS[params.twist], clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a child-friendly whodunit set at {SETTINGS[p.place].place} that uses the word "consult".',
        f'Write a short mystery where {p.name} must dive deeper into a clue and discover a gentle twist.',
        f"Tell a simple detective story about a missing item, a careful consult, and a final answer that is kinder than it first seemed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    clue: Clue = f["clue"]
    twist: Twist = f["twist"]
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]

    return [
        QAItem(
            question=f"Who was the little detective in the mystery at {world.setting.place}?",
            answer=f"{detective.id} was the little detective, and {helper.id} helped by watching the clues closely.",
        ),
        QAItem(
            question=f"What did {detective.id} consult before diving deeper into the mystery?",
            answer=f"{detective.id} consulted the {clue.label}, which was {clue.detail}.",
        ),
        QAItem(
            question=f"What did the detective do after consulting the clue?",
            answer=f"{detective.id} decided to dive deeper into the mystery and search where the clue pointed.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {suspect.id} was {twist.cause} and {twist.action}; in the end, {twist.truth}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to consult a clue?",
            answer="To consult a clue means to study it carefully and think about what it might be telling you.",
        ),
        QAItem(
            question="What does it mean to dive deeper into a mystery?",
            answer="It means to keep investigating and look more closely until the answer starts to appear.",
        ),
        QAItem(
            question="Why do whodunits often have twists?",
            answer="Whodunits often have twists because the answer is not what it first seemed to be, so the story can surprise you.",
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  clue_found={world.clue_found} dive_done={world.dive_done} twist_done={world.twist_done}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with a consult, a dive, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.twist:
        combos = [c for c in combos if c[2] == args.twist]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, twist = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHAR_NAMES)
    helper = args.helper or rng.choice([n for n in CHAR_NAMES if n != name])
    return StoryParams(place=place, clue=clue, twist=twist, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="study", clue="thread", twist="hidden_return", name="Mina", helper="Jules"),
    StoryParams(place="dock", clue="salt", twist="accidental_mislead", name="Pip", helper="Nina"),
    StoryParams(place="greenhouse", clue="mud", twist="hidden_return", name="Elsie", helper="Theo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
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
            header = f"### {p.name}: {p.place} / {p.clue} / {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
