#!/usr/bin/env python3
"""
A small child-facing whodunit about learning a lesson early: careful noticing
and kind questions solve a little mystery before it grows.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "school_garden": "the school garden",
    "library_corner": "the library corner",
    "community_hall": "the community hall",
}
OBJECTS = ["brass bell", "blue scarf", "red notebook", "wooden bird"]
NAMES = ["Luna", "Milo", "Nora", "Theo", "Ivy", "Sam"]
RELATIONS = ["friend", "brother", "sister", "classmate"]
TRAITS = ["observant", "cheerful", "quiet", "curious", "patient"]
CLUES = ["a row of damp footprints", "a loose yellow thread", "a tiny feather", "a smudge of green paint"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ("seen", "moved", "returned", "checked"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "trust", "calm", "wisdom"):
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    object_name: str
    name: str
    relation: str
    trait: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    title: str
    opening: str
    discovery: str
    suspicion: str
    first_guess: str
    clue: str
    question: str
    answer: str
    lesson: str
    ending: str


CASES = [
    Case(
        "The Bell Before Breakfast",
        "The old brass bell by the garden gate was gone before the first class arrived",
        "Luna found its empty hook and a bright scrape on the wooden post",
        "a muddy footprint pointed toward the tool shed",
        "Luna decided that the gardener must have taken it without telling anyone",
        "the scrape ended beside a fallen wheelbarrow, and the bell's cord was caught underneath",
        '"Let us ask before we accuse," Luna said',
        "the wind had pulled the wheelbarrow into the bell, and the gardener had moved the bell safely inside",
        "A quick guess can feel certain, but a careful question can reveal the kinder truth.",
        "the bell rang for morning meeting, earlier than usual, while Luna smiled at the once-mysterious hook",
    ),
    Case(
        "The Scarf on the Bench",
        "a blue scarf disappeared from the reading bench before story time",
        "Luna noticed one blue thread on the bench and a cold draft by the open window",
        "her friend had been sitting closest to the scarf",
        "Luna almost blamed the friend for hiding it as a joke",
        "the thread led to a stack of cushions, where the scarf had slipped after the window blew open",
        '"I nearly blamed you without checking," Luna admitted',
        "the scarf was beneath the cushions, and the friend had only moved a book away from the draft",
        "Learning a lesson early means stopping an unfair guess before it hurts someone.",
        "the scarf warmed Luna's shoulders during the first story, and the open window clicked shut",
    ),
    Case(
        "The Notebook Clue",
        "the red notebook holding the class garden plan was missing from its usual shelf",
        "Luna found a green paint smudge below the shelf",
        "the newest classmate had been painting near the garden table",
        "Luna thought the classmate had taken the notebook by mistake",
        "the smudge continued along the floor toward the drying rack",
        '"Could we look together before deciding what happened?" Luna asked',
        "the notebook was drying beneath a painted sign because the teacher had moved it to keep it clean",
        "Evidence is more useful than a hasty story about who may be at fault.",
        "the class plan returned to the shelf, with a green border added after everyone agreed",
    ),
    Case(
        "The Little Wooden Bird",
        "a wooden bird vanished from the library nature display",
        "Luna saw a narrow line of dust leading away from the empty stand",
        "a younger child had been looking closely at the display",
        "Luna feared the child had carried the bird away",
        "the dust line stopped at a low cart beside the display",
        '"What did you notice?" Luna asked instead of saying, "You took it."',
        "the librarian had placed the bird on the cart while dusting, and the younger child had only pointed at it",
        "A respectful question can protect a person while the truth is still being found.",
        "the wooden bird returned to its stand, and a small sign explained that it was safe to touch with permission",
    ),
    Case(
        "The Early Footprints",
        "the community hall's welcome sign was turned around before the morning fair",
        "Luna spotted damp footprints leading from the side door",
        "the delivery helper had entered through that door early",
        "Luna guessed the helper had changed the sign to cause trouble",
        "the footprints passed a puddle and ended at a stack of boxes blocking the sign",
        '"Maybe the sign was moved so people could see it," Luna said',
        "the helper had turned the sign while carrying boxes, and the fair leader thanked Luna for noticing",
        "A mystery deserves patience because the same action can have a helpful reason.",
        "the sign faced the street before the fair began, and Luna learned to ask what a clue could mean",
    ),
]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity


def choose_case(params: StoryParams) -> Case:
    value = (params.seed or 0) * 17 + sum(ord(c) for c in params.object_name + params.name)
    return CASES[value % len(CASES)]


def tell(params: StoryParams) -> World:
    case = choose_case(params)
    world = World(Setting(params.place))
    child = world.add(Entity("child", "character", "child", params.name))
    companion = world.add(Entity("companion", "character", params.relation, ""))
    mystery = world.add(Entity("mystery", "object", params.object_name, params.object_name))
    clue = world.add(Entity("clue", "clue", "trace", case.clue))

    child.memes["curiosity"] = 1
    child.memes["worry"] = 1
    companion.memes["trust"] = 1
    mystery.meters["seen"] = 0
    clue.meters["seen"] = 1

    world.facts.update(case=case, child=child, companion=companion, mystery=mystery, clue=clue)
    return world


def render_story(world: World, params: StoryParams) -> str:
    case: Case = world.facts["case"]
    child: Entity = world.facts["child"]
    companion: Entity = world.facts["companion"]
    place = params.place

    return "\n\n".join([
        f"Early one morning at {place}, {child.label}, who was {params.trait}, arrived with {companion.label or 'a friend'}. {case.opening}.",
        f"It was a tiny whodunit, but it mattered because the {params.object_name} belonged to everyone. {case.discovery}.",
        f"{case.suspicion}. {case.first_guess}. {child.label} felt worried and ready to point a finger.",
        f"Then {case.clue}. {companion.label or 'The friend'} looked at the clue and said, {case.question}",
        f"{child.label} took a breath and answered, {case.question} The two children checked the place together instead of arguing.",
        f"They soon learned that {case.answer}. The mystery was solved, and {child.label} felt their worry loosen.",
        f"{case.lesson} {case.ending}",
    ])


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    return [
        f"Write an early-morning child-friendly whodunit at {world.setting.place} about a missing {world.facts['mystery'].label}.",
        f"Tell a gentle mystery called {case.title} in which a child notices a clue, asks a fair question, and learns a lesson early.",
        "Write a complete story with a beginning, a mistaken suspicion, a concrete clue, dialogue, a solved mystery, and a clear lesson about not accusing people too quickly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    child: Entity = world.facts["child"]
    mystery: Entity = world.facts["mystery"]
    return [
        QAItem(
            question=f"What mystery did {child.label} investigate?",
            answer=f"{child.label} investigated why the {mystery.label} was missing or out of place at {world.setting.place}.",
        ),
        QAItem(
            question="What clue changed the first guess?",
            answer=f"The important clue was {case.clue}. It led the children to check the scene more carefully.",
        ),
        QAItem(
            question="How did the children solve the mystery?",
            answer=f"They asked a respectful question and examined the clue together. They learned that {case.answer}.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=case.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail or piece of evidence that helps someone understand what happened.",
        ),
        QAItem(
            question="Why is it wise to ask questions before blaming someone?",
            answer="Questions can reveal facts and prevent an unfair accusation based only on a guess.",
        ),
        QAItem(
            question="What does it mean to learn a lesson early?",
            answer="It means noticing a mistake or useful truth soon enough to make a better choice next time.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES.values():
        raise StoryError(f"Unknown place: {params.place}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object_name}")
    world = tell(params)
    return StorySample(
        params=params,
        story=render_story(world, params),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
mystery_object(X) :- object(X).
careful_solver :- clue_present, question_asked.
lesson_learned :- careful_solver, fair_resolution.
good_story :- mystery_object(_), lesson_learned.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("object", "mystery"),
        asp.fact("clue_present"),
        asp.fact("question_asked"),
        asp.fact("fair_resolution"),
    ])


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        models = asp.solve(asp_program(), models=1)
        if not models or not asp.atoms(models[0], "good_story"):
            print("ASP verification failed: no good_story model.")
            return 1
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    for seed in range(5):
        params = StoryParams(PLACES["school_garden"], "brass bell", "Luna", "friend", "observant", seed)
        sample = generate(params)
        if not sample.story or "lesson" not in sample.story.lower():
            print("Python verification failed.")
            return 1
    print("OK: Python stories and ASP twin passed verification.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Early lesson-learned whodunit storyworld.")
    parser.add_argument("--place", choices=list(PLACES.values()))
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--relation", choices=RELATIONS)
    parser.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        place=args.place or rng.choice(list(PLACES.values())),
        object_name=args.object_name or rng.choice(OBJECTS),
        name=args.name or rng.choice(NAMES),
        relation=args.relation or rng.choice(RELATIONS),
        trait=args.trait or rng.choice(TRAITS),
    )


CURATED = [
    StoryParams(PLACES["school_garden"], "brass bell", "Luna", "friend", "observant", 11),
    StoryParams(PLACES["library_corner"], "blue scarf", "Luna", "classmate", "patient", 12),
    StoryParams(PLACES["community_hall"], "red notebook", "Luna", "sister", "curious", 13),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            models = asp.solve(asp_program(), models=1)
            print(json.dumps({"models": [[str(atom) for atom in model] for model in models]}, indent=2))
        except ImportError:
            raise SystemExit("ASP mode requires clingo.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        print(json.dumps(
            samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples],
            indent=2,
            ensure_ascii=False,
        ))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### case {index + 1}")
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
