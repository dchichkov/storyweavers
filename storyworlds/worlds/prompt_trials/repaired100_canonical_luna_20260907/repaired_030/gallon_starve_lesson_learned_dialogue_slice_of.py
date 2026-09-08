#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a gallon of soup, an empty pantry, and
the lesson that noticing hunger and speaking kindly can change an ordinary day.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    child: str
    neighbor: str
    meal: str
    problem: str
    lesson: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Meal:
    name: str
    description: str
    smell: str
    serving: str


@dataclass(frozen=True)
class Problem:
    opening: str
    clue: str
    need: str
    repair: str
    result: str


@dataclass(frozen=True)
class Lesson:
    temptation: str
    admission: str
    advice: str
    action: str
    meaning: str


MEALS = {
    "soup": Meal(
        "vegetable soup",
        "a warm pot of vegetable soup",
        "carrots and tomatoes",
        "one gallon of soup",
    ),
    "stew": Meal(
        "bean stew",
        "a thick pot of bean stew",
        "onions and cumin",
        "one gallon of stew",
    ),
    "porridge": Meal(
        "apple porridge",
        "a large pot of apple porridge",
        "cinnamon and baked apples",
        "one gallon of porridge",
    ),
    "chili": Meal(
        "mild chili",
        "a red pot of mild chili",
        "beans and sweet peppers",
        "one gallon of chili",
    ),
}

PROBLEMS = {
    "empty_pantry": Problem(
        "After school, the kitchen smelled good, but the cupboard looked unusually bare.",
        "A single cracker sat on the shelf beside an empty lunch box.",
        "The neighbor had been too busy to eat and was trying not to say that hunger made the afternoon feel long.",
        "They filled a clean container, carried it across the hall, and made a simple plate before sitting down together.",
        "The neighbor ate slowly, and the tight look around their eyes softened.",
    ),
    "late_shift": Problem(
        "At supper time, the apartment hallway was quiet because the neighbor had just come home from a late shift.",
        "Their keys shook in the lock, and their kitchen light stayed off.",
        "The neighbor had skipped lunch and dinner while working, though they kept saying they were fine.",
        "They warmed a bowl, left the rest in a labeled container, and waited without making the neighbor feel watched.",
        "The neighbor finally smiled and asked for a second spoonful.",
    ),
    "rainy_day": Problem(
        "Rain tapped the windows while the child set the table for two.",
        "The neighbor's grocery bag held only tea, even though the evening was nearly over.",
        "The neighbor had planned to starve the worry away by pretending hunger was not important.",
        "They shared the meal, then wrote a small shopping list together for the next morning.",
        "The rain kept falling, but nobody in the hallway had to face it on an empty stomach.",
    ),
    "forgotten_lunch": Problem(
        "The child returned from school and found the neighbor looking under the sofa cushions.",
        "A lunch receipt was tucked in a pocket, but the lunch itself had never been bought.",
        "The neighbor had forgotten to eat during a hurried day.",
        "They divided the meal into two bowls and packed a second portion for the morning.",
        "The neighbor promised to keep a snack by the door.",
    ),
}

LESSONS = {
    "notice": Lesson(
        "pretend not to notice because asking might feel awkward",
        '"I noticed you had not eaten," the child said. "I should have asked sooner."',
        '"Kind questions do not make hunger embarrassing," the neighbor replied.',
        "ask gently, offer food, and listen to the answer",
        "care often begins with noticing a small clue and making room for an honest answer",
    ),
    "share": Lesson(
        "keep the whole gallon because there might not be enough for tomorrow",
        '"I was counting every spoonful," the child admitted. "But you need supper tonight."',
        '"Sharing does not mean forgetting tomorrow," the neighbor said. "We can plan for both days."',
        "serve two bowls, save a portion, and make a plan for breakfast",
        "a thoughtful share can meet a present need without ignoring the future",
    ),
    "ask_help": Lesson(
        "solve the problem silently so nobody would know the family was worried",
        '"I cannot fix every empty cupboard alone," the child said.',
        '"Asking for help gives other people a chance to be kind," the neighbor answered.',
        "call the building pantry and add their names to the next food pickup",
        "accepting help is a brave way to make sure no one has to starve alone",
    ),
    "listen": Lesson(
        "talk quickly and offer advice before hearing the whole story",
        '"Tell me what happened first," the child said. "I will listen."',
        '"Being heard helps me think about what I need," the neighbor replied.',
        "listen through the awkward silence, then offer the meal without a lecture",
        "listening can be as useful as food when someone feels ashamed or alone",
    ),
}

ENDINGS = {
    "window": "By the time the windows turned black with evening, two clean bowls rested beside the gallon pot.",
    "calendar": "Before bed, they marked the next pantry day on the calendar and left a snack by the door.",
    "hallway": "The hallway smelled of warm food, and the neighbor's key turned easily in the lock.",
    "morning": "In the morning, the saved portion became breakfast, and nobody had to pretend hunger was nothing.",
    "recipe": "They copied the recipe onto a card and wrote one more line beneath it: Ask who needs a bowl.",
}

NAMES = ["Luna", "Mara", "Niko", "Pia", "Sol", "Ivy", "Theo", "June"]
NEIGHBORS = ["Milo", "Rina", "Ari", "Tess", "Owen", "Nell", "Sam", "Bea"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("home_kitchen", meal, "neighbor") for meal in MEALS]


def explain_rejection() -> str:
    return "This storyworld only supports a home kitchen, a shared gallon of food, and a hungry neighbor."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slice-of-life gallon sharing storyworld.")
    parser.add_argument("--place", choices=["home_kitchen"])
    parser.add_argument("--meal", choices=sorted(MEALS))
    parser.add_argument("--recipient", choices=["neighbor"])
    parser.add_argument("--child")
    parser.add_argument("--neighbor")
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--lesson", choices=sorted(LESSONS))
    parser.add_argument("--ending", choices=sorted(ENDINGS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place not in (None, "home_kitchen"):
        raise StoryError(explain_rejection())
    if args.recipient not in (None, "neighbor"):
        raise StoryError(explain_rejection())
    child = args.child or rng.choice(NAMES)
    neighbor = args.neighbor or rng.choice([n for n in NEIGHBORS if n != child])
    if child == neighbor:
        raise StoryError("The child and neighbor need different names.")
    return StoryParams(
        child=child,
        neighbor=neighbor,
        meal=args.meal or rng.choice(list(MEALS)),
        problem=args.problem or rng.choice(list(PROBLEMS)),
        lesson=args.lesson or rng.choice(list(LESSONS)),
        ending=args.ending or rng.choice(list(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    meal = MEALS[params.meal]
    problem = PROBLEMS[params.problem]
    lesson = LESSONS[params.lesson]
    world = World()
    child = world.add(Entity(
        "child", "character", "child", params.child, "kitchen",
        meters={"energy": 0.7}, memes={"care": 0.4},
    ))
    neighbor = world.add(Entity(
        "neighbor", "character", "neighbor", params.neighbor, "hallway",
        meters={"energy": 0.3, "hunger": 0.9}, memes={"embarrassment": 0.7},
    ))
    pot = world.add(Entity(
        "gallon_pot", "food", "pot", meal.description, "kitchen",
        meters={"fullness": 1.0}, memes={"comfort": 0.8},
    ))
    world.facts.update(child=child, neighbor=neighbor, pot=pot, meal=meal, problem=problem, lesson=lesson)

    world.say(f"After school, {params.child} came home and found {meal.description} warming in the kitchen.")
    world.say(f"It held {meal.serving}, enough for supper and a little more.")
    world.say(problem.opening)

    world.para()
    world.say(problem.clue)
    world.say(f"{params.neighbor} knocked softly, then said, \"It smells wonderful, but I am all right.\"")
    world.say(f"\"You do not sound all right,\" {params.child} replied. \"Did you eat today?\"")
    world.say(f"{params.neighbor} looked down. \"Not really. I did not want to make it anyone else's problem.\"")
    neighbor.memes["embarrassment"] = 0.3
    child.memes["attention"] = 1.0

    world.para()
    world.say(problem.need)
    world.say(f"For one moment, {params.child} was tempted to {lesson.temptation}.")
    world.say(lesson.admission)
    world.say(lesson.advice)
    world.say(f"Then {params.child} chose to {lesson.action}.")
    pot.meters["fullness"] = 0.55
    neighbor.meters["hunger"] = 0.15
    neighbor.memes["relief"] = 1.0
    world.fired.add(("shared", params.meal))

    world.para()
    world.say(problem.repair)
    world.say(f"{problem.result}")
    world.say(f"They understood that {lesson.meaning}.")
    world.say(ENDINGS[params.ending])
    world.facts["resolved"] = True
    world.facts["lesson_meaning"] = lesson.meaning
    world.facts["changed_fact"] = problem.result
    return world


def generation_prompts(world: World) -> list[str]:
    meal: Meal = world.facts["meal"]  # type: ignore[assignment]
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life story about {meal.serving} shared in an ordinary home.",
        f"Include a dialogue where someone admits they may starve if nobody notices their hunger.",
        f"Show a lesson learned through a small, practical act of kindness: {problem.repair}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    neighbor: Entity = world.facts["neighbor"]  # type: ignore[assignment]
    meal: Meal = world.facts["meal"]  # type: ignore[assignment]
    problem: Problem = world.facts["problem"]  # type: ignore[assignment]
    lesson: Lesson = world.facts["lesson"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Who noticed that {neighbor.label} had not eaten?",
            f"{child.label} noticed the clues and asked {neighbor.label} directly instead of pretending nothing was wrong.",
        ),
        QAItem(
            f"What did {child.label} share?",
            f"{child.label} shared {meal.serving} from {meal.description}, serving a bowl and saving a portion for later.",
        ),
        QAItem(
            "What changed after the dialogue?",
            f"{neighbor.label} admitted being hungry, and the two neighbors made a practical plan. {problem.result}",
        ),
        QAItem(
            "What lesson was learned?",
            f"They learned that {lesson.meaning}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a gallon?",
            "A gallon is a unit used to measure liquid or food volume; it is larger than a quart.",
        ),
        QAItem(
            "Why is it important to notice hunger?",
            "Hunger can make a person tired and unwell, so noticing it gives people a chance to offer food or find help.",
        ),
        QAItem(
            "Why can dialogue help solve a problem?",
            "Kind dialogue lets people share facts and feelings, so they can understand the need and choose a useful action.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, location={entity.location}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(home_kitchen).
recipient(neighbor).
meal(soup).
meal(stew).
meal(porridge).
meal(chili).

valid(home_kitchen,soup,neighbor).
valid(home_kitchen,stew,neighbor).
valid(home_kitchen,porridge,neighbor).
valid(home_kitchen,chili,neighbor).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("place", "home_kitchen"),
        asp.fact("recipient", "neighbor"),
    ]
    facts.extend(asp.fact("meal", name) for name in MEALS)
    facts.extend(asp.fact("valid", "home_kitchen", meal, "neighbor") for meal in MEALS)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between Python and ASP valid combinations.")
    print("Only in Python:", sorted(python_set - asp_set))
    print("Only in ASP:", sorted(asp_set - python_set))
    return 1


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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        for prompt in sample.prompts:
            print(f"\n[Prompt] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print("\n" + show_qa_item(item))


CURATED = [
    StoryParams("Luna", "Milo", "soup", "empty_pantry", "notice", "window"),
    StoryParams("Pia", "Rina", "stew", "late_shift", "share", "calendar"),
    StoryParams("Theo", "Bea", "porridge", "rainy_day", "listen", "morning"),
    StoryParams("June", "Sam", "chili", "forgotten_lunch", "ask_help", "recipe"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 20):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
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
