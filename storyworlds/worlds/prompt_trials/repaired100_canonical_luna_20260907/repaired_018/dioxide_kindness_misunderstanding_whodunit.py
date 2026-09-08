#!/usr/bin/env python3
"""
A small child-facing whodunit about dioxide, kindness, and a mistaken clue.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = ["the school garden", "the greenhouse", "the science room", "the park pond"]
HERO_NAMES = ["Luna", "Mia", "Theo", "Nora", "Sam", "Ivy"]
HELPER_NAMES = ["Aunt Jo", "Ms. Reed", "Grandpa Sol", "Mr. Chen"]
OBJECTS = ["blue ribbon", "paper badge", "yellow glove", "red notebook"]


@dataclass
class StoryParams:
    hero: str
    helper: str
    place: str
    object_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Case:
    task: str
    trouble: str
    suspicion: str
    clue: str
    test: str
    cause: str
    kind_action: str
    helper_action: str
    solution: str
    ending: str
    worried: str
    reply: str


CASES = [
    Case(
        task="measure how plants use dioxide in the morning",
        trouble="the class's little dioxide card vanished from the seed tray",
        suspicion="the breeze had carried it away",
        clue="a round damp mark sat beside the card's empty place",
        test="held a mirror near the leaves and watched a faint cloud appear",
        cause="a watering cup had tipped, and the card was stuck beneath its wet rim",
        kind_action="lifted the cup gently instead of blaming the child who had watered",
        helper_action="made a dry tray for the cards",
        solution="they dried the card and checked the tray together",
        ending="the recovered card rested beside a row of green leaves drinking in dioxide",
        worried="Who took our dioxide card?",
        reply="Let's look for a clue before we accuse anyone.",
    ),
    Case(
        task="help the class explain why seedlings need dioxide",
        trouble="the chalk drawing about dioxide had been rubbed off the garden wall",
        suspicion="someone had erased the science picture on purpose",
        clue="tiny white smudges led from the wall to a nearby bench",
        test="followed the smudges and found a cloth with chalk dust on it",
        cause="the wind had knocked the cleaning cloth against the drawing",
        kind_action="thanked the younger child who had tried to tidy the bench",
        helper_action="moved the chalk lesson to a sheltered board",
        solution="they redrew the picture and invited the young cleaner to add leaves",
        ending="a bright leaf diagram showed dioxide arrows curling toward the plants",
        worried="Who wiped away our dioxide lesson?",
        reply="The marks may tell us what happened, and nobody needs blame yet.",
    ),
    Case(
        task="bring a dioxide jar to the greenhouse table",
        trouble="the jar was gone when the group returned from washing their hands",
        suspicion="the newest helper had hidden it as a joke",
        clue="a trail of silver beads led beneath the potting bench",
        test="crouched down and followed the beads with a flashlight",
        cause="the jar's loose label had peeled off and dragged behind a rolling cart",
        kind_action="asked the newest helper to help search rather than pointing a finger",
        helper_action="stopped the cart and checked its lower shelf",
        solution="they found the jar, fixed its label, and placed it in a marked basket",
        ending="the dioxide jar shone safely beside the greenhouse seedlings",
        worried="Did somebody hide the dioxide jar?",
        reply="We can search together. A missing thing is not proof of a guilty person.",
    ),
    Case(
        task="make a kindness poster about dioxide and growing plants",
        trouble="the poster's green leaf had disappeared from the display",
        suspicion="the shyest child had taken it because they disliked the project",
        clue="a green paper corner poked out from the donation box",
        test="asked the group what they had placed in the box before opening it",
        cause="a volunteer had put the leaf there with other scraps for recycling",
        kind_action="invited the shy child to choose a new leaf shape",
        helper_action="labeled the recycling box clearly",
        solution="they rebuilt the poster and added a note about kind questions",
        ending="the poster showed a leafy plant, a dioxide arrow, and many helpful hands",
        worried="Why is the poster missing its leaf?",
        reply="Let's ask kindly. A quiet person may know a clue, not be the culprit.",
    ),
    Case(
        task="solve a small dioxide mystery for the park gardener",
        trouble="the garden bell rang even though nobody stood near it",
        suspicion="the wind had made the bell ring by itself",
        clue="a muddy shoeprint pointed toward the compost corner",
        test="compared the print with the boots beside the watering shed",
        cause="a puppy had tugged the bell rope while sniffing a compost bucket",
        kind_action="guided the puppy away without shouting",
        helper_action="tied the rope higher and covered the compost bucket",
        solution="they checked the plants and left a safe path for the puppy",
        ending="the bell waited quietly while the garden breathed in morning dioxide",
        worried="Who rang the garden bell?",
        reply="The footprint is a clue, but we should follow it gently.",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dioxide kindness whodunit storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
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
        hero=args.hero or rng.choice(HERO_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(
        Entity(
            "hero",
            "character",
            params.hero,
            "child",
            memes={"curiosity": 1.0, "kindness": 1.0},
        )
    )
    world.add(Entity("helper", "character", params.helper, "adult", memes={"patience": 1.0}))
    world.add(
        Entity(
            "dioxide",
            "thing",
            "dioxide",
            "gas",
            meters={"present": 1.0},
            memes={"useful": 1.0},
        )
    )
    world.add(Entity("clue", "thing", params.object_name, "clue", meters={"visible": 1.0}))
    return world


def choose_case(params: StoryParams) -> Case:
    value = params.seed if params.seed is not None else sum(
        (index + 1) * ord(char)
        for index, char in enumerate("|".join(vars(params).values()[:-1]))
    )
    return CASES[value % len(CASES)]


def generate_story(world: World) -> None:
    p = world.params
    case = choose_case(p)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    dioxide = world.entities["dioxide"]

    world.say(
        f"At {p.place}, {p.hero} became the young detective for a science-and-kindness case. "
        f"The day's task was to {case.task}."
    )
    world.say(
        f"{p.helper} carried a small {p.object_name}, and {p.hero} carried the picture of a plant. "
        f"They remembered that plants use dioxide from the air while they grow."
    )

    world.para()
    world.say(f"Then {case.trouble}.")
    world.say(f"{p.helper} looked worried. '{case.worried}'")
    world.say(f"{p.hero} shook their head. '{case.reply}'")
    world.say(f"For a moment, the misunderstanding was that {case.suspicion}.")
    world.facts["misunderstanding"] = case.suspicion
    hero.memes["worry"] = 1.0

    world.para()
    world.say(f"The first clue was that {case.clue}.")
    world.say(f"To test the clue, {p.hero} {case.test}.")
    world.say(f"That careful test showed the truth: {case.cause}.")
    world.say(
        f"{p.helper} smiled. 'Good detectives notice facts, and kind detectives protect people while they search.'"
    )
    world.say(f"{p.hero} answered, 'Then kindness belongs in every mystery.'")
    world.facts.update(
        {
            "clue": case.clue,
            "test": case.test,
            "cause": case.cause,
            "dioxide": "Plants use dioxide from the air while they grow.",
        }
    )
    hero.memes["curiosity"] = 2.0
    helper.memes["relief"] = 1.0

    world.para()
    world.say(f"{p.hero} {case.kind_action}, and {p.helper} {case.helper_action}.")
    world.say(f"Their solution was simple: {case.solution}.")
    world.say(f"After that, {case.ending}.")
    world.say(
        f"The mystery was solved without a harsh accusation. {p.hero} wrote KIND QUESTIONS beside the case notes, "
        f"and everyone left {p.place} feeling ready to help."
    )
    hero.memes["kindness"] = 2.0
    hero.memes["pride"] = 1.0
    dioxide.meters["present"] = 2.0
    world.facts.update(
        {
            "kind_action": case.kind_action,
            "helper_action": case.helper_action,
            "solution": case.solution,
            "ending": case.ending,
            "kindness": True,
            "solved": True,
        }
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    case = choose_case(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-friendly whodunit at {params.place} about {params.hero}, dioxide, kindness, and a misunderstanding.",
            f"Tell a mystery where {params.hero} follows a clue, speaks kindly, and discovers what really happened.",
            "Explain how dioxide helps plants while keeping the story warm and funny.",
        ],
        story_qa=[
            QAItem(
                f"What was {params.hero}'s science task at {params.place}?",
                f"{params.hero}'s task was to {case.task}. The investigation also helped the group remember that plants use dioxide from the air while they grow.",
            ),
            QAItem(
                "What was the misunderstanding in the mystery?",
                f"The misunderstanding was that {case.suspicion}. That idea was corrected when the detectives examined the clue instead of blaming someone.",
            ),
            QAItem(
                f"What clue helped {params.hero} solve the case?",
                f"The clue was that {case.clue}. {params.hero} tested it by {case.test}, which revealed that {case.cause}.",
            ),
            QAItem(
                "How did kindness change the investigation?",
                f"{params.hero} {case.kind_action}. The group solved the mystery while protecting people's feelings and learning to ask kind questions.",
            ),
            QAItem(
                "What showed that the case was solved?",
                f"{case.ending} The mystery ended with a safe solution and everyone ready to help.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is dioxide?",
                "Dioxide is a name for a substance containing two oxygen atoms. Carbon dioxide is a gas in the air that plants can use as they grow.",
            ),
            QAItem(
                "Why should detectives check clues?",
                "Detectives check clues because a first guess can be wrong. Evidence helps them learn what really happened.",
            ),
            QAItem(
                "What does kindness mean?",
                "Kindness means treating people and living things with care, respect, and helpful words.",
            ),
        ],
        world=world,
    )


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for feature in ("dioxide", "kindness", "misunderstanding", "whodunit"):
        lines.append(asp.fact("feature", feature))
    return "\n".join(lines)


ASP_RULES = r"""
case_domain(P) :- place(P).
uses_dioxide(P) :- place(P).
kind_investigation(P) :- place(P).
misunderstanding_case(P) :- place(P).
whodunit(P) :- place(P).
solvable(P) :- uses_dioxide(P), kind_investigation(P), misunderstanding_case(P), whodunit(P).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(
        asp_program(
            "#show solvable/1.\n#show uses_dioxide/1.\n#show kind_investigation/1.\n#show misunderstanding_case/1."
        )
    )
    places = set(PLACES)
    checks = [
        set(asp.atoms(model, "solvable")) == {(p,) for p in places},
        set(asp.atoms(model, "uses_dioxide")) == {(p,) for p in places},
        set(asp.atoms(model, "kind_investigation")) == {(p,) for p in places},
        set(asp.atoms(model, "misunderstanding_case")) == {(p,) for p in places},
    ]
    if not all(checks):
        print("Mismatch between ASP and Python registries.")
        return 1
    for params in [
        StoryParams("Luna", "Ms. Reed", "the greenhouse", "blue ribbon", 1),
        StoryParams("Theo", "Aunt Jo", "the school garden", "yellow glove", 2),
    ]:
        sample = generate(params)
        if not sample.story or "dioxide" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print("OK: ASP parity and generated stories verified.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:8} ({entity.kind:9}) {entity.label} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"P{index}: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams("Luna", "Ms. Reed", "the greenhouse", "blue ribbon"),
    StoryParams("Mia", "Aunt Jo", "the school garden", "yellow glove"),
    StoryParams("Theo", "Mr. Chen", "the science room", "red notebook"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show solvable/1.\n#show uses_dioxide/1.\n#show kind_investigation/1.\n#show misunderstanding_case/1."
            )
        )
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        model = asp.one_model(
            asp_program(
                "#show solvable/1.\n#show uses_dioxide/1.\n#show kind_investigation/1.\n#show misunderstanding_case/1."
            )
        )
        print(f"solvable={len(asp.atoms(model, 'solvable'))}")
        print(f"uses_dioxide={len(asp.atoms(model, 'uses_dioxide'))}")
        print(f"kind_investigation={len(asp.atoms(model, 'kind_investigation'))}")
        print(f"misunderstanding_case={len(asp.atoms(model, 'misunderstanding_case'))}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero}'s case at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### case {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
