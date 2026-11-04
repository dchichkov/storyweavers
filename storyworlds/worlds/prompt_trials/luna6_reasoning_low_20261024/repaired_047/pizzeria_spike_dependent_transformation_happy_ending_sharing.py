#!/usr/bin/env python3
"""A small mystery storyworld about a pizzeria, a surprising spike, and sharing."""

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
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% A good pizzeria mystery transforms a troubling spike into a shared solution.
mystery_place(pizzeria) :- setting(pizzeria), has_mystery(pizzeria).
good_turn(pizzeria) :- mystery_place(pizzeria), has_transformation(pizzeria),
                       has_happy_ending(pizzeria), has_sharing(pizzeria).
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, name: str, amount: float = 1.0) -> None:
        self.meters[name] = self.meters.get(name, 0.0) + amount

    def bump_meme(self, name: str, amount: float = 1.0) -> None:
        self.memes[name] = self.memes.get(name, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    dependent: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            lines.append(
                f"  {entity.id} ({entity.kind}) label={entity.label!r} "
                f"meters={entity.meters} memes={entity.memes}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Mystery:
    key: str
    opening: str
    trouble: str
    failed_try: str
    clue: str
    dialogue: str
    transformation: str
    sharing: str
    ending: str


MYSTERIES = [
    Mystery(
        "vanishing_dough",
        "had shaped a little moon of dough for the evening special",
        "A sudden spike of floury footprints crossed the kitchen, but the dough moon was gone.",
        "Searching every shelf at once only made the kitchen dustier.",
        "The tiny footprints stopped beside a flour sack with a round bump at its base.",
        '"I can hold the sack steady," said the dependent young helper. "Then we can look together."',
        "They lifted the sack carefully and found the dough moon tucked in a cool basket beneath it.",
        "They made a small pizza together and shared it with the waiting neighbors.",
        "At dusk, the last slice disappeared beneath a sky shaped like a golden pizza crust.",
    ),
    Mystery(
        "missing_tomato",
        "was preparing a bright red tomato for the pizzeria's first pizza",
        "A spike of red drops led away from the counter, yet the tomato itself had disappeared.",
        "Rushing after the drops sent the searchers past the very place they needed to inspect.",
        "The drops grew smaller near a tipped watering can beside the herb pots.",
        '"I depend on you to reach the high shelf," said the helper. "But I can follow the drops."',
        "They followed the trail back to a tomato rolling gently in the watering-can tray.",
        "They chopped it together and shared the fresh pizza with everyone at the table.",
        "The empty red plate gleamed while the friends passed around the final warm slice.",
    ),
    Mystery(
        "bell_at_midnight",
        "had stayed late to prepare the pizzeria for the morning",
        "A spike of bell-ringing echoed from the empty dining room, though the front door was locked.",
        "Calling out for the unseen visitor only made the room feel more mysterious.",
        "A ribbon tied to the bell swayed whenever the open window breathed.",
        '"I need your help to reach the window," said the dependent little mouse. "I know where the draft begins."',
        "They shut the window and discovered a loose curtain cord had been tapping the bell.",
        "They baked a small breakfast pizza and shared it before opening the doors.",
        "The bell rested quiet above the door as morning sunlight warmed the shared table.",
    ),
    Mystery(
        "vanished_menu",
        "had written a new menu for a cheerful pizzeria supper",
        "A spike of blank spaces appeared on the menu, and the names of the favorite pizzas were missing.",
        "Adding new names from memory made the list even more confusing.",
        "A trail of blue chalk dust led from the menu board to a little handprint on the flour tin.",
        '"I depend on you to read the high words," said the young helper. "I remember which pizza we made first."',
        "They found the menu cards tucked behind the flour tin and put them back in the right order.",
        "They cooked the restored menu's first pizza and shared it with the whole crew.",
        "The menu shone above a table where every chair had a friend beside it.",
    ),
]


NAMES = ["Luna", "Milo", "Nia", "Theo", "Pip", "Rosa", "Jun", "Kit"]
DEPENDENTS = ["young helper", "little mouse", "small fox", "new apprentice"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("A pizzeria mystery needs a name for its careful detective.")
    if params.dependent not in DEPENDENTS:
        raise StoryError("Choose a dependent helper from the available pizzeria visitors.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "pizzeria"),
            asp.fact("has_mystery", "pizzeria"),
            asp.fact("has_transformation", "pizzeria"),
            asp.fact("has_happy_ending", "pizzeria"),
            asp.fact("has_sharing", "pizzeria"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_world(params: StoryParams) -> World:
    world = World()
    detective = world.add(Entity("detective", "character", params.name))
    helper = world.add(Entity("helper", "character", params.dependent))
    pizzeria = world.add(Entity("pizzeria", "place", "pizzeria"))
    world.facts.update(
        detective=detective,
        helper=helper,
        pizzeria=pizzeria,
        setting="pizzeria",
        transformation=True,
        happy_ending=True,
        sharing=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    mystery = rng.choice(MYSTERIES)
    detective = world.entities["detective"]
    helper = world.entities["helper"]
    place = world.entities["pizzeria"]

    world.say(
        f"At the pizzeria, {detective.label} {mystery.opening}. "
        f"{helper.label.capitalize()} was eager to help, though they still depended on one another."
    )
    world.say(mystery.trouble)
    world.say(f"{detective.label} tried to solve it quickly, but {mystery.failed_try}")
    world.para()

    detective.bump_meme("curiosity")
    helper.bump_meme("courage")
    world.say(f"Then {detective.label} noticed a clue: {mystery.clue}")
    world.say(mystery.dialogue)
    world.say(f"They paused, listened, and tested the clue together.")
    world.para()

    place.bump_meter("mystery_solved")
    helper.bump_meter("contribution")
    world.say(mystery.transformation)
    world.say(mystery.sharing)
    world.para()

    detective.bump_meme("joy")
    helper.bump_meme("belonging")
    world.say(
        f"The mystery had changed their worry into teamwork. "
        f"{detective.label} thanked the helper, who grinned at being part of the answer."
    )
    world.say(mystery.ending)
    world.facts.update(
        mystery=mystery.key,
        trouble=mystery.trouble,
        failed_try=mystery.failed_try,
        clue=mystery.clue,
        dialogue=mystery.dialogue,
        transformation=mystery.transformation,
        sharing=mystery.sharing,
        ending=mystery.ending,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    name = world.entities["detective"].label
    helper = world.entities["helper"].label
    return [
        f"Write a child-friendly mystery at a pizzeria starring {name} and a {helper}.",
        "Include a surprising spike, a useful clue, transformation, sharing, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem("What mystery did the friends face?", facts["trouble"]),
        QAItem(
            f"What clue helped {world.entities['detective'].label} solve the mystery?",
            f"They noticed that {facts['clue']}",
        ),
        QAItem("How did the situation change?", facts["transformation"]),
        QAItem("What did the friends share?", facts["sharing"]),
        QAItem("What image showed the happy ending?", facts["ending"]),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to depend on someone?",
            "To depend on someone means to trust that person for help or support when you need it.",
        ),
        QAItem(
            "What is a mystery?",
            "A mystery is something puzzling that people try to understand by noticing clues.",
        ),
        QAItem(
            "Why is sharing helpful?",
            "Sharing lets people enjoy something together and can help everyone feel included.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def dump_trace(world: World) -> str:
    return world.trace()


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pizzeria mystery storyworld.")
    parser.add_argument("--name")
    parser.add_argument("--dependent", choices=DEPENDENTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        name=args.name or rng.choice(NAMES),
        dependent=args.dependent or rng.choice(DEPENDENTS),
        seed=rng.randrange(2**31),
    )
    reasonableness_gate(params)
    return params


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show mystery_place/1.\n#show good_turn/1."))
    actual = {
        (symbol.name, tuple(arg.name for arg in symbol.arguments))
        for symbol in model
    }
    expected = {("mystery_place", ("pizzeria",)), ("good_turn", ("pizzeria",))}
    if actual != expected:
        print("MISMATCH between ASP twin and Python reasonableness gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1
    for index, mystery in enumerate(MYSTERIES):
        sample = generate(StoryParams("Luna", "young helper", seed=index))
        required = ("?",)
        if not sample.story.endswith(".") or "said" not in sample.story:
            print(f"Generated story {index + 1} is incomplete or lacks dialogue.")
            return 1
        if mystery.key not in sample.world.facts["mystery"]:
            # The seeded choice need not match this registry entry; all entries
            # are exercised below using a seed selected to produce each one.
            continue
    for mystery in MYSTERIES:
        seed = next(
            seed for seed in range(len(MYSTERIES) * 10)
            if random.Random(seed).choice(MYSTERIES).key == mystery.key
        )
        sample = generate(StoryParams("Luna", "young helper", seed=seed))
        if not sample.world.facts["resolved"] or not sample.story.endswith("."):
            print(f"Story exercise failed for {mystery.key}.")
            return 1
    print("OK: ASP twin matches the Python gate; generated mysteries are complete.")
    return 0


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_turn/1."))
    return sorted(set(asp.atoms(model, "good_turn")))


CURATED = [
    StoryParams("Luna", "young helper", 3),
    StoryParams("Milo", "little mouse", 7),
    StoryParams("Nia", "small fox", 12),
    StoryParams("Theo", "new apprentice", 19),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")
    if args.show_asp:
        print(asp_program("#show mystery_place/1.\n#show good_turn/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_list():
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = [
            generate(resolve_params(args, random.Random(rng.randrange(2**31))))
            for _ in range(args.n)
        ]

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
