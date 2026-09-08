#!/usr/bin/env python3
"""
A comic little magic world about a mower, an accidental transformation, and
the teamwork needed to put the yard right again.

Seed word: mower
Features: Transformation, Magic
Style: Comedy
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the sunny backyard",
    "the village green",
    "the school garden",
    "the park behind the bakery",
]
HERO_NAMES = ["Luna", "Milo", "Pip", "Nora", "Tess", "Bram"]
HELPER_NAMES = ["Aunt Bea", "Ollie", "Mara", "Jun", "Mr. Finch", "Zig"]
SPECIES = ["rabbit", "fox", "mouse", "badger", "goat", "hedgehog"]
MAGIC_COLORS = ["blue", "golden", "purple", "green"]
SILLY_FORMS = ["a tiny dragon", "a bouncing teapot", "a very round frog", "a squeaky wheelbarrow"]
SPELLS = [
    "Whirl, twirl, trim and chew!",
    "Grass be short and giggles too!",
    "Snip the weeds and spin around!",
    "Mower magic, make no frown!",
]
SOUNDS = [
    "brrr-brrr",
    "putt-putt-pop",
    "whizz-whizz",
    "chugga-chugga",
]


@dataclass
class Entity:
    id: str
    kind: str
    species: str
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"rabbit", "fox", "mouse", "badger", "goat", "hedgehog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str = "bright"


@dataclass
class Mood:
    comic: bool = True
    magical: bool = True
    repaired: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    spell_color: str
    silly_form: str
    spell: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mood: Mood) -> None:
        self.setting = setting
        self.mood = mood
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(line) for line in self.lines if line)


def replace_names(text: str, hero: str, helper: str) -> str:
    return (
        text.replace("the hero", hero)
        .replace("The hero", hero)
        .replace("the helper", helper)
        .replace("The helper", helper)
    )


def tell(params: StoryParams) -> World:
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")
    if params.hero_species == params.helper_species:
        raise StoryError("The hero and helper must be different species.")

    world = World(Setting(params.place), Mood())
    hero = world.add(Entity(params.hero_name, "character", params.hero_species))
    helper = world.add(Entity(params.helper_name, "character", params.helper_species))
    mower = world.add(
        Entity(
            "mower",
            "machine",
            "mower",
            label="the old red mower",
            owner=params.hero_name,
        )
    )
    yard = world.add(Entity("yard", "place", "yard", label=params.place))

    seed = params.seed
    if seed is None:
        seed = "|".join(
            [
                params.place,
                params.hero_name,
                params.hero_species,
                params.helper_name,
                params.helper_species,
                params.spell_color,
                params.silly_form,
                params.spell,
            ]
        )
    rng = random.Random(seed)
    sound = rng.choice(SOUNDS)
    extra_joke = rng.choice(
        [
            "A cabbage applauded by wobbling in a breeze.",
            "Even the scarecrow looked embarrassed, although nobody knew why.",
            "A robin tilted its head as if it had bought a ticket.",
            "The garden hose rolled away because it did not want to be involved.",
        ]
    )
    repair_tool = rng.choice(["a wooden spoon", "a watering can", "a broom", "a long ribbon"])

    hero.meters.update(steadiness=1.0, courage=1.0)
    helper.meters.update(observation=1.0, patience=1.0)
    mower.meters.update(fuel=1.0, blade_ready=1.0)
    hero.memes.update(pride=1.0, surprise=0.0)
    helper.memes.update(amusement=1.0, concern=0.0)

    world.say(
        f"On a bright morning at {params.place}, {hero.id}, a young {hero.species}, "
        f"promised to mow the grass before the picnic."
    )
    world.say(
        f"{helper.id}, a clever {helper.species}, held the mower handle while the old machine made a hopeful "
        f"{sound}."
    )
    world.say(
        f'"I know how to use it," said {hero.id}. "I watched three whole minutes of mowing yesterday."'
    )
    world.say(
        f'"That is almost an expert lesson," said {helper.id}, trying not to laugh.'
    )
    world.para()

    world.say(
        f"{hero.id} pulled the starter cord, and a spark of {params.spell_color} light hopped from the mower."
    )
    world.say(f"The mower rolled over a shiny button hidden in the grass, and {hero.id} read the tiny words aloud.")
    world.say(f'"{params.spell}"')
    world.say(
        f"With a pop, a puff, and one extremely surprised squeak, {hero.id} transformed into {params.silly_form}."
    )
    hero.meters["steadiness"] = 0.0
    hero.memes["surprise"] = 2.0
    world.say(
        f"{hero.id} tried to speak, but only made a sound like a spoon falling into soup."
    )
    world.say(extra_joke)
    world.para()

    world.say(
        f'"Do not panic," said {helper.id}. "Can you still point to the magic button?"'
    )
    world.say(
        f"{hero.id} bounced, rolled, or wobbled toward the mower and bumped the button twice."
    )
    world.say(
        f"{helper.id} noticed that the first transformation had started when the mower crossed a patch of clover, "
        f"so the clover was part of the magic."
    )
    world.say(
        f'"Then we need a careful plan," said {helper.id}. "I will hold the mower still, and you show me the safe path."'
    )
    world.say(
        f"Together they used {repair_tool} to lift the button from the grass without starting the mower."
    )
    world.say(
        f"{hero.id} guided the button back to the clover patch while {helper.id} repeated the spell backward, slowly and clearly."
    )
    world.say(
        f"The magic flashed {params.spell_color}, the mower sneezed, and {hero.id} changed back."
    )
    hero.meters["steadiness"] = 1.0
    hero.memes["surprise"] = 0.0
    helper.memes["concern"] = 0.0
    world.mood.repaired = True
    world.para()

    world.say(
        f'"Next time," said {hero.id}, brushing grass from {hero.pronoun("possessive")} clothes, '
        f'"I will read signs before saying them aloud."'
    )
    world.say(
        f'"Excellent," said {helper.id}. "And next time I will check the mower for enchanted buttons first."'
    )
    world.say(
        f"They moved the button into a locked shed, checked the mower together, and finished the yard at a sensible speed."
    )
    world.say(
        f"The grass stood neat and short, the picnic blanket stayed safely on the ground, and nobody became {params.silly_form} again."
    )
    world.say(
        f"At sunset, {hero.id} and {helper.id} shared lemonade while the mower rested quietly, pretending it had never sneezed."
    )

    mower.meters["magic_checked"] = 1.0
    mower.memes["embarrassment"] = 1.0
    yard.meters["grass_neat"] = 1.0
    yard.memes["safety"] = 1.0
    world.facts.update(
        hero=hero,
        helper=helper,
        mower=mower,
        yard=yard,
        repair_tool=repair_tool,
        sound=sound,
        extra_joke=extra_joke,
        spell=params.spell,
        spell_color=params.spell_color,
        silly_form=params.silly_form,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a funny child-friendly story about a mower in {world.setting.place}.",
        "Include a magical transformation caused by an accidentally spoken spell.",
        "Let two characters use clues, dialogue, and teamwork to reverse the transformation safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mower: Entity = world.facts["mower"]
    return [
        QAItem(
            question=f"What caused {hero.id}'s transformation?",
            answer=(
                f"{hero.id} read the mower's magical words aloud after a spark of "
                f"{world.facts['spell_color']} light jumped from the machine. The spell transformed "
                f"{hero.id} into {world.facts['silly_form']}."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} discover what was part of the magic?",
            answer=(
                f"{helper.id} noticed that the transformation began when the mower crossed a patch of clover. "
                f"That clue showed that the clover and the enchanted button mattered."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=(
                f"{helper.id} held the mower still while {hero.id} guided the button back to the clover patch. "
                f"They used {world.facts['repair_tool']} and repeated the spell backward until {hero.id} changed back."
            ),
        ),
        QAItem(
            question="What happened to the mower at the end?",
            answer=(
                f"{mower.label.capitalize()} was checked and the enchanted button was locked in a shed. "
                "The mower could rest safely while the finished grass looked neat."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=(
                f"{hero.id} learned to read signs before speaking strange words aloud and to ask for help "
                "when a surprising problem appears."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mower?",
            answer="A mower is a machine with moving blades used to cut grass shorter.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or shape into another.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an imaginary power that can make unusual things happen, such as a spell changing someone's form.",
        ),
        QAItem(
            question="Why should people check a mower before using it?",
            answer="People should check that a mower is safe, clear of strange objects, and ready before starting it.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.species}) "
            f"{' '.join(details)}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comedy storyworld about mower magic and a silly transformation."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero-name")
    parser.add_argument("--helper-name")
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
    place = args.place or rng.choice(PLACES)
    hero_species = rng.choice(SPECIES)
    helper_species = rng.choice([item for item in SPECIES if item != hero_species])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([item for item in HELPER_NAMES if item != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
        spell_color=rng.choice(MAGIC_COLORS),
        silly_form=rng.choice(SILLY_FORMS),
        spell=rng.choice(SPELLS),
    )


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


def asp_facts() -> str:
    return "\n".join(
        [
            "domain(mower_magic_comedy).",
            "object(mower).",
            "feature(transformation).",
            "feature(magic).",
            "feature(comedy).",
            "requires(mower, safety_check).",
            "resolved(transformation, teamwork).",
        ]
    )


ASP_RULES = r"""
valid_world :-
    domain(mower_magic_comedy),
    object(mower),
    feature(transformation),
    feature(magic),
    feature(comedy),
    requires(mower, safety_check),
    resolved(transformation, teamwork).
#show valid_world/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program("#show valid_world/0."))
    values = set(asp.atoms(model, "valid_world"))
    if values != {()}:
        print("MISMATCH:", values, "{()}")
        return 1

    params = StoryParams(
        place=PLACES[0],
        hero_name="Luna",
        hero_species="rabbit",
        helper_name="Ollie",
        helper_species="fox",
        spell_color="blue",
        silly_form="a tiny dragon",
        spell=SPELLS[0],
        seed=17,
    )
    sample = generate(params)
    required = ["mower", "transformed", "changed back", "teamwork"]
    lowered = sample.story.lower()
    missing = [word for word in required if word not in lowered]
    if missing:
        print("MISMATCH: generated story missing", missing)
        return 1

    print("OK: ASP facts and Python world agree; generated story exercised.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_world/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if len(samples) < args.n:
        raise StoryError("Could not generate the requested number of distinct stories.")

    if args.asp:
        try:
            import asp
        except ImportError as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        model = asp.one_model(asp_program("#show valid_world/0."))
        if set(asp.atoms(model, "valid_world")) != {()}:
            raise StoryError("ASP rejected the mower magic story world.")

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
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
