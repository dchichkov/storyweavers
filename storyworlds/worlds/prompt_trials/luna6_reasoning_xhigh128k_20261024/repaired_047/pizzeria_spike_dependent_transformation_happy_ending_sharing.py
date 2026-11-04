#!/usr/bin/env python3
"""
A standalone mystery storyworld about a neighborhood pizzeria, a puzzling bowl
of dough, and the friends who solve the case before supper.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _storyworlds_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "results.py").is_file():
            return parent
    return Path(__file__).resolve().parents[2]


STORYWORLDS_ROOT = _storyworlds_root()
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% A reasonable pizzeria mystery has a clue, a safe repair, and a hopeful ending.
mystery_case(K) :- registered_case(K), has_clue(K), safe_repair(K).
complete_story(K) :- mystery_case(K), transformation(K), sharing(K), happy_ending(K).
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = float(value)

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    baker: str
    guest: str
    pizzeria: str
    case_key: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    key: str
    label: str
    problem: str
    first_attempt: str
    failed_try: str
    clue: str
    detective_line: str
    baker_line: str
    explanation: str
    repair: str
    change_sentence: str
    result: str
    ending_image: str
    start_warmth: float
    start_rise: float
    start_moisture: float
    failed_rise_drop: float
    repaired_warmth: float
    repaired_rise: float
    repaired_moisture: float
    door_open: float = 0.0
    fan_running: float = 0.0
    oven_spike: float = 0.35
    has_clue: bool = True
    safe_repair: bool = True
    transformation: bool = True
    sharing: bool = True
    happy_ending: bool = True


CASES = [
    MysteryCase(
        key="cold_door",
        label="The Case of the Chilly Dough",
        problem="it had stayed flat in its bowl, even after a long rest",
        first_attempt="{name} blamed sleepy yeast and stirred in a pinch more",
        failed_try="the extra stirring only made the dough tighter",
        clue="paper tickets streamed toward the half-open back door, while the dough bowl felt cool along its sides",
        detective_line=(
            "The oven gauge spiked, but those tickets point to the back door. "
            "Could a cold draft be chilling the bowl?"
        ),
        baker_line=(
            "That's the clue. Dough is dependent on steady warmth, not a blazing oven. "
            "Let's shut the door and move the bowl to the proofing shelf."
        ),
        explanation=(
            "A draft from the partly open back door kept the dough too cool to rise."
        ),
        repair=(
            "shut the back door, moved the bowl to the gently warm proofing shelf, "
            "and let the dough rest without another stir"
        ),
        change_sentence=(
            "Soon, tiny bubbles freckled the surface, and the stubborn flat lump "
            "rose into a soft dome."
        ),
        result=(
            "Their first little pizza baked with an airy edge and a warm, tomato-red center."
        ),
        ending_image=(
            "A curl of steam fogged the rainy window while a golden slice traveled "
            "from hand to hand."
        ),
        start_warmth=0.20,
        start_rise=0.12,
        start_moisture=0.84,
        failed_rise_drop=0.03,
        repaired_warmth=0.67,
        repaired_rise=0.86,
        repaired_moisture=0.84,
        door_open=1.0,
        oven_spike=0.88,
    ),
    MysteryCase(
        key="fan_cover",
        label="The Case of the Cracked Dough",
        problem="it had puffed underneath, but its top had dried into a cracked little crust",
        first_attempt="{name} splashed water over the stiff top",
        failed_try="the wet patches turned sticky while the dry cracks stayed put",
        clue=(
            "a clean cloth lay on its hook, and the prep fan was blowing paper tickets "
            "away from the uncovered bowl"
        ),
        detective_line=(
            "The cover didn't disappear; the fan blew it off the bowl. "
            "That's why the top dried!"
        ),
        baker_line=(
            "You found it. Resting dough is dependent on a cover that keeps its moisture in. "
            "Let's stop the fan, mist the top lightly, and cover it with a clean damp cloth."
        ),
        explanation=(
            "The running prep fan blew the cloth off and dried the exposed dough."
        ),
        repair=(
            "switched off the prep fan, misted the dry surface lightly, "
            "and covered the bowl with a clean damp cloth"
        ),
        change_sentence=(
            "Under the quiet cover, the cracked surface softened and the dough puffed evenly."
        ),
        result=(
            "The dough stretched without tearing, and the pizzas came out tender instead of tough."
        ),
        ending_image=(
            "The clean cloth hung nearby to dry, and the neighbor's plate gleamed with "
            "one soft, bubbly slice."
        ),
        start_warmth=0.56,
        start_rise=0.50,
        start_moisture=0.22,
        failed_rise_drop=0.12,
        repaired_warmth=0.58,
        repaired_rise=0.89,
        repaired_moisture=0.83,
        fan_running=1.0,
        oven_spike=0.36,
    ),
    MysteryCase(
        key="oven_shelf",
        label="The Case of the Sinking Dough",
        problem="it had ballooned high, then sunk into a sticky hollow",
        first_attempt=(
            "{name} pressed the dough down and returned the bowl to the same warming shelf"
        ),
        failed_try="it ballooned too fast again and slumped",
        clue=(
            "the warming shelf sat directly above the oven vent; its thermometer showed "
            "a sharp spike, and the bowl felt too warm underneath"
        ),
        detective_line=(
            "The oven isn't broken—this shelf is catching all its heat. "
            "The thermometer has spiked right beside the dough."
        ),
        baker_line=(
            "Exactly. Dough is dependent on gentle warmth; too much makes it rise too fast "
            "and collapse. Let's move it to the cooler counter and give it a patient second rise."
        ),
        explanation=(
            "The shelf above the oven vent made the dough rise too quickly and collapse."
        ),
        repair=(
            "moved the bowl to the cooler counter, gently pressed out the extra air, "
            "and let it rise slowly a second time"
        ),
        change_sentence=(
            "This time the dough rose just to the rim, springy and even, instead of spilling over."
        ),
        result=(
            "Each pizza had a light, steady crust that held its toppings."
        ),
        ending_image=(
            "The thermometer rested quietly while the friends passed a light-crusted pie "
            "beneath the bright kitchen lamp."
        ),
        start_warmth=0.97,
        start_rise=0.43,
        start_moisture=0.78,
        failed_rise_drop=0.18,
        repaired_warmth=0.62,
        repaired_rise=0.82,
        repaired_moisture=0.78,
        oven_spike=0.98,
    ),
]

CASE_REGISTRY = {case.key: case for case in CASES}
DETECTIVE_NAMES = ["Mina", "Theo", "Nia", "Amir", "Jo", "Tess", "Ravi", "Sasha", "Ben", "Luca"]
BAKERS = ["Rosa", "Pietro", "Bea", "Sal", "Marco", "Asha"]
GUESTS = ["Eli", "June", "Kit", "Luz", "Finn", "Ivy"]
PIZZERIAS = [
    "Lantern Pizzeria",
    "Moonstone Pizzeria",
    "Clover Pizzeria",
    "Little Comet Pizzeria",
]

OPENINGS = [
    "Rain tapped the windows of {pizzeria} as {name} tied on an apron.",
    "The mystery began at {pizzeria}, just as the supper bell rang.",
    "At {pizzeria}, the last streak of daylight reached the floury counter.",
    "A warm smell of tomato and basil filled {pizzeria} as {name} hurried inside.",
    "The oven hummed at {pizzeria}, but something strange was happening beside the prep table.",
]

CLOSING_DETAILS = [
    "A little flour still dusted their sleeves, but nobody minded.",
    "The ticket rail was empty at last, and the kitchen sounded like a room full of friends.",
    "Even the old oven seemed to hum more cheerfully.",
    "The friends left one clean plate ready for the next person who came in hungry.",
    "Their teamwork made the busy kitchen feel like home.",
]


@dataclass
class World:
    place: str = "pizzeria"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part for part in paragraph) for paragraph in self.paragraphs if paragraph)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            bits = [f"label={entity.label!r}"]
            if entity.owner:
                bits.append(f"owner={entity.owner!r}")
            if entity.meters:
                bits.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                bits.append(f"memes={dict(entity.memes)}")
            lines.append(f"  {entity.id:16} ({entity.kind:12}) {' '.join(bits)}")
        lines.append(f"  place: {self.place}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


@dataclass(frozen=True)
class StoryBlueprint:
    opening: str
    closing_detail: str


def reasonableness_gate(params: StoryParams) -> None:
    for field_name, label in (
        ("name", "The detective"),
        ("baker", "The baker"),
        ("guest", "The neighbor"),
        ("pizzeria", "The pizzeria"),
    ):
        value = getattr(params, field_name)
        if not isinstance(value, str) or not value.strip():
            raise StoryError(f"{label} needs a name.")
        if len(value) > 48 or "\n" in value or "\r" in value:
            raise StoryError(f"{label} name must be a short, single-line name.")

    if params.pizzeria not in PIZZERIAS:
        raise StoryError("Choose a pizzeria from the pizzeria registry.")
    if params.baker not in BAKERS:
        raise StoryError("Choose a baker from the baker registry.")
    if params.guest not in GUESTS:
        raise StoryError("Choose a neighbor from the guest registry.")
    if params.case_key not in CASE_REGISTRY:
        raise StoryError(f"Unknown pizzeria mystery case: {params.case_key!r}.")
    if len({params.name, params.baker, params.guest}) != 3:
        raise StoryError("The detective, baker, and neighbor need different names.")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The story seed must be an integer.")

    case = CASE_REGISTRY[params.case_key]
    if not (
        case.has_clue
        and case.safe_repair
        and case.transformation
        and case.sharing
        and case.happy_ending
    ):
        raise StoryError("This mystery needs a clear clue, a safe repair, sharing, and a happy transformation.")


def valid_params(rng: random.Random) -> StoryParams:
    detective = rng.choice(DETECTIVE_NAMES)
    baker = rng.choice(BAKERS)
    guest = rng.choice(GUESTS)
    while guest in {detective, baker}:
        guest = rng.choice(GUESTS)
    return StoryParams(
        name=detective,
        baker=baker,
        guest=guest,
        pizzeria=rng.choice(PIZZERIAS),
        case_key=rng.choice(CASES).key,
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-friendly pizzeria mystery storyworld."
    )
    parser.add_argument("--name", help="Name of the young detective.")
    parser.add_argument("--baker", help="Choose a baker from the baker registry.")
    parser.add_argument("--guest", help="Choose a neighbor from the guest registry.")
    parser.add_argument("--pizzeria", help="Choose a pizzeria from the pizzeria registry.")
    parser.add_argument("--case", dest="case_key", help="Choose a registered dough mystery.")
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate.")
    parser.add_argument("--all", action="store_true", help="Generate one story for each mystery case.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for repeatable generation.")
    parser.add_argument("--trace", action="store_true", help="Print the simulated world state.")
    parser.add_argument("--qa", action="store_true", help="Print prompts and question-answer sets.")
    parser.add_argument("--json", action="store_true", help="Print results as JSON.")
    parser.add_argument("--asp", action="store_true", help="List cases accepted by the ASP twin.")
    parser.add_argument("--verify", action="store_true", help="Check ASP parity and exercise stories.")
    parser.add_argument("--show-asp", action="store_true", help="Print the inline ASP program.")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    if args.name is not None:
        params.name = args.name
    if args.baker is not None:
        params.baker = args.baker
    if args.guest is not None:
        params.guest = args.guest
    if args.pizzeria is not None:
        params.pizzeria = args.pizzeria
    if args.case_key is not None:
        params.case_key = args.case_key
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    case = CASE_REGISTRY[params.case_key]
    world = World()
    world.add(Entity(id="pizzeria", kind="place", label=params.pizzeria))
    world.add(Entity(id="detective", kind="character", label=params.name, owner="pizzeria"))
    world.add(Entity(id="baker", kind="character", label=params.baker, owner="pizzeria"))
    world.add(Entity(id="guest", kind="character", label=params.guest, owner="community_table"))
    world.add(Entity(id="oven", kind="equipment", label="stone oven", owner="pizzeria"))
    world.add(Entity(id="dough", kind="food", label="community supper dough", owner="pizzeria"))
    world.add(Entity(id="bowl", kind="container", label="dough bowl", owner="pizzeria"))
    world.add(Entity(id="back_door", kind="fixture", label="back door", owner="pizzeria"))
    world.add(Entity(id="prep_fan", kind="equipment", label="prep fan", owner="pizzeria"))
    world.add(Entity(id="thermometer", kind="tool", label="oven thermometer", owner="pizzeria"))
    world.add(Entity(id="ticket_rail", kind="fixture", label="order ticket rail", owner="pizzeria"))
    world.add(Entity(id="pizza", kind="food", label="shared pizza", owner="community_table"))
    world.add(Entity(id="table", kind="furniture", label="community supper table", owner="community"))
    world.add(Entity(id="pizzeria", kind="place", label=params.pizzeria))

    dough = world.get("dough")
    dough.set_meter("warmth", case.start_warmth)
    dough.set_meter("rise", case.start_rise)
    dough.set_meter("surface_moisture", case.start_moisture)
    world.get("oven").set_meter("heat", 0.78)
    world.get("oven").set_meter("reading_spike", case.oven_spike)
    world.get("back_door").set_meter("open", case.door_open)
    world.get("prep_fan").set_meter("running", case.fan_running)
    world.get("ticket_rail").set_meter("orders", 1.0)
    world.get("pizza").set_meter("baked", 0.0)
    world.get("table").set_meter("ready", 1.0)

    world.facts.update(
        pizzeria=params.pizzeria,
        detective=params.name,
        baker=params.baker,
        guest=params.guest,
        case_key=case.key,
        case_label=case.label,
        mystery_solved=False,
        dough_transformed=False,
        sharing=False,
        happy_ending=False,
    )
    return world


def choose_blueprint(params: StoryParams) -> StoryBlueprint:
    rng = random.Random(params.seed if params.seed is not None else 0)
    return StoryBlueprint(
        opening=rng.choice(OPENINGS).format(pizzeria=params.pizzeria, name=params.name),
        closing_detail=rng.choice(CLOSING_DETAILS),
    )


def tell_story(world: World, params: StoryParams) -> None:
    reasonableness_gate(params)
    case = CASE_REGISTRY[params.case_key]
    blueprint = choose_blueprint(params)

    detective = world.get("detective")
    baker = world.get("baker")
    guest = world.get("guest")
    dough = world.get("dough")
    oven = world.get("oven")
    pizzeria = world.get("pizzeria")

    detective.bump_meme("curiosity", 0.5)
    detective.bump_meme("worry", 0.7)
    baker.bump_meme("care", 0.5)
    pizzeria.bump_meme("busy", 1.0)

    world.say(blueprint.opening)
    world.say(
        "The little pizzeria was dependent on steady teamwork; a spike in dinner orders "
        "had filled the ticket rail. Their neighbor, "
        f"{guest.label}, waited at the community table, but the last bowl of dough "
        f"was the night's mystery: {case.problem}."
    )
    world.para()

    first_attempt = case.first_attempt.format(name=detective.label)
    world.say(f"At first, {first_attempt}, but {case.failed_try}.")
    dough.bump_meter("rise", -case.failed_rise_drop)
    detective.bump_meme("worry", 0.4)
    world.say(f"A closer look uncovered the clue: {case.clue}.")
    world.say(f'"{case.detective_line}" {detective.label} said.')
    world.say(f'"{case.baker_line}" {baker.label} replied.')
    detective.bump_meme("curiosity", 0.8)
    baker.bump_meme("trust", 0.7)
    world.para()

    world.say(
        f"Following that explanation, {detective.label} and {baker.label} {case.repair}."
    )
    dough.set_meter("warmth", case.repaired_warmth)
    dough.set_meter("rise", case.repaired_rise)
    dough.set_meter("surface_moisture", case.repaired_moisture)
    world.get("back_door").set_meter("open", 0.0)
    world.get("prep_fan").set_meter("running", 0.0)
    if dough.meters["rise"] >= 0.75:
        world.say(case.change_sentence)
    else:
        world.say("They waited patiently, checking that the dough was becoming soft and airy.")
    world.facts["mystery_solved"] = True
    world.facts["diagnosis"] = case.explanation
    world.facts["repair"] = case.repair
    detective.bump_meme("confidence", 1.0)
    baker.bump_meme("relief", 0.8)
    world.para()

    world.say(
        f"With the mystery solved, {detective.label} stretched the risen dough into small "
        f"rounds while {baker.label} spooned on tomato sauce and cheese. The oven "
        "transformed the pale rounds into golden pizzas with bubbling tops."
    )
    world.get("pizza").set_meter("baked", 1.0)
    world.get("pizza").set_meter("rounds_shared", 1.0)
    dough.set_meter("transformed", 1.0)
    pizzeria.bump_meme("welcome", 1.0)
    world.say(case.result)
    world.say(f'"You found the cause," {baker.label} said. "Let\'s share the first pie."')
    world.say(f'"And save a slice for {guest.label}!" {detective.label} replied.')
    world.say(
        f"They shared the warm pizzas with their neighbor, {guest.label}, and the people "
        "around the community table."
    )
    world.say(f"{case.ending_image} {blueprint.closing_detail}")
    world.facts.update(
        mystery_solved=True,
        dough_transformed=True,
        sharing=True,
        happy_ending=True,
        problem=case.problem,
        first_attempt=first_attempt,
        failed_try=case.failed_try,
        clue=case.clue,
        explanation=case.explanation,
        change_sentence=case.change_sentence,
        result=case.result,
        ending_image=case.ending_image,
        orders_filled=True,
    )
    detective.bump_meme("joy", 1.0)
    baker.bump_meme("joy", 0.8)
    guest.bump_meme("belonging", 1.0)
    pizzeria.bump_meter("orders_filled", 1.0)


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly mystery at {facts['pizzeria']} where {facts['detective']} "
        f"and baker {facts['baker']} solve a dough problem.",
        "Tell a pizzeria mystery with a clear clue, a surprising but safe explanation, "
        "a transformation, and a happy ending.",
        f"Write a story about {facts['detective']} sharing supper with neighbor "
        f"{facts['guest']} after solving a pizzeria mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question="What was the mystery in the pizzeria?",
            answer=f"The dough mystery was that {facts['problem']}.",
        ),
        QAItem(
            question=f"What clue helped {facts['detective']} and {facts['baker']} solve it?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question="What was really causing the dough trouble?",
            answer=str(facts["explanation"]),
        ),
        QAItem(
            question=f"What did {facts['detective']} and {facts['baker']} do after finding the clue?",
            answer=f"{facts['detective']} and {facts['baker']} {facts['repair']}.",
        ),
        QAItem(
            question="How did the dough change after the repair?",
            answer=f"After the friends corrected the problem, {facts['change_sentence']}",
        ),
        QAItem(
            question=f"How did the friends share their happy ending with {facts['guest']}?",
            answer=(
                f"{facts['detective']} and {facts['baker']} shared the finished pizzas "
                f"with their neighbor, {facts['guest']}, and the people at the community table."
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
            question="Why do bakers let dough rest?",
            answer=(
                "Resting gives yeast time to make tiny bubbles that help dough rise "
                "and become lighter."
            ),
        ),
        QAItem(
            question="Why might a baker cover resting dough?",
            answer=(
                "A clean cover helps keep the dough from drying out while it rests."
            ),
        ),
        QAItem(
            question="What does sharing mean?",
            answer=(
                "Sharing means giving others a chance to enjoy something with you."
            ),
        ),
        QAItem(
            question="What is a happy ending?",
            answer=(
                "A happy ending is when the main worry is solved and the characters "
                "finish with hope, safety, or joy."
            ),
        ),
    ]


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "pizzeria"),
        asp.fact("style", "mystery"),
    ]
    for case in CASES:
        lines.extend(
            [
                asp.fact("registered_case", case.key),
                asp.fact("has_clue", case.key) if case.has_clue else "",
                asp.fact("safe_repair", case.key) if case.safe_repair else "",
                asp.fact("transformation", case.key) if case.transformation else "",
                asp.fact("sharing", case.key) if case.sharing else "",
                asp.fact("happy_ending", case.key) if case.happy_ending else "",
            ]
        )
    return "\n".join(line for line in lines if line)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_cases() -> set[str]:
    return {
        case.key
        for case in CASES
        if case.has_clue
        and case.safe_repair
        and case.transformation
        and case.sharing
        and case.happy_ending
    }


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(
        asp_program("#show mystery_case/1.\n#show complete_story/1.")
    )
    return sorted(set(asp.atoms(model, "complete_story")))


def asp_verify() -> int:
    import asp

    show = "#show mystery_case/1.\n#show complete_story/1."
    model = asp.one_model(asp_program(show))
    asp_mysteries = set(asp.atoms(model, "mystery_case"))
    asp_complete = set(asp.atoms(model, "complete_story"))

    python_gate: set[str] = set()
    for case in CASES:
        params = StoryParams(
            name="Mina",
            baker="Rosa",
            guest="Eli",
            pizzeria=PIZZERIAS[0],
            case_key=case.key,
            seed=17,
        )
        try:
            reasonableness_gate(params)
        except StoryError:
            continue
        python_gate.add(case.key)

    expected = {(key,) for key in python_gate}
    if asp_mysteries != expected or asp_complete != expected:
        print("MISMATCH between the ASP twin and the Python reasonableness gate.")
        print("ASP mystery cases:", sorted(asp_mysteries))
        print("ASP complete stories:", sorted(asp_complete))
        print("Python gate:", sorted(expected))
        return 1

    failures = []
    for index, case in enumerate(CASES):
        params = StoryParams(
            name="Mina",
            baker="Rosa",
            guest="Eli",
            pizzeria=PIZZERIAS[index % len(PIZZERIAS)],
            case_key=case.key,
            seed=100 + index,
        )
        sample = generate(params)
        if not all(word in sample.story.lower() for word in ("pizzeria", "spike", "dependent")):
            failures.append(f"{case.key}: a requested seed word is missing")
        if sample.story.count('"') < 8:
            failures.append(f"{case.key}: the story is missing spoken exchanges")
        if sample.world is None or not (
            sample.world.facts.get("mystery_solved")
            and sample.world.facts.get("dough_transformed")
            and sample.world.facts.get("sharing")
            and sample.world.facts.get("happy_ending")
        ):
            failures.append(f"{case.key}: the simulated story did not reach its resolution")
        if not sample.story_qa or any(not item.answer.strip().endswith(".") for item in sample.story_qa):
            failures.append(f"{case.key}: story-grounded answers are incomplete")

    if failures:
        print("STORY EXERCISE FAILED:")
        for failure in failures:
            print("-", failure)
        return 1

    print(
        f"OK: ASP and Python agree on {len(expected)} mystery cases; "
        f"all {len(CASES)} generated stories reached a shared, transformed happy ending."
    )
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


def dump_trace(world: World) -> str:
    return world.trace()


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
    StoryParams(
        name="Mina",
        baker="Rosa",
        guest="Eli",
        pizzeria="Lantern Pizzeria",
        case_key="cold_door",
        seed=11,
    ),
    StoryParams(
        name="Theo",
        baker="Bea",
        guest="June",
        pizzeria="Moonstone Pizzeria",
        case_key="fan_cover",
        seed=29,
    ),
    StoryParams(
        name="Nia",
        baker="Sal",
        guest="Kit",
        pizzeria="Clover Pizzeria",
        case_key="oven_shelf",
        seed=47,
    ),
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.n < 0:
        parser.error("-n must be zero or greater.")

    if args.show_asp:
        print(asp_program("#show mystery_case/1.\n#show complete_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible pizzeria mystery cases:")
        for item in asp_list():
            print(item[0].replace("_", " "))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    try:
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            seen: set[str] = set()
            attempts = 0
            limit = max(100, args.n * 50)
            while len(samples) < args.n and attempts < limit:
                params = resolve_params(args, random.Random(rng.randrange(2**31)))
                sample = generate(params)
                attempts += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
    except StoryError as exc:
        parser.error(str(exc))

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
