#!/usr/bin/env python3
"""
A standalone storyworld about a child in superhero mode carrying a surprise
thank-you gift safely through a small weather hazard.

The domain is built around one simple common-sense constraint:
the hero needs clothing that matches the weather and a carrier that protects the
surprise gift. The story always begins at the end of a school term, moves
through a weather-shaped problem, and ends with a cheerful surprise returned by
the helper.

Run it
------
python storyworlds/worlds/gpt-5.4/term_coordinate_clothed_surprise_superhero_story.py
python storyworlds/worlds/gpt-5.4/term_coordinate_clothed_surprise_superhero_story.py --scene library --threat drizzle --gift poster
python storyworlds/worlds/gpt-5.4/term_coordinate_clothed_surprise_superhero_story.py --outfit warm_cloak --threat drizzle
python storyworlds/worlds/gpt-5.4/term_coordinate_clothed_surprise_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/term_coordinate_clothed_surprise_superhero_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/term_coordinate_clothed_surprise_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    weather_guard: set[str] = field(default_factory=set)
    gift_guard: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian_f", "gardener_f"}
        male = {"boy", "father", "man", "guard_m", "librarian_m", "gardener_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Scene:
    id: str
    place: str
    backdrop: str
    helper_name: str
    helper_type: str
    helper_role: str
    helper_work: str
    afford_threats: set[str] = field(default_factory=set)
    returned_surprise: str = ""
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
class Threat:
    id: str
    sky_line: str
    hero_risk: str
    gift_risk: str
    action_line: str
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
    making_line: str
    damage_line: str
    carrier_need: str
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
class Outfit:
    id: str
    label: str
    phrase: str
    shields: set[str] = field(default_factory=set)
    style_line: str = ""
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
class Carrier:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    hold_line: str = ""
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
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


def _r_weather_harm(world: World) -> list[str]:
    hero = world.get("hero")
    gift = world.get("gift")
    threat: Threat = world.facts["threat_cfg"]
    if hero.meters["mission_started"] < THRESHOLD:
        return []
    sig = ("weather_harm", threat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    out: list[str] = []
    if threat.id not in hero.weather_guard:
        hero.meters["weather_trouble"] += 1
        hero.memes["worry"] += 1
        out.append("__hero_trouble__")
    if gift.attrs.get("need_carrier") == "weather" and gift.id not in world.get("carrier").gift_guard:
        gift.meters["damaged"] += 1
        hero.memes["worry"] += 1
        out.append("__gift_trouble__")
    return out


def _r_carry_harm(world: World) -> list[str]:
    hero = world.get("hero")
    gift = world.get("gift")
    if hero.meters["mission_started"] < THRESHOLD:
        return []
    sig = ("carry_harm", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if gift.id not in world.get("carrier").gift_guard:
        gift.meters["damaged"] += 1
        hero.memes["worry"] += 1
        return ["__gift_trouble__"]
    return []


def _r_success(world: World) -> list[str]:
    hero = world.get("hero")
    gift = world.get("gift")
    if hero.meters["mission_started"] < THRESHOLD:
        return []
    sig = ("mission_result", gift.id)
    if sig in world.fired:
        return []
    if hero.meters["weather_trouble"] >= THRESHOLD or gift.meters["damaged"] >= THRESHOLD:
        return []
    world.fired.add(sig)
    gift.meters["delivered_safe"] += 1
    hero.memes["confidence"] += 1
    hero.memes["relief"] += 1
    return ["__safe__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="weather_harm", tag="physical", apply=_r_weather_harm),
    Rule(name="carry_harm", tag="physical", apply=_r_carry_harm),
    Rule(name="success", tag="social", apply=_r_success),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def suitable_outfits(threat: Threat) -> list[Outfit]:
    return [o for o in OUTFITS.values() if threat.id in o.shields]


def suitable_carriers(gift: Gift) -> list[Carrier]:
    return [c for c in CARRIERS.values() if gift.id in c.protects]


def valid_combo(scene: Scene, threat: Threat, gift: Gift) -> bool:
    if threat.id not in scene.afford_threats:
        return False
    return bool(suitable_outfits(threat) and suitable_carriers(gift))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, scene in SCENES.items():
        for tid, threat in THREATS.items():
            for gid, gift in GIFTS.items():
                if valid_combo(scene, threat, gift):
                    combos.append((sid, tid, gid))
    return combos


def outfit_fits(outfit: Outfit, threat: Threat) -> bool:
    return threat.id in outfit.shields


def carrier_fits(carrier: Carrier, gift: Gift) -> bool:
    return gift.id in carrier.protects


def predict_mission(world: World) -> dict[str, bool]:
    sim = world.copy()
    start_mission(sim, narrate=False)
    hero = sim.get("hero")
    gift = sim.get("gift")
    return {
        "hero_safe": hero.meters["weather_trouble"] < THRESHOLD,
        "gift_safe": gift.meters["damaged"] < THRESHOLD,
    }


def introduce(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    world.say(
        f"On the last afternoon of the spring term, {hero.id} and {sidekick.id} "
        f"raced through {scene.backdrop}, pretending to be the city's smallest superhero team."
    )
    world.say(
        f"{hero.id} liked to zoom first and think later, while {sidekick.id} liked to notice little details that saved the day."
    )


def plan_surprise(world: World, hero: Entity, sidekick: Entity, parent: Entity,
                  scene: Scene, gift: Gift) -> None:
    hero.memes["excitement"] += 1
    sidekick.memes["excitement"] += 1
    world.say(
        f"That day they had a real mission. They had made {gift.phrase} for {scene.helper_name}, "
        f"the {scene.helper_role} who had helped them all term by {scene.helper_work}."
    )
    world.say(
        f"{gift.making_line} {parent.label_word.capitalize()} helped coordinate the surprise, "
        f"and even {sidekick.id} promised not to blurt it out."
    )


def spot_problem(world: World, hero: Entity, threat: Threat, gift: Gift) -> None:
    hero.memes["hurry"] += 1
    world.say(threat.sky_line)
    world.say(
        f'"No waiting!" {hero.id} cried. "{threat.action_line} I can still deliver the surprise right now!"'
    )
    world.say(
        f"But {gift.phrase} would have to cross the weather too."
    )


def warn(world: World, parent: Entity, hero: Entity, threat: Threat, gift: Gift) -> None:
    pred = predict_mission(world)
    world.facts["pred_hero_safe"] = pred["hero_safe"]
    world.facts["pred_gift_safe"] = pred["gift_safe"]
    hero.memes["listening"] += 1
    world.say(
        f'{parent.label_word.capitalize()} touched {hero.id}\'s shoulder. "A real hero looks ahead," '
        f'{parent.pronoun()} said.'
    )
    if not pred["hero_safe"] and not pred["gift_safe"]:
        world.say(
            f'"If you run out like this, {threat.hero_risk}, and {threat.gift_risk}. '
            f'Super speed is not enough by itself."'
        )
    elif not pred["hero_safe"]:
        world.say(
            f'"If you run out like this, {threat.hero_risk}. A brave hero still needs safe gear."'
        )
    elif not pred["gift_safe"]:
        world.say(
            f'"If you run out like this, {threat.gift_risk}. A surprise only works if it arrives in one piece."'
        )


def suit_up(world: World, hero: Entity, sidekick: Entity, outfit: Outfit, carrier: Carrier) -> None:
    hero.weather_guard = set(outfit.shields)
    hero.attrs["outfit"] = outfit.label
    world.get("carrier").gift_guard = set(carrier.protects)
    hero.memes["confidence"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"Soon {hero.id} was clothed in {outfit.phrase}, and {sidekick.id} fastened the last flap with careful fingers."
    )
    world.say(
        f"{hero.id} took {carrier.phrase}. {carrier.hold_line} {outfit.style_line}"
    )


def start_mission(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.meters["mission_started"] += 1
    propagate(world, narrate=narrate)


def mission_turn(world: World, hero: Entity, sidekick: Entity, threat: Threat,
                 gift: Gift, scene: Scene) -> None:
    start_mission(world, narrate=False)
    damaged = world.get("gift").meters["damaged"] >= THRESHOLD
    troubled = hero.meters["weather_trouble"] >= THRESHOLD
    if threat.id == "drizzle":
        world.say(
            f"They hurried toward {scene.place} as tiny silver drops began to tap on railings and leaves."
        )
    elif threat.id == "gust":
        world.say(
            f"They dashed toward {scene.place} just as a jumpy gust came skimming around the corner."
        )
    else:
        world.say(
            f"They hurried toward {scene.place} while the chilly air nipped at noses and fingertips."
        )

    if troubled:
        world.say(
            f"For a moment, {threat.hero_risk[0].upper()}{threat.hero_risk[1:]}. {hero.id} slowed down and held the gift tighter."
        )
    else:
        world.say(
            f"{hero.id}'s gear did its job, so the weather felt like a challenge in a comic book instead of a real danger."
        )

    if damaged:
        world.say(
            f"But trouble reached the surprise anyway. {gift.damage_line}"
        )
    else:
        world.say(
            f"The gift stayed safe, and that made {sidekick.id} grin. " 
            f'"See?" {sidekick.id} said. "Superheroes can plan and zoom."'
        )


def deliver(world: World, hero: Entity, scene: Scene, gift: Gift) -> None:
    helper = world.get("helper")
    hero.memes["gratitude"] += 1
    helper.memes["gratitude"] += 1
    world.say(
        f"At last they reached {scene.place}, where {scene.helper_name} was still {scene.helper_work}."
    )
    world.say(
        f'{hero.id} lifted {gift.phrase}. "This is for you," {hero.pronoun()} said. '
        f'"From our superhero team."'
    )


def returned_surprise(world: World, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    helper = world.get("helper")
    hero.memes["surprise"] += 1
    hero.memes["pride"] += 1
    sidekick.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{scene.helper_name}'s eyes went wide, and then {helper.pronoun()} laughed a warm, happy laugh."
    )
    world.say(
        f'"Oh, my stars," {helper.pronoun()} said. "I have a surprise for heroes too." '
        f"{helper.pronoun().capitalize()} reached into a pocket and brought out {scene.returned_surprise}."
    )
    world.say(
        f"{hero.id} stood very still while {scene.helper_name} pinned it on. On the way home, "
        f"{hero.id} did not only feel fast anymore. {hero.pronoun().capitalize()} felt ready."
    )


def tell(scene: Scene, threat: Threat, gift_cfg: Gift, outfit_cfg: Outfit, carrier_cfg: Carrier,
         hero_name: str = "Nova", hero_gender: str = "girl",
         sidekick_name: str = "Ben", sidekick_gender: str = "boy",
         parent_type: str = "mother", trait: str = "bold") -> World:
    world = World(scene)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        role="sidekick",
        traits=["careful"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=scene.helper_type,
        label=scene.helper_name,
        role="helper",
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=gift_cfg.label,
        attrs={"need_carrier": gift_cfg.carrier_need},
    ))
    carrier = world.add(Entity(
        id="carrier",
        kind="thing",
        type="carrier",
        label=carrier_cfg.label,
        gift_guard=set(),
    ))

    hero.weather_guard = set()
    carrier.gift_guard = set()
    world.facts.update(
        scene_cfg=scene,
        threat_cfg=threat,
        gift_cfg=gift_cfg,
        outfit_cfg=outfit_cfg,
        carrier_cfg=carrier_cfg,
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        helper=helper,
        gift_ent=gift,
    )

    introduce(world, hero, sidekick, scene)
    plan_surprise(world, hero, sidekick, parent, scene, gift_cfg)

    world.para()
    spot_problem(world, hero, threat, gift_cfg)
    warn(world, parent, hero, threat, gift_cfg)
    suit_up(world, hero, sidekick, outfit_cfg, carrier_cfg)

    world.para()
    mission_turn(world, hero, sidekick, threat, gift_cfg, scene)
    deliver(world, hero, scene, gift_cfg)

    world.para()
    returned_surprise(world, hero, sidekick, scene)

    world.facts.update(
        delivered=world.get("gift").meters["delivered_safe"] >= THRESHOLD,
        hero_safe=hero.meters["weather_trouble"] < THRESHOLD,
        gift_safe=world.get("gift").meters["damaged"] < THRESHOLD,
    )
    return world


SCENES = {
    "library": Scene(
        id="library",
        place="the little library door",
        backdrop="the brick walk outside the town library",
        helper_name="Ms. Reed",
        helper_type="librarian_f",
        helper_role="librarian",
        helper_work="stacking the last return books",
        afford_threats={"drizzle", "gust", "chill"},
        returned_surprise="a shiny star sticker that said HELPER HERO",
        tags={"library", "helper"},
    ),
    "school_gate": Scene(
        id="school_gate",
        place="the bright school gate",
        backdrop="the painted path beside the school gate",
        helper_name="Mr. Lane",
        helper_type="guard_m",
        helper_role="crossing guard",
        helper_work="waving families safely across the street",
        afford_threats={"drizzle", "gust"},
        returned_surprise="a tiny silver whistle charm on a blue string",
        tags={"crossing_guard", "helper"},
    ),
    "garden": Scene(
        id="garden",
        place="the green garden shed",
        backdrop="the winding path through the community garden",
        helper_name="Aunt Sol",
        helper_type="gardener_f",
        helper_role="gardener",
        helper_work="watering beans and tying up sunflowers",
        afford_threats={"gust", "chill"},
        returned_surprise="a sunflower badge with a smiling face in the middle",
        tags={"garden", "helper"},
    ),
}

THREATS = {
    "drizzle": Threat(
        id="drizzle",
        sky_line="A fine drizzle began to float down from the cloudy sky.",
        hero_risk="your sleeves and shoes will turn cold and wet",
        gift_risk="the surprise could turn soggy before you get there",
        action_line="The city needs me",
        tags={"drizzle", "weather"},
    ),
    "gust": Threat(
        id="gust",
        sky_line="A lively gust came bouncing between fences and signs.",
        hero_risk="your costume will flap and tug while you run",
        gift_risk="the surprise could slip, crumple, or wobble",
        action_line="A gust cannot stop Captain Zoom",
        tags={"wind", "weather"},
    ),
    "chill": Threat(
        id="chill",
        sky_line="A chilly breeze slipped under jackets and made noses pink.",
        hero_risk="your hands will go cold before the mission is done",
        gift_risk="the surprise could shake loose if you start shivering",
        action_line="Even cold air cannot stop me",
        tags={"cold", "weather"},
    ),
}

GIFTS = {
    "poster": Gift(
        id="poster",
        label="thank-you poster",
        phrase="a bright thank-you poster covered with stars",
        making_line="They had written giant gold letters and drawn a red cape around the corner",
        damage_line="One bent edge popped up, but they caught it before it could crease any further.",
        carrier_need="weather",
        tags={"poster", "paper_gift"},
    ),
    "cupcakes": Gift(
        id="cupcakes",
        label="moon cupcakes",
        phrase="a box of tiny moon cupcakes with blue icing",
        making_line="They had stirred the batter, counted the paper cups, and added one silver sprinkle to each cake",
        damage_line="The frosting slid to one side and made a small blue moon on the lid.",
        carrier_need="carry",
        tags={"cupcakes", "food_gift"},
    ),
    "patch": Gift(
        id="patch",
        label="cape patch",
        phrase="a stitched cape patch shaped like a lightning bolt",
        making_line="They had picked felt, thread, and one brave yellow button for the middle",
        damage_line="The little patch tried to fold over on itself, but they smoothed it flat again.",
        carrier_need="carry",
        tags={"patch", "cloth_gift"},
    ),
}

OUTFITS = {
    "rain_armor": Outfit(
        id="rain_armor",
        label="rain armor",
        phrase="a blue raincoat, yellow boots, and a hood that sat snugly over the ears",
        shields={"drizzle"},
        style_line="With the hood up, {hero} looked less like a soggy child and more like a puddle-proof champion.",
        tags={"raincoat", "clothed"},
    ),
    "storm_suit": Outfit(
        id="storm_suit",
        label="storm suit",
        phrase="a close-fitting red jacket and soft shoes that would not slip or flap",
        shields={"gust", "drizzle"},
        style_line="Nothing loose could whip away, so even the weather had less to grab.",
        tags={"wind_gear", "clothed"},
    ),
    "warm_cloak": Outfit(
        id="warm_cloak",
        label="warm cloak",
        phrase="a wool cape over a thick sweater, with mittens tucked into warm pockets",
        shields={"chill"},
        style_line="The whole outfit made the mission feel like a winter comic book in the best way.",
        tags={"warm_clothes", "clothed"},
    ),
}

CARRIERS = {
    "star_tube": Carrier(
        id="star_tube",
        label="star tube",
        phrase="a silver poster tube with a shoulder strap",
        protects={"poster"},
        hold_line="The poster slid inside with a soft shh, safe from wrinkles and raindrops.",
        tags={"tube", "carrier"},
    ),
    "cake_carrier": Carrier(
        id="cake_carrier",
        label="cake carrier",
        phrase="a clear cake carrier with a tight click-lock lid",
        protects={"cupcakes"},
        hold_line="The cupcakes sat flat and proud, and the lid snapped shut like a shield.",
        tags={"cake_box", "carrier"},
    ),
    "satchel": Carrier(
        id="satchel",
        label="hero satchel",
        phrase="a small hero satchel worn across the chest",
        protects={"patch"},
        hold_line="The patch rested in the satchel where little hands and little gusts could not rumple it.",
        tags={"satchel", "carrier"},
    ),
    "utility_box": Carrier(
        id="utility_box",
        label="utility box",
        phrase="a sturdy hero utility box with a soft cloth inside",
        protects={"cupcakes", "patch"},
        hold_line="Inside, the surprise sat snug and still, as if the box understood secret missions.",
        tags={"box", "carrier"},
    ),
}

GIRL_NAMES = ["Nova", "Mia", "Ava", "Zoe", "Luna", "Ivy", "Ruby", "Nora"]
BOY_NAMES = ["Max", "Leo", "Finn", "Eli", "Jack", "Theo", "Sam", "Noah"]
TRAITS = ["bold", "sparky", "brave", "eager", "quick"]


@dataclass
class StoryParams:
    scene: str
    threat: str
    gift: str
    outfit: str
    carrier: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    parent: str
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


KNOWLEDGE = {
    "drizzle": [(
        "What is drizzle?",
        "Drizzle is very light rain made of tiny drops. It can still make paper soggy and clothes damp."
    )],
    "wind": [(
        "Why can wind make carrying things hard?",
        "Wind can push, tug, and wobble what you are carrying. That is why people use strong boxes or hold things carefully on blustery days."
    )],
    "cold": [(
        "Why do mittens help in cold weather?",
        "Mittens keep warm air around your hands. Warm hands can hold things more steadily and safely."
    )],
    "poster": [(
        "Why should a paper poster stay dry?",
        "Paper gets soft and wrinkly when it is wet. If you want words and pictures to stay neat, you keep the paper dry."
    )],
    "cupcakes": [(
        "Why do cupcakes need a box?",
        "A box helps keep cupcakes level and clean. It also stops the frosting from getting squished."
    )],
    "patch": [(
        "What is a patch on clothes?",
        "A patch is a small piece of cloth that can be sewn on. It can decorate something or help show a team or idea."
    )],
    "raincoat": [(
        "What does a raincoat do?",
        "A raincoat helps keep rain off your clothes and skin. It lets you stay drier when the weather turns wet."
    )],
    "wind_gear": [(
        "Why are snug clothes useful on a windy day?",
        "Snug clothes do not flap as much in the wind. That makes it easier to move and carry things safely."
    )],
    "warm_clothes": [(
        "Why do warm clothes help on a cold day?",
        "Warm clothes hold in body heat. When you feel warm, your hands and feet can work better."
    )],
    "tube": [(
        "What is a poster tube for?",
        "A poster tube is a round container that keeps paper rolled up safely. It helps protect paper from bends and rain."
    )],
    "cake_box": [(
        "What does a cake carrier do?",
        "A cake carrier is a box with a lid that protects cakes and cupcakes while you carry them. It helps keep them steady and clean."
    )],
    "satchel": [(
        "What is a satchel?",
        "A satchel is a small bag with a strap. People use it to carry things while keeping their hands free."
    )],
    "crossing_guard": [(
        "What does a crossing guard do?",
        "A crossing guard helps people cross the street safely. They watch traffic and tell walkers when it is safe to go."
    )],
    "library": [(
        "What does a librarian do?",
        "A librarian helps people find books and take care of them. Librarians also keep a library calm and welcoming."
    )],
    "garden": [(
        "Why do gardens need care?",
        "Plants need water, support, and time to grow. A careful gardener helps them stay healthy."
    )],
}
KNOWLEDGE_ORDER = [
    "drizzle", "wind", "cold", "poster", "cupcakes", "patch",
    "raincoat", "wind_gear", "warm_clothes", "tube", "cake_box",
    "satchel", "crossing_guard", "library", "garden"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene_cfg"]
    gift = f["gift_cfg"]
    threat = f["threat_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old about a child planning a surprise thank-you during the last school term, and include the word "term".',
        f"Tell a gentle superhero story where {hero.id} wants to rush through {threat.id} with {gift.phrase}, but a grown-up helps coordinate a safer plan.",
        f'Write a child-facing story that includes the words "coordinate" and "clothed" and ends with {scene.helper_name} giving the hero a surprise back.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    parent: Entity = f["parent"]
    scene: Scene = f["scene_cfg"]
    threat: Threat = f["threat_cfg"]
    gift: Gift = f["gift_cfg"]
    outfit: Outfit = f["outfit_cfg"]
    carrier: Carrier = f["carrier_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who was the story about?",
            f"It was about {hero.id}, a child pretending to be a superhero, and {sidekick.id}, the careful sidekick. They were taking a surprise thank-you gift to {scene.helper_name}, the {scene.helper_role}."
        ),
        (
            f"Why did {hero.id}'s {parent.label_word} stop to make a plan?",
            f"{parent.label_word.capitalize()} knew the weather could cause trouble. Without a plan, {threat.hero_risk}, and {threat.gift_risk}."
        ),
        (
            f"How was {hero.id} dressed for the mission?",
            f"{hero.id} was clothed in {outfit.phrase}. That outfit matched the weather, so the mission felt brave without being reckless."
        ),
        (
            f"What did {hero.id} carry the surprise in?",
            f"{hero.pronoun().capitalize()} carried it in {carrier.phrase}. The carrier protected the gift so it could arrive neat and ready."
        ),
        (
            "What was the surprise at the end?",
            f"{scene.helper_name} was surprised by the gift, and then gave the hero {scene.returned_surprise} in return. That turned the thank-you mission into a happy surprise for both sides."
        ),
    ]
    if f.get("gift_safe"):
        qa.append((
            f"Why did the surprise stay safe on the way?",
            f"It stayed safe because the gear matched the problem. The outfit handled the {threat.id}, and the carrier protected the {gift.label} while they hurried along."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["threat_cfg"].tags) | set(f["gift_cfg"].tags) | set(f["scene_cfg"].tags)
    tags |= set(f["outfit_cfg"].tags) | set(f["carrier_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.weather_guard:
            bits.append(f"weather_guard={sorted(ent.weather_guard)}")
        if ent.gift_guard:
            bits.append(f"gift_guard={sorted(ent.gift_guard)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="library",
        threat="drizzle",
        gift="poster",
        outfit="rain_armor",
        carrier="star_tube",
        hero="Nova",
        hero_gender="girl",
        sidekick="Max",
        sidekick_gender="boy",
        parent="mother",
        trait="bold",
    ),
    StoryParams(
        scene="school_gate",
        threat="gust",
        gift="cupcakes",
        outfit="storm_suit",
        carrier="cake_carrier",
        hero="Leo",
        hero_gender="boy",
        sidekick="Ivy",
        sidekick_gender="girl",
        parent="father",
        trait="eager",
    ),
    StoryParams(
        scene="garden",
        threat="chill",
        gift="patch",
        outfit="warm_cloak",
        carrier="satchel",
        hero="Ruby",
        hero_gender="girl",
        sidekick="Finn",
        sidekick_gender="boy",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        scene="library",
        threat="gust",
        gift="patch",
        outfit="storm_suit",
        carrier="utility_box",
        hero="Theo",
        hero_gender="boy",
        sidekick="Mia",
        sidekick_gender="girl",
        parent="father",
        trait="quick",
    ),
    StoryParams(
        scene="school_gate",
        threat="drizzle",
        gift="cupcakes",
        outfit="storm_suit",
        carrier="cake_carrier",
        hero="Ava",
        hero_gender="girl",
        sidekick="Eli",
        sidekick_gender="boy",
        parent="mother",
        trait="sparky",
    ),
]


def explain_combo(scene: Scene, threat: Threat, gift: Gift) -> str:
    if threat.id not in scene.afford_threats:
        return (
            f"(No story: {scene.place} is not a good place for the {threat.id} mission in this tiny world. "
            f"Pick a scene that allows that weather.)"
        )
    if not suitable_outfits(threat):
        return (
            f"(No story: the wardrobe has nothing that safely handles {threat.id}. "
            f"A superhero mission needs weather-matching clothes.)"
        )
    if not suitable_carriers(gift):
        return (
            f"(No story: the carrier catalog has nothing that safely protects {gift.label}. "
            f"The surprise has to make it to the helper intact.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def explain_outfit(outfit: Outfit, threat: Threat) -> str:
    good = ", ".join(sorted(o.id for o in suitable_outfits(threat)))
    return (
        f"(No story: {outfit.label} does not match {threat.id}. "
        f"Try one of these outfits: {good}.)"
    )


def explain_carrier(carrier: Carrier, gift: Gift) -> str:
    good = ", ".join(sorted(c.id for c in suitable_carriers(gift)))
    return (
        f"(No story: {carrier.label} does not properly protect {gift.label}. "
        f"Try one of these carriers: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    try:
        threat = THREATS[params.threat]
        gift = GIFTS[params.gift]
        outfit = OUTFITS[params.outfit]
        carrier = CARRIERS[params.carrier]
    except KeyError:
        return "failed"
    ok = outfit_fits(outfit, threat) and carrier_fits(carrier, gift)
    return "success" if ok else "failed"


ASP_RULES = r"""
has_outfit(T) :- threat(T), outfit(O), shields(O, T).
has_carrier(G) :- gift(G), carrier(C), protects(C, G).

valid(S, T, G) :- scene(S), threat(T), gift(G),
                  affords(S, T), has_outfit(T), has_carrier(G).

safe_weather :- chosen_threat(T), chosen_outfit(O), shields(O, T).
safe_gift    :- chosen_gift(G), chosen_carrier(C), protects(C, G).

outcome(success) :- safe_weather, safe_gift.
outcome(failed)  :- not outcome(success).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for threat_id in sorted(scene.afford_threats):
            lines.append(asp.fact("affords", sid, threat_id))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    for oid, outfit in OUTFITS.items():
        lines.append(asp.fact("outfit", oid))
        for threat_id in sorted(outfit.shields):
            lines.append(asp.fact("shields", oid, threat_id))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        for gift_id in sorted(carrier.protects):
            lines.append(asp.fact("protects", cid, gift_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_threat", params.threat),
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_outfit", params.outfit),
        asp.fact("chosen_carrier", params.carrier),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "failed"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _ = sample.to_json()
        _ = format_qa(sample)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke-tested normal generation, emit, JSON, and QA.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero-style surprise thank-you with safe gear."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--outfit", choices=OUTFITS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid scene/threat/gift combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.threat and args.gift:
        scene = SCENES[args.scene]
        threat = THREATS[args.threat]
        gift = GIFTS[args.gift]
        if not valid_combo(scene, threat, gift):
            raise StoryError(explain_combo(scene, threat, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.threat is None or combo[1] == args.threat)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, threat_id, gift_id = rng.choice(sorted(combos))
    scene = SCENES[scene_id]
    threat = THREATS[threat_id]
    gift = GIFTS[gift_id]

    outfit_choices = [o.id for o in suitable_outfits(threat)]
    if args.outfit is not None:
        if args.outfit not in OUTFITS:
            raise StoryError("(No story: unknown outfit.)")
        if not outfit_fits(OUTFITS[args.outfit], threat):
            raise StoryError(explain_outfit(OUTFITS[args.outfit], threat))
        outfit_id = args.outfit
    else:
        outfit_id = rng.choice(sorted(outfit_choices))

    carrier_choices = [c.id for c in suitable_carriers(gift)]
    if args.carrier is not None:
        if args.carrier not in CARRIERS:
            raise StoryError("(No story: unknown carrier.)")
        if not carrier_fits(CARRIERS[args.carrier], gift):
            raise StoryError(explain_carrier(CARRIERS[args.carrier], gift))
        carrier_id = args.carrier
    else:
        carrier_id = rng.choice(sorted(carrier_choices))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or _pick_name(rng, hero_gender)
    if args.sidekick_gender is not None:
        sidekick_gender = args.sidekick_gender
    else:
        sidekick_gender = rng.choice(["girl", "boy"])
    sidekick_name = args.sidekick or _pick_name(rng, sidekick_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        scene=scene.id,
        threat=threat.id,
        gift=gift.id,
        outfit=outfit_id,
        carrier=carrier_id,
        hero=hero_name,
        hero_gender=hero_gender,
        sidekick=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(No story: unknown scene '{params.scene}'.)")
    if params.threat not in THREATS:
        raise StoryError(f"(No story: unknown threat '{params.threat}'.)")
    if params.gift not in GIFTS:
        raise StoryError(f"(No story: unknown gift '{params.gift}'.)")
    if params.outfit not in OUTFITS:
        raise StoryError(f"(No story: unknown outfit '{params.outfit}'.)")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(No story: unknown carrier '{params.carrier}'.)")

    scene = SCENES[params.scene]
    threat = THREATS[params.threat]
    gift = GIFTS[params.gift]
    outfit = OUTFITS[params.outfit]
    carrier = CARRIERS[params.carrier]

    if not valid_combo(scene, threat, gift):
        raise StoryError(explain_combo(scene, threat, gift))
    if not outfit_fits(outfit, threat):
        raise StoryError(explain_outfit(outfit, threat))
    if not carrier_fits(carrier, gift):
        raise StoryError(explain_carrier(carrier, gift))

    world = tell(
        scene=scene,
        threat=threat,
        gift_cfg=gift,
        outfit_cfg=outfit,
        carrier_cfg=carrier,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    story = world.render()
    outfit_phrase = outfit.style_line.replace("{hero}", params.hero)
    if outfit_phrase and outfit_phrase not in story:
        story = story.replace(
            f"{params.hero} took {carrier.phrase}. {carrier.hold_line}",
            f"{params.hero} took {carrier.phrase}. {carrier.hold_line} {outfit_phrase}",
            1,
        )

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (scene, threat, gift) combos:\n")
        for scene, threat, gift in combos:
            print(f"  {scene:11} {threat:8} {gift}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.sidekick}: {p.gift} through {p.threat} at {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
