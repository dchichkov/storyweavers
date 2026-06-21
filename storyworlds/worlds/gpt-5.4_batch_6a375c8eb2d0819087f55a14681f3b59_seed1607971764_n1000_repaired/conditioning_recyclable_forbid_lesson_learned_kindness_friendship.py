#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py
================================================================================================

A standalone storyworld in a myth-like mode: two young friends find a heat-weary
creature near a shrine after a festival. One child wants the fastest shortcut:
take a sacred cloth from the altar steps. The other remembers that the elder did
forbid touching holy things. Instead, they use recyclable festival leftovers,
kind hands, and patience to help the creature reach cool shade and water.

The domain is intentionally small and constraint-checked:

* Different creatures need different kinds of help.
* A recyclable aid must physically fit the creature's needs.
* A comforting action must match what would truly calm or restore that creature.
* Sacred items are known to the world, but they are never a valid fix.

The stories aim for a complete arc:
beginning (festival aftermath and friendship),
middle turn (temptation toward the forbidden shortcut),
and ending (kindness succeeds, the creature recovers, and the friends change).

Run it
------
    python storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py
    python storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py --creature fledgling --aid basket --comfort hush_song
    python storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py --aid reed_sled
    python storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py --all
    python storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py --qa --json
    python storyworlds/worlds/gpt-5.4/conditioning_recyclable_forbid_lesson_learned_kindness_friendship.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "priestess": "keeper", "priest": "keeper"}.get(self.type, self.type)
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
class Creature:
    id: str
    label: str
    phrase: str
    place: str
    problem: str
    need_carrier: bool
    need_gentle: bool
    min_shade: int
    required_comfort: str
    ending_image: str
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
class RecyclableAid:
    id: str
    label: str
    phrase: str
    material: str
    carrier: bool
    gentle: bool
    shade: int
    move_text: str
    shelter_text: str
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
class Comfort:
    id: str
    label: str
    action_text: str
    effect_text: str
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
class SacredThing:
    id: str
    label: str
    phrase: str
    belongs_to: str
    danger: str
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
class StoryParams:
    creature: str
    aid: str
    comfort: str
    forbidden: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    elder: str
    elder_type: str
    trait1: str = "eager"
    trait2: str = "gentle"
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


def _r_heat_worsens(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["exposed"] < THRESHOLD:
        return []
    sig = ("heat_worsens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["thirst"] += 1
    creature.meters["fear"] += 1
    for friend in (world.get("friend1"), world.get("friend2")):
        friend.memes["concern"] += 1
    return ["__heat__"]


def _r_aid_shelters(world: World) -> list[str]:
    creature = world.get("creature")
    aid = world.get("aid")
    if aid.meters["used"] < THRESHOLD:
        return []
    sig = ("aid_shelters",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["exposed"] = 0.0
    creature.meters["shade"] += aid.attrs["shade"]
    if aid.attrs["carrier"]:
        creature.meters["moved"] += 1
    if aid.attrs["gentle"]:
        creature.meters["comforted"] += 1
    return []


def _r_comfort_helps(world: World) -> list[str]:
    creature = world.get("creature")
    comfort = world.get("comfort")
    if comfort.meters["used"] < THRESHOLD:
        return []
    sig = ("comfort_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if comfort.attrs["id"] == creature.attrs["required_comfort"]:
        creature.meters["comforted"] += 1
        creature.meters["thirst"] = max(0.0, creature.meters["thirst"] - 1.0)
        creature.meters["fear"] = max(0.0, creature.meters["fear"] - 1.0)
    return []


def _r_recover(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["exposed"] >= THRESHOLD:
        return []
    if creature.meters["shade"] < creature.attrs["min_shade"]:
        return []
    if creature.attrs["need_carrier"] and creature.meters["moved"] < THRESHOLD:
        return []
    if creature.attrs["need_gentle"] and creature.meters["comforted"] < THRESHOLD:
        return []
    if creature.attrs["required_comfort"] and creature.meters["comforted"] < THRESHOLD:
        return []
    sig = ("recover",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["safe"] += 1
    creature.meters["thirst"] = 0.0
    creature.meters["fear"] = 0.0
    for friend in (world.get("friend1"), world.get("friend2")):
        friend.memes["kindness"] += 1
        friend.memes["friendship"] += 1
        friend.memes["relief"] += 1
    return ["__recover__"]


CAUSAL_RULES = [
    Rule(name="heat_worsens", tag="physical", apply=_r_heat_worsens),
    Rule(name="aid_shelters", tag="physical", apply=_r_aid_shelters),
    Rule(name="comfort_helps", tag="emotional", apply=_r_comfort_helps),
    Rule(name="recover", tag="resolution", apply=_r_recover),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def aid_fits(creature: Creature, aid: RecyclableAid) -> bool:
    if creature.need_carrier and not aid.carrier:
        return False
    if creature.need_gentle and not aid.gentle:
        return False
    if aid.shade < creature.min_shade:
        return False
    return True


def comfort_fits(creature: Creature, comfort: Comfort) -> bool:
    return creature.required_comfort == comfort.id


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for cid, creature in CREATURES.items():
        for aid_id, aid in AIDS.items():
            if not aid_fits(creature, aid):
                continue
            for comfort_id, comfort in COMFORTS.items():
                if comfort_fits(creature, comfort):
                    out.append((cid, aid_id, comfort_id))
    return sorted(out)


def predict_recovery(world: World, creature: Creature, aid: RecyclableAid, comfort: Comfort) -> bool:
    sim = world.copy()
    sim.get("aid").attrs.update({
        "shade": aid.shade,
        "carrier": aid.carrier,
        "gentle": aid.gentle,
        "id": aid.id,
    })
    sim.get("comfort").attrs.update({"id": comfort.id})
    sim.get("aid").meters["used"] += 1
    sim.get("comfort").meters["used"] += 1
    propagate(sim, narrate=False)
    return sim.get("creature").meters["safe"] >= THRESHOLD


def festival_intro(world: World, elder: Entity, friend1: Entity, friend2: Entity, aid: RecyclableAid) -> None:
    for friend in (friend1, friend2):
        friend.memes["joy"] += 1
        friend.memes["friendship"] += 1
    world.say(
        f"In the age when the hill-shrine still listened to footsteps, {friend1.id} and "
        f"{friend2.id} were known as the closest of friends."
    )
    world.say(
        f"That morning, {elder.id} had taught them the patient conditioning of old festival scraps "
        f"so even discarded things might serve again. {friend1.id} loved how {aid.material} could be "
        f"turned into something recyclable and useful instead of being left to flutter in the dust."
    )


def discover_creature(world: World, friend1: Entity, friend2: Entity, creature: Creature) -> None:
    world.say(
        f"When the sun climbed high, the two friends found {creature.phrase} beside {creature.place}. "
        f"It looked {creature.problem}."
    )
    world.say(
        f"{friend2.id} knelt at once. \"Poor little one,\" {friend2.pronoun()} whispered. "
        f"{friend1.id} could see the creature needed help before the stones grew hotter."
    )


def temptation(world: World, friend1: Entity, friend2: Entity, forbidden: SacredThing, elder: Entity) -> None:
    friend1.memes["impatience"] += 1
    world.say(
        f'{friend1.id} pointed toward {forbidden.phrase}. "{forbidden.label.capitalize()} would make shade faster," '
        f'{friend1.pronoun()} said.'
    )
    world.say(
        f'{friend2.id} caught {friend1.pronoun("possessive")} sleeve. "No," {friend2.pronoun()} said softly. '
        f'"Did not {elder.id} forbid us to touch {forbidden.label}? It belongs to {forbidden.belongs_to}, '
        f'and {forbidden.danger}."'
    )


def choose_recyclable_help(world: World, friend1: Entity, friend2: Entity, aid: RecyclableAid, comfort: Comfort) -> None:
    friend2.memes["wisdom"] += 1
    world.say(
        f"Then {friend2.id} remembered the workbench under the fig tree. There lay {aid.phrase}, "
        f"mended from {aid.material}, and ready to be used with care."
    )
    world.say(
        f'"Let us use the recyclable thing we already healed," {friend2.id} said. '
        f'"I will help, and you help me."'
    )
    friend1.memes["shame"] += 1
    friend1.memes["friendship"] += 1
    world.say(
        f"{friend1.id} looked at the sacred cloth again, then bowed {friend1.pronoun('possessive')} head. "
        f'"You are right," {friend1.pronoun()} said. "A quick hand is not always a kind hand."'
    )
    world.facts["planned_comfort"] = comfort.id


def use_aid(world: World, aid: RecyclableAid) -> None:
    aid_ent = world.get("aid")
    aid_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(aid.move_text)
    world.say(aid.shelter_text)


def use_comfort(world: World, comfort: Comfort) -> None:
    comfort_ent = world.get("comfort")
    comfort_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(comfort.action_text)
    world.say(comfort.effect_text)


def elder_praise(world: World, elder: Entity, friend1: Entity, friend2: Entity) -> None:
    world.say(
        f"{elder.id} came from the shrine steps and saw what the friends had done. "
        f'"You remembered both kindness and measure," {elder.pronoun()} said.'
    )
    world.say(
        f'"The lesson is simple: when friendship is true, it does not grab what is forbidden. '
        f'It mends, shares, and helps."'
    )
    friend1.memes["lesson"] += 1
    friend2.memes["lesson"] += 1


def ending(world: World, friend1: Entity, friend2: Entity, creature: Creature) -> None:
    world.say(
        f"Soon {creature.ending_image}. The creature was safe, and the hard heat no longer ruled it."
    )
    world.say(
        f"As evening gold spread over the stones, {friend1.id} and {friend2.id} walked home side by side, "
        f"carrying nothing stolen and feeling richer for it."
    )


def tell(
    creature_cfg: Creature,
    aid_cfg: RecyclableAid,
    comfort_cfg: Comfort,
    forbidden_cfg: SacredThing,
    friend1_name: str,
    friend1_gender: str,
    friend2_name: str,
    friend2_gender: str,
    elder_name: str,
    elder_type: str,
    trait1: str,
    trait2: str,
) -> World:
    world = World()
    friend1 = world.add(Entity(id=friend1_name, kind="character", type=friend1_gender, role="friend1", traits=[trait1], label=friend1_name))
    friend2 = world.add(Entity(id=friend2_name, kind="character", type=friend2_gender, role="friend2", traits=[trait2], label=friend2_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder", traits=["patient"], label="the elder"))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="creature",
        label=creature_cfg.label,
        attrs={
            "required_comfort": creature_cfg.required_comfort,
            "need_carrier": creature_cfg.need_carrier,
            "need_gentle": creature_cfg.need_gentle,
            "min_shade": creature_cfg.min_shade,
        },
    ))
    aid = world.add(Entity(
        id="aid",
        kind="thing",
        type="aid",
        label=aid_cfg.label,
        attrs={
            "shade": aid_cfg.shade,
            "carrier": aid_cfg.carrier,
            "gentle": aid_cfg.gentle,
            "id": aid_cfg.id,
        },
    ))
    comfort = world.add(Entity(
        id="comfort",
        kind="thing",
        type="comfort",
        label=comfort_cfg.label,
        attrs={"id": comfort_cfg.id},
    ))
    creature.meters["exposed"] = 1.0
    creature.meters["thirst"] = 0.0
    creature.meters["fear"] = 0.0
    creature.meters["shade"] = 0.0
    creature.meters["moved"] = 0.0
    creature.meters["comforted"] = 0.0
    creature.meters["safe"] = 0.0
    aid.meters["used"] = 0.0
    comfort.meters["used"] = 0.0
    friend1.memes["concern"] = 0.0
    friend2.memes["concern"] = 0.0
    friend1.memes["friendship"] = 1.0
    friend2.memes["friendship"] = 1.0
    friend1.memes["kindness"] = 0.0
    friend2.memes["kindness"] = 0.0
    friend1.memes["lesson"] = 0.0
    friend2.memes["lesson"] = 0.0

    world.facts.update(
        creature_cfg=creature_cfg,
        aid_cfg=aid_cfg,
        comfort_cfg=comfort_cfg,
        forbidden_cfg=forbidden_cfg,
        friend1=friend1,
        friend2=friend2,
        elder=elder,
    )

    festival_intro(world, elder, friend1, friend2, aid_cfg)
    world.para()
    discover_creature(world, friend1, friend2, creature_cfg)
    propagate(world, narrate=False)

    world.para()
    temptation(world, friend1, friend2, forbidden_cfg, elder)
    choose_recyclable_help(world, friend1, friend2, aid_cfg, comfort_cfg)

    world.para()
    use_aid(world, aid_cfg)
    use_comfort(world, comfort_cfg)

    if creature.meters["safe"] < THRESHOLD:
        raise StoryError("The chosen help did not truly save the creature; no honest story can be told.")

    world.para()
    elder_praise(world, elder, friend1, friend2)
    ending(world, friend1, friend2, creature_cfg)

    world.facts.update(
        recovered=creature.meters["safe"] >= THRESHOLD,
        lesson_learned=friend1.memes["lesson"] >= THRESHOLD and friend2.memes["lesson"] >= THRESHOLD,
        kind_act=friend1.memes["kindness"] >= THRESHOLD and friend2.memes["kindness"] >= THRESHOLD,
        friendship_stronger=friend1.memes["friendship"] > 1.0 and friend2.memes["friendship"] > 1.0,
    )
    return world


CREATURES = {
    "fledgling": Creature(
        id="fledgling",
        label="fledgling",
        phrase="a sun-dazed fledgling",
        place="the lion-carved steps",
        problem="too weak to hop and too frightened to cry",
        need_carrier=True,
        need_gentle=True,
        min_shade=1,
        required_comfort="hush_song",
        ending_image="the fledgling tucked itself beneath a fig branch and answered the evening with one brave peep",
        tags={"bird", "shade", "song"},
    ),
    "tortoise": Creature(
        id="tortoise",
        label="tortoise",
        phrase="a dusty young tortoise",
        place="the white altar stones",
        problem="dry-mouthed and slow under the hammering noon",
        need_carrier=False,
        need_gentle=False,
        min_shade=2,
        required_comfort="spring_water",
        ending_image="the tortoise lifted its head, drank, and set off toward the cool moss by the spring",
        tags={"tortoise", "water", "shade"},
    ),
    "rabbit": Creature(
        id="rabbit",
        label="rabbit kit",
        phrase="a trembling rabbit kit",
        place="the cracked offering jars",
        problem="too startled to dash for cover",
        need_carrier=True,
        need_gentle=True,
        min_shade=2,
        required_comfort="hush_song",
        ending_image="the rabbit kit slipped into the thyme-shadow and twitched its nose as if the world were gentle again",
        tags={"rabbit", "shade", "song"},
    ),
}

AIDS = {
    "basket": RecyclableAid(
        id="basket",
        label="basket hood",
        phrase="an old fig basket turned upside down into a basket hood",
        material="split willow and patched festival cord",
        carrier=True,
        gentle=True,
        shade=2,
        move_text="Together they lifted the basket hood and carried the small creature as carefully as if they were carrying a promise.",
        shelter_text="The woven shade broke the sun into soft brown strips.",
        tags={"basket", "recyclable"},
    ),
    "parasol": RecyclableAid(
        id="parasol",
        label="mended parasol",
        phrase="a mended parasol made from yesterday's parade paper",
        material="bamboo ribs and stitched parade paper",
        carrier=False,
        gentle=True,
        shade=3,
        move_text="They opened the mended parasol and walked slowly beside the creature, keeping the fierce light off its back.",
        shelter_text="Under the round paper shadow, the stones no longer burned like little suns.",
        tags={"parasol", "recyclable"},
    ),
    "cloth_canopy": RecyclableAid(
        id="cloth_canopy",
        label="patchwork canopy",
        phrase="a patchwork canopy sewn from worn sailcloth and ribbon scraps",
        material="reused sailcloth and ribbon scraps",
        carrier=False,
        gentle=True,
        shade=3,
        move_text="They raised the patchwork canopy between them like a small cloud and moved with it over the creature.",
        shelter_text="The stitched cloth caught the glare and turned it into cool dimness.",
        tags={"cloth", "recyclable"},
    ),
    "reed_sled": RecyclableAid(
        id="reed_sled",
        label="reed sled",
        phrase="a rough reed sled tied from broken market trays",
        material="broken river-reed trays",
        carrier=True,
        gentle=False,
        shade=1,
        move_text="They dragged the reed sled across the stones.",
        shelter_text="It gave only a thin stripe of shade.",
        tags={"reed", "recyclable"},
    ),
}

COMFORTS = {
    "hush_song": Comfort(
        id="hush_song",
        label="hush song",
        action_text="While they moved, one friend sang the low hush song the shrine women used for frightened nestlings.",
        effect_text="The creature's shaking slowed, as if the song had laid a feather over its heart.",
        tags={"song", "comfort"},
    ),
    "spring_water": Comfort(
        id="spring_water",
        label="spring water",
        action_text="At the fig-root spring they cupped cool water in their hands and let the creature drink a little at a time.",
        effect_text="The water shone on its mouth like silver mercy, and strength returned by drops.",
        tags={"water", "comfort"},
    ),
    "leaf_fan": Comfort(
        id="leaf_fan",
        label="leaf fan",
        action_text="They fanned the air with broad leaves.",
        effect_text="The breeze was kind, but it could not truly mend what the creature needed most.",
        tags={"breeze", "comfort"},
    ),
}

FORBIDDEN = {
    "banner": SacredThing(
        id="banner",
        label="the shrine banner",
        phrase="the blue shrine banner on the altar rail",
        belongs_to="the Wind Lady",
        danger="holy cloth should not be snatched for ordinary use",
        tags={"sacred"},
    ),
    "garland": SacredThing(
        id="garland",
        label="the moon garland",
        phrase="the moon garland hanging over the prayer bowl",
        belongs_to="the Moon Daughter",
        danger="its threads are an offering, not a tool",
        tags={"sacred"},
    ),
    "veil": SacredThing(
        id="veil",
        label="the dawn veil",
        phrase="the dawn veil folded beside the lamp niche",
        belongs_to="the Dawn Mother",
        danger="to seize it would show hunger instead of reverence",
        tags={"sacred"},
    ),
}

GIRL_NAMES = ["Ione", "Nysa", "Thale", "Mira", "Dara", "Elia", "Cyra", "Lysa"]
BOY_NAMES = ["Aren", "Tarin", "Soren", "Pelas", "Niko", "Damon", "Ilar", "Theron"]
TRAITS_1 = ["eager", "swift", "bright", "restless"]
TRAITS_2 = ["gentle", "careful", "kind", "steady"]


def explain_rejection(creature: Creature, aid: RecyclableAid, comfort: Comfort) -> str:
    reasons: list[str] = []
    if creature.need_carrier and not aid.carrier:
        reasons.append(f"{creature.label} must be carried or guided under cover, but {aid.label} cannot carry it")
    if creature.need_gentle and not aid.gentle:
        reasons.append(f"{creature.label} is too fragile for {aid.label}")
    if aid.shade < creature.min_shade:
        reasons.append(f"{aid.label} does not cast enough shade for {creature.label}")
    if creature.required_comfort != comfort.id:
        reasons.append(f"{creature.label} needs {COMFORTS[creature.required_comfort].label}, not {comfort.label}")
    if not reasons:
        reasons.append("this combination does not fit the world")
    return "(No story: " + "; ".join(reasons) + ".)"


def ensure_keys(params: StoryParams) -> None:
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if params.forbidden not in FORBIDDEN:
        raise StoryError(f"(Unknown forbidden item: {params.forbidden})")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["creature_cfg"]
    aid = f["aid_cfg"]
    comfort = f["comfort_cfg"]
    friend1 = f["friend1"]
    friend2 = f["friend2"]
    forbidden = f["forbidden_cfg"]
    return [
        f'Write a short myth-like story for a young child that includes the words "conditioning", "recyclable", and "forbid".',
        f"Tell a gentle myth in which two friends, {friend1.id} and {friend2.id}, find {c.phrase} in danger, refuse to take {forbidden.label}, and instead use {aid.phrase}.",
        f"Write a story about kindness and friendship where a creature is saved with {comfort.label} and a recyclable aid rather than a forbidden shortcut.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c = f["creature_cfg"]
    aid = f["aid_cfg"]
    comfort = f["comfort_cfg"]
    forbidden = f["forbidden_cfg"]
    friend1 = f["friend1"]
    friend2 = f["friend2"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the main friends in the story?",
            f"The main friends are {friend1.id} and {friend2.id}. They act together from the moment they see the creature, which shows their friendship is one of the story's strongest powers.",
        ),
        (
            "What trouble did they find near the shrine?",
            f"They found {c.phrase} beside {c.place}, and it looked {c.problem}. The hot stones and bright sun made the creature unsafe, so the children had to help quickly.",
        ),
        (
            f"Why did {friend2.id} stop {friend1.id} from taking {forbidden.label}?",
            f"{friend2.id} remembered that {elder.id} had said they must not touch it. {forbidden.label.capitalize()} belonged to {forbidden.belongs_to}, so taking it for an easy fix would have been unkind as well as disobedient.",
        ),
        (
            "How did the friends help the creature?",
            f"They used {aid.phrase} and then gave the creature {comfort.label}. That worked because the aid matched the creature's body and the comfort matched what it truly needed.",
        ),
        (
            "What lesson did the friends learn?",
            f"They learned that kindness is better than grabbing what is forbidden. They also learned that real friendship means listening, mending what you already have, and helping together.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "recyclable": [
        (
            "What does recyclable mean?",
            "Recyclable means something can be used again instead of being thrown away. When people mend or remake old things, they give the material another life.",
        )
    ],
    "conditioning": [
        (
            "What can conditioning mean when people are making something by hand?",
            "Conditioning can mean preparing a material slowly so it becomes ready to use. For example, people may soak, soften, or shape old material before turning it into something helpful.",
        )
    ],
    "forbid": [
        (
            "What does forbid mean?",
            "To forbid something is to say it must not be done. A wise person may forbid an action to protect people, animals, or holy things.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help instead of harm. It often means noticing another creature's need and doing the gentle thing even when a faster selfish choice is possible.",
        )
    ],
    "friendship": [
        (
            "How can friendship help solve a problem?",
            "Friendship helps because friends can listen to each other, share work, and make better choices together. A true friend can stop you from doing the wrong thing and still stay by your side.",
        )
    ],
    "shade": [
        (
            "Why is shade important on a hot day?",
            "Shade blocks the strongest sunlight and helps a body cool down. Small creatures can become weak very quickly in hard heat, so shade can protect them.",
        )
    ],
    "spring_water": [
        (
            "Why should a thirsty animal drink a little at a time?",
            "A weak animal may need small gentle sips so it can recover safely. Going slowly is a careful kind of help.",
        )
    ],
    "song": [
        (
            "Why can a soft song calm a frightened animal?",
            "A soft, steady sound can make the world feel less scary. It does not solve every problem, but it can help a frightened creature feel safer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["conditioning", "recyclable", "forbid", "kindness", "friendship", "shade", "spring_water", "song"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"conditioning", "recyclable", "forbid", "kindness", "friendship", "shade"}
    comfort_id = world.facts["comfort_cfg"].id
    if comfort_id == "spring_water":
        tags.add("spring_water")
    if comfort_id == "hush_song":
        tags.add("song")
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
        attrs = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        creature="fledgling",
        aid="basket",
        comfort="hush_song",
        forbidden="banner",
        friend1="Aren",
        friend1_gender="boy",
        friend2="Ione",
        friend2_gender="girl",
        elder="Sera",
        elder_type="priestess",
        trait1="swift",
        trait2="gentle",
    ),
    StoryParams(
        creature="tortoise",
        aid="parasol",
        comfort="spring_water",
        forbidden="garland",
        friend1="Mira",
        friend1_gender="girl",
        friend2="Niko",
        friend2_gender="boy",
        elder="Thena",
        elder_type="priestess",
        trait1="bright",
        trait2="steady",
    ),
    StoryParams(
        creature="rabbit",
        aid="basket",
        comfort="hush_song",
        forbidden="veil",
        friend1="Theron",
        friend1_gender="boy",
        friend2="Cyra",
        friend2_gender="girl",
        elder="Olan",
        elder_type="priest",
        trait1="eager",
        trait2="kind",
    ),
    StoryParams(
        creature="tortoise",
        aid="cloth_canopy",
        comfort="spring_water",
        forbidden="banner",
        friend1="Lysa",
        friend1_gender="girl",
        friend2="Damon",
        friend2_gender="boy",
        elder="Sera",
        elder_type="priestess",
        trait1="restless",
        trait2="careful",
    ),
]


ASP_RULES = r"""
aid_fits(C, A) :- creature(C), aid(A),
                  need_carrier(C), carrier(A),
                  need_gentle(C), gentle(A),
                  min_shade(C, Need), shade(A, Have), Have >= Need.
aid_fits(C, A) :- creature(C), aid(A),
                  not need_carrier(C), not need_gentle(C),
                  min_shade(C, Need), shade(A, Have), Have >= Need.
aid_fits(C, A) :- creature(C), aid(A),
                  need_carrier(C), not need_gentle(C),
                  carrier(A),
                  min_shade(C, Need), shade(A, Have), Have >= Need.
aid_fits(C, A) :- creature(C), aid(A),
                  not need_carrier(C), need_gentle(C),
                  gentle(A),
                  min_shade(C, Need), shade(A, Have), Have >= Need.

comfort_fits(C, K) :- needs_comfort(C, K), comfort(K).
valid(C, A, K) :- creature(C), aid(A), comfort(K), aid_fits(C, A), comfort_fits(C, K).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.need_carrier:
            lines.append(asp.fact("need_carrier", cid))
        if c.need_gentle:
            lines.append(asp.fact("need_gentle", cid))
        lines.append(asp.fact("min_shade", cid, c.min_shade))
        lines.append(asp.fact("needs_comfort", cid, c.required_comfort))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.carrier:
            lines.append(asp.fact("carrier", aid_id))
        if aid.gentle:
            lines.append(asp.fact("gentle", aid_id))
        lines.append(asp.fact("shade", aid_id, aid.shade))
    for comfort_id in COMFORTS:
        lines.append(asp.fact("comfort", comfort_id))
    return "\n".join(lines)


def asp_program(extra_show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra_show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like storyworld: friends choose recyclable kindness over a forbidden shortcut."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--elder", choices=["priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.aid and args.comfort:
        creature = CREATURES[args.creature]
        aid = AIDS[args.aid]
        comfort = COMFORTS[args.comfort]
        if (args.creature, args.aid, args.comfort) not in set(valid_combos()):
            raise StoryError(explain_rejection(creature, aid, comfort))

    combos = [
        combo for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.aid is None or combo[1] == args.aid)
        and (args.comfort is None or combo[2] == args.comfort)
    ]
    if not combos:
        if args.creature and args.aid and args.comfort:
            raise StoryError(explain_rejection(CREATURES[args.creature], AIDS[args.aid], COMFORTS[args.comfort]))
        raise StoryError("(No valid combination matches the given options.)")

    creature, aid, comfort = rng.choice(sorted(combos))
    forbidden = args.forbidden or rng.choice(sorted(FORBIDDEN))
    g1 = rng.choice(["girl", "boy"])
    g2 = rng.choice(["girl", "boy"])
    friend1 = _pick_name(rng, g1)
    friend2 = _pick_name(rng, g2, avoid=friend1)
    elder_type = args.elder or rng.choice(["priestess", "priest"])
    elder_name = rng.choice(["Sera", "Olan", "Thena", "Moro", "Iria"])
    return StoryParams(
        creature=creature,
        aid=aid,
        comfort=comfort,
        forbidden=forbidden,
        friend1=friend1,
        friend1_gender=g1,
        friend2=friend2,
        friend2_gender=g2,
        elder=elder_name,
        elder_type=elder_type,
        trait1=rng.choice(TRAITS_1),
        trait2=rng.choice(TRAITS_2),
    )


def generate(params: StoryParams) -> StorySample:
    ensure_keys(params)
    if (params.creature, params.aid, params.comfort) not in set(valid_combos()):
        raise StoryError(explain_rejection(CREATURES[params.creature], AIDS[params.aid], COMFORTS[params.comfort]))

    world = tell(
        creature_cfg=CREATURES[params.creature],
        aid_cfg=AIDS[params.aid],
        comfort_cfg=COMFORTS[params.comfort],
        forbidden_cfg=FORBIDDEN[params.forbidden],
        friend1_name=params.friend1,
        friend1_gender=params.friend1_gender,
        friend2_name=params.friend2,
        friend2_gender=params.friend2_gender,
        elder_name=params.elder,
        elder_type=params.elder_type,
        trait1=params.trait1,
        trait2=params.trait2,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        try:
            sample = generate(params)
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL: curated generation crashed for {params}: {err}")
            continue
        if not sample.story.strip():
            rc = 1
            print(f"SMOKE FAIL: empty story for {params}")
    try:
        random_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        random_params.seed = 7
        sample = generate(random_params)
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False)
        finally:
            sys.stdout = old_stdout
        if not buf.getvalue().strip():
            rc = 1
            print("SMOKE FAIL: emit() produced no text.")
        else:
            print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE FAIL: random generate/emit crashed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, aid, comfort) combos:\n")
        for creature, aid, comfort in combos:
            print(f"  {creature:10} {aid:12} {comfort}")
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
            header = f"### {p.friend1} & {p.friend2}: {p.creature} with {p.aid} + {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
