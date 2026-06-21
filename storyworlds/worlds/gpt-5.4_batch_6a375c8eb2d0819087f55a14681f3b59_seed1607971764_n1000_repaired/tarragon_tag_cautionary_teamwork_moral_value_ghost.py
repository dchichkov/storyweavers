#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tarragon_tag_cautionary_teamwork_moral_value_ghost.py
=================================================================================

A standalone story world about a spooky mistake during a game of tag at dusk.
The domain is small and child-facing: two children play near a kitchen garden,
something ghostly seems to move near the tarragon, one child is tempted to dash
off alone, and the safer ending comes from teamwork, honesty, and asking a
grown-up for help.

This world models a gentle ghost-story shape:

- premise: tag at dusk in a place with a herb bed
- tension: a pale shape or eerie sound seems ghostly
- turn: one child wants to investigate alone
- cautionary logic: dark, cluttered hiding spots are unsafe alone
- resolution: teamwork and truth reveal an ordinary cause
- ending image: the game resumes more wisely, with light and company

Run it
------
    python storyworlds/worlds/gpt-5.4/tarragon_tag_cautionary_teamwork_moral_value_ghost.py
    python storyworlds/worlds/gpt-5.4/tarragon_tag_cautionary_teamwork_moral_value_ghost.py --qa
    python storyworlds/worlds/gpt-5.4/tarragon_tag_cautionary_teamwork_moral_value_ghost.py --all
    python storyworlds/worlds/gpt-5.4/tarragon_tag_cautionary_teamwork_moral_value_ghost.py --asp
    python storyworlds/worlds/gpt-5.4/tarragon_tag_cautionary_teamwork_moral_value_ghost.py --verify
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
TEAMWORK_GOOD = 6
BRAVERY_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "kind", "thoughtful", "sensible"}


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
    dark: bool = False
    risky: bool = False
    ghostly: bool = False
    gives_light: bool = False
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

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    dusk_line: str
    tag_line: str
    tarragon_line: str
    caretaker_home: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Spot:
    id: str
    label: str
    the: str
    inside: str
    ground: str
    hiding: str
    spooky: str
    trip_risk: int
    dark: bool = True
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Cause:
    id: str
    label: str
    hint: str
    motion: str
    reveal: str
    fit_spots: set[str] = field(default_factory=set)
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
class Light:
    id: str
    label: str
    phrase: str
    shine: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_trip(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("instigator")
    spot = world.entities.get("spot")
    if child is None or spot is None:
        return out
    if child.meters["entered_alone"] < THRESHOLD:
        return out
    if not spot.dark or not spot.risky:
        return out
    sig = ("trip", child.id, spot.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["scrape"] += 1
    child.meters["stumble"] += 1
    child.memes["fear"] += 2
    world.get("cautioner").memes["fear"] += 1
    world.get("caregiver").memes["concern"] += 1
    out.append("__stumble__")
    return out


def _r_share_courage(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("instigator")
    b = world.entities.get("cautioner")
    if a is None or b is None:
        return out
    if a.meters["stayed_together"] < THRESHOLD or b.meters["stayed_together"] < THRESHOLD:
        return out
    sig = ("share_courage", a.id, b.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["courage"] += 1
    b.memes["courage"] += 1
    a.memes["fear"] = max(0.0, a.memes["fear"] - 1)
    b.memes["fear"] = max(0.0, b.memes["fear"] - 1)
    out.append("__together__")
    return out


CAUSAL_RULES = [
    Rule(name="trip", tag="physical", apply=_r_trip),
    Rule(name="share_courage", tag="social", apply=_r_share_courage),
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


def ghostly_enough(spot: Spot, cause: Cause) -> bool:
    return spot.dark and spot.risky and spot.id in cause.fit_spots


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for spot_id in setting.affords:
            spot = SPOTS[spot_id]
            for cause_id, cause in CAUSES.items():
                if ghostly_enough(spot, cause):
                    combos.append((setting_id, spot_id, cause_id))
    return sorted(combos)


def initial_care(trait: str) -> float:
    return 4.0 if trait in CAREFUL_TRAITS else 2.0


def teamwork_score(relation: str, trust: int, trait: str, cautioner_age: int, instigator_age: int) -> int:
    score = trust // 2 + int(initial_care(trait))
    if relation == "siblings":
        score += 1
    if cautioner_age > instigator_age:
        score += 1
    return score


def would_heed(relation: str, trust: int, trait: str, cautioner_age: int, instigator_age: int) -> bool:
    return teamwork_score(relation, trust, trait, cautioner_age, instigator_age) >= TEAMWORK_GOOD


def predict_stumble(world: World) -> dict:
    sim = world.copy()
    sim.get("instigator").meters["entered_alone"] += 1
    propagate(sim, narrate=False)
    child = sim.get("instigator")
    return {
        "stumble": child.meters["stumble"] >= THRESHOLD,
        "scrape": child.meters["scrape"] >= THRESHOLD,
        "fear": child.memes["fear"],
    }


def play_setup(world: World, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At dusk, {a.id} and {b.id} played tag in {world.setting.place}. "
        f"{world.setting.dusk_line}"
    )
    world.say(world.setting.tag_line)
    world.say(world.setting.tarragon_line)


def ghost_hint(world: World, a: Entity, b: Entity, spot: Spot, cause: Cause) -> None:
    world.say(
        f"Then something pale moved near {spot.the}. {cause.hint}, and {spot.spooky}."
    )
    world.say(
        f'"Did you see that?" {b.id} whispered. For one chilly moment, the game of tag forgot itself.'
    )
    a.memes["bravado"] += 1
    world.say(
        f'"I\'ll go look," {a.id} said, trying to sound bold. "{cause.label.capitalize()} or not, '
        f'I can win tag and catch the mystery too."'
    )


def warn(world: World, a: Entity, b: Entity, spot: Spot) -> None:
    pred = predict_stumble(world)
    world.facts["predicted_stumble"] = pred["stumble"]
    world.facts["predicted_fear"] = pred["fear"]
    b.memes["care"] += 1
    world.say(
        f'{b.id} caught {a.pronoun("possessive")} sleeve. "Don\'t go into {spot.the} alone," '
        f'{b.pronoun()} said. "It is dark there, and {spot.ground}."'
    )
    if pred["stumble"]:
        world.say(
            f'{b.pronoun().capitalize()} could almost picture {a.id} tripping before {a.pronoun()} '
            f'ever reached the pale shape.'
        )


def dash_alone(world: World, a: Entity, spot: Spot) -> None:
    a.meters["entered_alone"] += 1
    a.memes["defiance"] += 1
    world.say(
        f'But the wish to prove {a.pronoun("object")}self brave was louder than the warning. '
        f'{a.id} darted toward {spot.the} alone.'
    )
    propagate(world, narrate=False)


def stumble(world: World, a: Entity, spot: Spot) -> None:
    if a.meters["stumble"] >= THRESHOLD:
        world.say(
            f'Inside {spot.the}, {a.pronoun()} caught {a.pronoun("possessive")} foot on {spot.ground} '
            f'and stumbled with a frightened gasp.'
        )
        if a.meters["scrape"] >= THRESHOLD:
            world.say(
                f'{a.pronoun("possessive").capitalize()} knee got a little scrape, and all at once '
                f'the place felt far darker than it had from the path.'
            )


def call_help(world: World, b: Entity, caregiver: Entity) -> None:
    b.memes["honesty"] += 1
    world.say(f'"{caregiver.label_word.capitalize()}!" {b.id} called. "Please come help us!"')


def together_choice(world: World, a: Entity, b: Entity, caregiver: Entity) -> None:
    a.meters["stayed_together"] += 1
    b.meters["stayed_together"] += 1
    a.memes["honesty"] += 1
    b.memes["honesty"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} took a breath and looked back at {b.id}. Then {a.pronoun()} nodded. '
        f'"You\'re right," {a.pronoun()} said. "We should stay together and tell {caregiver.label_word}."'
    )
    world.say(
        f'They walked side by side instead of creeping off alone, and the scary feeling shrank a little with every step.'
    )


def caregiver_arrives(world: World, caregiver: Entity, light: Light, spot: Spot) -> None:
    lamp = world.get("light")
    lamp.gives_light = True
    caregiver.memes["calm"] += 1
    world.say(
        f'{caregiver.label_word.capitalize()} came from {world.setting.caretaker_home} carrying {light.phrase} that {light.shine}.'
    )
    world.say(
        f'In the new light, {spot.the} looked smaller and less ghostly.'
    )


def reveal(world: World, caregiver: Entity, cause: Cause, spot: Spot) -> None:
    world.say(
        f'It was not a ghost at all. {cause.reveal}'
    )
    world.say(
        f'{caregiver.label_word.capitalize()} smiled gently. "Spooky things look bigger in the dark," '
        f'{caregiver.pronoun()} said.'
    )


def comfort_after_stumble(world: World, caregiver: Entity, a: Entity, b: Entity, spot: Spot) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'{caregiver.label_word.capitalize()} brushed the dirt from {a.id}\'s knee and kept both children close.'
    )
    world.say(
        f'"Being brave does not mean hurrying into {spot.the} alone," {caregiver.pronoun()} said. '
        f'"Real bravery is telling the truth when you are scared and staying where someone can help."'
    )


def calm_lesson(world: World, caregiver: Entity, a: Entity, b: Entity, spot: Spot) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'"You did the wise thing," {caregiver.label_word} told them. "When a place is dark and uncertain, '
        f'go together or ask for help first."'
    )


def wiser_game(world: World, a: Entity, b: Entity, light: Light) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f'Soon the shadows no longer felt like teeth and whispers. With {light.phrase} nearby, '
        f'{a.id} and {b.id} played tag again, slower now, calling out where they were going.'
    )
    world.say(
        f'The tarragon leaves stirred in the evening air, smelling green and clean, and the game ended with both children together instead of one child alone.'
    )


def tell(
    setting: Setting,
    spot_cfg: Spot,
    cause_cfg: Cause,
    light_cfg: Light,
    *,
    instigator: str = "Mina",
    instigator_gender: str = "girl",
    cautioner: str = "Theo",
    cautioner_gender: str = "boy",
    caregiver_type: str = "grandmother",
    trait: str = "careful",
    relation: str = "friends",
    trust: int = 6,
    instigator_age: int = 6,
    cautioner_age: int = 7,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=caregiver_type,
        label="the caregiver",
        role="caregiver",
        attrs={},
    ))
    spot = world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot_cfg.label,
        dark=spot_cfg.dark,
        risky=spot_cfg.risky,
        ghostly=True,
        attrs={"spot_id": spot_cfg.id},
    ))
    cause = world.add(Entity(
        id="cause",
        kind="thing",
        type="cause",
        label=cause_cfg.label,
        ghostly=True,
        attrs={"cause_id": cause_cfg.id},
    ))
    light = world.add(Entity(
        id="light",
        kind="thing",
        type="light",
        label=light_cfg.label,
        gives_light=False,
        attrs={"light_id": light_cfg.id},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["care"] = initial_care(trait)
    b.memes["trust"] = float(trust)
    caregiver.memes["calm"] = 1.0
    caregiver.memes["concern"] = 0.0
    a.meters["entered_alone"] = 0.0
    a.meters["stayed_together"] = 0.0
    b.meters["stayed_together"] = 0.0
    a.meters["scrape"] = 0.0
    a.meters["stumble"] = 0.0

    world.facts.update(
        setting=setting,
        spot_cfg=spot_cfg,
        cause_cfg=cause_cfg,
        light_cfg=light_cfg,
        instigator=a,
        cautioner=b,
        caregiver=caregiver,
        relation=relation,
        trust=trust,
        trait=trait,
    )

    play_setup(world, a, b)
    ghost_hint(world, a, b, spot_cfg, cause_cfg)

    world.para()
    warn(world, a, b, spot_cfg)
    heed = would_heed(relation, trust, trait, cautioner_age, instigator_age)

    if heed:
        together_choice(world, a, b, caregiver)
        world.para()
        caregiver_arrives(world, caregiver, light_cfg, spot_cfg)
        reveal(world, caregiver, cause_cfg, spot_cfg)
        calm_lesson(world, caregiver, a, b, spot_cfg)
        world.para()
        wiser_game(world, a, b, light_cfg)
        outcome = "heeded"
    else:
        dash_alone(world, a, spot_cfg)
        stumble(world, a, spot_cfg)
        call_help(world, b, caregiver)
        world.para()
        caregiver_arrives(world, caregiver, light_cfg, spot_cfg)
        reveal(world, caregiver, cause_cfg, spot_cfg)
        comfort_after_stumble(world, caregiver, a, b, spot_cfg)
        world.para()
        wiser_game(world, a, b, light_cfg)
        outcome = "rescued"

    world.facts.update(
        outcome=outcome,
        heeded=heed,
        stumbled=a.meters["stumble"] >= THRESHOLD,
        scraped=a.meters["scrape"] >= THRESHOLD,
        teamwork=teamwork_score(relation, trust, trait, cautioner_age, instigator_age),
        promised_help=a.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the old garden behind the house",
        dusk_line="The last light lay thin as silver thread on the path, and the beds of herbs made small shadowy islands.",
        tag_line='"No hiding by the gate," one of them laughed, and then their running feet pattered over the stones.',
        tarragon_line="Near the kitchen wall, a patch of tarragon breathed out a sharp sweet smell whenever the wind touched it.",
        caretaker_home="the warm back porch",
        affords={"greenhouse", "shed", "arbor"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the little orchard beside the cottage",
        dusk_line="The pear trees made long dark bars on the grass, and the evening birds had almost gone quiet.",
        tag_line='They played tag between the trunks, calling "You\'re it!" and laughing under the leaves.',
        tarragon_line="Beside the path, a narrow bed of tarragon shivered in the breeze and scented the air like supper herbs.",
        caretaker_home="the kitchen door",
        affords={"shed", "arbor"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the stone courtyard behind the inn",
        dusk_line="The walls held the twilight close, so every corner looked deeper than it really was.",
        tag_line='Their game of tag bounced from wall to wall with quick footsteps and breathless giggles.',
        tarragon_line="A wooden box of tarragon grew under the window, and the crushed leaves smelled bright against the cool air.",
        caretaker_home="the lamp-lit hallway",
        affords={"greenhouse", "shed"},
    ),
}

SPOTS = {
    "greenhouse": Spot(
        id="greenhouse",
        label="greenhouse",
        the="the greenhouse",
        inside="between the benches",
        ground="loose pots and a curled hose lay across the floor",
        hiding="behind the misty glass",
        spooky="the panes clicked softly together like teeth",
        trip_risk=2,
        dark=True,
        risky=True,
        tags={"greenhouse", "dark_place"},
    ),
    "shed": Spot(
        id="shed",
        label="tool shed",
        the="the tool shed",
        inside="past the hanging tools",
        ground="the floor was uneven with a rake and a bucket near the door",
        hiding="through the cracked doorway",
        spooky="something scraped once and then went still",
        trip_risk=2,
        dark=True,
        risky=True,
        tags={"shed", "dark_place"},
    ),
    "arbor": Spot(
        id="arbor",
        label="vine arbor",
        the="the vine arbor",
        inside="under the hanging leaves",
        ground="thick roots rose in little twists under the dirt",
        hiding="inside the woven shadows",
        spooky="the vines fluttered together with a whispery hiss",
        trip_risk=1,
        dark=True,
        risky=True,
        tags={"arbor", "dark_place"},
    ),
    "sunny_path": Spot(
        id="sunny_path",
        label="sunny path",
        the="the sunny path",
        inside="out in the open",
        ground="the stones were flat and clear",
        hiding="beside the hedge",
        spooky="nothing in it could truly seem ghostly",
        trip_risk=0,
        dark=False,
        risky=False,
        tags={"path"},
    ),
}

CAUSES = {
    "sheet": Cause(
        id="sheet",
        label="ghostly sheet",
        hint="A white washing sheet lifted and sank on the line",
        motion="lifted and sank",
        reveal="A sheet from the wash had caught on a peg and was flapping itself silly in the breeze.",
        fit_spots={"greenhouse", "shed", "arbor"},
        tags={"sheet", "wind"},
    ),
    "scarecrow": Cause(
        id="scarecrow",
        label="bent scarecrow",
        hint="A tall shape nodded once as the wind turned it",
        motion="nodded",
        reveal="An old scarecrow coat had slipped sideways on its post, so its sleeves looked like reaching arms.",
        fit_spots={"greenhouse", "arbor"},
        tags={"scarecrow", "wind"},
    ),
    "cat": Cause(
        id="cat",
        label="garden cat",
        hint="Two pale eyes blinked and a tin tag gave a tiny clink",
        motion="blinked",
        reveal="It was only the garden cat, nosing around with a shiny name tag that tapped against its dish.",
        fit_spots={"shed", "greenhouse"},
        tags={"cat", "tag"},
    ),
    "coat": Cause(
        id="coat",
        label="hanging coat",
        hint="A long coat swayed from a hook where no one had noticed it before",
        motion="swayed",
        reveal="A gardener's long coat had been left on a peg, and the sleeves waved whenever the door breathed open.",
        fit_spots={"shed"},
        tags={"coat", "wind"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        shine="cut a bright yellow path through the dark",
        tags={"flashlight", "light"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        shine="glowed warm as honey",
        tags={"lantern", "light"},
    ),
    "porch_lamp": Light(
        id="porch_lamp",
        label="porch lamp",
        phrase="the porch lamp in careful hands",
        shine="washed the shadows thin",
        tags={"lamp", "light"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "June", "Nora", "Ella", "Ruby", "Mae", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Max", "Owen", "Finn", "Eli", "Sam", "Jude"]
TRAITS = ["careful", "steady", "kind", "thoughtful", "curious", "brisk", "sensible"]


@dataclass
class StoryParams:
    setting: str
    spot: str
    cause: str
    light: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    caregiver: str
    trait: str
    relation: str = "friends"
    trust: int = 6
    instigator_age: int = 6
    cautioner_age: int = 7
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
    "tag": [
        (
            "What is tag?",
            "Tag is a running game where one player tries to touch another player and say who is next. It is more fun when everyone knows where the safe places and the rules are."
        )
    ],
    "tarragon": [
        (
            "What is tarragon?",
            "Tarragon is a green herb with thin leaves and a strong smell. Grown-ups use it to flavor food."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps you see where your feet are going. Good light can make a scary place easier to understand."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives steady light all around it. People use it so dark places are easier to see."
        )
    ],
    "cat": [
        (
            "Why might a cat seem spooky at night?",
            "At night, a cat's eyes can catch the light and shine. If you only see the eyes and hear a little sound, it can seem stranger than it really is."
        )
    ],
    "dark_place": [
        (
            "Why should children be careful in dark places?",
            "Dark places can hide roots, tools, or steps. Going slowly, staying with someone, and asking for help keeps you safer."
        )
    ],
    "teamwork": [
        (
            "What does teamwork mean?",
            "Teamwork means people help each other instead of acting alone. In a scary moment, teamwork can turn panic into a good plan."
        )
    ],
    "honesty": [
        (
            "Why is it good to tell the truth when you feel scared?",
            "Telling the truth helps other people understand what is wrong and help quickly. Pretending not to be scared can lead to unsafe choices."
        )
    ],
}
KNOWLEDGE_ORDER = ["tag", "tarragon", "dark_place", "flashlight", "lantern", "cat", "teamwork", "honesty"]


def display_name(ent: Entity) -> str:
    return ent.label or ent.id


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    caregiver = f["caregiver"]
    setting = f["setting"]
    spot = f["spot_cfg"]
    cause = f["cause_cfg"]
    outcome = f["outcome"]
    if outcome == "heeded":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "tarragon" and "tag", where two children stop playing tag at dusk because something near {spot.the} looks ghostly.',
            f"Tell a cautionary teamwork story where {display_name(a)} wants to investigate alone, but {display_name(b)} persuades {a.pronoun('object')} to stay together and ask {caregiver.label_word} for help.",
            f"Write a small spooky story with a warm ending in {setting.place}, where honesty and teamwork reveal that the ghostly shape was only {cause.label}.",
        ]
    return [
        f'Write a child-friendly ghost story that includes the words "tarragon" and "tag", where a child runs toward a spooky shape near {spot.the} and learns a careful lesson.',
        f"Tell a cautionary story where {display_name(a)} ignores {display_name(b)}'s warning, stumbles in the dark, and a calm {caregiver.label_word} helps reveal the harmless cause.",
        f"Write a spooky-but-safe story in {setting.place} where teamwork, honesty, and asking for help matter more than pretending to be brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    caregiver = f["caregiver"]
    setting = f["setting"]
    spot = f["spot_cfg"]
    cause = f["cause_cfg"]
    light = f["light_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, f['relation'])}, {display_name(a)} and {display_name(b)}, playing tag in {setting.place}. A calm {caregiver.label_word} helps them when the spooky moment comes."
        ),
        (
            "What made the place feel spooky?",
            f"Something pale or strange moved near {spot.the}, and in the dusk it looked ghostly. The darkness and the uncertain shapes made an ordinary thing seem much scarier than it was."
        ),
        (
            f"Why did {display_name(b)} tell {display_name(a)} not to go alone?",
            f"{display_name(b)} knew {spot.the} was dark and that {spot.ground}. {b.pronoun().capitalize()} was trying to keep {display_name(a)} from getting hurt before they even reached the strange shape."
        ),
    ]
    if f["outcome"] == "heeded":
        qa.append(
            (
                f"What did the children do instead of going into {spot.the} alone?",
                f"They stayed together and went to tell {caregiver.label_word}. That choice made the fear smaller because they had light, help, and each other."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the mystery explained and the children playing tag again near the tarragon. The ending shows they learned that teamwork and asking for help are wiser than creeping off alone."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {display_name(a)} ran toward {spot.the} alone?",
                f"{display_name(a)} stumbled in the dark and got a little scrape. The accident happened because the ground was hard to see and {a.pronoun()} went in alone instead of waiting for help."
            )
        )
        qa.append(
            (
                f"How did {display_name(b)} and {caregiver.label_word} help?",
                f"{display_name(b)} called for help right away, and {caregiver.label_word} came with {light.phrase}. The light and the quick help turned a frightening mistake into a safe lesson."
            )
        )
    qa.append(
        (
            "What was the ghost really?",
            f"It was really {cause.reveal[0].lower() + cause.reveal[1:]} The children had mistaken an ordinary sight for something supernatural because they saw it in the dark."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tag", "tarragon", "dark_place", "teamwork", "honesty"}
    tags |= set(f["light_cfg"].tags)
    tags |= set(f["cause_cfg"].tags)
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
        flags = [n for n, on in (("dark", e.dark), ("risky", e.risky), ("ghostly", e.ghostly), ("gives_light", e.gives_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        spot="greenhouse",
        cause="sheet",
        light="lantern",
        instigator="Mina",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        caregiver="grandmother",
        trait="careful",
        relation="friends",
        trust=7,
        instigator_age=6,
        cautioner_age=7,
    ),
    StoryParams(
        setting="orchard",
        spot="shed",
        cause="cat",
        light="flashlight",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        caregiver="grandfather",
        trait="thoughtful",
        relation="siblings",
        trust=8,
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        setting="courtyard",
        spot="shed",
        cause="coat",
        light="porch_lamp",
        instigator="Ruby",
        instigator_gender="girl",
        cautioner="Max",
        cautioner_gender="boy",
        caregiver="aunt",
        trait="curious",
        relation="friends",
        trust=3,
        instigator_age=7,
        cautioner_age=6,
    ),
    StoryParams(
        setting="garden",
        spot="arbor",
        cause="scarecrow",
        light="flashlight",
        instigator="Owen",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        caregiver="uncle",
        trait="steady",
        relation="siblings",
        trust=6,
        instigator_age=6,
        cautioner_age=8,
    ),
]


def explain_rejection(spot: Spot, cause: Cause) -> str:
    if not spot.dark or not spot.risky:
        return (
            f"(No story: {spot.the} is not dark and risky enough for a cautionary ghost tale. "
            f"The child needs a place where going alone could honestly be unsafe.)"
        )
    if spot.id not in cause.fit_spots:
        return (
            f"(No story: {cause.label} would not plausibly look ghostly at {spot.the}. "
            f"Pick a cause that fits that place.)"
        )
    return "(No story: this combination does not make a reasonable ghostly misunderstanding.)"


def explain_light(light_id: str) -> str:
    return f"(No story: light '{light_id}' is not in the light registry.)"


def outcome_of(params: StoryParams) -> str:
    if would_heed(params.relation, params.trust, params.trait, params.cautioner_age, params.instigator_age):
        return "heeded"
    return "rescued"


ASP_RULES = r"""
% --- valid story gate ------------------------------------------------------
ghostly_enough(S, C) :- spot(S), cause(C), dark(S), risky(S), fits(C, S).
valid(Place, S, C) :- setting(Place), affords(Place, S), ghostly_enough(S, C).

% --- teamwork / outcome model ---------------------------------------------
care_bonus(4) :- trait(T), careful_trait(T).
care_bonus(2) :- trait(T), not careful_trait(T).

relation_bonus(1) :- relation(siblings).
relation_bonus(0) :- not relation(siblings).

age_bonus(1) :- cautioner_age(CA), instigator_age(IA), CA > IA.
age_bonus(0) :- cautioner_age(CA), instigator_age(IA), CA <= IA.

trust_part(T / 2) :- trust(T).

teamwork_score(TP + CB + RB + AB) :-
    trust_part(TP), care_bonus(CB), relation_bonus(RB), age_bonus(AB).

heeded :- teamwork_score(S), teamwork_good(G), S >= G.
outcome(heeded) :- heeded.
outcome(rescued) :- not heeded.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, spot))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        if spot.dark:
            lines.append(asp.fact("dark", sid))
        if spot.risky:
            lines.append(asp.fact("risky", sid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for spot_id in sorted(cause.fit_spots):
            lines.append(asp.fact("fits", cid, spot_id))
    for lid in LIGHTS:
        lines.append(asp.fact("light", lid))
    lines.append(asp.fact("teamwork_good", TEAMWORK_GOOD))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
        asp.fact("relation", params.relation),
        asp.fact("trust", params.trust),
        asp.fact("trait", params.trait),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
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
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small ghost-story world about tag, tarragon, teamwork, and not going alone into dark places."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--caregiver", choices=["grandmother", "grandfather", "aunt", "uncle", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.cause:
        spot = SPOTS[args.spot]
        cause = CAUSES[args.cause]
        if not ghostly_enough(spot, cause):
            raise StoryError(explain_rejection(spot, cause))
    if args.spot and args.spot not in SPOTS:
        raise StoryError("(No story: unknown spot.)")
    if args.light and args.light not in LIGHTS:
        raise StoryError(explain_light(args.light))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spot is None or combo[1] == args.spot)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, spot_id, cause_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    caregiver = args.caregiver or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings"])
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    instigator_age, cautioner_age = ages[0], ages[1]
    trust = rng.randint(2, 9)

    return StoryParams(
        setting=setting_id,
        spot=spot_id,
        cause=cause_id,
        light=light_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        caregiver=caregiver,
        trait=trait,
        relation=relation,
        trust=trust,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(No story: unknown spot '{params.spot}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(No story: unknown light '{params.light}'.)")
    if params.caregiver not in {"grandmother", "grandfather", "aunt", "uncle", "mother", "father"}:
        raise StoryError(f"(No story: unknown caregiver '{params.caregiver}'.)")

    setting = SETTINGS[params.setting]
    spot = SPOTS[params.spot]
    cause = CAUSES[params.cause]
    if params.spot not in setting.affords:
        raise StoryError(f"(No story: {spot.the} is not part of {setting.place} in this world.)")
    if not ghostly_enough(spot, cause):
        raise StoryError(explain_rejection(spot, cause))

    world = tell(
        setting=setting,
        spot_cfg=spot,
        cause_cfg=cause,
        light_cfg=LIGHTS[params.light],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        caregiver_type=params.caregiver,
        trait=params.trait,
        relation=params.relation,
        trust=params.trust,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
    )

    return StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner),
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
        print(f"{len(combos)} compatible (setting, spot, cause) combos:\n")
        for setting_id, spot_id, cause_id in combos:
            print(f"  {setting_id:10} {spot_id:10} {cause_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.spot} / {p.cause} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
