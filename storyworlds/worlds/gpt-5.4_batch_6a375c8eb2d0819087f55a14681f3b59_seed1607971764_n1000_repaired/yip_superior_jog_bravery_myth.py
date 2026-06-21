#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py
===========================================================

A standalone storyworld in a small mythic domain: a child is sent up a sacred
path before dawn, hears a trapped fox spirit give a sharp yip, chooses bravery
over boasting, and uses the right gift to calm the path's danger and wake the
morning.

The domain is intentionally small and constraint-checked. Each route has one
true hazard, and only gifts that honestly counter that hazard are allowed. A
story is not just a paragraph with swapped nouns: the child frees the fox
spirit, gains courage, meets the hazard, uses the gift, and changes the world
by reaching the shrine.

Run it
------
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py --route sky_steps
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py --gift sun_lantern
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py --route briar_pass --gift sun_lantern
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py --all
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/yip_superior_jog_bravery_myth.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Route:
    id: str
    place: str
    opening: str
    shrine: str
    hazard: str
    hazard_face: str
    omen: str
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
class Hazard:
    id: str
    label: str
    threat: str
    failure: str
    calm_text: str
    knowledge: str
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
    protects: set[str] = field(default_factory=set)
    use_text: str = ""
    gift_text: str = ""
    knowledge: str = ""
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


def _r_bless_fox(world: World) -> list[str]:
    hero = world.get("hero")
    fox = world.get("fox")
    if fox.meters["freed"] < THRESHOLD:
        return []
    sig = ("fox_blessing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    hero.memes["kindness"] += 1
    fox.memes["gratitude"] += 1
    world.facts["fox_guided"] = True
    return ["__fox_blessing__"]


def _r_calm_hazard(world: World) -> list[str]:
    hero = world.get("hero")
    hazard = world.get("hazard")
    gift = world.get("gift")
    if hero.meters["at_hazard"] < THRESHOLD:
        return []
    if hazard.meters["calmed"] >= THRESHOLD:
        return []
    if hazard.id not in gift.attrs.get("protects", set()):
        return []
    sig = ("calm_hazard", hazard.id, gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hazard.meters["calmed"] += 1
    hero.memes["bravery"] += 1
    return ["__hazard_calmed__"]


def _r_threaten(world: World) -> list[str]:
    hero = world.get("hero")
    hazard = world.get("hazard")
    if hero.meters["at_hazard"] < THRESHOLD:
        return []
    if hazard.meters["calmed"] >= THRESHOLD:
        return []
    sig = ("threaten", hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.meters["stalled"] += 1
    return ["__hazard_threat__"]


RULES = [
    Rule(name="fox_blessing", tag="social", apply=_r_bless_fox),
    Rule(name="calm_hazard", tag="physical", apply=_r_calm_hazard),
    Rule(name="threaten", tag="physical", apply=_r_threaten),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s == "__fox_blessing__":
                fox = world.get("fox")
                hero = world.get("hero")
                world.say(
                    f"The little fox shook free, gave another bright yip, and touched "
                    f"{hero.id}'s ankle with {fox.pronoun('possessive')} nose. Warm courage "
                    f"ran into {hero.id} like sunrise through a crack in a door."
                )
            elif s == "__hazard_calmed__":
                hazard_cfg = world.facts["hazard_cfg"]
                world.say(hazard_cfg.calm_text)
            elif s == "__hazard_threat__":
                hazard_cfg = world.facts["hazard_cfg"]
                world.say(hazard_cfg.failure)
    return produced


ROUTES = {
    "sky_steps": Route(
        id="sky_steps",
        place="the Sky Steps",
        opening="a stair of pale stone that climbed straight toward the stars",
        shrine="the Shrine of Morning",
        hazard="wind_wall",
        hazard_face="the high stair where the wind shoved like giant hands",
        omen="blue prayer ribbons snapping hard in the dark",
        ending="the first gold light poured down the steps like grain from a bright bowl",
        tags={"mountain", "wind", "shrine"},
    ),
    "echo_cave": Route(
        id="echo_cave",
        place="the Echo Cave",
        opening="a tunnel of black rock where even whispers seemed to wander",
        shrine="the Chamber of Dawn",
        hazard="night_gloom",
        hazard_face="the bend where the dark grew thick enough to feel like cloth",
        omen="a black bend where even moonlight stopped",
        ending="the cave mouth blushed pink, and the sleeping swallows burst into the air",
        tags={"cave", "dark", "shrine"},
    ),
    "briar_pass": Route(
        id="briar_pass",
        place="the Briar Pass",
        opening="a narrow pass where ancient thorn-vines braided themselves across the road",
        shrine="the Gate of Spring",
        hazard="thorn_ring",
        hazard_face="the choke-point where the brambles hooked and hissed",
        omen="thorns knitting together as if they had fingers",
        ending="new green leaves opened all along the pass, and dew shone on every thorn",
        tags={"briar", "thorn", "shrine"},
    ),
}

HAZARDS = {
    "wind_wall": Hazard(
        id="wind_wall",
        label="the wind wall",
        threat="a storm-wind that could push a child from the sacred stair",
        failure="The air roared around the stones, and for a breath the climb seemed too dangerous to touch.",
        calm_text="The wild wind bowed around the gift and opened a quiet path up the stair.",
        knowledge="High mountain wind can shove hard enough to make walking unsafe.",
        tags={"wind"},
    ),
    "night_gloom": Hazard(
        id="night_gloom",
        label="the night gloom",
        threat="a holy darkness that swallowed the path and tricked the eyes",
        failure="The darkness pressed close, and every step wanted to turn into a wrong one.",
        calm_text="Gentle light spread ahead, and the black bend loosened into an honest path.",
        knowledge="Deep darkness can hide edges and turns, so people need light to move safely.",
        tags={"dark"},
    ),
    "thorn_ring": Hazard(
        id="thorn_ring",
        label="the thorn ring",
        threat="living brambles that caught skin and cloth and held travelers fast",
        failure="The thorns clicked together, and even brave feet could not walk through them bare.",
        calm_text="The angry thorns bent away, leaving a narrow lane clear to the shrine.",
        knowledge="Thick thorns can tear skin and clothes unless something shields you.",
        tags={"thorns"},
    ),
}

GIFTS = {
    "reed_rope": Gift(
        id="reed_rope",
        label="reed rope",
        phrase="a coil of river reed rope",
        protects={"wind_wall"},
        use_text="set the rope against the carved posts and climbed hand over hand, steady as a spider on silk",
        gift_text="Take this reed rope. It remembers the pull of the river and will help you stand against the wind.",
        knowledge="A rope gives hands something strong to hold when the wind pushes.",
        tags={"rope"},
    ),
    "sun_lantern": Gift(
        id="sun_lantern",
        label="sun lantern",
        phrase="a small sun lantern with one patient flame",
        protects={"night_gloom"},
        use_text="lifted the lantern high, and its warm circle showed the true floor of the cave",
        gift_text="Take this sun lantern. Small light can be stronger than great dark when it keeps showing the next true step.",
        knowledge="A lantern helps people see where to put their feet in the dark.",
        tags={"lantern"},
    ),
    "bramble_cloak": Gift(
        id="bramble_cloak",
        label="bramble cloak",
        phrase="a moon-gray bramble cloak sewn with smooth leather inside",
        protects={"thorn_ring"},
        use_text="wrapped the cloak close and walked through the scratching vines without letting them bite",
        gift_text="Take this bramble cloak. Thorns know its outer twigs and leave its wearer a little room.",
        knowledge="A thick cloak can keep thorns from scratching skin and snagging clothes.",
        tags={"cloak"},
    ),
    "bell_staff": Gift(
        id="bell_staff",
        label="bell staff",
        phrase="a staff tipped with a little bell of bright bronze",
        protects={"wind_wall", "night_gloom"},
        use_text="struck the staff once on stone, and the bell-note made a clear road where fear had been",
        gift_text="Take this bell staff. Some dangers break when they hear a brave, clean sound.",
        knowledge="A clear guide-sound can help people keep their way when wind or darkness confuses them.",
        tags={"staff", "bell"},
    ),
}

GIRL_NAMES = ["Alya", "Mira", "Tala", "Iria", "Neri", "Sona", "Luma", "Vela"]
BOY_NAMES = ["Tarin", "Kelan", "Oren", "Davi", "Ilan", "Soren", "Miro", "Bram"]
TRAITS = ["steady", "gentle", "quick", "thoughtful", "bright", "patient"]


def gift_works(route: Route, gift: Gift) -> bool:
    return route.hazard in gift.protects


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for route_id, route in ROUTES.items():
        for gift_id, gift in GIFTS.items():
            if gift_works(route, gift):
                combos.append((route_id, gift_id))
    return combos


@dataclass
class StoryParams:
    route: str
    gift: str
    hero_name: str
    hero_gender: str
    elder_type: str
    rival_name: str
    rival_gender: str
    trait: str
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


def introduce(world: World, route: Route, hero: Entity, elder: Entity) -> None:
    world.say(
        f"In the age when dawn had to be invited into the world each morning, "
        f"{hero.id} lived in a hill village below {route.place}, {route.opening}."
    )
    world.say(
        f"Before first light, the village lamps had burned thin, and {elder.label_word} "
        f"said that someone must climb to {route.shrine} before the dark grew proud."
    )


def charge(world: World, hero: Entity, elder: Entity, gift: Gift) -> None:
    world.say(
        f'{elder.label_word.capitalize()} placed {gift.phrase} in {hero.id}\'s hands and said, '
        f'"{gift.gift_text}"'
    )
    world.say(
        f"{hero.id} bowed, tucked the gift close, and began a small jog up the old road while the sky was still the color of ash."
    )


def boast(world: World, hero: Entity, rival: Entity) -> None:
    rival.memes["pride"] += 1
    world.say(
        f"{rival.id}, an older village runner, laughed from the gate. "
        f'"Keep your trinket," {rival.pronoun()} said. "My feet are superior to charms and lanterns and cloaks."'
    )
    world.say(
        f"But {hero.id} remembered that mountain paths do not bow to bragging."
    )


def fox_trouble(world: World, hero: Entity) -> None:
    fox = world.get("fox")
    hero.memes["concern"] += 1
    world.say(
        f"Halfway to the holy road, a sharp yip slipped out from a thorn bush. "
        f"There a little fox spirit lay caught by one hind leg, trembling but fierce-eyed."
    )
    world.say(
        f"{hero.id} could have run on, yet stopped, knelt in the cold grass, and worked the cruel twig loose."
    )
    fox.meters["freed"] += 1
    propagate(world, narrate=True)


def omen(world: World, route: Route, hero: Entity, fox: Entity) -> None:
    world.say(
        f'The fox sprang to a stone and looked toward {route.place}. "{route.omen}," '
        f"seemed to say {fox.pronoun()}, though no human mouth spoke. Then it ran ahead like a small ember with a tail."
    )


def meet_hazard(world: World, route: Route, hazard: Hazard, hero: Entity) -> None:
    hero.meters["at_hazard"] += 1
    world.say(
        f"At last {hero.id} reached {route.hazard_face}. There waited {hazard.label}, {hazard.threat}."
    )
    propagate(world, narrate=True)


def use_gift(world: World, gift: Gift, hero: Entity) -> None:
    world.say(
        f"{hero.id} did not turn back. {hero.pronoun().capitalize()} {gift.use_text}."
    )
    if world.get("hazard").meters["calmed"] < THRESHOLD:
        propagate(world, narrate=True)


def finish_quest(world: World, route: Route, hero: Entity, elder: Entity) -> None:
    shrine = world.get("shrine")
    hero.meters["progress"] += 1
    if world.get("hazard").meters["calmed"] >= THRESHOLD:
        shrine.meters["awakened"] += 1
        world.say(
            f"Step by step, {hero.id} reached {route.shrine} and touched the old altar stone."
        )
        world.say(
            f"At once the sleeping fire there woke, the bells above the village answered, and {route.ending}."
        )
        world.say(
            f"When {hero.id} came home, {elder.label_word} smiled and said that bravery is not loud feet, but a steady heart that helps and keeps going."
        )
    else:
        raise StoryError("(No story: the child reached the hazard without any honest way to calm it.)")


def tell(
    route: Route,
    gift: Gift,
    hero_name: str = "Alya",
    hero_gender: str = "girl",
    elder_type: str = "mother",
    rival_name: str = "Tarin",
    rival_gender: str = "boy",
    trait: str = "steady",
) -> World:
    if route.id not in ROUTES:
        raise StoryError(f"(Unknown route: {route.id})")
    if gift.id not in GIFTS:
        raise StoryError(f"(Unknown gift: {gift.id})")
    if not gift_works(route, gift):
        raise StoryError(explain_rejection(route, gift))

    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        tags={"hero"},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        tags={"elder"},
    ))
    rival = world.add(Entity(
        id="rival",
        kind="character",
        type=rival_gender,
        label=rival_name,
        role="rival",
        tags={"rival"},
    ))
    fox = world.add(Entity(
        id="fox",
        kind="character",
        type="spirit",
        label="the fox spirit",
        role="helper",
        tags={"fox", "spirit"},
    ))
    hazard_ent = world.add(Entity(
        id="hazard",
        kind="thing",
        type="hazard",
        label=HAZARDS[route.hazard].label,
        role="hazard",
        tags=set(HAZARDS[route.hazard].tags),
    ))
    gift_ent = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift.label,
        role="gift",
        attrs={"protects": set(gift.protects)},
        tags=set(gift.tags),
    ))
    shrine = world.add(Entity(
        id="shrine",
        kind="thing",
        type="shrine",
        label=route.shrine,
        role="goal",
        tags=set(route.tags),
    ))

    hero.memes["bravery"] = 1.0
    hero.memes["fear"] = 0.0
    hero.meters["at_hazard"] = 0.0
    hero.meters["stalled"] = 0.0
    hero.meters["progress"] = 0.0
    fox.meters["freed"] = 0.0
    hazard_ent.meters["calmed"] = 0.0
    shrine.meters["awakened"] = 0.0
    world.facts["fox_guided"] = False

    world.facts.update(
        route=route,
        gift_cfg=gift,
        hazard_cfg=HAZARDS[route.hazard],
        hero=hero,
        elder=elder,
        rival=rival,
        fox=fox,
        shrine=shrine,
    )

    introduce(world, route, hero, elder)
    charge(world, hero, elder, gift)

    world.para()
    boast(world, hero, rival)
    fox_trouble(world, hero)
    omen(world, route, hero, fox)

    world.para()
    meet_hazard(world, route, HAZARDS[route.hazard], hero)
    use_gift(world, gift, hero)
    finish_quest(world, route, hero, elder)

    world.facts.update(
        route_id=route.id,
        gift_id=gift.id,
        hazard_id=route.hazard,
        shrine_awakened=shrine.meters["awakened"] >= THRESHOLD,
        hero_bravery=hero.memes["bravery"],
        rival_pride=rival.memes["pride"],
        freed_fox=fox.meters["freed"] >= THRESHOLD,
    )
    hero.attrs["display_name"] = hero_name
    elder.attrs["display_name"] = elder_type
    rival.attrs["display_name"] = rival_name
    return world


KNOWLEDGE = {
    "fox": [(
        "What is a fox spirit in a myth?",
        "In a myth, a fox spirit is a magical fox that can guide, warn, or bless a traveler. It often stands for cleverness or a wild kind of help."
    )],
    "bravery": [(
        "What is bravery?",
        "Bravery is doing what is right even when you feel afraid. A brave person can still be gentle and careful."
    )],
    "wind": [(
        "Why can strong wind be dangerous on a mountain path?",
        "Strong wind can push a person off balance, especially on a high narrow path. That is why climbers hold tight and move carefully."
    )],
    "dark": [(
        "Why is a lantern useful in the dark?",
        "A lantern makes light so you can see the ground, the edges, and the next safe step. Seeing clearly helps people avoid getting lost or hurt."
    )],
    "thorns": [(
        "Why are thorns hard to walk through?",
        "Thorns are sharp and hook onto skin and clothes. They can scratch you and hold you back if nothing protects you."
    )],
    "rope": [(
        "What can a rope help someone do?",
        "A rope can give your hands something strong to hold. That helps you stay steady when the ground or the wind is difficult."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern carries light from one place to another. People use it when the path is too dark to trust with bare eyes."
    )],
    "cloak": [(
        "What is a cloak?",
        "A cloak is a loose outer covering worn over the body. A thick cloak can guard you from weather, scratches, or thorns."
    )],
    "staff": [(
        "What is a staff?",
        "A staff is a long stick carried in the hand. It can help a traveler keep balance and mark the way."
    )],
    "shrine": [(
        "What is a shrine in a story?",
        "A shrine is a special holy place where people go to honor something sacred. In myths, reaching a shrine often means finishing an important task."
    )],
}
KNOWLEDGE_ORDER = ["fox", "bravery", "wind", "dark", "thorns", "rope", "lantern", "cloak", "staff", "shrine"]


def generation_prompts(world: World) -> list[str]:
    route = world.facts["route"]
    gift = world.facts["gift_cfg"]
    hero = world.facts["hero"]
    hazard = world.facts["hazard_cfg"]
    hero_name = hero.attrs.get("display_name", "the child")
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the words "yip", "superior", and "jog".',
        f"Tell a mythic story where {hero_name} climbs toward {route.shrine}, frees a fox spirit after hearing its yip, and uses {gift.phrase} to overcome {hazard.label}.",
        f'Write a gentle bravery tale in myth style where a boastful runner says he is superior, but the true hero helps first and then keeps going.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    route = world.facts["route"]
    gift = world.facts["gift_cfg"]
    hazard = world.facts["hazard_cfg"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    rival = world.facts["rival"]
    hero_name = hero.attrs.get("display_name", "the child")
    rival_name = rival.attrs.get("display_name", "the rival")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child sent up {route.place} before dawn. It is also about a fox spirit, a proud older runner named {rival_name}, and the elder who trusted {hero_name} with a sacred gift."
        ),
        (
            f"Why did {hero_name} go up {route.place}?",
            f"{hero_name} went to reach {route.shrine} before dawn and wake the morning. The village needed the shrine answered before the dark grew stronger."
        ),
        (
            f"What happened when {hero_name} heard the yip?",
            f"{hero_name} found a little fox spirit trapped in the thorns and stopped to free it. That act of kindness made the fox guide {hero.pronoun('object')} and strengthened {hero.pronoun('possessive')} bravery."
        ),
        (
            f"Why was the boastful runner wrong to call himself superior?",
            f"{rival_name} thought fast feet were enough, but the path's danger was greater than bragging. The story shows that true bravery comes from helping first and using wisdom at the hard place."
        ),
        (
            f"How did {gift.label} help at {hazard.label}?",
            f"{hero_name} used {gift.label} when the path became dangerous. That gift matched the trouble honestly, so it calmed the danger and opened the way to the shrine."
        ),
        (
            "How did the story end?",
            f"{hero_name} reached {route.shrine}, the holy place woke, and {route.ending} The ending proves that the world changed because one brave child acted kindly and kept going."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bravery", "fox", "shrine"}
    tags |= set(world.facts["hazard_cfg"].tags)
    tags |= set(world.facts["gift_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(route: Route, gift: Gift) -> str:
    hazard = HAZARDS[route.hazard]
    return (
        f"(No story: {gift.label} does not honestly solve {hazard.label} on {route.place}. "
        f"That route needs a gift that can face {hazard.threat}.)"
    )


ASP_RULES = r"""
hazard_of(Route, Hazard) :- route(Route), route_hazard(Route, Hazard).
valid(Route, Gift) :- hazard_of(Route, Hazard), protects(Gift, Hazard).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_hazard", route_id, route.hazard))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        for hazard_id in sorted(gift.protects):
            lines.append(asp.fact("protects", gift_id, hazard_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        route="sky_steps",
        gift="reed_rope",
        hero_name="Alya",
        hero_gender="girl",
        elder_type="mother",
        rival_name="Kelan",
        rival_gender="boy",
        trait="steady",
        seed=101,
    ),
    StoryParams(
        route="echo_cave",
        gift="sun_lantern",
        hero_name="Tarin",
        hero_gender="boy",
        elder_type="father",
        rival_name="Mira",
        rival_gender="girl",
        trait="thoughtful",
        seed=102,
    ),
    StoryParams(
        route="briar_pass",
        gift="bramble_cloak",
        hero_name="Vela",
        hero_gender="girl",
        elder_type="mother",
        rival_name="Soren",
        rival_gender="boy",
        trait="gentle",
        seed=103,
    ),
    StoryParams(
        route="sky_steps",
        gift="bell_staff",
        hero_name="Ilan",
        hero_gender="boy",
        elder_type="father",
        rival_name="Neri",
        rival_gender="girl",
        trait="patient",
        seed=104,
    ),
    StoryParams(
        route="echo_cave",
        gift="bell_staff",
        hero_name="Luma",
        hero_gender="girl",
        elder_type="mother",
        rival_name="Bram",
        rival_gender="boy",
        trait="bright",
        seed=105,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a mythic climb, a fox spirit's yip, and bravery that wakes the dawn."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--rival-name")
    ap.add_argument("--rival-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (route, gift) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.gift:
        route = ROUTES[args.route]
        gift = GIFTS[args.gift]
        if not gift_works(route, gift):
            raise StoryError(explain_rejection(route, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.gift is None or combo[1] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, gift_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    rival_gender = args.rival_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    rival_pool = GIRL_NAMES if rival_gender == "girl" else BOY_NAMES
    rival_name = args.rival_name or rng.choice([n for n in rival_pool if n != hero_name] or rival_pool)
    elder_type = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        route=route_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        rival_name=rival_name,
        rival_gender=rival_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    route = ROUTES[params.route]
    gift = GIFTS[params.gift]
    if not gift_works(route, gift):
        raise StoryError(explain_rejection(route, gift))

    world = tell(
        route=route,
        gift=gift,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        rival_name=params.rival_name,
        rival_gender=params.rival_gender,
        trait=params.trait,
    )
    world.get("hero").id = params.hero_name
    world.get("elder").id = "Elder"
    world.get("rival").id = params.rival_name
    world.get("fox").id = "Fox"
    world.get("hazard").id = "Hazard"
    world.get("gift").id = "Gift"
    world.get("shrine").id = "Shrine"
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

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        default_params.seed = 0
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("FAILED: default resolve_params raised StoryError:", err)

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated empty story.)")
            if sample.world is None:
                raise StoryError("(Generated sample missing world.)")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:
            rc = 1
            print(f"FAILED: smoke generation crashed for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (route, gift) pairs:\n")
        for route_id, gift_id in combos:
            print(f"  {route_id:12} {gift_id}")
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
            header = f"### {p.hero_name}: {p.route} with {p.gift}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
