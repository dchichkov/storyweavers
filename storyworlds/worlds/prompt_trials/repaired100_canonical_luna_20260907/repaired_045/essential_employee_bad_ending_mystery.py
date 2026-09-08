#!/usr/bin/env python3
"""
A small mystery storyworld about an essential employee, a missing key, and a bad
ending that teaches why careful choices matter.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
REPOSITORY_ROOT = STORYWORLDS_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    employee: str
    helper: str
    manager: str
    place: str
    essential_duty: str
    missing_item: str
    seed: Optional[int] = None
    scenario: str = "archive"
    telling_mode: int = 0
    variant: int = 0
    bad_ending: bool = True


EMPLOYEE_NAMES = ["Luna", "Mara", "Nico", "Tess", "Owen", "Suri"]
HELPER_NAMES = ["Pip", "Bea", "Ravi", "Mina", "Jo", "Cal"]
MANAGER_NAMES = ["Mr. Bell", "Ms. Reed", "Aunt Sol", "Captain Vale"]

SCENARIOS: dict[str, dict[str, str]] = {
    "archive": {
        "premise": "the archive clock struck thirteen",
        "trouble": "the essential night employee could not open the records room",
        "clue": "a line of blue dust led from the missing key hook to a cart of fresh paint",
        "risk": "forcing the door would spill the archive shelves into the narrow hall",
        "cause": "the key had been carried away on the paint cart and buried beneath a folded drop cloth",
        "employee_action": "checked the sign-out board instead of blaming the lock",
        "helper_action": "followed the blue dust around the cart's wheels",
        "solution": "they found the key before the shelves were disturbed",
        "repair": "returned the key, cleaned the blue trail, and updated the sign-out board",
        "lesson": "An essential job deserves a careful plan, not a hurried guess.",
        "ending": "The archive clock settled back to twelve, and the records room closed safely.",
    },
    "station": {
        "premise": "the last train bell rang even though no train was due",
        "trouble": "the essential station employee could not find the signal lantern",
        "clue": "warm wax drops ran from the lantern shelf toward the parcel desk",
        "risk": "lighting the wrong lantern would send the next train toward a closed platform",
        "cause": "a parcel had been wrapped around the lantern by mistake and carried to the outgoing pile",
        "employee_action": "read the departure board and marked the unsafe platform",
        "helper_action": "examined the wax drops beside each parcel",
        "solution": "they recovered the lantern before the signal changed",
        "repair": "returned the parcel, relit the proper signal, and labeled the lantern shelf",
        "lesson": "A small clue can protect many people when someone takes time to notice it.",
        "ending": "The train arrived at the safe platform, but the forgotten parcel missed its owner.",
    },
    "greenhouse": {
        "premise": "the greenhouse fans whispered in the wrong rhythm",
        "trouble": "the essential plant employee could not find the watering valve key",
        "clue": "wet footprints crossed the dry path beside a crate of clay pots",
        "risk": "opening every valve would drown the seedlings before the leak was found",
        "cause": "the key had fallen into a clay pot while the delivery crate was moved",
        "employee_action": "closed the main water line and counted the thirsty beds",
        "helper_action": "tipped each empty pot gently over a cloth",
        "solution": "the key appeared before the seedlings were flooded",
        "repair": "reopened the right valve, dried the path, and placed the key on a bright hook",
        "lesson": "Careful work keeps a small mystery from becoming a large loss.",
        "ending": "The fans found their rhythm, but one row of seedlings remained wilted.",
    },
    "bakery": {
        "premise": "the bakery oven chimed before dawn",
        "trouble": "the essential bakery employee could not find the cooling-room pass",
        "clue": "a trail of flour ended beside a basket of unsold rolls",
        "risk": "leaving the hot loaves in the oven would scorch the morning bread",
        "cause": "the pass had slipped beneath the roll basket when someone cleared the counter",
        "employee_action": "moved the loaves to the safe rack and wrote down the oven temperature",
        "helper_action": "lifted the basket by its handles and sifted the flour beneath it",
        "solution": "they found the pass before the bread burned completely",
        "repair": "opened the cooling room, sorted the rolls, and clipped the pass to a red cord",
        "lesson": "Solving one problem carefully is better than creating two in a rush.",
        "ending": "The bread was served, but the burnt loaves left a bitter smell over breakfast.",
    },
}

OPENINGS = [
    "Luna was the essential employee on the quietest shift at {place}.",
    "Everyone at {place} knew that {employee} was an essential employee who noticed small changes.",
    "At {place}, the essential employee {employee} began each shift by checking every important door.",
    "The mystery began when {employee}, the essential employee at {place}, heard a sound that did not belong.",
    "Before sunrise, {employee} arrived at {place} to do the essential work no one else had remembered.",
]

DIALOGUE = [
    '"Do not force it," said {employee}. "What clue do we have?"',
    '"I saw something blue near the cart," said {helper}. "Then we should follow it," answered {employee}.',
    '"Could the key have been moved?" asked {helper}. "A careful search will tell us," said {employee}.',
    '"The danger is growing," said {employee}. "Then let us slow down and look closely," replied {helper}.',
]

BAD_LINES = [
    "They solved the lock, but they had waited too long for the safest result.",
    "The mystery was answered, although the delay left a lasting mark on the place.",
    "Their guess was nearly right, but nearly right was not enough for an essential job.",
    "The clue had been clear; the trouble came from ignoring it at first.",
]


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mystery storyworld about an essential employee.")
    parser.add_argument("--employee")
    parser.add_argument("--helper")
    parser.add_argument("--manager")
    parser.add_argument("--place")
    parser.add_argument("--essential-duty")
    parser.add_argument("--missing-item")
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


def validate(params: StoryParams) -> None:
    if not params.employee.strip():
        raise StoryError("employee must not be empty")
    if params.employee.casefold() == params.helper.casefold():
        raise StoryError("employee and helper must be different people")
    if not params.missing_item.strip():
        raise StoryError("missing_item must not be empty")
    if params.scenario not in SCENARIOS:
        raise StoryError(f"unknown scenario: {params.scenario}")
    if not params.bad_ending:
        raise StoryError("this domain requires the Bad Ending feature")


def generate_world(params: StoryParams) -> World:
    validate(params)
    world = World(params.place)
    world.add(Entity(
        id="employee",
        kind="character",
        type="employee",
        label=params.employee,
        meters={"attention": 0.8, "responsibility": 1.0},
        memes={"essential": 1.0},
    ))
    world.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=params.helper,
        meters={"curiosity": 0.9},
        memes={"patience": 0.8},
    ))
    world.add(Entity(
        id="manager",
        kind="character",
        type="manager",
        label=params.manager,
        meters={"trust": 0.7},
        memes={"accountability": 0.7},
    ))
    world.add(Entity(
        id="missing_item",
        kind="thing",
        label=params.missing_item,
        owner="workplace",
        meters={"found": 0.0},
    ))
    return world


def tell(world: World, params: StoryParams) -> World:
    case = SCENARIOS[params.scenario]
    rng = random.Random((params.seed or 0) ^ params.variant ^ 0x045)
    employee = world.get("employee")
    helper = world.get("helper")
    item = world.get("missing_item")

    opening = OPENINGS[params.telling_mode % len(OPENINGS)].format(
        employee=params.employee,
        place=params.place,
    )
    exchange = DIALOGUE[rng.randrange(len(DIALOGUE))].format(
        employee=params.employee,
        helper=params.helper,
    )

    world.say(opening)
    world.say(f"That morning, {case['premise']}. {case['trouble'].capitalize()}.")
    world.say(f"The missing item was {params.missing_item}, and the next shift depended on it.")
    world.say(f"{params.manager} had called the duty essential because {case['risk']}.")

    world.para()
    world.say(f"{params.employee} found the first clue: {case['clue']}.")
    world.say(exchange)
    world.say(f"{params.employee} {case['employee_action']}.")
    world.say(f"{params.helper} {case['helper_action']}.")
    world.say(f"Neither one knew yet that {case['cause']}.")

    world.para()
    world.say(f"The search became tense because {case['risk']}.")
    world.say(f"Then the clue led them to the answer: {case['cause']}.")
    world.say(f"They recovered the {params.missing_item}, and {case['solution']}.")

    if params.bad_ending:
        world.say(rng.choice(BAD_LINES))
        world.say(f"{params.manager} frowned. \"The mystery is solved, but an essential duty cannot end with careless damage.\"")
        world.say(f"{params.employee} answered, \"Next time, we will follow the clue before the danger grows.\"")
        world.say(f"Together, they {case['repair']}.")
        world.say(case["ending"])
    else:
        raise StoryError("Bad Ending must remain enabled for this storyworld.")

    employee.meters["attention"] = 1.0
    employee.meters["responsibility"] = 0.6
    employee.memes["essential"] = 1.0
    helper.memes["patience"] = 1.0
    item.meters["found"] = 1.0
    world.fired.update({"clue_found", "item_recovered", "bad_ending", "repair_attempted"})
    world.facts = {
        "employee": params.employee,
        "helper": params.helper,
        "manager": params.manager,
        "place": params.place,
        "essential_duty": params.essential_duty,
        "missing_item": params.missing_item,
        "scenario": params.scenario,
        "premise": case["premise"],
        "trouble": case["trouble"],
        "clue": case["clue"],
        "risk": case["risk"],
        "cause": case["cause"],
        "employee_action": case["employee_action"],
        "helper_action": case["helper_action"],
        "solution": case["solution"],
        "repair": case["repair"],
        "lesson": case["lesson"],
        "ending": case["ending"],
        "bad_ending": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a Mystery story about essential employee {facts['employee']} investigating {facts['missing_item']} at {facts['place']}.",
        f"Use the clue '{facts['clue']}' to explain why the item disappeared.",
        f"Include a Bad Ending showing the consequence of delaying an essential duty, followed by a repair attempt.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question="Who was the essential employee?",
            answer=f"{facts['employee']} was the essential employee at {facts['place']}.",
        ),
        QAItem(
            question=f"What item went missing?",
            answer=f"The missing item was {facts['missing_item']}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was that {facts['clue']}.",
        ),
        QAItem(
            question="What had really happened to the missing item?",
            answer=f"{facts['cause'].capitalize()}.",
        ),
        QAItem(
            question="How did the employee and helper work together?",
            answer=f"{facts['employee']} {facts['employee_action']}, while {facts['helper']} {facts['helper_action']}.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because the delay caused consequences even after {facts['solution']}. {facts['ending']}",
        ),
        QAItem(
            question="What lesson did the mystery teach?",
            answer=f"It taught that {facts['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does essential mean?",
            answer="Essential means necessary or very important for something to work.",
        ),
        QAItem(
            question="What is an employee?",
            answer="An employee is a person who works for an organization or another person.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or unanswered question that people investigate to discover the truth.",
        ),
        QAItem(
            question="Why are clues useful?",
            answer="Clues are useful because they provide evidence that can connect an event to its cause.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("role", "essential_employee"),
            asp.fact("feature", "bad_ending"),
            asp.fact("style", "mystery"),
            asp.fact("duty", "careful_search"),
        ]
    )


ASP_RULES = r"""
essential_role(essential_employee).
mystery_style(mystery).
bad_ending_feature(bad_ending).
valid_story :- essential_role(essential_employee),
               mystery_style(mystery),
               bad_ending_feature(bad_ending).
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    atoms = set(asp.atoms(model, "valid_story"))
    if atoms == {()}:
        print("OK: ASP gate confirms essential employee Mystery with Bad Ending.")
        return 0
    print("MISMATCH: ASP gate did not confirm the required story features.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind} label={entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for title, items in [
            ("== Generation prompts ==", sample.prompts),
            ("== Story questions ==", sample.story_qa),
            ("== World questions ==", sample.world_qa),
        ]:
            print(title)
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def generate(params: StoryParams) -> StorySample:
    world = tell(generate_world(params), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(
        employee="Luna",
        helper="Pip",
        manager="Mr. Bell",
        place="the Moon Archive",
        essential_duty="guarding the records",
        missing_item="the brass room key",
        seed=45,
        scenario="archive",
        telling_mode=0,
        variant=45,
    ),
    StoryParams(
        employee="Mara",
        helper="Bea",
        manager="Ms. Reed",
        place="North Station",
        essential_duty="checking the signals",
        missing_item="the signal lantern",
        seed=145,
        scenario="station",
        telling_mode=2,
        variant=145,
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    employee = args.employee or rng.choice(EMPLOYEE_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name.casefold() != employee.casefold()]
    scenario = rng.choice(list(SCENARIOS))
    defaults = {
        "archive": ("the Moon Archive", "guarding the records", "the brass room key"),
        "station": ("North Station", "checking the signals", "the signal lantern"),
        "greenhouse": ("Glasshill Greenhouse", "tending the seedlings", "the watering valve key"),
        "bakery": ("Dawn Bakery", "watching the ovens", "the cooling-room pass"),
    }
    place, duty, item = defaults[scenario]
    return StoryParams(
        employee=employee,
        helper=args.helper or rng.choice(helper_choices),
        manager=args.manager or rng.choice(MANAGER_NAMES),
        place=args.place or place,
        essential_duty=args.essential_duty or duty,
        missing_item=args.missing_item or item,
        seed=None,
        scenario=scenario,
        telling_mode=rng.randrange(len(OPENINGS)),
        variant=rng.randrange(1_000_000_000),
        bad_ending=True,
    )


def format_json(samples: list[StorySample]) -> str:
    if len(samples) == 1:
        return samples[0].to_json()
    return json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1
            if index > max(100, args.n * 40):
                raise StoryError("could not produce enough distinct stories")

    if args.asp:
        if asp_verify() != 0:
            raise StoryError("ASP verification failed")

    if args.json:
        print(format_json(samples))
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
