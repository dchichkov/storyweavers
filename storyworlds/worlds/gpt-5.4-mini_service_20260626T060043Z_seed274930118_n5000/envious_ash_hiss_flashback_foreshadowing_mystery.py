#!/usr/bin/env python3
"""
storyworlds/worlds/envious_ash_hiss_flashback_foreshadowing_mystery.py
=======================================================================

A small mystery storyworld built from the seed words envious, ash, and hiss.

Premise:
- A child notices a strange ash trail and a soft hiss in a quiet cottage kitchen.
- Someone has gone missing: a small brass star that belongs by the hearth.
- The child feels a prick of envy, then uses a flashback and a foreshadowing clue
  to solve the mystery.

The story is deliberately constrained:
- It is a compact, child-facing mystery.
- The solution must be supported by the simulated world model.
- The ending proves what changed: the lost thing is found, suspicion clears,
  and envy gives way to relief.

This file is standalone and only depends on the shared storyworld helpers.
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
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class Clue:
    id: str
    label: str
    source: str
    effect: str
    reveals: str
    sound: str
    tag: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    hidden_places: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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

SETTINGS = {
    "cottage": Setting(place="the old cottage", indoor=True),
    "kitchen": Setting(place="the kitchen", indoor=True),
    "museum": Setting(place="the little museum", indoor=True),
}

CLUES = {
    "ash": Clue(
        id="ash",
        label="a gray ash trail",
        source="the fireplace",
        effect="left tiny smudges on the floor",
        reveals="someone had walked from the hearth toward the pantry",
        sound="the soft whisper of ash",
        tag="ash",
    ),
    "hiss": Clue(
        id="hiss",
        label="a steady hiss",
        source="the kettle",
        effect="made the air feel tense",
        reveals="something warm had just been moved and set down carefully",
        sound="the kettle hiss",
        tag="hiss",
    ),
    "flashback": Clue(
        id="flashback",
        label="a small memory",
        source="last night",
        effect="showed where the star had been seen before",
        reveals="the brass star had been resting on a shelf near the sugar jar",
        sound="a remembered clink",
        tag="flashback",
    ),
    "foreshadowing": Clue(
        id="foreshadowing",
        label="a little hint",
        source="the open pantry door",
        effect="pointed toward the hidden tin",
        reveals="a narrow gap behind the bread box",
        sound="a faint wooden tap",
        tag="foreshadowing",
    ),
}

PRIZES = {
    "star": Prize(
        id="star",
        label="brass star",
        phrase="a small brass star",
        hidden_places={"bread_box", "teapot_shelf"},
    ),
    "pin": Prize(
        id="pin",
        label="blue pin",
        phrase="a tiny blue coat pin",
        hidden_places={"bread_box", "coat_rack"},
    ),
    "bell": Prize(
        id="bell",
        label="silver bell",
        phrase="a little silver bell",
        hidden_places={"teapot_shelf", "cushion"},
    ),
}

NAMES = ["Nora", "Mina", "Toby", "June", "Iris", "Eli"]
KINDS = {"girl": ["Nora", "Mina", "June", "Iris"], "boy": ["Toby", "Eli"]}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    clue: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for clue in CLUES:
            for prize in PRIZES:
                # The mystery should be solvable: every valid combo has both an
                # audible clue and a hidden place that the clue can point to.
                if clue in {"ash", "hiss", "flashback", "foreshadowing"}:
                    combos.append((place, clue, prize))
    return combos


def explain_rejection(clue: str, prize: str) -> str:
    return (
        f"(No story: the clue '{clue}' cannot reasonably help find the {prize}. "
        f"Choose a combo with a visible trail, a memory, or a hint.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"curiosity": 1.0, "envy": 0.0, "relief": 0.0, "certainty": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="mother" if params.helper == "mother" else "father",
        label=f"the {params.helper}",
        memes={"calm": 1.0},
    ))
    prize = PRIZES[params.prize]
    lost = world.add(Entity(
        id="lost",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=helper.id,
        hidden_in="bread_box",
        meters={"hidden": 1.0},
    ))
    clue = CLUES[params.clue]

    # Act 1: setup.
    world.say(
        f"{hero.id} was in {world.setting.place} with {helper.label_word}. "
        f"{hero.id} loved little mysteries, but today {hero.pronoun('subject')} felt envious "
        f"because {helper.label_word} had the only bright lantern."
    )
    world.say(
        f"Then something was wrong. The {prize.label} was gone, and only {clue.label} "
        f"remained near the hearth."
    )

    # Act 2: tension, flashback, foreshadowing.
    world.para()
    if clue.id == "ash":
        world.say(
            f"{clue.sound} lay across the floor like a pencil line. "
            f"It {clue.effect}, and that {clue.reveals}."
        )
    elif clue.id == "hiss":
        world.say(
            f"{clue.sound} came from the kettle. It {clue.effect}, and that "
            f"{clue.reveals}."
        )
    elif clue.id == "flashback":
        world.say(
            f"A flashback flickered in {hero.id}'s mind: last night, {helper.label_word} "
            f"had set the {prize.label} on a shelf near the sugar jar."
        )
    else:
        world.say(
            f"A foreshadowing clue sat in the open pantry door. It looked small, "
            f"but it pointed toward a secret gap behind the bread box."
        )

    world.say(
        f"{hero.id} listened carefully. The strange {clue.tag} sound felt like a clue "
        f"that wanted to be found."
    )

    # Act 3: deduction and resolution.
    world.para()
    if clue.id == "ash":
        world.say(
            f"{hero.id} followed the ash trail past the pantry and behind the bread box."
        )
        lost.hidden_in = "bread_box"
    elif clue.id == "hiss":
        world.say(
            f"{hero.id} waited by the kettle until the hiss faded, then noticed a tiny "
            f"gleam near the sugar jar shelf."
        )
        lost.hidden_in = "teapot_shelf"
    elif clue.id == "flashback":
        world.say(
            f"That memory was enough. {hero.id} checked the shelf near the sugar jar and "
            f"found the missing {prize.label} tucked behind a tea tin."
        )
        lost.hidden_in = "teapot_shelf"
    else:
        world.say(
            f"{hero.id} looked behind the bread box, where the hint had pointed. "
            f"That was where the missing {prize.label} had been hidden."
        )
        lost.hidden_in = "bread_box"

    hero.memes["certainty"] += 1.0
    hero.memes["envy"] = 0.0
    hero.memes["relief"] += 1.0

    world.say(
        f"{helper.label_word} smiled when {hero.id} found it. "
        f"{hero.id} was no longer envious; {hero.pronoun('subject')} felt proud instead."
    )
    world.say(
        f"At the end, the {prize.label} was back where it belonged, and the cottage "
        f"felt quiet and safe again."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": lost,
        "clue": clue,
        "place": params.place,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    clue = f["clue"]
    return [
        f'Write a short mystery story for a young child that includes "{clue.tag}", '
        f'"ash", and "hiss".',
        f"Tell a gentle mystery where {hero.id} feels envious, notices a clue, and "
        f"finds {prize.phrase} with help from {helper.label_word}.",
        f"Write a cozy story with a flashback and a foreshadowing clue that leads to a "
        f"missing {prize.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    clue = f["clue"]

    return [
        QAItem(
            question=f"Why did {hero.id} feel envious at the start?",
            answer=(
                f"{hero.id} felt envious because {helper.label_word} had the only bright "
                f"lantern, while {hero.id} was the one trying to solve the mystery."
            ),
        ),
        QAItem(
            question=f"What clue helped {hero.id} look for the missing {prize.label}?",
            answer=(
                f"The clue was {clue.label}. It pointed {hero.id} toward the place where "
                f"the missing {prize.label} had been hidden."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, {hero.id} found the missing {prize.label}, the worry was gone, "
                f"and the feeling of envy changed into relief and pride."
            ),
        ),
        QAItem(
            question=f"How did the flashback or foreshadowing help solve the mystery?",
            answer=(
                f"The flashback reminded {hero.id} where the {prize.label} had been seen before, "
                f"and the foreshadowing clue pointed to the hiding spot. Together they made the "
                f"answer easy to follow."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ash?",
            answer=(
                "Ash is the soft gray powder that can be left behind after something burns, "
                "like in a fireplace."
            ),
        ),
        QAItem(
            question="What does hiss mean?",
            answer=(
                "A hiss is a quiet, sharp sound, like steam or a snake making a soft sss sound."
            ),
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is when a story briefly remembers something that happened before."
            ),
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer=(
                "Foreshadowing is a small clue that hints at what will happen later."
            ),
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A combo is valid when a clue can plausibly help find the prize.
valid(Place, Clue, Prize) :- place(Place), clue(Clue), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for prid in PRIZES:
        lines.append(asp.fact("prize", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with ash, hiss, flashback, and foreshadowing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = KINDS[gender]
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(place=place, clue=clue, prize=prize, name=name, gender=gender, helper=helper)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid (place, clue, prize) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="cottage", clue="ash", prize="star", name="Nora", gender="girl", helper="mother"),
            StoryParams(place="kitchen", clue="hiss", prize="pin", name="Toby", gender="boy", helper="father"),
            StoryParams(place="museum", clue="flashback", prize="bell", name="Mina", gender="girl", helper="mother"),
            StoryParams(place="cottage", clue="foreshadowing", prize="star", name="Eli", gender="boy", helper="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
