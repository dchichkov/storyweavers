#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while not os.path.exists(os.path.join(_root, "results.py")) and os.path.dirname(_root) != _root:
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affordances: set[str]
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Mystery:
    id: str
    object_name: str
    clue: str
    false_guess: str
    truth: str
    repair: str
    ending: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "moonlit_library": Setting(
        "moonlit_library",
        "the moonlit library",
        "quiet",
        {"ledger", "desk", "lamp"},
        {"order": 1.0, "warmth": 1.0},
        {"wonder": 1.0},
    ),
    "sleepy_hall": Setting(
        "sleepy_hall",
        "the sleepy hall",
        "peaceful",
        {"noticeboard", "bell", "basket"},
        {"order": 1.0, "quiet": 1.0},
        {"calm": 1.0},
    ),
    "night_office": Setting(
        "night_office",
        "the little night office",
        "gentle",
        {"desk", "folders", "lamp"},
        {"order": 1.0, "light": 1.0},
        {"trust": 1.0},
    ),
}

MYSTERIES = {
    "missing_permission": Mystery(
        "missing_permission",
        "the permission card for tomorrow's quiet garden visit",
        "a small crescent-shaped ink mark on the empty file",
        "that someone had taken the card to stop the visit",
        "the card had been placed beneath a heavy book so its wet ink would not smear",
        "dry the card, copy its information into the administrative register, and return it to the file",
        "the moon-shaped mark shone beside the restored card as everyone settled for sleep",
        "careful records and patient questions protect trust",
    ),
    "vanished_key": Mystery(
        "vanished_key",
        "the brass key to the story cupboard",
        "a thread of blue wool caught on the filing drawer",
        "that the caretaker had hidden the key",
        "the key had been tucked into a wool mitten after it was found beside an open window",
        "label the key, record where it belongs, and return it to the cupboard",
        "the brass key gleamed in its labeled hook while the bedtime stories waited inside",
        "honesty makes shared things safe",
    ),
    "blank_roster": Mystery(
        "blank_roster",
        "the evening helper roster",
        "three neat dots of lavender ink beside the empty page",
        "that the roster had been erased on purpose",
        "the page had been moved under the blotter when a sleepy breeze scattered the papers",
        "flatten the page, rewrite the names, and place the roster in its proper folder",
        "the lavender dots looked like tiny stars above the names of tomorrow's helpers",
        "order is a kindness when many people depend on it",
    ),
    "lost_stamp": Mystery(
        "lost_stamp",
        "the silver approval stamp",
        "a faint round print on the edge of a bedtime book",
        "that a child had taken it as a toy",
        "the stamp had been used to steady a book while a loose page was repaired",
        "clean the stamp, note its use, and return it to the administrative tray",
        "the silver stamp rested quietly in its tray as the repaired book closed",
        "responsibility includes explaining helpful choices",
    ),
}

NAMES = ["Luna", "Mara", "Theo", "Nia", "Owen", "Iris"]
HELPERS = ["Milo", "Pia", "Sam", "Ada", "Jon", "Rae"]
GENDERS = {
    "Luna": "girl", "Mara": "girl", "Nia": "girl", "Iris": "girl",
    "Pia": "girl", "Ada": "girl", "Rae": "girl",
    "Theo": "boy", "Owen": "boy", "Milo": "boy", "Sam": "boy", "Jon": "boy",
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown setting '{setting}'. Choose one of: {', '.join(SETTINGS)}.")
    if mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery '{mystery}'. Choose one of: {', '.join(MYSTERIES)}.")
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if name == helper:
        raise StoryError("The child and helper must have different names.")
    return StoryParams(setting, mystery, name, helper)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity("child", "character", params.name, memes={"curiosity": 1.0}))
    helper = world.add(Entity("helper", "character", params.helper, memes={"care": 1.0}))
    folder = world.add(Entity("file", "administrative record", "the blue file", meters={"order": 1.0}))
    lamp = world.add(Entity("lamp", "object", "the bedside lamp", meters={"warmth": 1.0}))
    world.facts.update({
        "child": child,
        "helper": helper,
        "file": folder,
        "lamp": lamp,
        "mystery": MYSTERIES[params.mystery],
        "resolved": False,
    })
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES:
        raise StoryError("Story parameters do not name a registered setting and mystery.")
    if params.name == params.helper:
        raise StoryError("The child and helper must have different names.")

    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.name + params.helper)))
    world = build_world(params)
    child = world.facts["child"]
    helper = world.facts["helper"]
    mystery: Mystery = world.facts["mystery"]
    place = world.setting.place

    world.say(rng.choice([
        f"At bedtime, {child.label} sat in {place} beneath a warm little lamp.",
        f"The evening had grown soft and quiet in {place}, where {child.label} helped with one last administrative task.",
        f"Before sleep, {child.label} visited {place} to put the night's records in order.",
    ]))
    world.say(
        f"On the desk, {mystery.object_name} was missing, and its empty place made the peaceful room feel full of questions."
    )
    world.para()

    world.say(
        f"{child.label} found {mystery.clue}. The clue was small, but it was enough to begin a mystery to solve."
    )
    world.say(
        f"At first, {child.label} wondered {mystery.false_guess}."
    )
    world.say(
        f'"We should ask before we decide," {helper.label} said softly. '
        f'"Then the record can tell us what really happened."'
    )
    world.say(
        f'"You are right," said {child.label}. "Let us follow the clues carefully."'
    )
    world.para()

    world.say(
        f"Together they checked the desk, the folders, and the quiet corners of {place}. "
        f"At last, they learned that {mystery.truth}."
    )
    world.say(
        f"{child.label} felt relief, while {helper.label} felt proud that a patient search had protected someone from blame."
    )
    world.para()

    world.say(
        f"They worked together to {mystery.repair}. The administrative record became clear again, and the missing thing was safe."
    )
    world.facts["resolved"] = True
    world.facts["truth"] = mystery.truth
    world.facts["repair"] = mystery.repair
    world.facts["moral_value"] = mystery.lesson
    child.memes.update({"curiosity": 0.0, "relief": 1.0, "honesty": 1.0})
    helper.memes.update({"care": 1.0, "trust": 1.0})
    world.entities["file"].meters["order"] = 2.0

    world.say(
        f"Before climbing into bed, {child.label} wrote one sentence in the notebook: "
        f"\"{mystery.lesson.capitalize()}\"."
    )
    world.say(f"Then {mystery.ending}.")
    story = world.render()

    prompts = [
        "Write a gentle bedtime mystery about an administrative record, careful questions, and a moral value.",
        f"Tell a quiet story in which {params.name} solves a missing-record mystery with {params.helper}.",
        "Create a child-friendly mystery whose solution shows honesty and responsibility.",
    ]
    story_qa = [
        QAItem("Who solved the mystery?", f"{params.name} solved the mystery with help from {params.helper}."),
        QAItem("What was missing?", f"The missing item was {mystery.object_name}."),
        QAItem("What clue began the investigation?", f"The first clue was {mystery.clue}."),
        QAItem("What was the truth?", f"The truth was that {mystery.truth}."),
        QAItem("How was the problem repaired?", f"They worked together to {mystery.repair}."),
        QAItem("What moral value did the story show?", f"The story showed that {mystery.lesson}."),
    ]
    world_qa = [
        QAItem("What is an administrative record?", "It is an organized note or document that helps people remember plans, permissions, or responsibilities."),
        QAItem("Why should someone ask questions before blaming another person?", "Questions can reveal the truth and prevent an unfair accusation."),
        QAItem("What makes a mystery solvable?", "A mystery is solvable when careful observers collect clues and connect them to what happened."),
        QAItem("Why is honesty useful in a shared place?", "Honesty helps people trust one another and care for shared belongings and plans."),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"setting: {world.setting.place} ({world.setting.mood})")
    lines.append(f"resolved: {world.facts.get('resolved')}")
    for entity in world.entities.values():
        lines.append(f"{entity.id}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_mystery(M) :- mystery(M).
valid(S,M) :- valid_setting(S), valid_mystery(M).
solvable(S,M) :- valid(S,M), clue(M), truth(M), repair(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for mystery in MYSTERIES.values():
        lines.extend([
            asp.fact("mystery", mystery.id),
            asp.fact("clue", mystery.id),
            asp.fact("truth", mystery.id),
            asp.fact("repair", mystery.id),
        ])
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    python = set(valid_combos())
    model = asp.one_model(asp_program())
    answer = set(asp.atoms(model, "valid"))
    if python != answer:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(python - answer))
        print("Only ASP:", sorted(answer - python))
        return 1
    for setting, mystery in valid_combos():
        sample = generate(StoryParams(setting, mystery, "Luna", "Milo", 7))
        if "mystery" not in sample.story.lower() or not sample.world.facts["resolved"]:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP matches Python for {len(python)} combinations and stories resolve.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle administrative bedtime mystery.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/2."))
        for pair in sorted(asp.atoms(model, "solvable")):
            print(pair)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for setting, mystery in valid_combos():
            samples.append(generate(StoryParams(setting, mystery, "Luna", "Milo", base)))
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
