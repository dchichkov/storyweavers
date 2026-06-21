#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/harrow_misunderstanding_surprise_bravery_folk_tale.py
=================================================================================

A small folk-tale story world about a night noise, a misunderstanding, and a
brave child who discovers that the feared "monster" is only an animal tangled
with an old harrow.

The world is constraint-checked: a place must plausibly host the chosen animal,
the snag must fit that animal, and the rescue must truly free it. The prose is
driven by simulated state: the animal's struggle makes the harrow rattle, the
rattle raises fear, light reveals the truth, and the right rescue ends the
danger and the misunderstanding.

Run it
------
    python storyworlds/worlds/gpt-5.4/harrow_misunderstanding_surprise_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4/harrow_misunderstanding_surprise_bravery_folk_tale.py --place orchard_edge --animal goat --snag bramble_vine --rescue untangle
    python storyworlds/worlds/gpt-5.4/harrow_misunderstanding_surprise_bravery_folk_tale.py --animal donkey --snag bramble_vine
    python storyworlds/worlds/gpt-5.4/harrow_misunderstanding_surprise_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/harrow_misunderstanding_surprise_bravery_folk_tale.py --verify
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    opening: str
    path: str
    rumor: str
    afford_animals: set[str] = field(default_factory=set)
    fear: int = 2
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
class AnimalCfg:
    id: str
    label: str
    phrase: str
    cry: str
    gait: str
    temper: str
    tracks: str
    allows_snags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Snag:
    id: str
    label: str
    phrase: str
    seen: str
    sound: str
    fix_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Rescue:
    id: str
    label: str
    action: str
    touch: str
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
class HeroTrait:
    id: str
    label: str
    courage: int
    style: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "heard_noise": False,
            "misunderstood": False,
            "revealed": False,
            "freed": False,
            "lead": False,
        }

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_rattle(world: World) -> list[str]:
    animal = world.get("animal")
    harrow = world.get("harrow")
    if animal.meters["snagged"] < THRESHOLD or animal.meters["moving"] < THRESHOLD:
        return []
    sig = ("rattle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    harrow.meters["rattling"] += 1
    world.get("place").meters["alarm"] += 1
    for person in world.characters():
        if person.role in {"hero", "elder"}:
            person.memes["fear"] += 1
    world.facts["heard_noise"] = True
    return ["__rattle__"]


def _r_light_reveals(world: World) -> list[str]:
    hero = world.get("hero")
    harrow = world.get("harrow")
    animal = world.get("animal")
    if hero.attrs.get("has_light") != "yes":
        return []
    if harrow.meters["rattling"] < THRESHOLD or animal.meters["snagged"] < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["certainty"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    world.facts["revealed"] = True
    return []


def _r_release(world: World) -> list[str]:
    animal = world.get("animal")
    harrow = world.get("harrow")
    if animal.meters["snagged"] >= THRESHOLD:
        return []
    if harrow.meters["rattling"] < THRESHOLD:
        return []
    sig = ("release",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    harrow.meters["rattling"] = 0.0
    world.get("place").meters["alarm"] = 0.0
    animal.memes["calm"] += 1
    for person in world.characters():
        if person.role in {"hero", "elder"}:
            person.memes["relief"] += 1
            person.memes["fear"] = 0.0
    world.facts["freed"] = True
    return []


CAUSAL_RULES = [
    Rule(name="rattle", tag="physical", apply=_r_rattle),
    Rule(name="light_reveals", tag="epistemic", apply=_r_light_reveals),
    Rule(name="release", tag="physical", apply=_r_release),
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


PLACES = {
    "field_lane": Place(
        id="field_lane",
        label="the lane beside the rye field",
        opening="Beyond the last cottage lay the lane beside the rye field, where moonlight made every furrow look silver.",
        path="down the narrow lane where the rye whispered against the ditch",
        rumor="an iron goblin dragging its claws",
        afford_animals={"goat", "donkey"},
        fear=2,
        tags={"field", "night"},
    ),
    "orchard_edge": Place(
        id="orchard_edge",
        label="the edge of the old orchard",
        opening="At the edge of the old orchard, the apple trees stood black and round against the stars.",
        path="between the bent apple trees and the low stone wall",
        rumor="a thorn spirit shaking chains in the leaves",
        afford_animals={"goat", "calf"},
        fear=3,
        tags={"orchard", "night"},
    ),
    "meadow_ford": Place(
        id="meadow_ford",
        label="the meadow by the ford",
        opening="Past the mill path stretched the meadow by the ford, where mist slept close to the grass.",
        path="through the damp meadow toward the little ford",
        rumor="a river giant grinding its teeth",
        afford_animals={"donkey", "calf"},
        fear=3,
        tags={"meadow", "night"},
    ),
}

ANIMALS = {
    "goat": AnimalCfg(
        id="goat",
        label="goat",
        phrase="a little horned goat",
        cry="bleated",
        gait="skipped and jerked",
        temper="quick-eyed",
        tracks="small split hoofprints",
        allows_snags={"rope_loop", "bramble_vine"},
        tags={"goat", "animal"},
    ),
    "donkey": AnimalCfg(
        id="donkey",
        label="donkey",
        phrase="a gray donkey",
        cry="brayed",
        gait="lurched and stamped",
        temper="long-eared",
        tracks="broad hoofprints",
        allows_snags={"rope_loop", "harness_strap"},
        tags={"donkey", "animal"},
    ),
    "calf": AnimalCfg(
        id="calf",
        label="calf",
        phrase="a soft brown calf",
        cry="lowed",
        gait="stumbled and pulled",
        temper="big-eyed",
        tracks="round young hoofprints",
        allows_snags={"rope_loop", "bramble_vine"},
        tags={"calf", "animal"},
    ),
}

SNAGS = {
    "rope_loop": Snag(
        id="rope_loop",
        label="rope loop",
        phrase="a rope loop twisted through one of the harrow's iron teeth",
        seen="a pale rope drawn tight through the black iron",
        sound="The harrow clashed over stones with a hard iron clatter.",
        fix_by={"cut_rope"},
        tags={"rope", "harrow"},
    ),
    "harness_strap": Snag(
        id="harness_strap",
        label="harness strap",
        phrase="a broken harness strap hooked fast on the harrow",
        seen="a cracked leather strap caught where two iron teeth crossed",
        sound="The harrow scraped in rough, dragging bursts, as if something heavy kept catching and letting go.",
        fix_by={"unbuckle"},
        tags={"strap", "harrow"},
    ),
    "bramble_vine": Snag(
        id="bramble_vine",
        label="bramble vine",
        phrase="a bramble vine wound around the harrow and the frightened animal's leg rope",
        seen="thorny green strands twisted all through the iron teeth",
        sound="The harrow hissed and rattled through dry leaves, then banged whenever it struck a root.",
        fix_by={"untangle"},
        tags={"vine", "harrow"},
    ),
}

RESCUES = {
    "cut_rope": Rescue(
        id="cut_rope",
        label="small knife",
        action="took the little knife from the elder's belt and cut the rope free in one careful stroke",
        touch="kept one hand on the shaking animal while the other worked",
        qa_text="cut the rope free with a small knife",
        tags={"knife", "help"},
    ),
    "unbuckle": Rescue(
        id="unbuckle",
        label="steady fingers",
        action="set steady fingers to the old buckle and worked it loose until the strap slipped open",
        touch="spoke softly all the while so the animal would stand still",
        qa_text="worked the old strap buckle loose with steady fingers",
        tags={"buckle", "help"},
    ),
    "untangle": Rescue(
        id="untangle",
        label="patient hands",
        action="knelt in the thorns and unwound the vine strand by strand until the iron teeth were clear",
        touch="murmured to the frightened creature until its breathing slowed",
        qa_text="untangled the bramble vine by hand",
        tags={"thorns", "help"},
    ),
}

HERO_TRAITS = {
    "bold": HeroTrait(
        id="bold",
        label="bold",
        courage=3,
        style="was quick to step forward when others held back",
        tags={"brave"},
    ),
    "steady": HeroTrait(
        id="steady",
        label="steady",
        courage=2,
        style="did not rush, but once a promise was made, did not turn aside",
        tags={"brave"},
    ),
    "timid_but_true": HeroTrait(
        id="timid_but_true",
        label="timid but true",
        courage=1,
        style="often felt fear first, yet hated to leave another creature in trouble",
        tags={"brave", "fear"},
    ),
}

GIRL_NAMES = ["Mara", "Elsa", "Nella", "Tina", "Brina", "Lina"]
BOY_NAMES = ["Tomas", "Ivo", "Milo", "Pavel", "Nico", "Joren"]


@dataclass
class StoryParams:
    place: str
    animal: str
    snag: str
    rescue: str
    hero_name: str
    hero_gender: str
    elder_type: str
    hero_trait: str
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


def snag_supported(animal_id: str, snag_id: str) -> bool:
    return snag_id in ANIMALS[animal_id].allows_snags


def rescue_works(snag_id: str, rescue_id: str) -> bool:
    return rescue_id in SNAGS[snag_id].fix_by


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for animal_id in sorted(place.afford_animals):
            for snag_id in sorted(ANIMALS[animal_id].allows_snags):
                for rescue_id in sorted(SNAGS[snag_id].fix_by):
                    combos.append((place_id, animal_id, snag_id, rescue_id))
    return combos


def courage_value(trait_id: str) -> int:
    return HERO_TRAITS[trait_id].courage


def lead_outcome(params: StoryParams) -> str:
    return "lead" if courage_value(params.hero_trait) >= PLACES[params.place].fear else "follow"


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").attrs["has_light"] = "yes"
    propagate(sim, narrate=False)
    return {
        "revealed": sim.facts.get("revealed", False),
        "fear_after_light": sim.get("hero").memes["fear"],
    }


def predict_release(world: World, rescue: Rescue) -> dict:
    sim = world.copy()
    if rescue.id in SNAGS[sim.facts["snag"].id].fix_by:
        sim.get("animal").meters["snagged"] = 0.0
        propagate(sim, narrate=False)
    return {
        "freed": sim.facts.get("freed", False),
        "alarm": sim.get("place").meters["alarm"],
    }


def opening(world: World, hero: Entity, elder: Entity, trait: HeroTrait) -> None:
    world.say(
        f"In a village where people still remembered old sayings and old tools, {hero.id} lived with {hero.pronoun('possessive')} {elder.label_word}. "
        f"{PLACES[world.place.id].opening}"
    )
    world.say(
        f"Behind the shed leaned an old harrow with iron teeth like a comb for the earth. "
        f"The elders said it should rest by day and never be left loose by night."
    )
    world.say(f"{hero.id} {trait.style}.")


def night_noise(world: World, hero: Entity, elder: Entity, snag: Snag, animal: AnimalCfg) -> None:
    animal_ent = world.get("animal")
    animal_ent.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One night, when the lamps were low and the hens were asleep, a scraping cry came from {world.place.label}. {snag.sound}"
    )
    world.say(
        f'"Hear that?" whispered the {elder.label_word}. "It sounds like {world.place.rumor}."'
    )
    world.facts["misunderstood"] = True
    world.say(
        f"{hero.id} listened too, and for a moment the sound did seem bigger than any honest beast."
    )


def decide_to_go(world: World, hero: Entity, elder: Entity) -> None:
    pred = predict_reveal(world)
    world.facts["predicted_reveal"] = pred["revealed"]
    hero.memes["resolve"] += 1
    if lead_outcome(world.facts["params"]) == "lead":
        world.facts["lead"] = True
        hero.memes["bravery"] += 1
        world.say(
            f'"If something is hurting, we should not leave it in the dark," said {hero.id}. '
            f'With a lantern lifted high, {hero.pronoun()} went first {world.place.path}, and the {elder.label_word} followed close behind.'
        )
    else:
        world.facts["lead"] = False
        hero.memes["bravery"] += 1
        world.say(
            f"{hero.id}'s knees felt weak, yet {hero.pronoun()} would not stay by the fire. "
            f'Lantern in hand, {hero.pronoun()} went beside the {elder.label_word} {world.place.path}.'
        )


def reveal_truth(world: World, hero: Entity, elder: Entity, animal: AnimalCfg, snag: Snag) -> None:
    world.get("hero").attrs["has_light"] = "yes"
    propagate(world, narrate=False)
    world.say(
        f"The lantern poured a warm ring over the path, and the dreadful shape turned plain. "
        f"It was not a spirit at all, but {animal.phrase}."
    )
    world.say(
        f"The poor creature {animal.gait}, and behind it dragged the harrow. {snag.seen}."
    )
    world.say(
        f'The {elder.label_word} let out a long breath. "So that is our monster," {elder.pronoun()} said.'
    )


def rescue_scene(world: World, hero: Entity, elder: Entity, rescue: Rescue, animal: AnimalCfg) -> None:
    pred = predict_release(world, rescue)
    world.facts["predicted_release"] = pred["freed"]
    animal_ent = world.get("animal")
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} did not laugh at the frightened creature. {hero.pronoun().capitalize()} came near slowly, {rescue.touch}."
    )
    world.say(f"Then {hero.pronoun()} {rescue.action}.")
    animal_ent.meters["snagged"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"At once the harrow fell still. The {animal.label} gave one last startled sound, then stood quiet in the lantern glow."
    )


def ending(world: World, hero: Entity, elder: Entity, animal: AnimalCfg) -> None:
    world.say(
        f'The {elder.label_word} touched {hero.id} on the shoulder. "A brave heart is not the one that never shakes," {elder.pronoun()} said. '
        f'"It is the one that goes kindly toward the truth."'
    )
    world.para()
    world.say(
        f"By dawn the tale had gone around the village: no goblin had walked there, only a frightened {animal.label} and a wandering harrow. "
        f"People smiled at the old misunderstanding and tied the harrow safely behind the shed."
    )
    world.say(
        f"When the sun rose over {world.place.label}, the iron teeth shone harmlessly in the gold light, and {hero.id} was no longer only the youngest at the hearth, but the one who had been brave enough to look."
    )


def tell(
    place: Place,
    animal: AnimalCfg,
    snag: Snag,
    rescue: Rescue,
    hero_name: str,
    hero_gender: str,
    elder_type: str,
    hero_trait: HeroTrait,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait.id],
        attrs={"has_light": "no"},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        attrs={},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        attrs={},
    ))
    harrow = world.add(Entity(
        id="harrow",
        kind="thing",
        type="harrow",
        label="harrow",
        attrs={},
    ))
    animal_ent = world.add(Entity(
        id="animal",
        kind="thing",
        type=animal.id,
        label=animal.label,
        attrs={},
    ))

    place_ent.meters["alarm"] = 0.0
    harrow.meters["rattling"] = 0.0
    animal_ent.meters["moving"] = 0.0
    animal_ent.meters["snagged"] = 1.0
    animal_ent.memes["calm"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["certainty"] = 0.0
    elder.memes["fear"] = 0.0

    world.facts.update(
        params=None,
        place_cfg=place,
        animal_cfg=animal,
        snag=snag,
        rescue=rescue,
        hero=hero,
        elder=elder,
    )

    opening(world, hero, elder, hero_trait)
    world.para()
    night_noise(world, hero, elder, snag, animal)
    decide_to_go(world, hero, elder)
    world.para()
    reveal_truth(world, hero, elder, animal, snag)
    rescue_scene(world, hero, elder, rescue, animal)
    world.para()
    ending(world, hero, elder, animal)
    return world


KNOWLEDGE = {
    "harrow": [
        (
            "What is a harrow?",
            "A harrow is a farm tool with teeth or spikes that breaks up the soil after it is plowed. It is heavy, so if it is dragged the wrong way it can make a loud scraping noise."
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in the dark?",
            "A lantern spreads light so people can see what is really there. Light helps stop mistakes that begin with fear and guessing."
        )
    ],
    "rope": [
        (
            "Why can a rope get stuck on iron teeth?",
            "A rope can catch in sharp or crooked metal parts and pull tight. Then the thing tied to the rope may drag the heavy object behind it."
        )
    ],
    "vine": [
        (
            "Why are bramble vines hard to untangle?",
            "Bramble vines twist around things and their thorns catch on cloth, wood, and rope. That is why patient hands matter more than rushing."
        )
    ],
    "strap": [
        (
            "What does a buckle do on a strap?",
            "A buckle fastens a strap so it stays closed. If the strap catches somewhere, opening the buckle can free it without tearing."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel afraid. It is not pretending fear is gone; it is stepping forward kindly and carefully anyway."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is true but has the wrong idea. Looking closely and asking what really happened can clear it up."
        )
    ],
}

KNOWLEDGE_ORDER = ["harrow", "lantern", "rope", "vine", "strap", "misunderstanding", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    animal = f["animal_cfg"]
    snag = f["snag"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the word "harrow" and centers on a frightening misunderstanding in the night.',
        f"Tell a gentle village tale where {hero.id} hears a terrible scraping sound, bravely goes with {hero.pronoun('possessive')} {elder.label_word}, and discovers that the noise comes from {animal.phrase} caught by {snag.phrase}.",
        f'Write a folk-style story about fear turning into truth and kindness, with a surprise reveal that the feared monster is only an ordinary farm trouble.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    animal = f["animal_cfg"]
    snag = f["snag"]
    rescue = f["rescue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {hero.pronoun('possessive')} {elder.label_word}, and {animal.phrase}. The trouble began because an old harrow was dragged in the dark."
        ),
        (
            "What was the misunderstanding at the start?",
            f"They first thought the scraping noise might be {world.place.rumor}. It sounded frightening in the dark, so they guessed before they could see clearly."
        ),
        (
            f"Why did {hero.id} decide to go toward the sound?",
            f"{hero.id} was afraid, but {hero.pronoun()} thought something might be hurt. That is what made the choice brave: {hero.pronoun()} walked toward the trouble instead of hiding from it."
        ),
        (
            "What was the surprise when they lifted the lantern?",
            f"The surprise was that there was no spirit or monster at all. It was {animal.phrase} with {snag.phrase}, which made the harrow scrape and bang."
        ),
        (
            f"How did {hero.id} help?",
            f"{hero.id} {rescue.qa_text}. That stopped the harrow from rattling and let the frightened {animal.label} grow calm again."
        ),
        (
            "How did the story end?",
            f"The village learned that the night terror had been a simple farm accident. After that, the harrow was tied safely away, and {hero.id} was remembered for brave kindness rather than loud boasts."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"harrow", "lantern", "misunderstanding", "bravery"}
    snag = world.facts["snag"]
    if snag.id == "rope_loop":
        tags.add("rope")
    elif snag.id == "bramble_vine":
        tags.add("vine")
    elif snag.id == "harness_strap":
        tags.add("strap")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="field_lane",
        animal="donkey",
        snag="harness_strap",
        rescue="unbuckle",
        hero_name="Mara",
        hero_gender="girl",
        elder_type="father",
        hero_trait="steady",
    ),
    StoryParams(
        place="orchard_edge",
        animal="goat",
        snag="bramble_vine",
        rescue="untangle",
        hero_name="Tomas",
        hero_gender="boy",
        elder_type="aunt",
        hero_trait="bold",
    ),
    StoryParams(
        place="meadow_ford",
        animal="calf",
        snag="rope_loop",
        rescue="cut_rope",
        hero_name="Nella",
        hero_gender="girl",
        elder_type="uncle",
        hero_trait="timid_but_true",
    ),
    StoryParams(
        place="field_lane",
        animal="goat",
        snag="rope_loop",
        rescue="cut_rope",
        hero_name="Ivo",
        hero_gender="boy",
        elder_type="mother",
        hero_trait="bold",
    ),
    StoryParams(
        place="meadow_ford",
        animal="donkey",
        snag="rope_loop",
        rescue="cut_rope",
        hero_name="Lina",
        hero_gender="girl",
        elder_type="father",
        hero_trait="steady",
    ),
]


def explain_rejection(place_id: Optional[str], animal_id: str, snag_id: str, rescue_id: Optional[str]) -> str:
    if place_id is not None and animal_id not in PLACES[place_id].afford_animals:
        return (
            f"(No story: {PLACES[place_id].label} is not where this world expects a {animal_id} to be wandering at night. "
            f"Pick an animal the place can plausibly host.)"
        )
    if snag_id not in ANIMALS[animal_id].allows_snags:
        return (
            f"(No story: a {animal_id} is not modeled with the snag '{snag_id}'. "
            f"The misunderstanding must grow from a plausible tangle.)"
        )
    if rescue_id is not None and rescue_id not in SNAGS[snag_id].fix_by:
        return (
            f"(No story: the rescue '{rescue_id}' would not free a {snag_id}. "
            f"Choose a rescue that actually solves the problem.)"
        )
    return "(No story: the chosen options do not make a reasonable tale.)"


ASP_RULES = r"""
valid(P,A,S,R) :- place(P), animal(A), snag(S), rescue(R),
                  affords(P,A), allows(A,S), fixes(S,R).

lead :- chosen_trait(T), courage(T,C), chosen_place(P), fear(P,F), C >= F.
outcome(lead) :- lead.
outcome(follow) :- not lead.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("fear", pid, place.fear))
        for aid in sorted(place.afford_animals):
            lines.append(asp.fact("affords", pid, aid))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        for sid in sorted(animal.allows_snags):
            lines.append(asp.fact("allows", aid, sid))
    for sid, snag in SNAGS.items():
        lines.append(asp.fact("snag", sid))
        for rid in sorted(snag.fix_by):
            lines.append(asp.fact("fixes", sid, rid))
    for rid in RESCUES:
        lines.append(asp.fact("rescue", rid))
    for tid, trait in HERO_TRAITS.items():
        lines.append(asp.fact("trait", tid))
        lines.append(asp.fact("courage", tid, trait.courage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_trait", params.hero_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in clingo:", sorted(cset - pset))
        print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != lead_outcome(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome disagreements.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a night misunderstanding, a harrow, and brave kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--hero-trait", choices=HERO_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.animal and args.animal not in PLACES[args.place].afford_animals:
        raise StoryError(explain_rejection(args.place, args.animal, args.snag or next(iter(ANIMALS[args.animal].allows_snags)), args.rescue))
    if args.animal and args.snag and not snag_supported(args.animal, args.snag):
        raise StoryError(explain_rejection(args.place, args.animal, args.snag, args.rescue))
    if args.snag and args.rescue and not rescue_works(args.snag, args.rescue):
        animal_guess = args.animal or next(a for a, cfg in ANIMALS.items() if args.snag in cfg.allows_snags)
        raise StoryError(explain_rejection(args.place, animal_guess, args.snag, args.rescue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.snag is None or combo[2] == args.snag)
        and (args.rescue is None or combo[3] == args.rescue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, animal_id, snag_id, rescue_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(name_pool)
    elder_type = args.elder or rng.choice(["mother", "father", "aunt", "uncle"])
    hero_trait = args.hero_trait or rng.choice(sorted(HERO_TRAITS))
    return StoryParams(
        place=place_id,
        animal=animal_id,
        snag=snag_id,
        rescue=rescue_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if params.hero_trait not in HERO_TRAITS:
        raise StoryError(f"(Unknown hero trait: {params.hero_trait})")
    if params.animal not in PLACES[params.place].afford_animals:
        raise StoryError(explain_rejection(params.place, params.animal, params.snag, params.rescue))
    if not snag_supported(params.animal, params.snag):
        raise StoryError(explain_rejection(params.place, params.animal, params.snag, params.rescue))
    if not rescue_works(params.snag, params.rescue):
        raise StoryError(explain_rejection(params.place, params.animal, params.snag, params.rescue))

    world = tell(
        place=PLACES[params.place],
        animal=ANIMALS[params.animal],
        snag=SNAGS[params.snag],
        rescue=RESCUES[params.rescue],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        hero_trait=HERO_TRAITS[params.hero_trait],
    )
    world.facts["params"] = params
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, animal, snag, rescue) combos:\n")
        for place, animal, snag, rescue in combos:
            print(f"  {place:12} {animal:7} {snag:14} {rescue}")
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
            header = f"### {p.hero_name}: {p.animal} at {p.place} ({p.snag}, {p.rescue}, {lead_outcome(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
