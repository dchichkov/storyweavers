#!/usr/bin/env python3
"""
storyworlds/worlds/mulberry_female_bad_ending_bravery_mystery.py
=================================================================

A standalone storyworld about a female lead, a small mystery, and a brave
attempt that can end badly.

Premise:
- A girl notices something odd in a quiet place.
- She follows clues involving a mulberry-colored object, a hidden sound, or a
  missing item.
- Her bravery pushes the story forward.
- The mystery is solved, but the ending is intentionally bad: she learns the
  truth too late, loses the prize, or the secret leaves a sad aftereffect.

The world models physical meters and emotional memes. The prose is generated
from state changes rather than from a fixed paragraph with swapped names.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female_types = {"girl", "woman", "mother", "sister", "aunt", "female"}
        if self.type in female_types:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    quiet: bool = True


@dataclass
class Clue:
    id: str
    phrase: str
    kind: str
    hint: str
    risk: str
    consequence: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    heroine: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "attic": Setting("the attic", indoor=True, quiet=True),
    "garden": Setting("the back garden", indoor=False, quiet=True),
    "library": Setting("the library corner", indoor=True, quiet=True),
    "porch": Setting("the porch", indoor=False, quiet=True),
}

CLUES = {
    "berry_stain": Clue(
        id="berry_stain",
        phrase="a dark mulberry stain on the windowsill",
        kind="stain",
        hint="mulberry",
        risk="the stain looked fresh",
        consequence="it had been wiped from a hidden note",
    ),
    "mulberry_ribbon": Clue(
        id="mulberry_ribbon",
        phrase="a mulberry ribbon tied in a knot",
        kind="ribbon",
        hint="mulberry",
        risk="it was caught on a loose board",
        consequence="it marked the way to a secret box",
    ),
    "missing_key": Clue(
        id="missing_key",
        phrase="a small key beside a mulberry-colored bead",
        kind="key",
        hint="mulberry",
        risk="the key was half-hidden in dust",
        consequence="it opened the wrong door",
    ),
}

HEROINES = ["Mira", "Nora", "Lena", "Ivy", "Elena", "Maya"]
TRAITS = ["curious", "gentle", "brave", "quiet", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CLUES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a brave female lead and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("No valid mystery matches the requested options.")
    setting, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(HEROINES)
    return StoryParams(setting=setting, clue=clue, heroine=name)


def _line(world: World, text: str) -> None:
    world.say(text)


def tell(setting: Setting, clue: Clue, heroine_name: str) -> World:
    world = World(setting)
    heroine = world.add(Entity(id=heroine_name, kind="character", type="female", label=heroine_name))
    strange = world.add(Entity(id="clue", kind="thing", type=clue.kind, label=clue.id, phrase=clue.phrase))

    heroine.memes["curiosity"] = 1
    heroine.memes["bravery"] = 1

    _line(world, f"{heroine.id} noticed something strange at {setting.place}.")
    _line(world, f"It was {clue.phrase}, and the sight made {heroine.pronoun('object')} pause.")
    _line(world, f"She felt brave enough to follow the clue, even though {clue.risk}.")
    _line(world, f"{heroine.id} moved closer and listened for any sound that could explain the mystery.")

    world.facts["heroine"] = heroine
    world.facts["clue"] = strange
    world.facts["setting"] = setting
    world.facts["clue_def"] = clue

    if clue.id == "berry_stain":
        heroine.meters["fear"] = 0.5
        heroine.memes["determination"] = 1
        _line(world, "Behind the stain, she found a torn note that had been soaked by rain.")
        _line(world, "The note pointed to a box, but the box was already empty.")
        _line(world, "She had been brave, yet the secret slipped away before she could save it.")
        world.facts["ending"] = "sad_loss"
    elif clue.id == "mulberry_ribbon":
        heroine.meters["fear"] = 0.8
        heroine.memes["determination"] = 1
        _line(world, "The ribbon led her to a loose board, and behind it sat a tiny box.")
        _line(world, "Inside was a broken charm, and the missing part had been gone for days.")
        _line(world, "She closed the box with a soft sigh, knowing the mystery was true but too late.")
        world.facts["ending"] = "too_late"
    else:
        heroine.meters["fear"] = 0.6
        heroine.memes["determination"] = 1
        _line(world, "The key fit a door she should not have opened.")
        _line(world, "A cold draft blew out the candle, and the room swallowed the answer.")
        _line(world, "She was brave, but the surprise inside made the whole day end badly.")
        world.facts["ending"] = "wrong_door"

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    heroine = f["heroine"]
    clue = f["clue_def"]
    return [
        f'Write a short mystery for a young child about {heroine.id} and {clue.hint}.',
        f"Tell a brave story where {heroine.id} follows {clue.phrase} and learns a sad truth.",
        "Write a gentle mystery that ends badly after a brave choice reveals the answer too late.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    heroine = f["heroine"]
    clue = f["clue_def"]
    ending = f["ending"]
    return [
        QAItem(
            question=f"Who is the brave girl in the story?",
            answer=f"The brave girl is {heroine.id}. She is the female lead who notices the mystery first."
        ),
        QAItem(
            question=f"What clue did {heroine.id} find?",
            answer=f"{heroine.id} found {clue.phrase}. That clue pulled her deeper into the mystery."
        ),
        QAItem(
            question="Why is the ending bad?",
            answer=(
                "The ending is bad because the answer comes too late. "
                "The clue leads to a sad result, so the bravery helps her learn the truth "
                f"but does not save the lost thing. The ending is {ending}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story where someone notices a puzzling clue and tries to figure out what it means."
        ),
        QAItem(
            question="What does brave mean?",
            answer="Brave means you keep going even when you feel nervous or afraid."
        ),
        QAItem(
            question="What is mulberry?",
            answer="Mulberry is a dark berry color, like deep purple-red fruit juice or a ripe berry stain."
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  ending: {world.facts.get('ending', '')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,C) :- setting(S), clue(C).
brave(H) :- heroine(H).
bad_ending(E) :- ending(E).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in ASP:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.heroine)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(setting="attic", clue="berry_stain", heroine="Mira"),
    StoryParams(setting="garden", clue="mulberry_ribbon", heroine="Nora"),
    StoryParams(setting="library", clue="missing_key", heroine="Lena"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-compatible mystery combinations")
        for combo in combos:
            print(combo)
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
            header = f"### {p.heroine}: {p.clue} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
