#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py
===================================================================================

A small story world for a gentle mystery: a sudden hailstorm seems to have
ruined special rainbow party decorations, but two children follow clues,
discover it was an accident, and help transform the damaged thing into a new
beautiful decoration. The story always ends happily, and one of the families
in the world is openly gay in a simple, child-facing way.

Run it
------
    python storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py --place library --decor paper_banner --transform pinwheels
    python storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py --place bakery --cause high_window
    python storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py --all
    python storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/hail_gay_accident_transformation_happy_ending_mystery.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    roof_sound: str
    window: str
    party: str
    clue_spot: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Decor:
    id: str
    label: str
    phrase: str
    material: str
    damage: str
    clue_line: str
    final_bits: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transform:
    id: str
    label: str
    phrase: str
    materials: set[str] = field(default_factory=set)
    action: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    clue: str
    reveal: str
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_damage_worry(world: World) -> list[str]:
    decor = world.get("decor")
    kids = [world.get("hero"), world.get("friend")]
    if decor.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_worry", decor.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in kids:
        kid.memes["worry"] += 1
    return ["__damage__"]


def _r_solved_relief(world: World) -> list[str]:
    if world.get("mystery").meters["solved"] < THRESHOLD:
        return []
    sig = ("solved_relief", "mystery")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend", "parent1", "parent2"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["joy"] += 1
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="damage_worry", tag="emotion", apply=_r_damage_worry),
    Rule(name="solved_relief", tag="emotion", apply=_r_solved_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "library": Place(
        id="library",
        label="the little library hall",
        roof_sound="drummed on the glass skylight like a hundred tiny marbles",
        window="the tall side window",
        party="a rainbow riddle night",
        clue_spot="under the reading tree poster",
        allows={"high_window", "loose_clip"},
        tags={"library"},
    ),
    "bakery": Place(
        id="bakery",
        label="the warm corner bakery",
        roof_sound="rattled across the tin awning over the front window",
        window="the front awning window",
        party="a rainbow cookie mystery party",
        clue_spot="beside the cake stand",
        allows={"loose_clip", "open_door"},
        tags={"bakery"},
    ),
    "hall": Place(
        id="hall",
        label="the bright community hall",
        roof_sound="tapped on the high roof and skipped against the big windows",
        window="the high window",
        party="a rainbow mystery dance",
        clue_spot="by the folding stage",
        allows={"high_window", "open_door", "loose_clip"},
        tags={"hall"},
    ),
}

DECORS = {
    "paper_banner": Decor(
        id="paper_banner",
        label="banner",
        phrase="a long paper rainbow banner",
        material="paper",
        damage="soft, speckled, and torn with little round hail holes",
        clue_line="Cold white hail beads lay under it like spilled marbles.",
        final_bits="the bright paper pieces",
        tags={"paper", "banner"},
    ),
    "fabric_banner": Decor(
        id="fabric_banner",
        label="banner",
        phrase="a stitched fabric rainbow banner",
        material="fabric",
        damage="wet at the edge and snipped into fluttering strips by the hail",
        clue_line="A loose clip swung nearby, and damp threads curled at the edge.",
        final_bits="the strong rainbow strips",
        tags={"fabric", "banner"},
    ),
    "tissue_lanterns": Decor(
        id="tissue_lanterns",
        label="lanterns",
        phrase="three tissue-paper rainbow lanterns",
        material="tissue",
        damage="dimpled with tiny holes so the light looked freckled and strange",
        clue_line="Little icy pebbles glittered in the puddle below them.",
        final_bits="the dotted lantern shells",
        tags={"tissue", "lantern"},
    ),
}

TRANSFORMS = {
    "pinwheels": Transform(
        id="pinwheels",
        label="pinwheels",
        phrase="a row of rainbow pinwheels",
        materials={"paper"},
        action="cut the dry parts into squares and fold them into little pinwheels",
        ending_image="When the doors opened, the pinwheels spun whenever children ran past.",
        tags={"pinwheels", "paper"},
    ),
    "ribbon_garland": Transform(
        id="ribbon_garland",
        label="garland",
        phrase="a swishing ribbon garland",
        materials={"fabric"},
        action="trim the torn strips neatly and tie them into a soft ribbon garland",
        ending_image="By party time, the garland waved over the room like a happy rainbow river.",
        tags={"garland", "fabric"},
    ),
    "star_lanterns": Transform(
        id="star_lanterns",
        label="star lanterns",
        phrase="glowing star lanterns",
        materials={"tissue"},
        action="trace stars around the little holes and turn each lantern into a star lantern",
        ending_image="That evening, the lanterns shone with tiny star shapes all around the walls.",
        tags={"lantern", "stars"},
    ),
}

CAUSES = {
    "high_window": Cause(
        id="high_window",
        label="a cracked-open high window",
        clue="A wet line on the floor led straight from the window to the fallen decoration.",
        reveal="the window had been left cracked open for fresh air, and the hail had bounced in",
        places={"library", "hall"},
        tags={"window", "hail"},
    ),
    "loose_clip": Cause(
        id="loose_clip",
        label="a loose hanging clip",
        clue="One silver clip kept tapping and tapping, and it was hanging crooked.",
        reveal="the old clip had snapped when the hail shook the line",
        places={"library", "bakery", "hall"},
        tags={"clip", "hail"},
    ),
    "open_door": Cause(
        id="open_door",
        label="an open side door",
        clue="A trail of wet dots crossed the floor from the door to the decoration.",
        reveal="someone had propped the door open, and wind with hail had blown through",
        places={"bakery", "hall"},
        tags={"door", "hail"},
    ),
}


def transform_fits(decor: Decor, transform: Transform) -> bool:
    return decor.material in transform.materials


def cause_fits(place: Place, cause: Cause) -> bool:
    return cause.id in place.allows and place.id in cause.places


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for decor_id, decor in DECORS.items():
            for transform_id, transform in TRANSFORMS.items():
                if not transform_fits(decor, transform):
                    continue
                for cause_id, cause in CAUSES.items():
                    if cause_fits(place, cause):
                        combos.append((place_id, decor_id, transform_id, cause_id))
    return combos


def explain_transform(decor: Decor, transform: Transform) -> str:
    return (
        f"(No story: {transform.phrase} do not sensibly come from {decor.phrase}. "
        f"This world only allows transformations that match the damaged material.)"
    )


def explain_cause(place: Place, cause: Cause) -> str:
    return (
        f"(No story: {cause.label} does not fit {place.label}. "
        f"Pick a cause that could really happen there.)"
    )


def storm_noise(place: Place) -> str:
    return f"Then the hail {place.roof_sound}."


def predict_accident(world: World, cause_id: str) -> dict:
    sim = world.copy()
    do_hail(sim, cause_id=cause_id, narrate=False)
    decor = sim.get("decor")
    return {
        "damaged": decor.meters["damaged"] >= THRESHOLD,
        "wet": decor.meters["wet"] >= THRESHOLD,
        "holes": decor.meters["holes"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, parent1: Entity, parent2: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    parent1.memes["joy"] += 1
    parent2.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} were helping {hero.id}'s dads, {parent1.id} and {parent2.id}, "
        f"get {place.label} ready for {place.party}."
    )
    world.say(
        f"The children liked the secretive feeling of it all. Every table held a clue card, and every corner "
        f"looked as if it might be hiding a riddle."
    )
    world.say(
        f"{parent1.id} squeezed {parent2.id}'s hand and smiled. They were a gay couple, and together they made "
        f"the room feel bright and safe."
    )


def hang_decor(world: World, decor: Decor) -> None:
    world.say(
        f"Best of all was {decor.phrase}, hanging where everyone would see it first."
    )


def mystery_begins(world: World, place: Place, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(storm_noise(place))
    world.say(
        f'"Did you hear that?" whispered {friend.id}. "It sounds like a mystery beginning."'
    )


def do_hail(world: World, cause_id: str, narrate: bool = True) -> None:
    decor = world.get("decor")
    mystery = world.get("mystery")
    cause = CAUSES[cause_id]
    decor.meters["damaged"] += 1
    decor.meters["wet"] += 1
    decor.meters["holes"] += 1
    mystery.meters["mysterious"] += 1
    world.facts["culprit"] = cause
    propagate(world, narrate=narrate)


def discover_damage(world: World, decor: Decor, place: Place) -> None:
    world.say(
        f"When the hail grew quiet, the children hurried back and stopped short. {decor.phrase.capitalize()} was "
        f"{decor.damage}."
    )
    world.say(decor.clue_line)
    world.say(f"The strangest clue of all was at {place.clue_spot}.")


def inspect_clues(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"{hero.id} crouched low. {cause.clue} {friend.id} touched one icy bead and gave a little shiver."
    )
    world.say(
        f'"So it was not a mean person," said {hero.id}. "It was some kind of accident."'
    )


def reveal(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    world.get("mystery").meters["solved"] += 1
    propagate(world, narrate=False)
    hero.memes["understanding"] += 1
    friend.memes["understanding"] += 1
    world.say(
        f"Together they followed the clues and figured it out: {cause.reveal}."
    )
    world.say(
        f'"That means the damage was an accident," said {friend.id}. "And accidents can still be fixed."'
    )


def comfort(world: World, parent1: Entity, parent2: Entity, decor: Decor) -> None:
    parent1.memes["worry"] += 1
    parent2.memes["worry"] += 1
    world.say(
        f"{parent2.id} looked sadly at {decor.phrase}, but {parent1.id} knelt beside the children and said, "
        f'"We can be upset without blaming anyone. First we solve the mystery. Then we make something new."'
    )


def transform(world: World, hero: Entity, friend: Entity, decor: Decor, transform_cfg: Transform) -> None:
    decor.meters["damaged"] = 0.0
    decor.meters["transformed"] += 1
    decor.meters["beautiful"] += 1
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"So they saved {decor.final_bits} and {transform_cfg.action}. Soon the ruined decoration was becoming "
        f"{transform_cfg.phrase}."
    )


def happy_end(world: World, hero: Entity, friend: Entity, transform_cfg: Transform, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"When families arrived for {place.party}, everyone looked up and smiled."
    )
    world.say(transform_cfg.ending_image)
    world.say(
        f"{hero.id} grinned at {friend.id}. The hail had brought a mystery and an accident, but the room had ended "
        f"up even lovelier than before."
    )


def tell(
    place: Place,
    decor_cfg: Decor,
    transform_cfg: Transform,
    cause_cfg: Cause,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    friend_name: str = "Owen",
    friend_gender: str = "boy",
    dad1_name: str = "Papa Luis",
    dad2_name: str = "Papa Tom",
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent1 = world.add(Entity(id=dad1_name, kind="character", type="father", role="parent"))
    parent2 = world.add(Entity(id=dad2_name, kind="character", type="father", role="parent"))
    decor = world.add(Entity(id="decor", type="decor", label=decor_cfg.label, phrase=decor_cfg.phrase, role="decor"))
    mystery = world.add(Entity(id="mystery", type="mystery", label="the mystery", role="mystery"))

    introduce(world, hero, friend, parent1, parent2, place)
    hang_decor(world, decor_cfg)

    world.para()
    mystery_begins(world, place, hero, friend)
    comfort(world, parent1, parent2, decor_cfg)
    do_hail(world, cause_id=cause_cfg.id, narrate=False)
    discover_damage(world, decor_cfg, place)

    world.para()
    inspect_clues(world, hero, friend, cause_cfg)
    reveal(world, hero, friend, cause_cfg)

    world.para()
    transform(world, hero, friend, decor_cfg, transform_cfg)
    happy_end(world, hero, friend, transform_cfg, place)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent1=parent1,
        parent2=parent2,
        place=place,
        decor_cfg=decor_cfg,
        transform_cfg=transform_cfg,
        cause_cfg=cause_cfg,
        decor=decor,
        mystery=mystery,
        accident=True,
        solved=mystery.meters["solved"] >= THRESHOLD,
        transformed=decor.meters["transformed"] >= THRESHOLD,
        gay_family=True,
    )
    return world


KNOWLEDGE = {
    "hail": [
        (
            "What is hail?",
            "Hail is frozen rain that falls from clouds in little balls or lumps of ice. It can make a loud tapping sound when it hits roofs and windows.",
        )
    ],
    "accident": [
        (
            "What is an accident?",
            "An accident is something that goes wrong without anyone meaning to do harm. People can still fix the problem and help each other afterward.",
        )
    ],
    "gay": [
        (
            "What does gay mean?",
            "Gay is a word some people use when they love someone of the same gender. A gay couple is still a family full of care, rules, jokes, and love.",
        )
    ],
    "mystery": [
        (
            "What makes something a mystery?",
            "A mystery is something you do not understand at first. You solve it by noticing clues and thinking carefully about what happened.",
        )
    ],
    "window": [
        (
            "Why can an open window matter in a storm?",
            "An open window can let rain, wind, or hail blow inside. That can make things wet or knock them down.",
        )
    ],
    "door": [
        (
            "Why can an open door be a problem in bad weather?",
            "A strong wind can push through an open door and carry rain or hail with it. That can make a room messy very quickly.",
        )
    ],
    "clip": [
        (
            "What does a hanging clip do?",
            "A hanging clip holds paper or cloth in place. If it gets old or loose, it may snap and let the decoration fall.",
        )
    ],
    "pinwheels": [
        (
            "What is a pinwheel?",
            "A pinwheel is a paper toy or decoration with folded blades that spin in moving air. It can be made from flat paper.",
        )
    ],
    "garland": [
        (
            "What is a garland?",
            "A garland is a long decoration made to hang across a wall, doorway, or table. It can be made from ribbon, leaves, cloth, or paper.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light cover or lamp that glows softly. A paper lantern can turn tiny holes and cutouts into pretty shapes of light.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hail", "accident", "gay", "mystery", "window", "door", "clip", "pinwheels", "garland", "lantern"]


@dataclass
class StoryParams:
    place: str
    decor: str
    transform: str
    cause: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    dad1_name: str
    dad2_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="library",
        decor="paper_banner",
        transform="pinwheels",
        cause="high_window",
        hero_name="Nia",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        dad1_name="Papa Luis",
        dad2_name="Papa Tom",
    ),
    StoryParams(
        place="bakery",
        decor="fabric_banner",
        transform="ribbon_garland",
        cause="open_door",
        hero_name="Mara",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        dad1_name="Papa Joel",
        dad2_name="Papa Eli",
    ),
    StoryParams(
        place="hall",
        decor="tissue_lanterns",
        transform="star_lanterns",
        cause="loose_clip",
        hero_name="Ivy",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        dad1_name="Papa Arun",
        dad2_name="Papa Ben",
    ),
]


GIRL_NAMES = ["Nia", "Mara", "Ivy", "Lena", "Zoe", "Ava", "Mina", "Tess"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Noah", "Eli", "Sam", "Leo"]
DAD_NAMES = ["Papa Luis", "Papa Tom", "Papa Joel", "Papa Eli", "Papa Arun", "Papa Ben", "Papa Nico", "Papa Ray"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    decor = f["decor_cfg"]
    transform_cfg = f["transform_cfg"]
    cause = f["cause_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "hail", "gay", and "accident".',
        f"Tell a child-facing mystery where {hero.id} and {friend.id} help two gay dads at {place.label}, then follow clues to learn why {decor.phrase} was damaged.",
        f"Write a happy-ending transformation story where a hail accident is solved and the ruined decoration becomes {transform_cfg.phrase} because of {cause.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent1 = f["parent1"]
    parent2 = f["parent2"]
    place = f["place"]
    decor = f["decor_cfg"]
    transform_cfg = f["transform_cfg"]
    cause = f["cause_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, who were helping {hero.id}'s dads, {parent1.id} and {parent2.id}. The family was getting {place.label} ready for {place.party}.",
        ),
        (
            "What made the story feel like a mystery?",
            f"The hail made strange sounds, and afterward the children found the decoration damaged with odd clues around it. They had to notice the icy bits and the wet trail before they could understand what really happened.",
        ),
        (
            f"What happened to {decor.phrase}?",
            f"It was damaged during the storm and looked spoiled at first. The hail left it {decor.damage}, which made everyone worry.",
        ),
        (
            "Was someone mean to the decoration?",
            f"No. The children discovered it was an accident, not meanness. They followed clues and learned that {cause.reveal}.",
        ),
        (
            "How did they solve the problem?",
            f"They did not throw the damaged thing away. Instead, they saved the useful parts and turned it into {transform_cfg.phrase}.",
        ),
        (
            "How did the story end?",
            f"It ended happily at {place.party}. The new decoration looked beautiful, and the room felt even more special because the children had solved the mystery together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"hail", "accident", "gay", "mystery"}
    tags |= set(world.facts["cause_cfg"].tags)
    tags |= set(world.facts["transform_cfg"].tags)
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(D, T) :- decor(D), transform(T), made_of(D, M), uses(T, M).
cause_ok(P, C) :- place(P), cause(C), allows(P, C), happens_in(C, P).
valid(P, D, T, C) :- place(P), decor(D), transform(T), cause(C), fits(D, T), cause_ok(P, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cause_id in sorted(place.allows):
            lines.append(asp.fact("allows", place_id, cause_id))
    for decor_id, decor in DECORS.items():
        lines.append(asp.fact("decor", decor_id))
        lines.append(asp.fact("made_of", decor_id, decor.material))
    for transform_id, transform in TRANSFORMS.items():
        lines.append(asp.fact("transform", transform_id))
        for material in sorted(transform.materials):
            lines.append(asp.fact("uses", transform_id, material))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("happens_in", cause_id, place_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle mystery storyworld: hail damages a rainbow decoration, children solve the accident, and the damaged thing is transformed into something beautiful."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--decor", choices=DECORS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos() and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        if not cause_fits(PLACES[args.place], CAUSES[args.cause]):
            raise StoryError(explain_cause(PLACES[args.place], CAUSES[args.cause]))
    if args.decor and args.transform:
        if not transform_fits(DECORS[args.decor], TRANSFORMS[args.transform]):
            raise StoryError(explain_transform(DECORS[args.decor], TRANSFORMS[args.transform]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.decor is None or combo[1] == args.decor)
        and (args.transform is None or combo[2] == args.transform)
        and (args.cause is None or combo[3] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, decor, transform_id, cause = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    dads = rng.sample(DAD_NAMES, 2)
    return StoryParams(
        place=place,
        decor=decor,
        transform=transform_id,
        cause=cause,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        dad1_name=dads[0],
        dad2_name=dads[1],
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.decor not in DECORS:
        raise StoryError(f"(Unknown decor: {params.decor})")
    if params.transform not in TRANSFORMS:
        raise StoryError(f"(Unknown transform: {params.transform})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")

    place = PLACES[params.place]
    decor = DECORS[params.decor]
    transform_cfg = TRANSFORMS[params.transform]
    cause = CAUSES[params.cause]

    if not cause_fits(place, cause):
        raise StoryError(explain_cause(place, cause))
    if not transform_fits(decor, transform_cfg):
        raise StoryError(explain_transform(decor, transform_cfg))

    world = tell(
        place=place,
        decor_cfg=decor,
        transform_cfg=transform_cfg,
        cause_cfg=cause,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        dad1_name=params.dad1_name,
        dad2_name=params.dad2_name,
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
        print(f"{len(combos)} compatible (place, decor, transform, cause) combos:\n")
        for place, decor, transform_id, cause in combos:
            print(f"  {place:8} {decor:15} {transform_id:14} {cause}")
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
            header = f"### {p.place}: {p.decor} -> {p.transform} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
