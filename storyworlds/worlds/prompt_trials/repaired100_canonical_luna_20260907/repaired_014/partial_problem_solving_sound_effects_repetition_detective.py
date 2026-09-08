#!/usr/bin/env python3
"""
A small detective storyworld about a partial clue, a repeating sound, and
careful problem solving.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=lambda: {"listen", "inspect", "repeat", "compare"})


@dataclass
class StoryParams:
    name: str
    helper_name: str
    witness_name: str
    case: int = 0
    method: int = 0
    sound: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    place: str
    opening: str
    partial_clue: str
    sound: str
    cause: str
    first_test: str
    repeated_test: str
    repair: str
    ending: str


CASES = [
    Case(
        "the little museum",
        "Detective Luna found a torn blue ticket beneath the clock.",
        "Only the ticket's left half remained, with three dots and a silver star.",
        "tap... tap... tap",
        "a loose display bell swinging against the clock case",
        "placed a strip of paper under the bell to stop it",
        "lifted the paper, waited, and repeated the same test",
        "fastened the bell's thread to a small brass hook",
        "the blue ticket rested beside a clock that ticked without a tap",
    ),
    Case(
        "the rainy train station",
        "Detective Luna noticed a muddy footprint ending beside a bench.",
        "The print showed only the front half of a small boot.",
        "plink, plink",
        "rainwater dripping from a bent umbrella into a tin sign",
        "moved the umbrella while her partner counted the drops",
        "returned it and moved it again to compare the sound",
        "opened the umbrella beneath the covered rack",
        "the partial footprint dried while the tin sign stood quiet",
    ),
    Case(
        "the town library",
        "Detective Luna discovered a half-written note inside a storybook.",
        "The note ended after the words, 'Look beneath the...'",
        "scritch, scritch",
        "a bookmark tassel brushing the wooden shelf in a draft",
        "closed one window and listened to the shelf",
        "opened and closed that window twice more",
        "tucked the tassel between the book's pages",
        "the unfinished note stayed safe while the shelf made no sound",
    ),
    Case(
        "the old theater",
        "Detective Luna found one shiny button beneath the stage.",
        "A partial row of buttons led toward the curtain.",
        "jingle... jingle",
        "a costume chain caught on a curtain wheel",
        "held the curtain still and marked the chain's place",
        "released and held it again to check the sound",
        "freed the chain from the wheel",
        "the buttons lined the costume while the curtain rested silently",
    ),
]

METHODS = [
    ("made a neat clue chart", "recorded what changed and what stayed the same"),
    ("drew a map of the room", "marked each tested spot with a chalk circle"),
    ("used three cards labeled LOOK, LISTEN, and TEST", "turned over one card after every careful check"),
    ("followed the rule 'change one thing at a time'", "waited for the same result before making a new guess"),
]

SOUNDS = [
    ("Listen carefully," " said Luna. "The sound is a clue, not an answer."),
    ("A repeated sound can point to a repeated motion," " said Luna."),
    ("We should not chase every guess," " said Luna. "We should test one."),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def validate(params: StoryParams) -> None:
    if not params.name.strip() or not params.helper_name.strip() or not params.witness_name.strip():
        raise StoryError("Detective, helper, and witness names must not be empty.")
    if params.name.strip().lower() == params.helper_name.strip().lower():
        raise StoryError("The detective and helper need different names.")
    if not isinstance(params.case, int) or not 0 <= params.case < len(CASES):
        raise StoryError("case must select a registered detective case.")
    if not isinstance(params.method, int) or not 0 <= params.method < len(METHODS):
        raise StoryError("method must select a registered investigation method.")
    if not isinstance(params.sound, int) or not 0 <= params.sound < len(SOUNDS):
        raise StoryError("sound must select a registered dialogue pattern.")


def build_story(params: StoryParams) -> World:
    validate(params)
    case = CASES[params.case]
    method = METHODS[params.method]
    setting = Setting(case.place)
    world = World(setting)

    detective = world.add(Entity("Detective", "character", "child", params.name))
    helper = world.add(Entity("Helper", "character", "child", params.helper_name))
    witness = world.add(Entity("Witness", "character", "adult", params.witness_name))
    clue = world.add(Entity("PartialClue", "object", "clue", "the partial clue"))
    sound = world.add(Entity("Sound", "object", "sound", case.sound))
    detective.memes["curiosity"] = 1.0
    helper.memes["patience"] = 1.0
    sound.meters["repetitions_heard"] = 0.0

    world.facts.update(
        case=case,
        method=method,
        detective=detective,
        helper=helper,
        witness=witness,
        clue=clue,
        sound=sound,
        setting=setting,
        solved=False,
    )

    world.say(f"In {setting.place}, {detective.label} wore a paper detective badge and examined a puzzling scene.")
    world.say(case.opening)
    world.say(f"{case.partial_clue} It was only a partial clue, so it could not tell the whole story.")
    world.say(f'Then everyone heard "{case.sound}."')
    world.say(f'"{SOUNDS[params.sound][0]}{SOUNDS[params.sound][1]}')
    world.say(f'"Could the sound be hiding another clue?" asked {helper.label}.')
    world.say(f'"Yes," said {detective.label}. "We will solve the problem by checking what repeats."')
    world.para()

    world.say(f"{detective.label} and {helper.label} {method[0]}.")
    world.say(f"{witness.label} pointed toward the strange object, but {detective.label} did not guess. The detective decided to {case.first_test}.")
    sound.meters["repetitions_heard"] = 1.0
    world.say(f"The sound stopped for a moment. Then it returned: {case.sound}.")
    world.say(f'"It came back when the same motion came back," said {helper.label}.')
    world.say(f'"That is useful evidence," replied {detective.label}. "Let us repeat the test before we trust it."')
    world.para()

    world.say(f"They {case.repeated_test}. {method[1].capitalize()}.")
    sound.meters["repetitions_heard"] = 2.0
    world.say(f"The result matched the first test. The partial clue, the repeated sound, and the moving object now pointed to one cause: {case.cause}.")
    detective.memes["confidence"] = 1.0
    helper.memes["confidence"] = 1.0
    world.say(f"{witness.label} nodded. " + '"' + "Your careful test found what a quick guess missed," + f'" said {witness.label}.')
    world.para()

    world.say(f"Together, they {case.repair}.")
    sound.meters["repetitions_heard"] = 3.0
    world.facts["solved"] = True
    world.say(f"They repeated the first check one last time. No sound answered.")
    world.say(f"{detective.label} completed the partial clue by understanding how its pieces fit together.")
    world.say(f"At last, {case.ending}.")
    world.say(f"The young detectives learned that problem solving means testing a good idea, repeating it, and letting evidence choose the answer.")
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly detective story about {detective.label}, a partial clue, and a repeating sound in {case.place}.",
        f"Show problem solving through repeated tests that reveal {case.cause}.",
        "Use sound effects and a brief dialogue exchange to show how evidence changes the detective's decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Why was the clue called partial?",
            f"It was called partial because {case.partial_clue[0].lower() + case.partial_clue[1:]} It gave the detectives only part of the information.",
        ),
        QAItem(
            f"How did {detective.label} solve the mystery?",
            f"{detective.label} changed one thing, watched what happened, repeated the test, and compared the results. That evidence revealed {case.cause}.",
        ),
        QAItem(
            f"What did {helper.label}'s question help the detectives do?",
            f"{helper.label}'s question encouraged the detectives to treat the sound as a clue and investigate it instead of guessing about it.",
        ),
        QAItem(
            "What lesson did the detectives learn?",
            "They learned that careful repetition can turn a partial clue into a clear answer when each test is based on evidence.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a detective?", "A detective is someone who gathers clues and uses careful reasoning to solve a mystery."),
        QAItem("What does partial mean?", "Partial means incomplete or showing only part of something."),
        QAItem("Why can repetition help solve a problem?", "Repetition helps people compare results and notice whether the same action causes the same effect."),
        QAItem("What is a sound effect?", "A sound effect is a written or performed sound, such as 'tap' or 'scritch,' used to show what is happening."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:12} ({entity.type:8}) meters={meters} memes={memes}")
    lines.append(f"  solved: {world.facts.get('solved')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "sound_effects"),
            asp.fact("feature", "repetition"),
            asp.fact("clue", "partial"),
            asp.fact("action", "compare"),
            asp.fact("action", "test"),
            asp.fact("action", "repeat"),
        ]
    )


ASP_RULES = r"""
feature(problem_solving).
feature(sound_effects).
feature(repetition).
clue(partial).
action(compare).
action(test).
action(repeat).

evidence_based :- clue(partial), action(test), action(compare).
case_solved :- evidence_based, action(repeat), feature(repetition).
story_ok :- case_solved, feature(problem_solving), feature(sound_effects).
#show story_ok/0.
"""


def asp_program(show: str = "#show story_ok/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if any(symbol.name == "story_ok" for symbol in model):
        for case_index in range(len(CASES)):
            sample = generate(StoryParams("Luna", "Milo", "Ms. Reed", case=case_index))
            if not sample.story or "partial" not in sample.story.lower():
                print("MISMATCH: generated story failed verification.")
                return 1
        print("OK: ASP twin and generated stories pass.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


GIRL_NAMES = ["Luna", "Mina", "Ivy", "Nora", "Ruby"]
BOY_NAMES = ["Milo", "Theo", "Eli", "Finn", "Owen"]
WITNESS_NAMES = ["Ms. Reed", "Mr. Vale", "Aunt June", "Coach Sam"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detective storyworld about partial clues and repeating sounds.")
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
    parser.add_argument("--witness-name")
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
        name=args.name or rng.choice(BOY_NAMES + ["Luna"]),
        helper_name=args.helper_name or rng.choice(GIRL_NAMES),
        witness_name=args.witness_name or rng.choice(WITNESS_NAMES),
        case=rng.randrange(len(CASES)),
        method=rng.randrange(len(METHODS)),
        sound=rng.randrange(len(SOUNDS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("story_ok" if any(symbol.name == "story_ok" for symbol in model) else "no model")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for case_index in range(len(CASES)):
            params = StoryParams("Luna", "Milo", "Ms. Reed", case=case_index, method=case_index % len(METHODS), sound=case_index % len(SOUNDS), seed=seed + case_index)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            rng = random.Random(seed + index)
            params = resolve_params(args, rng)
            params.seed = seed + index
            index += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
