#!/usr/bin/env python3
"""A child-friendly detective StoryWorld about a monger, curiosity, repetition, and change."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))

from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "The Monger's Repeating Clue"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class StoryParams:
    monger_name: str = "Mara"
    mystery: str = "the missing bell"
    place: str = "the market lane"
    object_name: str = "a silver bell"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    name: str
    object_name: str
    first_clue: str
    wrong_guess: str
    repeated_clue: str
    transformation: str
    resolution: str
    ending: str
    helper: str
    chant: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CASES = [
    Case(
        "the bell in the basket",
        "a silver bell",
        "three tiny flour marks led away from the empty bell hook",
        "the bell had been stolen by a sneaky crow",
        "each flour mark appeared beside a basket that had been moved twice",
        "a plain bread basket became a clue map when its handles were turned toward the hook",
        "Mara and the baker followed the repeated marks and found the bell beneath a folded cloth",
        "the bell rang above the stall while fresh bread cooled in a warm basket",
        "the baker",
        "Look, repeat, compare the sign; little clues can draw the line!",
    ),
    Case(
        "the blue button",
        "a blue coat button",
        "a blue thread curled three times beside the empty tailor's box",
        "the button had rolled into the drain",
        "the same curl appeared on a coat, a curtain, and a sack",
        "a torn scrap became a matching pattern when Mara folded it into three loops",
        "the tailor recognized the repeated pattern and found the button tucked in a pocket",
        "the repaired coat shone in the window, its blue button bright as a tiny moon",
        "the tailor",
        "Fold, repeat, and turn it round; hidden shapes can still be found!",
    ),
    Case(
        "the vanished map",
        "a little market map",
        "a trail of red chalk ended at three identical crates",
        "a gust had blown the map beyond the rooftops",
        "every crate had been turned from left to right",
        "a pile of empty boxes became an arrow when their labels were rotated",
        "Mara turned the crates in the repeated order and discovered the map inside the last one",
        "the map hung above the market gate, showing every friendly path home",
        "the cart driver",
        "Turn, repeat, and check the track; careful eyes can bring it back!",
    ),
    Case(
        "the golden key",
        "a golden key",
        "a round scratch circled the locked cupboard three times",
        "the key had been carried off by a mouse",
        "the scratch matched circles on a nearby spool and a toy wheel",
        "a broken wheel became a key-shaped guide after Mara traced its repeated curve",
        "the toy maker used the guide to spot the key inside a roll of bright ribbon",
        "the cupboard opened, and its shelves transformed into a neat display of toys",
        "the toy maker",
        "Circle, circle, test the clue; change one shape and find what is true!",
    ),
    Case(
        "the green feather",
        "a green feather",
        "green dots crossed the stone steps in pairs",
        "the feather had fallen into the fountain",
        "the pairs repeated beside the gate, the bench, and the flower pot",
        "a line of pebbles became a trail when Mara grouped them into matching pairs",
        "the gardener followed the paired trail to a nest behind the flower pot",
        "the green feather rested safely in the nest beside two newly hatched chicks",
        "the gardener",
        "Pair by pair, inspect the way; repeated clues can save the day!",
    ),
]

MONGERS = ["Mara", "Milo", "Nia"]
MYSTERIES = ["the missing bell", "the lost button", "the vanished map", "the hidden key"]
PLACES = ["the market lane", "the covered bazaar", "the old town square"]
OBJECTS = ["a silver bell", "a blue coat button", "a little market map", "a golden key"]


def choose_case(params: StoryParams) -> tuple[Case, int]:
    seed = params.seed if params.seed is not None else 0
    return CASES[seed % len(CASES)], (seed // len(CASES)) % 4


def setup_world(params: StoryParams, case: Case, route: int) -> World:
    world = World(params.place)
    monger = world.add(Entity(
        id="monger",
        kind="character",
        type="monger",
        label=params.monger_name,
        memes={"curiosity": 0.0, "patience": 0.0, "detective_skill": 0.0},
    ))
    object_entity = world.add(Entity(
        id="mystery_object",
        kind="thing",
        type="clue_object",
        label=case.object_name,
        owner="market",
        meters={"visibility": 0.0, "safety": 0.0},
    ))
    world.facts.update(
        monger=monger,
        object=object_entity,
        case=case,
        route=route,
        mystery=params.mystery,
        place=params.place,
    )
    return world


def tell(params: StoryParams) -> World:
    case, route = choose_case(params)
    world = setup_world(params, case, route)
    monger: Entity = world.facts["monger"]  # type: ignore[assignment]
    object_entity: Entity = world.facts["object"]  # type: ignore[assignment]

    openings = [
        f"In {world.place}, {monger.label} was known as a monger: a careful seller who knew the stories of every small object on the market tables.",
        f"At {world.place}, {monger.label} worked as a monger, sorting useful goods and noticing details that hurried shoppers missed.",
        f"Each morning in {world.place}, {monger.label} opened a monger's stall and placed every object where its owner could find it.",
        f"The stalls of {world.place} were waking when {monger.label}, a young monger, heard that a market mystery had begun.",
    ]
    world.say(openings[route])
    world.say(
        f"The trouble was {case.name}: {case.object_name} had disappeared. "
        f"Only {case.first_clue} remained."
    )
    world.say(
        f'"I am curious," said {monger.label}. "But I will not accuse anyone until the clues agree."'
    )
    world.para()

    world.say(
        f"At first, {monger.label} followed a tempting idea: {case.wrong_guess}. "
        "The path ended at an empty place, and the mystery grew no smaller."
    )
    monger.memes["curiosity"] = 1.0
    monger.meters["first_guess"] = 1.0
    world.fired.add("curiosity_started_investigation")
    world.say(
        f'The {case.helper} called, "What did you notice?" '
        f'{monger.label} answered, "The first clue is not alone. I need to see what repeats."'
    )
    world.para()

    world.say(
        f"{monger.label} checked the market slowly. {case.repeated_clue.capitalize()} "
        f"That repetition changed the case from a wild guess into a pattern."
    )
    monger.memes["patience"] = 1.0
    monger.memes["detective_skill"] = 1.0
    world.fired.add("repetition_confirmed")
    world.say(
        f'"Say the steps aloud," said the {case.helper}. '
        f'"Notice, repeat, then transform the clue," replied {monger.label}.'
    )
    world.say(f"Together they whispered a detective chant: \"{case.chant}\"")
    world.para()

    world.say(
        f"Following the pattern, {case.transformation}. "
        f"That transformation revealed the safe path: {case.resolution}."
    )
    object_entity.meters["visibility"] = 1.0
    object_entity.meters["safety"] = 1.0
    monger.memes["curiosity"] = 0.0
    monger.memes["confidence"] = 1.0
    world.fired.add("transformation_revealed_solution")
    world.say(
        f'"Curiosity helped me begin, repetition helped me check, and transformation helped me see," '
        f"said {monger.label}."
    )
    world.say(f"By evening, {case.ending}.")
    world.fired.add("mystery_resolved")
    world.facts.update(
        first_clue=case.first_clue,
        wrong_guess=case.wrong_guess,
        repeated_clue=case.repeated_clue,
        transformation=case.transformation,
        resolution=case.resolution,
        helper=case.helper,
        chant=case.chant,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    monger: Entity = world.facts["monger"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly detective story about monger {monger.label} solving {case.name} in {world.place}.",
        f"Show how curiosity begins the investigation, repetition confirms a clue, and transformation reveals the answer about {case.object_name}.",
        "Include a brief dialogue exchange in which the detective and a helper change what they decide or do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    monger: Entity = world.facts["monger"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {monger.label} investigate the mystery?",
            answer=f"{monger.label} was curious about {case.name}, but promised to wait for clues instead of accusing someone.",
        ),
        QAItem(
            question="What clue repeated during the investigation?",
            answer=f"The repeated clue was that {case.repeated_clue}. Seeing it more than once showed that it was a pattern, not an accident.",
        ),
        QAItem(
            question="How did transformation help solve the case?",
            answer=f"{case.transformation.capitalize()} This changed an ordinary object or mark into a useful guide.",
        ),
        QAItem(
            question="What did the helper and the monger say to each other?",
            answer=f"The {case.helper} asked what {monger.label} had noticed. {monger.label} explained that the first clue was not alone and that the repeated pattern needed checking.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{case.resolution.capitalize()} Then {case.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a monger?",
            answer="A monger is a person who sells or deals in a particular kind of goods. In this story, the monger sells market objects and notices their details.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is a wish to learn more or find out why something happened.",
        ),
        QAItem(
            question="Why is repetition useful in a mystery?",
            answer="A repeated mark, action, or shape can show a pattern and help a detective separate a real clue from a coincidence.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing something so it takes a new form or serves a new purpose.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:16} ({entity.type:12}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = ["monger(monger).", "curiosity.", "repetition.", "transformation."]
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for mystery in MYSTERIES:
        lines.append(asp.fact("mystery", mystery))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    return "\n".join(lines)


ASP_RULES = r"""
investigate(M) :- monger(M), curiosity.
check_pattern :- repetition, investigate(monger).
solve_case :- check_pattern, transformation.
good_story :- solve_case.
#show investigate/1.
#show check_pattern/0.
#show solve_case/0.
#show good_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/0."))
    if asp.atoms(model, "good_story"):
        for seed in range(len(CASES) * 2):
            sample = generate(StoryParams(seed=seed))
            if "monger" not in sample.story.lower():
                print("ASP verification failed: generated story omitted monger.")
                return 1
            if "curious" not in sample.story.lower() and "curiosity" not in sample.story.lower():
                print("ASP verification failed: generated story omitted curiosity.")
                return 1
        print("OK: ASP program grounded and generated stories passed.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective story world about a monger, curiosity, repetition, and transformation."
    )
    parser.add_argument("--monger-name", choices=MONGERS, default=None)
    parser.add_argument("--mystery", choices=MYSTERIES, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--object-name", choices=OBJECTS, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        monger_name=args.monger_name or rng.choice(MONGERS),
        mystery=args.mystery or rng.choice(MYSTERIES),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=args.seed,
    )


def validate_params(params: StoryParams) -> None:
    if params.monger_name not in MONGERS:
        raise StoryError(f"Unknown monger name: {params.monger_name}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object_name}")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
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


CURATED = [
    StoryParams(monger_name="Mara", mystery="the missing bell", place="the market lane", object_name="a silver bell", seed=0),
    StoryParams(monger_name="Milo", mystery="the lost button", place="the covered bazaar", object_name="a blue coat button", seed=1),
    StoryParams(monger_name="Nia", mystery="the vanished map", place="the old town square", object_name="a little market map", seed=2),
    StoryParams(monger_name="Mara", mystery="the hidden key", place="the market lane", object_name="a golden key", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show investigate/1. #show check_pattern/0. #show solve_case/0. #show good_story/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program("#show investigate/1. #show check_pattern/0. #show solve_case/0. #show good_story/0.")
        )
        for predicate in ("investigate", "check_pattern", "solve_case", "good_story"):
            print(asp.atoms(model, predicate))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        target = max(0, args.n)
        while len(samples) < target and attempts < max(target * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.monger_name} / {sample.params.mystery}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
