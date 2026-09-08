#!/usr/bin/env python3
"""Luna and the Mystery of the Non-Tan Stone.

A small simulated Tall Tale about a child, a puzzling stone, and a promise
that its color will be explained by the world rather than by a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.meme(key) + amount


@dataclass(frozen=True)
class Setting:
    id: str
    name: str
    landmark: str
    clue: str


@dataclass(frozen=True)
class Mystery:
    id: str
    object_label: str
    true_color: str
    expected_color: str
    cause: str
    revealing_action: str
    ending_image: str


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0
        self.fired: set[str] = set()

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

    def record(
        self,
        kind: str,
        text: str,
        cause: str,
        result: str,
        actor: str = "Luna",
        target: str = "mystery",
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "hill": Setting(
        "hill",
        "the hill",
        "a wind-bent pine",
        "three round tracks pressed through the dust",
    ),
    "meadow": Setting(
        "meadow",
        "the meadow",
        "a blue fence",
        "a line of silver grass bent toward the creek",
    ),
    "ravine": Setting(
        "ravine",
        "the ravine",
        "a crooked bridge",
        "a bright thread of water under the stones",
    ),
}

MYSTERIES = {
    "stone": Mystery(
        "stone",
        "a small stone",
        "blue",
        "tan",
        "the stone was covered by a thin skin of dry clay",
        "Luna dipped the stone into the creek and rubbed it with her sleeve",
        "the clean blue stone shone beside the creek like a tiny piece of sky",
    ),
    "button": Mystery(
        "button",
        "a round button",
        "green",
        "tan",
        "the button was hidden beneath a cap of yellow dust",
        "Luna brushed the button with a soft grass stem",
        "the green button winked from the grass while the wind bowed around it",
    ),
    "shell": Mystery(
        "shell",
        "a little shell",
        "pink",
        "tan",
        "the shell was wrapped in a coat of brown mud",
        "Luna rinsed the shell in a puddle and turned it toward the sun",
        "the pink shell gleamed like a small sunrise in Luna's palm",
    ),
}

NAMES = ["Luna", "Milo", "Nia", "Toby", "Ada"]
HELPERS = ["Grandma", "Dad", "Aunt May", "Uncle Sol"]
MOODS = ["bold", "curious", "patient", "bright"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str = "Luna"
    helper: str = "Grandma"
    mood: str = "curious"
    seed: Optional[int] = None


KNOWLEDGE = {
    "stone": QAItem(
        "Why can a stone look different after it is washed?",
        "Water can remove dust or clay from a stone, revealing the color underneath.",
    ),
    "button": QAItem(
        "Why can brushing help reveal a button?",
        "Brushing can move loose dust away so the button's real color can be seen.",
    ),
    "shell": QAItem(
        "Why can rinsing change how a shell looks?",
        "Rinsing can wash away mud, allowing the shell's smoother color to shine.",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, mystery) for setting in SETTINGS for mystery in MYSTERIES]


def build_world(params: StoryParams) -> World:
    if (params.setting, params.mystery) not in valid_combos():
        raise StoryError("That setting and mystery do not form a supported story.")
    if params.name in {"mystery", "helper", "object", "clue"}:
        raise StoryError("The child's name collides with a world object.")

    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting, mystery)
    hero = world.add(Entity(params.name, "character", params.name))
    helper = world.add(Entity("helper", "character", params.helper))
    object_entity = world.add(Entity("object", "thing", mystery.object_label))
    clue = world.add(Entity("clue", "thing", setting.clue))
    world.facts.update(hero=hero, helper=helper, object=object_entity, clue=clue)
    hero.add_meme("curiosity")
    hero.add_meme(params.mood)
    return world


def opening(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.mystery
    setting = world.setting
    world.record(
        "arrive",
        (
            f"{hero.label} marched into {setting.name}, where {setting.landmark} "
            f"leaned so far that it seemed to be listening to the clouds. "
            f"Near the path, {hero.label} found {mystery.object_label}. "
            f"It looked {mystery.expected_color}, although {hero.label} felt sure "
            f"it had once been {mystery.true_color}. "
            f'"Grandma, this is non-{mystery.expected_color}!" {hero.label} cried. '
            f'"Then it is a mystery worth solving," {helper.label} said.'
        ),
        cause=(
            f"The {mystery.object_label} looked {mystery.expected_color}, "
            f"but Luna expected it to be {mystery.true_color}."
        ),
        result=f"{hero.label} decided to find out why the color seemed wrong.",
        actor=hero.id,
        target="object",
    )


def investigate(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.mystery
    setting = world.setting
    hero.add_meme("wonder")
    world.para()
    world.record(
        "clue",
        (
            f"{hero.label} inspected the ground and discovered {setting.clue}. "
            f"She thought, *If the stone is truly tan, why does it feel as if a "
            f"blue answer is hiding underneath?* "
            f'"Look closely," {helper.label} advised. '
            f'"A mystery leaves clues, even when it wears a dusty hat." '
            f"{hero.label} noticed a thin crust clinging to the {mystery.object_label}."
        ),
        cause=(
            f"The place held a clue, and the {mystery.object_label} had a thin "
            f"covering that could hide its color."
        ),
        result=f"{hero.label} learned that the strange color might be on the surface.",
        actor=hero.id,
        target="clue",
    )


def reveal(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.mystery
    hero.add_meter("attempts")
    hero.add_meme("patience")
    world.para()
    world.turn += 1
    world.record(
        "reveal",
        (
            f"{hero.label} {mystery.revealing_action}. "
            f"The covering slid away, and the {mystery.object_label} flashed "
            f"{mystery.true_color}. "
            f'"It was not really tan!" {hero.label} said. '
            f'"It was wearing tan," {helper.label} replied. '
            f"{hero.label} laughed so loudly that a bird flew backward for three "
            f"whole wingbeats."
        ),
        cause=mystery.cause.capitalize() + ".",
        result=(
            f"The {mystery.object_label} showed its true {mystery.true_color} color "
            f"after the covering was removed."
        ),
        actor=hero.id,
        target="object",
    )


def finish(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.mystery
    hero.add_meter("solved")
    hero.add_meme("joy")
    world.para()
    world.record(
        "solve",
        (
            f"{hero.label} placed the clean {mystery.object_label} beside the path "
            f"so everyone could see the answer. "
            f'"Mystery solved," {hero.label} announced. '
            f'"And what will you call it?" {helper.label} asked. '
            f'"The Non-Tan Wonder," {hero.label} said, because a proper Tall Tale '
            f"needs a name big enough to shake the hills. {mystery.ending_image.capitalize()}."
        ),
        cause=(
            f"{hero.label} removed the covering and checked the "
            f"{mystery.object_label} instead of trusting its first appearance."
        ),
        result=f"The mystery was solved when the {mystery.object_label} revealed its true color.",
        actor=hero.id,
        target="object",
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    opening(world, params)
    investigate(world)
    reveal(world)
    finish(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mystery = world.mystery
    return [
        (
            f"Write a Tall Tale for young children about {hero.label} solving a "
            f"mystery involving {mystery.object_label}, the words non and tan, "
            f"an inner thought, and a surprising reveal."
        ),
        (
            f"Tell a story in which a child thinks a {mystery.object_label} is tan "
            f"but discovers why it is non-tan after following a clue and speaking "
            f"with a helper."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrive": "What seemed strange about the object?",
        "clue": "What clue helped the child investigate?",
        "reveal": "What caused the object's surprising color?",
        "solve": "How was the mystery solved?",
    }
    return [
        QAItem(question=questions[event.kind], answer=f"{event.cause} {event.result}")
        for event in world.history
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE[world.mystery.id]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id}: {entity.kind} {entity.label}; "
            f"meters={meters}; memes={memes}"
        )
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(M) :- object(M).
has_clue(S) :- setting(S).
reasonable(S, M) :- setting(S), mystery(M), has_clue(S).
solved(S, M) :- reasonable(S, M), revealed(M).
revealed(stone).
revealed(button).
revealed(shell).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for mystery in MYSTERIES:
        lines.append(asp.fact("object", mystery))
        lines.append(asp.fact("mystery", mystery))
        lines.append(asp.fact("true_color", mystery, MYSTERIES[mystery].true_color))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/2.") -> str:
    facts = asp_facts()
    return f"{facts}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "reasonable"))
    expected = set(valid_combos())
    if found != expected:
        print("MISMATCH: ASP and Python mystery choices differ.")
        return 1
    for setting, mystery in expected:
        sample = generate(
            StoryParams(setting=setting, mystery=mystery, name="Luna", helper="Grandma")
        )
        check_sample(sample)
    print(f"OK: {len(expected)} ASP/Python combinations and story checks.")
    return 0


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world is not None
    assert world.get("hero").meter("attempts") == 1
    assert world.get("hero").meter("solved") == 1
    assert world.mystery.true_color in sample.story
    assert "non-" in sample.story
    assert all(event.text in sample.story for event in world.history)
    assert all(len(item.answer.split()) >= 8 for item in sample.story_qa)
    assert not any(mark in sample.story for mark in ("{", "}", "__", "meters=", "memes="))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Tall Tale about Luna and a non-tan mystery."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--mood", choices=MOODS)
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
    settings = [args.setting] if args.setting else sorted(SETTINGS)
    mysteries = [args.mystery] if args.mystery else sorted(MYSTERIES)
    if not settings or not mysteries:
        raise StoryError("No valid setting or mystery was selected.")
    return StoryParams(
        setting=rng.choice(settings),
        mystery=rng.choice(mysteries),
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        mood=args.mood or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    check_sample(sample)
    return sample


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
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show reasonable/2."))
        for setting, mystery in sorted(set(asp.atoms(model, "reasonable"))):
            print(f"{setting}: {mystery}")
        return

    if args.all:
        params_list = [
            StoryParams(setting=setting, mystery=mystery, name="Luna", helper="Grandma")
            for setting, mystery in valid_combos()
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        params_list = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.setting}: {sample.params.mystery}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
