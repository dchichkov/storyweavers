#!/usr/bin/env python3
"""
storyworlds/worlds/hiccing_description_dialogue_whodunit.py
===========================================================

A small whodunit story world with dialogue, description, and a single tidy
mystery shape: someone keeps hiccing, a missing object has to be explained, and
the final answer turns on a concrete clue.

The generated stories stay close to a classic child-friendly whodunit:
- a careful setting description,
- a short list of suspects,
- dialogue that raises and resolves suspicion,
- a clue that proves what happened,
- a clear ending image with the mystery solved.

The seed words are used in-world:
- hiccing
- description
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    description: str
    indoor: bool = True


@dataclass
class Mystery:
    missing: str
    missing_label: str
    culprit: str
    culprit_label: str
    motive: str
    clue: str
    reveal: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    detective_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.asked: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "library": Setting(
        place="the little library",
        description="Tall shelves stood in neat rows, and the reading nook had a blue rug and a round lamp.",
        indoor=True,
    ),
    "kitchen": Setting(
        place="the sunny kitchen",
        description="A checkered table sat by the window, and the teapot gleamed on the counter.",
        indoor=True,
    ),
    "toyshop": Setting(
        place="the toy shop",
        description="Bright boxes filled the shelves, and a brass bell hung above the door.",
        indoor=True,
    ),
}

MYSTERIES = {
    "cookie": Mystery(
        missing="cookie",
        missing_label="the star-shaped cookie",
        culprit="blue paint on the detective's sleeve",
        culprit_label="blue paint",
        motive="the cookie had been carried past the craft table and brushed the wet paint",
        clue="a blue fingerprint on the cookie plate",
        reveal="the wet paint showed who had touched the plate first",
    ),
    "bell": Mystery(
        missing="bell",
        missing_label="the little brass bell",
        culprit="a ribbon tied to the friend’s wrist",
        culprit_label="a ribbon",
        motive="the bell had snagged on the ribbon during a game of hiding and seeking",
        clue="a tiny ribbon thread stuck on the bell rope",
        reveal="the thread matched the ribbon on the wrist",
    ),
    "book": Mystery(
        missing="book",
        missing_label="the picture book with the red cover",
        culprit="jam on the friend’s fingers",
        culprit_label="jam",
        motive="the book had been opened at snack time, and sticky fingers left marks",
        clue="a sticky red smudge on page three",
        reveal="the smudge matched the jam from snack time",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Maya", "Zoe"]
BOY_NAMES = ["Eli", "Finn", "Noah", "Theo", "Ben", "Max"]
TRAITS = ["careful", "curious", "brave", "quiet", "quick", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with dialogue and description.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    det_type = args.detective_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    det_name = args.detective_name or rng.choice(GIRL_NAMES if det_type == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    if det_name == friend_name:
        friend_name = (friend_name + "y") if friend_name[-1] != "y" else (friend_name + "a")
    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=det_name,
        detective_type=det_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def _character_phrase(name: str, kind: str) -> str:
    return f"little {kind} {name}"


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting, mystery)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        meters={"attention": 1.0},
        memes={"curiosity": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        meters={"attention": 1.0},
        memes={"nervous": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="thing",
        label=mystery.missing_label,
        phrase=mystery.missing_label,
        owner=friend.id,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label=mystery.clue,
        phrase=mystery.clue,
    ))

    world.facts.update(
        detective=detective,
        friend=friend,
        missing=missing,
        clue=clue,
        setting=setting,
        mystery=mystery,
    )

    world.say(f"In {setting.place}, {setting.description}")
    world.say(
        f"{_character_phrase(detective.id, detective.type)} was a careful little detective, "
        f"and {friend.id} was a {params.friend_type} friend who kept hiccing whenever someone asked a hard question."
    )
    world.say(
        f'"We need a description of what is missing," said {detective.id}. '
        f'"I know," hicced {friend.id}. "It was right there a minute ago."'
    )

    world.lines.append(
        f'"Look closely," said {detective.id}. "Who saw {mystery.missing_label} last?"'
    )
    world.lines.append(
        f'"I did," said {friend.id}, "but I was busy helping near the craft table."'
    )
    world.lines.append(
        f'"And what about the clue?" asked {detective.id}. '
        f'"A blue fingerprint on the plate," whispered {friend.id}, still hiccing.'
    )
    world.lines.append(
        f'{detective.id} bent down and checked the table edge. There it was: {mystery.clue}.'
    )
    world.lines.append(
        f'"That means {mystery.reveal}," said {detective.id}. "The missing thing was not stolen at all."'
    )
    world.lines.append(
        f'{friend.id} stopped hiccing for a moment. "So who did it?"'
    )
    world.lines.append(
        f'"Nobody did anything bad," said {detective.id}. "Your {mystery.culprit_label} caused the trouble. '
        f'{mystery.motive}."'
    )
    world.lines.append(
        f'{friend.id} looked relieved. "Oh! Then the {mystery.missing} is probably safe."'
    )
    world.lines.append(
        f'"Exactly," said {detective.id}. They found {mystery.missing_label} tucked where it had been left, '
        f'and the whole room felt calm again.'
    )
    world.lines.append(
        f'By the end, {friend.id} had stopped hiccing, the description made sense, and the mystery was solved.'
    )

    world.facts["solved"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).

valid(S, M) :- setting(S), mystery(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos()")
    print("only python:", sorted(py - ac))
    print("only clingo:", sorted(ac - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    detective: Entity = f["detective"]  # type: ignore[assignment]
    return [
        f'Write a child-friendly whodunit set in {setting.place} that includes the words "hiccing" and "description".',
        f'Tell a short mystery where {detective.id} listens to dialogue, follows a clue, and solves the problem about {mystery.missing_label}.',
        f'Write a gentle detective story with a clear ending image, a clue, and a calm reveal in {setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {detective.id}, a careful little {detective.type} in {setting.place}.",
        ),
        QAItem(
            question=f"What was the missing thing?",
            answer=f"The missing thing was {mystery.missing_label}.",
        ),
        QAItem(
            question=f"Why was {friend.id} hiccing during the questioning?",
            answer=f"{friend.id} kept hiccing because the questions were making {friend.pronoun('object')} nervous, not because anything dangerous was happening.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was {mystery.clue}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved, {friend.id} calmer, and {mystery.missing_label} found again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a description in a story?",
            answer="A description is a set of details that helps you picture a place, a person, or an object in your mind.",
        ),
        QAItem(
            question="What is a clue in a whodunit?",
            answer="A clue is a small detail that helps the detective figure out what happened.",
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer="Stories use dialogue so the characters can speak to each other and share their thoughts directly.",
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
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  setting={world.setting.place}")
    lines.append(f"  mystery={world.mystery.missing}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", mystery="cookie", detective_name="Mina", detective_type="girl", friend_name="Eli", friend_type="boy"),
    StoryParams(setting="kitchen", mystery="book", detective_name="Noah", detective_type="boy", friend_name="Lily", friend_type="girl"),
    StoryParams(setting="toyshop", mystery="bell", detective_name="Ava", detective_type="girl", friend_name="Ben", friend_type="boy"),
]


def explain_rejection() -> str:
    return "(No story: the requested options do not form a valid whodunit.)"


def resolve_combo(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/mystery combos:\n")
        for s, m in combos:
            print(f"  {s:8} {m:8}")
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
            params = resolve_combo(args, random.Random(seed))
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
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
