#!/usr/bin/env python3
"""A gentle folk tale about a moustache, a hidden dimension, and brave friendship."""

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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Tomas"
    setting: str = "the village of Bellroot"
    dimension: str = "the Velvet Dimension"
    fave: str = "strawberry buns"
    moustache: str = "a silver moustache"
    scenario: str = "bridge"
    variant: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass(frozen=True)
class Scenario:
    key: str
    trouble: str
    clue: str
    fear: str
    brave_action: str
    exchange: str
    consequence: str
    ending: str


SCENARIOS = (
    Scenario(
        "bridge",
        "the silver moustache blew across the border into the Velvet Dimension",
        "a tiny red thread on the moustache pointed toward a safe stepping stone",
        "cross the humming gap alone",
        "asked Tomas to hold the lantern while Luna tied a ribbon from stone to stone",
        "“My knees are trembling,” Luna said. “Then we shall make a path together,” said Tomas.",
        "the ribbon path led them safely to the moustache",
        "The silver moustache curled proudly above Luna’s lip, and the ribbon bridge shone between the two dimensions.",
    ),
    Scenario(
        "echo",
        "a boastful echo trapped Luna’s favorite strawberry buns in a crystal cave",
        "the echo repeated every honest word but swallowed every boast",
        "shout louder until the cave cracked",
        "spoke a small truthful sentence and listened for the echo’s answer",
        "“I am afraid,” Luna called. “That is a brave truth,” Tomas answered.",
        "the cave opened when Luna named her fear instead of hiding it",
        "The buns came home warm, and the cave kept only a gentle echo of Luna’s brave truth.",
    ),
    Scenario(
        "dragon",
        "a sleepy paper dragon guarded the only door back to the village",
        "the dragon’s tail wagged whenever someone offered kindness",
        "grab the door and run before the dragon woke",
        "offered the dragon her fave bun and asked permission to pass",
        "“What if it is hungry?” Luna whispered. “We can be careful and kind,” said Tomas.",
        "the dragon accepted the bun, curled aside, and opened the door",
        "The paper dragon became the village’s new doorkeeper, with crumbs on its friendly nose.",
    ),
    Scenario(
        "clock",
        "the dimension’s backward clock made everyone forget why they had entered",
        "the moustache held one warm memory of home",
        "pretend to understand and wander farther",
        "touched the moustache, remembered Bellroot, and led Tomas toward the golden exit",
        "“I remember the bakery bell,” Luna said. “Then home is still calling,” said Tomas.",
        "their shared memory restored the clock’s hands",
        "The clock ticked forward, and the bakery bell rang just as Luna and Tomas stepped home.",
    ),
)

NAMES = ("Luna", "Mara", "Pip", "Nell")
HELPERS = ("Tomas", "Brin", "Odo", "Mira")
SETTINGS = ("the village of Bellroot", "the mossy village", "the hill town of Candlewick")
DIMENSIONS = ("the Velvet Dimension", "the Lantern Dimension", "the Blueberry Dimension")
FAVES = ("strawberry buns", "honey cakes", "plum jam")
MOUSTACHES = ("a silver moustache", "a curly gold moustache", "a soft blue moustache")


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity("hero", "person", params.name, {"bravery": 0.45, "safety": 0.5}, {"curiosity": 0.8}))
    helper = world.add(Entity("helper", "person", params.helper, {"care": 0.9}, {"trust": 0.8}))
    world.add(Entity("moustache", "heirloom", params.moustache, {"shine": 0.8}, {"home": 1.0}, params.name))
    world.add(Entity("fave", "food", params.fave, {"warmth": 0.7}, {"comfort": 0.9}, params.name))
    world.add(Entity("lantern", "tool", "a moon lantern", {"light": 0.8}, {"hope": 0.8}, params.helper))
    world.facts.update(hero=hero.id, helper=helper.id, home=params.setting, dimension=params.dimension)
    return world


def simulate(world: World) -> World:
    p = world.params
    scenario = next(item for item in SCENARIOS if item.key == p.scenario)
    hero = world.entities["hero"]

    world.say(f"In {p.setting}, where chimneys leaned together like old friends, {p.name} wore {p.moustache}.")
    world.say(f"Everyone knew that {p.moustache} was not merely a moustache. It was a compass to {p.dimension}, and it always smelled faintly of {p.fave}.")
    world.say(f"One market morning, {scenario.trouble}.")
    world.para()
    world.say(f"{p.name} followed the silver shimmer to the threshold. There she noticed that {scenario.clue}.")
    world.say(f"For a moment, {scenario.fear} seemed easier than admitting she needed help.")
    world.say(scenario.exchange)
    world.para()
    world.say(f"Together, {p.name} and {p.helper} {scenario.brave_action}.")
    world.say(f"They moved slowly, watched one another, and let the clue guide each step.")
    world.say(f"Because bravery was joined with care, {scenario.consequence}.")
    world.say(scenario.ending)
    world.say(f"That evening, the people of {p.setting} gathered around the oven. {p.name} shared {p.fave} and told them that bravery did not mean having no fear; it meant choosing a wise step while fear was still nearby.")

    hero.meters["bravery"] = 0.95
    hero.meters["safety"] = 0.95
    hero.memes["trust"] = 1.0
    world.fired.update({"noticed_clue", "asked_for_help", "brave_choice", "returned_home"})
    world.facts.update(
        scenario=p.scenario,
        trouble=scenario.trouble,
        clue=scenario.clue,
        rejected_fear=scenario.fear,
        brave_action=scenario.brave_action,
        consequence=scenario.consequence,
        ending=scenario.ending,
        used_helper=True,
        returned_home=True,
    )
    return world


def validate(params: StoryParams) -> None:
    if params.scenario not in {item.key for item in SCENARIOS}:
        raise StoryError(f"unknown scenario: {params.scenario}")
    if not params.name.strip() or not params.helper.strip():
        raise StoryError("a hero and helper must have names")
    if params.name == params.helper:
        raise StoryError("the hero and helper must be different people")
    if not params.moustache.strip():
        raise StoryError("the story needs a moustache")
    if not params.dimension.strip():
        raise StoryError("the story needs a dimension")
    if not params.fave.strip():
        raise StoryError("the story needs a favorite thing")


def generation_prompts(world: World) -> list[str]:
    p = world.params
    scenario = next(item for item in SCENARIOS if item.key == p.scenario)
    return [
        f"Write a child-friendly folk tale about {p.name}, {p.moustache}, and {p.dimension}.",
        f"Tell a story in which {p.name}'s bravery helps recover {p.fave}; the clue is {scenario.clue}.",
        "Include a brief dialogue between the hero and helper and end with a concrete image showing what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    scenario = next(item for item in SCENARIOS if item.key == p.scenario)
    return [
        QAItem(
            f"What went wrong for {p.name}?",
            f"{scenario.trouble.capitalize()}. The trouble carried {p.name} toward {p.dimension}.",
        ),
        QAItem(
            "What clue did the hero notice?",
            f"{p.name} noticed that {scenario.clue}. That clue helped guide the next safe choice.",
        ),
        QAItem(
            "How did the helper change the outcome?",
            f"{p.helper} helped {p.name} act carefully. Together they {scenario.brave_action}.",
        ),
        QAItem(
            "Why was the fearful shortcut rejected?",
            f"It was not wise to {scenario.fear}. The story shows that bravery works best with care and attention.",
        ),
        QAItem(
            "What proves the problem was solved?",
            f"{scenario.consequence.capitalize()} {scenario.ending}",
        ),
        QAItem(
            "What did the folk tale teach?",
            "Bravery does not require a person to feel no fear; it means taking a thoughtful step and accepting help when help is needed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a moustache?",
            "A moustache is hair that grows above a person’s upper lip.",
        ),
        QAItem(
            "What does dimension mean in this tale?",
            "A dimension is a separate imagined world or realm reached through the story’s magical boundary.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing a careful or helpful action even when something feels frightening.",
        ),
        QAItem(
            "Why can asking for help be brave?",
            "Asking for help can be brave because it honestly names a difficulty and lets people work together toward a safer solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = """
brave(X) :- hero(X), noticed_clue(X), asked_for_help(X), brave_choice(X).
safe_return(X) :- brave(X), returned_home(X).
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    name = (params or StoryParams()).name.lower().replace("-", "_").replace(" ", "_")
    return "\n".join(
        [
            asp.fact("hero", name),
            asp.fact("noticed_clue", name),
            asp.fact("asked_for_help", name),
            asp.fact("brave_choice", name),
            asp.fact("returned_home", name),
        ]
    )


def asp_program(show: str, params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show safe_return/1."))
    found = asp.atoms(symbols, "safe_return")
    if found:
        print("OK: ASP twin confirms careful bravery and return.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk tale storyworld about a moustache and a magical dimension.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--dimension", choices=DIMENSIONS)
    parser.add_argument("--fave", choices=FAVES)
    parser.add_argument("--moustache", choices=MOUSTACHES)
    parser.add_argument("--scenario", choices=tuple(item.key for item in SCENARIOS))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
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
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        setting=args.setting or rng.choice(SETTINGS),
        dimension=args.dimension or rng.choice(DIMENSIONS),
        fave=args.fave or rng.choice(FAVES),
        moustache=args.moustache or rng.choice(MOUSTACHES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        variant=rng.randrange(1, 2**31),
    )


def generate(params: StoryParams) -> StorySample:
    validate(params)
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print(f"\n--- trace ---\nfacts: {sample.world.facts}")
        print(f"fired: {sorted(sample.world.fired)}")
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave/1.\n#show safe_return/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(
                StoryParams(
                    seed=base_seed,
                    name="Luna",
                    helper="Tomas",
                    setting="the village of Bellroot",
                    dimension="the Velvet Dimension",
                    fave="strawberry buns",
                    moustache="a silver moustache",
                    scenario=scenario.key,
                    variant=index + 1,
                )
            )
            for index, scenario in enumerate(SCENARIOS)
        ]
    else:
        samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)]

    if args.asp:
        import asp

        for sample in samples:
            model = asp.one_model(asp_program("#show safe_return/1.", sample.params))
            if not asp.atoms(model, "safe_return"):
                raise StoryError("ASP twin rejected a generated brave return")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
