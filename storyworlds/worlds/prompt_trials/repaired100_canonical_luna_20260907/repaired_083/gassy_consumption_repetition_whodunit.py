#!/usr/bin/env python3
"""
A small child-friendly whodunit about a gassy snack, repeated clues, and careful
problem solving.

The mystery is gentle: a noisy tummy is not a crime, and the detectives solve
the case by comparing what was eaten, when it was eaten, and what happened next.
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

    def meter(self, name: str, amount: float) -> None:
        self.meters[name] = self.meters.get(name, 0.0) + amount

    def feel(self, name: str, amount: float) -> None:
        self.memes[name] = self.memes.get(name, 0.0) + amount


@dataclass(frozen=True)
class Snack:
    id: str
    label: str
    gas_score: int
    color: str


@dataclass(frozen=True)
class Case:
    id: str
    place: str
    setup: str
    repeated_clue: str
    suspects: tuple[str, ...]
    first_guess: str
    test: str
    culprit: str
    reveal: str
    repair: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    case_id: str
    telling_mode: str = "clue_first"
    detail_id: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


PLACES = {
    "moonlit_pantry": "the moonlit pantry",
    "rainy_cafe": "the rainy-day café",
    "garden_table": "the little garden table",
}

SNACKS = {
    "beans": Snack("beans", "a bowl of beans", 4, "cream"),
    "fizz": Snack("fizz", "a fizzy drink", 3, "gold"),
    "cabbage": Snack("cabbage", "a crunchy cabbage wrap", 2, "green"),
    "toast": Snack("toast", "a slice of toast", 0, "brown"),
}

CASES = {
    "bean_bowl": Case(
        id="bean_bowl",
        place="moonlit_pantry",
        setup="A tiny bell rang each time someone opened the snack cupboard",
        repeated_clue="three round bean stickers appeared in a row on the supper chart",
        suspects=("the cupboard", "the fizzy drink", "the bowl of beans"),
        first_guess="that the cupboard itself was making the mysterious tummy sounds",
        test="count the stickers, read the snack chart, and compare each snack with the time of the noises",
        culprit="the repeated bean snack",
        reveal="the beans had been served at supper and then served again as a late snack",
        repair="circle the second bean entry, offer water, and choose a small toast snack instead",
        lesson="a repeated serving can explain a repeated result, so checking the whole record matters",
        ending="the chart showed one bean bowl crossed out, and a quiet toast crumb rested beside the water cup",
    ),
    "fizz_echo": Case(
        id="fizz_echo",
        place="rainy_cafe",
        setup="A silver straw trembled whenever a round tummy rumble sounded",
        repeated_clue="the same star was stamped twice beside the fizzy drink on the order pad",
        suspects=("the trembling straw", "the rain on the roof", "the fizzy drink"),
        first_guess="that the rain was copying the sound from the roof",
        test="tap the table, listen between raindrops, and compare the two drink marks with the café receipt",
        culprit="the repeated fizzy drink order",
        reveal="one drink was delivered, then another was poured when the first cup was forgotten",
        repair="share the extra drink with the grown-up, sip water, and mark one order as already served",
        lesson="a repeated order can cause repeated trouble when nobody checks the receipt",
        ending="the rain kept tapping while one gold drink ticket lay neatly under the café receipt",
    ),
    "cabbage_wrap": Case(
        id="cabbage_wrap",
        place="garden_table",
        setup="A paper napkin fluttered each time a soft puff escaped near the picnic basket",
        repeated_clue="two green crumbs and two matching leaf-shaped smudges sat on the same plate",
        suspects=("the fluttering napkin", "the windy hedge", "the cabbage wrap"),
        first_guess="that the hedge was blowing the napkin and causing every sound",
        test="shield the napkin from the wind, inspect the plate, and ask who had taken the first half",
        culprit="the repeated cabbage wrap",
        reveal="the wrap had been eaten once at lunch and its second half had been mistaken for a new one",
        repair="label the remaining half, eat slowly, and leave space before choosing another snack",
        lesson="repetition can hide in a familiar-looking portion, so count what was already eaten",
        ending="the leaf-shaped crumbs made a little trail toward the labeled plate while the hedge swayed harmlessly",
    ),
}

TELLING_MODES = (
    "clue_first",
    "dialogue_first",
    "question_first",
    "quiet_first",
)

OPENINGS = {
    "clue_first": "{hero} noticed the first clue before anyone noticed the first puff.",
    "dialogue_first": "'A mystery needs careful ears,' said {helper}, as {hero} opened the snack chart.",
    "question_first": "Who had caused the gassy rumbles at snack time? {hero} was ready to find out.",
    "quiet_first": "The little room was quiet except for rain, leaves, and one uncertain tummy.",
}

BRIDGES = (
    "The clue looked small, but a repeated mark can tell a large story.",
    "{hero} copied the clue once, then copied it again, so no detail would be lost.",
    "They did not point fingers. They pointed to the chart.",
    "The mystery waited beside the snack plate while everyone took a calm breath.",
)

REACTIONS = (
    "'We have a guess, not proof,' said {hero}.",
    "{helper} nodded. 'Let us compare what happened, not just what we heard.'",
    "'A tummy sound is a clue,' said {hero}, 'but it is not a name tag.'",
    "They made two columns: eaten once and eaten twice.",
)


def story_reasonable(place: str, case_id: str) -> bool:
    return place in PLACES and case_id in CASES and CASES[case_id].place == place


def explain_rejection(place: str, case_id: str) -> str:
    return f"'{place}' and case '{case_id}' do not form a supported storyworld combination."


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(explain_rejection(params.place, params.case_id))
    if params.case_id not in CASES:
        raise StoryError(f"Unknown mystery case '{params.case_id}'.")
    case = CASES[params.case_id]
    if case.place != params.place:
        raise StoryError(explain_rejection(params.place, params.case_id))

    world = World(params.place)
    hero = world.add(Entity(params.hero_name, "detective", params.hero_name))
    helper = world.add(Entity(params.helper_name, "helper", params.helper_name))
    snack = world.add(Entity("snack", "food", case.culprit))
    chart = world.add(Entity("chart", "record", "the snack chart"))
    tummy = world.add(Entity("tummy", "body", "the tummy"))

    hero.feel("curiosity", 2)
    hero.feel("care", 2)
    helper.feel("patience", 2)
    snack.meter("gas_score", 3)
    snack.meter("consumption_count", 2)
    chart.meter("repeated_marks", 2)
    tummy.meter("rumble_count", 2)
    tummy.feel("uncomfortable", 1)

    world.facts.update(
        hero=hero,
        helper=helper,
        snack=snack,
        chart=chart,
        tummy=tummy,
        case=case,
    )

    mode = params.telling_mode if params.telling_mode in OPENINGS else "clue_first"
    world.say(OPENINGS[mode].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"In {PLACES[params.place]}, {params.hero_name} and {params.helper_name} were checking "
        "snacks after a meal when a gassy tummy made two soft rumbles."
    )
    world.say(f"{case.setup}. Then they found the repeated clue: {case.repeated_clue}.")
    world.say(BRIDGES[params.detail_id % len(BRIDGES)].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"The possible suspects were {case.suspects[0]}, {case.suspects[1]}, and {case.suspects[2]}."
    )
    world.say(f"At first, {params.hero_name} guessed {case.first_guess}.")
    world.say(REACTIONS[(params.detail_id + 1) % len(REACTIONS)].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"'{case.test.capitalize()},' said {params.helper_name}. "
        f"'{case.test.split(',')[0].capitalize()},' replied {params.hero_name}."
    )
    world.say(
        f"They compared the consumption record with the sounds. The repeated mark matched {case.culprit}."
    )
    world.say(f"Then the whodunit turned: {case.reveal}.")
    world.say(
        f"Together they chose to {case.repair}. "
        f"'{case.lesson.capitalize()},' said {params.hero_name}. 'And careful checking helps everyone,' answered {params.helper_name}."
    )
    world.say(f"They learned that {case.lesson}.")
    world.say(
        f"By the end, {case.ending}. The mystery was solved, the tummy felt calmer, and nobody was blamed."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly whodunit in which {hero.label} investigates a gassy tummy and repeated consumption clues.",
        f"Build a gentle mystery around this repeated clue: {case.repeated_clue}. Include suspects, a fair test, and a reveal.",
        f"Tell a story showing that repeated consumption can cause repeated discomfort, ending with a concrete caring solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {hero.label} and {helper.label} investigate?",
            answer=f"They investigated a gassy tummy mystery caused by repeated consumption clues: {case.repeated_clue}.",
        ),
        QAItem(
            question="What was the repeated clue?",
            answer=f"The repeated clue was that {case.repeated_clue}.",
        ),
        QAItem(
            question="Who or what did they first suspect?",
            answer=f"They first suspected {case.first_guess}. They treated that idea as a guess and tested it.",
        ),
        QAItem(
            question="How did they solve the whodunit?",
            answer=f"They solved it by choosing to {case.test}. This showed that {case.reveal}.",
        ),
        QAItem(
            question="How did they help afterward?",
            answer=f"They chose to {case.repair}. This gave the tummy time to feel calmer.",
        ),
        QAItem(
            question="What lesson did the detectives learn?",
            answer=f"They learned that {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gassy mean?",
            answer="Gassy means having extra gas in the tummy, which can cause rumbling or puffs.",
        ),
        QAItem(
            question="What is consumption?",
            answer="Consumption is the act of using or eating something.",
        ),
        QAItem(
            question="Why can repeating a snack matter?",
            answer="Repeating a snack matters because eating it more than once can change how much a person has consumed and how their tummy feels.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_place/1.
#show valid_case/1.
#show valid_story/2.

valid_place(P) :- place(P).
valid_case(C) :- case(C).
valid_story(P,C) :- valid_place(P), valid_case(C), set_in(P,C), has_repetition(C), has_consumption(C), has_gassy_effect(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for case in CASES.values():
        lines.append(asp.fact("case", case.id))
        lines.append(asp.fact("set_in", case.place, case.id))
        lines.append(asp.fact("has_repetition", case.id))
        lines.append(asp.fact("has_consumption", case.id))
        lines.append(asp.fact("has_gassy_effect", case.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp

    expected = {(case.place, case.id) for case in CASES.values()}
    found = set(asp_valid_stories())
    if found != expected:
        print("MISMATCH between ASP and Python:")
        print("ASP only:", sorted(found - expected))
        print("Python only:", sorted(expected - found))
        return 1

    for case in CASES.values():
        params = StoryParams(
            place=case.place,
            hero_name="Luna",
            helper_name="Milo",
            case_id=case.id,
            seed=1,
        )
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print(f"Generated story failed for case {case.id}.")
            return 1

    print(f"OK: ASP gate matches Python registry ({len(expected)} stories), and generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle gassy-consumption repetition whodunit storyworld."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--case-id", choices=CASES)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    possible = [case.id for case in CASES.values() if case.place == place]
    case_id = args.case_id or (rng.choice(possible) if possible else next(iter(CASES)))
    hero_name = args.hero_name or rng.choice(("Luna", "Milo", "Nia", "Owen", "Pip"))
    helper_name = args.helper_name or rng.choice(("Ari", "Tess", "Grandpa Jo", "Mina", "Sam"))
    mode = rng.choice(TELLING_MODES)
    detail_id = rng.randrange(len(BRIDGES))
    return StoryParams(
        place=place,
        hero_name=hero_name,
        helper_name=helper_name,
        case_id=case_id,
        telling_mode=mode,
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
    lines = ["--- world trace ---", f"place: {world.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


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
    StoryParams("moonlit_pantry", "Luna", "Milo", "bean_bowl", "clue_first", 0),
    StoryParams("rainy_cafe", "Nia", "Ari", "fizz_echo", "dialogue_first", 1),
    StoryParams("garden_table", "Pip", "Tess", "cabbage_wrap", "question_first", 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("\n".join(str(item) for item in asp_valid_stories()))
        return

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
