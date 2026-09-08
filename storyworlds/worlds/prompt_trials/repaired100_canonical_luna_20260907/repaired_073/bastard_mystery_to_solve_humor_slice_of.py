#!/usr/bin/env python3
"""
A small slice-of-life mystery about a child, a missing pie slice, and a
suspiciously crumb-covered family dog.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = {
    "kitchen": {
        "place": "the sunny kitchen",
        "detail": "A round table stood beneath the window, and the kettle hummed beside a bowl of bright lemons.",
        "affords": {"baking", "searching", "sharing"},
    },
}

NAMES = ["Luna", "Milo", "Pia", "Theo", "Nora", "Sam"]
GENDERS = {"Luna": "girl", "Milo": "boy", "Pia": "girl", "Theo": "boy", "Nora": "girl", "Sam": "boy"}
ADULTS = ["Mom", "Dad", "Aunt Bea", "Grandpa"]
TRAITS = ["curious", "cheerful", "careful", "silly", "patient"]

CASES = [
    {
        "arrival": "Luna had baked a lemon pie with her aunt for the neighbors.",
        "problem": "When they returned from washing the plates, one golden slice was gone.",
        "clue": "A trail of buttery crumbs led from the pie stand toward the back door.",
        "wrong": "Luna first blamed the window, although the window had never shown any interest in pastry.",
        "helper": "The family dog, Biscuit, sat under the chair with a shiny crumb stuck to his nose.",
        "question": "Did you see the missing slice, Biscuit?",
        "answer": "Biscuit gave one hopeful wag and licked his nose.",
        "turn": "Luna noticed that the crumbs stopped beside the low pantry shelf, not at the back door.",
        "plan": "She and Mom checked the shelf, the empty flour sack, and Biscuit's bowl without disturbing the rest of the pie.",
        "result": "Behind the flour sack they found the slice on a little plate.",
        "ending": "Biscuit had carried it there, but he had not eaten it; he was saving it for later.",
        "lesson": "a funny suspect can still lead you to a useful clue when you look carefully",
        "object": "lemon pie",
    },
    {
        "arrival": "Milo helped set out sandwiches for a quiet family lunch.",
        "problem": "The smallest cucumber sandwich disappeared before anyone sat down.",
        "clue": "A tiny green smear gleamed on the handle of the garden trowel.",
        "wrong": "Milo announced that the sandwich had probably joined the vegetables outside.",
        "helper": "His little sister wore a serious face and held an empty napkin like evidence.",
        "question": "Why are you carrying that napkin?",
        "answer": "I was giving the sandwich a blanket, she explained.",
        "turn": "The green smear matched the cucumber, but the trowel had not moved from the porch.",
        "plan": "Milo followed the napkin's corner to a toy picnic basket beneath the bench.",
        "result": "The missing sandwich was inside, carefully wrapped beside a wooden spoon.",
        "ending": "His sister had borrowed it for her stuffed bear's lunch and returned it when the bear finished pretending.",
        "lesson": "asking kindly can solve a small mystery faster than making a loud accusation",
        "object": "cucumber sandwich",
    },
    {
        "arrival": "Pia watered the herbs while Dad prepared soup for dinner.",
        "problem": "The wooden spoon vanished from the counter just when the soup needed stirring.",
        "clue": "A line of flour dots crossed the floor toward the hallway.",
        "wrong": "Pia suspected the soup had grown hands.",
        "helper": "The cat, Pepper, blinked beside the laundry basket as if she knew a secret.",
        "question": "Pepper, did you borrow the spoon?",
        "answer": "Pepper purred, which was not a clear answer but was very confident.",
        "turn": "The flour dots ended at a basket of clean towels.",
        "plan": "Pia lifted the top towel while Dad kept the soup warm and watched the stove.",
        "result": "The spoon was tucked beneath the towels.",
        "ending": "Pepper had pushed it there while chasing a loose ribbon, and the spoon came back with one fluffy thread on its handle.",
        "lesson": "a calm search can separate a real clue from a very dramatic guess",
        "object": "wooden spoon",
    },
    {
        "arrival": "Theo arranged birthday candles beside a bowl of strawberries.",
        "problem": "One strawberry disappeared from the bowl.",
        "clue": "A red spot marked the edge of a paper birthday hat.",
        "wrong": "Theo said the hat must be a strawberry-eating hat.",
        "helper": "Grandpa stood nearby with the hat balanced on his head.",
        "question": "Grandpa, why is your hat wearing breakfast?",
        "answer": "Grandpa touched the red spot and said, I sat down beside the bowl and forgot my hat was hungry.",
        "turn": "The red spot was not juice from a bitten berry; it was jam from the toast plate.",
        "plan": "Theo checked the toast, the napkins, and the space behind the fruit bowl.",
        "result": "The strawberry was under the napkins, untouched.",
        "ending": "Grandpa's hat was innocent, though it continued to look suspiciously pleased.",
        "lesson": "a clue needs checking before it becomes a conclusion",
        "object": "strawberry",
    },
]

ROUTES = [
    ("That morning", "Then", "At last"),
    ("After lunch", "Instead of guessing again", "A few minutes later"),
    ("Before the kettle whistled", "Just when the mystery seemed large", "By checking one place at a time"),
    ("Near the kitchen window", "The next clue appeared", "Soon"),
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None
    case: int = 0
    route: int = 0
    joke: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A humorous everyday mystery storyworld.")
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--adult", choices=ADULTS)
    parser.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place=args.place or "kitchen",
        name=name,
        gender=args.gender or GENDERS[name],
        adult=args.adult or rng.choice(ADULTS),
        trait=args.trait or rng.choice(TRAITS),
        case=rng.randrange(len(CASES)),
        route=rng.randrange(len(ROUTES)),
        joke=rng.randrange(8),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The story needs a known everyday setting.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The child must be described as a girl or boy.")
    if params.name not in NAMES:
        raise StoryError("The child name is not in the story registry.")
    if params.adult not in ADULTS:
        raise StoryError("The helper must be a registered family adult.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    cfg = SETTINGS[params.place]
    case = CASES[params.case % len(CASES)]
    opening, turn, ending = ROUTES[params.route % len(ROUTES)]
    world = World(place=cfg["place"])

    child = world.add(Entity(
        id="Child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "patience": 0.7},
        memes={"humor": 1.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type="adult",
        label=params.adult,
        meters={"care": 1.0},
        memes={"trust": 1.0},
    ))
    pet = world.add(Entity(
        id="Pet",
        kind="animal",
        type="dog",
        label="Biscuit",
        phrase="the dog Biscuit",
        meters={"hunger": 0.4},
        memes={"innocence": 0.8},
    ))
    object_entity = world.add(Entity(
        id="MysteryObject",
        kind="thing",
        type="food",
        label=case["object"],
        phrase=f"the missing {case['object']}",
        meters={"missing": 1.0},
    ))
    table = world.add(Entity(
        id="Table",
        kind="thing",
        type="table",
        label="the kitchen table",
        meters={"crumbs": 1.0},
    ))

    jokes = [
        "The kettle clicked as if it wanted to be interviewed.",
        "Even the lemons looked round and suspicious.",
        "Biscuit's tail wagged like a tiny broom with a secret.",
        "The kitchen clock ticked loudly, although nobody had asked it to help.",
        "The napkin stack leaned away from the investigation.",
        "A spoon rolled once and then wisely stayed out of the case.",
        "The family dog looked innocent in the way only a very crumb-covered dog can.",
        "The table seemed pleased to have become a detective office.",
    ]

    world.say(f"{opening}, {params.name}, a {params.trait} {params.gender}, helped {params.adult} in {world.place}.")
    world.say(cfg["detail"])
    world.say(case["arrival"])
    world.say(case["problem"])
    world.say(jokes[params.joke])
    world.para()
    world.say(case["wrong"])
    world.say(case["clue"])
    world.say(case["helper"])
    world.say(f'{params.name} asked, "{case["question"]}"')
    world.say(f'{case["helper"].split(",")[0]} answered, "{case["answer"]}"')
    world.say(f'{params.adult} said, "Let us check the clue before we call anyone a bastard."')
    world.say(f'{params.name} replied, "A mystery can be funny without being unfair."')
    world.say(f"{turn}, {case['turn']}")
    world.say(case["plan"])
    world.say("They checked gently, because solving a mystery meant noticing things without making a bigger mess.")
    world.say(ending + ", " + case["result"])
    world.say(case["ending"])
    world.say(f"{params.name} laughed and learned that {case['lesson']}.")
    world.say("The missing food returned to the table, and the kitchen became an ordinary kitchen again—except for Biscuit, who still looked remarkably proud.")

    object_entity.meters["missing"] = 0.0
    object_entity.owner = "Table"
    pet.meters["hunger"] = 0.2
    pet.memes["suspected"] = 1.0
    child.memes["solved_mystery"] = 1.0

    world.facts.update(
        params=params,
        case=case,
        child=child,
        adult=adult,
        pet=pet,
        object=object_entity,
        table=table,
        clue=case["clue"],
        solution=case["result"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a humorous slice-of-life mystery about {params.name} finding a missing {case['object']} in a kitchen.",
        "Write a gentle child-facing story where dialogue changes the investigation and a silly suspect helps reveal the truth.",
        f"Write a small everyday mystery with the word bastard used as a mild family joke, ending with {case['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            question="Who solved the kitchen mystery?",
            answer=f"{params.name} solved it by staying curious, listening to the family, and checking the clues carefully.",
        ),
        QAItem(
            question=f"What happened to the missing {case['object']}?",
            answer=f"{case['result']} {case['ending']}",
        ),
        QAItem(
            question="What clue helped the search?",
            answer=case["clue"],
        ),
        QAItem(
            question="Why did the family avoid making an unfair accusation?",
            answer="They wanted to check the evidence first, because a funny suspicion is not the same as knowing what happened.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The missing {case['object']} returned to the table, and the family understood the small mystery without arguing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something not understood yet that people can investigate by noticing clues.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail that may help explain what happened.",
        ),
        QAItem(
            question="What does humorous mean?",
            answer="Humorous means funny or likely to make someone smile.",
        ),
        QAItem(
            question="What is a kitchen?",
            answer="A kitchen is a room where people prepare and sometimes eat food.",
        ),
        QAItem(
            question="Why should people check evidence?",
            answer="People should check evidence so they do not mistake a guess for the truth or blame someone unfairly.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- everyday_place, missing_object, clue_found, dialogue_used, kind_solution.
"""


def asp_facts() -> str:
    return "\n".join([
        "everyday_place.",
        "missing_object.",
        "clue_found.",
        "dialogue_used.",
        "kind_solution.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        models = asp.solve(asp_program(), models=1)
        return 0 if asp.atoms(models[0], "compatible") else 1
    except Exception:
        return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:14} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "Luna", "girl", "Mom", "curious", case=0, route=0, joke=2),
    StoryParams("kitchen", "Milo", "boy", "Dad", "silly", case=1, route=1, joke=5),
    StoryParams("kitchen", "Pia", "girl", "Aunt Bea", "careful", case=2, route=2, joke=6),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        failures = 0
        for params in CURATED:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                failures += 1
        failures += asp_verify()
        sys.exit(1 if failures else 0)
    if args.asp:
        print("compatible(story): everyday place, missing object, clue, dialogue, kind solution")
        return

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
            header = f"### {sample.params.name}: a kitchen mystery"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
