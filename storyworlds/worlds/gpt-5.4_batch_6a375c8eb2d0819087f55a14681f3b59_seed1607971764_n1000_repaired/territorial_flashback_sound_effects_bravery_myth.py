#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py
===============================================================================

A standalone storyworld for a tiny myth-shaped domain: during a dry spell, a
child must approach a territorial guardian of a sacred place. An elder's
flashback reveals the old custom of respect, and the child's bravery determines
whether the guardian shares, grants only a little, or sends the child home to
prepare properly and return at dawn.

This world models:
- physical meters: thirst, danger, calm, full_basket, etc.
- emotional memes: fear, bravery, trust, awe, relief
- a state-driven turn: a guardian reacts to the child's approach
- a flashback that changes what the child dares to do
- sound effects in the narrated world: Hoooo, Rrrrumble, Clack-clack

Run it
------
    python storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py
    python storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py --place echo_cave --guardian stone_lion
    python storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py --gift figs
    python storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py --all
    python storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/territorial_flashback_sound_effects_bravery_myth.py --verify
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
BRAVERY_HIGH = 6
BRAVERY_MID = 4
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
    territorial: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "elder", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    name: str
    boundary: str
    treasure: str
    path: str
    echo: str
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
class Guardian:
    id: str
    label: str
    creature_type: str
    place: str
    sound: str
    motion: str
    old_kindness: str
    accepted_gift: str
    favored_approach: str
    respectful_approaches: set[str] = field(default_factory=set)
    bravery_need: int = BRAVERY_HIGH
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
class Gift:
    id: str
    label: str
    phrase: str
    matches: set[str] = field(default_factory=set)
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
class Approach:
    id: str
    label: str
    sense: int
    respectful: bool
    volume: str
    action_text: str
    wrong_text: str
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


def _r_boundary_threat(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    guardian = world.get("guardian")
    if hero.meters["crossed_boundary"] < THRESHOLD:
        return out
    if guardian.meters["angered"] < THRESHOLD:
        return out
    sig = ("boundary_threat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    world.get("place").meters["danger"] += 1
    out.append("__roar__")
    return out


def _r_calm_opens_path(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.get("guardian")
    if guardian.meters["calm"] < THRESHOLD:
        return out
    sig = ("calm_opens_path",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["danger"] = 0.0
    world.get("spring").meters["reachable"] += 1
    out.append("__open__")
    return out


def _r_water_relieves_thirst(world: World) -> list[str]:
    out: list[str] = []
    spring = world.get("spring")
    hero = world.get("hero")
    if spring.meters["shared"] < THRESHOLD:
        return out
    sig = ("water_relieves",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["thirst"] = 0.0
    hero.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="boundary_threat", tag="social", apply=_r_boundary_threat),
    Rule(name="calm_opens_path", tag="social", apply=_r_calm_opens_path),
    Rule(name="water_relieves", tag="physical", apply=_r_water_relieves_thirst),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "moon_spring": Place(
        id="moon_spring",
        name="the Moon Spring",
        boundary="a ring of white stones",
        treasure="silver water that shone like a fallen moon",
        path="a pale path between reeds",
        echo="Hoooo",
        tags={"spring", "water", "myth"},
    ),
    "cedar_glen": Place(
        id="cedar_glen",
        name="the Cedar Glen",
        boundary="a circle of roots thick as sleeping snakes",
        treasure="a hidden pool under the cedar shade",
        path="a brown path under fragrant branches",
        echo="Shhhh",
        tags={"forest", "water", "myth"},
    ),
    "echo_cave": Place(
        id="echo_cave",
        name="the Echo Cave",
        boundary="a broken line of black stones",
        treasure="a cold basin where drops rang like little bells",
        path="a narrow path under the cliff",
        echo="Drip... drip...",
        tags={"cave", "water", "myth"},
    ),
}

GUARDIANS = {
    "river_serpent": Guardian(
        id="river_serpent",
        label="the river serpent",
        creature_type="serpent",
        place="moon_spring",
        sound="Hissss!",
        motion="coiled above the white stones",
        old_kindness="once lifted its silver head and let thirsty children fill their jars",
        accepted_gift="reeds",
        favored_approach="song",
        respectful_approaches={"song", "bow"},
        bravery_need=6,
        tags={"serpent", "territorial", "myth"},
    ),
    "cedar_stag": Guardian(
        id="cedar_stag",
        label="the cedar stag",
        creature_type="stag",
        place="cedar_glen",
        sound="Clack-clack!",
        motion="struck its bright antlers against a cedar trunk",
        old_kindness="once stepped aside for a village carrying empty cups",
        accepted_gift="figs",
        favored_approach="bow",
        respectful_approaches={"bow", "song"},
        bravery_need=4,
        tags={"stag", "territorial", "myth"},
    ),
    "stone_lion": Guardian(
        id="stone_lion",
        label="the stone lion",
        creature_type="lion",
        place="echo_cave",
        sound="Rrrrumble!",
        motion="rose from the dark as if the cliff itself had grown a mane",
        old_kindness="once guarded the cave by night and shared its basin at dawn",
        accepted_gift="salt",
        favored_approach="drum",
        respectful_approaches={"drum", "bow"},
        bravery_need=6,
        tags={"lion", "territorial", "myth"},
    ),
}

GIFTS = {
    "reeds": Gift(
        id="reeds",
        label="river reeds",
        phrase="a little braid of river reeds",
        matches={"river_serpent"},
        tags={"gift", "reeds"},
    ),
    "figs": Gift(
        id="figs",
        label="sweet figs",
        phrase="a leaf bowl of sweet figs",
        matches={"cedar_stag"},
        tags={"gift", "figs"},
    ),
    "salt": Gift(
        id="salt",
        label="a salt stone",
        phrase="a polished salt stone from the hill",
        matches={"stone_lion"},
        tags={"gift", "salt"},
    ),
}

APPROACHES = {
    "bow": Approach(
        id="bow",
        label="a deep bow",
        sense=3,
        respectful=True,
        volume="quiet",
        action_text="bowed so low that the dust brushed the child's forehead",
        wrong_text="stood still and bowed, but the guardian did not yet know the old rhythm of welcome",
        tags={"respect", "quiet"},
    ),
    "song": Approach(
        id="song",
        label="a soft song",
        sense=3,
        respectful=True,
        volume="soft",
        action_text="sang the old thanks-song in a small steady voice",
        wrong_text="sang politely, but the sound did not fit the guardian's oldest custom",
        tags={"respect", "music"},
    ),
    "drum": Approach(
        id="drum",
        label="a hand drum",
        sense=2,
        respectful=True,
        volume="steady",
        action_text="tapped a hand drum: dum... dum... dum... like a brave heart walking",
        wrong_text="beat the drum with care, yet the guardian listened for a different sign",
        tags={"respect", "music", "sound"},
    ),
    "shout": Approach(
        id="shout",
        label="a loud shout",
        sense=1,
        respectful=False,
        volume="loud",
        action_text="shouted into the sacred place",
        wrong_text="shouted and made the place feel challenged instead of honored",
        tags={"loud"},
    ),
}


def guardian_fits_place(guardian: Guardian, place: Place) -> bool:
    return guardian.place == place.id


def gift_fits_guardian(gift: Gift, guardian: Guardian) -> bool:
    return guardian.id in gift.matches


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for guardian_id, guardian in GUARDIANS.items():
            for gift_id, gift in GIFTS.items():
                if guardian_fits_place(guardian, place) and gift_fits_guardian(gift, guardian):
                    combos.append((place_id, guardian_id, gift_id))
    return combos


def respectful_for(guardian: Guardian, approach: Approach) -> bool:
    return approach.id in guardian.respectful_approaches and approach.respectful


def outcome_for(guardian: Guardian, gift: Gift, approach: Approach, bravery: int) -> str:
    if not gift_fits_guardian(gift, guardian):
        return "return_with_elders"
    if not respectful_for(guardian, approach):
        return "return_with_elders"
    if bravery >= guardian.bravery_need and approach.id == guardian.favored_approach:
        return "shared"
    if bravery >= BRAVERY_MID:
        return "sipped"
    return "return_with_elders"


def predict_reaction(world: World, bravery: int) -> dict:
    sim = world.copy()
    guardian = sim.get("guardian")
    if sim.facts["gift_fit"] and sim.facts["approach_respectful"]:
        guardian.meters["calm"] += 1
        guardian.meters["angered"] = 0.0
    else:
        guardian.meters["angered"] += 1
    sim.get("hero").meters["crossed_boundary"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("place").meters["danger"],
        "can_share": sim.facts["gift_fit"] and sim.facts["approach_respectful"] and bravery >= sim.facts["guardian_cfg"].bravery_need,
    }


def opening(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    hero.meters["thirst"] += 1
    hero.memes["care"] += 1
    world.say(
        f"In the old days, when hills still listened and springs remembered names, "
        f"{hero.id} lived in a village beside dry fields. The jars were light, the leaves were curling, "
        f"and everyone spoke of {place.name}, where {place.treasure} still waited behind {place.boundary}."
    )
    world.say(
        f"But every child knew the place was territorial. No one crossed its border carelessly, "
        f"for a guardian kept watch there."
    )
    world.say(
        f"{elder.id}, the oldest keeper of stories, touched the empty jar and looked toward the hills."
    )


def flashback(world: World, elder: Entity, guardian: Guardian, place: Place, gift: Gift) -> None:
    elder.memes["memory"] += 1
    hero = world.get("hero")
    hero.memes["hope"] += 1
    world.para()
    world.say(
        f'"Listen," said {elder.id}. "When I was small, I went with my own mother to {place.name}."'
    )
    world.say(
        f"The room seemed to dim around the old voice, and the story slipped backward like a lantern into water."
    )
    world.say(
        f'In that flashback, {elder.id} remembered how {guardian.label} {guardian.old_kindness}. '
        f'"We did not snatch or boast," {elder.pronoun()} said. "We carried {gift.phrase}, '
        f'and we thanked the place before asking."'
    )
    world.say(
        f'That memory gave {hero.id} a map for the heart as much as for the feet.'
    )


def set_out(world: World, hero: Entity, place: Place, gift: Gift) -> None:
    hero.memes["bravery"] = float(world.facts["bravery"])
    world.para()
    world.say(
        f"So {hero.id} took {gift.phrase} and followed {place.path}. {place.echo} went the wind through the stones, "
        f"and the empty jar bumped softly against {hero.pronoun('possessive')} knee."
    )
    world.say(
        f"{hero.id} was afraid, but not so afraid as the village was thirsty."
    )


def warning(world: World, guardian: Entity, guardian_cfg: Guardian, approach: Approach) -> None:
    hero = world.get("hero")
    pred = predict_reaction(world, int(hero.memes["bravery"]))
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'At the boundary, {guardian_cfg.label} {guardian_cfg.motion}. "{guardian_cfg.sound}" it cried.'
    )
    world.say(
        f"{hero.id}'s hands trembled around the gift. For one blink, {hero.pronoun()} almost turned back."
    )


def approach_boundary(world: World, approach: Approach) -> None:
    hero = world.get("hero")
    world.say(f"Then {hero.id} {approach.action_text}.")
    hero.meters["crossed_boundary"] += 1
    guardian = world.get("guardian")
    if world.facts["gift_fit"] and world.facts["approach_respectful"]:
        guardian.meters["calm"] += 1
        guardian.meters["angered"] = 0.0
    else:
        guardian.meters["angered"] += 1
    propagate(world, narrate=False)


def shared_ending(world: World, place: Place, guardian_cfg: Guardian) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    spring = world.get("spring")
    guardian.memes["trust"] += 1
    spring.meters["shared"] += 1
    hero.meters["full_jar"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The guardian's fierce shape loosened. The old anger went out of its eyes, and {guardian_cfg.label} moved aside."
    )
    world.say(
        f'"Brave child," the silence seemed to say, "you remembered." {hero.id} filled the jar, and the water flashed silver to the brim.'
    )
    world.para()
    world.say(
        f"When {hero.id} came home, the whole village drank. From that day on, no one called {place.name} a hoard anymore. "
        f"They called it a promise, and even the territorial guardian was greeted as a keeper, not an enemy."
    )


def sip_ending(world: World, place: Place, guardian_cfg: Guardian, approach: Approach) -> None:
    hero = world.get("hero")
    spring = world.get("spring")
    spring.meters["shared"] += 1
    hero.meters["sip"] += 1
    hero.memes["relief"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{guardian_cfg.label} did not fully smile, if such a being could smile, but it stopped growling."
    )
    world.say(
        f"It let {hero.id} kneel for one careful drink and wet the cloth over the jar's mouth, though not fill it all the way. "
        f"{approach.wrong_text.capitalize()}, yet the gift had been true, and truth earned a little mercy."
    )
    world.para()
    world.say(
        f"{hero.id} ran back with a cool forehead and a wiser plan. At dawn, the villagers would come together with songs, bowls, and thanks, "
        f"and the old custom would be mended properly."
    )


def return_ending(world: World, place: Place, guardian_cfg: Guardian, gift: Gift, approach: Approach, elder: Entity) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    guardian.meters["angered"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{guardian_cfg.sound} rang again, and the sacred place felt narrow as a closed fist.'
    )
    reason = []
    if not world.facts["gift_fit"]:
        reason.append(f"the gift was not the one this guardian remembered")
    if not world.facts["approach_respectful"]:
        reason.append("the approach sounded more like a challenge than thanks")
    because = " and ".join(reason) if reason else "the moment was not ready"
    world.say(
        f"{hero.id} did not run in panic. {hero.pronoun().capitalize()} stepped back from the boundary, because {because}."
    )
    world.para()
    world.say(
        f"Back in the village, {hero.id} told {elder.id} everything. Together they prepared the older, truer welcome for morning. "
        f"The tale did not end with water that night, but with bravery wiser than grabbing: the bravery to return, learn, and come again."
    )


def tell(
    place: Place,
    guardian_cfg: Guardian,
    gift: Gift,
    approach: Approach,
    *,
    hero_name: str = "Iria",
    hero_gender: str = "girl",
    elder_name: str = "Orun",
    elder_type: str = "elder",
    bravery: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["kind", "steady"],
        attrs={},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        traits=["wise"],
        attrs={},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_cfg.creature_type,
        label=guardian_cfg.label,
        role="guardian",
        territorial=True,
        attrs={},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.name,
        attrs={},
    ))
    spring = world.add(Entity(
        id="spring",
        kind="thing",
        type="water",
        label=place.treasure,
        attrs={},
    ))

    world.facts["place_cfg"] = place
    world.facts["guardian_cfg"] = guardian_cfg
    world.facts["gift_cfg"] = gift
    world.facts["approach_cfg"] = approach
    world.facts["gift_fit"] = gift_fits_guardian(gift, guardian_cfg)
    world.facts["approach_respectful"] = respectful_for(guardian_cfg, approach)
    world.facts["bravery"] = bravery

    opening(world, hero, elder, place)
    flashback(world, elder, guardian_cfg, place, gift)
    set_out(world, hero, place, gift)
    warning(world, guardian, guardian_cfg, approach)

    world.para()
    approach_boundary(world, approach)

    outcome = outcome_for(guardian_cfg, gift, approach, bravery)
    world.facts["outcome"] = outcome

    if outcome == "shared":
        shared_ending(world, place, guardian_cfg)
    elif outcome == "sipped":
        sip_ending(world, place, guardian_cfg, approach)
    else:
        return_ending(world, place, guardian_cfg, gift, approach, elder)

    world.facts.update(
        hero=hero,
        elder=elder,
        guardian=guardian,
        spring=spring,
        shared=spring.meters["shared"] >= THRESHOLD,
        danger=place_ent.meters["danger"],
    )
    return world


KNOWLEDGE = {
    "territorial": [(
        "What does territorial mean?",
        "Territorial means someone or something feels very strongly that a place is theirs and wants to guard it. A territorial animal or guardian may act fierce when others come too close."
    )],
    "myth": [(
        "What is a myth?",
        "A myth is an old kind of story that explains a place, a custom, or a mystery with wonder. Myths often have guardians, brave children, and special promises."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is a short trip to an earlier time inside the story. It helps readers understand something important that happened before."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery is doing the right thing even while you feel afraid. It does not mean never being scared."
    )],
    "sound": [(
        "Why do stories use sound effects like 'Rrrrumble!' or 'Hissss!'?",
        "They help you hear the scene in your mind. Sound words can make a guardian feel near, loud, and alive."
    )],
    "spring": [(
        "What is a spring?",
        "A spring is a place where water comes out of the ground. People and animals may depend on it when the weather is dry."
    )],
    "gift": [(
        "Why might a gift matter in an old sacred story?",
        "In many old stories, a gift shows respect before someone asks for help. It says, 'I remember the custom, and I am not here to grab.'"
    )],
}
KNOWLEDGE_ORDER = ["territorial", "myth", "flashback", "bravery", "sound", "spring", "gift"]


@dataclass
class StoryParams:
    place: str
    guardian: str
    gift: str
    approach: str
    hero_name: str
    hero_gender: str
    elder_name: str
    bravery: int
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


CURATED = [
    StoryParams(
        place="moon_spring",
        guardian="river_serpent",
        gift="reeds",
        approach="song",
        hero_name="Iria",
        hero_gender="girl",
        elder_name="Orun",
        bravery=7,
        seed=None,
    ),
    StoryParams(
        place="cedar_glen",
        guardian="cedar_stag",
        gift="figs",
        approach="song",
        hero_name="Tarin",
        hero_gender="boy",
        elder_name="Mira",
        bravery=5,
        seed=None,
    ),
    StoryParams(
        place="echo_cave",
        guardian="stone_lion",
        gift="salt",
        approach="drum",
        hero_name="Seli",
        hero_gender="girl",
        elder_name="Doran",
        bravery=6,
        seed=None,
    ),
    StoryParams(
        place="cedar_glen",
        guardian="cedar_stag",
        gift="figs",
        approach="bow",
        hero_name="Nami",
        hero_gender="girl",
        elder_name="Orun",
        bravery=3,
        seed=None,
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    guardian_cfg = world.facts["guardian_cfg"]
    place = world.facts["place_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "shared":
        end = "and ends with the guardian sharing water because the child remembers the old custom."
    elif outcome == "sipped":
        end = "and ends with the child earning a little mercy and a wiser plan for dawn."
    else:
        end = "and ends with the child bravely turning back to prepare the right welcome instead of grabbing."
    return [
        f'Write a short myth for a 3-to-5-year-old that uses the word "territorial" and includes a flashback, sound effects, and bravery.',
        f"Tell a gentle myth where {hero.id} must approach {guardian_cfg.label} at {place.name}, hears the guardian's cry, and remembers an elder's flashback about respect.",
        f"Write a child-facing myth about a territorial sacred place, a brave child, and an old custom of asking before taking, {end}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    guardian_cfg = world.facts["guardian_cfg"]
    place = world.facts["place_cfg"]
    gift = world.facts["gift_cfg"]
    approach = world.facts["approach_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a brave child, and {guardian_cfg.label} that watched over {place.name}. It also includes {elder.id}, whose old memory helped guide what {hero.id} did."
        ),
        (
            f"Why did {hero.id} go to {place.name}?",
            f"{hero.id} went because the village was thirsty and water still waited there. The need for water was bigger than {hero.pronoun('possessive')} fear."
        ),
        (
            "What was the flashback about?",
            f"The flashback was {elder.id}'s memory of a time when {guardian_cfg.label} shared instead of blocking the way. It taught that people should bring {gift.phrase} and thank the place before asking."
        ),
        (
            f"What sound did the guardian make, and how did that change the moment?",
            f'The guardian cried "{guardian_cfg.sound}" at the boundary. That sound made the place feel dangerous and tested whether {hero.id} would stay brave.'
        ),
        (
            f"What did {hero.id} do at the boundary?",
            f"{hero.id} brought {gift.phrase} and used {approach.label}. That choice mattered because the guardian judged not only the gift, but also whether the child came with respect."
        ),
    ]
    if outcome == "shared":
        qa.append((
            "How did the story end?",
            f"The guardian remembered the old custom and moved aside, so {hero.id} filled the jar. The ending shows that bravery joined with respect can turn a territorial guard into a keeper who shares."
        ))
    elif outcome == "sipped":
        qa.append((
            "Did the guardian fully share the water?",
            f"No, not fully. The guardian allowed only a small drink and a little mercy because the child was respectful, but the oldest welcome had not been completed in exactly the right way."
        ))
        qa.append((
            "What did the child learn?",
            f"{hero.id} learned that bravery is not only stepping forward. It is also listening to what the moment still needs and returning with a wiser plan."
        ))
    else:
        qa.append((
            "Why did the child turn back instead of grabbing the water?",
            f"{hero.id} turned back because grabbing would have broken the old custom and made the danger worse. That was brave too, because {hero.pronoun()} chose wisdom over rushing."
        ))
        qa.append((
            "How did the story still end hopefully?",
            f"It ended with {hero.id} and {elder.id} preparing to return properly at dawn. The hope comes from learning the right way instead of forcing the wrong one."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"territorial", "myth", "flashback", "bravery", "sound", "gift", "spring"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.territorial:
            bits.append("territorial=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo_rejection(place: Place, guardian: Guardian, gift: Gift) -> str:
    if guardian.place != place.id:
        return (
            f"(No story: {guardian.label} does not belong to {place.name}. In this world, each sacred place has its own guardian.)"
        )
    if guardian.id not in gift.matches:
        return (
            f"(No story: {gift.label} is not the remembered gift for {guardian.label}. The old custom has to fit the guardian's tradition.)"
        )
    return "(No story: this combination does not fit the world's sacred custom.)"


def explain_approach_rejection(approach: Approach) -> str:
    return (
        f"(Refusing approach '{approach.id}': it scores too low on common sense for this child-facing myth "
        f"(sense={approach.sense} < {SENSE_MIN}). Try one of: "
        f"{', '.join(sorted(a.id for a in sensible_approaches()))}.)"
    )


ASP_RULES = r"""
guardian_fits_place(G, P) :- guardian(G), place(P), belongs(G, P).
gift_fits_guardian(Gf, Gu) :- gift(Gf), guardian(Gu), accepts(Gu, Gf).
valid(P, Gu, Gf) :- guardian_fits_place(Gu, P), gift_fits_guardian(Gf, Gu).

sensible_approach(A) :- approach(A), sense(A, S), sense_min(M), S >= M.
respectful_for(Gu, A) :- respects(Gu, A), respectful(A).

outcome(return_with_elders) :- chosen_guardian(Gu), chosen_gift(Gf),
                               not gift_fits_guardian(Gf, Gu).
outcome(return_with_elders) :- chosen_guardian(Gu), chosen_gift(Gf),
                               gift_fits_guardian(Gf, Gu),
                               chosen_approach(A), not respectful_for(Gu, A).
outcome(shared) :- chosen_guardian(Gu), chosen_gift(Gf), gift_fits_guardian(Gf, Gu),
                   chosen_approach(A), respectful_for(Gu, A),
                   bravery(B), favored(Gu, A), bravery_need(Gu, N), B >= N.
outcome(sipped) :- chosen_guardian(Gu), chosen_gift(Gf), gift_fits_guardian(Gf, Gu),
                   chosen_approach(A), respectful_for(Gu, A),
                   bravery(B), bravery_mid(M), B >= M,
                   not outcome(shared).
outcome(return_with_elders) :- chosen_guardian(Gu), chosen_gift(Gf), gift_fits_guardian(Gf, Gu),
                               chosen_approach(A), respectful_for(Gu, A),
                               bravery(B), bravery_mid(M), B < M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for guardian_id, guardian in GUARDIANS.items():
        lines.append(asp.fact("guardian", guardian_id))
        lines.append(asp.fact("belongs", guardian_id, guardian.place))
        lines.append(asp.fact("bravery_need", guardian_id, guardian.bravery_need))
        lines.append(asp.fact("favored", guardian_id, guardian.favored_approach))
        for approach_id in sorted(guardian.respectful_approaches):
            lines.append(asp.fact("respects", guardian_id, approach_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for guardian_id in sorted(gift.matches):
            lines.append(asp.fact("accepts", guardian_id, gift_id))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("sense", approach_id, approach.sense))
        if approach.respectful:
            lines.append(asp.fact("respectful", approach_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_mid", BRAVERY_MID))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_approaches() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_approach/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_approach"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_guardian", params.guardian),
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_approach", params.approach),
        asp.fact("bravery", params.bravery),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a territorial guardian, an elder's flashback, and a brave child in a myth."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--bravery", type=int, choices=list(range(2, 8)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Iria", "Seli", "Nami", "Tala", "Mira", "Ena"]
BOY_NAMES = ["Tarin", "Oren", "Daro", "Lio", "Soran", "Kelan"]
ELDER_NAMES = ["Orun", "Mira", "Doran", "Selu", "Aven"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.guardian and args.gift:
        place = PLACES[args.place]
        guardian = GUARDIANS[args.guardian]
        gift = GIFTS[args.gift]
        if not (guardian_fits_place(guardian, place) and gift_fits_guardian(gift, guardian)):
            raise StoryError(explain_combo_rejection(place, guardian, gift))
    elif args.place and args.guardian:
        place = PLACES[args.place]
        guardian = GUARDIANS[args.guardian]
        if not guardian_fits_place(guardian, place):
            gift = GIFTS[args.gift] if args.gift else next(iter(GIFTS.values()))
            raise StoryError(explain_combo_rejection(place, guardian, gift))
    if args.approach and APPROACHES[args.approach].sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(APPROACHES[args.approach]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.guardian is None or combo[1] == args.guardian)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, guardian_id, gift_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(a.id for a in sensible_approaches()))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    bravery = args.bravery if args.bravery is not None else rng.randint(3, 7)

    return StoryParams(
        place=place_id,
        guardian=guardian_id,
        gift=gift_id,
        approach=approach_id,
        hero_name=hero_name,
        hero_gender=gender,
        elder_name=elder_name,
        bravery=bravery,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        guardian = GUARDIANS[params.guardian]
        gift = GIFTS[params.gift]
        approach = APPROACHES[params.approach]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not guardian_fits_place(guardian, place) or not gift_fits_guardian(gift, guardian):
        raise StoryError(explain_combo_rejection(place, guardian, gift))
    if approach.sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(approach))

    world = tell(
        place=place,
        guardian_cfg=guardian,
        gift=gift,
        approach=approach,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_name=params.elder_name,
        bravery=params.bravery,
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
    py_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py_combos == clingo_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_combos - clingo_combos:
            print("  only in python:", sorted(py_combos - clingo_combos))
        if clingo_combos - py_combos:
            print("  only in clingo:", sorted(clingo_combos - py_combos))

    py_sense = {a.id for a in sensible_approaches()}
    clingo_sense = set(asp_sensible_approaches())
    if py_sense == clingo_sense:
        print(f"OK: sensible approaches match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible approaches: python={sorted(py_sense)} clingo={sorted(clingo_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random params for seed {seed}.")
            break

    bad = 0
    for params in cases:
        py = outcome_for(GUARDIANS[params.guardian], GIFTS[params.gift], APPROACHES[params.approach], params.bravery)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} clingo={cl}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_approach/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_approaches()
        print(f"sensible approaches: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, guardian, gift) combos:\n")
        for place, guardian, gift in combos:
            print(f"  {place:12} {guardian:14} {gift}")
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
            header = f"### {p.hero_name}: {p.guardian} at {p.place} ({outcome_for(GUARDIANS[p.guardian], GIFTS[p.gift], APPROACHES[p.approach], p.bravery)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
