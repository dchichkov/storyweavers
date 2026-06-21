#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py
======================================================================

A standalone story world for a tiny adventure domain built from the seed words
"dancer" and "menagerie" with explicit foreshadowing.

Reference premise
-----------------
A child dancer travels with a small menagerie cart toward a hilltop lantern
festival. On the road, the child notices an early warning sign at an old bridge:
a missing plank, a frayed rope, or a loose wheel strap. That warning matters
later. When one little animal from the menagerie panics at the crossing, the
child and a grown-up must choose a sensible way to get everyone safely across.

This world models:
- a child-facing adventure tone
- a foreshadowing beat that predicts later trouble
- typed entities with physical meters and emotional memes
- a reasonableness gate over route, animal, warning sign, and rescue method
- a small ASP twin for parity checks

Run it
------
python storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py
python storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py --route canyon_bridge --animal pony
python storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py --warning wind_flag --animal tortoise
python storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py --method drag_cart
python storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py --all
python storyworlds/worlds/gpt-5.4/dancer_menagerie_foreshadowing_adventure.py --verify
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
class Route:
    id: str
    place: str
    bridge: str
    vista: str
    destination: str
    risk: str
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
    article: str
    feet_kind: str
    fear_sound: str
    nimble: int
    likes_rhythm: bool
    tags: set[str] = field(default_factory=set)

    @property
    def phrase(self) -> str:
        return f"{self.article} {self.label}"
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
class WarningCfg:
    id: str
    clue: str
    hint: str
    severity: int
    needs: str
    believable_for: set[str] = field(default_factory=set)
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
class MethodCfg:
    id: str
    sense: int
    power: int
    uses_rhythm: bool
    needs: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
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
class PropCfg:
    id: str
    label: str
    phrase: str
    use_text: str
    kind: str
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


def _r_shake(world: World) -> list[str]:
    bridge = world.get("bridge")
    animal = world.get("animal")
    if bridge.meters["strain"] < THRESHOLD or animal.memes["fear"] < THRESHOLD:
        return []
    sig = ("shake",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["danger"] += 1
    animal.meters["stalled"] += 1
    hero = world.get("hero")
    hero.memes["resolve"] += 1
    return ["__shake__"]


def _r_calm(world: World) -> list[str]:
    animal = world.get("animal")
    hero = world.get("hero")
    if hero.memes["rhythm"] < THRESHOLD or animal.memes["fear"] < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["fear"] = max(0.0, animal.memes["fear"] - 1.0)
    animal.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="shake", tag="physical", apply=_r_shake),
    Rule(name="calm", tag="social", apply=_r_calm),
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


ROUTES = {
    "canyon_bridge": Route(
        id="canyon_bridge",
        place="the red canyon trail",
        bridge="the old rope bridge over the canyon",
        vista="far below, the river flashed like a silver ribbon",
        destination="the lantern hill beyond the canyon",
        risk="the boards hung over a long drop",
        tags={"bridge", "canyon", "adventure"},
    ),
    "jungle_bridge": Route(
        id="jungle_bridge",
        place="the green jungle path",
        bridge="the vine bridge over the ravine",
        vista="parrots flashed between the leaves and mist rose from the stones below",
        destination="the sun gate deep in the jungle",
        risk="the bridge swayed above dark rocks",
        tags={"bridge", "jungle", "adventure"},
    ),
    "sea_cliff_bridge": Route(
        id="sea_cliff_bridge",
        place="the windy cliff path",
        bridge="the plank bridge between two sea cliffs",
        vista="white gulls wheeled above the water and foam shone on the rocks below",
        destination="the star tower on the far cliff",
        risk="the sea wind pushed at every loose board",
        tags={"bridge", "sea", "adventure"},
    ),
}

ANIMALS = {
    "pony": AnimalCfg(
        id="pony",
        label="pony",
        article="a",
        feet_kind="small hooves",
        fear_sound="snorted and tossed its mane",
        nimble=2,
        likes_rhythm=True,
        tags={"pony", "animal"},
    ),
    "goat": AnimalCfg(
        id="goat",
        label="goat",
        article="a",
        feet_kind="quick little hooves",
        fear_sound="bleated and danced sideways",
        nimble=3,
        likes_rhythm=True,
        tags={"goat", "animal"},
    ),
    "tortoise": AnimalCfg(
        id="tortoise",
        label="tortoise",
        article="a",
        feet_kind="broad slow feet",
        fear_sound="pulled its head into its shell",
        nimble=1,
        likes_rhythm=False,
        tags={"tortoise", "animal"},
    ),
}

WARNINGS = {
    "missing_plank": WarningCfg(
        id="missing_plank",
        clue="one plank near the middle was missing, leaving a dark gap",
        hint="Mira marked the gap in her mind and wondered how frightened feet would step past it later",
        severity=2,
        needs="step_lightly",
        believable_for={"pony", "goat", "tortoise"},
        tags={"foreshadowing", "bridge"},
    ),
    "frayed_rope": WarningCfg(
        id="frayed_rope",
        clue="the left side rope was fuzzy with broken fibers",
        hint="The torn strands looked like a warning whisper from the bridge itself",
        severity=3,
        needs="steady_weight",
        believable_for={"pony", "goat", "tortoise"},
        tags={"foreshadowing", "rope"},
    ),
    "wind_flag": WarningCfg(
        id="wind_flag",
        clue="a strip of old red cloth on the railing kept snapping hard in the wind",
        hint="Even before anything went wrong, the cloth seemed to shout that the crossing would not stay calm for long",
        severity=1,
        needs="calm_rhythm",
        believable_for={"pony", "goat"},
        tags={"foreshadowing", "wind"},
    ),
}

PROPS = {
    "ankle_bells": PropCfg(
        id="ankle_bells",
        label="ankle bells",
        phrase="a string of ankle bells",
        use_text="let the bells answer the bridge with a bright, steady chime",
        kind="rhythm",
        tags={"bells", "dance"},
    ),
    "silk_scarf": PropCfg(
        id="silk_scarf",
        label="silk scarf",
        phrase="a long silk scarf",
        use_text="lifted the scarf so it floated ahead like a soft little flag to follow",
        kind="guide",
        tags={"scarf", "dance"},
    ),
    "lantern_pole": PropCfg(
        id="lantern_pole",
        label="lantern pole",
        phrase="a little lantern pole",
        use_text="raised the lantern pole so warm light showed each safe board",
        kind="light",
        tags={"lantern", "light"},
    ),
}

METHODS = {
    "lead_slowly": MethodCfg(
        id="lead_slowly",
        sense=3,
        power=3,
        uses_rhythm=False,
        needs={"step_lightly", "steady_weight"},
        text="unloaded the cart, tested each board with a staff, and led the {animal} across one slow step at a time while Mira walked beside it",
        fail="unloaded the cart and tried to lead the {animal} across, but the crossing still shook too wildly",
        qa_text="unloaded the cart and led the animal across one slow step at a time",
        tags={"careful", "bridge"},
    ),
    "dance_and_lure": MethodCfg(
        id="dance_and_lure",
        sense=3,
        power=2,
        uses_rhythm=True,
        needs={"calm_rhythm", "step_lightly"},
        text="asked Mira to dance ahead in tiny careful steps while the bells and scarf drew the {animal} after her",
        fail="asked Mira to dance ahead and lure the {animal}, but the frightened little creature froze before the worst part of the bridge",
        qa_text="had Mira dance ahead and gently lure the animal across",
        tags={"dance", "bridge"},
    ),
    "retie_then_cross": MethodCfg(
        id="retie_then_cross",
        sense=3,
        power=4,
        uses_rhythm=False,
        needs={"steady_weight"},
        text="lashed the weak side rope tight, then took the {animal} over only after the bridge stopped lurching",
        fail="retied the rope, but the bridge groaned so hard that the crossing was still unsafe",
        qa_text="tightened the weak rope before leading the animal across",
        tags={"repair", "rope"},
    ),
    "drag_cart": MethodCfg(
        id="drag_cart",
        sense=1,
        power=1,
        uses_rhythm=False,
        needs=set(),
        text="hauled the full menagerie cart straight onto the bridge and hoped speed would solve the problem",
        fail="dragged the full cart forward, and that only made the bridge buck harder",
        qa_text="dragged the full cart straight onto the bridge",
        tags={"bad_idea", "bridge"},
    ),
}


GIRL_NAMES = ["Mira", "Lina", "Nora", "Ava", "Zuri", "Tali", "Esme", "Nia"]
BOY_NAMES = ["Kian", "Leo", "Rafi", "Milo", "Tao", "Eli", "Noah", "Arin"]
TRAITS = ["brave", "careful", "nimble", "curious", "steady", "hopeful"]


def route_supports_warning(route_id: str, warning_id: str) -> bool:
    if warning_id == "wind_flag":
        return route_id in {"sea_cliff_bridge", "canyon_bridge"}
    return True


def warning_believable(animal_id: str, warning_id: str) -> bool:
    return animal_id in WARNINGS[warning_id].believable_for


def hazard_at_risk(route_id: str, animal_id: str, warning_id: str) -> bool:
    return route_supports_warning(route_id, warning_id) and warning_believable(animal_id, warning_id)


def sensible_methods() -> list[MethodCfg]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def challenge_level(animal_id: str, warning_id: str, extra_delay: int) -> int:
    animal = ANIMALS[animal_id]
    warning = WARNINGS[warning_id]
    return max(1, warning.severity + (2 - animal.nimble) + extra_delay)


def method_works(method_id: str, animal_id: str, warning_id: str, extra_delay: int) -> bool:
    method = METHODS[method_id]
    warning = WARNINGS[warning_id]
    if method.sense < SENSE_MIN:
        return False
    if warning.needs and not (method.needs & {warning.needs}):
        return False
    if method.uses_rhythm and not ANIMALS[animal_id].likes_rhythm:
        return False
    return method.power >= challenge_level(animal_id, warning_id, extra_delay)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    bridge = sim.get("bridge")
    animal = sim.get("animal")
    bridge.meters["strain"] += 1
    animal.memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": bridge.meters["danger"],
        "fear": animal.memes["fear"],
        "stalled": animal.meters["stalled"],
    }


def introduce(world: World, hero: Entity, mentor: Entity, route: Route, animal_cfg: AnimalCfg, prop: PropCfg) -> None:
    world.say(
        f"{hero.id} was the youngest dancer in a little rolling menagerie that rattled along {route.place}. "
        f"In the painted cart behind {mentor.label_word}, there were bright trunks, folded tents, and {animal_cfg.phrase} named Pip."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept {prop.phrase} close and dreamed of reaching {route.destination} before sunset."
    )


def adventure_beat(world: World, route: Route) -> None:
    world.say(
        f"By noon they reached {route.bridge}. {route.vista}, and {route.risk}."
    )


def foreshadow(world: World, hero: Entity, route: Route, warning: WarningCfg) -> None:
    hero.memes["alert"] += 1
    world.say(
        f"Before anyone stepped out, {hero.id} noticed that {warning.clue}. {warning.hint}"
    )
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_stalled"] = pred["stalled"]


def set_off(world: World, hero: Entity, mentor: Entity, animal: Entity, route: Route) -> None:
    world.say(
        f'"Stay close," said {mentor.label_word.capitalize()}, taking the lead rope. '
        f'{hero.id} stepped onto the first board, and the little menagerie followed.'
    )
    world.say(
        f"Pip tapped {animal.attrs['feet_kind']} on the wood and looked down through the gaps."
    )


def panic(world: World, hero: Entity, animal: Entity, warning: WarningCfg) -> None:
    bridge = world.get("bridge")
    bridge.meters["strain"] += 1
    animal.memes["fear"] += 1
    animal.meters["hesitation"] += 1
    propagate(world, narrate=False)
    if warning.id == "missing_plank":
        world.say(
            f"Then they reached the very spot {hero.id} had noticed before. The missing plank opened like a dark mouth under the bridge."
        )
    elif warning.id == "frayed_rope":
        world.say(
            f"Halfway across, the weak side rope gave a harsh twang. Fibers flew loose in the air."
        )
    else:
        world.say(
            f"Halfway across, a hard gust slapped the bridge. The old red cloth cracked like a whip."
        )
    world.say(
        f"Pip {animal.attrs['fear_sound']}, and the whole bridge began to wobble."
    )


def choose_method(world: World, hero: Entity, mentor: Entity, animal_cfg: AnimalCfg, method: MethodCfg, prop: PropCfg) -> None:
    if method.uses_rhythm:
        hero.memes["rhythm"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} did not run. {hero.pronoun().capitalize()} {prop.use_text}."
        )
    else:
        world.say(
            f"{mentor.label_word.capitalize()} held up a steady hand, and {hero.id} copied the slow calm breath {hero.pronoun()} had practiced before every dance."
        )
    body = method.text.replace("{animal}", animal_cfg.label)
    world.say(
        f"Together they {body}."
    )


def rescue_success(world: World, hero: Entity, mentor: Entity, animal: Entity, route: Route, method: MethodCfg) -> None:
    bridge = world.get("bridge")
    bridge.meters["danger"] = 0.0
    bridge.meters["strain"] = 0.0
    animal.meters["crossed"] += 1
    animal.meters["stalled"] = 0.0
    animal.memes["fear"] = 0.0
    animal.memes["trust"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    mentor.memes["relief"] += 1
    world.say(
        f"Board by board, the shaking eased. At last Pip stepped onto the far side and blew out a warm little breath."
    )
    world.say(
        f'"You saw the trouble before it came," {mentor.label_word} said. "That is what good adventurers do."'
    )
    world.say(
        f"With the bridge behind them, the tiny menagerie rolled on toward {route.destination}, and {hero.id}'s dancer steps felt braver than ever."
    )


def rescue_fail(world: World, hero: Entity, mentor: Entity, animal_cfg: AnimalCfg, method: MethodCfg, route: Route) -> None:
    bridge = world.get("bridge")
    animal = world.get("animal")
    bridge.meters["danger"] += 1
    bridge.meters["blocked"] += 1
    animal.meters["stalled"] += 1
    hero.memes["worry"] += 1
    mentor.memes["worry"] += 1
    world.say(
        f"But the plan was not strong enough. {method.fail.replace('{animal}', animal_cfg.label)}."
    )
    world.say(
        f"So they backed away from the middle, led Pip to safety, and made camp on the near side as the sky turned gold."
    )
    world.say(
        f"That night, beside the quiet cart, {hero.id} listened to the bridge creak in the dark and understood why small warnings must never be ignored."
    )


def gift_resolution(world: World, hero: Entity, mentor: Entity, prop: PropCfg) -> None:
    mentor.memes["love"] += 1
    world.say(
        f"At dawn, {mentor.label_word.capitalize()} tied {prop.phrase} more snugly for {hero.id}. "
        f'"Today we cross the careful way," {mentor.pronoun()} said.'
    )


def tell(
    route: Route,
    animal_cfg: AnimalCfg,
    warning: WarningCfg,
    prop: PropCfg,
    method: MethodCfg,
    *,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    mentor_type: str = "mother",
    hero_trait: str = "brave",
    extra_delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait, "dancer"],
        attrs={},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        label="the guide",
        role="mentor",
        attrs={},
    ))
    animal = world.add(Entity(
        id="animal",
        kind="thing",
        type="animal",
        label=animal_cfg.label,
        role="animal",
        attrs={"feet_kind": animal_cfg.feet_kind, "fear_sound": animal_cfg.fear_sound},
    ))
    bridge = world.add(Entity(
        id="bridge",
        kind="thing",
        type="bridge",
        label=route.bridge,
        role="bridge",
        attrs={},
    ))
    cart = world.add(Entity(
        id="cart",
        kind="thing",
        type="cart",
        label="menagerie cart",
        role="cart",
        attrs={},
    ))

    hero.memes["hope"] = 1.0
    hero.memes["rhythm"] = 0.0
    hero.memes["alert"] = 0.0
    hero.memes["resolve"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["pride"] = 0.0
    hero.memes["worry"] = 0.0
    mentor.memes["relief"] = 0.0
    mentor.memes["love"] = 0.0
    mentor.memes["worry"] = 0.0
    animal.memes["fear"] = 0.0
    animal.memes["trust"] = 0.0
    animal.meters["hesitation"] = 0.0
    animal.meters["stalled"] = 0.0
    animal.meters["crossed"] = 0.0
    bridge.meters["strain"] = 0.0
    bridge.meters["danger"] = 0.0
    bridge.meters["blocked"] = 0.0

    world.facts["route"] = route
    world.facts["animal_cfg"] = animal_cfg
    world.facts["warning"] = warning
    world.facts["prop"] = prop
    world.facts["method"] = method
    world.facts["extra_delay"] = extra_delay

    introduce(world, hero, mentor, route, animal_cfg, prop)
    adventure_beat(world, route)

    world.para()
    foreshadow(world, hero, route, warning)
    set_off(world, hero, mentor, animal, route)

    world.para()
    if extra_delay > 0:
        world.say(
            f"A gust and a long pause from the cart gave the danger a little more time to build."
        )
    panic(world, hero, animal, warning)

    world.para()
    choose_method(world, hero, mentor, animal_cfg, method, prop)
    worked = method_works(method.id, animal_cfg.id, warning.id, extra_delay)
    if worked:
        rescue_success(world, hero, mentor, animal, route, method)
    else:
        rescue_fail(world, hero, mentor, animal_cfg, method, route)
        world.para()
        gift_resolution(world, hero, mentor, prop)

    outcome = "crossed" if worked else "camped"
    world.facts.update(
        hero=hero,
        mentor=mentor,
        animal=animal,
        bridge=bridge,
        outcome=outcome,
        worked=worked,
        challenge=challenge_level(animal_cfg.id, warning.id, extra_delay),
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id in ROUTES:
        for animal_id in ANIMALS:
            for warning_id in WARNINGS:
                if hazard_at_risk(route_id, animal_id, warning_id):
                    combos.append((route_id, animal_id, warning_id))
    return combos


@dataclass
class StoryParams:
    route: str
    animal: str
    warning: str
    prop: str
    method: str
    hero_name: str
    hero_gender: str
    mentor: str
    hero_trait: str
    extra_delay: int = 0
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
    "bridge": [
        (
            "Why can an old bridge be dangerous?",
            "Old bridges can have weak boards or ropes that do not hold steady. If they shake or break, people and animals can get scared or stuck."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows a small early clue about something important that will happen later. It helps the later danger feel prepared instead of sudden."
        )
    ],
    "dance": [
        (
            "How can dancing help in a story adventure?",
            "Dancing can help by keeping steps steady and calm. Rhythm can also make a frightened animal feel safer."
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small kind of horse. Ponies can be brave, but they can also get nervous on narrow or noisy paths."
        )
    ],
    "goat": [
        (
            "Why is a goat good at climbing?",
            "Goats have quick feet and good balance. That helps them move over steep or rocky places."
        )
    ],
    "tortoise": [
        (
            "Why does a tortoise move slowly?",
            "A tortoise has a heavy shell and short legs, so it travels at a slow steady pace. That can make tricky crossings take longer."
        )
    ],
    "bells": [
        (
            "What do ankle bells do?",
            "Ankle bells make a light jingling sound when a dancer moves. That sound can help keep steps even and easy to follow."
        )
    ],
    "scarf": [
        (
            "How can a scarf guide someone?",
            "A bright scarf can wave where to go next. Following it can feel easier than staring at a scary path."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful on a journey?",
            "A lantern helps people see where it is safe to put their feet. Good light makes careful choices easier."
        )
    ],
    "repair": [
        (
            "Why is fixing something before using it a good idea?",
            "Fixing a weak thing first makes the danger smaller. It is often safer than hurrying and hoping for the best."
        )
    ],
}
KNOWLEDGE_ORDER = ["foreshadowing", "bridge", "dance", "pony", "goat", "tortoise", "bells", "scarf", "lantern", "repair"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    route = world.facts["route"]
    animal_cfg = world.facts["animal_cfg"]
    warning = world.facts["warning"]
    outcome = world.facts["outcome"]
    if outcome == "crossed":
        return [
            f'Write an adventure story for a 3-to-5-year-old that includes the words "dancer" and "menagerie" and uses foreshadowing at an old bridge.',
            f"Tell a gentle adventure where {hero.id}, a child dancer traveling with a little menagerie, notices that {warning.clue} before crossing {route.bridge}.",
            f"Write a story where {animal_cfg.phrase} is frightened during a crossing, but an early warning helps the heroes solve the problem the careful way.",
        ]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "dancer" and "menagerie" and uses foreshadowing to warn of trouble.',
        f"Tell a story where {hero.id}, a young dancer in a traveling menagerie, notices that {warning.clue} before anyone understands why it matters.",
        f"Write a bridge-crossing adventure where the heroes must stop and camp safely because the warning sign was real and the danger is too big for a weak plan.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    route = f["route"]
    animal_cfg = f["animal_cfg"]
    warning = f["warning"]
    prop = f["prop"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young dancer traveling with a little menagerie, and {mentor.label_word} guiding the cart. They are trying to reach {route.destination}."
        ),
        (
            "What was the early warning sign?",
            f"The early warning sign was that {warning.clue}. That clue matters later because it shows the bridge already had a weak spot before the crossing became scary."
        ),
        (
            "Why was that an example of foreshadowing?",
            f"It was foreshadowing because the story showed the bridge problem before the real trouble started. Later, when Pip panicked on the bridge, the warning finally made sense."
        ),
        (
            "What made the crossing dangerous?",
            f"The crossing was dangerous because the bridge was old and the warning sign showed it was not fully safe. When Pip got frightened, the shaking made the danger even worse."
        ),
    ]
    if outcome == "crossed":
        qa.append(
            (
                "How did they get Pip across safely?",
                f"They used a careful plan: they {method.qa_text}. That worked because it matched the kind of trouble the warning had already hinted at."
            )
        )
        qa.append(
            (
                f"How did {hero.id}'s dancing help?",
                f"{hero.id}'s dancer training helped {hero.pronoun('object')} stay calm and precise. The steady movement gave the frightened animal something safe to trust."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the little menagerie safely beyond the bridge and still heading for {route.destination}. The ending shows that the early warning changed what they did."
            )
        )
    else:
        qa.append(
            (
                "Why did they stop instead of finishing the crossing?",
                f"They stopped because their plan was not strong enough for the danger waiting on the bridge. Turning back kept both the people and the animal safe."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with them camping on the near side and promising to cross more carefully in the morning. That ending proves they learned to respect the warning sign instead of pushing ahead."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"foreshadowing", "bridge", "dance"}
    animal_id = f["animal_cfg"].id
    if animal_id in KNOWLEDGE:
        tags.add(animal_id)
    for tag in f["prop"].tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
    for tag in f["method"].tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="canyon_bridge",
        animal="pony",
        warning="missing_plank",
        prop="ankle_bells",
        method="dance_and_lure",
        hero_name="Mira",
        hero_gender="girl",
        mentor="mother",
        hero_trait="brave",
        extra_delay=0,
    ),
    StoryParams(
        route="jungle_bridge",
        animal="goat",
        warning="frayed_rope",
        prop="silk_scarf",
        method="retie_then_cross",
        hero_name="Nia",
        hero_gender="girl",
        mentor="father",
        hero_trait="careful",
        extra_delay=0,
    ),
    StoryParams(
        route="sea_cliff_bridge",
        animal="pony",
        warning="wind_flag",
        prop="ankle_bells",
        method="dance_and_lure",
        hero_name="Ava",
        hero_gender="girl",
        mentor="mother",
        hero_trait="steady",
        extra_delay=0,
    ),
    StoryParams(
        route="canyon_bridge",
        animal="tortoise",
        warning="frayed_rope",
        prop="lantern_pole",
        method="lead_slowly",
        hero_name="Leo",
        hero_gender="boy",
        mentor="father",
        hero_trait="careful",
        extra_delay=0,
    ),
    StoryParams(
        route="jungle_bridge",
        animal="tortoise",
        warning="frayed_rope",
        prop="silk_scarf",
        method="lead_slowly",
        hero_name="Noah",
        hero_gender="boy",
        mentor="mother",
        hero_trait="hopeful",
        extra_delay=1,
    ),
]


def explain_combo_rejection(route_id: str, animal_id: str, warning_id: str) -> str:
    if not route_supports_warning(route_id, warning_id):
        return (
            f"(No story: the warning '{warning_id}' does not fit {ROUTES[route_id].bridge}. "
            f"That clue would not feel honest in this place.)"
        )
    if not warning_believable(animal_id, warning_id):
        return (
            f"(No story: {WARNINGS[warning_id].clue} is not the kind of clue that would naturally frighten a {ANIMALS[animal_id].label} here.)"
        )
    return "(No story: that route, animal, and warning do not form a believable adventure.)"


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of the safer methods: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "crossed" if method_works(params.method, params.animal, params.warning, params.extra_delay) else "camped"


ASP_RULES = r"""
route_supports_warning(canyon_bridge, wind_flag).
route_supports_warning(sea_cliff_bridge, wind_flag).
route_supports_warning(R, W) :- warning(W), W != wind_flag, route(R).

warning_believable(p, wind_flag) :- false.
warning_believable(pony, wind_flag).
warning_believable(goat, wind_flag).
warning_believable(A, W) :- believable(A, W).

hazard(R, A, W) :- route(R), animal(A), warning(W), route_supports_warning(R, W), warning_believable(A, W).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

challenge(A, W, D, C) :- severity(W, S), nimble(A, N), delay(D), C = S + (2 - N) + D, C >= 1.
challenge(A, W, D, 1) :- severity(W, S), nimble(A, N), delay(D), S + (2 - N) + D < 1.

fits_need(M, W) :- needs_warning(W, N), method_need(M, N).
works(M, A, W, D) :- sensible(M), challenge(A, W, D, C), power(M, P), P >= C,
                     fits_need(M, W), not blocked_by_rhythm(M, A).

blocked_by_rhythm(M, A) :- uses_rhythm(M), not likes_rhythm(A).

outcome(crossed) :- chosen_method(M), chosen_animal(A), chosen_warning(W), delay(D), works(M, A, W, D).
outcome(camped) :- chosen_method(M), chosen_animal(A), chosen_warning(W), delay(D), not works(M, A, W, D).

valid(R, A, W) :- hazard(R, A, W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id in ROUTES:
        lines.append(asp.fact("route", route_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("nimble", animal_id, animal.nimble))
        if animal.likes_rhythm:
            lines.append(asp.fact("likes_rhythm", animal_id))
    for warning_id, warning in WARNINGS.items():
        lines.append(asp.fact("warning", warning_id))
        lines.append(asp.fact("severity", warning_id, warning.severity))
        lines.append(asp.fact("needs_warning", warning_id, warning.needs))
        for animal_id in sorted(warning.believable_for):
            lines.append(asp.fact("believable", animal_id, warning_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
        if method.uses_rhythm:
            lines.append(asp.fact("uses_rhythm", method_id))
        for need in sorted(method.needs):
            lines.append(asp.fact("method_need", method_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_warning", params.warning),
        asp.fact("delay", params.extra_delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "menagerie" not in sample.story or "dancer" not in sample.story:
            raise StoryError("smoke test story missing required core content")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world: a young dancer, a little menagerie, an old bridge, and a foreshadowed problem."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--extra-delay", type=int, choices=[0, 1], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.animal and args.warning:
        if not hazard_at_risk(args.route, args.animal, args.warning):
            raise StoryError(explain_combo_rejection(args.route, args.animal, args.warning))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.animal is None or combo[1] == args.animal)
        and (args.warning is None or combo[2] == args.warning)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, animal_id, warning_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    mentor = args.mentor or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    extra_delay = args.extra_delay if args.extra_delay is not None else rng.choice([0, 0, 1])

    possible_props = sorted(PROPS)
    if METHODS[method_id].uses_rhythm:
        preferred = [pid for pid, p in PROPS.items() if p.kind in {"rhythm", "guide"}]
        prop_id = rng.choice(sorted(preferred))
    else:
        prop_id = rng.choice(possible_props)

    return StoryParams(
        route=route_id,
        animal=animal_id,
        warning=warning_id,
        prop=prop_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=gender,
        mentor=mentor,
        hero_trait=hero_trait,
        extra_delay=extra_delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.warning not in WARNINGS:
        raise StoryError(f"(Unknown warning: {params.warning})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.method and METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if not hazard_at_risk(params.route, params.animal, params.warning):
        raise StoryError(explain_combo_rejection(params.route, params.animal, params.warning))

    world = tell(
        ROUTES[params.route],
        ANIMALS[params.animal],
        WARNINGS[params.warning],
        PROPS[params.prop],
        METHODS[params.method],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mentor_type=params.mentor,
        hero_trait=params.hero_trait,
        extra_delay=params.extra_delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, animal, warning) combos:\n")
        for route_id, animal_id, warning_id in combos:
            print(f"  {route_id:16} {animal_id:8} {warning_id}")
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
            header = f"### {p.hero_name}: {p.animal} on {p.route} ({p.warning}, {p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
