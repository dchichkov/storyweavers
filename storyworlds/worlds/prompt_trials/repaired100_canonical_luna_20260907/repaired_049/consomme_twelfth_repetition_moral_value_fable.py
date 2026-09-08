#!/usr/bin/env python3
"""
A small fable about a twelfth bowl of consomme, the repetition of a kind act,
and the moral value of patience.

The world models a village kitchen, its physical supplies, and the emotional
memes that grow when a young helper repeats a careful kindness.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Recipe:
    id: str
    name: str
    liquid: str
    flavor: str
    servings: int


@dataclass(frozen=True)
class Trial:
    id: str
    problem: str
    clue: str
    remedy: str
    result: str
    moral: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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


SETTING = Setting(
    place="the monastery kitchen",
    affordances={"cooking", "counting", "sharing", "listening"},
)

RECIPES = {
    "clear_consom​​me": Recipe(
        id="clear_consomme",
        name="consomme",
        liquid="clear broth",
        flavor="parsley and roasted onion",
        servings=12,
    )
}

TRIALS = {
    "twelfth_bowl": Trial(
        id="twelfth_bowl",
        problem="the first eleven bowls were warm and clear, but the twelfth bowl kept turning cloudy",
        clue="a thin veil of steam gathered whenever the ladle was hurried",
        remedy="lifted the ladle slowly, skimmed the broth three times, and repeated the same patient motion",
        result="the twelfth bowl became clear enough to reflect the kitchen window",
        moral="patience repeated with care becomes a kindness that others can taste",
    )
}

NAMES = ["Luna", "Mara", "Tavi", "Niko", "Sela", "Pia"]
ELDER_NAMES = ["the old cook", "the patient aunt", "the keeper of the hearth"]
ADJECTIVES = ["curious", "quick", "gentle", "restless", "thoughtful", "hopeful"]

OPENINGS = [
    "In a little kitchen beneath a bell tower, a cook prepared one pot of consomme for twelve hungry travelers.",
    "At the edge of a quiet village stood a kitchen where every bowl was counted before the soup was served.",
    "A young helper once entered a monastery kitchen just as a fragrant pot of consomme began to sing.",
    "The village fable begins with a silver ladle, a deep pot, and twelve bowls waiting in a row.",
]

DIALOGUES = [
    ("Why does the last bowl resist us?", "Perhaps it is asking us to slow down."),
    ("Should I hurry before the travelers arrive?", "No. A repeated careful act may save the whole meal."),
    ("What did you notice in the steam?", "It curled when the ladle moved too quickly."),
    ("Must I do the same motion again?", "If the first eleven were helped by care, the twelfth deserves care too."),
]

ENDING_IMAGES = [
    "The twelfth bowl shone like a small moon, and the travelers ate in grateful silence.",
    "When the bell rang, twelve clear bowls stood together, each carrying the same warm kindness.",
    "Luna placed the last bowl beside the first eleven, and the row looked like twelve golden promises.",
    "The kitchen window reflected twelve bowls, but the cook said the brightest one was the patience behind them.",
]


@dataclass
class StoryParams:
    place: str
    recipe: str
    trial: str
    name: str
    trait: str
    elder: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable about consomme, repetition, and moral value."
    )
    parser.add_argument("--place", choices=["kitchen"])
    parser.add_argument("--recipe", choices=["clear_consomme"])
    parser.add_argument("--trial", choices=["twelfth_bowl"])
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=ADJECTIVES)
    parser.add_argument("--elder", choices=ELDER_NAMES)
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
    recipe = args.recipe or "clear_consomme"
    trial = args.trial or "twelfth_bowl"
    if recipe not in RECIPES:
        raise StoryError("Unknown recipe.")
    if trial not in TRIALS:
        raise StoryError("Unknown trial.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(ADJECTIVES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams("kitchen", recipe, trial, name, trait, elder)


def reasonableness_gate(params: StoryParams) -> None:
    if params.recipe != "clear_consomme":
        raise StoryError("This fable requires the consomme recipe.")
    if params.trial != "twelfth_bowl":
        raise StoryError("This fable's trial is the twelfth bowl.")


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def simulate(world: World, params: StoryParams) -> None:
    recipe = RECIPES[params.recipe]
    trial = TRIALS[params.trial]
    choice = (params.seed or 0) % len(DIALOGUES)
    dialogue = DIALOGUES[choice]
    ending = ENDING_IMAGES[(params.seed or 0) % len(ENDING_IMAGES)]

    child = world.add(Entity(params.name, "character", "child", params.name))
    elder = world.add(Entity("cook", "character", "cook", params.elder))
    pot = world.add(Entity("pot", "object", "pot", "the copper pot"))
    ladle = world.add(Entity("ladle", "object", "ladle", "the silver ladle"))
    bowls = world.add(Entity("bowls", "object", "bowls", "twelve white bowls"))

    add_meme(child, "curiosity")
    add_meme(child, "impatience")
    add_meter(pot, "servings", recipe.servings)

    world.say(OPENINGS[(params.seed or 0) % len(OPENINGS)])
    world.say(
        f"{child.label}, a {params.trait} helper, counted {recipe.servings} bowls while "
        f"{elder.label} watched the clear broth tremble in the pot."
    )
    world.say(
        f"The first eleven bowls of {recipe.name} were ready, but {trial.problem}."
    )
    world.para()

    world.say(
        f"{child.label} lifted the {ladle.label} quickly and said, "
        f"\"{dialogue[0]}\""
    )
    world.say(f"{elder.label} answered, \"{dialogue[1]}\"")
    add_meme(child, "attention")
    add_meme(elder, "trust")
    world.say(f"Together they watched the steam. {trial.clue}.")
    world.say(
        f"{child.label} tried the careful work once, then again, and then a twelfth time: "
        f"{trial.remedy}."
    )
    add_meter(child, "repeated_care", 1.0)
    add_meter(ladle, "patient_strokes", 3.0)
    world.para()

    world.say(f"The result was plain: {trial.result}.")
    add_meme(child, "patience")
    add_meme(child, "kindness")
    add_meter(bowls, "filled", 12.0)
    world.say(
        f"The elder placed the twelfth bowl beside the other eleven and said, "
        f"\"A moral value is not proved by saying its name. It is proved by repeating it "
        f"when the last person still needs it.\""
    )
    world.say(
        f"{child.label} understood that {trial.moral}. Then {ending}"
    )

    world.facts.update(
        child=child,
        elder=elder,
        recipe=recipe,
        trial=trial,
        pot=pot,
        ladle=ladle,
        bowls=bowls,
        dialogue=dialogue,
        ending=ending,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    simulate(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    trial = world.facts["trial"]
    return [
        f"Write a fable about {child.label}, consomme, and the twelfth bowl.",
        f"Tell a child-friendly story in which repetition reveals the moral value of patience.",
        f"Write a gentle kitchen tale using this problem: {trial.problem}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    recipe = world.facts["recipe"]
    trial = world.facts["trial"]
    return [
        QAItem(
            "Who helped prepare the twelfth bowl?",
            f"{child.label}, a {child.memes and 'curious' or 'young'} kitchen helper, prepared the twelfth bowl with the old cook.",
        ),
        QAItem(
            "What was wrong with the twelfth bowl?",
            f"The twelfth bowl of {recipe.name} kept turning cloudy even though the first eleven bowls were clear.",
        ),
        QAItem(
            "What clue did the helper notice?",
            f"The helper noticed that {trial.clue}.",
        ),
        QAItem(
            "What did the helper repeat?",
            f"The helper {trial.remedy}. Repeating the careful motion made the broth clear.",
        ),
        QAItem(
            "What moral value did the story teach?",
            f"It taught that {trial.moral}.",
        ),
        QAItem(
            "How did the story end?",
            f"{trial.result.capitalize()}, and the twelfth bowl joined the other eleven so the travelers could share the meal.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is consomme?",
            "Consomme is a clear, carefully strained soup made from flavorful broth.",
        ),
        QAItem(
            "What is repetition?",
            "Repetition means doing an action again, often so it can be practiced or completed carefully.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle that helps people choose caring, fair, or responsible actions.",
        ),
        QAItem(
            "Why can patience help while cooking?",
            "Patience can help because slow, careful work gives ingredients and tools time to produce a better result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(kitchen, clear_consomme, twelfth_bowl).
has_moral_value(twelfth_bowl, patience).
uses_repetition(twelfth_bowl).
consomme(clear_consomme).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "kitchen"),
            asp.fact("recipe", "clear_consomme"),
            asp.fact("trial", "twelfth_bowl"),
        ]
    )


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("kitchen", "clear_consomme", "twelfth_bowl")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_values = set(valid_combos())
        asp_values = set(asp_valid_combos())
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    if python_values != asp_values:
        print("MISMATCH: ASP and Python registries differ.")
        return 1
    sample = generate(
        StoryParams("kitchen", "clear_consomme", "twelfth_bowl", "Luna", "patient", "the old cook")
    )
    required = ["consomme", "twelfth", "repeated", "moral value"]
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story omitted a required narrative instrument.")
        return 1
    print("OK: ASP matches Python and generated story passed.")
    return 0


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
    StoryParams("kitchen", "clear_consomme", "twelfth_bowl", "Luna", "curious", "the old cook"),
    StoryParams("kitchen", "clear_consomme", "twelfth_bowl", "Tavi", "gentle", "the patient aunt"),
    StoryParams("kitchen", "clear_consomme", "twelfth_bowl", "Mara", "restless", "the keeper of the hearth"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
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
            header = f"### {sample.params.name}: consomme / twelfth bowl"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
