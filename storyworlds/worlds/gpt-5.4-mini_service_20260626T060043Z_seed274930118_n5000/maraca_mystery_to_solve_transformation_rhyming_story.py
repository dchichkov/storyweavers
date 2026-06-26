#!/usr/bin/env python3
"""
storyworlds/worlds/maraca_mystery_to_solve_transformation_rhyming_story.py
===========================================================================

A small story world about a child, a missing sound, and a maraca that changes
when the mystery is solved.

Premise:
- A child hears a tiny shake-shake sound and wonders where it came from.
- The mystery leads to a hidden maraca.

Turn:
- The child searches the room, follows clues, and finds the maraca in an odd
  place.

Resolution:
- The maraca transforms from plain and quiet into bright and musical when the
  child joins in with rhythm.

Style:
- Rhyming, child-facing prose with a clear beginning, middle, and ending image.
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
    hidden_in: str = ""
    transformed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    soundy: bool = True
    rhyme_word: str = ""


@dataclass
class Mystery:
    id: str
    clue: str
    hiding_place: str
    solved_line: str
    riddle_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    before: str
    after: str
    trigger: str
    sparkle_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def rhyme(a: str, b: str) -> bool:
    return a[-2:] == b[-2:] if len(a) >= 2 and len(b) >= 2 else a[-1:] == b[-1:]


def with_rhyme(line: str, rhyme_word: str) -> str:
    if line.endswith((".", "!", "?")):
        return line[:-1] + f" with {rhyme_word}."
    return line + f" with {rhyme_word}."


def _r_guess(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    mystery = world.facts.get("mystery")
    if not hero or not mystery:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("guess", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["guessed"] = True
    out.append("A clue began to glow in the air.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    mystery = world.facts.get("mystery")
    if not hero or not mystery:
        return out
    if not world.facts.get("found") or world.facts.get("solved"):
        return out
    sig = ("solve", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["solved"] = True
    out.append(mystery.solved_line)
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    myst = world.facts.get("transformation")
    hero = world.facts.get("hero")
    maraca = world.facts.get("maraca")
    if not myst or not hero or not maraca:
        return out
    if not world.facts.get("solved") or maraca.transformed:
        return out
    sig = ("transform", myst.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    maraca.transformed = True
    maraca.label = "bright maraca"
    maraca.phrase = "a bright maraca that gleamed and chimed"
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    out.append(myst.sparkle_line)
    return out


RULES = [
    _r_guess,
    _r_solve,
    _r_transform,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    mystery: str
    transformation: str
    seed: Optional[int] = None


SETTINGS = {
    "playroom": Setting(place="the playroom", soundy=True, rhyme_word="glow"),
    "backyard": Setting(place="the backyard", soundy=True, rhyme_word="tree"),
    "music_room": Setting(place="the music room", soundy=True, rhyme_word="tune"),
}

MYSTERIES = {
    "missing_sound": Mystery(
        id="missing_sound",
        clue="a tiny shake-shake sound",
        hiding_place="under a cloth",
        solved_line="The child lifted the cloth, and there was the maraca.",
        riddle_line="What made the shake-shake sound so sly?",
        tags={"maraca", "sound"},
    ),
    "quiet_corner": Mystery(
        id="quiet_corner",
        clue="a soft pat-pat behind the stool",
        hiding_place="behind a stool",
        solved_line="The child peeked behind the stool, and there was the maraca.",
        riddle_line="What was hiding in the quiet place?",
        tags={"maraca", "hide"},
    ),
}

TRANSFORMATIONS = {
    "plain_to_bright": Transformation(
        id="plain_to_bright",
        before="plain and pale",
        after="bright and bold",
        trigger="a happy rhythm",
        sparkle_line="Then the plain maraca shone bright and gold.",
        tags={"maraca", "change"},
    ),
    "dust_to_dazzle": Transformation(
        id="dust_to_dazzle",
        before="dusty and dull",
        after="twinkly and new",
        trigger="a brave little shake",
        sparkle_line="Then the dull maraca began to ring through and through.",
        tags={"maraca", "change"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "cheery", "brave", "spry", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for myst in MYSTERIES:
            for trans in TRANSFORMATIONS:
                combos.append((place, myst, trans))
    return combos


def reasonableness_gate(place: str, mystery: str, transformation: str) -> None:
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery choice.")
    if transformation not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation choice.")
    if place not in SETTINGS:
        raise StoryError("Unknown setting choice.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.soundy:
            lines.append(asp.fact("soundy", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("hides", mid, m.hiding_place))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("before", tid, t.before))
        lines.append(asp.fact("after", tid, t.after))
    return "\n".join(lines)


ASP_RULES = r"""
can_story(P,M,T) :- setting(P), mystery(M), transformation(T).
#show can_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    clingo_set = set(asp.atoms(model, "can_story"))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming mystery story with a maraca and a transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery, transformation = rng.choice(sorted(combos))
    reasonableness_gate(place, mystery, transformation)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent,
                       mystery=mystery, transformation=transformation)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"curiosity": 0.0, "joy": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    mystery = MYSTERIES[params.mystery]
    trans = TRANSFORMATIONS[params.transformation]
    maraca = world.add(Entity(id="maraca", type="toy", label="maraca", phrase="a plain maraca", owner=hero.id))
    clue = world.add(Entity(id="clue", type="clue", label="clue", phrase=mystery.clue, hidden_in=mystery.hiding_place))

    world.facts.update(hero=hero, parent=parent, mystery=mystery, transformation=trans, maraca=maraca, clue=clue)

    hero.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, {hero.id} heard a tiny shake-shake sound, so light and so spry,"
    )
    world.say(
        f"and {hero.pronoun().capitalize()} asked, “What makes that little music? I want to know why.”"
    )
    world.para()
    world.say(
        f"{hero.id} looked high and low, then under a cloth and behind a chair,"
    )
    world.say(
        f"for every good mystery likes a clue hiding there."
    )
    world.say(
        f"{parent.label.capitalize()} smiled and said, “Keep looking, sweet pea, keep your hope in the air.”"
    )
    propagate(world)
    world.para()
    world.say(
        f"When {hero.id} found the maraca, it seemed plain and pale,"
    )
    world.say(
        f"but {hero.id} gave it a brave little shake, and the room began to sail."
    )
    propagate(world)
    if maraca.transformed:
        world.say(
            f"Now the maraca was bright and bold, and its cheerful tune would not fail."
        )
    world.facts["found"] = True
    world.facts["solved"] = True
    propagate(world)
    world.say(
        f"So {hero.id} danced in a rhyming ring, with {parent.label} close by,"
    )
    world.say(
        f"and the once-quiet maraca rang out sweetly beneath the sky."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short rhyming story for a little {hero.type} named {hero.id} who finds a maraca and solves a mystery.",
        f"Tell a gentle mystery story that starts with a shake-shake sound and ends with a bright transformation.",
        f"Write a child-friendly rhyming tale about a maraca hidden in a room and a happy change after it is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    mystery = f["mystery"]
    trans = f["transformation"]
    maraca = f["maraca"]
    return [
        QAItem(
            question=f"What did {hero.id} hear at the start of the story?",
            answer=f"{hero.id} heard a tiny shake-shake sound in {world.setting.place}.",
        ),
        QAItem(
            question=f"What was the mystery hiding place?",
            answer=f"The mystery was solved when the child looked {mystery.hiding_place}.",
        ),
        QAItem(
            question=f"What did {hero.id} find when the mystery was solved?",
            answer=f"{hero.id} found the maraca, which had been waiting quietly in the room.",
        ),
        QAItem(
            question=f"How did the maraca change at the end?",
            answer=f"It transformed from {trans.before} to {trans.after}, and it began to shine and sing.",
        ),
        QAItem(
            question=f"Who was nearby when the maraca started to ring?",
            answer=f"{parent.label.capitalize()} was nearby, smiling while {hero.id} danced and listened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maraca?",
            answer="A maraca is a small shaker instrument. When you shake it, it makes a cheerful sound.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling question or secret. People solve it by looking for clues.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes different.",
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="playroom", name="Mia", gender="girl", parent="mother", mystery="missing_sound", transformation="plain_to_bright"),
    StoryParams(place="backyard", name="Leo", gender="boy", parent="father", mystery="quiet_corner", transformation="dust_to_dazzle"),
    StoryParams(place="music_room", name="Nora", gender="girl", parent="mother", mystery="missing_sound", transformation="dust_to_dazzle"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_valid_stories() -> list[tuple]:
    return []


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
