#!/usr/bin/env python3
"""
A small fable-like condominium mystery about redundancy, a buddy, and teamwork.

Seed premise:
- A young caretaker and a buddy live in a busy condominium.
- Two clues seem to disagree about a missing shared bell.
- Redundancy gives the team a second way to check the truth.
- The mystery is solved through patient teamwork, and the neighbors celebrate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
buddy_pair(a, b) :- buddy(a, b).
buddy_pair(b, a) :- buddy(a, b).
redundant_check(X) :- clue(X), backup(X).
teamwork_ready :- buddy_pair(a, b), clue(wet_marks), clue(brass_key), backup(wet_marks).
mystery_solved :- teamwork_ready, checked(wet_marks), checked(brass_key), found(bell).
safe_fable :- mystery_solved, shared(bell).
"""


NAMES = ["Luna", "Milo", "Tessa", "Nora", "Pip", "Ollie", "Suri", "Bram"]
BUDDIES = ["Moss", "Wren", "Juniper", "Pax", "Clover", "Theo", "Maple", "Finn"]
PLACES = ["the garden condominium", "the riverside condominium", "the sunny condominium", "the old brick condominium"]
OBJECTS = ["brass bell", "silver key", "blue welcome flag", "red lantern"]
TREATS = ["honey biscuits", "apple slices", "warm muffins", "berry buns"]


@dataclass(frozen=True)
class CASE:
    title: str
    opening: str
    mystery: str
    clue_one: str
    clue_two: str
    false_lead: str
    action: str
    discovery: str
    result: str
    lesson: str
    ending: str
    joke: str


CASES = [
    CASE(
        "the silent entry bell",
        "At dawn, the condominium's shared entry bell refused to ring.",
        "The bell was not broken, but it had vanished from its little wooden hook.",
        "a trail of damp paw marks led toward the laundry room",
        "a bright brass scratch showed near the courtyard gate",
        "a hurried neighbor blamed the raccoon who visited the bins",
        "marked both routes, asked neighbors what they had seen, and checked each clue with a second method",
        "the bell tucked inside a clean laundry basket beneath a folded welcome mat",
        "the caretaker returned the bell to the hook before the first visitors arrived",
        "A second check can keep a quick guess from becoming a wrong accusation.",
        "When the bell rang, every window filled with smiling faces.",
        "The raccoon had an alibi: it was busy guarding a cabbage.",
    ),
    CASE(
        "the missing garden key",
        "After rain, the condominium garden gate stood open while its key was nowhere to be found.",
        "Someone had moved the key, yet the garden beds were still safe.",
        "muddy prints stopped beside the tool shed",
        "a tiny thread of blue wool clung to the gate latch",
        "the neighbors suspected the wind had carried the key away",
        "worked in buddy pairs, compared the print size, and used the spare lock to test the route",
        "the key resting in a watering can beside a blue wool scarf",
        "the garden gate was locked and the seedlings were protected",
        "Teamwork grows stronger when every clue gets a fair hearing.",
        "New green leaves lifted their heads behind the safely latched gate.",
        "The wind was questioned, but it whistled no useful answer.",
    ),
    CASE(
        "the upside-down notice",
        "The condominium notice board displayed tomorrow's picnic notice upside down.",
        "The picnic had not been canceled; the notice had simply been turned around.",
        "crumbs formed a neat line from the board to the stairwell",
        "the thumbtack rested in a flowerpot under the board",
        "a sleepy neighbor blamed a mischievous child",
        "followed the crumbs and checked the board with a spare notice kept in the office",
        "a curious pigeon had nudged the paper while seeking crumbs",
        "the notice was fixed, and everyone learned the picnic time",
        "Redundancy means keeping a backup way to know what is true.",
        "At noon, neighbors shared lunch beneath the board's straight, cheerful notice.",
        "The pigeon confessed only by dropping one very official crumb.",
    ),
    CASE(
        "the lantern in the lift",
        "The little safety lantern disappeared from the condominium lift before a storm.",
        "It had been moved for a good reason, but nobody knew who had moved it.",
        "a line of yellow dust led to the basement cupboard",
        "the cupboard's spare label had been peeled loose",
        "the storm clouds made everyone think the lantern had blown outside",
        "paired up, followed the dust, and compared the cupboard list with the caretaker's notebook",
        "the lantern beside a basket of emergency blankets",
        "the light and blankets were ready before thunder reached the roof",
        "A buddy helps us notice what one pair of eyes might miss.",
        "The lantern glowed in the hall while rain drummed safely beyond the windows.",
        "The storm had many talents, but peeling labels was not one of them.",
    ),
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    name: str
    buddy: str
    place: str
    object_name: str
    treat: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Character
    buddy: Character
    case: CASE
    object_name: str
    treat: str
    route: int
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fable-like condominium teamwork mystery.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--buddy", choices=BUDDIES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--treat", choices=TREATS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        buddy=args.buddy or rng.choice(BUDDIES),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    if params.name == params.buddy:
        raise StoryError("The hero and buddy must have different names.")
    key_text = "|".join(
        [params.name, params.buddy, params.place, params.object_name, params.treat, str(params.seed)]
    )
    key = params.seed if params.seed is not None else int.from_bytes(
        hashlib.sha256(key_text.encode("utf-8")).digest()[:8], "big"
    )
    hero = Character(
        id=params.name,
        role="young caretaker",
        meters={"curiosity": 1.0, "care": 1.0, "teamwork": 0.8},
        memes={"trust": 0.7, "patience": 0.8},
    )
    buddy = Character(
        id=params.buddy,
        role="buddy",
        meters={"observation": 1.0, "care": 0.9, "teamwork": 1.0},
        memes={"trust": 0.8, "patience": 0.7},
    )
    return World(
        setting=Setting(params.place),
        hero=hero,
        buddy=buddy,
        case=CASES[key % len(CASES)],
        object_name=params.object_name,
        treat=params.treat,
        route=(key // len(CASES)) % 3,
    )


def tell(world: World) -> None:
    h, b, case = world.hero, world.buddy, world.case
    greetings = [
        f"In {world.setting.place}, {case.opening}",
        f"One bright morning in {world.setting.place}, {case.opening.lower()}",
        f"The neighbors of {world.setting.place} woke to a puzzle: {case.opening.lower()}",
    ]
    world.say(greetings[world.route])
    world.say(
        f"{h.id}, the young caretaker, noticed that {case.mystery} "
        f"The neighbors wanted an answer before the day grew busy."
    )
    world.para()
    world.say(
        f'"I think {case.false_lead}," said {h.id}. '
        f'"Let us not decide yet," replied {b.id}. "A mystery needs two eyes, and a wise team checks its clues twice."'
    )
    world.say(
        f"Together, the buddies examined the first sign: {case.clue_one}. "
        f"Then they found a second sign: {case.clue_two}. The clues seemed to point in different directions."
    )
    world.para()
    world.say(
        f"Instead of arguing, {h.id} and {b.id} used redundancy: they {case.action}. "
        f"Each check made the mystery smaller and the neighbors calmer."
    )
    world.say(
        f"At last, they discovered {case.discovery}. "
        f"The answer was not a frightening trick at all; it was a small problem waiting for patient teamwork."
    )
    world.para()
    world.say(
        f"They {case.result}. Then the neighbors shared {world.object_name} stories and passed around "
        f"{world.treat} so that everyone could celebrate together."
    )
    world.say(f'"{case.joke}," said {b.id}. {h.id} laughed, and even the worried neighbors smiled.')
    world.say(
        f"The fable taught them this: {case.lesson} {case.ending}"
    )
    world.facts.update(
        hero=h,
        buddy=b,
        setting=world.setting,
        case=case,
        clue_one=case.clue_one,
        clue_two=case.clue_two,
        discovery=case.discovery,
        result=case.result,
        lesson=case.lesson,
        ending=case.ending,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.case
    return [
        f"Write a child-friendly fable about a condominium mystery in which {world.hero.id} and buddy {world.buddy.id} use teamwork and redundancy to find the {world.object_name}.",
        f"Tell a mystery-to-solve story using these clues: {case.clue_one} and {case.clue_two}. Let the buddies check both clues before deciding.",
        f"Write a warm fable ending with this changed world: {case.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.case
    h, b = world.hero, world.buddy
    return [
        QAItem(
            question=f"What mystery did {h.id} and {b.id} solve?",
            answer=f"They solved the mystery of why {case.opening.lower()} The missing or misplaced shared item was connected to {case.mystery.lower()}",
        ),
        QAItem(
            question="What were the two clues?",
            answer=f"The first clue was {case.clue_one}, and the second clue was {case.clue_two}.",
        ),
        QAItem(
            question=f"How did the buddy team use redundancy?",
            answer=f"They {case.action}. They checked the clues in more than one way instead of trusting a quick guess.",
        ),
        QAItem(
            question="What did the team discover?",
            answer=f"They discovered {case.discovery}. This showed that the mystery had a sensible explanation.",
        ),
        QAItem(
            question="What changed after the mystery was solved?",
            answer=f"They {case.result}. The ending image is that {case.ending}",
        ),
        QAItem(
            question="What lesson did the condominium neighbors learn?",
            answer=f"They learned that {case.lesson}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a condominium?",
            answer="A condominium is a place where people have their own homes but share some spaces and responsibilities, such as a hall, garden, gate, or notice board.",
        ),
        QAItem(
            question="What does redundancy mean in this fable?",
            answer="Redundancy means having a backup check or another way to confirm important information, so one mistake does not decide everything.",
        ),
        QAItem(
            question="Why is a buddy useful when solving a mystery?",
            answer="A buddy can notice a different detail, ask a helpful question, and make careful teamwork easier.",
        ),
    ]


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("buddy", "a", "b"),
            asp.fact("clue", "wet_marks"),
            asp.fact("clue", "brass_key"),
            asp.fact("backup", "wet_marks"),
            asp.fact("checked", "wet_marks"),
            asp.fact("checked", "brass_key"),
            asp.fact("found", "bell"),
            asp.fact("shared", "bell"),
        ]
    )


def asp_program(shows: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{shows}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_fable/0."))
    if set(asp.atoms(model, "safe_fable")) == {()}:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH: ASP did not derive safe_fable.")
    return 1


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"place={world.setting.place}",
            f"hero={world.hero.id} role={world.hero.role} meters={world.hero.meters} memes={world.hero.memes}",
            f"buddy={world.buddy.id} role={world.buddy.role} meters={world.buddy.meters} memes={world.buddy.memes}",
            f"object={world.object_name}",
            f"case={world.case.title}",
            f"clue_one={world.case.clue_one}",
            f"clue_two={world.case.clue_two}",
            f"discovery={world.case.discovery}",
            f"result={world.case.result}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Moss", "the garden condominium", "brass bell", "honey biscuits"),
        StoryParams("Milo", "Wren", "the riverside condominium", "silver key", "apple slices"),
        StoryParams("Tessa", "Juniper", "the sunny condominium", "blue welcome flag", "warm muffins"),
        StoryParams("Nora", "Pax", "the old brick condominium", "red lantern", "berry buns"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show teamwork_ready/0.\n#show mystery_solved/0.\n#show safe_fable/0."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        for params in curated():
            sample = generate(params)
            if not sample.story or len(sample.story.split()) < 80:
                print("MISMATCH: generated story was too short.")
                sys.exit(1)
        print("OK: generated stories verified.")
        return

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show buddy_pair/2.\n#show redundant_check/1.\n"
                "#show teamwork_ready/0.\n#show mystery_solved/0.\n#show safe_fable/0."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index if args.seed is not None else None
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
