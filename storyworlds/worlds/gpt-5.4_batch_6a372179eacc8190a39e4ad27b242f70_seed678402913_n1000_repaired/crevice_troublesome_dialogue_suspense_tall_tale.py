#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py
=============================================================================

A standalone story world for a child-facing tall tale about a troublesome animal,
a scary crevice, and a rescue that works only when the chosen tool honestly fits
the job.

Seed requirements rebuilt as simulation
---------------------------------------
Words: crevice, troublesome
Features: Dialogue, Suspense
Style: Tall Tale

This world imagines a ranch-country tall tale: a bold child and a steady grown-up
must rescue a troublesome animal that has gotten stuck beside or inside a crevice.
The story leans into playful exaggeration -- boots thump like drums, the wind has
opinions, the gap in the ground looks wide enough to hide a moonbeam -- but the
core logic stays sensible.

Reasonableness constraint
-------------------------
Not every rescue tool can save every animal from every crevice. The world checks
the rescue physically:

* pull-tools (lasso, hook pole) need enough reach for the crevice depth and enough
  pull power for the animal's size
* bridge-tools (ladder bridge, plank bridge) need enough span for the crevice width
  and enough steadiness for the animal's size

Invalid explicit choices are refused with StoryError and explained clearly.

Run it
------
    python storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py
    python storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py --animal goat --crevice narrow --tool lasso
    python storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py --animal mule --crevice deep --tool plank
    python storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crevice_troublesome_dialogue_suspense_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
        }.get(self.type, self.type)


@dataclass
class Locale:
    id: str
    label: str
    opener: str
    sky: str
    close: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    size: int
    hoofed: bool
    voice: str
    trouble: str
    lure: str
    boast: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreviceCfg:
    id: str
    label: str
    width: int
    depth: int
    image: str
    edge: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    method: str
    reach: int
    power: int
    span: int
    steady: int
    action: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


LOCALES = {
    "mesa": Locale(
        id="mesa",
        label="the red mesa",
        opener="Out on the red mesa, where jackrabbits looked small as buttons and the wind bragged louder than a brass band,",
        sky="The sky sat high and bright, and every sound skipped for miles.",
        close="By sundown the mesa looked peaceful again, as if it had only been practicing its frown.",
        tags={"mesa", "ranch"},
    ),
    "prairie": Locale(
        id="prairie",
        label="the long prairie",
        opener="On the long prairie, where grass could whisper a whole story before breakfast,",
        sky="Cloud shadows rolled over the ground like slow gray wagons.",
        close="At evening the prairie stretched quiet and golden, wide enough to hold one more good promise.",
        tags={"prairie", "ranch"},
    ),
    "canyon": Locale(
        id="canyon",
        label="the canyon trail",
        opener="Along the canyon trail, where even pebbles liked to sound important when they tumbled,",
        sky="The cliffs threw back every word until it sounded twice as bold.",
        close="When the light turned honey-colored, the canyon walls kept the day like a secret.",
        tags={"canyon", "ranch"},
    ),
}

ANIMALS = {
    "goat": AnimalCfg(
        id="goat",
        label="goat",
        phrase="a troublesome goat named Pepper",
        size=1,
        hoofed=True,
        voice="Maa-aa!",
        trouble="liked to climb anything that stood still longer than a minute",
        lure="an apple slice",
        boast="Pepper could find mischief in an empty bucket.",
        tags={"goat", "animal", "troublesome"},
    ),
    "calf": AnimalCfg(
        id="calf",
        label="calf",
        phrase="a troublesome calf named Clover",
        size=2,
        hoofed=True,
        voice="Mooo!",
        trouble="had a habit of poking her nose into every fence, sack, and supper plan",
        lure="a tin cup of oats",
        boast="Clover wandered toward trouble the way sunflowers turn toward the sun.",
        tags={"calf", "animal", "troublesome"},
    ),
    "mule": AnimalCfg(
        id="mule",
        label="mule",
        phrase="a troublesome young mule named Dusty",
        size=3,
        hoofed=True,
        voice="Hee-haw!",
        trouble="believed every new problem had been laid out especially for him",
        lure="a carrot",
        boast="Dusty was so troublesome he could tie worry into a knot with one stomp.",
        tags={"mule", "animal", "troublesome"},
    ),
}

CREVICES = {
    "narrow": CreviceCfg(
        id="narrow",
        label="narrow crevice",
        width=1,
        depth=1,
        image="a narrow crevice split the ground like a crooked zipper",
        edge="one hoof on each side with nowhere safe to go",
        echo="A pebble clicked down below and took its time answering back.",
        tags={"crevice", "gap"},
    ),
    "windy": CreviceCfg(
        id="windy",
        label="windy crevice",
        width=2,
        depth=2,
        image="a windy crevice yawned open across the trail",
        edge="half-slid onto a ledge no wider than a supper plate",
        echo="The hollow below sent up a cool breath that made everyone speak softer.",
        tags={"crevice", "wind"},
    ),
    "deep": CreviceCfg(
        id="deep",
        label="deep crevice",
        width=2,
        depth=3,
        image="a deep crevice cut through the earth as if a giant had dragged a thumbnail there",
        edge="down on a dusty shelf with pebbles skating away under restless hooves",
        echo="Every tiny rock went rattling down so long that the waiting felt bigger than the sky.",
        tags={"crevice", "deep"},
    ),
}

TOOLS = {
    "lasso": ToolCfg(
        id="lasso",
        label="lasso",
        phrase="a long ranch lasso",
        method="pull",
        reach=3,
        power=2,
        span=0,
        steady=0,
        action="swung the loop wide, dropped it neat around the animal, and pulled with steady hands",
        qa_text="used a long lasso to loop the animal and pull it to safety",
        tags={"lasso", "rope"},
    ),
    "hook_pole": ToolCfg(
        id="hook_pole",
        label="hook pole",
        phrase="a sturdy hook pole",
        method="pull",
        reach=4,
        power=3,
        span=0,
        steady=0,
        action="lowered the hook pole, caught the rescue strap, and guided the animal upward inch by inch",
        qa_text="used a hook pole and rescue strap to guide the animal up",
        tags={"pole", "rescue"},
    ),
    "ladder_bridge": ToolCfg(
        id="ladder_bridge",
        label="ladder bridge",
        phrase="a ranch ladder laid flat like a bridge",
        method="bridge",
        reach=0,
        power=0,
        span=2,
        steady=2,
        action="laid the ladder across the gap, held it firm, and coaxed the animal over rung by rung",
        qa_text="laid a ladder across the crevice and led the animal over it",
        tags={"ladder", "bridge"},
    ),
    "plank": ToolCfg(
        id="plank",
        label="plank bridge",
        phrase="a thick plank bridge",
        method="bridge",
        reach=0,
        power=0,
        span=3,
        steady=3,
        action="set a thick plank across the gap and kept it steady while the animal crossed",
        qa_text="set a thick plank across the crevice and helped the animal cross",
        tags={"plank", "bridge"},
    ),
}

GIRL_NAMES = ["Maggie", "Lila", "Nora", "June", "Rosie", "Elsie"]
BOY_NAMES = ["Bo", "Eli", "Wyatt", "Cal", "Jesse", "Finn"]
TRAITS = ["steady", "quick-thinking", "brave", "patient", "sharp-eyed"]
HELPERS = ["grandfather", "grandmother", "father", "mother"]


def tool_works(tool: ToolCfg, animal: AnimalCfg, crevice: CreviceCfg) -> bool:
    if tool.method == "pull":
        return tool.reach >= crevice.depth and tool.power >= animal.size
    if tool.method == "bridge":
        return tool.span >= crevice.width and tool.steady >= animal.size
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for locale in LOCALES:
        for animal_id, animal in ANIMALS.items():
            for crevice_id, crevice in CREVICES.items():
                for tool_id, tool in TOOLS.items():
                    if tool_works(tool, animal, crevice):
                        combos.append((locale, animal_id, crevice_id, tool_id))
    return combos


@dataclass
class StoryParams:
    locale: str
    animal: str
    crevice: str
    tool: str
    hero_name: str
    hero_gender: str
    helper_type: str
    hero_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        locale="mesa",
        animal="goat",
        crevice="narrow",
        tool="lasso",
        hero_name="Maggie",
        hero_gender="girl",
        helper_type="grandfather",
        hero_trait="steady",
        seed=101,
    ),
    StoryParams(
        locale="prairie",
        animal="calf",
        crevice="windy",
        tool="ladder_bridge",
        hero_name="Bo",
        hero_gender="boy",
        helper_type="mother",
        hero_trait="quick-thinking",
        seed=102,
    ),
    StoryParams(
        locale="canyon",
        animal="mule",
        crevice="deep",
        tool="hook_pole",
        hero_name="Rosie",
        hero_gender="girl",
        helper_type="grandmother",
        hero_trait="patient",
        seed=103,
    ),
    StoryParams(
        locale="mesa",
        animal="mule",
        crevice="windy",
        tool="plank",
        hero_name="Wyatt",
        hero_gender="boy",
        helper_type="father",
        hero_trait="brave",
        seed=104,
    ),
]


def explain_rejection(tool: ToolCfg, animal: AnimalCfg, crevice: CreviceCfg) -> str:
    if tool.method == "pull":
        problems: list[str] = []
        if tool.reach < crevice.depth:
            problems.append(f"reach {tool.reach} is too short for depth {crevice.depth}")
        if tool.power < animal.size:
            problems.append(f"pull power {tool.power} is too weak for a {animal.label} sized {animal.size}")
        why = "; ".join(problems) if problems else "it cannot do that rescue"
        return (
            f"(No story: {tool.label} will not rescue the {animal.label} from the {crevice.label} -- {why}. "
            f"Choose a longer or stronger pull tool, or use a bridge that can carry the animal.)"
        )
    problems = []
    if tool.span < crevice.width:
        problems.append(f"span {tool.span} is too short for width {crevice.width}")
    if tool.steady < animal.size:
        problems.append(f"steadiness {tool.steady} is too weak for a {animal.label} sized {animal.size}")
    why = "; ".join(problems) if problems else "it cannot do that rescue"
    return (
        f"(No story: {tool.label} will not rescue the {animal.label} from the {crevice.label} -- {why}. "
        f"Choose a wider, steadier bridge or a pull tool with enough reach and strength.)"
    )


def choose_name(gender: str, rng: random.Random) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def introduce(world: World, hero: Entity, helper: Entity, locale: Locale, animal: AnimalCfg) -> None:
    hero.memes["confidence"] += 1
    world.say(
        f"{locale.opener} {hero.id} rode along beside {hero.pronoun('possessive')} "
        f"{helper.label_word}, and {locale.sky}"
    )
    world.say(
        f"{hero.id} was a {hero.attrs['trait']} {hero.type} who could spot a loose horseshoe nail at ten paces, "
        f"or so {helper.label_word} liked to say."
    )
    world.say(
        f"With them trotted {animal.phrase}. {animal.boast} Pepper" if animal.id == "goat" else
        f"With them trailed {animal.phrase}. {animal.boast}" if animal.id == "calf" else
        f"Behind them clopped {animal.phrase}. {animal.boast}"
    )


def day_task(world: World, hero: Entity, helper: Entity, locale: Locale, animal: AnimalCfg) -> None:
    world.say(
        f"They were only trying to check fence posts near {locale.label}, but {animal.label} "
        f"{animal.trouble}."
    )
    world.say(
        f'"Keep one eye on that {animal.label}," said {helper.label_word}. '
        f'"A troublesome creature can turn a simple morning into a whole parade."'
    )
    world.say(f'"I am keeping one eye on {animal.pronoun("object")} and one eye on breakfast," {hero.id} said.')


def stumble(world: World, hero: Entity, helper: Entity, animal_ent: Entity, animal: AnimalCfg, crevice: CreviceCfg) -> None:
    animal_ent.meters["peril"] += 1
    animal_ent.memes["fear"] += 1
    hero.memes["alarm"] += 1
    helper.memes["alarm"] += 1
    world.say(
        f"Then the ground gave one mean little shrug. Ahead of them, {crevice.image}, "
        f"and the troublesome {animal.label} skidded to the edge and landed with {crevice.edge}."
    )
    world.say(f'{animal.voice} echoed up from below.')
    world.say(crevice.echo)


def suspense(world: World, hero: Entity, helper: Entity, animal_ent: Entity, crevice: CreviceCfg) -> None:
    world.say(
        f"{hero.id} dropped to {hero.pronoun('possessive')} knees and peered down. "
        f"Pebbles kept slipping past the animal and vanishing into the crevice."
    )
    world.say(
        f'"Don\'t thrash," {hero.id} whispered. "{animal_ent.id if animal_ent.id else "There now"}"'
    )
    world.say(
        f'"Easy," said {helper.label_word}. "If those hooves slide one more foot, '
        f'this turns from troublesome into terrible."'
    )


def plan(world: World, hero: Entity, helper: Entity, tool: ToolCfg, animal: AnimalCfg) -> None:
    helper.memes["trust"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id}'s eyes jumped from the frightened animal to {tool.phrase} strapped on the wagon side."
    )
    if tool.method == "pull":
        world.say(
            f'"I\'ve got it," said {hero.id}. "That {tool.label} can reach." '
            f'"And if {animal.label} kicks?" asked {helper.label_word}. '
            f'"Then I\'ll talk faster than {animal.pronoun("subject")} can kick," said {hero.id}.'
        )
    else:
        world.say(
            f'"I\'ve got it," said {hero.id}. "We can make a road where there isn\'t one." '
            f'"That\'s a mighty skinny road," said {helper.label_word}. '
            f'"Skinny is enough if it stays steady," said {hero.id}.'
        )


def rescue(world: World, hero: Entity, helper: Entity, animal_ent: Entity, animal: AnimalCfg, tool: ToolCfg) -> None:
    animal_ent.meters["peril"] = 0.0
    animal_ent.meters["safe"] += 1
    animal_ent.memes["fear"] = 0.0
    animal_ent.memes["relief"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Very slowly, while the wind held its breath and even the wagon seemed to wait, "
        f"{hero.id} {tool.action}."
    )
    if tool.method == "pull":
        world.say(
            f'The troublesome {animal.label} scrabbled, snorted, and came up in a shower of dust. '
            f'At last all four hooves thumped safe ground.'
        )
    else:
        world.say(
            f'The troublesome {animal.label} trembled, tested the way with one hoof, then another, '
            f'and crossed at last with a shaky clatter.'
        )
    world.say(f'"There now," said {helper.label_word}, letting out a breath. "That was nearer than I like."')


def ending(world: World, hero: Entity, helper: Entity, locale: Locale, animal_ent: Entity, animal: AnimalCfg, crevice: CreviceCfg) -> None:
    animal_ent.meters["mischief"] = 0.0
    animal_ent.memes["calm"] += 1
    world.say(
        f"{hero.id} rubbed the animal's neck while it leaned close and stopped acting troublesome for at least three whole minutes."
    )
    world.say(
        f'"What did we learn?" asked {helper.label_word}. '
        f'"That a crevice can hide where the ground looks honest," said {hero.id}. '
        f'"And?" asked {helper.label_word}. '
        f'"And that big talk is no good unless your hands stay steady."'
    )
    world.say(
        f"After that, whenever they crossed the rough ground, even {animal.phrase.split(' named ')[0]} stepped slower near a crevice."
    )
    world.say(locale.close)


def tell(
    locale: Locale,
    animal: AnimalCfg,
    crevice: CreviceCfg,
    tool: ToolCfg,
    hero_name: str,
    hero_gender: str,
    helper_type: str,
    hero_trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        attrs={"trait": hero_trait},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    animal_ent = world.add(Entity(
        id=animal.label,
        kind="character",
        type="animal",
        label=animal.label,
        phrase=animal.phrase,
        role="animal",
        attrs={"size": animal.size, "hoofed": animal.hoofed, "lure": animal.lure},
    ))

    introduce(world, hero, helper, locale, animal)
    day_task(world, hero, helper, locale, animal)

    world.para()
    stumble(world, hero, helper, animal_ent, animal, crevice)
    suspense(world, hero, helper, animal_ent, crevice)

    world.para()
    plan(world, hero, helper, tool, animal)
    rescue(world, hero, helper, animal_ent, animal, tool)

    world.para()
    ending(world, hero, helper, locale, animal_ent, animal, crevice)

    world.facts.update(
        hero=hero,
        helper=helper,
        animal=animal,
        animal_ent=animal_ent,
        locale=locale,
        crevice=crevice,
        tool=tool,
        rescued=animal_ent.meters["safe"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "crevice": [
        (
            "What is a crevice?",
            "A crevice is a narrow crack or split in rock or ground. It can be hard to see from far away, so people and animals need to watch their steps near one.",
        )
    ],
    "goat": [
        (
            "Why do goats like to climb?",
            "Goats are good climbers because their hooves can grip rough places. That is useful on hills, but it can also lead them into trouble.",
        )
    ],
    "calf": [
        (
            "What is a calf?",
            "A calf is a young cow. Calves are curious, so they often wander where they should not.",
        )
    ],
    "mule": [
        (
            "What is a mule?",
            "A mule is a strong animal with long ears that people often use for work. A mule can carry heavy things, but it can also be stubborn.",
        )
    ],
    "lasso": [
        (
            "What is a lasso?",
            "A lasso is a long rope with a loop in it. Ranchers can throw the loop around something to catch it or pull it safely.",
        )
    ],
    "bridge": [
        (
            "Why does a bridge help over a gap?",
            "A bridge gives you a path across empty space. If it is wide and steady enough, it keeps feet from slipping into the gap.",
        )
    ],
    "rescue": [
        (
            "Why is it important to stay calm during a rescue?",
            "Staying calm helps people think clearly and move carefully. In a scary moment, quiet hands and a good plan work better than rushing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["crevice", "goat", "calf", "mule", "lasso", "bridge", "rescue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal"]
    crevice = f["crevice"]
    tool = f["tool"]
    locale = f["locale"]
    return [
        (
            f'Write a short tall tale for a 3-to-5-year-old that includes the words '
            f'"crevice" and "troublesome", with dialogue and suspense, set on {locale.label}.'
        ),
        (
            f"Tell a child-friendly rescue story where {hero.id} and {hero.pronoun('possessive')} "
            f"{helper.label_word} save a troublesome {animal.label} from a {crevice.label} using {tool.phrase}."
        ),
        (
            f"Write a playful western-style tale with suspenseful dialogue, a frightened animal near a crevice, "
            f"and an ending that shows everyone has learned to step more carefully."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal"]
    crevice = f["crevice"]
    tool = f["tool"]
    locale = f["locale"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} {helper.label_word}, and a troublesome {animal.label}. They are out on {locale.label} when the trouble begins.",
        ),
        (
            f"Why was the {animal.label} called troublesome?",
            f"The {animal.label} kept poking into places it should not go. That habit is what brought it too close to the crevice.",
        ),
        (
            f"What made the middle of the story feel scary?",
            f"The animal was stuck by the crevice while pebbles kept slipping away below it. That made everyone worry it might slide farther before help reached it.",
        ),
        (
            f"How did {hero.id} rescue the {animal.label}?",
            f"{hero.id} {tool.qa_text}. The tool worked because it matched the shape of the danger, not just because {hero.pronoun('subject')} was brave.",
        ),
        (
            "How did the story end?",
            f"It ended with the animal back on safe ground and acting calm for a little while. After that, they all stepped more carefully near a crevice, which shows the scare changed them.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal"]
    tool = f["tool"]
    tags: list[str] = ["crevice"]
    if animal.id in {"goat", "calf", "mule"}:
        tags.append(animal.id)
    if tool.method == "pull":
        tags.append("lasso")
    else:
        tags.append("bridge")
    tags.append("rescue")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
pull_tool(T)   :- tool(T), method(T, pull).
bridge_tool(T) :- tool(T), method(T, bridge).

works(T, A, C) :- pull_tool(T), reach(T, R), depth(C, D), R >= D,
                  power(T, P), size(A, S), P >= S.
works(T, A, C) :- bridge_tool(T), span(T, W), width(C, CW), W >= CW,
                  steady(T, St), size(A, S), St >= S.

valid(L, A, C, T) :- locale(L), animal(A), crevice(C), tool(T), works(T, A, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lid in LOCALES:
        lines.append(asp.fact("locale", lid))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("size", aid, animal.size))
    for cid, crevice in CREVICES.items():
        lines.append(asp.fact("crevice", cid))
        lines.append(asp.fact("width", cid, crevice.width))
        lines.append(asp.fact("depth", cid, crevice.depth))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("method", tid, tool.method))
        lines.append(asp.fact("reach", tid, tool.reach))
        lines.append(asp.fact("power", tid, tool.power))
        lines.append(asp.fact("span", tid, tool.span))
        lines.append(asp.fact("steady", tid, tool.steady))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _check_params(params: StoryParams) -> None:
    if params.locale not in LOCALES:
        raise StoryError(f"(Unknown locale: {params.locale})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.crevice not in CREVICES:
        raise StoryError(f"(Unknown crevice: {params.crevice})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    animal = ANIMALS[params.animal]
    crevice = CREVICES[params.crevice]
    tool = TOOLS[params.tool]
    if not tool_works(tool, animal, crevice):
        raise StoryError(explain_rejection(tool, animal, crevice))
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED[:2])
    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated empty story.)")
            emit(sample, trace=False, qa=False, header="")
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a troublesome animal, a crevice, and a rescue tool that must honestly fit."
    )
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--crevice", choices=CREVICES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.animal and args.crevice:
        tool = TOOLS[args.tool]
        animal = ANIMALS[args.animal]
        crevice = CREVICES[args.crevice]
        if not tool_works(tool, animal, crevice):
            raise StoryError(explain_rejection(tool, animal, crevice))

    combos = [
        combo for combo in valid_combos()
        if (args.locale is None or combo[0] == args.locale)
        and (args.animal is None or combo[1] == args.animal)
        and (args.crevice is None or combo[2] == args.crevice)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    locale_id, animal_id, crevice_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper or rng.choice(HELPERS)
    hero_name = args.name or choose_name(gender, rng)
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        locale=locale_id,
        animal=animal_id,
        crevice=crevice_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=gender,
        helper_type=helper_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        locale=LOCALES[params.locale],
        animal=ANIMALS[params.animal],
        crevice=CREVICES[params.crevice],
        tool=TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        hero_trait=params.hero_trait,
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
        print(f"{len(combos)} compatible (locale, animal, crevice, tool) combos:\n")
        for locale_id, animal_id, crevice_id, tool_id in combos:
            print(f"  {locale_id:8} {animal_id:6} {crevice_id:7} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name}: {p.animal} at {p.locale} ({p.crevice}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
