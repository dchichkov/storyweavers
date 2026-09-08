#!/usr/bin/env python3
"""
A tiny rhyming storyworld about a charged curiosity, a dangerous label, and a
flashback that helps a child choose repair over a bad ending.
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
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


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
    fired: set[str] = field(default_factory=set)

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


@dataclass(frozen=True)
class Case:
    id: str
    object_name: str
    object_phrase: str
    danger: str
    charge_source: str
    clue: str
    repair: str
    ending: str


CASES = {
    "lantern": Case(
        "lantern",
        "lantern",
        "a bright brass lantern",
        "the charge could leap to the wet rail",
        "a humming battery hidden beneath its base",
        "a blue spark crawled toward the dry wooden handle",
        "lifted the lantern with the wooden handle and set it inside a dry safety box",
        "The lantern shone softly, and the wet rail stayed dark and still.",
    ),
    "music_box": Case(
        "music_box",
        "music box",
        "a silver music box",
        "the charge could jump into the puddle by the door",
        "a tiny winding coil beneath its lid",
        "the sparks faded whenever the lid was closed",
        "closed the lid, dried the floor, and carried the box to a rubber mat",
        "The tune played gently, while the puddle reflected only the moon.",
    ),
    "toy_train": Case(
        "toy train",
        "toy train",
        "a little copper toy train",
        "the charge could race along its metal track",
        "a fresh cell clipped beneath one carriage",
        "the wheels stopped when the red switch was turned down",
        "turned the red switch down and moved the train onto a cloth track",
        "The toy train rested safely, puffing one quiet paper-cloud puff.",
    ),
    "star_badge": Case(
        "star badge",
        "star badge",
        "a silver star badge",
        "the charge could sting anyone who grabbed its sharp pin",
        "a static lining inside its velvet case",
        "the badge crackled only when rubbed against the wool scarf",
        "laid the scarf aside and lifted the badge by its broad ribbon",
        "The star badge gleamed on its ribbon, harmless and bright.",
    ),
}

NAMES = ["Luna", "Mira", "Theo", "Nia", "Owen", "Zara"]
ROLES = ["girl", "boy"]
OPENINGS = [
    "At dusk in the little hall",
    "Beneath the moonlit wall",
    "When silver raindrops tapped the pane",
    "Before the evening train",
    "In a room both snug and small",
]
REFLECTIONS = [
    "Curiosity needs care, not a daring race.",
    "A label cannot tell a person's whole heart or face.",
    "When a mistake is made, repair can start the way.",
    "A calm question can brighten a dangerous day.",
]

REJECTED_LABEL = (
    "The word 'sociopath' is an inaccurate and hurtful label for a person. "
    "This story uses it only as a mistaken word that the characters correct."
)


@dataclass
class StoryParams:
    case: str
    name: str
    role: str
    opening: int
    reflection: int
    seed: Optional[int] = None


def _meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    case = CASES[params.case]
    world = World()
    child = world.add(Entity(params.name, "character", params.name))
    friend = world.add(Entity("Pip", "character", "Pip"))
    object_entity = world.add(Entity("charged_object", "object", case.object_name))
    room = world.add(Entity("hall", "place", "the little hall"))
    world.facts.update(case=case, child=child, friend=friend, object=object_entity, room=room)

    _meter(object_entity, "charge", 1.0)
    _meme(child, "curiosity", 1.0)
    _meme(friend, "care", 1.0)

    opening = OPENINGS[params.opening % len(OPENINGS)]
    reflection = REFLECTIONS[params.reflection % len(REFLECTIONS)]

    world.say(
        f"{opening}, {params.name} came to call, "
        f"with bright-eyed curiosity, curious and tall. "
        f"{case.object_phrase.capitalize()} waited by the chair, "
        f"and a soft little hum trembled in the air."
    )
    world.say(
        f'"What makes it buzz?" asked {params.name}. "Can I touch and see?" '
        f'"First look, then ask," said Pip. "Let safety be our key."'
    )
    world.say(
        f"The charge gave a tiny crackle; the room grew still and strange. "
        f"{case.danger.capitalize()}, so one quick touch could change the range."
    )
    world.para()

    world.say(
        f"Then {params.name} remembered a flash from an earlier day: "
        f"a rushed hand, a startled shout, and a toy swept away. "
        f"In that flashback, a grown-up had said, "
        f'"Curiosity is good when careful questions lead."'
    )
    world.fired.add("flashback")

    world.say(
        f'Pip whispered, "Someone called a person a sociopath when they made a mistake." '
        f'"That word can hurt," said {params.name}. "A mistake is not a whole person\'s fate."'
    )
    world.say(
        f'"We should not use that label," said Pip. "We can name the action instead." '
        f'"The rushed choice was unsafe," said {params.name}. "Now let us learn the best."'
    )
    world.fired.add("harmful_label_corrected")
    world.para()

    world.say(
        f"{case.clue.capitalize()}, clear as a bell, "
        f"so {params.name} could choose well. "
        f"{params.name} {case.repair}."
    )
    _meter(object_entity, "charge", 0.0)
    _meme(child, "curiosity", 0.5)
    _meme(child, "confidence", 1.0)
    world.fired.add("repair")

    world.say(
        f"{case.ending} "
        f'"I was curious," said {params.name}, "but I can pause before I try." '
        f'"And I can ask for help," said Pip. "That keeps both of us safe nearby."'
    )
    world.say(
        f"The bad ending they had feared did not arrive at all; "
        f"care turned a risky spark into a lesson for the hall. "
        f"{reflection} "
        f"With a quiet glow and a thoughtful grin, the two friends let the safe evening begin."
    )
    world.facts["resolved"] = True
    world.facts["bad_ending_avoided"] = True
    world.facts["flashback_used"] = True
    return world


def valid_cases() -> list[str]:
    return sorted(CASES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.case not in CASES:
        raise StoryError(f"Unknown case {args.case!r}. Choose a listed charged object.")
    case = args.case or rng.choice(valid_cases())
    return StoryParams(
        case=case,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    return [
        f"Write a rhyming story about curiosity near {case.object_phrase}.",
        "Include a flashback, a bad ending that is avoided, and a kind correction of the word sociopath.",
        f"Use the charge from {case.charge_source} as the concrete danger and end with repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    child: Entity = world.facts["child"]
    return [
        QAItem(
            "What made the object dangerous?",
            f"The {case.object_name} carried a charge from {case.charge_source}, and {case.danger}.",
        ),
        QAItem(
            f"Why did {child.label} stop before touching it?",
            f"{child.label} remembered a flashback about a rushed unsafe choice and noticed the clue that {case.clue}.",
        ),
        QAItem(
            "How did the characters handle the word sociopath?",
            "They explained that it is a hurtful and inaccurate label, then named the unsafe action instead of judging a whole person.",
        ),
        QAItem(
            "What bad ending did the friends avoid?",
            f"They avoided the danger that {case.danger}. Careful observation and the repair step kept everyone safe.",
        ),
        QAItem(
            "How was curiosity shown responsibly?",
            f"{child.label} asked questions, listened to Pip, used the clue, and {case.repair}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an electric charge?",
            "Electric charge is a property of matter that can cause attraction, repulsion, or a flow of electricity.",
        ),
        QAItem(
            "Why should a person be careful around an unknown charged object?",
            "An unknown charged object may shock someone, damage equipment, or send electricity through an unsafe path, so a person should keep back and ask a knowledgeable adult for help.",
        ),
        QAItem(
            "Why is sociopath a poor label for a person?",
            "It is an imprecise, stigmatizing label rather than a respectful diagnosis. It is kinder and clearer to describe a specific action or discuss mental health with a qualified professional.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
charged_object(X) :- object(X), has_charge(X).
safe_case(C) :- story_case(C), has_clue(C), has_repair(C).
valid_story(C) :- charged_object(C), safe_case(C), flashback, kind_language.
"""


def asp_facts() -> str:
    import asp

    lines = ["flashback.", "kind_language."]
    for case_id, case in CASES.items():
        lines.extend(
            [
                asp.fact("story_case", case_id),
                asp.fact("object", case_id),
                asp.fact("has_charge", case_id),
                asp.fact("has_clue", case_id),
                asp.fact("has_repair", case_id),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> set[str]:
    import asp

    model = asp.one_model(asp_program())
    return {row[0] for row in asp.atoms(model, "valid_story")}


def asp_verify() -> int:
    py = set(valid_cases())
    clingo_cases = asp_valid_cases()
    if py == clingo_cases:
        print(f"OK: clingo gate matches Python cases ({len(py)} cases).")
        return 0
    print("Mismatch between Python and ASP:")
    print("only in Python:", sorted(py - clingo_cases))
    print("only in ASP:", sorted(clingo_cases - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"Unsupported case: {params.case}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rhyming charge-and-curiosity storyworld."
    )
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--name")
    parser.add_argument("--role", choices=ROLES)
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


CURATED = [
    StoryParams("lantern", "Luna", "girl", 0, 0),
    StoryParams("music_box", "Mira", "girl", 1, 1),
    StoryParams("toy_train", "Theo", "boy", 2, 2),
    StoryParams("star_badge", "Nia", "girl", 3, 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                raise StoryError("Generated verification story was incomplete.")
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
