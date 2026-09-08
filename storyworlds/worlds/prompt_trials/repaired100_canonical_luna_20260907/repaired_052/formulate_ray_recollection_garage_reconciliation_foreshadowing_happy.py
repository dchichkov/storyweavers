#!/usr/bin/env python3
"""
A small standalone Detective Story storyworld set in a garage, where a clue is
formulated from a ray of light and a recollection leads to reconciliation and
a happy ending.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "mechanic"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Garage:
    name: str = "Maple Street Garage"
    setting: str = "garage"
    case: str = "a missing brass key"
    light: str = "a narrow ray of afternoon light"


@dataclass
class StoryParams:
    detective: str
    helper: str
    garage_name: str
    seed: Optional[int] = None
    case: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Case:
    key: str
    premise: str
    clue: str
    wrong_guess: str
    consequence: str
    recollection: str
    formulation: str
    reveal: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


DETECTIVE_NAMES = ["Luna", "Mara", "Nell", "Iris", "Cleo", "June"]
HELPER_NAMES = ["Theo", "Milo", "Pip", "Sam", "Owen", "Bea"]
GARAGE_NAMES = [
    "Maple Street Garage",
    "Blue Door Garage",
    "Sunbeam Garage",
    "Old Lantern Garage",
]
TELLING_MODES = ["arrival", "warning", "question", "memory", "dialogue", "countdown"]

CASES = [
    Case(
        key="brass_key",
        premise="the garage's small brass key had vanished before the Saturday repair bell",
        clue="a thin ray of sunlight crossed the empty hook and ended on a trail of blue paint",
        wrong_guess="accused the newest customer of taking it",
        consequence="the customer left sadly, and the real trail was almost swept away",
        recollection="remembered that the key had been placed beside a blue bicycle during last week's rain",
        formulation="formed a careful theory: the key had traveled with the bicycle's dripping repair cloth",
        reveal="the key was tucked inside a folded cloth beneath the bicycle seat",
        apology="admitted that the accusation had been unfair",
        repair="invited the customer back and returned the key with a sincere apology",
        outcome="the customer forgave the mistake and helped ring the repair bell",
        lesson="a good detective tests a theory before blaming a person",
        ending="the brass key shone on its hook while the blue bicycle waited safely nearby",
    ),
    Case(
        key="vanished_tyre",
        premise="a fresh bicycle tire disappeared from the garage shelf before a child's race",
        clue="a bright ray touched a line of rubber dust leading toward the old workbench",
        wrong_guess="suspected that the friendly delivery driver had taken it",
        consequence="the driver stopped smiling, and the child worried that the race was ruined",
        recollection="recalled hearing a slow wobble under the workbench when the delivery boxes arrived",
        formulation="formulated a new idea: the tire had rolled away rather than been carried",
        reveal="the tire was wedged behind a cabinet, resting against a loose wheel",
        apology="told the driver that the suspicion had been wrong",
        repair="moved the cabinet together and thanked the driver for helping search",
        outcome="the driver found the missing pump, and the child's bicycle was ready",
        lesson="recollection can correct a hasty conclusion",
        ending="the repaired bicycle rolled into the sunlight as the starting bell rang",
    ),
    Case(
        key="painted_star",
        premise="the golden star for the garage's kindness award was missing from the front window",
        clue="a ray on the dusty glass revealed one clean star-shaped patch",
        wrong_guess="decided that the neighboring shop had borrowed it without asking",
        consequence="the two shopkeepers stopped waving to each other",
        recollection="remembered that the star had been removed during a storm and placed near the drying paint",
        formulation="formulated a fairer question: who had moved it to keep it safe",
        reveal="the neighbor had carried it inside after finding it in a puddle",
        apology="said the angry guess had hurt their friendship",
        repair="cleaned the star and hung it between both shop doors",
        outcome="the shopkeepers reconciled and shared the award with everyone",
        lesson="asking kindly can uncover a helpful act hidden by confusion",
        ending="the golden star gleamed between the two doors as both shops opened together",
    ),
    Case(
        key="silent_radio",
        premise="the old radio in the garage went silent just before the family listening hour",
        clue="a ray of light flashed across a loose copper wire under the dashboard",
        wrong_guess="blamed the younger helper for touching the controls",
        consequence="the helper folded his arms and stopped helping with the repair",
        recollection="remembered that the radio had worked after a storm only when its wire was tied high",
        formulation="formed a simple repair plan instead of another accusation",
        reveal="the wire had slipped when a toolbox was moved",
        apology="acknowledged that the helper had done nothing wrong",
        repair="asked the helper to hold the wire while the connection was secured",
        outcome="the radio played a cheerful tune and the helper felt trusted again",
        lesson="a careful memory can turn blame into teamwork",
        ending="music floated through the garage while the repaired wire shone above the dashboard",
    ),
    Case(
        key="missing_mug",
        premise="the mechanic's red mug disappeared from the garage counter",
        clue="a narrow ray lit a red drip on the floor beside the parts cart",
        wrong_guess="thought the apprentice had hidden it as a joke",
        consequence="the apprentice grew quiet and the morning work slowed",
        recollection="recalled carrying the mug near the cart while searching for a missing screw",
        formulation="formulated a trail that included the detective's own footsteps",
        reveal="the mug sat behind a tire stack, where it had been placed for safety",
        apology="admitted that the apprentice had been blamed without proof",
        repair="washed the mug and asked the apprentice to choose its new safe place",
        outcome="the apprentice laughed, and both workers finished the repair together",
        lesson="honesty makes room for forgiveness when the mistake is your own",
        ending="the red mug rested on its new shelf beside two warm cups of cocoa",
    ),
    Case(
        key="silver-bell",
        premise="the silver bell for the garage's lost-and-found shelf disappeared",
        clue="a sun ray struck a tiny bell mark in the dust near the front tire",
        wrong_guess="claimed that a passing child must have taken it",
        consequence="the child looked frightened and hid behind the gate",
        recollection="remembered that the bell had been used to decorate a bicycle for a welcome parade",
        formulation="made a better explanation: someone had returned it to the parade basket",
        reveal="the bell was waiting in the basket with a note of thanks",
        apology="knelt down and told the child the suspicion had been unfair",
        repair="walked with the child to retrieve the bell and put it back on the shelf",
        outcome="the child forgave the detective and donated a second bell",
        lesson="kind questions protect trust while clues grow clearer",
        ending="two silver bells chimed on the shelf whenever the garage door opened",
    ),
]


class World:
    def __init__(self, garage: Garage) -> None:
        self.garage = garage
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective Story storyworld about clues, reconciliation, and a happy garage ending."
    )
    parser.add_argument("--detective", choices=DETECTIVE_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--garage-name", choices=GARAGE_NAMES)
    parser.add_argument("--case", choices=[case.key for case in CASES])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != detective]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(
        detective=detective,
        helper=helper,
        garage_name=args.garage_name or rng.choice(GARAGE_NAMES),
        seed=args.seed,
        case=args.case or rng.choice(CASES).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("domain", "garage"),
            asp.fact("style", "detective_story"),
            asp.fact("feature", "reconciliation"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "happy_ending"),
            asp.fact("seed_word", "formulate"),
            asp.fact("seed_word", "ray"),
            asp.fact("seed_word", "recollection"),
            asp.fact("requires", "clue"),
            asp.fact("requires", "apology"),
            asp.fact("requires", "repair"),
        ]
    )


ASP_RULES = r"""
valid_story :- domain(garage), style(detective_story),
               feature(reconciliation), feature(foreshadowing),
               feature(happy_ending), seed_word(formulate),
               seed_word(ray), seed_word(recollection),
               requires(clue), requires(apology), requires(repair).
#show valid_story/0.
#show feature/1.
#show seed_word/1.
"""


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    valid = asp.atoms(model, "valid_story")
    words = sorted(asp.atoms(model, "seed_word"))
    expected = [("formulate",), ("ray",), ("recollection",)]
    if valid and words == expected:
        print("OK: ASP and Python story requirements agree.")
        return 0
    print("MISMATCH: ASP requirements were not satisfied.")
    return 1


def _opening(params: StoryParams, case: Case) -> list[str]:
    detective = params.detective
    helper = params.helper
    mode = params.telling_mode or "arrival"
    garage = params.garage_name
    if mode == "warning":
        return [
            f'"Something is missing," {helper} warned as {detective} entered {garage}.',
            f"The detective looked around the garage. {case.premise.capitalize()}.",
        ]
    if mode == "question":
        return [
            f'"Who moved it?" {helper} asked inside {garage}.',
            f"{detective} raised a notebook. {case.premise.capitalize()}.",
        ]
    if mode == "memory":
        return [
            f"Years later, {detective} would remember the quiet beginning in {garage}.",
            f"That morning, {case.premise}.",
        ]
    if mode == "dialogue":
        return [
            f'"Ready to investigate?" {detective} asked. "Ready," {helper} replied.',
            f"Together they entered {garage}. {case.premise.capitalize()}.",
        ]
    if mode == "countdown":
        return [
            f"The garage clock had ten minutes left before opening time.",
            f"Inside {garage}, {detective} and {helper} discovered that {case.premise}.",
        ]
    return [
        f"{detective} arrived at {garage} with a notebook in one hand and a small flashlight in the other.",
        f"{case.premise.capitalize()}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.case not in {case.key for case in CASES}:
        raise StoryError(f"Unknown case: {params.case!r}")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling mode: {params.telling_mode!r}")

    rng = random.Random(params.seed)
    case = next(item for item in CASES if item.key == params.case)
    garage = Garage(name=params.garage_name)
    world = World(garage)

    detective = world.add(
        Entity(
            id=params.detective,
            kind="character",
            type="detective",
            label="detective",
            phrase=params.detective,
            location="garage office",
            traits=["careful", "curious"],
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="mechanic",
            label="helper",
            phrase=params.helper,
            location="repair bay",
            traits=["quick", "kind"],
        )
    )
    clue = world.add(
        Entity(
            id="ray_clue",
            kind="thing",
            type="clue",
            label="ray of light",
            phrase="a narrow ray of light",
            location="garage window",
            meters={"brightness": 1.0, "clarity": 0.2},
            memes={"foreshadowing": 1.0},
        )
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        clue=clue,
        case=case.key,
        premise=case.premise,
        clue_text=case.clue,
        wrong_guess=case.wrong_guess,
        recollection=case.recollection,
        formulation=case.formulation,
        reveal=case.reveal,
        repair=case.repair,
        resolution="reconciled",
    )

    for sentence in _opening(params, case):
        world.say(sentence)

    world.say(
        rng.choice(
            [
                f"Then {garage.light} slipped through the dusty window.",
                f"A ray of light cut across the concrete floor like a bright detective's arrow.",
                "The garage grew still, except for one shining line between the tools.",
            ]
        )
    )
    world.say(f"It offered the first foreshadowing clue: {case.clue}.")

    world.para()
    world.say(
        rng.choice(
            [
                f"{detective} hurried to a conclusion and {case.wrong_guess}.",
                f'"I know what happened," {detective} said, but the guess was simple: {case.wrong_guess}.',
                f"The clue looked tempting, so {detective} {case.wrong_guess}.",
            ]
        )
    )
    world.say(f"The hasty guess caused trouble: {case.consequence}.")
    world.say(
        f'"Wait," {helper} said. "A clue should help us learn, not hurt someone."'
    )
    world.say(
        f'"You are right," {detective} replied. "Let us look again and formulate a fair idea."'
    )

    world.para()
    world.say(f"While studying the ray, {detective} had a useful recollection: {case.recollection}.")
    world.say(f"That memory helped {detective} {case.formulation}.")
    world.say(f"The new theory led to the truth: {case.reveal}.")
    world.say(
        rng.choice(
            [
                "The mystery became smaller when the detectives checked the place instead of guessing about a person.",
                "The bright ray had foreshadowed the answer all along, but only careful attention made it visible.",
            ]
        )
    )

    world.para()
    world.say(f"{detective} {case.apology}.")
    world.say(
        f'"Thank you for telling the truth," {helper} said. "Now we can repair more than the missing thing."'
    )
    world.say(f"Together they {case.repair}.")
    world.say(f"Because they spoke honestly, {case.outcome}.")

    world.para()
    world.say(f"The case taught them that {case.lesson}.")
    world.say(f"As evening warmed the garage, {case.ending}.")
    world.say("It was a happy ending built from a careful clue, a brave recollection, and reconciliation.")

    clue.location = "understood and resolved"
    clue.meters["clarity"] = 1.0
    detective.memes["reconciliation"] = 1.0
    helper.memes["trust"] = 1.0
    world.facts.update(
        foreshadowing=True,
        formulated=True,
        recollection_used=True,
        reconciled=True,
        happy_ending=True,
    )

    prompts = [
        f"Write a child-friendly Detective Story set in {params.garage_name}, where {params.detective} uses a ray and a recollection to solve a mystery.",
        f"Tell a garage mystery in which the detective must formulate a fair theory instead of blaming someone.",
        f"Create a story with foreshadowing, reconciliation, and a happy ending. Include this clue: {case.clue}.",
    ]
    story_qa = [
        QAItem(
            question=f"What mystery did {params.detective} investigate?",
            answer=f"{params.detective} investigated how {case.premise}. The mystery took place in {params.garage_name}.",
        ),
        QAItem(
            question="What foreshadowing clue appeared first?",
            answer=f"A ray of light revealed that {case.clue}. That clue pointed toward the later solution.",
        ),
        QAItem(
            question="How did recollection help solve the case?",
            answer=f"{params.detective} remembered that {case.recollection}. This helped formulate the idea that {case.formulation}.",
        ),
        QAItem(
            question="Why was reconciliation needed?",
            answer=f"Reconciliation was needed because {case.wrong_guess}, which caused {case.consequence}. The detective then apologized and {case.repair}.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"The characters repaired their trust, and {case.outcome}. The ending showed that {case.ending}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early detail that quietly hints at something important later in a story.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a mistake, hurt feeling, or disagreement.",
        ),
        QAItem(
            question="Why should a detective formulate a theory?",
            answer="A detective should formulate a theory from checked clues so the theory explains the evidence without unfairly blaming someone.",
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("\n".join(str(symbol) for symbol in model))
        return
    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        test_params = StoryParams(
            detective="Luna",
            helper="Theo",
            garage_name="Maple Street Garage",
            seed=17,
            case="brass_key",
            telling_mode="dialogue",
        )
        sample = generate(test_params)
        required = ["ray", "recollection", "formulate", "reconciliation"]
        if not all(word in sample.story.lower() for word in required):
            print("MISMATCH: generated story is missing a required narrative instrument.")
            sys.exit(1)
        print("OK: generated story exercises the required narrative instruments.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Theo", "Maple Street Garage", 101, "brass_key", "arrival"),
            StoryParams("Mara", "Milo", "Blue Door Garage", 202, "painted_star", "dialogue"),
            StoryParams("Iris", "Bea", "Sunbeam Garage", 303, "silent_radio", "memory"),
            StoryParams("Cleo", "Sam", "Old Lantern Garage", 404, "missing_mug", "question"),
        ]
        samples = [generate(params) for params in curated]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            attempt += 1
            seed = base_seed + attempt
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
        if args.all:
            header = f"### {sample.params.detective} investigates at {sample.params.garage_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
