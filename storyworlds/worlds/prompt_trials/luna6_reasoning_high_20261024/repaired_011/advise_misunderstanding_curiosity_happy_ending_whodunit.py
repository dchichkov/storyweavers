#!/usr/bin/env python3
"""
A small whodunit storyworld about curiosity, mistaken assumptions, and kind advice.

A child notices that an important object has gone missing and suspects a friend.
With an adviser's help, the child asks questions and follows the evidence. The
mystery resolves happily, without turning a confusing clue into an accusation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_REPO_ROOT = None
for _parent in os.path.abspath(__file__).split(os.sep):
    del _parent
for _candidate in __import__("pathlib").Path(__file__).resolve().parents:
    if (_candidate / "storyworlds" / "results.py").is_file():
        _REPO_ROOT = str(_candidate)
        break
if _REPO_ROOT is None:
    raise RuntimeError("Could not locate storyworlds/results.py from this script.")
sys.path.insert(0, _REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    case_id: str
    kid: str
    adviser: str
    friend: str
    opening: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


@dataclass(frozen=True)
class Mystery:
    id: str
    item: str
    setting: str
    setup: str
    notice: str
    clue: str
    misread: str
    guess: str
    witness: str
    method: str
    reveal: str
    cause: str
    lesson: str
    resolution: str
    endings: tuple[str, str]


@dataclass(frozen=True)
class CaseState:
    item: str
    clue: str
    method: str
    solution: str


KIDS = ["Luna", "Arlo", "Bea", "Nico", "Uma", "Finn"]
ADVISERS = ["Aunt Mira", "Grandpa Sol", "Ms. Wren", "Uncle Ivo"]
FRIENDS = ["Tavi", "Jo", "Pip", "Remy", "Kit", "Milo"]

OPENINGS = [
    "At {setting}, even a tiny sound could become an important clue.",
    "{kid} liked asking how things worked, but this was a mystery that needed more than a guess.",
    "The friends were nearly ready at {setting} when an unexpected puzzle stopped them.",
]

MYSTERIES = [
    Mystery(
        id="wandering_handbell",
        item="the brass handbell",
        setting="the reading nook",
        setup=(
            "{kid} and {friend} were setting up a puppet show in the reading nook. "
            "They placed the brass handbell on a low shelf to ring at curtain time."
        ),
        notice="When curtain time arrived, the brass handbell was gone from the shelf.",
        clue=(
            "A loop of red yarn hung from the empty hook, and a faint curved line "
            "crossed the dust on the shelf."
        ),
        misread=(
            "{kid} saw {friend}'s red yarn beside the empty hook and wrongly wondered "
            "if {friend} had taken the handbell for the puppet show."
        ),
        guess="Could you have moved the handbell for the show?",
        witness=(
            "I looped my yarn there while mending the puppet's scarf. I heard a little "
            "ring when a breeze came through the open window."
        ),
        method=(
            "Taking that clue seriously, they followed the curved dust line and "
            "carefully drew the curtain aside."
        ),
        reveal="There was the handbell, nestled in a felt basket behind the curtain.",
        cause=(
            "A breeze from the open window had rolled the handbell off the shelf and "
            "into the basket; {friend}'s yarn was there because of the puppet repair."
        ),
        lesson=(
            "The yarn was a real clue about a mended puppet, but it was not proof that "
            "anyone had taken the bell."
        ),
        resolution=(
            "{kid} placed the handbell inside a shallow felt ring on the shelf, so "
            "another breeze could not send it wandering."
        ),
        endings=(
            "The bell gave a bright ding, and the puppet show began beneath a curtain "
            "that no longer hid any mysteries.",
            "As the puppets bowed, the handbell shone in its safe little ring, and "
            "{kid} smiled at the mystery's harmless hiding place.",
        ),
    ),
    Mystery(
        id="paper_moon_bookmark",
        item="the paper moon bookmark",
        setting="the little planetarium",
        setup=(
            "{kid} and {friend} were preparing a star story at the little planetarium. "
            "They set the paper moon bookmark beside the open star atlas."
        ),
        notice="When they opened the atlas to begin, the paper moon bookmark had vanished.",
        clue=(
            "A silver dot of craft glue shone beside the atlas, and one corner of the "
            "star map fluttered whenever the desk fan hummed."
        ),
        misread=(
            "{kid} saw the silver glue on {friend}'s fingers and wrongly wondered if "
            "{friend} had taken the bookmark to decorate a cardboard planet."
        ),
        guess="Did you take the paper moon to decorate your planet?",
        witness=(
            "I only glued my cardboard Saturn. That fan keeps lifting the star map; "
            "something might be caught underneath."
        ),
        method=(
            "They switched off the desk fan and gently lifted the fluttering star map "
            "together."
        ),
        reveal=(
            "The paper moon bookmark was tucked beneath the map, with one pointed tip "
            "peeking out."
        ),
        cause=(
            "The fan's breeze had slipped the light bookmark beneath the map, while "
            "{friend}'s silver glue belonged to the cardboard Saturn."
        ),
        lesson=(
            "The glue explained what {friend} had been making, but the fluttering map "
            "was the clue that led them to the bookmark."
        ),
        resolution=(
            "{kid} weighted the map with a smooth blue stone, then used the bookmark "
            "to open the atlas to its page about the moon."
        ),
        endings=(
            "The paper moon rested beside its painted twin in the atlas, no longer "
            "lost beneath a fluttering sky.",
            "Under the quiet fan, the friends read about the moon together, with the "
            "bookmark shining like a small silver smile.",
        ),
    ),
    Mystery(
        id="puppet_stage_key",
        item="the wooden stage key",
        setting="the puppet stage",
        setup=(
            "{kid} and {friend} were getting a puppet castle ready at the puppet "
            "stage. They left the wooden stage key beside the prop box."
        ),
        notice="When they needed to open the castle's little door, the wooden stage key was gone.",
        clue=(
            "Muddy bootprints stopped beside the prop box, and a thin streak of gold "
            "paint slanted down the stage ramp."
        ),
        misread=(
            "{kid} noticed {friend}'s muddy boots and wrongly thought {friend} might "
            "have taken the wooden key to play castle guard."
        ),
        guess="Did you move the wooden key to play the guard?",
        witness=(
            "I left my boots by the door. I heard a little tap under the stage a "
            "moment ago."
        ),
        method=(
            "Instead of deciding from the bootprints, they followed the gold paint "
            "streak down the ramp and peered beneath the stage."
        ),
        reveal=(
            "The wooden stage key lay behind the prop basket, right where the ramp "
            "ended."
        ),
        cause=(
            "The slanted ramp had let the key slide behind the basket; {friend}'s "
            "muddy bootprints were only from coming in out of the rain."
        ),
        lesson=(
            "The bootprints showed where {friend} had walked, but the gold streak "
            "helped explain where the key had rolled."
        ),
        resolution=(
            "{kid} put the key in a lidded prop box, and the friends opened the "
            "castle door together."
        ),
        endings=(
            "The puppet king stepped through the little door as the audience clapped, "
            "and the key stayed safely in its box.",
            "A warm stage light gleamed on the wooden key while the castle's door "
            "swung open for the first time that afternoon.",
        ),
    ),
]

MYSTERY_BY_ID = {mystery.id: mystery for mystery in MYSTERIES}


ASP_RULES = r"""
#show valid_case/1.

valid_case(C) :-
    case_id(C),
    has_item(C),
    has_clue(C),
    has_method(C),
    has_solution(C).
"""


def _is_complete(mystery: Mystery) -> bool:
    return all(
        isinstance(value, str) and value.strip()
        for value in (mystery.item, mystery.clue, mystery.method, mystery.cause)
    )


def valid_cases() -> list[str]:
    """Return registered cases with the minimum pieces needed for a fair solution."""
    return sorted(mystery.id for mystery in MYSTERIES if _is_complete(mystery))


def asp_facts() -> str:
    """Emit the case registry and completeness facts for the ASP twin."""
    from storyworlds import asp

    lines: list[str] = []
    for mystery in MYSTERIES:
        lines.append(asp.fact("case_id", mystery.id))
        if mystery.item.strip():
            lines.append(asp.fact("has_item", mystery.id))
        if mystery.clue.strip():
            lines.append(asp.fact("has_clue", mystery.id))
        if mystery.method.strip():
            lines.append(asp.fact("has_method", mystery.id))
        if mystery.cause.strip():
            lines.append(asp.fact("has_solution", mystery.id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_case/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[str]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted({case_id for (case_id,) in asp.atoms(model, "valid_case")})


def asp_verify() -> int:
    python_cases = set(valid_cases())
    clingo_cases = set(asp_valid_cases())
    if python_cases == clingo_cases:
        print(f"OK: clingo gate matches valid_cases() ({len(python_cases)} cases).")
        return 0

    print("MISMATCH between clingo and valid_cases():")
    if python_cases - clingo_cases:
        print("  only in Python:", sorted(python_cases - clingo_cases))
    if clingo_cases - python_cases:
        print("  only in clingo:", sorted(clingo_cases - python_cases))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A curious-child whodunit storyworld about advice and mistaken clues."
    )
    parser.add_argument("--case", help="choose a registered mystery case")
    parser.add_argument("--kid", help="choose the curious child")
    parser.add_argument("--adviser", help="choose the person who gives advice")
    parser.add_argument("--friend", help="choose the friend in the mystery")
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--all", action="store_true", help="show one story for every case")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true", help="show the simulated world state")
    parser.add_argument("--qa", action="store_true", help="show prompts and question-answer sets")
    parser.add_argument("--json", action="store_true", help="emit samples as JSON")
    parser.add_argument("--asp", action="store_true", help="list cases accepted by the ASP gate")
    parser.add_argument("--verify", action="store_true", help="check ASP parity and generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the grounded ASP program")
    return parser


def _validate_name(value: Optional[str], registry: list[str], field_name: str) -> None:
    if value is not None and value not in registry:
        choices = ", ".join(registry)
        raise StoryError(f"Unknown {field_name} {value!r}. Choose one of: {choices}.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    _validate_name(args.kid, KIDS, "kid")
    _validate_name(args.adviser, ADVISERS, "adviser")
    _validate_name(args.friend, FRIENDS, "friend")

    cases = valid_cases()
    if args.case is not None:
        if args.case not in MYSTERY_BY_ID:
            choices = ", ".join(cases)
            raise StoryError(f"Unknown mystery case {args.case!r}. Choose one of: {choices}.")
        if args.case not in cases:
            raise StoryError(f"The mystery case {args.case!r} does not have a complete solution.")
        cases = [args.case]
    if not cases:
        raise StoryError("No complete mystery cases are registered.")

    kid = args.kid or rng.choice(KIDS)
    friend = args.friend or rng.choice(FRIENDS)
    adviser = args.adviser or rng.choice(ADVISERS)
    if len({kid, friend, adviser}) != 3:
        raise StoryError("The kid, friend, and adviser must be three different characters.")

    return StoryParams(
        case_id=rng.choice(cases),
        kid=kid,
        adviser=adviser,
        friend=friend,
        opening=rng.randrange(len(OPENINGS)),
        ending=rng.randrange(2),
    )


def _check_params(params: StoryParams) -> Mystery:
    if params.case_id not in MYSTERY_BY_ID or params.case_id not in valid_cases():
        raise StoryError(f"No complete mystery is registered for case {params.case_id!r}.")
    if params.kid not in KIDS:
        raise StoryError(f"Unknown kid {params.kid!r}.")
    if params.adviser not in ADVISERS:
        raise StoryError(f"Unknown adviser {params.adviser!r}.")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend {params.friend!r}.")
    if len({params.kid, params.adviser, params.friend}) != 3:
        raise StoryError("The kid, friend, and adviser must be three different characters.")
    if not 0 <= params.opening < len(OPENINGS):
        raise StoryError(f"Opening index must be between 0 and {len(OPENINGS) - 1}.")
    if not 0 <= params.ending < 2:
        raise StoryError("Ending index must be 0 or 1.")
    return MYSTERY_BY_ID[params.case_id]


def generate(params: StoryParams) -> StorySample:
    mystery = _check_params(params)
    values = {
        "kid": params.kid,
        "friend": params.friend,
        "adviser": params.adviser,
        "setting": mystery.setting,
    }

    world = World()
    kid = world.add(
        Entity(
            id="kid",
            kind="character",
            label=params.kid,
            memes={"curiosity": 0.8, "worry": 0.2, "confidence": 0.3},
        )
    )
    adviser = world.add(
        Entity(
            id="adviser",
            kind="character",
            label=params.adviser,
            memes={"patience": 0.9, "care": 0.9},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            label=params.friend,
            memes={"kindness": 0.8, "worry": 0.1},
        )
    )
    item = world.add(
        Entity(
            id="missing_item",
            kind="object",
            label=mystery.item,
            meters={"visible": 0.0, "secured": 0.0},
            memes={"importance": 0.7},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="evidence",
            label=mystery.clue,
            meters={"noticed": 1.0, "checked": 0.0},
            memes={"ambiguity": 0.8},
        )
    )
    place = world.add(
        Entity(
            id="setting",
            kind="place",
            label=mystery.setting,
            meters={"searched": 0.0},
            memes={"mystery": 0.7},
        )
    )

    world.say(OPENINGS[params.opening].format(**values))
    world.say(mystery.setup.format(**values))
    world.para()

    world.say(mystery.notice)
    world.say(mystery.clue)
    world.say(mystery.misread.format(**values))
    world.say(f'"Who moved it?" {kid.label} wondered, looking from the clue to {friend.label}.')

    kid.memes["worry"] = 0.8
    kid.memes["curiosity"] = 1.0
    world.para()

    world.say(
        f'{kid.label} whispered, "{mystery.guess}" '
        f'{adviser.label} advised, "A clue is a question, not proof. Ask kindly, then check what you can." '
        f'{kid.label} replied, "Will you help me find out before I guess?"'
    )
    world.say(f'{friend.label} answered, "{mystery.witness}"')

    kid.memes["worry"] = 0.3
    adviser.memes["reassurance"] = 1.0
    friend.memes["worry"] = 0.0
    clue.meters["checked"] = 1.0
    world.say(mystery.method.format(**values))
    world.say(mystery.reveal)
    world.say(mystery.cause.format(**values))

    item.meters["visible"] = 1.0
    item.meters["secured"] = 1.0
    place.meters["searched"] = 1.0
    kid.memes["worry"] = 0.0
    kid.memes["confidence"] = 1.0
    kid.memes["joy"] = 0.9
    friend.memes["joy"] = 0.8
    adviser.memes["pride"] = 0.7

    world.para()
    world.say(mystery.lesson.format(**values))
    world.say(mystery.resolution.format(**values))
    world.say(mystery.endings[params.ending].format(**values))

    world.facts.update(
        case_id=mystery.id,
        item=mystery.item,
        setting=mystery.setting,
        clue=mystery.clue,
        misunderstanding=mystery.misread.format(**values),
        advice="Ask kindly, then check what the clue can prove.",
        method=mystery.method.format(**values),
        solution=mystery.cause.format(**values),
        resolved=True,
    )

    prompts = [
        "Write a child-friendly whodunit in which a curious child misunderstands a clue, receives kind advice, and solves the mystery without blaming a friend.",
        (
            f"Tell a happy-ending mystery about {params.kid} and {params.friend} at "
            f"{mystery.setting}, where {params.adviser} advises them to investigate carefully."
        ),
        (
            f"Write a warm whodunit with {mystery.item}, a misleading clue, a spoken "
            "exchange, a fair explanation, and a satisfying final image."
        ),
    ]

    story_qa = [
        QAItem(
            question="Who tried to solve the mystery?",
            answer=(
                f"{params.kid} investigated the missing {mystery.item.removeprefix('the ')} "
                f"with help from {params.friend} and advice from {params.adviser}."
            ),
        ),
        QAItem(
            question="What misunderstanding made the mystery more tense?",
            answer=(
                f"{params.kid} wrongly wondered whether {params.friend} had moved the "
                f"item because {mystery.misread.format(**values).split(' and wrongly')[0].split(' wrongly')[0].split(' saw ')[-1]}."
            ),
        ),
        QAItem(
            question=f"What advice did {params.adviser} give?",
            answer=(
                f"{params.adviser} advised {params.kid} that a clue was a question, not "
                "proof, and suggested asking kindly and checking the evidence."
            ),
        ),
        QAItem(
            question="How did the friends solve the mystery?",
            answer=(
                f"They followed the clue by {mystery.method.format(**values)[0].lower()}"
                f"{mystery.method.format(**values)[1:]}. They found the item and learned "
                f"that {mystery.cause.format(**values)}"
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=mystery.endings[params.ending].format(**values),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a whodunit?",
            answer=(
                "A whodunit is a mystery story in which characters gather clues and try "
                "to discover what happened or who was involved."
            ),
        ),
        QAItem(
            question="Why should someone check a clue before blaming a person?",
            answer=(
                "A clue can have more than one explanation, so checking it helps people "
                "understand what really happened before they blame anyone."
            ),
        ),
        QAItem(
            question="What does it mean to advise someone?",
            answer=(
                "To advise someone is to offer a helpful suggestion that can guide what "
                "they choose to do."
            ),
        ),
        QAItem(
            question="How can curiosity help solve a mystery?",
            answer=(
                "Curiosity encourages people to ask questions, notice details, and look "
                "for evidence instead of settling for a guess."
            ),
        ),
        QAItem(
            question="What makes a happy ending?",
            answer=(
                "A happy ending shows that a problem has been resolved and leaves the "
                "characters feeling safer, wiser, or glad to be together."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions -- answerable from the story text =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions -- child level, no story needed =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:14} ({entity.kind:9}) {' '.join(bits)}")
    if world.facts:
        lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            case_id=mystery.id,
            kid=KIDS[index % len(KIDS)],
            adviser=ADVISERS[index % len(ADVISERS)],
            friend=FRIENDS[index % len(FRIENDS)],
            opening=index % len(OPENINGS),
            ending=index % 2,
        )
        for index, mystery in enumerate(MYSTERIES)
    ]


CURATED = build_curated()


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def verify_generated_stories() -> int:
    for index, mystery in enumerate(MYSTERIES):
        params = StoryParams(
            case_id=mystery.id,
            kid=KIDS[index % len(KIDS)],
            adviser=ADVISERS[index % len(ADVISERS)],
            friend=FRIENDS[index % len(FRIENDS)],
            opening=index % len(OPENINGS),
            ending=index % 2,
            seed=index,
        )
        sample = generate(params)
        if sample.world is None:
            print(f"FAIL: {mystery.id} did not retain its world model.")
            return 1
        if mystery.item not in sample.story or mystery.reveal not in sample.story:
            print(f"FAIL: {mystery.id} did not include its missing item and reveal.")
            return 1
        if sample.story.count('"') < 6:
            print(f"FAIL: {mystery.id} did not include a spoken exchange.")
            return 1
        item_state = sample.world.entities["missing_item"]
        if item_state.meters.get("visible") != 1.0 or not sample.world.facts.get("resolved"):
            print(f"FAIL: {mystery.id} did not reach a resolved world state.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print(f"FAIL: {mystery.id} did not produce both Q&A sets.")
            return 1

    print(f"OK: generated and checked {len(MYSTERIES)} complete mystery stories.")
    return 0


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.show_asp:
            print(asp_program())
            return 0

        if args.verify:
            parity_status = asp_verify()
            if parity_status:
                return parity_status
            return verify_generated_stories()

        if args.asp:
            cases = asp_valid_cases()
            print(f"{len(cases)} complete mystery cases:\n")
            for case_id in cases:
                mystery = MYSTERY_BY_ID[case_id]
                print(f"  {case_id:24} -> {mystery.item} at {mystery.setting}")
            return 0

        if not args.all and args.n < 1:
            raise StoryError("The number of stories must be at least one.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            samples: list[StorySample] = []
            seen: set[str] = set()
            attempt = 0
            max_attempts = max(50, args.n * 100)
            while len(samples) < args.n and attempt < max_attempts:
                seed = base_seed + attempt
                attempt += 1
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                params.opening = seed % len(OPENINGS)
                params.ending = (seed // 3) % 2
                sample = generate(params)
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)

            if len(samples) != args.n:
                raise StoryError(
                    f"Could generate only {len(samples)} distinct stories after "
                    f"{max_attempts} attempts."
                )

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                mystery = MYSTERY_BY_ID[sample.params.case_id]
                header = f"### {sample.params.kid}: {mystery.item} at {mystery.setting}"
            elif len(samples) > 1:
                header = f"### mystery {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0

    except StoryError as error:
        print(f"No story: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
