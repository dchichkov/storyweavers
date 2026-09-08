#!/usr/bin/env python3
"""
A small detective storyworld about diffusing conflict through teamwork.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective: str
    partner: str
    object_name: str
    setting: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    problem: str
    conflict: str
    clue: str
    test: str
    cause: str
    teamwork: str
    repair: str
    lesson: str
    ending: str


CASES = [
    Case(
        "the school garden's welcome flag had vanished",
        "Mara thought Theo had moved it, while Theo thought Mara had forgotten it",
        "a blue thread caught on the empty flagpole",
        "they followed the thread together through the herb beds",
        "a gust had carried the flag into a low hedge",
        "Mara held the lantern while Theo searched beneath the leaves",
        "tied the flag with a shorter cord and added a small wind clip",
        "When a conflict spreads, patient teamwork can make room for every voice.",
        "the welcome flag waved safely above the garden gate",
    ),
    Case(
        "the library's story bell would not ring",
        "the helpers argued about who had damaged it",
        "a tiny wooden bead lay beside the bell rope",
        "they rolled the bead along the floor to see where it had come from",
        "a puppet cart had pulled the rope loose as it passed",
        "one child held the cart still while the other reattached the rope",
        "moved the cart away and marked a clear path",
        "A shared test is kinder and wiser than a quick accusation.",
        "the bell rang once before the next story began",
    ),
    Case(
        "the picnic map pointed everyone toward the pond",
        "two teammates blamed each other when the trail markers confused the group",
        "a wet leaf covered one arrow",
        "they lifted the leaf and compared the map with the path",
        "rain had pasted the leaf over the correct direction",
        "one teammate held the map flat while the other checked each marker",
        "covered the map and painted larger arrows on the posts",
        "Teamwork grows when people check the same facts together.",
        "friends followed the clear path to a sunny picnic blanket",
    ),
    Case(
        "the workshop's wooden bridge leaned to one side",
        "the builders disagreed about whose plank was crooked",
        "fresh sawdust marked one loose peg",
        "they placed a ruler across the bridge and tapped each peg gently",
        "one peg had slipped when a heavy box crossed",
        "they shared the ruler and steadied the bridge while replacing the peg",
        "added a second support beneath the crossing",
        "A conflict can diffuse when everyone works on the real problem.",
        "the little bridge held a row of toy wagons in a neat line",
    ),
]

OPENINGS = [
    "The detective story began with a small problem and a very loud disagreement.",
    "At first, the trouble seemed ordinary, but the arguing made it harder to see.",
    "Detective work was needed that morning because a small conflict had spread through the team.",
    "The mystery started when something useful disappeared and two friends stopped listening.",
]

DIALOGUES = [
    '"I think you caused it," said the partner. "Let us not guess yet," replied the detective.',
    '"That is not fair," said the detective. "Then help me test it," answered the partner.',
    '"We see the problem differently," said the partner. "We can still search together," said the detective.',
    '"I am worried," said the detective. "I am too," replied the partner, "so let us share the clues."',
]

CLOSINGS = [
    "The conflict had diffused into calm questions.",
    "Their teamwork had turned blame into a useful plan.",
    "The friends smiled because solving the mystery had also repaired their trust.",
    "The casebook received one final note: listen, test, and work together.",
]


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


def tell(world: World, params: StoryParams) -> None:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__str__())))
    rng = random.Random(seed ^ 0x4817)
    case = rng.choice(CASES)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUES)
    closing = rng.choice(CLOSINGS)

    detective = world.add(Entity("detective", "character", "child", params.detective))
    partner = world.add(Entity("partner", "character", "child", params.partner))
    object_entity = world.add(Entity("object", "thing", "clue_object", params.object_name))
    place = world.add(Entity("place", "thing", "setting", params.setting))

    detective.memes.update(curiosity=1.0, worry=0.0, trust=0.5, teamwork=0.0)
    partner.memes.update(curiosity=0.0, worry=1.0, trust=0.5, teamwork=0.0)
    object_entity.meters.update(found=0.0, repaired=0.0)
    place.meters.update(safe=0.0)

    world.say(opening)
    world.say(
        f"{detective.label}, a careful young detective, worked with {partner.label} in {place.label}."
    )
    world.say(f"Their important {object_entity.label} was needed before the day could continue.")

    world.para()
    world.say(f"They discovered that {case.problem}.")
    world.say(f"The trouble grew into conflict because {case.conflict}.")
    world.say(dialogue)

    detective.memes["worry"] = 1.0
    partner.memes["worry"] = 1.0
    detective.memes["trust"] = 0.3
    partner.memes["trust"] = 0.3
    world.fired.add("conflict_started")

    world.para()
    world.say(f"Instead of choosing sides, {detective.label} asked everyone to pause and look closely.")
    world.say(f"Then they found a useful clue: {case.clue}.")
    world.say(f"To test it, {case.test}.")
    world.say(f"The test showed that {case.cause}.")

    detective.memes["curiosity"] = 1.0
    partner.memes["curiosity"] = 1.0
    detective.memes["teamwork"] = 1.0
    partner.memes["teamwork"] = 1.0
    detective.memes["trust"] = 1.0
    partner.memes["trust"] = 1.0
    world.fired.add("teamwork_began")

    world.para()
    world.say(f"They diffused the conflict by listening to one another and sharing the work.")
    world.say(f"{case.teamwork.capitalize()}.")
    world.say(f"Together, they {case.repair}.")
    object_entity.meters["found"] = 1.0
    object_entity.meters["repaired"] = 1.0
    place.meters["safe"] = 1.0
    world.fired.add("case_resolved")

    world.say(f'{detective.label} closed the notebook. "{case.lesson}"')
    world.say(f"{closing} {case.ending}.")

    world.facts.update(
        detective=detective,
        partner=partner,
        object=object_entity,
        place=place,
        case=case,
    )


PLACES = {
    "community room": "the community room",
    "school garden": "the school garden",
    "library": "the library",
    "workshop": "the workshop",
}

OBJECTS = {
    "welcome flag": "welcome flag",
    "story bell": "story bell",
    "picnic map": "picnic map",
    "wooden bridge": "wooden bridge",
}

NAMES = ["Luna", "Milo", "Nia", "Owen", "Ivy", "Sam", "Zoe", "Kai"]


ASP_RULES = r"""
conflict_started :- conflict.
teamwork_resolved :- conflict, clue_checked, shared_work.
#show conflict_started/0.
#show teamwork_resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("conflict"),
            asp.fact("clue_checked"),
            asp.fact("shared_work"),
        ]
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detective stories about diffusing conflict through teamwork.")
    parser.add_argument("--detective")
    parser.add_argument("--partner")
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--setting", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective or rng.choice(NAMES)
    partner_choices = [name for name in NAMES if name != detective]
    partner = args.partner or rng.choice(partner_choices)
    return StoryParams(
        detective=detective,
        partner=partner,
        object_name=args.object_name or rng.choice(list(OBJECTS)),
        setting=args.setting or rng.choice(list(PLACES)),
    )


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        'Write a gentle detective story containing the word "diffuse".',
        f"Tell how {world.facts['detective'].label} and {world.facts['partner'].label} solve a conflict through teamwork.",
        f"Include the clue that {case.clue}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What problem did {detective.label} and {partner.label} investigate?",
            f"They investigated how {case.problem}.",
        ),
        QAItem(
            "Why did a conflict begin?",
            f"The conflict began because {case.conflict}.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"They found that {case.clue}.",
        ),
        QAItem(
            "How did teamwork help?",
            f"They worked together by {case.teamwork.lower()}.",
        ),
        QAItem(
            "What caused the trouble?",
            f"They discovered that {case.cause}.",
        ),
        QAItem(
            "What lesson did the detectives learn?",
            answer=case.lesson,
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem("What is conflict?", "Conflict is a disagreement or struggle between people or ideas."),
        QAItem("What is teamwork?", "Teamwork is when people cooperate and share jobs to reach a goal."),
        QAItem("What does diffuse mean in this story?", "To diffuse means to make a tense conflict calmer and less likely to grow."),
        QAItem("What does a detective do?", "A detective studies clues and tests ideas to understand what happened."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.detective == params.partner:
        raise StoryError("detective and partner must be different characters")
    if params.setting not in PLACES:
        raise StoryError(f"unknown setting: {params.setting}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"unknown object: {params.object_name}")

    world = World(PLACES[params.setting])
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict_started/0.\n#show teamwork_resolved/0."))
    names = {symbol.name for symbol in model}
    expected = {"conflict_started", "teamwork_resolved"}
    if names == expected:
        print("OK: ASP conflict/teamwork parity.")
        return 0
    print(f"MISMATCH: expected {sorted(expected)}, got {sorted(names)}")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict_started/0.\n#show teamwork_resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show conflict_started/0.\n#show teamwork_resolved/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "welcome flag", "community room", base_seed),
            StoryParams("Nia", "Owen", "story bell", "library", base_seed + 1),
            StoryParams("Ivy", "Sam", "wooden bridge", "workshop", base_seed + 2),
            StoryParams("Zoe", "Kai", "picnic map", "school garden", base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
