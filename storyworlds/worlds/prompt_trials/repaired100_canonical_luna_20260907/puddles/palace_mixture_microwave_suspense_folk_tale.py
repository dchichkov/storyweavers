#!/usr/bin/env python3
"""The Palace Microwave.

A small folk tale of a palace kitchen, a bubbling mixture, and a careful child
who learns that suspense is a reason to slow down, not a reason to panic.
"""

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Ingredient:
    id: str
    label: str
    flavor: str
    safe: bool = True


@dataclass
class StoryParams:
    palace: str = "the Moonlit Palace"
    ingredient: str = "honey"
    helper: str = "grandmother"
    hero: str = "Luna"
    problem: str = "mixture"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
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

    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.history.append(Event(kind, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


INGREDIENTS = {
    "honey": Ingredient("honey", "a spoonful of honey", "sweet"),
    "berries": Ingredient("berries", "three red berries", "bright and tart"),
    "oats": Ingredient("oats", "a little bowl of oats", "warm and nutty"),
}

HELPERS = {
    "grandmother": ("Grandmother", "grandmother", "she", "her"),
    "uncle": ("Uncle Rowan", "uncle", "he", "his"),
    "cook": ("the palace cook", "cook", "she", "her"),
}

PALACES = {
    "moonlit": "the Moonlit Palace",
    "bell": "the Palace of Seven Bells",
    "glass": "the Glass Palace",
}

ASP_RULES = r"""
valid_ingredient(I) :- ingredient(I), safe(I).
can_mix(P, I) :- palace(P), valid_ingredient(I).
needs_pause(P, I) :- can_mix(P, I).
resolved(P, I) :- needs_pause(P, I), checked(P), stirred(P), heated(P), rested(P).
#show can_mix/2.
#show resolved/2.
"""


def valid_story(params: StoryParams) -> bool:
    return (
        params.palace in PALACES.values()
        and params.ingredient in INGREDIENTS
        and params.helper in HELPERS
    )


def make_world(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("The palace, ingredient, or helper is not in the story registry.")

    world = World(params)
    hero = world.add(Entity(params.hero, "character", params.hero))
    helper_id, helper_label, helper_pronoun, helper_pos = HELPERS[params.helper]
    helper = world.add(Entity("helper", "character", helper_label))
    bowl = world.add(Entity("bowl", "thing", "silver bowl"))
    microwave = world.add(Entity("microwave", "thing", "the old microwave"))
    mixture = world.add(Entity("mixture", "thing", "the mixture"))
    palace = world.add(Entity("palace", "place", params.palace))
    world.facts.update(
        hero=hero,
        helper=helper,
        bowl=bowl,
        microwave=microwave,
        mixture=mixture,
        palace=palace,
        helper_id=helper_id,
        helper_pronoun=helper_pronoun,
        helper_pos=helper_pos,
        ingredient=INGREDIENTS[params.ingredient],
        checked=False,
        stirred=False,
        heated=False,
        rested=False,
        resolved=False,
    )

    world.record(
        "arrival",
        f"In {params.palace}, {params.hero} found a silver bowl beside an old microwave. "
        f"The palace cook had left {INGREDIENTS[params.ingredient].label} for a warm evening treat, "
        f"and the moonlight made the kitchen shine like a secret.",
        "The palace kitchen held a bowl, a microwave, and an ingredient waiting to become a treat.",
        "Luna found a chance to make something kind for the palace guests.",
    )

    world.para()
    world.facts["mixture"].meters["ingredients"] = 1
    world.facts["mixture"].memes["hope"] = 1
    world.record(
        "mix",
        f'"I will make the mixture," {params.hero} whispered. {helper_label.capitalize()} looked over. '
        f'"A warm treat is welcome, but the microwave must be watched." '
        f'{params.hero} stirred the {INGREDIENTS[params.ingredient].flavor} mixture until it shone.',
        "Luna wanted to help, but the mixture needed heat and care.",
        "The ingredients became one mixture, ready for the microwave.",
    )

    world.para()
    world.facts["mixture"].meters["danger"] = 1
    world.facts["mixture"].memes["worry"] = 1
    world.record(
        "suspense",
        f'{params.hero} placed the bowl near the microwave. Then the microwave gave a low hum, '
        f'and one bright spark blinked behind its door. "Should I press the button?" {params.hero} asked. '
        f'"First check the bowl and the time," said {helper_label}. The quiet kitchen seemed to hold its breath.',
        "The strange spark made the heating step uncertain, so rushing could spoil the mixture.",
        "Luna learned that suspense was a signal to pause and inspect.",
    )

    world.para()
    world.facts["checked"] = True
    world.facts["stirred"] = True
    world.facts["mixture"].meters["danger"] = 0
    world.facts["mixture"].memes["trust"] = 1
    world.record(
        "check",
        f'{params.hero} checked the bowl for cracks and read the small timer. '
        f'"The bowl is sound, and five gentle minutes will do," {params.hero} said. '
        f'{helper_label.capitalize()} nodded. "Then use the microwave only while we stay beside it."',
        "Checking the bowl and choosing a short time removed the dangerous guess.",
        "Luna and the helper made a careful plan before heating.",
    )

    world.para()
    world.facts["heated"] = True
    world.facts["mixture"].meters["warmth"] = 1
    world.facts["mixture"].memes["hope"] = 2
    world.record(
        "heat",
        f'The microwave hummed, and the palace clock counted five slow chimes. '
        f'{params.hero} watched through the glass while {helper_label} stood close. '
        f'The mixture rose, trembled, and settled. "There is the answer," said {helper_label}. '
        f'"It is warm, not wild."',
        "A short watched heating time warmed the mixture without letting it boil over.",
        "The microwave finished safely because Luna and the helper stayed near it.",
    )

    world.para()
    world.facts["rested"] = True
    world.facts["resolved"] = True
    world.facts["mixture"].meters["warmth"] = 0.5
    world.facts["mixture"].memes["joy"] = 1
    world.record(
        "share",
        f'{params.hero} let the mixture rest before touching the bowl. Then {params.hero} carried small cups '
        f'to the palace hall. The guests tasted the sweet treat, and the old microwave rested in silence. '
        f'"A careful hand makes a brave feast," said {helper_label}. Luna smiled as the palace bells rang.',
        "Resting the hot mixture made it safe to carry and share.",
        "The palace guests enjoyed the treat, and Luna became known for patient courage.",
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "mix": "What did Luna make in the palace kitchen?",
        "suspense": "Why did Luna pause before using the microwave?",
        "check": "What did Luna and the helper check?",
        "heat": "How was the mixture heated safely?",
        "share": "What happened after the mixture rested?",
    }
    return [
        QAItem(question=questions[event.kind], answer=f"{event.cause} {event.result}")
        for event in world.history
        if event.kind in questions
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should someone stay nearby when using a microwave?",
            "A person should stay nearby to notice spills, sparks, or other trouble and stop the microwave safely.",
        ),
        QAItem(
            "Why should hot food rest before it is carried?",
            "Hot food should rest because the bowl and mixture may burn someone before they cool enough to handle.",
        ),
        QAItem(
            "What is a mixture?",
            "A mixture is made when two or more ingredients are stirred together without becoming separate piles.",
        ),
    ]


def prompts(world: World) -> list[str]:
    return [
        f"Tell a suspenseful folk tale about {world.params.hero} making a mixture in {world.params.palace} with a microwave.",
        f"Write a gentle folk tale in which a child pauses, checks the bowl, and safely shares a warm treat.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: {entity.kind} {entity.label}")
        if meters:
            lines.append(f"    meters={meters}")
        if memes:
            lines.append(f"    memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("palace", "palace"),
        asp.fact("ingredient", "honey"),
        asp.fact("ingredient", "berries"),
        asp.fact("ingredient", "oats"),
        asp.fact("safe", "honey"),
        asp.fact("safe", "berries"),
        asp.fact("safe", "oats"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_check() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "can_mix"))
    expected = {("palace", key) for key in INGREDIENTS}
    if found != expected:
        print("MISMATCH: ASP and Python ingredient choices differ.")
        return 1
    sample = generate(StoryParams())
    if not sample.world or not sample.world.facts["resolved"]:
        print("MISMATCH: generated story did not resolve.")
        return 1
    print("OK: ASP/Python parity and story resolution verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A suspenseful folk tale about a palace microwave.")
    parser.add_argument("--palace", choices=list(PALACES), default=None)
    parser.add_argument("--ingredient", choices=list(INGREDIENTS), default=None)
    parser.add_argument("--helper", choices=list(HELPERS), default=None)
    parser.add_argument("--hero", default=None)
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
    palace_key = args.palace or rng.choice(list(PALACES))
    ingredient = args.ingredient or rng.choice(list(INGREDIENTS))
    helper = args.helper or rng.choice(list(HELPERS))
    hero = args.hero or rng.choice(["Luna", "Mira", "Nell", "Tara", "Pip"])
    return StoryParams(
        palace=PALACES[palace_key],
        ingredient=ingredient,
        helper=helper,
        hero=hero,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_check())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        for palace, ingredient in sorted(asp.atoms(model, "can_mix")):
            print(f"{palace}: {ingredient}")
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    if args.all:
        for palace_key in PALACES:
            for ingredient in INGREDIENTS:
                params = StoryParams(
                    palace=PALACES[palace_key],
                    ingredient=ingredient,
                    helper="grandmother",
                    hero="Luna",
                )
                samples.append(generate(params))
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = None if args.seed is None else args.seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### tale {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
