#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py
============================================================================

A standalone storyworld for a tall-tale quest about assembling an enormous sweet
for Madam Marigold at the town fair. The child hero must travel out, gather one
giant fruit, bring it back, and assemble it on a sturdy base with a sticky
binder strong enough for the fair wind.

The world model prefers a small set of plausible, high-quality stories over wide
coverage. A story is only valid when:
- the chosen base can truly hold the giant fruit, and
- the chosen binder is sticky enough for the wind at the fair.

That way the quest has a real problem, a grounded turn, and a happy ending that
proves what changed: the towering dessert stands, the crowd cheers, and Madam
Marigold smiles.

Run it
------
    python storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py
    python storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py --fruit moonberry
    python storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py --base pie_tin
    python storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py --all
    python storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py --qa --json
    python storyworlds/worlds/gpt-5.4/assemble_sweet_madam_quest_happy_ending_tall.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we need to add the
# storyworlds/ package directory itself to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "madam"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    path: str
    fair_name: str
    wind: int
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    patch: str
    weight: int
    height: int
    sweetness: int
    carry_text: str
    color_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Base:
    id: str
    label: str
    phrase: str
    capacity: int
    width: int
    build_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Binder:
    id: str
    label: str
    phrase: str
    stickiness: int
    pour_text: str
    shine_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def base_margin(base: Base, fruit: Fruit) -> int:
    return base.capacity - fruit.weight


def initial_wobble(setting: Setting, base: Base, fruit: Fruit) -> int:
    wobble = max(0, setting.wind + fruit.height - base.width)
    wobble += max(0, fruit.weight - base.capacity)
    return wobble


def stabilized(setting: Setting, fruit: Fruit, base: Base, binder: Binder) -> bool:
    if base.capacity < fruit.weight:
        return False
    wobble = initial_wobble(setting, base, fruit)
    return binder.stickiness >= wobble


def valid_story(setting: Setting, fruit: Fruit, base: Base, binder: Binder) -> bool:
    return stabilized(setting, fruit, base, binder)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for fruit_id, fruit in FRUITS.items():
            for base_id, base in BASES.items():
                for binder_id, binder in BINDERS.items():
                    if valid_story(setting, fruit, base, binder):
                        combos.append((setting_id, fruit_id, base_id, binder_id))
    return sorted(combos)


def explain_rejection(setting: Setting, fruit: Fruit, base: Base, binder: Binder) -> str:
    if base.capacity < fruit.weight:
        return (
            f"(No story: {base.phrase} cannot truly hold {fruit.phrase}. "
            f"The fruit is too heavy for that base, so the tall dessert would slump before the quest could end happily.)"
        )
    wobble = initial_wobble(setting, base, fruit)
    if binder.stickiness < wobble:
        return (
            f"(No story: at {setting.fair_name}, the wind and height would make the dessert wobble too much for {binder.phrase}. "
            f"Pick a stickier binder or a steadier base.)"
        )
    return "(No story: those choices do not make a stable tall dessert.)"


def predict_wobble(world: World, fruit: Fruit, base: Base, binder: Binder) -> dict:
    sim = world.copy()
    dessert = sim.get("dessert")
    dessert.meters["tower_height"] += fruit.height
    dessert.meters["wobble"] += float(initial_wobble(sim.setting, base, fruit))
    dessert.meters["stickiness"] += binder.stickiness
    propagate(sim, narrate=False)
    return {
        "wobble": dessert.meters["wobble"],
        "standing": dessert.meters["standing"] >= THRESHOLD,
    }


def _r_stick(world: World) -> list[str]:
    dessert = world.get("dessert")
    if dessert.meters["wobble"] < THRESHOLD or dessert.meters["stickiness"] < THRESHOLD:
        return []
    sig = ("stick",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    settle = min(dessert.meters["wobble"], dessert.meters["stickiness"])
    dessert.meters["wobble"] -= settle
    return []


def _r_stand(world: World) -> list[str]:
    dessert = world.get("dessert")
    if dessert.meters["assembled"] < THRESHOLD:
        return []
    if dessert.meters["wobble"] >= THRESHOLD:
        return []
    sig = ("stand",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dessert.meters["standing"] += 1
    world.get("hero").memes["pride"] += 1
    world.get("madam").memes["relief"] += 1
    world.get("crowd").memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="stick", tag="physical", apply=_r_stick),
    Rule(name="stand", tag="physical", apply=_r_stand),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
            else:
                before = len(world.fired)
                rule.apply(world)
                if len(world.fired) != before:
                    changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def introduce(world: World, hero: Entity, madam: Entity, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"On the morning of {setting.fair_name}, {hero.id} stood in {setting.place} under {setting.sky}. "
        f"Nothing in that town was ever small; even the shadows looked tall enough to need ladders."
    )
    world.say(
        f"At the bakery door waited Madam Marigold, flour on her sleeves and a plan in her head. "
        f'"{hero.id}," said the madam, "today we must assemble the tallest sweet in three counties, '
        f'or the fair table will look lonely."'
    )


def assign_quest(world: World, hero: Entity, fruit: Fruit, setting: Setting) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"She pointed past {setting.path} toward {fruit.patch}, where {fruit.label}s grew so large that birds rested on them like porch swings."
    )
    world.say(
        f'"Bring me {fruit.phrase}," Madam Marigold said, "and hurry back before the wind at the fair starts bragging again."'
    )


def journey(world: World, hero: Entity, fruit: Fruit, setting: Setting) -> None:
    hero.meters["distance"] += 1
    hero.meters["fatigue"] += 1
    hero.memes["grit"] += 1
    world.say(
        f"So off {hero.pronoun()} went along {setting.path}. {fruit.color_text.capitalize()} shone ahead, and each step seemed long enough to count as two."
    )
    world.say(
        f"When {hero.id} reached {fruit.patch}, {fruit.carry_text}."
    )


def return_with_fruit(world: World, hero: Entity, fruit: Fruit) -> None:
    hero.meters["carried_weight"] += fruit.weight
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} rolled and tugged that prize all the way back to town, cheeks pink and shoes dusty, while children ran behind chanting, "
        f'"Sweet for Madam! Sweet for Madam!"'
    )


def build_base(world: World, madam: Entity, base: Base) -> None:
    world.say(
        f"Back at the bakery tent, Madam Marigold had already {base.build_text}. "
        f"It waited in the middle of the table like a little round stage."
    )


def stack_fruit(world: World, hero: Entity, fruit: Fruit, base: Base) -> None:
    dessert = world.get("dessert")
    dessert.meters["assembled"] += 1
    dessert.meters["tower_height"] += fruit.height
    dessert.meters["sweetness"] += fruit.sweetness
    dessert.meters["wobble"] += float(initial_wobble(world.setting, base, fruit))
    hero.memes["worry"] += 1
    world.say(
        f"Together they heaved {fruit.phrase} onto {base.phrase}. "
        f"For a glorious blink, the dessert reached so high it looked ready to knock on a cloud."
    )
    if dessert.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Then the tower gave a slow, squeaky wobble. The fair flags fluttered, the table shivered, and even the spoons seemed to hold their breath."
        )


def choose_binder(world: World, hero: Entity, madam: Entity, fruit: Fruit, base: Base, binder: Binder) -> None:
    pred = predict_wobble(world, fruit, base, binder)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.say(
        f'"Quick now," cried Madam Marigold, "bring {binder.phrase}!"'
    )
    world.say(
        f"{hero.id} seized the bowl and {binder.pour_text}. {binder.shine_text.capitalize()}."
    )


def settle(world: World, binder: Binder) -> None:
    dessert = world.get("dessert")
    dessert.meters["stickiness"] += binder.stickiness
    propagate(world, narrate=False)
    if dessert.meters["standing"] >= THRESHOLD:
        world.say(
            "The wobble slowed, thought about causing trouble, and then changed its mind."
        )


def celebration(world: World, hero: Entity, madam: Entity, fruit: Fruit, binder: Binder, setting: Setting) -> None:
    world.say(
        f"Soon the great sweet stood steady and proud, glossy with {binder.label}, taller than the mayor's hat rack and twice as handsome."
    )
    world.say(
        f'Madam Marigold laughed and clapped floury hands. "A quest well done!" she said. '
        f'"You brought the fruit, helped assemble the tower, and saved the fair table all at once."'
    )
    world.say(
        f"When they cut the first slice, it tasted so {fruit.label}-sweet that the whole crowd smiled with both cheeks. "
        f"By sunset, the plates were clean, the table was empty, and {hero.id} walked home feeling ten feet taller inside."
    )


def tell(setting: Setting, fruit: Fruit, base: Base, binder: Binder,
         hero_name: str = "Tess", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "brave") -> World:
    if not valid_story(setting, fruit, base, binder):
        raise StoryError(explain_rejection(setting, fruit, base, binder))

    world = World(setting=setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["little", trait],
    ))
    madam = world.add(Entity(
        id="Madam Marigold",
        kind="character",
        type="madam",
        label="madam",
        role="madam",
        traits=["kind", "busy", "clever"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    dessert = world.add(Entity(
        id="dessert",
        type="dessert",
        label="towering sweet",
        phrase="the towering fair sweet",
        role="dessert",
    ))
    crowd = world.add(Entity(
        id="crowd",
        type="crowd",
        label="the crowd",
        role="crowd",
    ))

    introduce(world, hero, madam, setting)
    assign_quest(world, hero, fruit, setting)

    world.para()
    journey(world, hero, fruit, setting)
    return_with_fruit(world, hero, fruit)

    world.para()
    build_base(world, madam, base)
    stack_fruit(world, hero, fruit, base)
    choose_binder(world, hero, madam, fruit, base, binder)
    settle(world, binder)

    world.para()
    celebration(world, hero, madam, fruit, binder, setting)

    world.facts.update(
        hero=hero,
        madam=madam,
        parent=parent,
        crowd=crowd,
        dessert=dessert,
        setting=setting,
        fruit=fruit,
        base=base,
        binder=binder,
        stable=dessert.meters["standing"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the long meadow town",
        path="the fence road",
        fair_name="Lantern Fair",
        wind=2,
        sky="a blue sky stretched thin as a tablecloth",
        tags={"fair", "wind"},
    ),
    "hollow": Setting(
        id="hollow",
        place="the apple-cart hollow",
        path="the mill lane",
        fair_name="Honey Banner Fair",
        wind=1,
        sky="a gold sky polished bright as a penny",
        tags={"fair", "wind"},
    ),
    "ridge": Setting(
        id="ridge",
        place="the high ridge village",
        path="the switchback path",
        fair_name="Ribbon Hill Fair",
        wind=3,
        sky="a windy sky with clouds trotting fast",
        tags={"fair", "wind"},
    ),
}

FRUITS = {
    "moonberry": Fruit(
        id="moonberry",
        label="moonberry",
        phrase="a moonberry the size of a wheelbarrow",
        patch="the moonberry patch beyond the creek",
        weight=2,
        height=2,
        sweetness=3,
        carry_text="it took both hands, one shoulder, and a promise not to give up to budge the giant berry loose",
        color_text="purple light",
        tags={"berry", "sweet"},
    ),
    "sunpeach": Fruit(
        id="sunpeach",
        label="sunpeach",
        phrase="a sunpeach round as a porch table",
        patch="the sunny orchard by the mill",
        weight=3,
        height=2,
        sweetness=3,
        carry_text="the peach was so plump and warm that holding it felt like carrying a sleepy little sun",
        color_text="golden light",
        tags={"peach", "sweet"},
    ),
    "plumstar": Fruit(
        id="plumstar",
        label="plumstar",
        phrase="a plumstar wider than a washbasin",
        patch="the plum rows near the red barn",
        weight=1,
        height=1,
        sweetness=2,
        carry_text="one good shove sent the shining fruit rolling after like a tame purple comet",
        color_text="violet light",
        tags={"plum", "sweet"},
    ),
}

BASES = {
    "wagon_crust": Base(
        id="wagon_crust",
        label="wagon-crust",
        phrase="a wagon-crust baked in a brass pan",
        capacity=3,
        width=3,
        build_text="rolled out a wagon-crust baked in a brass pan, broad enough to land a chicken on",
        tags={"crust", "sturdy"},
    ),
    "barrel_tart": Base(
        id="barrel_tart",
        label="barrel-lid tart",
        phrase="a barrel-lid tart shell",
        capacity=2,
        width=2,
        build_text="set down a barrel-lid tart shell, crisp and brown around the rim",
        tags={"crust", "sturdy"},
    ),
    "pie_tin": Base(
        id="pie_tin",
        label="deep pie tin",
        phrase="a deep silver pie tin",
        capacity=1,
        width=1,
        build_text="polished a deep silver pie tin until it flashed like a small moon",
        tags={"crust"},
    ),
}

BINDERS = {
    "honey_rope": Binder(
        id="honey_rope",
        label="honey rope",
        phrase="the honey rope",
        stickiness=4,
        pour_text="looped thick ribbons of honey rope around the towering fruit",
        shine_text="the golden glaze caught the light and held fast",
        tags={"honey", "sticky"},
    ),
    "jam_lacquer": Binder(
        id="jam_lacquer",
        label="jam lacquer",
        phrase="the jam lacquer",
        stickiness=2,
        pour_text="brushed bright jam lacquer over every seam and edge",
        shine_text="the red shine gleamed like a tiny sunset",
        tags={"jam", "sticky"},
    ),
    "cream_cloud": Binder(
        id="cream_cloud",
        label="cream cloud",
        phrase="the cream cloud",
        stickiness=1,
        pour_text="piled soft cream cloud all around the fruit in sweet white drifts",
        shine_text="the cream looked lovely, but it was a gentle sort of lovely",
        tags={"cream", "sweet"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    fruit: str
    base: str
    binder: str
    hero_name: str
    hero_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="meadow",
        fruit="moonberry",
        base="wagon_crust",
        binder="honey_rope",
        hero_name="Tess",
        hero_type="girl",
        parent_type="mother",
        trait="brave",
    ),
    StoryParams(
        setting="hollow",
        fruit="sunpeach",
        base="wagon_crust",
        binder="jam_lacquer",
        hero_name="Eli",
        hero_type="boy",
        parent_type="father",
        trait="steady",
    ),
    StoryParams(
        setting="ridge",
        fruit="plumstar",
        base="barrel_tart",
        binder="honey_rope",
        hero_name="Mara",
        hero_type="girl",
        parent_type="mother",
        trait="cheerful",
    ),
    StoryParams(
        setting="hollow",
        fruit="plumstar",
        base="pie_tin",
        binder="jam_lacquer",
        hero_name="Ben",
        hero_type="boy",
        parent_type="father",
        trait="nimble",
    ),
    StoryParams(
        setting="meadow",
        fruit="sunpeach",
        base="wagon_crust",
        binder="honey_rope",
        hero_name="Nora",
        hero_type="girl",
        parent_type="mother",
        trait="helpful",
    ),
]

GIRL_NAMES = ["Tess", "Mara", "Nora", "Lila", "June", "Ada", "Wren", "Molly"]
BOY_NAMES = ["Eli", "Ben", "Otis", "Finn", "Jude", "Levi", "Cal", "Milo"]
TRAITS = ["brave", "steady", "cheerful", "helpful", "quick", "nimble"]


KNOWLEDGE = {
    "berry": [(
        "What is a berry?",
        "A berry is a small juicy fruit with soft skin and sweet juice inside. In stories, berries are often used for pies and jam."
    )],
    "peach": [(
        "What is a peach?",
        "A peach is a round fruit with soft skin and sweet flesh. It has a hard pit in the middle."
    )],
    "plum": [(
        "What is a plum?",
        "A plum is a smooth fruit that can be sweet and juicy. Some plums are purple, and they have a pit inside."
    )],
    "honey": [(
        "What is honey?",
        "Honey is a thick sweet food made by bees. It is sticky, so it can cling to things."
    )],
    "jam": [(
        "What is jam?",
        "Jam is fruit cooked with sugar until it becomes thick and spreadable. It tastes sweet and can be quite sticky."
    )],
    "cream": [(
        "What is cream?",
        "Cream is the rich part of milk. Whipped cream is soft and tasty, but it is not as sticky as honey or jam."
    )],
    "fair": [(
        "What is a fair?",
        "A fair is a happy gathering with games, food, and people coming together to celebrate. Town fairs often have tables full of treats."
    )],
    "quest": [(
        "What is a quest?",
        "A quest is a trip with a clear goal, like going out to find or bring back something important. In stories, the hero usually changes while trying to finish it."
    )],
    "sturdy": [(
        "What does sturdy mean?",
        "Sturdy means strong and steady, not easy to bend or tip over. A sturdy base can hold something heavy on top."
    )],
}
KNOWLEDGE_ORDER = ["fair", "quest", "berry", "peach", "plum", "honey", "jam", "cream", "sturdy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, setting, fruit, base, binder = (
        f["hero"], f["setting"], f["fruit"], f["base"], f["binder"]
    )
    return [
        'Write a tall-tale story for a 3-to-5-year-old that includes the words "assemble", "sweet", and "madam".',
        f"Tell a quest story where {hero.id} helps Madam Marigold bring back {fruit.phrase} and assemble a towering dessert for {setting.fair_name}.",
        f"Write a happy-ending fair story in a tall-tale style where a child uses {base.label} and {binder.label} to steady an enormous sweet."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, madam, setting, fruit, base, binder, dessert = (
        f["hero"], f["madam"], f["setting"], f["fruit"], f["base"], f["binder"], f["dessert"]
    )
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child helper, and Madam Marigold, the baker at {setting.fair_name}. Together they work to make one enormous sweet for the town."
        ),
        (
            "What was the quest?",
            f"The quest was to bring back {fruit.phrase} from {fruit.patch} so they could assemble a towering dessert. The fair needed that giant fruit to make the table feel grand enough."
        ),
        (
            f"Why did the dessert wobble?",
            f"It wobbled because the dessert was very tall and the fair wind pushed at it. When they first set {fruit.phrase} on {base.phrase}, the whole tower shook before it was sealed in place."
        ),
        (
            f"How did {hero.id} help Madam Marigold?",
            f"{hero.id} went on the quest, brought back the giant fruit, and then helped assemble the dessert. When the tower started to wobble, {hero.pronoun()} quickly used {binder.label} to steady it."
        ),
    ]
    if dessert.meters["standing"] >= THRESHOLD:
        qa.append((
            "How did the story end?",
            f"It ended happily with the towering sweet standing strong on the fair table. Madam Marigold laughed, the crowd cheered, and the first slice tasted wonderfully sweet."
        ))
        qa.append((
            f"Why was {binder.label} important?",
            f"{binder.label.capitalize()} was important because it held the tall dessert together when the wind made it wobble. Without that sticky finish, the tower would not have stood so proudly."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | {"quest", "sturdy"}
    tags |= set(f["fruit"].tags) | set(f["base"].tags) | set(f["binder"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:16} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F, B, K) :- setting(S), fruit(F), base(B), binder(K),
                     capacity(B, C), weight(F, W), C >= W,
                     wind(S, Wi), height(F, H), width(B, Bw),
                     wobble(S, F, B, V), stickiness(K, St), St >= V.

wobble(S, F, B, V) :- wind(S, Wi), height(F, H), width(B, Bw),
                      capacity(B, C), weight(F, W),
                      over_a(S, F, B, A), over_b(S, F, B, Bm), V = A + Bm.
over_a(S, F, B, Wi + H - Bw) :- wind(S, Wi), height(F, H), width(B, Bw), Wi + H > Bw.
over_a(S, F, B, 0) :- wind(S, Wi), height(F, H), width(B, Bw), Wi + H <= Bw.
over_b(S, F, B, W - C) :- weight(F, W), capacity(B, C), W > C.
over_b(S, F, B, 0) :- weight(F, W), capacity(B, C), W <= C.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("wind", sid, s.wind))
    for fid, f in FRUITS.items():
        lines.append(asp.fact("fruit", fid))
        lines.append(asp.fact("weight", fid, f.weight))
        lines.append(asp.fact("height", fid, f.height))
    for bid, b in BASES.items():
        lines.append(asp.fact("base", bid))
        lines.append(asp.fact("capacity", bid, b.capacity))
        lines.append(asp.fact("width", bid, b.width))
    for kid, k in BINDERS.items():
        lines.append(asp.fact("binder", kid))
        lines.append(asp.fact("stickiness", kid, k.stickiness))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "Madam Marigold" not in sample.story:
            raise StoryError("smoke test story was empty or missing the madam.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(7)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 7
        sample = generate(params)
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("generated sample did not produce QA.")
        print("OK: random generation + QA succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale quest storyworld: a child helps Madam Marigold assemble a giant sweet for the fair."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--binder", choices=BINDERS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.fruit and args.base and args.binder:
        setting = SETTINGS[args.setting]
        fruit = FRUITS[args.fruit]
        base = BASES[args.base]
        binder = BINDERS[args.binder]
        if not valid_story(setting, fruit, base, binder):
            raise StoryError(explain_rejection(setting, fruit, base, binder))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.fruit is None or combo[1] == args.fruit)
        and (args.base is None or combo[2] == args.base)
        and (args.binder is None or combo[3] == args.binder)
    ]
    if not combos:
        if args.setting and args.fruit and args.base and args.binder:
            raise StoryError(explain_rejection(
                SETTINGS[args.setting], FRUITS[args.fruit], BASES[args.base], BINDERS[args.binder]
            ))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, fruit_id, base_id, binder_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        fruit=fruit_id,
        base=base_id,
        binder=binder_id,
        hero_name=hero_name,
        hero_type=hero_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.fruit not in FRUITS:
        raise StoryError(f"(Unknown fruit: {params.fruit})")
    if params.base not in BASES:
        raise StoryError(f"(Unknown base: {params.base})")
    if params.binder not in BINDERS:
        raise StoryError(f"(Unknown binder: {params.binder})")

    world = tell(
        setting=SETTINGS[params.setting],
        fruit=FRUITS[params.fruit],
        base=BASES[params.base],
        binder=BINDERS[params.binder],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        parent_type=params.parent_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, fruit, base, binder) combos:\n")
        for setting, fruit, base, binder in combos:
            print(f"  {setting:8} {fruit:10} {base:12} {binder}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.fruit} on {p.base} with {p.binder} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
