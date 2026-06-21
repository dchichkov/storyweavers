#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py
================================================================================================

A standalone story world for a pirate-flavored tale about friendship, bravery,
and reconciliation. Two children play pirates, quarrel over a treasure clue,
and one hides a painful injury from pride. A calm grown-up helper treats the
wound sensibly, tells the child to elevate the hurt limb, and the friends make
up before sailing back into play together.

The world models:
- physical meters: pain, limp, swelling, infected, cleaned, bandaged, danger
- emotional memes: pride, fear, trust, guilt, courage, relief, friendship

The keyword "abscessed" appears when a puncture-type wound is left untreated long
enough to become infected. The keyword "elevate" appears in the helper's care
instructions when the hurt body part is one that should be raised on a pillow or stool.

Run it
------
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py --deck cove --injury shell_cut --care rinse_bandage
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py --injury rope_burn --care rinse_bandage
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py --care treasure_song
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/abscessed_elevate_reconciliation_friendship_bravery_pirate_tale.py --qa --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "mother", "aunt", "woman", "nurse"}
        male = {"boy", "father", "uncle", "man", "doctor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}
        return mapping.get(self.type, self.type or self.label)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Deck:
    id: str
    scene: str
    rig: str
    hunt: str
    dark_or_wild: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Injury:
    id: str
    label: str
    body_part: str
    article_part: str
    cause: str
    sharp: bool
    can_abscess: bool
    needs_elevate: bool
    severity: int
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def object_phrase(self) -> str:
        return f"the hurt {self.body_part}"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Care:
    id: str
    sense: int
    power: int
    works_for: set[str]
    text: str
    comfort: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Treasure:
    id: str
    label: str
    clue: str
    shared_use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_pain_to_limp(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["pain"] >= THRESHOLD:
        sig = ("pain_to_limp", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["limp"] += 1
            out.append("__limp__")
    return out


def _r_delay_to_infection(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    injury = world.facts["injury_cfg"]
    if injury.can_abscess and world.facts["delay"] >= 1 and hero.meters["cleaned"] < THRESHOLD:
        sig = ("delay_to_infection", injury.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["infected"] += 1
            hero.meters["swelling"] += 1
            hero.meters["pain"] += 1
            out.append("__infected__")
    return out


def _r_help_clears_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["bandaged"] >= THRESHOLD:
        sig = ("bandaged_relief", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["fear"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="pain_to_limp", tag="physical", apply=_r_pain_to_limp),
    Rule(name="delay_to_infection", tag="physical", apply=_r_delay_to_infection),
    Rule(name="help_clears_fear", tag="emotional", apply=_r_help_clears_fear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def injury_needs_elevation(injury: Injury) -> bool:
    return injury.needs_elevate


def care_works(care: Care, injury: Injury) -> bool:
    return injury.id in care.works_for and care.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for deck in DECKS:
        for injury_id, injury in INJURIES.items():
            for care_id, care in CARES.items():
                if care_works(care, injury):
                    combos.append((deck, injury_id, care_id))
    return combos


def predict_worsening(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "infected": sim.get("hero").meters["infected"] >= THRESHOLD,
        "limp": sim.get("hero").meters["limp"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, mate: Entity, deck: Deck, treasure: Treasure) -> None:
    hero.memes["friendship"] += 1
    mate.memes["friendship"] += 1
    world.say(
        f"On a windy afternoon, {hero.id} and {mate.id} turned the yard into {deck.scene}. "
        f"{deck.rig}"
    )
    world.say(
        f'Together they hunted for {treasure.clue}, certain it would lead to {deck.hunt}.'
    )


def quarrel(world: World, hero: Entity, mate: Entity, treasure: Treasure) -> None:
    hero.memes["pride"] += 1
    mate.memes["hurt"] += 1
    world.say(
        f"But when they reached the next clue, both children grabbed for the {treasure.label} at once."
    )
    world.say(
        f'"I should carry it. I am the captain today," {hero.id} said.'
    )
    world.say(
        f'{mate.id} pulled {mate.pronoun("possessive")} hand back and frowned. '
        f'"Pirates share maps," {mate.pronoun()} said.'
    )


def storm_off(world: World, hero: Entity, deck: Deck) -> None:
    world.say(
        f"Proud and hot-cheeked, {hero.id} marched alone toward {deck.dark_or_wild}, "
        f"trying to look brave even while the game felt suddenly lonely."
    )


def get_hurt(world: World, hero: Entity, injury: Injury) -> None:
    hero.meters["pain"] += 1
    hero.memes["fear"] += 1
    hero.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun('possessive')} bare {injury.body_part} brushed {injury.cause}, "
        f"and {hero.pronoun()} gave a sharp little gasp."
    )
    world.say(
        f"It was only a small hurt at first, but it stung hard enough to stop the make-believe ship in its tracks."
    )


def hide_hurt(world: World, hero: Entity, mate: Entity, injury: Injury) -> None:
    pred = predict_worsening(world)
    world.facts["predicted_infected"] = pred["infected"]
    world.facts["predicted_limp"] = pred["limp"]
    hero.memes["pride"] += 1
    if pred["limp"]:
        world.say(
            f"{hero.id} tried to stand tall, but a limp slipped into every step."
        )
    world.say(
        f'"I am fine," {hero.id} insisted, even though {hero.pronoun("possessive")} voice had gone thin.'
    )
    if pred["infected"]:
        world.say(
            f'{mate.id} looked down at {injury.object_phrase} and whispered, '
            f'"That little hurt could turn red and abscessed if we only pretend it is nothing."'
        )
    else:
        world.say(
            f'{mate.id} stayed close and said, "Real captains tell the truth when something hurts."'
        )


def brave_confession(world: World, hero: Entity, mate: Entity) -> None:
    hero.memes["courage"] += 1
    mate.memes["trust"] += 1
    world.say(
        f"For one quiet moment, {hero.id} had to choose between pride and bravery."
    )
    world.say(
        f'"All right," {hero.pronoun()} whispered at last. "It really does hurt. Will you stay with me?"'
    )
    world.say(
        f'"Of course," said {mate.id}. {mate.pronoun().capitalize()} took {hero.pronoun("possessive")} hand at once.'
    )


def call_helper(world: World, helper: Entity, hero: Entity, injury: Injury, care: Care) -> None:
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    body = care.text.format(part=injury.body_part)
    world.say(
        f"Soon {helper.label_word.capitalize()} came hurrying over, calm as a harbor on a still morning, and {body}."
    )
    if injury.needs_elevate:
        world.say(
            f'"First we clean it, then we elevate your {injury.body_part} on a pillow and let it rest," '
            f'{helper.pronoun()} said.'
        )
    else:
        world.say(
            f'"First we clean it and wrap it snugly so it can rest," {helper.pronoun()} said.'
        )


def treat(world: World, hero: Entity, injury: Injury, care: Care) -> None:
    hero.meters["cleaned"] += 1
    hero.meters["bandaged"] += 1
    hero.meters["pain"] = max(0.0, hero.meters["pain"] - 1)
    if hero.meters["infected"] >= THRESHOLD and care.power >= 3:
        hero.meters["infected"] = 0.0
        hero.meters["swelling"] = max(0.0, hero.meters["swelling"] - 1)
    elif hero.meters["infected"] >= THRESHOLD:
        hero.meters["danger"] += 1
    propagate(world, narrate=False)
    world.say(care.comfort.format(part=injury.body_part))


def reconcile(world: World, hero: Entity, mate: Entity, treasure: Treasure) -> None:
    hero.memes["guilt"] += 1
    hero.memes["friendship"] += 1
    mate.memes["friendship"] += 1
    hero.memes["pride"] = 0.0
    world.say(
        f"Then {hero.id} looked at {mate.id} and felt sorrier for the quarrel than for the sting."
    )
    world.say(
        f'"I was trying so hard to win that I forgot how to be a friend," {hero.pronoun()} said. '
        f'"I am sorry."'
    )
    world.say(
        f'{mate.id} smiled and squeezed {hero.pronoun("possessive")} fingers. '
        f'"I am sorry too. We can share the {treasure.label} and still be bold."'
    )


def return_to_play(world: World, hero: Entity, mate: Entity, deck: Deck, treasure: Treasure, injury: Injury) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    if injury.needs_elevate:
        world.say(
            f"They propped {hero.id}'s {injury.body_part} on a striped pillow like the stern of a tiny ship."
        )
    else:
        world.say(
            f"They sat side by side on the porch step while the bandage settled into place."
        )
    world.say(
        f"With the {treasure.label} open between them, they planned the next part of the voyage together."
    )
    world.say(
        f"By sunset, the quarrel was gone, the friendship was brighter, and {deck.ending}."
    )


def tell(
    deck: Deck,
    injury: Injury,
    care: Care,
    treasure: Treasure,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    mate_name: str = "Tom",
    mate_gender: str = "boy",
    helper_type: str = "mother",
    trait: str = "proud",
    delay: int = 1,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="captain", traits=[trait]))
    mate = world.add(Entity(id="mate", kind="character", type=mate_gender, label=mate_name, role="mate", traits=["loyal"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    hero.attrs["name"] = hero_name
    mate.attrs["name"] = mate_name
    helper.attrs["name"] = helper.label_word.capitalize()
    hero.meters["pain"] = 0.0
    hero.meters["infected"] = 0.0
    hero.meters["cleaned"] = 0.0
    hero.meters["bandaged"] = 0.0
    hero.meters["swelling"] = 0.0
    hero.meters["limp"] = 0.0
    hero.meters["danger"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["friendship"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["guilt"] = 0.0
    mate.memes["friendship"] = 0.0
    mate.memes["trust"] = 0.0
    mate.memes["hurt"] = 0.0
    mate.memes["joy"] = 0.0
    helper.memes["care"] = 0.0
    world.facts["delay"] = delay
    world.facts["injury_cfg"] = injury
    world.facts["deck_cfg"] = deck
    world.facts["care_cfg"] = care
    world.facts["treasure_cfg"] = treasure
    world.facts["predicted_infected"] = False
    world.facts["predicted_limp"] = False

    introduce(world, hero, mate, deck, treasure)
    world.para()
    quarrel(world, hero, mate, treasure)
    storm_off(world, hero, deck)
    get_hurt(world, hero, injury)
    hide_hurt(world, hero, mate, injury)
    world.para()
    brave_confession(world, hero, mate)
    call_helper(world, helper, hero, injury, care)
    treat(world, hero, injury, care)
    reconcile(world, hero, mate, treasure)
    world.para()
    return_to_play(world, hero, mate, deck, treasure, injury)

    outcome = "quick_heal"
    if delay >= 1 and injury.can_abscess:
        if care.power >= 3:
            outcome = "treated_infection"
        else:
            outcome = "worsened"
    world.facts.update(
        hero=hero,
        mate=mate,
        helper=helper,
        injury_cfg=injury,
        care_cfg=care,
        treasure_cfg=treasure,
        deck_cfg=deck,
        outcome=outcome,
        reconciled=hero.memes["guilt"] >= THRESHOLD and hero.memes["friendship"] >= THRESHOLD,
        brave=hero.memes["courage"] >= THRESHOLD,
        elevated=injury.needs_elevate,
        infected_before_treatment=delay >= 1 and injury.can_abscess,
        healed=hero.meters["danger"] < THRESHOLD,
    )
    return world


DECKS = {
    "cove": Deck(
        id="cove",
        scene="a windy pirate cove",
        rig="The sandbox became a golden beach, the climbing frame became their mast, and a striped towel served as a snapping sail.",
        hunt="the emerald chest buried beyond the rocks",
        dark_or_wild="the pebbly edge of the cove",
        ending="their pirate ship felt big enough for two captains",
        tags={"pirate", "shore"},
    ),
    "dock": Deck(
        id="dock",
        scene="a creaky pirate dock",
        rig="The porch steps became a harbor pier, a broom became a lookout pole, and a laundry basket held all their pretend loot.",
        hunt="the silver bell hidden by the posts",
        dark_or_wild="the end of the dock",
        ending="the old dock seemed to glow with forgiven, laughing light",
        tags={"pirate", "harbor"},
    ),
    "island": Deck(
        id="island",
        scene="a brave little treasure island",
        rig="The garden path became a secret shore, a cardboard box became their skiff, and a chalk line showed where sharks were not allowed.",
        hunt="the ruby compass under the palm-sized fern",
        dark_or_wild="the wild side of the island path",
        ending="the island breeze fluttered their shared flag above them",
        tags={"pirate", "island"},
    ),
}

INJURIES = {
    "shell_cut": Injury(
        id="shell_cut",
        label="shell cut",
        body_part="foot",
        article_part="a foot",
        cause="a cracked shell hidden in the sand",
        sharp=True,
        can_abscess=True,
        needs_elevate=True,
        severity=2,
        tags={"cut", "foot", "infection"},
    ),
    "splinter_ankle": Injury(
        id="splinter_ankle",
        label="splinter scrape",
        body_part="ankle",
        article_part="an ankle",
        cause="a rough board with a sharp splinter",
        sharp=True,
        can_abscess=True,
        needs_elevate=True,
        severity=2,
        tags={"splinter", "ankle", "infection"},
    ),
    "rope_burn": Injury(
        id="rope_burn",
        label="rope burn",
        body_part="hand",
        article_part="a hand",
        cause="the fast-sliding toy rope",
        sharp=False,
        can_abscess=False,
        needs_elevate=False,
        severity=1,
        tags={"rope", "hand"},
    ),
}

CARES = {
    "rinse_bandage": Care(
        id="rinse_bandage",
        sense=2,
        power=2,
        works_for={"rope_burn"},
        text="gently rinsed the sore {part} with clean water and wrapped it in a soft bandage",
        comfort='"There now," said the helper. "A clean bandage gives your {part} a quiet place to heal."',
        qa_text="rinsed the hurt place and wrapped it in a clean bandage",
        tags={"bandage", "clean"},
    ),
    "wash_ointment_elevate": Care(
        id="wash_ointment_elevate",
        sense=3,
        power=3,
        works_for={"shell_cut", "splinter_ankle", "rope_burn"},
        text="washed the hurt {part}, spread on ointment, and tied on a neat little bandage",
        comfort='"You were brave to speak up," said the helper. "We cleaned it before the sore place could stay dirty."',
        qa_text="washed the hurt place, used ointment, and bandaged it",
        tags={"bandage", "ointment", "clean", "elevate"},
    ),
    "treasure_song": Care(
        id="treasure_song",
        sense=1,
        power=0,
        works_for=set(),
        text="sang a treasure song and called that good enough",
        comfort='"A song is cheerful," said the helper, "but songs alone cannot clean a wound."',
        qa_text="only sang a song",
        tags={"song"},
    ),
}

TREASURES = {
    "map": Treasure(
        id="map",
        label="map",
        clue="a torn pirate map",
        shared_use="They could hold one corner each and still steer together.",
        tags={"map"},
    ),
    "compass": Treasure(
        id="compass",
        label="compass",
        clue="a brass compass with a wobbling needle",
        shared_use="They could take turns calling north and still stay a crew.",
        tags={"compass"},
    ),
    "flag": Treasure(
        id="flag",
        label="flag",
        clue="a black paper flag with a chalk skull",
        shared_use="They could raise it together and make one ship from two stubborn hearts.",
        tags={"flag"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["proud", "spirited", "stubborn", "bold", "eager"]


@dataclass
class StoryParams:
    deck: str
    injury: str
    care: str
    treasure: str
    hero_name: str
    hero_gender: str
    mate_name: str
    mate_gender: str
    helper: str
    trait: str
    delay: int = 1
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "infection": [
        (
            "What does abscessed mean?",
            "Abscessed means a sore place has become infected and filled with angry swelling or pus. It is a sign that the body part needs grown-up care, cleaning, and rest."
        )
    ],
    "elevate": [
        (
            "What does elevate mean when someone is hurt?",
            "To elevate a hurt foot or ankle means to raise it up on a pillow or stool. That can help swelling go down and lets the sore place rest."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage covers a hurt place and helps keep it clean. It also protects the skin while it heals."
        )
    ],
    "ointment": [
        (
            "What is ointment?",
            "Ointment is a smooth medicine that a grown-up can spread on a scrape or cut. It helps protect the sore place while it heals."
        )
    ],
    "friendship": [
        (
            "What helps friendship after an argument?",
            "Telling the truth, saying sorry, and listening kindly can help friendship mend. Sharing again shows that the change is real."
        )
    ],
    "bravery": [
        (
            "Is it brave to ask for help when you are hurt?",
            "Yes. Asking for help is brave because you tell the truth even when you feel embarrassed or scared."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map helps people find where they want to go. Pirates in stories use maps to hunt for treasure."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass shows direction, like north and south. In adventure stories, it helps travelers know which way to go."
        )
    ],
    "flag": [
        (
            "What is a flag on a ship for?",
            "A flag shows who the ship belongs to and can help it stand out from far away. In pretend play, it can make the game feel real."
        )
    ],
}
KNOWLEDGE_ORDER = ["infection", "elevate", "bandage", "ointment", "friendship", "bravery", "map", "compass", "flag"]


CURATED = [
    StoryParams(
        deck="cove",
        injury="shell_cut",
        care="wash_ointment_elevate",
        treasure="map",
        hero_name="Nora",
        hero_gender="girl",
        mate_name="Tom",
        mate_gender="boy",
        helper="mother",
        trait="proud",
        delay=1,
    ),
    StoryParams(
        deck="dock",
        injury="splinter_ankle",
        care="wash_ointment_elevate",
        treasure="compass",
        hero_name="Ben",
        hero_gender="boy",
        mate_name="Lucy",
        mate_gender="girl",
        helper="father",
        trait="bold",
        delay=1,
    ),
    StoryParams(
        deck="island",
        injury="rope_burn",
        care="rinse_bandage",
        treasure="flag",
        hero_name="Mia",
        hero_gender="girl",
        mate_name="Finn",
        mate_gender="boy",
        helper="aunt",
        trait="spirited",
        delay=0,
    ),
]


def explain_injury_care(injury: Injury, care: Care) -> str:
    if care.sense < SENSE_MIN:
        return (
            f"(Refusing care '{care.id}': it is too weak or silly for a real hurt. "
            f"Pick a sensible treatment like wash_ointment_elevate or rinse_bandage.)"
        )
    return (
        f"(No story: {care.id} is not a reasonable treatment for {injury.label}. "
        f"The chosen care must actually fit the type of injury.)"
    )


def outcome_of(params: StoryParams) -> str:
    injury = INJURIES[params.injury]
    care = CARES[params.care]
    if params.delay >= 1 and injury.can_abscess:
        return "treated_infection" if care.power >= 3 else "worsened"
    return "quick_heal"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    injury = f["injury_cfg"]
    treasure = f["treasure_cfg"]
    deck = f["deck_cfg"]
    return [
        f'Write a gentle pirate tale for a 3-to-5-year-old that includes the words "abscessed" and "elevate".',
        f"Tell a pirate-style story where {hero.attrs['name']} and {mate.attrs['name']} quarrel over a {treasure.label}, then make up after {hero.pronoun('subject')} bravely admits a hurt {injury.body_part}.",
        f"Write a short story set in {deck.scene} where friendship is tested, a child needs help, and reconciliation is proved by the children sharing the treasure at the end.",
    ]


def pair_noun(hero: Entity, mate: Entity) -> str:
    if hero.type == "boy" and mate.type == "boy":
        return "two pirate boys"
    if hero.type == "girl" and mate.type == "girl":
        return "two pirate girls"
    return "two pirate friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    helper = f["helper"]
    injury = f["injury_cfg"]
    care = f["care_cfg"]
    treasure = f["treasure_cfg"]
    deck = f["deck_cfg"]
    hero_name = hero.attrs["name"]
    mate_name = mate.attrs["name"]
    helper_name = helper.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, mate)}, {hero_name} and {mate_name}, who were pretending to sail through {deck.scene}. Their pirate game becomes a story about hurt feelings, bravery, and making up."
        ),
        (
            "Why did the friends start to quarrel?",
            f"They both wanted to carry the {treasure.label} and lead the treasure hunt. The quarrel started because pride made sharing feel harder than it should have."
        ),
        (
            f"How did {hero_name} get hurt?",
            f"{hero_name} stormed off alone and {injury.body_part} brushed {injury.cause}. That small hurt brought the game to a stop because it stung and made walking or moving harder."
        ),
    ]
    if f.get("predicted_infected"):
        qa.append(
            (
                f"Why did {mate_name} worry about the hurt place?",
                f"{mate_name} could see that the wound might get worse if nobody cleaned it. {mate.pronoun().capitalize()} warned that it could become abscessed, which means the sore place could turn infected and swollen."
            )
        )
    else:
        qa.append(
            (
                f"Why was it brave for {hero_name} to tell the truth?",
                f"It was brave because {hero_name} had first tried to hide the pain out of pride. Telling the truth let {mate_name} and {helper_name.lower()} help before the hurt grew worse."
            )
        )
    qa.append(
        (
            f"How did {helper_name.lower()} help {hero_name}?",
            f"{helper.pronoun().capitalize()} {care.qa_text}. Because the injury was on the {injury.body_part}, the care also focused on rest and keeping the sore place clean."
        )
    )
    if injury.needs_elevate:
        qa.append(
            (
                f"Why did {helper_name.lower()} tell them to elevate the {injury.body_part}?",
                f"{helper.pronoun().capitalize()} wanted the sore {injury.body_part} raised up so it could rest and swell less. Elevating it also showed the children they had paused the game to take real care of the injury."
            )
        )
    qa.append(
        (
            "How do we know the friends reconciled?",
            f"We know because {hero_name} said sorry, {mate_name} forgave {hero.pronoun('object')}, and they shared the {treasure.label} together at the end. The ending image proves the friendship changed from tugging and frowning back to working as one crew."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"friendship", "bravery"}
    injury = f["injury_cfg"]
    care = f["care_cfg"]
    treasure = f["treasure_cfg"]
    if injury.can_abscess:
        tags.add("infection")
    if injury.needs_elevate:
        tags.add("elevate")
    if "bandage" in care.tags:
        tags.add("bandage")
    if "ointment" in care.tags:
        tags.add("ointment")
    tags |= set(treasure.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(D, I, C) :- deck(D), injury(I), care(C), works_for(C, I), sense(C, S), sense_min(M), S >= M.

infected_before_help :- chosen_injury(I), can_abscess(I), delay(D), D >= 1.
healed :- chosen_care(C), power(C, P), not infected_before_help, P >= 1.
healed :- chosen_care(C), power(C, P), infected_before_help, P >= 3.
worsened :- infected_before_help, chosen_care(C), power(C, P), P < 3.

outcome(quick_heal) :- not infected_before_help, healed.
outcome(treated_infection) :- infected_before_help, healed.
outcome(worsened) :- worsened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DECKS:
        lines.append(asp.fact("deck", did))
    for iid, injury in INJURIES.items():
        lines.append(asp.fact("injury", iid))
        if injury.can_abscess:
            lines.append(asp.fact("can_abscess", iid))
        if injury.needs_elevate:
            lines.append(asp.fact("needs_elevate", iid))
    for cid, care in CARES.items():
        lines.append(asp.fact("care", cid))
        lines.append(asp.fact("sense", cid, care.sense))
        lines.append(asp.fact("power", cid, care.power))
        for iid in sorted(care.works_for):
            lines.append(asp.fact("works_for", cid, iid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_injury", params.injury),
            asp.fact("chosen_care", params.care),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate friends quarrel, a child is hurt, help arrives, and friendship is repaired."
    )
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--care", choices=CARES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = help comes before infection; 1 = delay lets puncture wounds worsen")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.injury and args.care:
        injury = INJURIES[args.injury]
        care = CARES[args.care]
        if not care_works(care, injury):
            raise StoryError(explain_injury_care(injury, care))
    if args.care and CARES[args.care].sense < SENSE_MIN:
        injury = INJURIES[args.injury] if args.injury else next(iter(INJURIES.values()))
        raise StoryError(explain_injury_care(injury, CARES[args.care]))

    combos = [
        c for c in valid_combos()
        if (args.deck is None or c[0] == args.deck)
        and (args.injury is None or c[1] == args.injury)
        and (args.care is None or c[2] == args.care)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    deck, injury, care = rng.choice(sorted(combos))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    hero_name, hero_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=hero_name)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    if delay == 1 and not INJURIES[injury].can_abscess:
        delay = 0

    return StoryParams(
        deck=deck,
        injury=injury,
        care=care,
        treasure=treasure,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        helper=helper,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.deck not in DECKS:
        raise StoryError(f"(Unknown deck: {params.deck})")
    if params.injury not in INJURIES:
        raise StoryError(f"(Unknown injury: {params.injury})")
    if params.care not in CARES:
        raise StoryError(f"(Unknown care: {params.care})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.helper not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")

    injury = INJURIES[params.injury]
    care = CARES[params.care]
    if not care_works(care, injury):
        raise StoryError(explain_injury_care(injury, care))
    if params.delay not in {0, 1}:
        raise StoryError("(Delay must be 0 or 1.)")
    if params.delay == 1 and not injury.can_abscess:
        raise StoryError("(This injury does not plausibly become abscessed after a short delay.)")

    world = tell(
        deck=DECKS[params.deck],
        injury=injury,
        care=care,
        treasure=TREASURES[params.treasure],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: valid combo gate matches ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if params.delay == 1 and not INJURIES[params.injury].can_abscess:
            continue
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if "abscessed" not in smoke.story or "elevate" not in smoke.story:
            raise StoryError("(Smoke test story did not contain required seed words.)")
        if not smoke.story_qa or not smoke.world_qa or not smoke.prompts:
            raise StoryError("(Smoke test story did not produce complete QA/prompts.)")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (deck, injury, care) combos:\n")
        for deck, injury, care in combos:
            print(f"  {deck:8} {injury:16} {care}")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name} & {p.mate_name}: {p.injury} on {p.deck} ({p.care}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
