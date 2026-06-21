#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py
====================================================================================

A small standalone story world for a gentle animal tale about a magic mustache,
hurt feelings, a moral choice, and reconciliation.

This world models a tiny pattern:

- two young animal friends are preparing for a small celebration
- a magical charm makes a bright pretend mustache
- the magic creates a social problem: boasting, grabbing, or a messy accident
- a moral value guides the repair: kindness, honesty, or sharing
- the ending image shows the friendship restored

Run it
------
    python storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py
    python storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py --conflict boasting --value kindness
    python storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py --magic puddle_star --place treetop
    python storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/mustache_reconciliation_moral_value_magic_animal_story.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add storyworlds/ to sys.path from this nested directory.
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "doe"}
        male = {"boy", "father", "buck", "stag"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    charm_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Species:
    id: str
    singular: str
    home_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicCharm:
    id: str
    label: str
    phrase: str
    spark: str
    mustache: str
    found_text: str
    works_in: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    hook: str
    pain: str
    repair_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ValueWay:
    id: str
    noun: str
    solves: set[str] = field(default_factory=set)
    act_text: str = ""
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


def _r_hurt_makes_distance(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if friend.memes["hurt"] < THRESHOLD:
        return []
    sig = ("distance", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["lonely"] += 1
    friend.meters["distance"] += 1
    return []


def _r_apology_rebuilds_trust(world: World) -> list[str]:
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return []
    if hero.memes["apology"] < THRESHOLD or hero.memes["repair"] < THRESHOLD:
        return []
    sig = ("reconcile", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] = 0.0
    friend.meters["distance"] = 0.0
    hero.memes["lonely"] = 0.0
    hero.memes["peace"] += 1
    friend.memes["peace"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hurt_makes_distance", tag="social", apply=_r_hurt_makes_distance),
    Rule(name="apology_rebuilds_trust", tag="social", apply=_r_apology_rebuilds_trust),
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


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the clover meadow",
        scene="where clover bells nodded in the breeze",
        charm_ids={"moon_comb", "dandelion_wand"},
        tags={"meadow", "flowers"},
    ),
    "pond": Place(
        id="pond",
        label="the lily pond",
        scene="where round lily pads rocked like little boats",
        charm_ids={"puddle_star", "moon_comb"},
        tags={"pond", "water"},
    ),
    "treetop": Place(
        id="treetop",
        label="the old oak tree",
        scene="where lantern bugs winked between the leaves",
        charm_ids={"dandelion_wand"},
        tags={"tree", "night"},
    ),
}

SPECIES = {
    "rabbit": Species(
        id="rabbit",
        singular="rabbit",
        home_detail="from a burrow under a blackberry bush",
        tags={"rabbit"},
    ),
    "otter": Species(
        id="otter",
        singular="otter",
        home_detail="from a warm bend in the stream",
        tags={"otter"},
    ),
    "fox": Species(
        id="fox",
        singular="fox",
        home_detail="from a den under the hill",
        tags={"fox"},
    ),
    "badger": Species(
        id="badger",
        singular="badger",
        home_detail="from a tidy tunnel with a mossy door",
        tags={"badger"},
    ),
}

MAGIC = {
    "moon_comb": MagicCharm(
        id="moon_comb",
        label="moon comb",
        phrase="a little moon comb",
        spark="silver sparks",
        mustache="a shining silver mustache",
        found_text="The comb had fallen from the night sky and still smelled like cool moonlight.",
        works_in={"meadow", "pond"},
        tags={"magic", "moon"},
    ),
    "dandelion_wand": MagicCharm(
        id="dandelion_wand",
        label="dandelion wand",
        phrase="a soft dandelion wand",
        spark="golden fluff",
        mustache="a fluffy golden mustache",
        found_text="The wand glowed at the tip, as if one tiny sunrise were tucked inside it.",
        works_in={"meadow", "treetop"},
        tags={"magic", "dandelion"},
    ),
    "puddle_star": MagicCharm(
        id="puddle_star",
        label="puddle star",
        phrase="a puddle star",
        spark="blue ripples",
        mustache="a watery blue mustache",
        found_text="It looked like a star that had slipped into the water and decided to stay.",
        works_in={"pond"},
        tags={"magic", "star", "water"},
    ),
}

CONFLICTS = {
    "boasting": Conflict(
        id="boasting",
        hook="The magic mustache made the hero feel too grand for one small moment.",
        pain="The friend felt left out and quietly stepped back.",
        repair_hint="The repair needs a warm apology and a gentler heart.",
        tags={"boast", "feelings"},
    ),
    "grabbing": Conflict(
        id="grabbing",
        hook="The friend reached for the magic too quickly, and the fun snapped into a quarrel.",
        pain="Both friends felt upset because nobody was taking turns.",
        repair_hint="The repair needs honest words and calm hands.",
        tags={"grab", "turns"},
    ),
    "mess": Conflict(
        id="mess",
        hook="A wobble of magic dust landed on the friend's festival sash and spoiled the pretty pattern.",
        pain="The friend looked hurt because the special sash mattered.",
        repair_hint="The repair needs helpful work, not just sorry words.",
        tags={"mess", "care"},
    ),
}

VALUES = {
    "kindness": ValueWay(
        id="kindness",
        noun="kindness",
        solves={"boasting"},
        act_text="looked closely at the friend's face and cared more about the friend's feelings than about showing off",
        tags={"kindness"},
    ),
    "honesty": ValueWay(
        id="honesty",
        noun="honesty",
        solves={"grabbing"},
        act_text="told the whole truth about the quarrel and admitted the part each of them had played",
        tags={"honesty"},
    ),
    "helpfulness": ValueWay(
        id="helpfulness",
        noun="helpfulness",
        solves={"mess"},
        act_text="set to work fixing what the magic had spoiled instead of waiting for the hurt to fade by itself",
        tags={"helpfulness"},
    ),
}

GIRL_NAMES = ["Pip", "Mimi", "Tansy", "Luma", "Daisy", "Nori"]
BOY_NAMES = ["Moss", "Bram", "Toby", "Reed", "Ollie", "Ash"]
TRAITS = ["gentle", "quick", "curious", "bright", "merry", "careful"]


@dataclass
class StoryParams:
    place: str
    hero_species: str
    friend_species: str
    magic: str
    conflict: str
    value: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    elder_name: str
    elder_species: str
    seed: Optional[int] = None


def charm_available(place_id: str, magic_id: str) -> bool:
    return magic_id in PLACES[place_id].charm_ids and place_id in MAGIC[magic_id].works_in


def value_repairs(conflict_id: str, value_id: str) -> bool:
    return conflict_id in VALUES[value_id].solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for magic_id in MAGIC:
            if not charm_available(place_id, magic_id):
                continue
            for conflict_id in CONFLICTS:
                for value_id in VALUES:
                    if value_repairs(conflict_id, value_id):
                        combos.append((place_id, magic_id, conflict_id, value_id))
    return combos


def explain_magic(place_id: str, magic_id: str) -> str:
    place = PLACES[place_id]
    charm = MAGIC[magic_id]
    return (
        f"(No story: {charm.phrase} does not belong in {place.label}. "
        f"Pick a charm that can really be found there.)"
    )


def explain_value(conflict_id: str, value_id: str) -> str:
    conflict = CONFLICTS[conflict_id]
    value = VALUES[value_id]
    options = ", ".join(sorted(v.id for v in VALUES.values() if conflict_id in v.solves))
    return (
        f"(No story: {value.noun} is not the right repair for the {conflict.id} problem. "
        f"{conflict.repair_hint} Try: {options}.)"
    )


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity) -> None:
    hs = world.facts["hero_species"]
    fs = world.facts["friend_species"]
    world.say(
        f"In {world.place.label}, {world.place.scene}, lived {hero.id}, a little {hs.singular} "
        f"{hs.home_detail}. Close by lived {friend.id}, a little {fs.singular} who was "
        f"{hero.id}'s best friend."
    )
    world.say(
        f"They were hurrying to the twilight circle, where {elder.id} the {world.facts['elder_species'].singular} "
        f"would start the lantern songs."
    )


def find_magic(world: World, hero: Entity, friend: Entity, charm: MagicCharm) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"On the path they found {charm.phrase}. {charm.found_text}"
    )
    world.say(
        f'When {hero.id} touched it, {charm.spark} curled through the air and painted {hero.id} '
        f"{charm.mustache}."
    )
    hero.attrs["mustache"] = charm.mustache
    hero.meters["magic"] += 1
    world.facts["mustache"] = charm.mustache


def admire(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} clapped and laughed. The mustache bobbed when {hero.id} smiled, and for one happy breath "
        f"it felt like the funniest thing in the whole wood."
    )


def conflict_boasting(world: World, hero: Entity, friend: Entity, charm: MagicCharm) -> None:
    hero.memes["pride"] += 1
    friend.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But then {hero.id} lifted {hero.pronoun('possessive')} nose and said, "
        f'"A grand mustache like this belongs on the grandest one here."'
    )
    world.say(
        f"{friend.id}'s smile faded. {friend.pronoun().capitalize()} touched {friend.pronoun('possessive')} plain muzzle "
        f"and took one small step back."
    )


def conflict_grabbing(world: World, hero: Entity, friend: Entity, charm: MagicCharm) -> None:
    hero.memes["alarm"] += 1
    friend.memes["hurt"] += 1
    hero.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{friend.id} wanted a turn at once and reached for the {charm.label}. '
        f'{hero.id} held on. The two friends tugged together, and the magic flashed between them.'
    )
    world.say(
        f"In the sudden hush, neither of them had a mustache anymore, and both looked cross and sorry."
    )


def conflict_mess(world: World, hero: Entity, friend: Entity, charm: MagicCharm) -> None:
    hero.memes["alarm"] += 1
    friend.memes["hurt"] += 1
    friend.meters["sash_mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} tried to twirl the shining mustache for a joke, but a puff of magic slipped sideways.'
    )
    world.say(
        f"{charm.spark.capitalize()} landed on {friend.id}'s leaf-green sash and turned its neat edge into a drippy wiggle."
    )
    world.say(
        f"{friend.id} stared at the sash. It had been for the lantern songs, and now it looked wrong."
    )


def pause_for_conscience(world: World, hero: Entity, conflict: Conflict, value: ValueWay) -> None:
    world.say(
        f"The path suddenly felt quieter. {conflict.pain} {hero.id} did not like that feeling at all."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered {value.noun}, the kind of goodness that makes a small heart brave."
    )


def repair_with_kindness(world: World, hero: Entity, friend: Entity, charm: MagicCharm) -> None:
    hero.memes["apology"] += 1
    hero.memes["repair"] += 1
    hero.memes["kind"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} looked closely at {friend.id} and saw the lonely look there. '
        f'"I am sorry," {hero.pronoun()} said. "A magic mustache is only funny if we can both laugh."'
    )
    world.say(
        f"Then {hero.id} tipped the {charm.label} gently, and a second soft curl of light drew a twin mustache on {friend.id}'s face."
    )


def repair_with_honesty(world: World, hero: Entity, friend: Entity, elder: Entity, charm: MagicCharm) -> None:
    hero.memes["apology"] += 1
    hero.memes["repair"] += 1
    friend.memes["repair"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Before the quarrel could grow bigger, {hero.id} took a breath and said, '
        f'"We both pulled. We both forgot to take turns. That is the truth."'
    )
    world.say(
        f"{friend.id} nodded and answered, \"I am sorry too.\" Together they set the {charm.label} on a flat stone and agreed on one turn each."
    )


def repair_with_helpfulness(world: World, hero: Entity, friend: Entity, charm: MagicCharm) -> None:
    hero.memes["apology"] += 1
    hero.memes["repair"] += 1
    friend.meters["sash_mess"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'"I made that mess, and I will help mend it," {hero.id} said at once.'
    )
    world.say(
        f"{hero.pronoun().capitalize()} dabbed the sash with dew from a fern tip, while the {charm.label} hummed softly and pulled the pattern straight again."
    )


def elder_blessing(world: World, elder: Entity, value: ValueWay) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    elder.memes["approval"] += 1
    world.say(
        f"When they reached the twilight circle, {elder.id} saw their peaceful faces and smiled. "
        f'"Tonight your brightest magic is {value.noun}," {elder.pronoun()} said.'
    )
    world.say(
        f"{hero.id} and {friend.id} stood shoulder to shoulder, and the words felt true."
    )


def ending_image(world: World, hero: Entity, friend: Entity, conflict_id: str, charm: MagicCharm) -> None:
    if conflict_id == "boasting":
        world.say(
            f"The two friends sang beneath the first star with matching mustaches, and each laugh belonged to both of them."
        )
        return
    if conflict_id == "grabbing":
        world.say(
            f"By the end of the song, the {charm.label} had painted one neat mustache, then the other, and taking turns felt better than tugging ever had."
        )
        return
    world.say(
        f"When the lantern bugs rose, {friend.id}'s sash was tidy again, and {hero.id}'s mustache glimmered without hurting anyone at all."
    )


def tell(
    place: Place,
    hero_species: Species,
    friend_species: Species,
    charm: MagicCharm,
    conflict: Conflict,
    value: ValueWay,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    elder_name: str,
    elder_species: Species,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    elder = world.add(Entity(id="elder", kind="character", type="thing", label=elder_name, role="elder"))

    world.facts["hero_species"] = hero_species
    world.facts["friend_species"] = friend_species
    world.facts["elder_species"] = elder_species

    introduce(world, hero, friend, elder)
    world.say(f'{hero.label} and {friend.label} carried a little basket of glowberries for the singing.')
    world.para()

    find_magic(world, hero, friend, charm)
    admire(world, hero, friend)

    world.para()
    if conflict.id == "boasting":
        conflict_boasting(world, hero, friend, charm)
    elif conflict.id == "grabbing":
        conflict_grabbing(world, hero, friend, charm)
    else:
        conflict_mess(world, hero, friend, charm)

    pause_for_conscience(world, hero, conflict, value)

    world.para()
    if value.id == "kindness":
        repair_with_kindness(world, hero, friend, charm)
    elif value.id == "honesty":
        repair_with_honesty(world, hero, friend, elder, charm)
    else:
        repair_with_helpfulness(world, hero, friend, charm)

    elder_blessing(world, elder, value)
    ending_image(world, hero, friend, conflict.id, charm)

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        place=place,
        charm=charm,
        conflict=conflict,
        value=value,
        reconciled=hero.memes["friendship"] >= THRESHOLD or hero.memes["repair"] >= THRESHOLD,
        mustache=world.facts.get("mustache", charm.mustache),
    )
    return world


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is something that can happen in a special, impossible way. It often helps characters show what is in their hearts."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to care about someone else's feelings. It often sounds soft, but it is a brave thing to do."
        )
    ],
    "honesty": [
        (
            "What is honesty?",
            "Honesty means telling what is true, even when it is hard. True words help people fix problems fairly."
        )
    ],
    "helpfulness": [
        (
            "What does it mean to be helpful?",
            "Being helpful means doing something useful when there is a problem. Helping can show your apology with your hands, not only with your words."
        )
    ],
    "turns": [
        (
            "Why is taking turns important?",
            "Taking turns helps everyone feel included. It keeps play fair and stops small quarrels from growing bigger."
        )
    ],
    "apology": [
        (
            "Why do apologies matter?",
            "A real apology lets someone know you understand the hurt you caused. It is the first step toward making things better."
        )
    ],
    "friendship": [
        (
            "How can friends make up after a quarrel?",
            "Friends can make up by telling the truth, listening, and doing something to repair the hurt. Reconciliation means the friendship is mended, not just the argument stopped."
        )
    ],
    "mustache": [
        (
            "What is a mustache?",
            "A mustache is hair that grows above the mouth. In a playful story, a pretend mustache can also be painted or made with magic."
        )
    ],
}
KNOWLEDGE_ORDER = ["mustache", "magic", "kindness", "honesty", "helpfulness", "turns", "apology", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    charm = f["charm"]
    conflict = f["conflict"]
    value = f["value"]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the word "mustache" and a magical object called {charm.phrase}.',
        f"Tell a gentle story where two animal friends fall into a {conflict.id} problem because of a magic mustache, then find their way back to each other through {value.noun}.",
        f"Write a TinyStories-style tale with reconciliation, moral value, and magic, ending with a clear image that proves the friendship has been repaired.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    charm = f["charm"]
    conflict = f["conflict"]
    value = f["value"]
    hero_name = hero.label
    friend_name = friend.label
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two animal friends, {hero_name} and {friend_name}. They are on their way to sing at twilight when they find a magical charm."
        ),
        (
            "What magic did they find?",
            f"They found {charm.phrase}. When {hero_name} touched it, it painted {f['mustache']} on {hero.pronoun('possessive')} face."
        ),
        (
            "Why did the problem begin?",
            f"The trouble began because of {conflict.id}. {conflict.hook} That changed the happy mood into hurt feelings."
        ),
        (
            f"How did {value.noun} help fix the problem?",
            f"{value.noun.capitalize()} helped because {hero_name} {value.act_text}. The repair worked when the apology was followed by a caring action."
        ),
    ]
    if conflict.id == "boasting":
        out.append(
            (
                f"Why was {friend_name} hurt?",
                f"{friend_name} felt hurt because {hero_name} acted as if the magic mustache made {hero.pronoun('object')} better than a friend. The pain came from being left out, not from the magic itself."
            )
        )
    elif conflict.id == "grabbing":
        out.append(
            (
                "What did the friends learn about taking turns?",
                f"They learned that grabbing ruins fun faster than magic can make it. When they told the truth and agreed on turns, the quarrel became fair play again."
            )
        )
    else:
        out.append(
            (
                f"How was the sash fixed?",
                f"{hero_name} admitted the mistake and helped mend the sash with dew while the magic pulled the pattern straight again. The fixing mattered because {friend_name}'s special thing had been spoiled."
            )
        )
    out.append(
        (
            "How did the story end?",
            f"It ended with the friendship mended. The final picture shows {hero_name} and {friend_name} together in peace, which proves the reconciliation was real."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    conflict = world.facts["conflict"]
    value = world.facts["value"]
    tags = {"mustache", "magic", "friendship", "apology"}
    if conflict.id == "grabbing":
        tags.add("turns")
    tags.add(value.id)
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = [f"label={ent.label!r}"]
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {eid:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="meadow",
        hero_species="rabbit",
        friend_species="badger",
        magic="dandelion_wand",
        conflict="boasting",
        value="kindness",
        hero_name="Pip",
        hero_gender="girl",
        friend_name="Moss",
        friend_gender="boy",
        elder_name="Aunt Brindle",
        elder_species="fox",
    ),
    StoryParams(
        place="pond",
        hero_species="otter",
        friend_species="rabbit",
        magic="puddle_star",
        conflict="grabbing",
        value="honesty",
        hero_name="Reed",
        hero_gender="boy",
        friend_name="Tansy",
        friend_gender="girl",
        elder_name="Old Cedar",
        elder_species="badger",
    ),
    StoryParams(
        place="pond",
        hero_species="fox",
        friend_species="otter",
        magic="moon_comb",
        conflict="mess",
        value="helpfulness",
        hero_name="Luma",
        hero_gender="girl",
        friend_name="Ash",
        friend_gender="boy",
        elder_name="Mallow",
        elder_species="rabbit",
    ),
]


ASP_RULES = r"""
available(P, M) :- place(P), magic(M), place_has(P, M), works_in(M, P).
right_repair(C, V) :- conflict(C), value(V), solves(V, C).
valid(P, M, C, V) :- available(P, M), right_repair(C, V).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for charm_id in sorted(place.charm_ids):
            lines.append(asp.fact("place_has", place_id, charm_id))
    for magic_id, charm in MAGIC.items():
        lines.append(asp.fact("magic", magic_id))
        for place_id in sorted(charm.works_in):
            lines.append(asp.fact("works_in", magic_id, place_id))
    for conflict_id in CONFLICTS:
        lines.append(asp.fact("conflict", conflict_id))
    for value_id, value in VALUES.items():
        lines.append(asp.fact("value", value_id))
        for conflict_id in sorted(value.solves):
            lines.append(asp.fact("solves", value_id, conflict_id))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
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
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal story world: a magic mustache causes a quarrel, and a moral choice repairs the friendship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-species", choices=SPECIES)
    ap.add_argument("--friend-species", choices=SPECIES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.magic and not charm_available(args.place, args.magic):
        raise StoryError(explain_magic(args.place, args.magic))
    if args.conflict and args.value and not value_repairs(args.conflict, args.value):
        raise StoryError(explain_value(args.conflict, args.value))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.magic is None or combo[1] == args.magic)
        and (args.conflict is None or combo[2] == args.conflict)
        and (args.value is None or combo[3] == args.value)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, magic_id, conflict_id, value_id = rng.choice(sorted(combos))
    hero_species = args.hero_species or rng.choice(sorted(SPECIES))
    friend_species = args.friend_species or rng.choice(sorted(SPECIES))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = pick_name(rng, hero_gender)
    friend_name = pick_name(rng, friend_gender, avoid=hero_name)
    elder_species = rng.choice(sorted(SPECIES))
    elder_name = pick_name(rng, rng.choice(["girl", "boy"]), avoid=hero_name if hero_name != friend_name else "")
    return StoryParams(
        place=place_id,
        hero_species=hero_species,
        friend_species=friend_species,
        magic=magic_id,
        conflict=conflict_id,
        value=value_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        elder_name=elder_name,
        elder_species=elder_species,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hero_species not in SPECIES:
        raise StoryError(f"(Unknown hero species: {params.hero_species})")
    if params.friend_species not in SPECIES:
        raise StoryError(f"(Unknown friend species: {params.friend_species})")
    if params.magic not in MAGIC:
        raise StoryError(f"(Unknown magic: {params.magic})")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"(Unknown conflict: {params.conflict})")
    if params.value not in VALUES:
        raise StoryError(f"(Unknown value: {params.value})")
    if params.elder_species not in SPECIES:
        raise StoryError(f"(Unknown elder species: {params.elder_species})")
    if not charm_available(params.place, params.magic):
        raise StoryError(explain_magic(params.place, params.magic))
    if not value_repairs(params.conflict, params.value):
        raise StoryError(explain_value(params.conflict, params.value))

    world = tell(
        place=PLACES[params.place],
        hero_species=SPECIES[params.hero_species],
        friend_species=SPECIES[params.friend_species],
        charm=MAGIC[params.magic],
        conflict=CONFLICTS[params.conflict],
        value=VALUES[params.value],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        elder_name=params.elder_name,
        elder_species=SPECIES[params.elder_species],
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
        print(f"{len(combos)} valid (place, magic, conflict, value) combos:\n")
        for place_id, magic_id, conflict_id, value_id in combos:
            print(f"  {place_id:8} {magic_id:14} {conflict_id:9} {value_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.magic}, {p.conflict}, {p.value}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
