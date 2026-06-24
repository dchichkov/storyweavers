#!/usr/bin/env python3
"""
storyworlds/worlds/blur_lesson_learned_mystery.py
==================================================

A small mystery story world about a blurred clue, a careful look, and a lesson
learned at the end.

The seed premise:
- A child finds something important, but it is too blurry to read clearly.
- The mystery feels stuck until they slow down, clean the view, and look again.
- The ending proves what changed: the clue becomes clear, the problem is solved,
  and the child learns that careful looking can matter as much as quick looking.

This world keeps the prose child-facing and concrete, while the simulated state
drives the turn from confusion to discovery.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    revealed_text: str
    initial_blur: float = 1.0


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    reveals: float


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(
        place="the library",
        detail="Quiet shelves made a hush around the reading table.",
        affords={"search"},
    ),
    "attic": Setting(
        place="the attic",
        detail="Old boxes stood in a row under a dusty window.",
        affords={"search"},
    ),
    "porch": Setting(
        place="the porch",
        detail="Rain had left tiny silver drops on the rail.",
        affords={"search"},
    ),
}

CLUES = {
    "note": Clue(
        label="note",
        phrase="a little note with curly writing",
        revealed_text="the cat was hiding behind the blue door",
    ),
    "map": Clue(
        label="map",
        phrase="a folded map with one blurred corner",
        revealed_text="the missing key was under the red mat",
    ),
    "picture": Clue(
        label="picture",
        phrase="a family picture with a blurry side",
        revealed_text="the puppy had fallen asleep in the laundry basket",
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="soft cloth",
        phrase="a soft cloth from the shelf",
        action="wipe the blur away",
        reveals=1.0,
    ),
    "glass": Tool(
        id="glass",
        label="magnifying glass",
        phrase="a shiny magnifying glass",
        action="look closer through it",
        reveals=0.8,
    ),
    "lamp": Tool(
        id="lamp",
        label="desk lamp",
        phrase="a small desk lamp",
        action="shine more light on it",
        reveals=0.6,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max", "Ben", "Sam"]
TRAITS = ["curious", "careful", "brave", "patient", "quick", "quiet"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is solveable when some tool can reduce its blur to clear enough.
solveable(P, C, T) :- place(P), clue(C), tool(T),
                      has_clue(P, C), has_tool(T),
                      blur_of(C, B), reveal(T, R), B <= R.

% A lesson is learned when the clue becomes clear after using a tool.
learned(P, C, T) :- solveable(P, C, T).

#show solveable/3.
#show learned/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("has_clue", "any", cid))
        lines.append(asp.fact("blur_of", cid, int(clue.initial_blur * 10)))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("has_tool", tid))
        lines.append(asp.fact("reveal", tid, int(tool.reveals * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show solveable/3."))
    return sorted(set(asp.atoms(model, "solveable")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Core world logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                combos.append((p, c, t))
    return combos


def clean_text(clue: Clue) -> str:
    return clue.revealed_text


def introduce(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.get('traits', ['curious']))} {hero.type} "
        f"who liked quiet mysteries."
    )
    world.say(
        f"One day, {hero.pronoun('subject')} found {clue.phrase} at {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {helper.label} stayed nearby, watching patiently."
    )


def set_up_mystery(world: World, hero: Entity, clue: Entity) -> None:
    clue.meters["blur"] = 1.0
    hero.memes["wonder"] = 1.0
    hero.memes["curiosity"] = 1.0
    world.say(
        f"The problem was that the clue was blurred, so {hero.id} could not read it yet."
    )


def try_tool(world: World, hero: Entity, tool: Entity, clue: Entity) -> bool:
    if clue.meters.get("blur", 0.0) <= 0:
        return True
    before = clue.meters.get("blur", 0.0)
    clue.meters["blur"] = max(0.0, before - tool.meters["reveals"])
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{hero.id} picked up {tool.phrase} and tried to {tool.phrase.split('a ',1)[-1] if tool.id != 'cloth' else 'wipe the blur away'}."
    )
    if clue.meters["blur"] > 0:
        world.say("It helped a little, but the writing was still fuzzy.")
        return False
    world.say(f"At last, the blur was gone.")
    return True


def reveal_solution(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    world.say(
        f"{hero.id} leaned in again and read the note clearly: {clean_text(world.facts['clue_obj'])}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["lesson"] = 1.0
    world.say(
        f"{hero.id} smiled and said, 'I learned that if something looks blurry, I should slow down and look carefully.'"
    )
    world.say(
        f"{helper.id} nodded, and together they found the answer."
    )


# ---------------------------------------------------------------------------
# Narrative build
# ---------------------------------------------------------------------------
def tell(setting: Setting, clue: Clue, tool: Tool, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"traits": [trait]}))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper, label=f"the {helper}"))
    clue_ent = world.add(Entity(id="Clue", type="thing", label=clue.label, phrase=clue.phrase))
    tool_ent = world.add(Entity(id=tool.id, type="thing", label=tool.label, phrase=tool.phrase))
    tool_ent.meters["reveals"] = tool.reveals
    clue_ent.meters["blur"] = clue.initial_blur

    world.facts.update(hero=hero, helper=helper_ent, clue=clue_ent, clue_obj=clue, tool=tool_ent)

    world.say(f"{hero.id} was a {trait} {gender} who loved mysteries.")
    world.say(f"At {setting.place}, {hero.id} found {clue.phrase}.")
    world.para()
    world.say(setting.detail)
    world.say(
        f"But the clue was blurred, and that made the mystery feel stuck."
    )
    world.say(
        f"{helper_ent.id} said, 'Let's not rush. Let's look carefully.'"
    )
    world.para()
    world.say(
        f"{hero.id} tried to solve it by using {tool.phrase}."
    )
    solved = try_tool(world, hero, tool_ent, clue_ent)
    if not solved:
        world.say(f"{hero.id} took a breath and tried again, this time slower.")
        clue_ent.meters["blur"] = 0.0
        world.say("Careful looking made the blurred letters settle into place.")
    world.para()
    reveal_solution(world, hero, helper_ent, clue_ent)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue_obj: Clue = f["clue_obj"]
    return [
        f'Write a short mystery story for a young child that includes the word "blur" and ends with a lesson learned.',
        f"Tell a gentle mystery about {hero.id}, who finds {clue_obj.phrase} and learns to slow down when the clue is blurry.",
        f"Write a simple story where a blurry clue becomes clear after careful looking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue_obj: Clue = f["clue_obj"]
    tool: Entity = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {clue_obj.phrase}, but it was blurred at first.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay calm during the mystery?",
            answer=f"{helper.id} helped by telling {hero.id} to slow down and look carefully.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help with the blur?",
            answer=f"{hero.id} used {tool.phrase} to make the clue easier to read.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that if something looks blurry, it helps to slow down and look carefully again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does blurry mean?",
            answer="Blurry means not clear enough to see or read well.",
        ),
        QAItem(
            question="Why can a cloth help with a blurry clue?",
            answer="A cloth can wipe away dust or smudges so words and pictures are easier to see.",
        ),
        QAItem(
            question="What should you do if you cannot read something clearly?",
            answer="You can slow down, look carefully, and try again in a better way.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery world about a blur and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "librarian", "grandma"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    tool = args.tool or rng.choice(list(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "librarian", "grandma"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], TOOLS[params.tool],
                 params.name, params.gender, params.helper, params.trait)
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
CURATED = [
    StoryParams(place="library", clue="note", tool="cloth", name="Mia", gender="girl", helper="librarian", trait="careful"),
    StoryParams(place="attic", clue="map", tool="glass", name="Leo", gender="boy", helper="grandma", trait="curious"),
    StoryParams(place="porch", clue="picture", tool="lamp", name="Nora", gender="girl", helper="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show learned/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_combos()
        print(f"{len(combos)} solveable combos:\n")
        for p, c, t in combos:
            print(f"  {p:8} {c:8} {t:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
