#!/usr/bin/env python3
"""
A heartwarming masquerade storyworld about learning to believe in a hidden
kindness.

The simulated world tracks a child, a costume, a village celebration, and the
emotional change that follows when appearances hide a generous act.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
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
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Masquerade:
    id: str
    name: str
    mask: str
    costume: str
    hidden_identity: str
    visible_deed: str
    clue: str
    moral_value: str
    ending_image: str


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


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


SETTING = Setting(
    place="the lantern-lit town square",
    affords={"masquerade", "music", "kindness", "believing"},
)

MASQUERADES = {
    "silver_moon": Masquerade(
        id="silver_moon",
        name="the Silver Moon Masquerade",
        mask="a silver moon mask",
        costume="a cloak sewn with tiny stars",
        hidden_identity="the quiet baker",
        visible_deed="carrying warm buns and blankets to the lonely families",
        clue="flour dust glittered on the masked guest's gloves",
        moral_value="Do not judge a heart by a costume; kindness can wear any face.",
        ending_image="silver masks resting beside warm bread while the whole square glowed gently",
    ),
    "garden_lights": Masquerade(
        id="garden_lights",
        name="the Garden Lights Masquerade",
        mask="a green leaf mask",
        costume="a coat covered with stitched flowers",
        hidden_identity="the old gardener",
        visible_deed="quietly repairing the lanterns along the dark garden path",
        clue="a tiny thread of green yarn clung to the broken lantern hook",
        moral_value="Believe in goodness before deciding what another person means.",
        ending_image="lanterns shining through the garden while flower masks hung from the same friendly tree",
    ),
    "rainbow_ribbons": Masquerade(
        id="rainbow_ribbons",
        name="the Rainbow Ribbon Masquerade",
        mask="a bright rainbow mask",
        costume="a patchwork cape made from old festival ribbons",
        hidden_identity="the shy school caretaker",
        visible_deed="making a dry corner for children caught in the sudden rain",
        clue="the careful knots matched the ribbons from the school curtain",
        moral_value="A small act of care is worth more than a grand appearance.",
        ending_image="rainbow ribbons fluttering above a dry bench where everyone could sit together",
    ),
}

NAMES = ["Luna", "Mira", "Tavi", "Niko", "Sela", "Pia"]
TRAITS = ["hopeful", "curious", "thoughtful", "gentle", "brave"]
DIALOGUES = [
    (
        "That masked guest looks mysterious.",
        "Mysterious does not mean unkind. What have we actually seen?",
    ),
    (
        "Should we follow the stranger?",
        "We can watch carefully and help without making a hurtful guess.",
    ),
    (
        "I am not sure whom to believe.",
        "Believe the kindness you can test, and leave room for a good surprise.",
    ),
    (
        "What if the costume is hiding trouble?",
        "Then we will stay together. But we should not call a heart bad before we know it.",
    ),
]

SCENARIO_IDS = list(MASQUERADES)


@dataclass
class StoryParams:
    masquerade: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming masquerade tale about learning to believe."
    )
    parser.add_argument("--masquerade", choices=MASQUERADES)
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
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
    masquerade = args.masquerade or rng.choice(SCENARIO_IDS)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(masquerade, name, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.masquerade not in MASQUERADES:
        raise StoryError("The chosen masquerade is not part of this storyworld.")
    if not params.name.strip():
        raise StoryError("A masquerade story needs a named child observer.")
    if params.trait not in TRAITS:
        raise StoryError("The child's trait must be one of the registered traits.")


def tell(world: World, params: StoryParams) -> World:
    masquerade = MASQUERADES[params.masquerade]
    seed_value = params.seed if params.seed is not None else sum(
        (index + 1) * ord(char)
        for index, char in enumerate(f"{params.masquerade}|{params.name}|{params.trait}")
    )
    dialogue = DIALOGUES[seed_value % len(DIALOGUES)]
    opening_style = seed_value % 3

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="child",
            label=params.name,
            meters={"attention": 1.0},
            memes={"wonder": 1.0, "doubt": 1.0},
        )
    )
    masked_guest = world.add(
        Entity(
            id="masked_guest",
            kind="character",
            type="guest",
            label=masquerade.hidden_identity,
            meters={"helping": 0.0},
            memes={"kindness": 1.0},
        )
    )
    mask = world.add(
        Entity(
            id="mask",
            kind="object",
            type="mask",
            label=masquerade.mask,
            owner="masked_guest",
            meters={"mystery": 1.0},
        )
    )
    square = world.add(
        Entity(
            id="square",
            kind="place",
            type="celebration",
            label="the lantern-lit town square",
            meters={"warmth": 0.0},
        )
    )

    if opening_style == 0:
        world.say(
            f"On the evening of {masquerade.name}, {params.name}, a {params.trait} child, entered the lantern-lit town square."
        )
    elif opening_style == 1:
        world.say(
            f"The town square shimmered with music and ribbons when {params.name}, a {params.trait} child, arrived for {masquerade.name}."
        )
    else:
        world.say(
            f"Once each year, the town held {masquerade.name}, and {params.name}, a {params.trait} child, loved the bright costumes and hidden faces."
        )

    world.say(
        f"Every guest wore a disguise, but one visitor stood out in {masquerade.costume} and {masquerade.mask}."
    )
    world.para()

    world.say(
        f"{params.name} noticed the masked guest {masquerade.visible_deed}, yet the stranger moved so quietly that no one knew who was beneath the mask."
    )
    world.say(
        f"Some children whispered that the guest might be playing a trick, and {params.name} felt doubt tug at the wonder in their chest."
    )
    world.say(
        f'"{dialogue[0]}" {params.name} said.'
    )
    world.say(
        f"A friend named Remy answered, \"{dialogue[1]}\""
    )
    world.say(
        f"Together they watched from a respectful distance instead of chasing the guest away."
    )
    add_meter(child, "attention", 1.0)
    add_meme(child, "doubt", -1.0)

    world.para()
    world.say(
        f"Then the masked guest stumbled, and {params.name} saw {masquerade.clue}."
    )
    world.say(
        f"The clue connected the beautiful disguise to the quiet work, but {params.name} still needed more than a guess."
    )
    world.say(
        f"Rather than pull off the mask, {params.name} offered a hand and asked, \"May we help?\""
    )
    world.say(
        f"The masked guest nodded, and together they finished the caring task before the music began again."
    )
    add_meter(masked_guest, "helping", 1.0)
    add_meter(child, "helping", 1.0)
    add_meter(square, "warmth", 1.0)
    add_meme(child, "trust", 1.0)

    world.para()
    world.say(
        f"When the final drumbeat sounded, the guest removed the mask and revealed {masquerade.hidden_identity}."
    )
    world.say(
        f"{params.name} smiled, because the important truth had appeared before the face did: the guest had chosen to care."
    )
    world.say(
        f"The town praised the deed, not the disguise, and everyone repeated the moral value: {masquerade.moral_value}"
    )
    world.say(
        f"Afterward, {masquerade.ending_image}."
    )

    world.facts.update(
        child=child,
        masked_guest=masked_guest,
        mask=mask,
        square=square,
        masquerade=masquerade,
        dialogue=dialogue,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(World(SETTING), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    masquerade = world.facts["masquerade"]
    child = world.facts["child"]
    return [
        f"Write a heartwarming story about {child.id} at {masquerade.name}, using the words masquerade and believe.",
        f"Tell a gentle tale in which a child learns that {masquerade.moral_value}",
        f"Write a child-friendly masquerade story where kindness is discovered through a small clue rather than a hurried judgment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"]
    masquerade = facts["masquerade"]
    guest = facts["masked_guest"]
    return [
        QAItem(
            question=f"Where did {child.id} go?",
            answer=f"{child.id} went to {world.setting.place} for {masquerade.name}.",
        ),
        QAItem(
            question="Why did the masked guest seem mysterious?",
            answer=f"The guest wore {masquerade.mask} and {masquerade.costume}, so nobody knew at first who was underneath.",
        ),
        QAItem(
            question=f"What kind deed did {guest.label} do?",
            answer=f"{guest.label} was {masquerade.visible_deed}.",
        ),
        QAItem(
            question="What clue helped reveal the truth?",
            answer=f"The clue was that {masquerade.clue} It connected the costume with the helpful work.",
        ),
        QAItem(
            question=f"How did {child.id} respond to the mystery?",
            answer=f"{child.id} did not pull off the mask or make a cruel guess. Instead, {child.id} offered help and worked with the masked guest.",
        ),
        QAItem(
            question="What did the masquerade teach the children?",
            answer=f"It taught them that {masquerade.moral_value}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a masquerade?",
            answer="A masquerade is a celebration where people wear masks or costumes so their identities are hidden for a while.",
        ),
        QAItem(
            question="What does it mean to believe someone?",
            answer="To believe someone means to trust that what they say or show is truthful, while still using care and good judgment.",
        ),
        QAItem(
            question="Why can judging by appearances be unfair?",
            answer="Appearances show only part of a person, so judging too quickly can hide their intentions or kindness.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a guiding idea about how to treat others, such as kindness, honesty, courage, or fairness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Prompts =="]
    sections.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story QA ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== World QA ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(details)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(silver_moon).
valid(garden_lights).
valid(rainbow_ribbons).
moral_value(silver_moon, kindness).
moral_value(garden_lights, belief).
moral_value(rainbow_ribbons, care).
reasonable(X) :- valid(X), moral_value(X, _).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "town_square"),
            asp.fact("theme", "masquerade"),
            asp.fact("word", "believe"),
            *[
                asp.fact("masquerade", scenario.id)
                for scenario in MASQUERADES.values()
            ],
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str]]:
    return [(scenario_id,) for scenario_id in SCENARIO_IDS]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_values = set(valid_combos())
        asp_values = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if python_values != asp_values:
        print("MISMATCH")
        print(f"Python: {sorted(python_values)}")
        print(f"ASP: {sorted(asp_values)}")
        return 1
    for params in [
        StoryParams("silver_moon", "Luna", "hopeful"),
        StoryParams("garden_lights", "Mira", "thoughtful"),
        StoryParams("rainbow_ribbons", "Tavi", "gentle"),
    ]:
        sample = generate(params)
        if "masquerade" not in sample.story.lower() or "believe" not in (
            sample.story.lower() + " " + sample.world_qa[1].answer.lower()
        ):
            print("Generated story exercise failed.")
            return 1
    print(f"OK: ASP matches Python ({len(python_values)} masquerades), stories pass.")
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
    StoryParams("silver_moon", "Luna", "hopeful"),
    StoryParams("garden_lights", "Mira", "thoughtful"),
    StoryParams("rainbow_ribbons", "Tavi", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            current_seed = base_seed + index
            index += 1
            rng = random.Random(current_seed)
            try:
                params = resolve_params(args, rng)
                params.seed = current_seed
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.name}: {sample.params.masquerade}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
