#!/usr/bin/env python3
"""
A standalone storyworld for a Tall Tale about paste, a brow, and gin
in a reading nook.

The world models a boastful child, a careful librarian, a paste pot, a
storybook brow, and a bottle of gin-shaped ink cleaner that belongs to an
adult. Repeated warnings create the tension, a daring mistake makes the
paste spread, and a calm repair gives the tale its moral value.
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
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sticky": 0.0, "mess": 0.0, "clean": 0.0, "high": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "patience": 0.0, "trust": 0.0}


@dataclass
class Setting:
    name: str
    affords: set[str]


@dataclass(frozen=True)
class Tale:
    title: str
    task: str
    warning: str
    accident: str
    clue: str
    repair: str
    ending: str
    moral: str


@dataclass
class StoryParams:
    setting: str
    hero_type: str
    helper_type: str
    name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


SETTINGS = {
    "reading_nook": Setting("the reading nook", {"read", "paste_craft", "clean"}),
}

HERO_TYPES = ["rabbit", "fox", "squirrel", "bear"]
HELPER_TYPES = ["librarian", "badger", "owl", "mouse"]

NAMES = {
    "rabbit": ["Luna", "Pip", "Mara"],
    "fox": ["Luna", "Finn", "Tess"],
    "squirrel": ["Luna", "Suki", "Jax"],
    "bear": ["Luna", "Benny", "Milo"],
    "librarian": ["Nora", "Mabel", "Iris"],
    "badger": ["Bruno", "Bram", "Otis"],
    "owl": ["Olive", "Orla", "Rue"],
    "mouse": ["Mina", "Moss", "Poppy"],
}

TALES = [
    Tale(
        "The Paste That Climbed the Bookshelf",
        "make a bright label for the nook's tallest story shelf",
        "Use one dab of paste, Luna. One dab is plenty.",
        "Luna slapped down a whole spoonful, and the label leaped from the table to the shelf like a white pancake",
        "three sticky fingerprints climbed upward while the paste pot stayed open below",
        "closed the pot, softened the paste with a damp cloth, and pressed the label flat from the center outward",
        "The label shone straight on the tallest shelf, where even the dust seemed to stand at attention",
        "A small measure used wisely can reach farther than a giant boast",
    ),
    Tale(
        "The Brow of the Book Dragon",
        "repair the painted brow above the nook's friendly book dragon",
        "Touch the brow gently, Luna. Paint and paste are not wrestling ropes.",
        "Luna tugged at the loose brow, and paste from yesterday's craft crawled across the dragon's forehead",
        "the old paste was crusted at one edge, while the fresh paste was shining at the other",
        "lifted the dry crust, used a tiny fresh dab, and held the brow still until it settled",
        "The dragon's brow curved proudly again, and its painted eyes looked ready for a hundred bedtime tales",
        "Gentle hands protect old treasures better than mighty hands",
    ),
    Tale(
        "The Gin Bottle Nobody Should Touch",
        "clean a reading tray before the evening story circle",
        "That bottle is gin for grown-ups, not a cleaner for children. Ask before using it.",
        "Luna reached toward the gin bottle, thinking its clear shine could conquer every smudge",
        "the bottle wore an adult's red warning tag, while the tray had only a little paste dust",
        "left the gin alone, called the helper, and cleaned the tray with warm water and a safe cloth",
        "The tray gleamed beneath the lamp, and the gin bottle remained sealed on its high cabinet",
        "Knowing what not to touch is part of knowing how to help",
    ),
    Tale(
        "The Brow That Became a Banner",
        "paste a tiny paper brow above Luna's favorite character",
        "One small strip, Luna. Repeating the same mistake will make a bigger mess.",
        "Luna pasted one strip, then another, then another, until the brow drooped like a banner",
        "each extra strip made the paper heavier, and the first strip had already been holding",
        "removed the loose strips, dried the page, and used one narrow strip beneath the brow",
        "The character wore one neat brow instead of a pastey curtain, and the page turned smoothly",
        "When a good action works, repeating it without thought can undo the good",
    ),
]


ASP_RULES = r"""
valid_setting(S) :- setting(S), affords(S,read), affords(S,paste_craft), affords(S,clean).
safe_tool(paste) :- tool(paste), child_safe(paste).
safe_tool(cloth) :- tool(cloth), child_safe(cloth).
unsafe_tool(gin) :- tool(gin), adult_only(gin).
reasonable(S) :- valid_setting(S), safe_tool(paste), safe_tool(cloth), unsafe_tool(gin).
"""


def apply_paste(world: World, target: Entity, amount: float) -> None:
    if amount <= 0:
        raise StoryError("Paste must be used in a positive amount.")
    target.meters["sticky"] += amount
    target.meters["mess"] += max(0.0, amount - 1.0)


def repeat_paste(world: World, target: Entity, times: int) -> None:
    if times < 1:
        raise StoryError("A repetition count must be at least one.")
    for _ in range(times):
        apply_paste(world, target, 1.0)


def careful_repair(world: World, target: Entity) -> None:
    target.meters["sticky"] = 0.2
    target.meters["mess"] = 0.0
    target.meters["clean"] += 1.0
    target.memes["trust"] += 1.0


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"Unknown hero type: {params.hero_type}")
    if params.helper_type not in HELPER_TYPES:
        raise StoryError(f"Unknown helper type: {params.helper_type}")
    if params.name == params.helper_name:
        raise StoryError("The hero and helper need different names.")

    seed = params.seed if params.seed is not None else 41
    rng = random.Random(seed)
    tale = rng.choice(TALES)
    world = World(SETTINGS[params.setting])

    hero = world.add(Entity(params.name, "character", params.hero_type))
    helper = world.add(Entity(params.helper_name, "character", params.helper_type))
    paste = world.add(Entity("paste", type="paste", label="a pot of paste"))
    brow = world.add(Entity("brow", type="brow", label="a paper brow"))
    gin = world.add(Entity("gin", type="gin", label="a sealed bottle of gin"))
    cloth = world.add(Entity("cloth", type="cloth", label="a safe cleaning cloth"))

    hero.memes["pride"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["patience"] = 1.0
    helper.memes["trust"] = 1.0
    gin.meters["high"] = 1.0

    if "paste_craft" not in world.setting.affords:
        raise StoryError("The reading nook does not have a suitable place for paste craft.")
    if tale.title == "The Gin Bottle Nobody Should Touch":
        apply_paste(world, brow, 1.0)
        brow.meters["mess"] = 0.4
    else:
        apply_paste(world, brow, 2.0)
    repeat_paste(world, brow, 1)
    world.facts["tale"] = tale
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["paste"] = paste
    world.facts["brow"] = brow
    world.facts["gin"] = gin
    world.facts["cloth"] = cloth

    opening = (
        f"In {world.setting.name}, Luna the {params.hero_type} made a promise so enormous "
        f"that three bookmarks fluttered when she said it: she would {tale.task}."
    )
    world.say(opening)
    world.say(
        f"{params.helper_name} the {params.helper_type} pointed to the paste and repeated the caution. "
        f'"{tale.warning}"'
    )
    world.say(
        f'Luna puffed out her brow and answered, "I heard you the first time, and the second time, '
        f'and I will prove I can do it bigger than anyone."'
    )
    world.para()

    world.say(f"Then {tale.accident}.")
    world.say(f"{tale.clue}.")
    world.say(
        f"{params.helper_name} repeated the warning once more: "
        f'"Stop, look, and ask before you reach for anything unusual."'
    )
    world.say(
        f'Luna whispered, "I repeated the paste because the first dab worked. '
        f'But repeating a mistake only makes the mistake taller."'
    )
    world.para()

    world.say(f"Together they {tale.repair}.")
    careful_repair(world, brow)
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 0.4
    hero.memes["trust"] += 1.0
    helper.memes["patience"] += 1.0
    world.say(
        f"The gin stayed sealed and out of reach, while the safe cloth and the little paste pot "
        f"returned to their proper places."
    )
    world.say(f"{tale.ending}.")
    world.say(f"The moral value of the day was plain: {tale.moral}.")
    world.para()

    world.facts["safe"] = True
    world.facts["tale"] = tale
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    return [
        f"Write a Tall Tale set in a reading nook using paste, a brow, and gin, with the caution: {tale.warning}",
        f"Use repetition to show how a small mistake grows, then end with the moral value: {tale.moral}",
        f"Tell a child-friendly story about Luna learning what to touch and what to leave alone.",
    ]


def story_questions(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What did {hero.id} promise to do?",
            f"{hero.id} promised to {tale.task} in the reading nook.",
        ),
        QAItem(
            "What warning was repeated?",
            f'The warning was, "{tale.warning}" It was repeated because careful use mattered.',
        ),
        QAItem(
            "What caused the trouble?",
            f"The trouble began when {tale.accident}.",
        ),
        QAItem(
            f"How did {helper.id} help?",
            f"{helper.id} helped by noticing that {tale.clue} and by guiding the safe repair: {tale.repair}.",
        ),
        QAItem(
            "What happened to the gin?",
            "The gin stayed sealed and out of reach because it was an adult-only substance, not a child's cleaner.",
        ),
        QAItem(
            "What moral value did the story teach?",
            f"It taught this moral value: {tale.moral}.",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is paste used for?",
            "Paste is a sticky material used to attach paper or other light materials.",
        ),
        QAItem(
            "What is a brow?",
            "A brow is the ridge above an eye; in the story it is also a paper shape placed above a painted character's eye.",
        ),
        QAItem(
            "Why should children leave gin alone?",
            "Gin is an alcoholic drink for adults, so children should never handle or taste it. An adult should manage any bottle of gin.",
        ),
        QAItem(
            "Why can repetition be dangerous?",
            "Repeating a helpful action without checking the result can make a small problem larger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "reading_nook"),
        asp.fact("affords", "reading_nook", "read"),
        asp.fact("affords", "reading_nook", "paste_craft"),
        asp.fact("affords", "reading_nook", "clean"),
        asp.fact("tool", "paste"),
        asp.fact("tool", "cloth"),
        asp.fact("tool", "gin"),
        asp.fact("child_safe", "paste"),
        asp.fact("child_safe", "cloth"),
        asp.fact("adult_only", "gin"),
    ]
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: ASP did not find the reasonable reading-nook world.")
        return 1
    params = StoryParams("reading_nook", "rabbit", "librarian", "Luna", "Nora", 7)
    sample = generate(params)
    if "reading nook" not in sample.story or "gin" not in sample.story:
        print("MISMATCH: generated story failed the ASP-supported domain checks.")
        return 1
    print("OK: ASP gate matches Python expectations and generated story checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tall Tale world of paste, brow, and gin.")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--hero-type", choices=HERO_TYPES, default=None)
    parser.add_argument("--helper-type", choices=HELPER_TYPES, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--helper-name", default=None)
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
    setting = args.setting or "reading_nook"
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    name = args.name or "Luna"
    helper_name = args.helper_name or rng.choice(NAMES[helper_type])
    if name == helper_name:
        helper_name = next(n for n in NAMES[helper_type] if n != name)
    return StoryParams(setting, hero_type, helper_type, name, helper_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("reading_nook", "rabbit", "librarian", "Luna", "Nora", 1),
    StoryParams("reading_nook", "fox", "badger", "Luna", "Bram", 2),
    StoryParams("reading_nook", "squirrel", "owl", "Luna", "Olive", 3),
    StoryParams("reading_nook", "bear", "mouse", "Luna", "Mina", 4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP reasonable:", asp_valid())
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name}: {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
