#!/usr/bin/env python3
"""
A small mystery storyworld set in a pizzeria, where a dependent neighbor
helps uncover a clue and the friends transform a worry into a shared meal.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        STORYWORLDS_ROOT = _parent
        break
else:
    raise RuntimeError("Could not locate storyworlds/results.py")

if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% In this pizzeria, a mystery can become a kind and shareable transformation.
reasonable_story(D) :-
    setting(pizzeria),
    has_transformation,
    has_happy_ending,
    has_sharing,
    dependent(D).
"""


PLACE = "pizzeria"
NAMES = ["Luna", "Milo", "Nia", "Theo", "Zara", "Pip", "Amara", "Jules"]
DEPENDENTS = ["little mouse", "young rabbit", "small hedgehog", "little badger"]
INGREDIENTS = ["tomato", "basil", "cheese", "sweet pepper"]

DEPENDENT_REGISTRY = {
    "little mouse": "a little mouse",
    "young rabbit": "a young rabbit",
    "small hedgehog": "a small hedgehog",
    "little badger": "a little badger",
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
    dependent: str
    ingredient: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    key: str
    premise: str
    trouble: str
    first_try: str
    clue: str
    dependent_line: str
    hero_line: str
    investigation: str
    reveal: str
    transformation: str
    ending_image: str


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            details = []
            if entity.meters:
                details.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                details.append(f"memes={dict(entity.memes)}")
            if entity.label:
                details.append(f"label={entity.label!r}")
            lines.append(
                f"  {entity.id:12} ({entity.kind:10}) {' '.join(details)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


MYSTERIES = [
    Mystery(
        key="thermometer_spike",
        premise="was setting out dough for the evening supper",
        trouble=(
            "The oven thermometer showed a sudden spike, though the oven had "
            "been warming gently a moment before."
        ),
        first_try=(
            "turning the dial down did not explain why the needle jumped "
            "whenever the oven door opened"
        ),
        clue=(
            "a shiny serving spoon lay beside the thermometer, and its bright "
            "reflection moved when the door swung wide"
        ),
        dependent_line=(
            '"The needle jumps with the door, not with the oven," the little '
            "neighbor noticed."
        ),
        hero_line=(
            '"Then let us check the oven safely before we bake anything," '
            "Luna said."
        ),
        investigation=(
            "Luna switched the oven off and asked the grown-up cook to check "
            "the thermometer away from the spoon"
        ),
        reveal=(
            "the oven was warming steadily; the moving reflection had only "
            "made the needle hard to read"
        ),
        transformation=(
            "After the cook confirmed the oven was safe, the friends turned "
            "the quiet corner into a little supper table and made a fresh "
            "cheese-and-tomato pizza"
        ),
        ending_image=(
            "The thermometer rested clearly on its hook while the warm pizza "
            "was shared in neat, golden slices."
        ),
    ),
    Mystery(
        key="vanishing_dough",
        premise="was shaping dough for the neighborhood supper",
        trouble=(
            "There was a spike in the number of dough rounds missing from the "
            "tray, and nobody knew where they had gone."
        ),
        first_try=(
            "counting the empty spaces again still left one round unaccounted "
            "for"
        ),
        clue=(
            "a soft trail of flour curved toward the covered basket by the "
            "cool window"
        ),
        dependent_line=(
            '"The flour trail stops at the basket," the young neighbor said. '
            '"Could the dough be resting there?"'
        ),
        hero_line=(
            '"Good eyes. We can lift the cloth gently and find out together," '
            "Luna replied."
        ),
        investigation=(
            "they lifted one corner of the cloth while the cook checked the "
            "dough"
        ),
        reveal=(
            "the cook had tucked the rounds there to keep them cool, then "
            "forgotten to tell the pizza makers"
        ),
        transformation=(
            "The friends brought the dough back, shaped one round together, "
            "and transformed the empty tray into a place for a shared "
            "vegetable pizza"
        ),
        ending_image=(
            "The flour trail ended at a basket of safely covered dough, and "
            "the last slice went to the little neighbor."
        ),
    ),
    Mystery(
        key="mystery_bell",
        premise="was preparing the pizzeria for its evening guests",
        trouble=(
            "A spike in the number of little bell rings came from the empty "
            "front counter, as if an unseen guest were calling."
        ),
        first_try=(
            "looking through the front window showed no one waiting outside"
        ),
        clue=(
            "the bell rang just after the back door moved, and a loose paper "
            "menu fluttered beside it"
        ),
        dependent_line=(
            '"The door breeze is moving that menu," the little neighbor said. '
            '"Listen for the next ring."'
        ),
        hero_line=(
            '"I will hold the door still, and you can watch the bell," Luna '
            "answered."
        ),
        investigation=(
            "they tested the idea together while the cook made sure the "
            "doorway stayed clear"
        ),
        reveal=(
            "a corner of the menu was tapping the bell whenever a breeze "
            "slipped through the doorway"
        ),
        transformation=(
            "They moved the menu to a safe stand, then transformed the "
            "silent counter into a sharing station with small plates and a "
            "fresh basil pizza"
        ),
        ending_image=(
            "The bell waited quietly beside the menu as friends passed warm "
            "basil pizza around the table."
        ),
    ),
    Mystery(
        key="missing_menu_star",
        premise="was arranging a special menu for the supper table",
        trouble=(
            "The golden star that marked the sharing pizza had vanished, and "
            "a spike of floury footprints crossed the floor."
        ),
        first_try=(
            "searching the empty menu board did not reveal who had moved the "
            "star"
        ),
        clue=(
            "the smallest footprints turned toward the low shelf, where a "
            "piece of gold paper peeked out"
        ),
        dependent_line=(
            '"I tucked it there so I could reach it," the small neighbor '
            "explained. 'I wanted to help.'"
        ),
        hero_line=(
            '"Thank you for telling me. Let us make a place you can reach," '
            "Luna said."
        ),
        investigation=(
            "they checked the shelf together and brought the star back "
            "without disturbing the other menus"
        ),
        reveal=(
            "the dependent neighbor had moved the star while trying to help, "
            "but the tall board had been too hard to reach"
        ),
        transformation=(
            "Luna lowered the menu to the neighbor's height, and they "
            "transformed the board into a shared menu where everyone could "
            "choose a topping"
        ),
        ending_image=(
            "The golden star shone at the little neighbor's eye level above "
            "a pizza covered in everyone’s favorite toppings."
        ),
    ),
]


OPENINGS = [
    "At supper time, warm light filled the pizzeria as {name} opened the door.",
    "The pizzeria smelled of fresh dough when {name} noticed something unusual.",
    "A little bell chimed over the pizzeria door, and {name} looked up from the counter.",
    "Just before the neighborhood supper, {name} found a mystery waiting in the pizzeria.",
    "Flour dust sparkled in the pizzeria's window as {name} began the evening preparations.",
]

REACTIONS = [
    "{name} paused instead of guessing; a mystery needed careful eyes.",
    "{name} took a breath and asked the neighbor what they had noticed.",
    "The first answer had not helped, so {name} looked again for a clue.",
    "{name} listened closely, ready to follow the smallest useful detail.",
]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A pizzeria story needs a name for its main character.")
    if params.dependent not in DEPENDENTS:
        raise StoryError(
            "Choose a dependent neighbor from the pizzeria's small-animal registry."
        )
    if params.ingredient not in INGREDIENTS:
        raise StoryError(
            "Choose a familiar pizza ingredient such as tomato, basil, cheese, or sweet pepper."
        )


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "pizzeria"),
        "has_transformation.",
        "has_happy_ending.",
        "has_sharing.",
    ]
    lines.extend(asp.fact("dependent", value.replace(" ", "_")) for value in DEPENDENTS)
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_dependents() -> list[str]:
    return list(DEPENDENTS)


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        dependent=rng.choice(DEPENDENTS),
        ingredient=rng.choice(INGREDIENTS),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery, transformation, and sharing at a neighborhood pizzeria."
    )
    parser.add_argument("--name")
    parser.add_argument("--dependent", choices=valid_dependents())
    parser.add_argument("--ingredient", choices=INGREDIENTS)
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
    if args.name is not None:
        params.name = args.name
    if args.dependent is not None:
        params.dependent = args.dependent
    if args.ingredient is not None:
        params.ingredient = args.ingredient
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", label=params.name))
    neighbor = world.add(
        Entity(id="neighbor", kind="character", label=params.dependent)
    )
    pizza = world.add(Entity(id="pizza", kind="food", label=params.ingredient))
    world.facts.update(
        hero=hero,
        neighbor=neighbor,
        pizza=pizza,
        place=PLACE,
        transformation=True,
        happy_ending=True,
        sharing=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    mystery = rng.choice(MYSTERIES)
    opening = rng.choice(OPENINGS).format(name=params.name)
    reaction = rng.choice(REACTIONS).format(name=params.name)
    hero = world.get("hero")
    neighbor = world.get("neighbor")
    pizza = world.get("pizza")
    dependent_phrase = DEPENDENT_REGISTRY[neighbor.label]

    hero.bump_meme("care")
    neighbor.bump_meme("hope")
    world.say(opening)
    world.say(
        f"{hero.label} was getting ready to share supper with {dependent_phrase}. "
        f"The little neighbor was dependent on the pizzeria's supper basket while "
        f"their family tended to a broken kitchen. {hero.label} {mystery.premise}."
    )
    world.para()

    world.say(mystery.trouble)
    world.say(f"At first, {mystery.first_try}.")
    world.say(reaction)
    world.para()

    hero.bump_meme("curiosity")
    neighbor.bump_meme("courage")
    world.say(f"Then they noticed a clue: {mystery.clue}.")
    world.say(mystery.dependent_line)
    world.say(mystery.hero_line)
    world.say(mystery.investigation.capitalize() + ".")
    world.para()

    world.get("pizza").bump_meter("prepared", 1)
    world.get("hero").bump_meter("careful_steps", 1)
    world.say(f"The mystery was solved: {mystery.reveal}.")
    world.say(mystery.transformation + f", using {pizza.label}.")
    world.say(mystery.ending_image)
    world.para()

    hero.bump_meme("joy")
    neighbor.bump_meme("belonging")
    neighbor.bump_meter("shared_supper", 1)
    world.say(
        f"{hero.label} and {neighbor.label} shared the meal, and the neighbor "
        "helped choose the very last topping."
    )
    world.say(
        "The pizzeria felt different now: its small mystery had made more room "
        "for everyone at the table."
    )

    world.facts.update(
        mystery=mystery.key,
        trouble=mystery.trouble,
        first_try=mystery.first_try,
        clue=mystery.clue,
        reveal=mystery.reveal,
        investigation=mystery.investigation,
        transformation=mystery.transformation,
        ending_image=mystery.ending_image,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"].label
    neighbor = facts["neighbor"].label
    return [
        f"Write a child-friendly mystery set in a pizzeria where {hero} and {neighbor} follow a clue.",
        "Tell a story about a dependent neighbor, a surprising spike, and a kind discovery.",
        "Write a complete story with a transformation, a happy ending, and a meal shared by friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    neighbor = facts["neighbor"].label
    return [
        QAItem(
            question="What mystery interrupted supper preparations?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue helped {hero} and {neighbor} investigate?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question="What did the friends discover?",
            answer=f"They discovered that {facts['reveal']}.",
        ),
        QAItem(
            question="How did the pizzeria change after the mystery was solved?",
            answer=facts["transformation"] + ".",
        ),
        QAItem(
            question="What showed that the ending was happy?",
            answer=str(facts["ending_image"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people investigate by noticing clues and asking careful questions.",
        ),
        QAItem(
            question="What does dependent mean?",
            answer="Dependent means needing or relying on someone or something for help, care, or support.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people enjoy or use something with you.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change that makes someone or something different from before.",
        ),
    ]


def dump_trace(world: World) -> str:
    return world.trace()


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions -- answerable from the story text =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World-knowledge questions -- child level, no story needed =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show reasonable_story/1."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show reasonable_story/1."))
    asp_results = set(asp.atoms(model, "reasonable_story"))
    python_results = set()
    for dependent in DEPENDENTS:
        try:
            reasonableness_gate(
                StoryParams(
                    name="Luna",
                    dependent=dependent,
                    ingredient="cheese",
                    seed=1,
                )
            )
        except StoryError:
            continue
        python_results.add((dependent.replace(" ", "_"),))

    if asp_results != python_results:
        print("MISMATCH between the Python reasonableness gate and ASP twin.")
        print("ASP:", sorted(asp_results))
        print("PY :", sorted(python_results))
        return 1

    for seed in range(32):
        params = StoryParams(
            name=NAMES[seed % len(NAMES)],
            dependent=DEPENDENTS[seed % len(DEPENDENTS)],
            ingredient=INGREDIENTS[seed % len(INGREDIENTS)],
            seed=seed,
        )
        sample = generate(params)
        text = sample.story.lower()
        required = (
            "pizzeria",
            "dependent",
            "spike",
            "mystery",
            "shared",
        )
        if any(word not in text for word in required):
            print(f"Generated-story check failed for seed {seed}.")
            return 1
        if '"' not in sample.story or not sample.world.facts.get("resolved"):
            print(f"Dialogue or resolution check failed for seed {seed}.")
            return 1

    print("OK: ASP matches the Python gate, and generated stories pass their checks.")
    return 0


CURATED = [
    StoryParams(name="Luna", dependent="little mouse", ingredient="cheese", seed=3),
    StoryParams(name="Milo", dependent="young rabbit", ingredient="basil", seed=8),
    StoryParams(name="Nia", dependent="small hedgehog", ingredient="tomato", seed=11),
    StoryParams(name="Theo", dependent="little badger", ingredient="sweet pepper", seed=14),
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible pizzeria story choices:")
        for item in asp_list():
            print(item)
        return
    if args.n < 0:
        raise StoryError("The number of stories must be zero or greater.")

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
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
    main()
