#!/usr/bin/env python3
"""A gentle ghost story about a brother, clobber, and dim toast."""

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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    brother: str = "Luna"
    helper: str = "Milo"
    place: str = "the old kitchen"
    object_name: str = "the toast"
    scenario: str = "midnight_toast"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    beginning: str
    strange_event: str
    misunderstanding: str
    clue: str
    action: str
    exchange: tuple[str, str]
    reveal: str
    ending: str
    lesson: str


SCENARIOS = (
    Scenario(
        "midnight_toast",
        "The Toast That Dimmed",
        "One quiet night, Luna and her brother Milo crept into the old kitchen for a snack.",
        "the toaster clicked by itself, and one slice of toast came out dim and gray",
        "Luna thought a ghost had clobbered the toast because it was angry",
        "a tiny silver thread was caught beneath the toaster lever",
        "lifted the toaster away from the wall and looked carefully instead of blaming a ghost",
        ("“The ghost clobbered it!” Luna whispered.", "“Or something is hiding under the lever,” Milo answered."),
        "The silver thread had come from a loose dishcloth, and it had stopped the toast from warming evenly.",
        "The brothers freed the thread, made a bright golden slice, and shared it beneath the moonlit window.",
        "A spooky guess can feel real, but a careful look can uncover a kinder truth.",
    ),
    Scenario(
        "shadow_clobber",
        "The Shadowy Bump",
        "Luna and her brother walked past the kitchen after the house had gone dark.",
        "a long shadow clobbered the pantry door with a loud bump",
        "Luna thought the pantry ghost had chased Milo away",
        "the moonlight was moving a hanging coat against the door",
        "stepped closer together and shone a small lantern toward the bump",
        ("“The pantry ghost struck again!” Luna cried.", "“Stay with me. Let us see what the light finds,” Milo said."),
        "The lantern showed the coat sleeve swinging in a draft, while the pantry stayed still.",
        "They hung the coat on a peg, and the next bump became only a soft rustle.",
        "When fear mixes up a shadow and a danger, gentle questions can set things right.",
    ),
    Scenario(
        "lost_brother",
        "The Brother in the Mist",
        "At dawn, Luna woke in the little house and could not see her brother beside the stairs.",
        "a pale shape drifted across the hallway and seemed to clobber the umbrella stand",
        "Luna thought the mist had carried Milo away",
        "Milo was hiding behind the open umbrella while trying to surprise her",
        "called his name, listened for an answer, and checked the safe rooms before running outside",
        ("“Milo, are you there?” Luna called.", "“I am here!” Milo laughed. “The umbrella made me look like a ghost.”"),
        "The pale shape was only the umbrella, and Milo stepped out with two mugs of warm milk.",
        "They closed the umbrella, laughed at the mist, and watched the sunrise together.",
        "Checking facts and speaking clearly can turn a frightening misunderstanding into comfort.",
    ),
)

SCENARIO_BY_KEY = {item.key: item for item in SCENARIOS}
BROTHERS = ("Luna", "Nina", "Tess", "Pip")
HELPERS = ("Milo", "Finn", "Ollie", "Sam")
PLACES = ("the old kitchen", "the narrow hallway", "the moonlit pantry", "the little house")
OBJECTS = ("the toast", "the pantry door", "the umbrella stand")


def build_world(params: StoryParams) -> World:
    world = World(params)
    brother = world.add(
        Entity(
            id=params.brother,
            kind="brother",
            label=params.brother,
            meters={"courage": 0.55, "certainty": 0.35},
            memes={"wonder": 0.8, "worry": 0.45},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="brother",
            label=params.helper,
            meters={"courage": 0.8, "certainty": 0.65},
            memes={"patience": 0.9, "care": 0.9},
        )
    )
    world.add(Entity(id="ghostly_clue", kind="clue", label="a ghostly-looking clue"))
    world.add(Entity(id="warm_snack", kind="object", label=params.object_name, owner=brother.id))
    world.facts["brother"] = brother.id
    world.facts["helper"] = helper.id
    return world


def validate(params: StoryParams) -> None:
    if params.brother == params.helper:
        raise StoryError("The brother and helper must have different names.")
    if params.scenario not in SCENARIO_BY_KEY:
        raise StoryError(f"Unknown scenario: {params.scenario}")
    if params.variant < 0:
        raise StoryError("variant must not be negative.")


def choose(options: tuple[str, ...], params: StoryParams, salt: int) -> str:
    return random.Random((params.variant + 17) * 1009 + salt * 7919).choice(options)


def simulate(world: World) -> World:
    p = world.params
    validate(p)
    scenario = SCENARIO_BY_KEY[p.scenario]
    brother = world.entities[p.brother]
    helper = world.entities[p.helper]

    world.say(f"In {p.place}, where the floorboards whispered at night, {p.brother} lived with {p.helper}, her brother.")
    world.say(scenario.beginning)
    world.say("They were brave enough to explore, but even brave children could be surprised by a dark room.")
    world.para()

    world.say(f"Then {scenario.strange_event}.")
    world.say(f"{p.brother} misunderstood the clue: {scenario.misunderstanding}.")
    world.say(f"The thought felt spooky, but the useful clue was that {scenario.clue}.")
    world.say("A quick guess wanted to clobber the truth before anyone could see it clearly.")
    world.para()

    first, second = scenario.exchange
    world.say(f"{first} {second}")
    world.say(f"{p.helper} did not laugh at {p.brother}'s fear. Together they {scenario.action}.")
    world.say(f"Because they checked instead of guessing, {scenario.reveal}")
    world.para()

    world.say(f"{scenario.ending}")
    world.say(f"{p.brother} smiled at {p.helper}. “Next time, we ask the clue a question before we call it a ghost.”")
    world.say(f"{scenario.lesson}")
    world.fired.update({"surprise", "misunderstanding", "clue_checked", "truth_revealed", "happy_ending"})
    brother.meters.update(courage=0.9, certainty=0.95)
    brother.memes.update(worry=0.1, wonder=0.95, happiness=1.0)
    helper.memes["care"] = 1.0
    world.facts.update(
        scenario=p.scenario,
        surprise=scenario.strange_event,
        misunderstanding=scenario.misunderstanding,
        clue=scenario.clue,
        action=scenario.action,
        reveal=scenario.reveal,
        happy_ending=scenario.ending,
        toast_dim="toast-dim" in scenario.strange_event,
        clobber=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    scenario = SCENARIO_BY_KEY[p.scenario]
    return [
        f"Write a gentle ghost story about brother {p.brother} and {p.helper} in {p.place}.",
        f"Include Surprise, Misunderstanding, and a Happy Ending caused by this clue: {scenario.clue}.",
        f"Use the words brother, clobber, and toast-dim naturally without making the story frightening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    scenario = SCENARIO_BY_KEY[p.scenario]
    return [
        QAItem(
            question=f"What surprised {p.brother}?",
            answer=f"{p.brother} was surprised when {scenario.strange_event}.",
        ),
        QAItem(
            question=f"What did {p.brother} misunderstand?",
            answer=f"{p.brother} misunderstood the event and thought that {scenario.misunderstanding}.",
        ),
        QAItem(
            question="What clue helped the brothers?",
            answer=f"The clue was that {scenario.clue}. It gave them a reason to investigate instead of blaming a ghost.",
        ),
        QAItem(
            question=f"How did {p.brother} and {p.helper} solve the problem?",
            answer=f"They {scenario.action}. Their careful action revealed that {scenario.reveal}",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=scenario.ending,
        ),
        QAItem(
            question="What did the brothers learn?",
            answer=scenario.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone interprets a person, object, or event incorrectly.",
        ),
        QAItem(
            question="What can help when something seems frightening?",
            answer="A person can pause, stay with a trusted helper, ask clear questions, and look for safe evidence before deciding what happened.",
        ),
        QAItem(
            question="Why can a surprise feel spooky?",
            answer="A surprise is unfamiliar, so the mind may fill in missing details with a frightening explanation even when the real cause is harmless.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the characters are safe, understand what happened, and share comfort or joy after solving the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """brother(X) :- person(X), sibling(X).
safe(X) :- brother(X), clue_checked(X), truth_revealed(X).
happy(X) :- safe(X), shared_comfort(X).
#show happy/1.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    p = params or StoryParams()
    subject = p.brother.lower()
    return "\n".join(
        [
            asp.fact("person", subject),
            asp.fact("sibling", subject),
            asp.fact("clue_checked", subject),
            asp.fact("truth_revealed", subject),
            asp.fact("shared_comfort", subject),
        ]
    )


def asp_program(params: Optional[StoryParams] = None, show: str = "#show happy/1.") -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    found = set(asp.atoms(symbols, "happy"))
    expected = {(StoryParams().brother.lower(),)}
    if found == expected:
        print("OK: ASP twin confirms the safe happy ending.")
        return 0
    print(f"ASP verification failed: expected {expected}, got {found}.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ghost Story brother and dim-toast StoryWorld.")
    parser.add_argument("--brother", choices=BROTHERS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", choices=OBJECTS, default=None)
    parser.add_argument("--scenario", choices=tuple(SCENARIO_BY_KEY))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    brother = args.brother or rng.choice(BROTHERS)
    helper = args.helper or rng.choice(tuple(name for name in HELPERS if name != brother))
    return StoryParams(
        seed=args.seed,
        brother=brother,
        helper=helper,
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        scenario=args.scenario or rng.choice(tuple(SCENARIO_BY_KEY)),
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
        print(f"fired: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(
                StoryParams(
                    seed=base_seed,
                    brother="Luna",
                    helper="Milo",
                    place="the old kitchen",
                    object_name="the toast",
                    scenario=scenario.key,
                    variant=index + 1,
                )
            )
            for index, scenario in enumerate(SCENARIOS)
        ]
    else:
        samples = [generate(resolve_params(args, random.Random(base_seed + index))) for index in range(args.n)]

    if args.asp:
        import asp

        for sample in samples:
            symbols = asp.one_model(asp_program(sample.params))
            print(json.dumps({"happy": asp.atoms(symbols, "happy")}, ensure_ascii=False))
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
