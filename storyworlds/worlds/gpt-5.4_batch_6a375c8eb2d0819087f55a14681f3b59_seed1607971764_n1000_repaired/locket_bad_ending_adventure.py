#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py
=========================================================

A standalone story world for a small adventure tale about a treasured locket,
a dangerous shortcut, and the sad cost of not choosing the safe path.

The domain aims for a child-facing *adventure* tone: map, lookout, cove, ruins,
trail, rope, ranger. The world model drives the prose:

- two children set out on a pretend-real adventure toward a special place
- one child wears a family locket as a lucky charm
- a dangerous shortcut promises speed and excitement
- the other child warns that the hazard can make them slip
- if the warning fails, the shortcut goes wrong and the locket is knocked loose
- sometimes a strong rescue recovers it, but in the bad-ending branch it is lost

The model includes:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus an inline ASP twin
- state-grounded prompts, story Q&A, and world-knowledge Q&A
- verify mode that checks ASP/Python parity and runs generation smoke tests

Run it
------
    python storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py
    python storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py --hazard tide_rocks
    python storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py --response grab_hand
    python storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py --all
    python storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/locket_bad_ending_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    wearable: bool = False
    secure_clasp: bool = False
    # Two axes used uniformly: physical state and emotional state.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "guide_f"}
        male = {"boy", "father", "man", "guide_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "guide_f": "guide",
            "guide_m": "guide",
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
class Adventure:
    id: str
    scene: str
    opening: str
    goal: str
    goal_place: str
    map_word: str
    ending_image: str
    hazards: set[str] = field(default_factory=set)
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
class Hazard:
    id: str
    label: str
    kind: str
    shortcut: str
    warning: str
    stumble: str
    loss: str
    place_line: str
    severity: int
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
class Response:
    id: str
    label: str
    kinds: set[str]
    sense: int
    power: int
    success_text: str
    fail_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


def _r_slip_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    locket = world.get("locket")
    if hero.meters["slipping"] < THRESHOLD:
        return out
    sig = ("slip_fear", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    world.get("friend").memes["fear"] += 1
    locket.meters["dangling"] += 1
    out.append("__slip__")
    return out


def _r_locket_falls(world: World) -> list[str]:
    out: list[str] = []
    locket = world.get("locket")
    if locket.meters["dangling"] < THRESHOLD:
        return out
    sig = ("locket_falls", locket.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    locket.meters["lost_risk"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip_fear", tag="social", apply=_r_slip_fear),
    Rule(name="locket_falls", tag="physical", apply=_r_locket_falls),
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


def hazard_supported(adventure: Adventure, hazard: Hazard) -> bool:
    return hazard.id in adventure.hazards


def sensible_responses_for(hazard: Hazard) -> list[Response]:
    return [
        r for r in RESPONSES.values()
        if hazard.kind in r.kinds and r.sense >= SENSE_MIN
    ]


def hazard_severity(hazard: Hazard, delay: int) -> int:
    return hazard.severity + delay


def recovered(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard_severity(hazard, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    friend_older = relation == "siblings" and friend_age > hero_age
    authority = initial_caution(trait) + 1.0 + (4.0 if friend_older else 0.0)
    return friend_older and authority > BRAVERY_INIT


def predict_loss(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["slipping"] += 1
    propagate(sim, narrate=False)
    locket = sim.get("locket")
    return {
        "slip": hero.meters["slipping"] >= THRESHOLD,
        "dangling": locket.meters["dangling"] >= THRESHOLD,
        "loss_risk": locket.meters["lost_risk"] >= THRESHOLD,
    }


def setup(world: World, adventure: Adventure, hero: Entity, friend: Entity, guide: Entity) -> None:
    for kid in (hero, friend):
        kid.memes["joy"] += 1
    world.say(
        f"Early that afternoon, {hero.id} and {friend.id} set out for {adventure.scene}. "
        f"{adventure.opening}"
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} folded {adventure.map_word}, "
        f"and around {hero.pronoun('possessive')} neck hung a small silver locket "
        f"from Grandma, bright as a secret moon."
    )
    world.say(
        f'"If we follow the map, we can reach {adventure.goal_place} before the sun tips low," '
        f'{hero.id} said. Even {guide.label_word} smiled at how grand the plan sounded.'
    )


def approach(world: World, adventure: Adventure, hazard: Hazard, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Soon the trail bent toward {adventure.goal_place}. {hazard.place_line}"
    )
    world.say(
        f"A safe path curled the long way around, but {hazard.shortcut} looked faster, "
        f"and much more like the sort of daring move in a real adventure."
    )
    friend.memes["worry"] += 1
    world.say(
        f'{friend.id} slowed down and squinted at it. "That way looks wrong," '
        f'{friend.pronoun()} said.'
    )


def tempt(world: World, hazard: Hazard, hero: Entity) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} grinned. "Adventurers do not creep," {hero.pronoun()} said. '
        f'"We take the shortcut."'
    )


def warn(world: World, hazard: Hazard, hero: Entity, friend: Entity) -> None:
    pred = predict_loss(world, hazard)
    world.facts["predicted_loss"] = pred["loss_risk"]
    friend.memes["caution"] += 1
    extra = ""
    if friend.memes["caution"] >= 6:
        extra = f" {friend.pronoun().capitalize()} held out a hand, already sure the shortcut was a mistake."
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "{hazard.warning} '
        f'If you slip, your locket could come loose."{extra}'
    )


def back_down(world: World, hero: Entity, friend: Entity, guide: Entity, adventure: Adventure) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["bravery"] = 0.0
    world.say(
        f"{hero.id} looked at the locket, then at {friend.id}, and the brave grin faded. "
        f'"All right," {hero.pronoun()} said. "We can still be explorers on the safe path."'
    )
    world.say(
        f"They took the long trail with {guide.label_word}, reached {adventure.goal_place}, "
        f"and the locket stayed warm and safe against {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"From there they saw {adventure.ending_image}, and the adventure felt wiser than it had at the start."
    )


def defy(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["defiance"] += 1
    if hero.attrs.get("relation") == "siblings" and hero.age > friend.age:
        world.say(
            f'"Stay close," {hero.id} said, already stepping forward like an older captain. '
            f'{friend.id} hated the idea, but did not stop {hero.pronoun("object")}.'
        )
    else:
        world.say(
            f'{hero.id} only waved once and stepped onto the shortcut before anyone could argue again.'
        )


def crossing(world: World, hazard: Hazard, hero: Entity) -> None:
    hero.meters["slipping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For one heartbeat the shortcut almost worked. Then {hazard.stumble}"
    )
    world.say(
        f"The locket chain snapped tight, flashed once in the light, and flew free."
    )
    world.get("locket").meters["lost"] += 1


def cry_out(world: World, hero: Entity, friend: Entity, guide: Entity, hazard: Hazard) -> None:
    world.say(f'"My locket!" {hero.id} cried.')
    world.say(
        f'{friend.id} gasped and called for {guide.label_word}. The little adventure suddenly felt real and frightening.'
    )


def rescue_success(world: World, guide: Entity, response: Response, hero: Entity, hazard: Hazard) -> None:
    locket = world.get("locket")
    locket.meters["lost"] = 0.0
    locket.meters["recovered"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{guide.label_word.capitalize()} moved fast and {response.success_text}."
    )
    world.say(
        f"In another moment the locket was back in {hero.id}'s shaking hands, muddy and cold but not gone."
    )


def rescue_fail(world: World, guide: Entity, response: Response, hero: Entity, hazard: Hazard) -> None:
    hero.memes["grief"] += 1
    friend = world.get("friend")
    friend.memes["grief"] += 1
    world.say(
        f"{guide.label_word.capitalize()} tried to help and {response.fail_text}."
    )
    world.say(
        f"{hazard.loss} The silver flash vanished, and the place swallowed it as if it had never been there."
    )


def lesson_happy(world: World, guide: Entity, hero: Entity, friend: Entity) -> None:
    for kid in (hero, friend):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{guide.label_word.capitalize()} crouched beside them. "An adventure still needs sense," '
        f'{guide.pronoun()} said. "A shortcut is not brave if it throws away what matters."'
    )
    world.say(
        f"{hero.id} pressed the locket to {hero.pronoun('possessive')} chest and nodded. "
        f"{friend.id} nodded too, still pale but smiling."
    )


def lesson_bad(world: World, guide: Entity, hero: Entity, friend: Entity, adventure: Adventure) -> None:
    for kid in (hero, friend):
        kid.memes["lesson"] += 1
    world.say(
        f"For a while nobody spoke. Then {guide.label_word} put an arm around both children."
    )
    world.say(
        f'"Things can be replaced, but some things cannot be reached once we make a careless choice," '
        f'{guide.pronoun()} said softly. "{adventure.goal} can wait. People matter first, and safe paths matter too."'
    )
    world.say(
        f"{hero.id} touched the empty place at {hero.pronoun('possessive')} collar and wished very hard for one minute back."
    )


def ending_bad(world: World, hero: Entity, friend: Entity, adventure: Adventure) -> None:
    hero.memes["joy"] = 0.0
    friend.memes["joy"] = 0.0
    world.say(
        f"They turned away from {adventure.goal_place} and walked home by the long path instead."
    )
    world.say(
        f"The map still rustled in {hero.id}'s pocket, but the adventure had gone flat. "
        f"Without the locket, even the evening light on {adventure.ending_image} looked far away and lonely."
    )


def ending_happy(world: World, hero: Entity, friend: Entity, adventure: Adventure) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"A little later they reached {adventure.goal_place} by the safer trail."
    )
    world.say(
        f"The wind lifted their hair, {adventure.ending_image} spread below them, and the locket glimmered quietly where it belonged."
    )


def tell(
    adventure: Adventure,
    hazard: Hazard,
    response: Response,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    friend_name: str = "Theo",
    friend_gender: str = "boy",
    guide_type: str = "guide_f",
    trait: str = "careful",
    delay: int = 1,
    hero_age: int = 6,
    friend_age: int = 5,
    relation: str = "friends",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        age=hero_age,
        attrs={"relation": relation},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type=guide_type,
        label="the guide",
        role="guide",
    ))
    locket = world.add(Entity(
        id="locket",
        kind="thing",
        type="locket",
        label="locket",
        wearable=True,
        secure_clasp=True,
    ))

    hero.memes["bravery"] = BRAVERY_INIT
    friend.memes["caution"] = initial_caution(trait)
    friend.memes["trust"] = 5.0
    locket.meters["worn"] = 1.0
    world.facts["adventure"] = adventure
    world.facts["hazard_cfg"] = hazard
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["relation"] = relation

    setup(world, adventure, hero, friend, guide)
    world.para()
    approach(world, adventure, hazard, hero, friend)
    tempt(world, hazard, hero)
    warn(world, hazard, hero, friend)

    averted = would_avert(relation, hero_age, friend_age, trait)
    if averted:
        world.para()
        back_down(world, hero, friend, guide, adventure)
        outcome = "averted"
    else:
        defy(world, hero, friend)
        world.para()
        crossing(world, hazard, hero)
        cry_out(world, hero, friend, guide, hazard)
        sev = hazard_severity(hazard, delay)
        world.get("locket").meters["severity"] = float(sev)
        got_back = recovered(response, hazard, delay)
        world.para()
        if got_back:
            rescue_success(world, guide, response, hero, hazard)
            lesson_happy(world, guide, hero, friend)
            world.para()
            ending_happy(world, hero, friend, adventure)
            outcome = "recovered"
        else:
            rescue_fail(world, guide, response, hero, hazard)
            lesson_bad(world, guide, hero, friend, adventure)
            world.para()
            ending_bad(world, hero, friend, adventure)
            outcome = "lost"

    world.facts.update(
        hero=hero,
        friend=friend,
        guide=guide,
        locket=locket,
        ignited=False,
        adventure_cfg=adventure,
        hazard=hazard,
        outcome=outcome,
        recovered=(outcome == "recovered"),
        lost=(outcome == "lost"),
        averted=(outcome == "averted"),
    )
    return world


ADVENTURES = {
    "cove": Adventure(
        id="cove",
        scene="the windy path above Gull Cove",
        opening="A paper map showed a star near the old lookout, and both children had decided that meant treasure, or at least a wonderful secret.",
        goal="the hidden lookout",
        goal_place="the hidden lookout",
        map_word="map",
        ending_image="the sea folded into blue shining ribbons below",
        hazards={"tide_rocks", "bridge_gap"},
    ),
    "ruins": Adventure(
        id="ruins",
        scene="the ivy-grown hill above the old stone ruins",
        opening="Their map marked a moon gate in red pencil, and the whole slope smelled of thyme and warm dust.",
        goal="the moon gate",
        goal_place="the moon gate",
        map_word="map",
        ending_image="the broken towers glowing orange in the late sun",
        hazards={"crumbled_wall", "bridge_gap"},
    ),
    "falls": Adventure(
        id="falls",
        scene="the pine trail near Fern Falls",
        opening="A tiny X on the map promised a secret ledge where the waterfall could be seen through the trees like silver thread.",
        goal="the fern ledge",
        goal_place="the fern ledge",
        map_word="map",
        ending_image="mist rising over the waterfall like white breath",
        hazards={"stream_log", "tide_rocks"},
    ),
}

HAZARDS = {
    "stream_log": Hazard(
        id="stream_log",
        label="stream log",
        kind="water",
        shortcut="a narrow log over the stream",
        warning="That log is slick with spray.",
        stumble="hero's foot skidded on the wet bark, and hero pinwheeled over the rushing water".replace("hero", "the child's"),
        loss="The locket dropped between the black stones and was swept under the racing water",
        place_line="Across the last bend ran a cold stream, noisy with white bubbles.",
        severity=2,
        tags={"stream", "water", "rope"},
    ),
    "tide_rocks": Hazard(
        id="tide_rocks",
        label="tide rocks",
        kind="water",
        shortcut="a line of dark tide rocks cut by foamy water",
        warning="Those rocks are shiny and slippery.",
        stumble="one shoe slid sideways, and the child lurched hard over the foam",
        loss="The locket bounced once on the rock edge and slipped into the churning water below",
        place_line="Below the path, the tide crashed in and out of sharp black rocks.",
        severity=3,
        tags={"water", "tide", "rope"},
    ),
    "bridge_gap": Hazard(
        id="bridge_gap",
        label="bridge gap",
        kind="height",
        shortcut="the broken middle of an old footbridge",
        warning="The boards there do not meet anymore.",
        stumble="a board tipped, and the child dropped to one knee with both hands flying for balance",
        loss="The locket spun through the empty gap and vanished into the bramble-filled drop beneath",
        place_line="An old wooden bridge crossed a steep cut in the ground, but its middle was broken and open to the air.",
        severity=2,
        tags={"bridge", "height", "ranger"},
    ),
    "crumbled_wall": Hazard(
        id="crumbled_wall",
        label="crumbled wall",
        kind="height",
        shortcut="the top of a crumbled stone wall",
        warning="Those stones are loose as marbles.",
        stumble="the child landed on a wobbling stone, and the whole top edge shivered underfoot",
        loss="The locket knocked against the rock and dropped into a narrow crack too deep for small hands",
        place_line="Near the ruins stood a fallen wall with a steep drop on the far side.",
        severity=3,
        tags={"ruins", "height", "ranger"},
    ),
}

RESPONSES = {
    "throw_rope": Response(
        id="throw_rope",
        label="rope",
        kinds={"water", "height"},
        sense=3,
        power=3,
        success_text="threw a coil of rope, hooked the locket chain, and drew it back inch by inch",
        fail_text="threw a rope again and again, but the current and the dark gap were quicker",
        qa_text="used a rope to hook the locket and pull it back",
        tags={"rope"},
    ),
    "call_ranger": Response(
        id="call_ranger",
        label="ranger",
        kinds={"water", "height"},
        sense=3,
        power=4,
        success_text="called the park ranger, who came with a long grabber and careful hands",
        fail_text="called the ranger, but by the time help came the locket had already gone where nobody could reach it",
        qa_text="called the ranger for careful help",
        tags={"ranger"},
    ),
    "branch_hook": Response(
        id="branch_hook",
        label="branch",
        kinds={"water"},
        sense=2,
        power=2,
        success_text="lay flat, stretched out a forked branch, and snagged the chain before the water dragged it farther",
        fail_text="stretched out a branch, but the water knocked the locket away before it could be caught",
        qa_text="used a branch to snag the chain",
        tags={"stream", "water"},
    ),
    "grab_hand": Response(
        id="grab_hand",
        label="bare hand",
        kinds={"water", "height"},
        sense=1,
        power=1,
        success_text="leaned down and somehow caught the chain with bare fingers",
        fail_text="reached with bare hands, but it was too far and too dangerous",
        qa_text="tried to grab the locket by hand",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Ava", "Zoe", "Nora", "Maya", "Ella", "Lucy"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Eli", "Noah", "Jack", "Sam"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "boldish"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for aid, adv in ADVENTURES.items():
        for hid, hazard in HAZARDS.items():
            if hazard_supported(adv, hazard) and sensible_responses_for(hazard):
                combos.append((aid, hid))
    return combos


@dataclass
class StoryParams:
    adventure: str
    hazard: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    guide: str
    trait: str
    delay: int = 1
    hero_age: int = 6
    friend_age: int = 5
    relation: str = "friends"
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
    "locket": [(
        "What is a locket?",
        "A locket is a small piece of jewelry that opens and can hold a tiny picture or keepsake. People often treasure it because it reminds them of someone they love."
    )],
    "rope": [(
        "Why is a rope useful in an adventure?",
        "A rope lets people reach something from a safer place instead of leaning too far. It can help pull things back without getting too close to danger."
    )],
    "ranger": [(
        "What does a park ranger do?",
        "A park ranger helps look after trails and wild places. Rangers also help people stay safe when something goes wrong outside."
    )],
    "stream": [(
        "Why can a stream be dangerous to step over?",
        "Stream rocks and wet logs can be slippery, so feet can slide suddenly. Fast water can also carry small things away before you can grab them."
    )],
    "bridge": [(
        "Why is a broken bridge unsafe?",
        "A broken bridge does not give your feet a full place to land. If a board tips or ends too soon, you can stumble or drop something."
    )],
    "height": [(
        "Why should children be careful near high places?",
        "High places are tricky because loose ground and sudden slips feel bigger there. It is safer to keep back and let a grown-up help if something falls."
    )],
    "water": [(
        "Why is it hard to get a small object back from moving water?",
        "Moving water keeps pushing the object along and hiding it between rocks. Even something shiny can disappear very fast once the current catches it."
    )],
}
KNOWLEDGE_ORDER = ["locket", "rope", "ranger", "stream", "bridge", "height", "water"]


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young explorers"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adv = f["adventure_cfg"]
    hazard = f["hazard"]
    outcome = f["outcome"]
    base = (
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "locket" '
        f"and a dangerous shortcut near {hazard.label}."
    )
    if outcome == "lost":
        return [
            base,
            f"Tell a sad adventure where {hero.label} ignores {friend.label}'s warning, tries the shortcut toward {adv.goal_place}, and loses a treasured locket for good.",
            f'Write a cautionary adventure with a bad ending: the children stay safe, but the locket is lost because they chose the reckless path instead of the safe one.',
        ]
    if outcome == "recovered":
        return [
            base,
            f"Tell an adventure where {hero.label} nearly loses a treasured locket at {hazard.label}, but careful help brings it back and teaches a lesson.",
            f'Write a tense but gentle adventure where a child learns that bravery without sense is risky, and the locket is saved in the end.',
        ]
    return [
        base,
        f"Tell an adventure where {friend.label}, the older child, talks {hero.label} out of a dangerous shortcut before the locket is lost.",
        f'Write a gentle near-miss adventure where a treasured locket is kept safe because the children choose the long path instead of the reckless one.',
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    guide = f["guide"]
    adv = f["adventure_cfg"]
    hazard = f["hazard"]
    response = f["response"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, friend, relation)}, {hero.label} and {friend.label}, on an outdoor adventure with their guide. {hero.label} is wearing a treasured locket from Grandma."
        ),
        (
            "What were they trying to reach?",
            f"They were trying to reach {adv.goal_place} by following a map. That goal made the shortcut feel tempting, because they wanted to get there fast and feel brave."
        ),
        (
            f"Why did {friend.label} warn {hero.label}?",
            f"{friend.label} warned that {hazard.warning.lower()} A slip there could make the locket come loose, so the danger was not only falling but also losing something precious."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{hero.label} stopped and chose the long path instead. That choice kept the locket safe and changed the adventure from reckless to wise."
        ))
        qa.append((
            "How did the story end?",
            f"They reached {adv.goal_place} safely, and the locket was still hanging where it belonged. The ending shows that choosing the safer route still let them have an adventure."
        ))
    elif f["outcome"] == "recovered":
        qa.append((
            "What went wrong at the shortcut?",
            f"{hero.label} slipped, and the locket flew free during the stumble. The risky path turned exciting for only a moment, then became frightening very fast."
        ))
        qa.append((
            f"How was the locket saved?",
            f"{guide.label_word.capitalize()} {response.qa_text}. Careful help worked because someone used a safer method instead of leaning farther into danger."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that an adventure still needs sense, and that a shortcut is not brave if it risks something important. The locket coming back gave them a second chance to remember that lesson."
        ))
    else:
        qa.append((
            "What went wrong at the shortcut?",
            f"{hero.label} slipped, and the locket was knocked loose. Once it dropped into the dangerous place, it moved beyond what small hands could safely reach."
        ))
        qa.append((
            "Why could they not get the locket back?",
            f"{guide.label_word.capitalize()} tried to help, but the place was too dangerous or too deep by then. The bad ending came from the first careless choice, because that is what put the locket where it could be lost forever."
        ))
        qa.append((
            "How did the story end?",
            f"They walked home safely, but without the locket, and the adventure no longer felt bright. The ending proves what changed because the map was still there, yet the thing that mattered most was gone."
        ))
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"locket"} | set(f["hazard"].tags) | set(f["response"].tags)
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
        adventure="cove",
        hazard="tide_rocks",
        response="throw_rope",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        guide="guide_f",
        trait="careful",
        delay=1,
        hero_age=6,
        friend_age=5,
        relation="friends",
    ),
    StoryParams(
        adventure="ruins",
        hazard="crumbled_wall",
        response="call_ranger",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        guide="guide_m",
        trait="steady",
        delay=2,
        hero_age=7,
        friend_age=5,
        relation="siblings",
    ),
    StoryParams(
        adventure="falls",
        hazard="stream_log",
        response="branch_hook",
        hero_name="Lucy",
        hero_gender="girl",
        friend_name="Nora",
        friend_gender="girl",
        guide="guide_f",
        trait="cautious",
        delay=1,
        hero_age=5,
        friend_age=7,
        relation="siblings",
    ),
    StoryParams(
        adventure="cove",
        hazard="bridge_gap",
        response="call_ranger",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        guide="guide_m",
        trait="sensible",
        delay=0,
        hero_age=6,
        friend_age=8,
        relation="siblings",
    ),
]


def explain_rejection(adventure: Adventure, hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.label} does not fit the route in {adventure.scene}. "
        f"Pick a hazard that belongs in that adventure setting.)"
    )


def explain_response(hazard: Hazard, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try a safer response like "
            f"{', '.join(sorted(r.id for r in sensible_responses_for(hazard)))}.)"
        )
    return (
        f"(No story: response '{response.id}' does not fit hazard kind '{hazard.kind}'. "
        f"Choose a response that can reasonably help with this danger.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.friend_age, params.trait):
        return "averted"
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    return "recovered" if recovered(response, hazard, params.delay) else "lost"


ASP_RULES = r"""
valid(A, H) :- adventure(A), hazard(H), supports(A, H), has_sensible(H).

sensible_for(H, R) :- response(R), hazard_kind(H, K), handles(R, K), sense(R, S), sense_min(M), S >= M.
has_sensible(H) :- sensible_for(H, _).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

friend_older :- relation(siblings), hero_age(HA), friend_age(FA), FA > HA.
bonus(4) :- friend_older.
bonus(0) :- not friend_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- friend_older, authority(A), bravery_init(BR), A > BR.

severity(Sv + D) :- chosen_hazard(H), hazard_severity(H, Sv), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(lost) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for aid, adv in ADVENTURES.items():
        for hid in sorted(adv.hazards):
            lines.append(asp.fact("supports", aid, hid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_kind", hid, hazard.kind))
        lines.append(asp.fact("hazard_severity", hid, hazard.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for kind in sorted(response.kinds):
            lines.append(asp.fact("handles", rid, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_for(hazard_id: str) -> list[str]:
    import asp

    program = asp_program(asp.fact("chosen_hazard", hazard_id), "#show sensible_for/2.")
    model = asp.one_model(program)
    return sorted(r for (_, r) in asp.atoms(model, "sensible_for") if _ == hazard_id)


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for hid, hazard in HAZARDS.items():
        p = {r.id for r in sensible_responses_for(hazard)}
        c = set(asp_sensible_for(hid))
        if p != c:
            rc = 1
            print(f"MISMATCH in sensible responses for {hid}: clingo={sorted(c)} python={sorted(p)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure during verify for seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story or "locket" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story missing expected text.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an adventure shortcut, a treasured locket, and a lesson about careless bravery."
    )
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guide", choices=["guide_f", "guide_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much head start the loss gets before help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (adventure, hazard) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.adventure and args.hazard:
        adventure = ADVENTURES[args.adventure]
        hazard = HAZARDS[args.hazard]
        if not hazard_supported(adventure, hazard):
            raise StoryError(explain_rejection(adventure, hazard))

    if args.response and args.hazard:
        hazard = HAZARDS[args.hazard]
        response = RESPONSES[args.response]
        if hazard.kind not in response.kinds or response.sense < SENSE_MIN:
            raise StoryError(explain_response(hazard, response))

    combos = [
        combo for combo in valid_combos()
        if (args.adventure is None or combo[0] == args.adventure)
        and (args.hazard is None or combo[1] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    adventure_id, hazard_id = rng.choice(sorted(combos))
    hazard = HAZARDS[hazard_id]

    if args.response:
        response_id = args.response
        response = RESPONSES[response_id]
        if hazard.kind not in response.kinds or response.sense < SENSE_MIN:
            raise StoryError(explain_response(hazard, response))
    else:
        response_id = rng.choice(sorted(r.id for r in sensible_responses_for(hazard)))

    hero_name, hero_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=hero_name)
    guide = args.guide or rng.choice(["guide_f", "guide_m"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, friend_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        adventure=adventure_id,
        hazard=hazard_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        guide=guide,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        friend_age=friend_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.adventure not in ADVENTURES:
        raise StoryError(f"(Unknown adventure: {params.adventure})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.guide not in {"guide_f", "guide_m"}:
        raise StoryError(f"(Unknown guide: {params.guide})")

    adventure = ADVENTURES[params.adventure]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]

    if not hazard_supported(adventure, hazard):
        raise StoryError(explain_rejection(adventure, hazard))
    if response.sense < SENSE_MIN or hazard.kind not in response.kinds:
        raise StoryError(explain_response(hazard, response))

    world = tell(
        adventure=adventure,
        hazard=hazard,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        guide_type=params.guide,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        relation=params.relation,
    )

    story = world.render().replace("hero", world.get("hero").label).replace("friend", world.get("friend").label)
    story = story.replace(" guide", f" {world.get('guide').label_word}")
    story = story.replace("Guide", world.get("guide").label_word.capitalize())

    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/2.\n#show sensible_for/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (adventure, hazard) combos:\n")
        for adventure, hazard in combos:
            sensible = asp_sensible_for(hazard)
            print(f"  {adventure:8} {hazard:14} sensible responses: {', '.join(sensible)}")
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
            header = (
                f"### {p.hero_name} & {p.friend_name}: {p.adventure} / {p.hazard} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
