#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a vivid craft workshop, a small advantage,
and a lesson learned through dialogue.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass(frozen=True)
class Workshop:
    key: str
    place: str
    light: str
    table: str
    sound: str


@dataclass(frozen=True)
class CraftCase:
    key: str
    project: str
    material: str
    vivid_detail: str
    advantage: str
    trouble: str
    first_guess: str
    test: str
    twist: str
    repair: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    workshop: str
    hero_name: str
    helper_name: str
    case_id: str = "lantern"
    detail_id: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


WORKSHOPS = {
    "moonlit": Workshop(
        "moonlit",
        "the moonlit craft workshop",
        "silver moonlight",
        "a broad pine table",
        "the soft tick of a wall clock",
    ),
    "rainy": Workshop(
        "rainy",
        "the rainy craft workshop",
        "a warm amber lamp",
        "a scarred oak table",
        "the hush and patter of rain",
    ),
    "cozy": Workshop(
        "cozy",
        "the cozy craft workshop",
        "a row of golden lamps",
        "a round maple table",
        "the sleepy hum of the heater",
    ),
}

CASES = {
    "lantern": CraftCase(
        "lantern",
        "a paper lantern",
        "colored paper",
        "a vivid blue moon cut into its side",
        "a folding ruler that made every crease even",
        "the lantern leaned to one side and its little door would not close",
        "that the glue had simply dried badly",
        "fold the paper beside the ruler, check each crease, and test the door before adding more glue",
        "the folding ruler had made one crease too close to the edge, so the lantern had no balanced side",
        "open the careful crease, measure a fresh center line, and fasten the door with a paper tab",
        "a small advantage helps only when it is used with care and checked against the whole design",
        "the vivid blue moon shone evenly while the lantern rested straight above the quiet table",
    ),
    "kite": CraftCase(
        "kite",
        "a star kite",
        "thin willow sticks",
        "a vivid orange tail curled like a sunrise",
        "a light frame that could lift in a gentle breeze",
        "the kite spun instead of rising",
        "that the wind was too weak",
        "hold the kite by its balance point, compare both sides, and shorten the heavier tail",
        "the bright tail had been tied with one extra knot, giving one side too much weight",
        "remove the extra knot, retie the tail at the center, and try the kite again in the garden",
        "an advantage in materials cannot replace balance, patience, and a careful test",
        "the star kite climbed quietly, its vivid tail streaming like a small ribbon of dawn",
    ),
    "puppet": CraftCase(
        "puppet",
        "a fox puppet",
        "soft felt",
        "vivid green eyes that winked when the string was pulled",
        "a springy wooden lever that could make the paw wave",
        "the fox waved both paws whenever the hero pulled only one string",
        "that the lever was broken",
        "trace each string, move the lever slowly, and watch which knot moved with it",
        "the two strings had been tied through one loop, so the clever lever controlled both paws",
        "separate the strings, tie each to its own loop, and test one gentle pull at a time",
        "a clever tool becomes useful when its parts remain clear and separate",
        "the fox puppet bowed with one paw and waved with the other beneath the sleepy lamp",
    ),
    "box": CraftCase(
        "box",
        "a keepsake box",
        "thin cedar strips",
        "a vivid red star painted on the lid",
        "a magnetic clasp that could hold the lid shut",
        "the lid snapped closed before the small treasures were inside",
        "that the clasp was too strong",
        "place a paper spacer beneath the clasp, close the lid gently, and inspect the hinge",
        "the hinge had been mounted backward, making the lid swing past its resting place",
        "turn the hinge around, lower the clasp plate, and test the lid with an empty box",
        "a useful advantage still needs the right position before it can help",
        "the red star gleamed on a box that opened softly and held a tiny collection of treasures",
    ),
}

OPENINGS = (
    "{hero} found the workshop awake with {sound}.",
    "When the evening star appeared, {hero} stepped into {place}.",
    "The craft workshop glowed softly, and {hero} carried a new idea to the table.",
    "Under {light}, {hero} and {helper} began a quiet making-time adventure.",
)

BRIDGES = (
    "The colors looked lovely, but {hero} remembered that lovely work also needed careful steps.",
    "{helper} placed the useful tool beside the materials instead of rushing to use it.",
    "A tiny mark on the table became their first clue.",
    "They let the clock tick twice before changing anything.",
)


def story_reasonable(workshop: str, case_id: str) -> bool:
    return workshop in WORKSHOPS and case_id in CASES


def explain_rejection(workshop: str, case_id: str) -> str:
    if workshop not in WORKSHOPS:
        return f"The workshop '{workshop}' is not in this storyworld."
    return f"The craft project '{case_id}' is not in this storyworld."


def tell(params: StoryParams) -> World:
    if not story_reasonable(params.workshop, params.case_id):
        raise StoryError(explain_rejection(params.workshop, params.case_id))

    workshop = WORKSHOPS[params.workshop]
    case = CASES[params.case_id]
    world = World(workshop)

    hero = world.add(Entity(params.hero_name, "character", params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_name))
    project = world.add(Entity("project", "craft", case.project))
    tool = world.add(Entity("tool", "tool", case.advantage))
    project.add_meter("unfinished", 1)
    hero.add_meme("curious", 1)
    helper.add_meme("patient", 1)

    world.facts.update(
        hero=hero,
        helper=helper,
        project=project,
        tool=tool,
        case=case,
    )

    world.say(
        OPENINGS[params.detail_id % len(OPENINGS)].format(
            hero=hero.label,
            helper=helper.label,
            place=workshop.place,
            light=workshop.light,
            sound=workshop.sound,
        )
    )
    world.say(
        f"In {workshop.place}, they worked at {workshop.table} while {workshop.sound} "
        f"filled the room."
    )
    world.say(
        f"Tonight they were making {case.project} from {case.material}. "
        f"It already had {case.vivid_detail}, bright enough to paint a dream."
    )
    world.say(
        f"{helper.label} showed {hero.label} {case.advantage}. "
        f"'This gives us an advantage,' said {helper.label}, 'but it cannot do the thinking for us.'"
    )
    world.say(
        BRIDGES[params.detail_id % len(BRIDGES)].format(hero=hero.label, helper=helper.label)
    )
    world.say(f"Then {case.trouble}.")
    world.say(f"{hero.label} first guessed {case.first_guess}.")
    world.say(
        f"'Let us not blame the tool yet,' said {helper.label}. "
        f"'What can we learn by looking closely?'"
    )
    world.say(
        f"Together they decided to {case.test}. "
        f"{hero.label} noticed that the careful test changed what they knew."
    )
    world.say(f"The twist was that {case.twist}.")
    world.say(
        f"'Now I see it,' said {hero.label}. "
        f"{helper.label} smiled. 'Then we can {case.repair}.'"
    )
    world.say(
        f"They worked slowly, and the project became steady. "
        f"They learned that {case.lesson}."
    )
    world.say(
        f"At bedtime, {case.ending}. "
        f"{hero.label} turned out the lamp, carrying the new lesson like a small warm light."
    )
    project.add_meter("unfinished", -1)
    project.add_meme("completed", 1)
    hero.add_meme("understanding", 1)
    helper.add_meme("trust", 1)
    return world


def generation_prompts(world: World) -> list[str]:
    case: CraftCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a bedtime story in which {hero.label} builds {case.project} in a craft workshop.",
        f"Include vivid imagery, a useful advantage, gentle dialogue, a fair test, and a lesson learned about {case.lesson}.",
        f"Show how the problem with {case.project} changes after the characters investigate {case.trouble}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: CraftCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What were {hero.label} and {helper.label} making?",
            f"They were making {case.project} from {case.material}, with {case.vivid_detail}.",
        ),
        QAItem(
            "What advantage did they have?",
            f"They had {case.advantage}. It helped only after they used it carefully.",
        ),
        QAItem(
            "What problem appeared?",
            f"The problem was that {case.trouble}.",
        ),
        QAItem(
            "How did they investigate the problem?",
            f"They chose to {case.test}, which helped them find the real cause.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {case.twist}.",
        ),
        QAItem(
            "What lesson did they learn?",
            f"They learned that {case.lesson}.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended when {case.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should a craft project be tested before it is finished?",
            "Testing can reveal a loose, uneven, or misplaced part before the project is used.",
        ),
        QAItem(
            "What is an advantage?",
            "An advantage is something that makes a task easier or gives someone a helpful starting point.",
        ),
        QAItem(
            "Why is dialogue useful in a story?",
            "Dialogue lets characters share ideas, ask questions, and change what they decide to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_workshop/1.
#show valid_case/1.
#show valid_story/2.

valid_workshop(W) :- workshop(W).
valid_case(C) :- craft_case(C).
valid_story(W,C) :- valid_workshop(W), valid_case(C), supports(W,C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [asp.fact("workshop", key) for key in WORKSHOPS]
    for case_id in CASES:
        lines.append(asp.fact("craft_case", case_id))
    for workshop in WORKSHOPS:
        for case_id in CASES:
            lines.append(asp.fact("supports", workshop, case_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_workshop/1."))
    found = {row[0] for row in asp.atoms(model, "valid_workshop")}
    expected = set(WORKSHOPS)
    if found != expected:
        print("MISMATCH between ASP and Python workshop registries.")
        print("ASP only:", sorted(found - expected))
        print("Python only:", sorted(expected - found))
        return 1

    for key in WORKSHOPS:
        sample = generate(
            StoryParams(
                workshop=key,
                hero_name="Luna",
                helper_name="Mara",
                case_id="lantern",
                seed=17,
            )
        )
        if not sample.story or "Luna" not in sample.story or "Mara" not in sample.story:
            print("Generated story exercise failed.")
            return 1

    print(f"OK: ASP gate matches Python registry ({len(expected)} workshops); stories exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A bedtime craft-workshop storyworld about vivid making and a useful advantage."
    )
    parser.add_argument("--workshop", choices=sorted(WORKSHOPS))
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--case-id", choices=sorted(CASES))
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    workshop = args.workshop or rng.choice(list(WORKSHOPS))
    case_id = args.case_id or rng.choice(list(CASES))
    hero_name = args.hero_name or rng.choice(["Luna", "Milo", "Tess", "Nia", "Owen"])
    helper_name = args.helper_name or rng.choice(["Mara", "Grandma", "Ari", "Ben", "Aunt Rose"])
    if hero_name == helper_name:
        raise StoryError("The hero and helper must have different names.")
    detail_id = (sample_seed if sample_seed is not None else rng.randrange(100000)) % len(BRIDGES)
    return StoryParams(
        workshop=workshop,
        hero_name=hero_name,
        helper_name=helper_name,
        case_id=case_id,
        detail_id=detail_id,
        seed=sample_seed,
    )


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


def dump_trace(world: World) -> str:
    lines = [
        "--- world trace ---",
        f"workshop: {world.workshop.place}",
        f"project: {world.facts['project'].label}",  # type: ignore[union-attr]
    ]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


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


CURATED = [
    StoryParams("moonlit", "Luna", "Mara", "lantern", 0),
    StoryParams("rainy", "Milo", "Grandma", "kite", 1),
    StoryParams("cozy", "Tess", "Ari", "puppet", 2),
    StoryParams("moonlit", "Nia", "Aunt Rose", "box", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        for row in sorted(asp.atoms(model, "valid_story")):
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            sample_seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
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
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
