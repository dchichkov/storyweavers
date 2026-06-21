#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py
==============================================================================

A standalone storyworld about Hazel, a brave child in a superhero cape who hears
a frightened pet in the attic and wants to make a daring rescue alone.

Every story includes the words "saltine", "attic", and "Hazel", and keeps a
child-facing superhero tone. The world model prefers sensible adult rescue
methods, allows a near-miss branch where a wiser sidekick stops Hazel in time,
and also supports a bad ending when brave-but-careless action goes wrong.

Run it
------
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py --pet puppy
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py --response cape_loop
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py --all
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py --trace
    python storyworlds/worlds/gpt-5.4/saltine_attic_hazel_bravery_bad_ending_superhero.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Theme:
    id: str
    base: str
    boast: str
    mission_name: str
    ending_image: str
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
class PetCfg:
    id: str
    label: str
    cry: str
    move: str
    hide_spot: str
    comfort: str
    skittish: int
    suitable_responses: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "sidekick"}]

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


def _r_attic_danger(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.role == "hero"), None)
    pet = next((e for e in world.entities.values() if e.role == "pet"), None)
    attic = world.entities.get("attic")
    if hero is None or pet is None or attic is None:
        return out
    if hero.meters["in_attic"] < THRESHOLD or pet.memes["panic"] < THRESHOLD:
        return out
    sig = ("attic_danger", hero.id, pet.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    attic.meters["danger"] += 1
    hero.memes["fear"] += 1
    for kid in world.kids():
        if kid.role == "sidekick":
            kid.memes["fear"] += 1
    out.append("__danger__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="attic_danger", tag="physical", apply=_r_attic_danger),
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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for pet_id, pet in PETS.items():
            for rid, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and rid in pet.suitable_responses:
                    combos.append((theme_id, pet_id, rid))
    return combos


def rescue_severity(pet: PetCfg, delay: int) -> int:
    return pet.skittish + delay


def is_contained(response: Response, pet: PetCfg, delay: int) -> bool:
    return response.power >= rescue_severity(pet, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, sidekick_age: int, trait: str) -> bool:
    sidekick_older = relation == "siblings" and sidekick_age > hero_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if sidekick_older else 0.0)
    return sidekick_older and authority > BRAVERY_INIT


def predict_attic(world: World) -> dict:
    sim = world.copy()
    hero = next(e for e in sim.characters() if e.role == "hero")
    hero.meters["in_attic"] += 1
    propagate(sim, narrate=False)
    attic = sim.get("attic")
    pet = next(e for e in sim.entities.values() if e.role == "pet")
    return {
        "danger": attic.meters["danger"],
        "pet_panic": pet.memes["panic"],
    }


def setup_scene(world: World, theme: Theme, hero: Entity, sidekick: Entity, pet: PetCfg) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"Hazel tied on a towel cape and turned the upstairs hall into {theme.base}. "
        f"{theme.boast}"
    )
    world.say(
        f"In her pocket she had one last saltine from snack time, because every hero, "
        f"she said, needed an emergency cracker."
    )
    world.say(
        f"Then a soft {pet.cry} came from the attic hatch. {pet.The} had slipped up "
        f"there and was now hiding {pet.hide_spot}."
    )


def declare_mission(world: World, theme: Theme, hero: Entity, pet: PetCfg) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'"{theme.mission_name}!" Hazel whispered. "I will save {pet.the} myself."'
    )
    world.say(
        "The words made her feel tall and shining, the way heroes do in comic books."
    )


def warn_sidekick(world: World, sidekick: Entity, parent: Entity, pet: PetCfg) -> None:
    pred = predict_attic(world)
    sidekick.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{sidekick.id} looked up at the dark attic opening and shook '
        f'{sidekick.pronoun("possessive")} head. "Wait for {parent.label_word}," '
        f'{sidekick.pronoun()} said. "It is dusty up there, {pet.the} is scared, '
        f'and the boards could creak under you."'
    )


def back_down(world: World, hero: Entity, sidekick: Entity, parent: Entity, pet: PetCfg) -> None:
    hero.memes["bravery"] = 0.0
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(
        f'Hazel put one foot on the first rung, then looked at {sidekick.id}. '
        f'Because {sidekick.id} was her older sibling, the warning landed hard. '
        f'She took her foot back down and whispered, "A real hero can wait for help."'
    )
    world.say(
        f"They called for {parent.label_word}, kept the attic hatch closed, and stayed "
        f"together on the landing instead of climbing."
    )


def climb(world: World, hero: Entity, pet: Entity, pet_cfg: PetCfg) -> None:
    hero.meters["in_attic"] += 1
    hero.memes["defiance"] += 1
    pet.memes["panic"] += 1
    propagate(world, narrate=False)
    world.say(
        "Before anyone could stop her, Hazel climbed the narrow ladder and pushed her "
        "head into the attic."
    )
    world.say(
        f"Dust floated in the flashlight beam from the hall. {pet_cfg.The} darted "
        f"{pet_cfg.move}, and the boards gave a long, unhappy creak under Hazel's shoes."
    )


def alarm(world: World, sidekick: Entity, parent: Entity, pet: PetCfg) -> None:
    world.say(
        f'"Hazel, come down!" {sidekick.id} cried. Then {sidekick.pronoun().capitalize()} '
        f'shouted for {parent.label_word}: "{parent.label_word.capitalize()}! '
        f'{pet_cfg.The} is scared, and Hazel is in the attic!"'
    )


def rescue(world: World, parent: Entity, response: Response, pet_cfg: PetCfg, theme: Theme) -> None:
    hero = next(e for e in world.characters() if e.role == "hero")
    pet = next(e for e in world.entities.values() if e.role == "pet")
    attic = world.get("attic")
    hero.meters["in_attic"] = 0.0
    attic.meters["danger"] = 0.0
    pet.memes["panic"] = 0.0
    hero.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came fast but calm and {response.text.replace('{pet}', pet_cfg.label)}."
    )
    world.say(
        f"In another moment Hazel was back on the landing, clutching the rail, while "
        f"{pet.the} was safe at last."
    )
    world.say(
        f'"That was a brave heart and a risky choice," {parent.label_word} said. '
        f'"Superheroes do not rescue alone when a grown-up can help."'
    )
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    world.say(
        f"That evening Hazel drew a new badge for her cape: {theme.ending_image}."
    )


def rescue_fail(world: World, parent: Entity, response: Response, pet_cfg: PetCfg) -> None:
    hero = next(e for e in world.characters() if e.role == "hero")
    pet = next(e for e in world.entities.values() if e.role == "pet")
    attic = world.get("attic")
    attic.meters["danger"] += 1
    hero.memes["fear"] += 1
    hero.meters["hurt"] += 1
    pet.memes["panic"] += 1
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {response.fail.replace('{pet}', pet_cfg.label)}."
    )
    world.say(
        "But the frightened scramble came first. Hazel lunged, the board shifted, and "
        "she slipped down hard onto the ladder, scraping her arm and twisting her ankle."
    )


def bad_ending(world: World, parent: Entity, sidekick: Entity, pet_cfg: PetCfg) -> None:
    hero = next(e for e in world.characters() if e.role == "hero")
    hero.meters["in_attic"] = 0.0
    hero.memes["lesson"] += 1
    hero.memes["sadness"] += 1
    sidekick.memes["sadness"] += 1
    world.say(
        f"{parent.label_word.capitalize()} got Hazel down safely, but the rescue was ruined. "
        f"{pet_cfg.The} stayed hidden until late that night, and Hazel had to sit with an ice pack "
        f"instead of finishing her game."
    )
    world.say(
        f"The torn towel cape hung over a chair, dusty and crooked. Hazel stared at the attic "
        f"door and wished she had been brave enough to wait."
    )


def safe_after_averted(world: World, parent: Entity, pet_cfg: PetCfg, response: Response) -> None:
    world.say(
        f"A minute later, {parent.label_word} handled the whole thing sensibly and "
        f"{response.qa_text.replace('{pet}', pet_cfg.label)}."
    )
    world.say(
        f"Hazel gave {pet.the} the little saltine crumb she had been carrying, then laughed "
        f"at herself. The best part of the mission was that nobody had to get hurt."
    )
    hero = next(e for e in world.characters() if e.role == "hero")
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    hero.memes["love"] += 1


def tell(
    theme: Theme,
    pet_cfg: PetCfg,
    response: Response,
    *,
    sidekick_name: str = "Milo",
    sidekick_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    hero_age: int = 6,
    sidekick_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="Hazel",
        kind="character",
        type="girl",
        role="hero",
        age=hero_age,
        attrs={"relation": relation},
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        role="sidekick",
        age=sidekick_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    pet = world.add(Entity(
        id="pet",
        type="pet",
        label=pet_cfg.label,
        role="pet",
    ))
    attic = world.add(Entity(
        id="attic",
        type="place",
        label="the attic",
        attrs={"dark": True},
    ))

    hero.memes["bravery"] = BRAVERY_INIT
    sidekick.memes["caution"] = initial_caution(trait)
    pet.memes["panic"] = float(pet_cfg.skittish)

    world.facts.update(
        theme=theme,
        pet_cfg=pet_cfg,
        response=response,
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        pet=pet,
        attic=attic,
        relation=relation,
        delay=delay,
    )

    setup_scene(world, theme, hero, sidekick, pet_cfg)
    world.para()
    declare_mission(world, theme, hero, pet_cfg)
    warn_sidekick(world, sidekick, parent, pet_cfg)

    averted = would_avert(relation, hero_age, sidekick_age, trait)

    if averted:
        back_down(world, hero, sidekick, parent, pet_cfg)
        world.para()
        safe_after_averted(world, parent, pet_cfg, response)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        world.para()
        climb(world, hero, pet, pet_cfg)
        alarm(world, sidekick, parent, pet_cfg)
        severity = rescue_severity(pet_cfg, delay)
        contained = is_contained(response, pet_cfg, delay)
        world.para()
        if contained:
            rescue(world, parent, response, pet_cfg, theme)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, pet_cfg)
            bad_ending(world, parent, sidekick, pet_cfg)
            outcome = "bad"

    world.facts.update(
        outcome=outcome,
        rescued=contained,
        severity=severity,
        promised=hero.memes["lesson"] >= THRESHOLD,
        averted=averted,
        scraped=hero.meters["hurt"] >= THRESHOLD,
    )
    return world


THEMES = {
    "midnight_city": Theme(
        id="midnight_city",
        base="Midnight City, where the stairs were rooftops and the banister was a silver sky-bridge",
        boast="She named herself Captain Comet and told her sidekick the house was under watch.",
        mission_name="Attic Rescue",
        ending_image='CAREFUL HEROES CALL FOR BACKUP',
        tags={"superhero"},
    ),
    "storm_tower": Theme(
        id="storm_tower",
        base="Storm Tower, a secret headquarters above the sleeping rooms",
        boast="She swished her cape and promised to guard every corner before bedtime.",
        mission_name="Thunder Mission",
        ending_image='BRAVE MEANS WISE, NOT ALONE',
        tags={"superhero"},
    ),
    "star_base": Theme(
        id="star_base",
        base="Star Base, where each bedroom door was a launch bay for tiny heroes",
        boast="She whispered that danger never rested, so neither could Captain Hazel.",
        mission_name="Sky Hatch Save",
        ending_image='REAL HEROES WAIT FOR HELP',
        tags={"superhero"},
    ),
}

PETS = {
    "kitten": PetCfg(
        id="kitten",
        label="kitten",
        cry="mew-mew",
        move="behind a stack of winter blankets",
        hide_spot="behind a stack of winter blankets",
        comfort="soft and shivery",
        skittish=2,
        suitable_responses={"towel_bundle", "carrier"},
        tags={"kitten", "pet"},
    ),
    "puppy": PetCfg(
        id="puppy",
        label="puppy",
        cry="whine-whine",
        move="between two old trunks",
        hide_spot="between two old trunks",
        comfort="wriggly and worried",
        skittish=3,
        suitable_responses={"leash_treat", "carrier"},
        tags={"puppy", "pet"},
    ),
    "rabbit": PetCfg(
        id="rabbit",
        label="rabbit",
        cry="thump-thump",
        move="under the cedar chest",
        hide_spot="under the cedar chest",
        comfort="small and jumpy",
        skittish=2,
        suitable_responses={"towel_bundle", "carrier"},
        tags={"rabbit", "pet"},
    ),
}

RESPONSES = {
    "carrier": Response(
        id="carrier",
        sense=3,
        power=4,
        text="opened the pet carrier, spoke softly to the {pet}, and guided it inside before helping Hazel back down",
        fail="opened the pet carrier, but the {pet} bolted deeper into the shadows before Hazel could move away",
        qa_text="used the pet carrier and a calm voice to bring the {pet} down",
        tags={"carrier", "pet"},
    ),
    "towel_bundle": Response(
        id="towel_bundle",
        sense=3,
        power=3,
        text="wrapped a towel around her arm, scooped the {pet} close, and brought both rescues down one careful step at a time",
        fail="tried to bundle the {pet} in a towel, but it sprang away and made Hazel lurch after it",
        qa_text="wrapped the {pet} safely in a towel and carried it down",
        tags={"towel", "pet"},
    ),
    "leash_treat": Response(
        id="leash_treat",
        sense=2,
        power=3,
        text="knelt below the hatch with the leash and a dog treat until the {pet} inched back toward the ladder",
        fail="shook the leash and treat, but the {pet} spun away and the attic panic only grew",
        qa_text="used a leash and treat to coax the {pet} down",
        tags={"leash", "pet"},
    ),
    "cape_loop": Response(
        id="cape_loop",
        sense=1,
        power=1,
        text="threw Hazel's cape up like a loop, hoping to snag the {pet}",
        fail="threw Hazel's cape up like a loop, which only startled the {pet} more",
        qa_text="tried to use Hazel's cape like a loop",
        tags={"cape", "pet"},
    ),
}

SIDEKICK_NAMES = {
    "girl": ["Ivy", "Nora", "June", "Maya", "Lucy"],
    "boy": ["Milo", "Theo", "Ben", "Eli", "Noah"],
}
TRAITS = ["careful", "steady", "sensible", "curious", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    theme: str
    pet: str
    response: str
    sidekick_name: str
    sidekick_gender: str
    parent: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    sidekick_age: int = 4
    relation: str = "siblings"
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
    "attic": [(
        "What is an attic?",
        "An attic is a space under the roof where people often keep boxes and old things. It can be dark and cramped, so children should not explore it alone."
    )],
    "saltine": [(
        "What is a saltine?",
        "A saltine is a thin, crunchy cracker. It is a simple snack, not a superhero tool."
    )],
    "carrier": [(
        "What is a pet carrier for?",
        "A pet carrier is a safe box for moving a pet from one place to another. It helps keep a scared animal from running away."
    )],
    "towel": [(
        "Why might a grown-up use a towel to help a scared pet?",
        "A towel can help hold a small pet gently and safely. It can also protect a person's hands from scratches."
    )],
    "leash": [(
        "What does a leash do?",
        "A leash helps a person guide a dog safely. It keeps the dog from running off while someone is helping it."
    )],
    "pet": [(
        "Why can pets hide when they are scared?",
        "Pets hide because dark, tucked-away places can feel safe to them. When they are frightened, they often run instead of listening."
    )],
    "backup": [(
        "Why is asking for help brave?",
        "Asking for help is brave because it means you care more about safety than about showing off. Real courage is making the wise choice, even when it feels less exciting."
    )],
}
KNOWLEDGE_ORDER = ["attic", "saltine", "pet", "carrier", "towel", "leash", "backup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    pet = f["pet_cfg"]
    outcome = f["outcome"]
    response = f["response"]
    if outcome == "averted":
        return [
            f'Write a superhero story for a 3-to-5-year-old about Hazel hearing {pet.the} in the attic and wanting to make a daring rescue, but an older sidekick talks her into waiting for help. Include the word "saltine".',
            f"Tell a gentle near-miss story where Hazel thinks bravery means climbing alone, then learns that backup is part of being a hero.",
            f'Write a short story with a bright superhero voice where Hazel begins "{theme.mission_name}" but ends by choosing the safer plan.'
        ]
    if outcome == "bad":
        return [
            f'Write a cautionary superhero story for a 3-to-5-year-old where Hazel tries to rescue {pet.the} from the attic alone. Include the words "saltine" and "attic", and give it a bad ending.',
            f"Tell a superhero story where bravery turns into a poor choice, the rescue goes wrong, and Hazel ends the night sad and sore.",
            f'Write a simple story that teaches that real heroes ask for help before climbing into dark places.'
        ]
    return [
        f'Write a superhero story for a 3-to-5-year-old where Hazel hears {pet.the} in the attic, starts a rescue mission, and a grown-up helps safely. Include the word "saltine".',
        f"Tell a story where Hazel feels brave like a comic-book hero, but learns that careful help saves the day.",
        f'Write a short child-facing story with a superhero tone, a frightened pet, and a calm rescue from the attic.'
    ]


def pair_noun(sidekick: Entity, relation: str) -> str:
    if relation == "siblings":
        return "her sibling"
    return "her friend"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sidekick = f["sidekick"]
    parent = f["parent"]
    pet = f["pet_cfg"]
    response = f["response"]
    theme = f["theme"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Hazel, {pair_noun(sidekick, relation)} {sidekick.id}, and {pet.the} in the attic. Hazel was pretending to be a superhero when the trouble began."
        ),
        (
            "Why did Hazel think she had a mission?",
            f"She heard {pet.the} crying from the attic while she was already playing hero in {theme.base}. That made the rescue feel like a superhero mission instead of an ordinary problem."
        ),
        (
            "Why did the attic feel dangerous?",
            f"The attic was dark and dusty, and {pet.the} was already scared. Because the pet was panicking, Hazel's climb made the boards creak and the danger feel bigger."
        ),
        (
            "What was the saltine for?",
            "Hazel had the saltine in her pocket from snack time because she liked the idea of an emergency hero cracker. It shows how much she wanted the game to feel real."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"How was Hazel brave without climbing into the attic?",
            f"Hazel was brave because she listened, stopped at the ladder, and waited for backup. She changed her mind even after making a big heroic promise, which is a hard kind of courage."
        ))
        qa.append((
            f"What did {parent.label_word} do?",
            f"{parent.label_word.capitalize()} {response.qa_text.replace('{pet}', pet.label)}. The grown-up solved the problem safely because the rescue was handled before panic could grow."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with Hazel laughing and learning that heroes can ask for help. The rescue still happened, but nobody had to get hurt."
        ))
    elif outcome == "contained":
        qa.append((
            f"How did {parent.label_word} rescue {pet.the}?",
            f"{parent.label_word.capitalize()} {response.qa_text.replace('{pet}', pet.label)}. The calm method worked because it matched the frightened pet and came in time."
        ))
        qa.append((
            "What did Hazel learn?",
            "Hazel learned that a brave heart is not enough by itself. She needed help because real heroes think about safety before they charge ahead."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with Hazel safe on the landing and the rescue finished well. The new badge on her cape showed that she understood bravery in a wiser way."
        ))
    else:
        qa.append((
            "What went wrong with Hazel's rescue?",
            f"The rescue went wrong because Hazel climbed up alone while {pet.the} was frightened and jumpy. When the panic grew, she lunged at the wrong moment and slipped."
        ))
        qa.append((
            "Why is the ending a bad ending?",
            "It is a bad ending because Hazel got hurt, the game stopped, and the rescue was spoiled. The torn cape and ice pack show that her brave feeling did not lead to a happy result."
        ))
        qa.append((
            "What did Hazel learn at the end?",
            "Hazel learned that waiting for help would have been the braver choice. She understood the lesson, but she had to learn it the hard way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    response = f["response"]
    tags = {"attic", "saltine", "pet", "backup"} | set(response.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="midnight_city",
        pet="kitten",
        response="carrier",
        sidekick_name="Milo",
        sidekick_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        hero_age=6,
        sidekick_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="storm_tower",
        pet="puppy",
        response="leash_treat",
        sidekick_name="Ivy",
        sidekick_gender="girl",
        parent="father",
        trait="gentle",
        delay=0,
        hero_age=6,
        sidekick_age=6,
        relation="friends",
    ),
    StoryParams(
        theme="star_base",
        pet="puppy",
        response="leash_treat",
        sidekick_name="Theo",
        sidekick_gender="boy",
        parent="mother",
        trait="thoughtful",
        delay=1,
        hero_age=6,
        sidekick_age=5,
        relation="siblings",
    ),
    StoryParams(
        theme="storm_tower",
        pet="rabbit",
        response="towel_bundle",
        sidekick_name="Nora",
        sidekick_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
        hero_age=5,
        sidekick_age=7,
        relation="siblings",
    ),
]


def explain_pet_response(pet: PetCfg, response: Response) -> str:
    return (
        f"(No story: {response.id} is not a sensible rescue for {pet.the}. "
        f"Pick one of: {', '.join(sorted(pet.suitable_responses))}.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.sidekick_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    pet = PETS[params.pet]
    return "contained" if is_contained(response, pet, params.delay) else "bad"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
fits(P,R) :- suitable(P,R).
valid(T,P,R) :- theme(T), pet(P), response(R), sensible(R), fits(P,R).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
sidekick_older :- relation(siblings), hero_age(HA), sidekick_age(SA), SA > HA.
bonus(4) :- sidekick_older.
bonus(0) :- not sidekick_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- sidekick_older, authority(A), bravery_init(BR), A > BR.

severity(Sk + D) :- chosen_pet(P), skittish(P,Sk), delay(D).
resp_power(Pw) :- chosen_response(R), power(R,Pw).
contained :- resp_power(Pw), severity(Sv), Pw >= Sv.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(bad) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, pet in PETS.items():
        lines.append(asp.fact("pet", pid))
        lines.append(asp.fact("skittish", pid, pet.skittish))
        for rid in sorted(pet.suitable_responses):
            lines.append(asp.fact("suitable", pid, rid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_pet", params.pet),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("sidekick_age", params.sidekick_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(150):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: Hazel, a superhero rescue mission, and the attic. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="how long the panic grows before the rescue works")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_sidekick(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    return rng.choice(SIDEKICK_NAMES[gender]), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.pet and args.response:
        pet = PETS[args.pet]
        response = RESPONSES[args.response]
        if args.response not in pet.suitable_responses:
            raise StoryError(explain_pet_response(pet, response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.pet is None or combo[1] == args.pet)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, pet, response = rng.choice(sorted(combos))
    sidekick_name, sidekick_gender = _pick_sidekick(rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, sidekick_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme,
        pet=pet,
        response=response,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        sidekick_age=sidekick_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet: {params.pet})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    pet = PETS[params.pet]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.response not in pet.suitable_responses:
        raise StoryError(explain_pet_response(pet, response))

    world = tell(
        THEMES[params.theme],
        pet,
        response,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        sidekick_age=params.sidekick_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, pet, response) combos:\n")
        for theme, pet, response in combos:
            print(f"  {theme:14} {pet:8} {response}")
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
            header = f"### Hazel: {p.pet} in attic ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
