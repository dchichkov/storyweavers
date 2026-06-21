#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/communion_magic_conflict_slice_of_life.py
====================================================================

A small story world about a child on a communion morning: a treasured object,
a little quarrel, a minor accident, and a gentle magical repair that helps the
family step back into the day together.

The domain aims for a slice-of-life feeling first: kitchen light, careful hands,
soft clothes, a cousin or sibling underfoot, and a grown-up who fixes both the
object and the mood. The "magic" stays domestic and child-facing: a hum, a warm
teacup, a silver pin, a spoon that seems to know just where to lift the wax.

Reasonableness gate
-------------------
Not every mishap fits every keepsake, and not every repair fits every material.

- A ribbon knot makes sense for cloth and ribbon items, not paper prayer cards.
- A crease makes sense for paper, not lace veils.
- A wax spot makes sense near a candle, chiefly on the ribbon tied to it.
- A repair must match the mishap and the material.

The world model rejects mismatched combinations instead of producing weak prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/communion_magic_conflict_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/communion_magic_conflict_slice_of_life.py --place parish_hall --keepsake candle_bow --mishap wax_spot
    python storyworlds/worlds/gpt-5.4/communion_magic_conflict_slice_of_life.py --keepsake prayer_card --mishap knot
    python storyworlds/worlds/gpt-5.4/communion_magic_conflict_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/communion_magic_conflict_slice_of_life.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    phrase: str
    close: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    material: str
    article: str
    vulnerable_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    label: str
    damage_key: str
    text: str
    cause: str
    materials: set[str] = field(default_factory=set)
    place_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    fixes: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
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


def _r_damage_feelings(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("keepsake")
    child = world.entities.get("child")
    cousin = world.entities.get("cousin")
    room = world.entities.get("room")
    if item is None or child is None or cousin is None or room is None:
        return out
    if item.meters["damaged"] < THRESHOLD:
        return out
    sig = ("damage_feelings", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    cousin.memes["guilt"] += 1
    room.memes["hush"] += 1
    return out


def _r_repair_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("keepsake")
    child = world.entities.get("child")
    cousin = world.entities.get("cousin")
    if item is None or child is None or cousin is None:
        return out
    if item.meters["fixed"] < THRESHOLD:
        return out
    sig = ("repair_relief", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    cousin.memes["relief"] += 1
    child.memes["forgiveness"] += 1
    cousin.memes["forgiveness"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="damage_feelings", tag="social", apply=_r_damage_feelings),
    Rule(name="repair_relief", tag="social", apply=_r_repair_relief),
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
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "bedroom": Place(
        id="bedroom",
        phrase="the small bedroom at the end of the hall",
        close="the bedroom door stood open to the bright hall",
        affords={"knot", "crease"},
        tags={"home", "quiet"},
    ),
    "kitchen": Place(
        id="kitchen",
        phrase="the sunny kitchen",
        close="the tea kettle whispered on the stove",
        affords={"crease"},
        tags={"home", "tea"},
    ),
    "parish_hall": Place(
        id="parish_hall",
        phrase="the parish hall beside the church",
        close="soft voices drifted in from the church doors",
        affords={"knot", "wax_spot"},
        tags={"church", "crowded"},
    ),
    "chapel_steps": Place(
        id="chapel_steps",
        phrase="the chapel steps in the cool morning air",
        close="bells rang once, small and silver, above the stone steps",
        affords={"knot", "wax_spot"},
        tags={"church", "outdoor"},
    ),
}

KEEPSAKES = {
    "sash": Keepsake(
        id="sash",
        label="sash",
        phrase="a white communion sash with a tiny silver cross",
        material="cloth",
        article="the",
        vulnerable_to={"knot"},
        tags={"sash", "cloth", "communion"},
    ),
    "veil": Keepsake(
        id="veil",
        label="veil",
        phrase="a lace communion veil soft as milk foam",
        material="cloth",
        article="the",
        vulnerable_to={"knot"},
        tags={"veil", "cloth", "communion"},
    ),
    "prayer_card": Keepsake(
        id="prayer_card",
        label="prayer card",
        phrase="a cream prayer card edged in gold",
        material="paper",
        article="the",
        vulnerable_to={"crease"},
        tags={"prayer_card", "paper", "communion"},
    ),
    "candle_bow": Keepsake(
        id="candle_bow",
        label="ribbon on the candle",
        phrase="a satin bow tied around the communion candle",
        material="ribbon",
        article="the",
        vulnerable_to={"knot", "wax_spot"},
        tags={"candle", "ribbon", "communion"},
    ),
}

MISHAPS = {
    "knot": Mishap(
        id="knot",
        label="knot",
        damage_key="tangled",
        text="twisted into a hard little knot",
        cause="both children grabbed at once",
        materials={"cloth", "ribbon"},
        place_tags={"bedroom", "parish_hall", "chapel_steps"},
        tags={"knot", "conflict"},
    ),
    "crease": Mishap(
        id="crease",
        label="crease",
        damage_key="creased",
        text="came back with a sharp bend across the middle",
        cause="small hands squeezed it too fast",
        materials={"paper"},
        place_tags={"bedroom", "kitchen"},
        tags={"paper", "conflict"},
    ),
    "wax_spot": Mishap(
        id="wax_spot",
        label="wax spot",
        damage_key="spotted",
        text="caught a pearly drop of wax",
        cause="the candle tipped for one breath",
        materials={"ribbon"},
        place_tags={"parish_hall", "chapel_steps"},
        tags={"wax", "conflict"},
    ),
}

REPAIRS = {
    "silver_hum": Repair(
        id="silver_hum",
        label="silver hum",
        fixes={"knot"},
        materials={"cloth", "ribbon"},
        text="laid the ribbon across a warm lap, touched the knot with a silver hairpin, and hummed so softly that the twist seemed to remember how to lie flat again",
        qa_text="used a silver pin and a low hum to loosen the knot",
        tags={"repair", "magic", "cloth"},
    ),
    "book_press": Repair(
        id="book_press",
        label="book press",
        fixes={"crease"},
        materials={"paper"},
        text="slid the prayer card between two clean napkins, rested the family missal on top, and whispered a blessing while the bent paper slowly flattened",
        qa_text="pressed the prayer card flat under the missal while whispering a blessing",
        tags={"repair", "magic", "paper"},
    ),
    "spoon_lift": Repair(
        id="spoon_lift",
        label="spoon lift",
        fixes={"wax_spot"},
        materials={"ribbon"},
        text="cooled a spoon against a teacup, lifted the wax away in one careful curl, and breathed over the satin until its shine came back",
        qa_text="lifted the wax away with a cool spoon and smoothed the satin",
        tags={"repair", "magic", "wax"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Sofia", "Nina", "Rosa", "Eva", "Clara", "Mila"]
BOY_NAMES = ["Leo", "Tomas", "Noel", "Evan", "Milo", "Sam", "Jonah", "Ben"]
TRAITS = ["careful", "hopeful", "fidgety", "gentle", "earnest", "bright"]


def mishap_fits(place: Place, keepsake: Keepsake, mishap: Mishap) -> bool:
    return (
        mishap.id in place.affords
        and keepsake.material in mishap.materials
        and mishap.id in keepsake.vulnerable_to
        and place.id in mishap.place_tags
    )


def repair_fits(keepsake: Keepsake, mishap: Mishap, repair: Repair) -> bool:
    return (
        mishap.id in repair.fixes
        and keepsake.material in repair.materials
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            for mishap_id, mishap in MISHAPS.items():
                if not mishap_fits(place, keepsake, mishap):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(keepsake, mishap, repair):
                        combos.append((place_id, keepsake_id, mishap_id, repair_id))
    return combos


@dataclass
class StoryParams:
    place: str
    keepsake: str
    mishap: str
    repair: str
    child_name: str
    child_gender: str
    cousin_name: str
    cousin_gender: str
    helper: str
    trait: str
    relation: str = "cousin"
    seed: Optional[int] = None


def opening_detail(place: Place) -> str:
    if place.id == "bedroom":
        return "Buttons winked on the bedspread, and white clothes waited on padded hangers."
    if place.id == "kitchen":
        return "The table smelled of sweet bread and oranges, and sunlight lay in yellow squares on the floor."
    if place.id == "parish_hall":
        return "Paper flowers trembled on the long tables while families moved past with careful smiles."
    return "The stone still held the night's coolness, and everyone spoke in the soft voice people save for church mornings."


def introduce(world: World, child: Entity, cousin: Entity, helper: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"On the morning of {child.id}'s communion, the family moved through {world.place.phrase} in their good shoes and quiet voices."
    )
    world.say(opening_detail(world.place))
    world.say(
        f"{child.id} kept looking at {keepsake.phrase}. It felt important in the way small beautiful things do when a day matters very much."
    )
    if world.place.id in {"parish_hall", "chapel_steps"}:
        world.say(
            f"{cousin.id} stayed close, curious about everything, while {helper.label_word} carried a bag with tissues, safety pins, and all the other little things grown-ups remember."
        )
    else:
        world.say(
            f"{cousin.id} hovered nearby, curious and a little bouncy, while {helper.label_word} moved from chair to mirror making small last-minute fixes."
        )


def admire(world: World, child: Entity, cousin: Entity, keepsake: Keepsake) -> None:
    child.memes["pride"] += 1
    cousin.memes["interest"] += 1
    world.say(
        f'"Can I hold it for one second?" {cousin.id} asked.'
    )
    world.say(
        f'{child.id} hugged {keepsake.article} {keepsake.label} closer. "Just be careful," {child.pronoun()} said.'
    )


def quarrel(world: World, child: Entity, cousin: Entity, keepsake: Keepsake, mishap: Mishap) -> None:
    child.memes["defiance"] += 1
    cousin.memes["defiance"] += 1
    world.say(
        f"But careful was hard to manage with excitement buzzing in both of them. {cousin.id} reached again, {child.id} pulled back, and for one unhappy moment {mishap.cause}."
    )
    if mishap.id == "knot":
        world.say(
            f"When they looked down, {keepsake.article} {keepsake.label} had {mishap.text}."
        )
    elif mishap.id == "crease":
        world.say(
            f"When {child.id} snatched it back, {keepsake.article} {keepsake.label} {mishap.text}."
        )
    else:
        world.say(
            f"When they both froze, {keepsake.article} {keepsake.label} had {mishap.text}."
        )


def damage(world: World, keepsake_ent: Entity, mishap: Mishap) -> None:
    keepsake_ent.meters["damaged"] += 1
    keepsake_ent.meters[mishap.damage_key] += 1
    propagate(world, narrate=False)


def hush(world: World, child: Entity, cousin: Entity, helper: Entity, keepsake: Keepsake, mishap: Mishap) -> None:
    room = world.get("room")
    if room.memes["hush"] >= THRESHOLD:
        world.say(
            f"The room seemed to go still around them. {child.id}'s eyes filled at once, and {cousin.id} looked at the floor as if it might kindly open up and hide {cousin.pronoun('object')}."
        )
    world.say(
        f'"Oh no," {child.id} whispered. "{keepsake.article.capitalize()} {keepsake.label} was for communion."'
    )
    world.say(
        f'{helper.label_word.capitalize()} came over at once, not cross, just quick and calm. "{mishap.label.capitalize()} first, tears second," {helper.pronoun()} said. "Let me see."'
    )


def apology(world: World, child: Entity, cousin: Entity) -> None:
    cousin.memes["guilt"] += 1
    child.memes["hurt"] += 1
    world.say(
        f'"I am sorry," {cousin.id} said in a small voice. "I only wanted to help."'
    )
    world.say(
        f'{child.id} swallowed hard. "{cousin.id}, I should have let you look without tugging," {child.pronoun()} said.'
    )


def repair_scene(world: World, helper: Entity, keepsake_ent: Entity, keepsake: Keepsake, repair: Repair) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label_word.capitalize()} smiled the way grown-ups do when they have already decided a thing can be mended."
    )
    world.say(
        f"{helper.pronoun().capitalize()} {repair.text}."
    )
    keepsake_ent.meters["damaged"] = 0.0
    keepsake_ent.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In another breath, {keepsake.article} {keepsake.label} looked right again, as if it had only needed patient hands and a little morning magic."
    )


def reconcile(world: World, child: Entity, cousin: Entity, helper: Entity, keepsake: Keepsake) -> None:
    child.memes["peace"] += 1
    cousin.memes["peace"] += 1
    world.say(
        f'{cousin.id} reached out this time with open palms. "You can carry it," {cousin.pronoun()} said. "I can walk beside you."'
    )
    world.say(
        f'{child.id} nodded and let {cousin.pronoun("object")} straighten one edge. That small job was enough to make them both smile.'
    )
    if world.place.id in {"parish_hall", "chapel_steps"}:
        world.say(
            f"Together they walked toward the church doors, slower now. The bells sounded again, and {child.id} stepped into the communion day with {keepsake.article} {keepsake.label} safe and {cousin.id} close beside {child.pronoun('object')}."
        )
    elif world.place.id == "kitchen":
        world.say(
            f"They went back to the table where the sweet bread waited. Steam rose from the tea, orange peels shone in a bowl, and the morning felt settled again before it was time to leave for communion."
        )
    else:
        world.say(
            f"They left the room hand in hand, following {helper.label_word} down the bright hall. White sleeves brushed together, and the whole house seemed gentler on the way out to communion."
        )


def tell(
    place: Place,
    keepsake: Keepsake,
    mishap: Mishap,
    repair: Repair,
    child_name: str = "Lina",
    child_gender: str = "girl",
    cousin_name: str = "Leo",
    cousin_gender: str = "boy",
    helper_type: str = "grandmother",
    trait: str = "hopeful",
    relation: str = "cousin",
) -> World:
    world = World(place=place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"name": child_name, "trait": trait},
    ))
    cousin = world.add(Entity(
        id="cousin",
        kind="character",
        type=cousin_gender,
        label=cousin_name,
        phrase=cousin_name,
        role="cousin",
        attrs={"name": cousin_name, "relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        phrase=helper_type,
        role="helper",
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=keepsake.label,
        phrase=keepsake.phrase,
        role="keepsake",
        attrs={"material": keepsake.material},
        tags=set(keepsake.tags),
    ))
    world.add(Entity(id="room", kind="thing", type="room", label=place.phrase))

    introduce(world, child, cousin, helper, keepsake)
    world.para()
    admire(world, child, cousin, keepsake)
    quarrel(world, child, cousin, keepsake, mishap)
    damage(world, keepsake_ent, mishap)
    hush(world, child, cousin, helper, keepsake, mishap)
    world.para()
    apology(world, child, cousin)
    repair_scene(world, helper, keepsake_ent, keepsake, repair)
    reconcile(world, child, cousin, helper, keepsake)

    outcome = "mended"
    world.facts.update(
        place=place,
        keepsake_cfg=keepsake,
        keepsake=keepsake_ent,
        mishap=mishap,
        repair=repair,
        child=child,
        cousin=cousin,
        helper=helper,
        child_name=child_name,
        cousin_name=cousin_name,
        relation=relation,
        outcome=outcome,
        damage_seen=True,
        repaired=keepsake_ent.meters["fixed"] >= THRESHOLD,
        calm=helper.memes["calm"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "communion": [
        (
            "What is communion?",
            "Communion is a church service where people remember Jesus in a special way. Families often dress carefully and treat the day as holy and important."
        )
    ],
    "veil": [
        (
            "What is a veil?",
            "A veil is a light piece of fabric worn over the hair or head. It can be part of special clothes for a ceremony."
        )
    ],
    "sash": [
        (
            "What is a sash?",
            "A sash is a long strip of cloth worn neatly over clothes or around the waist. It can make special clothes look finished."
        )
    ],
    "prayer_card": [
        (
            "What is a prayer card?",
            "A prayer card is a small card with a prayer or holy picture on it. People sometimes keep one in a pocket or book during a church day."
        )
    ],
    "candle": [
        (
            "Why do people use candles at special times?",
            "Candles can stand for light, hope, and prayer. At a ceremony, they help the moment feel quiet and meaningful."
        )
    ],
    "paper": [
        (
            "Why does paper crease easily?",
            "Paper bends when it is squeezed or folded too hard. That is why careful hands help paper stay smooth."
        )
    ],
    "wax": [
        (
            "What happens when candle wax drips?",
            "Warm wax falls as a little drop and then cools into a solid piece. It can stick to ribbon or cloth if it lands there."
        )
    ],
    "repair": [
        (
            "Why do careful repairs matter?",
            "Careful repairs save important things without making the damage worse. They also help people slow down and be gentle again."
        )
    ],
    "magic": [
        (
            "What kind of magic is in this story?",
            "It is soft home magic, the kind that feels like patience, humming, and kind hands. It does not replace care; it works together with care."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "communion",
    "veil",
    "sash",
    "prayer_card",
    "candle",
    "paper",
    "wax",
    "repair",
    "magic",
]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cousin = f["cousin"]
    keepsake = f["keepsake_cfg"]
    mishap = f["mishap"]
    place = f["place"]
    helper = f["helper"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "communion", a tiny magical repair, and a brief quarrel between children.',
        f"Tell a gentle family story set in {place.phrase} where {display_name(child)} and {display_name(cousin)} argue over {keepsake.phrase}, something goes wrong, and {helper.label_word} fixes both the object and the mood.",
        f"Write a calm magical story about a communion morning where a {mishap.label} threatens an important keepsake, but patient hands and a little wonder set things right."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    cousin = f["cousin"]
    helper = f["helper"]
    keepsake = f["keepsake_cfg"]
    mishap = f["mishap"]
    repair = f["repair"]
    place = f["place"]
    child_name = display_name(child)
    cousin_name = display_name(cousin)
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name} on the morning of communion, {cousin_name} who wanted to help, and {helper_word} who stayed calm when something went wrong."
        ),
        (
            "What important thing did the child keep looking at?",
            f"{child_name} kept looking at {keepsake.phrase}. It mattered because communion felt like a big day, and the keepsake was part of that special morning."
        ),
        (
            f"What caused the problem with the {keepsake.label}?",
            f"The problem started when the two children argued and moved too fast. {mishap.cause.capitalize()}, so the {keepsake.label} {mishap.text}."
        ),
        (
            f"How did {helper_word} help?",
            f"{helper_word.capitalize()} did not scold first; {helper.pronoun()} came over calm and ready to mend things. Then {helper.pronoun()} {repair.qa_text}, which fixed the keepsake and helped everyone breathe again."
        ),
        (
            "How did the children make peace?",
            f"They both apologized and stopped pulling against each other. After the repair, one child carried the keepsake while the other walked beside, which showed the quarrel had turned into teamwork."
        ),
    ]
    if place.id in {"parish_hall", "chapel_steps"}:
        qa.append(
            (
                "How did the ending show that the morning had changed?",
                f"At the end, they walked toward church more slowly and gently than before. The safe keepsake and the quiet walk beside each other showed the communion morning had settled."
            )
        )
    else:
        qa.append(
            (
                "How did the ending show that the morning had changed?",
                f"At the end, the house felt calm again instead of tense. The children moved together and the family was ready to leave for communion without the earlier fuss."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"communion", "repair", "magic"}
    tags |= set(f["keepsake_cfg"].tags)
    tags |= set(f["mishap"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bedroom",
        keepsake="veil",
        mishap="knot",
        repair="silver_hum",
        child_name="Rosa",
        child_gender="girl",
        cousin_name="Leo",
        cousin_gender="boy",
        helper="grandmother",
        trait="hopeful",
        relation="cousin",
    ),
    StoryParams(
        place="kitchen",
        keepsake="prayer_card",
        mishap="crease",
        repair="book_press",
        child_name="Noel",
        child_gender="boy",
        cousin_name="Mila",
        cousin_gender="girl",
        helper="mother",
        trait="earnest",
        relation="sister",
    ),
    StoryParams(
        place="parish_hall",
        keepsake="candle_bow",
        mishap="wax_spot",
        repair="spoon_lift",
        child_name="Clara",
        child_gender="girl",
        cousin_name="Ben",
        cousin_gender="boy",
        helper="aunt",
        trait="gentle",
        relation="cousin",
    ),
    StoryParams(
        place="chapel_steps",
        keepsake="candle_bow",
        mishap="knot",
        repair="silver_hum",
        child_name="Tomas",
        child_gender="boy",
        cousin_name="Eva",
        cousin_gender="girl",
        helper="father",
        trait="bright",
        relation="cousin",
    ),
    StoryParams(
        place="bedroom",
        keepsake="sash",
        mishap="knot",
        repair="silver_hum",
        child_name="Lina",
        child_gender="girl",
        cousin_name="Sam",
        cousin_gender="boy",
        helper="grandmother",
        trait="careful",
        relation="brother",
    ),
]


def explain_rejection(place: Place, keepsake: Keepsake, mishap: Mishap, repair: Optional[Repair] = None) -> str:
    if mishap.id not in place.affords or place.id not in mishap.place_tags:
        return (
            f"(No story: a {mishap.label} is not a good fit for {place.phrase}. "
            f"That place does not naturally support this little accident on communion morning.)"
        )
    if keepsake.material not in mishap.materials or mishap.id not in keepsake.vulnerable_to:
        return (
            f"(No story: {keepsake.phrase} is made of {keepsake.material}, so a {mishap.label} does not make good sense for it.)"
        )
    if repair is not None and not repair_fits(keepsake, mishap, repair):
        return (
            f"(No story: the repair '{repair.id}' does not match a {mishap.label} on {keepsake.material}. Pick a repair that really fixes the problem.)"
        )
    return "(No story: this combination does not form a reasonable mishap and repair.)"


ASP_RULES = r"""
% A mishap is plausible in a place when the place affords it.
place_supports(P, M) :- affords(P, M), mishap_place(P, M).

% A mishap fits a keepsake when the material matches and the keepsake is vulnerable to it.
mishap_fits(P, K, M) :- place(P), keepsake(K), mishap(M),
                        place_supports(P, M),
                        material(K, Mat), mishap_material(M, Mat),
                        vulnerable(K, M).

% A repair fits when it fixes the mishap and can work on the keepsake's material.
repair_fits(K, M, R) :- keepsake(K), mishap(M), repair(R),
                        material(K, Mat), repair_material(R, Mat),
                        fixes(R, M).

valid(P, K, M, R) :- mishap_fits(P, K, M), repair_fits(K, M, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for mishap_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, mishap_id))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("material", keepsake_id, keepsake.material))
        for mishap_id in sorted(keepsake.vulnerable_to):
            lines.append(asp.fact("vulnerable", keepsake_id, mishap_id))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        for mat in sorted(mishap.materials):
            lines.append(asp.fact("mishap_material", mishap_id, mat))
        for place_id in sorted(mishap.place_tags):
            lines.append(asp.fact("mishap_place", place_id, mishap_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for mishap_id in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair_id, mishap_id))
        for mat in sorted(repair.materials):
            lines.append(asp.fact("repair_material", repair_id, mat))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if "communion" not in sample.story.lower():
                raise StoryError("story omitted the seed word 'communion'")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a communion morning, a small quarrel, and a magical repair."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [name for name in names if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.keepsake and args.mishap:
        place = PLACES[args.place]
        keepsake = KEEPSAKES[args.keepsake]
        mishap = MISHAPS[args.mishap]
        if not mishap_fits(place, keepsake, mishap):
            raise StoryError(explain_rejection(place, keepsake, mishap))
    if args.place and args.keepsake and args.mishap and args.repair:
        place = PLACES[args.place]
        keepsake = KEEPSAKES[args.keepsake]
        mishap = MISHAPS[args.mishap]
        repair = REPAIRS[args.repair]
        if not (mishap_fits(place, keepsake, mishap) and repair_fits(keepsake, mishap, repair)):
            raise StoryError(explain_rejection(place, keepsake, mishap, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.mishap is None or combo[2] == args.mishap)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, keepsake_id, mishap_id, repair_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    cousin_name, cousin_gender = _pick_child(rng, avoid=child_name)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "aunt"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["cousin", "brother", "sister"])
    return StoryParams(
        place=place_id,
        keepsake=keepsake_id,
        mishap=mishap_id,
        repair=repair_id,
        child_name=child_name,
        child_gender=child_gender,
        cousin_name=cousin_name,
        cousin_gender=cousin_gender,
        helper=helper,
        trait=trait,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.mishap not in MISHAPS:
        raise StoryError(f"(Unknown mishap: {params.mishap})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    place = PLACES[params.place]
    keepsake = KEEPSAKES[params.keepsake]
    mishap = MISHAPS[params.mishap]
    repair = REPAIRS[params.repair]
    if not mishap_fits(place, keepsake, mishap):
        raise StoryError(explain_rejection(place, keepsake, mishap))
    if not repair_fits(keepsake, mishap, repair):
        raise StoryError(explain_rejection(place, keepsake, mishap, repair))

    world = tell(
        place=place,
        keepsake=keepsake,
        mishap=mishap,
        repair=repair,
        child_name=params.child_name,
        child_gender=params.child_gender,
        cousin_name=params.cousin_name,
        cousin_gender=params.cousin_gender,
        helper_type=params.helper,
        trait=params.trait,
        relation=params.relation,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, keepsake, mishap, repair) combos:\n")
        for place, keepsake, mishap, repair in combos:
            print(f"  {place:12} {keepsake:12} {mishap:10} {repair}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.keepsake} in {p.place} ({p.mishap} -> {p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
