#!/usr/bin/env python3
"""A child-friendly detective storyworld about a digest, a beaker, and a muddy slope."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Sam", "Ravi", "Zoe"]
HELPERS = ["Grandma", "Uncle Jo", "Aunt May", "Dr. Moss"]
OPENINGS = [
    "Rain had polished the muddy slope until it shone like chocolate.",
    "A gray cloud hung above the muddy slope, and tiny streams curled between the stones.",
    "Luna found the muddy slope quiet except for a plop from the reeds.",
    "The field path ended at the muddy slope, where boot prints crossed like secret writing.",
    "Mist floated over the muddy slope as the little detective opened her notebook.",
]
DIALOGUE = [
    ("I found a beaker, but the clue inside is smudged.", "Then we must protect it and read every mark before we guess."),
    ("The trail stops here.", "A trail can hide under mud; let us look for what changed."),
    ("Should we follow the biggest footprint?", "Only after we compare it with the marks beside the beaker."),
    ("This digest has a missing corner.", "That missing piece may be the twist, not a mistake."),
    ("I want to solve the quest quickly.", "A careful detective lets the evidence choose the next step."),
]
TWISTS = [
    "the largest footprints belonged to a rolling garden cart, not the missing hiker",
    "the beaker had been carried by a beetle-sized toy wagon",
    "the muddy arrow pointed backward because the slope had washed the sign around",
    "the missing digest piece was stuck beneath the beaker's cork",
    "the quietest clue was a clean patch where a stone had recently moved",
]
SURPRISES = [
    "a blue bead popped from the mud",
    "a frog blinked beside the beaker",
    "a paper star floated out of a puddle",
    "a tiny bell rang under a flat stone",
    "a red thread appeared between two reeds",
]
ENDINGS = [
    "The rescued map dried beside the beaker while the slope glittered in the evening rain.",
    "The digest was repaired, and its final drawing showed the safe path home.",
    "The small mystery ended with warm tea, clean boots, and a clue board full of answered questions.",
    "The beaker held only rainwater at last, but the detective's notebook held the whole truth.",
    "The muddy slope kept its secrets, yet one bright trail now led everyone safely back.",
]


@dataclass(frozen=True)
class Case:
    key: str
    clue: str
    object_name: str
    action: str
    lesson: str


CASES = [
    Case("beaker_beacon", "a crescent scratch beside the puddle", "a glass beaker", "lifted the beaker with a cloth", "Good detectives protect clues before they explain them."),
    Case("digest_map", "three crumbs arranged like a little arrow", "a folded digest", "flattened the digest beneath a clean notebook", "Small details can guide a large search."),
    Case("carved_mark", "a fresh carved line on a flat root", "a carved wooden token", "compared the carving with the nearby footprints", "A mark matters most when it is compared with other evidence."),
    Case("muddy_wagon", "two narrow grooves beneath the mud", "a tin beaker", "brushed the grooves clear with a twig", "The safest answer comes from patient observation."),
    Case("reed_message", "a reed tied with a yellow thread", "a damp digest page", "placed the page in a dry envelope", "Care keeps a clue useful for everyone."),
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the muddy slope"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper: str
    case_key: str
    opening_index: int = 0
    dialogue_index: int = 0
    twist_index: int = 0
    surprise_index: int = 0
    ending_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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


def _case(key: str) -> Case:
    for case in CASES:
        if case.key == key:
            return case
    raise StoryError(f"Unknown case: {key}")


def _speak(world: World, name: str, line: str) -> None:
    world.say(f'"{line}" {name} said.')


def tell(setting: Setting, params: StoryParams) -> World:
    case = _case(params.case_key)
    world = World(setting)
    hero = world.add(Entity("hero", "detective", params.hero_name))
    helper = world.add(Entity("helper", "helper", params.helper))
    beaker = world.add(Entity("beaker", "evidence", case.object_name))
    digest = world.add(Entity("digest", "document", "the digest"))
    carving = world.add(Entity("carving", "mark", "the carved mark"))

    hero.memes.update(curiosity=1.0, patience=1.0, courage=1.0)
    helper.memes.update(wisdom=1.0, caution=1.0)
    beaker.meters.update(clear=0.0, protected=1.0, evidence=1.0)
    digest.meters.update(readable=0.0, repaired=0.0)
    carving.meters.update(observed=1.0)
    hero.owner = "case"
    beaker.holder = "hero"
    digest.holder = "hero"

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    line_one, line_two = DIALOGUE[params.dialogue_index % len(DIALOGUE)]
    twist = TWISTS[params.twist_index % len(TWISTS)]
    surprise = SURPRISES[params.surprise_index % len(SURPRISES)]
    ending = ENDINGS[params.ending_index % len(ENDINGS)]

    world.say(opening)
    world.say(
        f"{params.hero_name} was a young detective on a Quest to solve a small mystery at {setting.place}. "
        f"{case.clue.capitalize()} lay beside {case.object_name}."
    )
    _speak(world, params.hero_name, line_one)
    _speak(world, params.helper, line_two)
    world.para()

    world.say(
        f"The first clue was a digest, a short written report about what had happened. "
        f"It told of a missing trail marker and included a picture of something someone had tried to carve."
    )
    world.say(
        f"{params.hero_name} {case.action}. The muddy water made the page hard to read, "
        "so the detective did not rub it or pour anything into the beaker."
    )
    world.say(f"Then came a Surprise: {surprise}.")
    world.para()

    world.say(
        f"The footprints seemed to lead downhill, but the Twist was that {twist}. "
        f"{params.hero_name} compared the digest, the beaker, the carved mark, and the ground before choosing a path."
    )
    _speak(world, params.helper, "What does the evidence tell us now?")
    _speak(world, params.hero_name, f"It tells us to follow the careful clue, not the loudest one: {case.clue}.")
    world.say(
        f"Together they {case.action}. The beaker stayed safe, the digest became readable, "
        "and the little carved mark matched the sign beside the dry path."
    )
    world.para()

    world.say(
        f"The Quest was solved because {case.lesson.lower()} "
        f"{params.helper} helped mark the safe route with stones, and {params.hero_name} recorded the answer."
    )
    world.say(ending)

    world.fired.update({
        ("quest", params.case_key),
        ("twist", params.case_key),
        ("surprise", params.case_key),
        ("resolution", params.case_key),
    })
    world.facts.update(
        hero=hero,
        helper=helper,
        beaker=beaker,
        digest=digest,
        carving=carving,
        case=case,
        twist=twist,
        surprise=surprise,
        ending=ending,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly detective story about {p.hero_name} solving a Quest on {p.place}.",
        f"Include a digest, a beaker, and something to carve or a carved clue; use the case clue {case.clue}.",
        "Add a clear Twist and Surprise, then resolve the mystery through careful observation and safe choices.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What Quest was {p.hero_name} trying to complete?",
            f"{p.hero_name} was trying to solve a small mystery at {p.place by if False else p.place}. "
            "The detective needed to understand the missing trail marker and find the safe route.",
        ),
        QAItem(
            "What clues did the detective examine?",
            f"The detective examined {case.object_name}, the digest, the carved mark, and the muddy ground. "
            f"The important clue was {case.clue}.",
        ),
        QAItem(
            "What was the Twist?",
            f"The Twist was that {world.facts['twist']}. This changed how the footprints should be understood.",
        ),
        QAItem(
            "What Surprise happened?",
            f"The Surprise was that {world.facts['surprise']}. It added a new detail without making the detective abandon careful thinking.",
        ),
        QAItem(
            "How was the mystery solved?",
            f"{p.hero_name} protected the evidence, compared the digest, beaker, carving, and footprints, and followed the careful clue. "
            f"{case.lesson}",
        ),
        QAItem(
            "What showed that the ending was safe?",
            f"The beaker stayed safe, the digest became readable, and the safe route was marked with stones beside the muddy slope.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a digest?", "A digest is a short summary or report that gives the main facts about something."),
        QAItem("What is a beaker?", "A beaker is a container, often made of glass, used to hold or observe liquids."),
        QAItem("What does it mean to carve?", "To carve means to cut a mark or shape into a firm material such as wood."),
        QAItem("What is a Twist in a story?", "A Twist is an unexpected change that makes the mystery or story look different."),
        QAItem("What is a Quest?", "A Quest is a purposeful search or journey to complete an important task."),
        QAItem("What is a Surprise?", "A Surprise is something unexpected that catches attention and adds new information."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} {entity.label} "
            f"owner={entity.owner} holder={entity.holder} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(H,D) :- detective(H), digest(D), beaker(B), carving(C).
twist(H,Q) :- quest(H,Q), evidence(Q).
surprise(H,Q) :- twist(H,Q), muddy_slope(Q).
safe_resolution(H,Q) :- surprise(H,Q), careful(H).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("detective", "hero"),
        asp.fact("digest", "digest"),
        asp.fact("beaker", "beaker"),
        asp.fact("carving", "carving"),
        asp.fact("evidence", "case"),
        asp.fact("muddy_slope", "case"),
        asp.fact("careful", "hero"),
    ])


def asp_program(show: str = "#show safe_resolution/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A detective storyworld on a muddy slope.")
    parser.add_argument("--place", default="the muddy slope")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--case", dest="case_key", choices=[c.key for c in CASES])
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
    return StoryParams(
        place=args.place,
        hero_name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        case_key=args.case_key or rng.choice([c.key for c in CASES]),
        opening_index=rng.randrange(len(OPENINGS)),
        dialogue_index=rng.randrange(len(DIALOGUE)),
        twist_index=rng.randrange(len(TWISTS)),
        surprise_index=rng.randrange(len(SURPRISES)),
        ending_index=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(params.place), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not asp.atoms(model, "safe_resolution"):
        raise StoryError("ASP verification found no safe resolution.")
    for case in CASES:
        params = StoryParams("the muddy slope", "Luna", "Grandma", case.key)
        sample = generate(params)
        if "digest" not in sample.story or "beaker" not in sample.story:
            raise StoryError("Generated story omitted required evidence words.")
        if not sample.world or ("resolution", case.key) not in sample.world.fired:
            raise StoryError("Python world did not record a resolution.")
    return 0


CURATED = [
    StoryParams("the muddy slope", "Luna", "Grandma", "beaker_beacon", 0, 0, 0, 0, 0),
    StoryParams("the muddy slope", "Milo", "Uncle Jo", "digest_map", 1, 1, 1, 1, 1),
    StoryParams("the muddy slope", "Nia", "Aunt May", "carved_mark", 2, 2, 2, 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest/2.\n#show twist/2.\n#show surprise/2.\n#show safe_resolution/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show quest/2.\n#show twist/2.\n#show surprise/2.\n#show safe_resolution/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
