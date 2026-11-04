#!/usr/bin/env python3
"""
A standalone storyworld for a small pizzeria mystery.

A sudden spike in orders hides the reason a tray of dough rounds has vanished.
Clues reveal a gentle transformation, and the solved mystery becomes a shared
meal.
"""

from __future__ import annotations

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


ASP_RULES = r"""
% A sound pizzeria mystery needs clues, an explanation, and a kind resolution.
reasonable_case(C) :-
    mystery_case(C),
    has_clue(C),
    has_explanation(C),
    has_transformation(C),
    has_sharing(C),
    happy_ending(C).
"""

PLACE = "pizzeria"

NAMES = ["Luna", "Mara", "Nico", "Sami", "Tess", "Owen", "Ivy", "Rafi"]
PARTNERS = ["Eli", "Mina", "Jun", "Pip", "Nora", "Sol", "Kit", "Ari"]
PIZZERIAS = ["Moonbeam", "Maple Street", "Red Kettle", "Little Comet"]
TOPPINGS = ["basil", "sweet peppers", "olives", "mushrooms"]

CASE_REGISTRY = {
    "rising_dough": {
        "clue": "A trail of flour dots led to the proofing cupboard, whose lid bulged gently above a warm, yeasty smell.",
        "explanation": (
            "The tray had been tucked into the warm proofing cupboard during the rush. "
            "The dough was dependent on gentle warmth and time to rise."
        ),
        "transformation": (
            "The six neat rounds had risen together into one soft, puffy mound."
        ),
        "sharing": "The cousins shaped the risen dough into little star pizzas for the neighborhood supper.",
        "happy_ending": "Their neighbors shared the golden star-shaped slices around one long table.",
    }
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    partner: str
    pizzeria: str
    topping: str
    case: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in para if part) for para in self.paragraphs if para)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            state = []
            if entity.label:
                state.append(f"label={entity.label!r}")
            if entity.owner:
                state.append(f"owner={entity.owner!r}")
            if entity.meters:
                state.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                state.append(f"memes={dict(entity.memes)}")
            lines.append(f"  {entity.id:10} ({entity.kind:10}) {' '.join(state)}")
        visible_facts = {
            key: value
            for key, value in self.facts.items()
            if key not in {"hero_entity", "partner_entity"}
        }
        lines.append(f"  facts: {visible_facts}")
        return "\n".join(lines)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The story needs a name for its young detective.")
    if not params.partner.strip():
        raise StoryError("The story needs a name for the detective's cousin.")
    if params.pizzeria not in PIZZERIAS:
        raise StoryError(
            "Choose a pizzeria from: " + ", ".join(PIZZERIAS) + "."
        )
    if params.topping not in TOPPINGS:
        raise StoryError(
            "Choose a familiar pizza topping from: " + ", ".join(TOPPINGS) + "."
        )
    if params.case not in CASE_REGISTRY:
        raise StoryError(
            "That pizzeria mystery is not in the story registry. "
            "Try --case rising_dough."
        )


def asp_facts() -> str:
    import asp

    lines = []
    for case_key in CASE_REGISTRY:
        lines.extend(
            [
                asp.fact("mystery_case", case_key),
                asp.fact("has_clue", case_key),
                asp.fact("has_explanation", case_key),
                asp.fact("has_transformation", case_key),
                asp.fact("has_sharing", case_key),
                asp.fact("happy_ending", case_key),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_cases() -> list[str]:
    return list(CASE_REGISTRY)


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        partner=rng.choice(PARTNERS),
        pizzeria=rng.choice(PIZZERIAS),
        topping=rng.choice(TOPPINGS),
        case=rng.choice(valid_cases()),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly pizzeria mystery storyworld."
    )
    parser.add_argument("--name")
    parser.add_argument("--partner")
    parser.add_argument("--pizzeria")
    parser.add_argument("--topping")
    parser.add_argument("--case")
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
    params = valid_params(rng)
    for field_name in ("name", "partner", "pizzeria", "topping", "case"):
        value = getattr(args, field_name, None)
        if value is not None:
            setattr(params, field_name, value)
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.name,
            meters={"steps_from_counter_m": 0.0},
            memes={"curiosity": 0.4, "confidence": 0.3},
        )
    )
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            label=params.partner,
            meters={"steps_from_counter_m": 0.0},
            memes={"worry": 0.7, "trust": 0.5},
        )
    )
    dough = world.add(
        Entity(
            id="dough",
            kind="food",
            label="six dough rounds",
            owner=params.partner,
            meters={"rise_cm": 0.8},
            memes={"patience": 0.8},
        )
    )
    tray = world.add(
        Entity(
            id="tray",
            kind="tool",
            label="the dough tray",
            owner=params.partner,
            meters={"counter_distance_m": 0.0},
        )
    )
    cupboard = world.add(
        Entity(
            id="cupboard",
            kind="furniture",
            label="the proofing cupboard",
            meters={"warmth_c": 31.0},
        )
    )
    world.facts.update(
        hero_entity=hero,
        partner_entity=partner,
        dough=dough,
        tray=tray,
        cupboard=cupboard,
        hero=params.name,
        partner=params.partner,
        pizzeria=params.pizzeria,
        topping=params.topping,
        case=params.case,
        place=PLACE,
        order_spike=True,
        tray_missing=True,
        solved=False,
        transformed=False,
        shared=False,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = CASE_REGISTRY[params.case]
    hero = world.get("hero")
    partner = world.get("partner")
    dough = world.get("dough")
    tray = world.get("tray")

    openings = [
        "At the {pizzeria} pizzeria, the little brass bell rang so often that lunch orders rose in a sudden spike.",
        "The {pizzeria} pizzeria was usually calm at noon, but today a spike in orders sent everyone hurrying.",
        "A bright noon sun shone on the {pizzeria} pizzeria just as a spike in lunch orders made the kitchen bustle.",
    ]
    false_leads = [
        "They checked beneath the prep table and behind the flour sacks, but the tray was nowhere in sight.",
        "They peeked by the back door and under the counter, yet found only a few ordinary crumbs.",
        "They searched the shelves first, careful not to disturb the bowls, but the dough tray was not there.",
    ]
    partner_questions = [
        "Could someone have carried the tray away?",
        "Did I leave the dough by the back door?",
        "Could the dough have disappeared while we were answering orders?",
    ]
    endings = [
        "Flour still dusted their sleeves, but now the cousins were smiling as they passed the first warm slices.",
        "The brass bell rang again, and this time it sounded like a supper invitation.",
        "By the last slice, the once-empty counter held only a bright scatter of flour and a star-shaped crumb.",
    ]

    world.say(rng.choice(openings).format(pizzeria=params.pizzeria))
    world.say(
        f"{hero.label} and their cousin {partner.label} had promised to make a sharing pizza "
        f"for the neighbors. Then the tray of six dough rounds vanished from the counter."
    )
    world.para()

    world.say(rng.choice(false_leads))
    world.say(
        f"{case['clue']} {partner.label} looked worried, and {hero.label} stopped guessing long "
        "enough to follow the trail."
    )
    world.say(
        f'“{rng.choice(partner_questions)}” asked {partner.label}. '
        f'“Let’s follow the flour before we decide,” said {hero.label}.'
    )
    world.para()

    world.say(
        f"At the cupboard, {partner.label} suddenly remembered: “I tucked the tray in here "
        "when the orders began to spike, so the dough could stay warm. I forgot!”"
    )
    world.say(
        f"“That explains the warm cupboard,” said {hero.label}. “The dough was dependent on "
        "gentle warmth and time to rise. Let’s lift the lid together.”"
    )
    world.say(
        f"{case['explanation']} {case['transformation']} "
        "The missing dough had not been taken at all; it had quietly changed while the kitchen was busy."
    )
    world.para()

    hero.bump_meter("steps_from_counter_m", 2.0)
    partner.bump_meter("steps_from_counter_m", 2.0)
    dough.meters["rise_cm"] = 5.5
    dough.memes["patience"] = 1.0
    tray.meters["counter_distance_m"] = 2.0
    hero.bump_meme("confidence", 0.6)
    hero.bump_meme("curiosity", 0.3)
    partner.bump_meme("worry", -0.6)
    partner.bump_meme("trust", 0.4)
    world.facts.update(
        clue=case["clue"],
        explanation=case["explanation"],
        transformation=case["transformation"],
        false_lead=rng.choice(false_leads),
        solved=True,
        transformed=True,
        dough_location="proofing cupboard",
    )

    world.say(
        f"Working side by side, the cousins gently divided the risen dough and shaped it "
        f"into little stars. They added {params.topping}, and Aunt Rosa slid the pizzas into "
        "the oven."
    )
    world.say(
        f"When the stars came out golden, they carried them to the neighborhood table. "
        f"{case['sharing']} {case['happy_ending']}"
    )
    world.say(rng.choice(endings))
    world.facts.update(
        shared=True,
        topping=params.topping,
        resolution=case["sharing"],
        ending_image=case["happy_ending"],
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly mystery at the {facts['pizzeria']} pizzeria about {facts['hero']} and {facts['partner']}.",
        "Include a spike in orders, a useful clue, a gentle transformation, and a happy ending with sharing.",
        f"Tell how the cousins solve the {facts['case'].replace('_', ' ')} mystery and share pizzas topped with {facts['topping']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question="What disappeared during the rush at the pizzeria?",
            answer="The tray of six dough rounds disappeared from the counter during the rush.",
        ),
        QAItem(
            question="What clues helped the cousins find the dough?",
            answer=f"They followed the clue that {facts['clue'][0].lower() + facts['clue'][1:]}",
        ),
        QAItem(
            question=f"Why had the dough changed while {facts['hero']} and {facts['partner']} searched?",
            answer=(
                f"{facts['explanation']} {facts['transformation']}"
            ),
        ),
        QAItem(
            question="How did the cousins turn their discovery into a happy ending?",
            answer=(
                f"They shaped the risen dough into little star pizzas with {facts['topping']}, "
                f"then shared them with the neighbors. {facts['ending_image']}"
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pizzeria?",
            answer="A pizzeria is a place where people make and serve pizza.",
        ),
        QAItem(
            question="What does a spike in orders mean?",
            answer="A spike in orders means that the number of orders suddenly rises.",
        ),
        QAItem(
            question="What does dependent mean?",
            answer="Dependent means needing or relying on something or someone else.",
        ),
        QAItem(
            question="Why does pizza dough rise?",
            answer="Yeast makes tiny bubbles in dough, and gentle warmth and time help the dough puff up.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(
        [
            "",
            "== (2) Story questions -- answerable from the story text ==",
        ]
    )
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(
        [
            "",
            "== (3) World-knowledge questions -- child level, no story needed ==",
        ]
    )
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable_case/1."))
    return sorted(set(asp.atoms(model, "reasonable_case")))


def asp_verify() -> int:
    import asp

    program = asp_program("#show reasonable_case/1.")
    model = asp.one_model(program)
    actual = set(asp.atoms(model, "reasonable_case"))
    expected = {
        (case_key,)
        for case_key in CASE_REGISTRY
        if all(
            (
                CASE_REGISTRY[case_key].get("clue"),
                CASE_REGISTRY[case_key].get("explanation"),
                CASE_REGISTRY[case_key].get("transformation"),
                CASE_REGISTRY[case_key].get("sharing"),
                CASE_REGISTRY[case_key].get("happy_ending"),
            )
        )
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reasonableness gates.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for index, case_key in enumerate(CASE_REGISTRY):
        params = StoryParams(
            name=NAMES[index],
            partner=PARTNERS[index],
            pizzeria=PIZZERIAS[index],
            topping=TOPPINGS[index],
            case=case_key,
            seed=100 + index,
        )
        sample = generate(params)
        required_words = ("pizzeria", "spike", "dependent")
        if not all(word in sample.story.lower() for word in required_words):
            print(f"Generated story is missing a required seed word for {case_key}.")
            return 1
        if sample.story.count("“") < 4 or not sample.world.facts["shared"]:
            print(f"Generated story failed dialogue or sharing checks for {case_key}.")
            return 1
        if not sample.world.facts["solved"] or not sample.world.facts["transformed"]:
            print(f"Generated story failed its mystery or transformation for {case_key}.")
            return 1

    print("OK: ASP and Python gates match; generated stories pass their world checks.")
    return 0


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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


CURATED = [
    StoryParams(
        name="Luna",
        partner="Eli",
        pizzeria="Moonbeam",
        topping="basil",
        case="rising_dough",
        seed=11,
    ),
    StoryParams(
        name="Mara",
        partner="Jun",
        pizzeria="Maple Street",
        topping="sweet peppers",
        case="rising_dough",
        seed=29,
    ),
    StoryParams(
        name="Nico",
        partner="Pip",
        pizzeria="Red Kettle",
        topping="olives",
        case="rising_dough",
        seed=47,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible pizzeria mysteries:")
        for item in asp_list():
            print(item)
        return
    if args.n < 1 and not args.all:
        raise StoryError("The number of stories must be at least one.")

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
    try:
        main()
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        sys.exit(2)
