#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/white_sneer_flashback_teamwork_fairy_tale.py
=======================================================================

A small fairy-tale storyworld about two children who must reach a white treasure
beyond a small obstacle while a sneering creature tries to scare them out of it.
The turn comes through a flashback: one child remembers an elder's lesson, and
the pair solves the problem through teamwork instead of lonely pride.

This world is intentionally narrow. It only tells stories where:
- a fairy-tale place really contains the chosen obstacle,
- the chosen aid really helps with that obstacle,
- and the remembered lesson actually teaches the matching cooperative method.

Run it
------
    python storyworlds/worlds/gpt-5.4/white_sneer_flashback_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/white_sneer_flashback_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/white_sneer_flashback_teamwork_fairy_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/white_sneer_flashback_teamwork_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/white_sneer_flashback_teamwork_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    path: str
    mood: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    article: str
    danger: str
    beyond: str
    verb: str
    need: str
    risk: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"{self.article} {self.label}"

    @property
    def The(self) -> str:
        text = self.the
        return text[0].upper() + text[1:]


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    elder: str
    line: str
    teaches: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    glow: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Taunter:
    id: str
    label: str
    style: str
    strength: int
    voice: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sneer_fear(world: World) -> list[str]:
    taunter = world.entities.get("taunter")
    if not taunter or taunter.memes["sneer"] < THRESHOLD:
        return []
    sig = ("sneer_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("path").meters["gloom"] += 1
    return []


def _r_team_courage(world: World) -> list[str]:
    a = world.entities.get("lead")
    b = world.entities.get("partner")
    if not a or not b:
        return []
    if a.meters["helping"] < THRESHOLD or b.meters["helping"] < THRESHOLD:
        return []
    sig = ("team_courage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (a, b):
        kid.memes["courage"] += 1
        if kid.memes["fear"] >= THRESHOLD:
            kid.memes["fear"] -= 1
    world.get("path").meters["hope"] += 1
    return []


def _r_reach_treasure(world: World) -> list[str]:
    obstacle = world.entities.get("obstacle")
    treasure = world.entities.get("treasure")
    if not obstacle or not treasure:
        return []
    if obstacle.meters["crossed"] < THRESHOLD or treasure.meters["taken"] >= THRESHOLD:
        return []
    sig = ("reach_treasure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["taken"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule("sneer_fear", "social", _r_sneer_fear),
    Rule("team_courage", "social", _r_team_courage),
    Rule("reach_treasure", "physical", _r_reach_treasure),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def obstacle_needs(obstacle_id: str) -> tuple[str, str]:
    return REQUIREMENTS[obstacle_id]


def valid_combo(place_id: str, obstacle_id: str, aid_id: str, lesson_id: str) -> bool:
    if obstacle_id not in PLACES[place_id].affords:
        return False
    aid_need, lesson_need = obstacle_needs(obstacle_id)
    return aid_id == aid_need and lesson_id == lesson_need


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affords):
            aid_need, lesson_need = obstacle_needs(obstacle_id)
            out.append((place_id, obstacle_id, aid_need, lesson_need))
    return sorted(out)


def explain_rejection(place_id: str, obstacle_id: str, aid_id: str, lesson_id: str) -> str:
    place = PLACES[place_id]
    obstacle = OBSTACLES[obstacle_id]
    aid = AIDS[aid_id]
    lesson = LESSONS[lesson_id]
    if obstacle_id not in place.affords:
        return (
            f"(No story: {place.name} does not hold {obstacle.the}. "
            f"Try an obstacle that belongs in that place.)"
        )
    aid_need, lesson_need = obstacle_needs(obstacle_id)
    if aid_id != aid_need:
        right = AIDS[aid_need]
        return (
            f"(No story: {aid.phrase} would not safely solve {obstacle.the}. "
            f"Use {right.phrase} instead.)"
        )
    if lesson_id != lesson_need:
        right = LESSONS[lesson_need]
        return (
            f"(No story: the flashback lesson must fit {obstacle.the}. "
            f"Remember {right.elder}'s advice instead.)"
        )
    return "(No story: this combination does not make a reasonable fairy tale.)"


def opening_line(place: Place) -> str:
    return (
        f"In a small kingdom where dawn liked to linger on rooftops, "
        f"there was {place.name}, {place.mood}."
    )


def quest_setup(world: World, lead: Entity, partner: Entity, place: Place, treasure: Treasure) -> None:
    lead.memes["care"] += 1
    partner.memes["care"] += 1
    world.say(opening_line(place))
    world.say(
        f"One morning, {lead.id} and {partner.id} were sent along {place.path} "
        f"to fetch {treasure.phrase}. The village needed it {treasure.use}."
    )
    world.say(
        f"They had heard that {treasure.label} shone so pale and bright that even a "
        f"winter cloud looked gray beside its white light."
    )


def sight_obstacle(world: World, place: Place, obstacle: Obstacle, taunter: Taunter) -> None:
    world.say(
        f"At the far end of {place.name}, they came to {obstacle.the}, "
        f"{obstacle.danger}."
    )
    world.say(
        f"Beyond it, on {obstacle.beyond}, waited the treasure they had come to find."
    )
    taunter_ent = world.get("taunter")
    taunter_ent.memes["sneer"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {taunter.label} peeped out and let a {taunter.style} sneer curl across "
        f"{taunter.pronoun('possessive')} face. "
        f'"{taunter.voice}" it said.'
    )


def lone_try(world: World, lead: Entity, obstacle: Obstacle, taunter: Taunter) -> None:
    lead.memes["pride"] += 1
    lead.meters["reaching"] += 1
    world.say(
        f"For one worried moment, {lead.id} thought about facing {obstacle.the} alone. "
        f"{lead.pronoun().capitalize()} took a brave little step and nearly {obstacle.verb}."
    )
    if taunter.strength >= 2:
        world.say(
            f"The sneer stung more than the cold air, and {lead.id}'s heart gave a jump."
        )


def flashback(world: World, lead: Entity, partner: Entity, lesson: Lesson) -> None:
    lead.memes["memory"] += 1
    partner.memes["trust"] += 1
    world.say(
        f"Then a memory flickered through {lead.id}'s mind like a lamp behind frosty glass."
    )
    world.say(
        f"In a flashback, {lead.pronoun()} saw {lesson.elder} again: {lesson.image}. "
        f'"{lesson.line}"'
    )
    world.say(
        f"{lead.id} looked at {partner.id} and understood that the old lesson had never "
        f"been about being strongest. It had been about being together."
    )


def teamwork_action(
    world: World,
    lead: Entity,
    partner: Entity,
    obstacle: Obstacle,
    aid: Aid,
    treasure: Treasure,
) -> None:
    lead.meters["helping"] += 1
    partner.meters["helping"] += 1
    world.get("aid").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Together," {lead.id} whispered, and {partner.id} nodded.'
    )
    world.say(
        f"They used {aid.phrase}. {aid.action} as they faced {obstacle.the}."
    )
    world.get("obstacle").meters["crossed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Step by step, their teamwork did what lonely rushing never could. "
        f"They passed {obstacle.the} and reached {treasure.phrase}."
    )
    world.say(
        f"When {partner.id} lifted it, {treasure.glow}, and the path no longer looked so dark."
    )


def return_home(world: World, lead: Entity, partner: Entity, taunter: Taunter, treasure: Treasure) -> None:
    taunter_ent = world.get("taunter")
    taunter_ent.memes["sneer"] = 0.0
    taunter_ent.memes["silenced"] += 1
    world.say(
        f"The sneer on {taunter.label}'s face slipped away. It had no cruel word left."
    )
    world.say(
        f"{lead.id} and {partner.id} carried {treasure.label} home between them, "
        f"carefully and proudly."
    )
    world.say(
        f"That evening, {treasure.label} stood in the village square, white and bright, "
        f"and everyone could see what had changed: two small travelers had become a true team."
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    aid: Aid,
    lesson: Lesson,
    treasure: Treasure,
    taunter: Taunter,
    lead_name: str = "Elsa",
    lead_gender: str = "girl",
    partner_name: str = "Tobin",
    partner_gender: str = "boy",
    relation: str = "friends",
    lead_trait: str = "brave",
    partner_trait: str = "gentle",
) -> World:
    world = World()
    lead = world.add(Entity(id="lead", kind="character", type=lead_gender, role="lead", label=lead_name,
                            traits=[lead_trait], attrs={"relation": relation, "name": lead_name}))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, role="partner",
                               label=partner_name, traits=[partner_trait],
                               attrs={"relation": relation, "name": partner_name}))
    world.add(Entity(id="path", type="path", label=place.path))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    world.add(Entity(id="aid", type="aid", label=aid.label))
    world.add(Entity(id="treasure", type="treasure", label=treasure.label))
    world.add(Entity(id="taunter", type="creature", label=taunter.label))

    quest_setup(world, lead, partner, place, treasure)
    world.para()
    sight_obstacle(world, place, obstacle, taunter)
    lone_try(world, lead, obstacle, taunter)
    world.para()
    flashback(world, lead, partner, lesson)
    teamwork_action(world, lead, partner, obstacle, aid, treasure)
    world.para()
    return_home(world, lead, partner, taunter, treasure)

    world.facts.update(
        place=place,
        obstacle=obstacle,
        aid=aid,
        lesson=lesson,
        treasure=treasure,
        taunter=taunter,
        lead=lead,
        partner=partner,
        relation=relation,
        teamwork=lead.meters["helping"] >= THRESHOLD and partner.meters["helping"] >= THRESHOLD,
        treasure_taken=world.get("treasure").meters["taken"] >= THRESHOLD,
        flashback_used=lead.memes["memory"] >= THRESHOLD,
    )
    return world


PLACES = {
    "moon_meadow": Place(
        "moon_meadow",
        "Moon Meadow",
        "the silver path through the reeds",
        "where dew stayed on the grass long after sunrise",
        affords={"brook"},
        tags={"meadow"},
    ),
    "glass_hill": Place(
        "glass_hill",
        "Glass Hill",
        "the winding stair of old stones",
        "where the rocks shone as if a giant had polished them",
        affords={"wall"},
        tags={"hill"},
    ),
    "rose_lane": Place(
        "rose_lane",
        "Rose Lane",
        "the lane of bent gateposts",
        "where even the gate cast a thorny shadow",
        affords={"thorns"},
        tags={"lane"},
    ),
    "whisper_wood": Place(
        "whisper_wood",
        "Whisper Wood",
        "the mossy track under the birches",
        "where every leaf seemed to listen",
        affords={"brook", "thorns"},
        tags={"wood"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        "brook",
        "brook",
        "a",
        "its black water running cold over bright stones",
        "a low white rock in the middle of the stream",
        "slip into the water",
        "someone to hold fast while crossing",
        "wet shoes and a frightened tumble",
        tags={"brook", "water"},
    ),
    "wall": Obstacle(
        "wall",
        "stone wall",
        "a",
        "its top too high for one child alone",
        "the little ledge where the treasure rested",
        "slide back down the stones",
        "someone to steady and someone to pull",
        "a scraped knee and a hard drop",
        tags={"wall", "climb"},
    ),
    "thorns": Obstacle(
        "thorns",
        "thorn hedge",
        "a",
        "its hooked branches knitting themselves into a prickly fence",
        "the patch of clear ground behind the hedge",
        "catch a sleeve on the briars",
        "shared hands and a cover over the briars",
        "snags, scratches, and tears",
        tags={"thorns", "briar"},
    ),
}

AIDS = {
    "rope": Aid(
        "rope",
        "rope",
        "a coil of rope",
        "One held the rope tight while the other crossed, and then they traded places",
        supports={"brook"},
        tags={"rope"},
    ),
    "stool": Aid(
        "stool",
        "stool",
        "a little wooden stool",
        "One braced the stool while the other climbed, then a strong hand reached back to pull the other up",
        supports={"wall"},
        tags={"stool"},
    ),
    "cloak": Aid(
        "cloak",
        "cloak",
        "a patched blue cloak",
        "They spread the cloak over the worst thorns and moved it together as a soft shield",
        supports={"thorns"},
        tags={"cloak"},
    ),
}

LESSONS = {
    "hold_fast": Lesson(
        "hold_fast",
        "Grandmother Rowan",
        "When the ground is unkind, hold fast to each other before you hold fast to your wish.",
        "an old winter morning when Grandmother Rowan helped them cross a ditch by gripping both their hands",
        "brook",
        tags={"grandmother", "teamwork"},
    ),
    "step_and_pull": Lesson(
        "step_and_pull",
        "Old Mason Brindle",
        "A high place is climbed twice: once by your own feet and once by the friend who pulls you after.",
        "the day Old Mason Brindle laughed softly and showed them how one child could steady the other on a loose step",
        "wall",
        tags={"mason", "teamwork"},
    ),
    "spread_and_share": Lesson(
        "spread_and_share",
        "Aunt Willow",
        "Briars grow meanest where hands try to hurry alone; lay kindness down first and go together.",
        "a spring afternoon when Aunt Willow laid her shawl over nettles so both children could pass without tears",
        "thorns",
        tags={"aunt", "teamwork"},
    ),
}

TREASURES = {
    "rose": Treasure(
        "rose",
        "the white rose",
        "the white rose",
        "its petals held the faint shine of moonmilk",
        "to brighten the winter feast table",
        tags={"rose", "white"},
    ),
    "feather": Treasure(
        "feather",
        "the white feather",
        "the white feather",
        "it gleamed like a stroke of snow caught in sunlight",
        "to tuck above the story chair in the hall",
        tags={"feather", "white"},
    ),
    "bellflower": Treasure(
        "bellflower",
        "the white bellflower",
        "the white bellflower",
        "its pale cup glimmered like a tiny lantern",
        "to ring the first song of dawn with its soft scent",
        tags={"flower", "white"},
    ),
}

TAUNTERS = {
    "imp": Taunter(
        "imp",
        "a reed imp",
        "pinched little",
        2,
        "No two children can pass that way. One will turn back crying, and the other will follow.",
        tags={"imp", "sneer"},
    ),
    "rook": Taunter(
        "rook",
        "a black rook",
        "sharp beaky",
        1,
        "Hop if you like. The stones will not grow shorter for you.",
        tags={"rook", "sneer"},
    ),
    "goblin": Taunter(
        "goblin",
        "a hedge goblin",
        "thin green",
        2,
        "Run at it alone, little one. That is how small heroes become small mistakes.",
        tags={"goblin", "sneer"},
    ),
}

REQUIREMENTS = {
    "brook": ("rope", "hold_fast"),
    "wall": ("stool", "step_and_pull"),
    "thorns": ("cloak", "spread_and_share"),
}

GIRL_NAMES = ["Elsa", "Mira", "Nell", "Ivy", "Lina", "Ada", "Pippa", "Ruth"]
BOY_NAMES = ["Tobin", "Finn", "Ari", "Milo", "Rowan", "Hugh", "Otto", "Bram"]
TRAITS = ["brave", "gentle", "steady", "quick", "kind", "careful"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    aid: str
    lesson: str
    treasure: str
    taunter: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    relation: str
    lead_trait: str
    partner_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "brook": [
        (
            "Why is a brook hard to cross?",
            "A brook can have slippery stones and fast cold water. Even a small stream can make you fall if you rush."
        )
    ],
    "wall": [
        (
            "Why is climbing a wall easier with help?",
            "A friend can steady you and reach back for you. Two careful people can do safely what one small child may not."
        )
    ],
    "thorns": [
        (
            "Why are thorn bushes tricky?",
            "Thorns are sharp little spikes on a plant. They can catch clothes and scratch skin if you push through too fast."
        )
    ],
    "rope": [
        (
            "What is a rope useful for?",
            "A rope can help people hold on and keep steady. It is useful when someone needs support crossing a tricky place."
        )
    ],
    "stool": [
        (
            "What does a stool help you do?",
            "A stool gives you a small extra step upward. It can help you reach a place that is a little too high."
        )
    ],
    "cloak": [
        (
            "What is a cloak?",
            "A cloak is a loose outer cloth people wear over their clothes. In old tales it can also cover something rough or prickly for a moment."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back to an earlier memory. It helps a character remember something important from before."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another toward the same goal. Working together can solve problems that feel too big alone."
        )
    ],
    "white": [
        (
            "Why do fairy tales often use white things as treasures?",
            "White can look bright, clean, and moonlit in a fairy tale. It helps a treasure seem special and easy to picture."
        )
    ],
    "sneer": [
        (
            "What does it mean to sneer?",
            "To sneer is to smile or speak in a mean, mocking way. A sneer tries to make someone feel small."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "flashback", "teamwork", "sneer", "white",
    "brook", "wall", "thorns", "rope", "stool", "cloak",
]


def pair_noun(lead: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if lead.type == "girl" and partner.type == "girl":
            return "two sisters"
        if lead.type == "boy" and partner.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    obstacle = f["obstacle"]
    treasure = f["treasure"]
    taunter = f["taunter"]
    return [
        (
            'Write a short fairy tale for a 3-to-5-year-old that includes the words '
            '"white" and "sneer", uses a flashback, and ends with teamwork solving the problem.'
        ),
        (
            f"Tell a gentle fairy tale where {lead.label} and {partner.label} must pass "
            f"{obstacle.the} to fetch {treasure.label}, while {taunter.label} tries to mock them."
        ),
        (
            f"Write a fairy-tale story in which a mean sneer almost scares two children, "
            f"but a remembered lesson helps them work together and bring home {treasure.label}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    place = f["place"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    lesson = f["lesson"]
    treasure = f["treasure"]
    taunter = f["taunter"]
    relation = f["relation"]
    pair = pair_noun(lead, partner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {lead.label} and {partner.label}. They travel through {place.name} to fetch {treasure.label} for their village."
        ),
        (
            f"What stood between the children and {treasure.label}?",
            f"{obstacle.The} stood in the way. It looked dangerous enough that one child alone might {obstacle.verb}."
        ),
        (
            "Who sneered at them, and why did that matter?",
            f"{taunter.label.capitalize()} sneered at them and tried to make them feel small. The mean words raised their fear for a moment and made the problem feel bigger."
        ),
    ]
    if f["flashback_used"]:
        qa.append(
            (
                "What happened in the flashback?",
                f"{lead.label} remembered {lesson.elder} and the lesson, \"{lesson.line}\". The memory mattered because it taught that the obstacle should be faced together, not alone."
            )
        )
    if f["teamwork"]:
        qa.append(
            (
                f"How did {lead.label} and {partner.label} solve the problem?",
                f"They used {aid.phrase} and worked as a team to pass {obstacle.the}. Their teamwork turned fear into courage because each child helped the other do the part that was hardest alone."
            )
        )
    if f["treasure_taken"]:
        qa.append(
            (
                "How did the story end?",
                f"They brought home {treasure.label}, and it stood white and bright in the village square. The ending shows that the children changed from worried travelers into a true team."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {
        "flashback",
        "teamwork",
        "sneer",
        "white",
        f["obstacle"].id,
        f["aid"].id,
    }
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        "moon_meadow", "brook", "rope", "hold_fast", "rose", "imp",
        "Elsa", "girl", "Tobin", "boy", "friends", "brave", "steady"
    ),
    StoryParams(
        "glass_hill", "wall", "stool", "step_and_pull", "bellflower", "rook",
        "Mira", "girl", "Finn", "boy", "siblings", "careful", "kind"
    ),
    StoryParams(
        "rose_lane", "thorns", "cloak", "spread_and_share", "feather", "goblin",
        "Nell", "girl", "Ada", "girl", "friends", "quick", "gentle"
    ),
    StoryParams(
        "whisper_wood", "brook", "rope", "hold_fast", "bellflower", "goblin",
        "Bram", "boy", "Ivy", "girl", "siblings", "steady", "brave"
    ),
]


ASP_RULES = r"""
requires_aid(brook, rope).
requires_lesson(brook, hold_fast).
requires_aid(wall, stool).
requires_lesson(wall, step_and_pull).
requires_aid(thorns, cloak).
requires_lesson(thorns, spread_and_share).

valid(P, O, A, L) :- place(P), obstacle(O), aid(A), lesson(L),
                     affords(P, O),
                     requires_aid(O, A),
                     requires_lesson(O, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for aid_id in AIDS:
        lines.append(asp.fact("aid", aid_id))
    for lesson_id in LESSONS:
        lines.append(asp.fact("lesson", lesson_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Generated sample is missing QA/prompts during verify.")
        print("OK: smoke test generated a normal story with QA.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a white treasure, a sneer, a flashback, and teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--taunter", choices=TAUNTERS)
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_place = args.place
    explicit_obstacle = args.obstacle
    explicit_aid = args.aid
    explicit_lesson = args.lesson

    if explicit_place and explicit_obstacle and explicit_aid and explicit_lesson:
        if not valid_combo(explicit_place, explicit_obstacle, explicit_aid, explicit_lesson):
            raise StoryError(explain_rejection(explicit_place, explicit_obstacle, explicit_aid, explicit_lesson))
    elif explicit_place and explicit_obstacle and explicit_aid:
        need_lesson = REQUIREMENTS[explicit_obstacle][1]
        if explicit_obstacle not in PLACES[explicit_place].affords or explicit_aid != REQUIREMENTS[explicit_obstacle][0]:
            raise StoryError(explain_rejection(explicit_place, explicit_obstacle, explicit_aid, need_lesson))
    elif explicit_place and explicit_obstacle and explicit_lesson:
        need_aid = REQUIREMENTS[explicit_obstacle][0]
        if explicit_obstacle not in PLACES[explicit_place].affords or explicit_lesson != REQUIREMENTS[explicit_obstacle][1]:
            raise StoryError(explain_rejection(explicit_place, explicit_obstacle, need_aid, explicit_lesson))
    elif explicit_obstacle and explicit_aid:
        need_lesson = REQUIREMENTS[explicit_obstacle][1]
        place_probe = explicit_place or next(pid for pid, p in PLACES.items() if explicit_obstacle in p.affords)
        if explicit_aid != REQUIREMENTS[explicit_obstacle][0]:
            raise StoryError(explain_rejection(place_probe, explicit_obstacle, explicit_aid, need_lesson))
    elif explicit_obstacle and explicit_lesson:
        need_aid = REQUIREMENTS[explicit_obstacle][0]
        place_probe = explicit_place or next(pid for pid, p in PLACES.items() if explicit_obstacle in p.affords)
        if explicit_lesson != REQUIREMENTS[explicit_obstacle][1]:
            raise StoryError(explain_rejection(place_probe, explicit_obstacle, need_aid, explicit_lesson))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
        and (args.lesson is None or combo[3] == args.lesson)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, aid_id, lesson_id = rng.choice(sorted(combos))
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    taunter_id = args.taunter or rng.choice(sorted(TAUNTERS))
    lead_name, lead_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=lead_name)
    relation = args.relation or rng.choice(["friends", "siblings"])
    lead_trait = rng.choice(TRAITS)
    partner_trait = rng.choice([t for t in TRAITS if t != lead_trait] or TRAITS)
    return StoryParams(
        place_id, obstacle_id, aid_id, lesson_id, treasure_id, taunter_id,
        lead_name, lead_gender, partner_name, partner_gender,
        relation, lead_trait, partner_trait
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        OBSTACLES[params.obstacle],
        AIDS[params.aid],
        LESSONS[params.lesson],
        TREASURES[params.treasure],
        TAUNTERS[params.taunter],
        params.lead_name,
        params.lead_gender,
        params.partner_name,
        params.partner_gender,
        params.relation,
        params.lead_trait,
        params.partner_trait,
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
        print(f"{len(combos)} compatible (place, obstacle, aid, lesson) combos:\n")
        for place_id, obstacle_id, aid_id, lesson_id in combos:
            print(f"  {place_id:12} {obstacle_id:8} {aid_id:6} {lesson_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.lead_name} and {p.partner_name}: "
                f"{p.obstacle} at {p.place} with {p.aid}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
