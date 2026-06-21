#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py
==============================================================================

A standalone storyworld for a tiny animal-story domain built from the seed
"boom, dominate, gyp" with Friendship and Rhyme.

Premise
-------
Two animal friends are making a rhyming song for a little forest gathering.
One of them is tempted to use a very loud boom-beat to dominate the show and
gyp a friend out of a verse. A careful friend warns that songs sound best when
they are shared. Depending on temperament, respect, place echo, and the chosen
repair, the story ends in one of three ways:

* shared   -- the boastful friend backs down before the big boom
* repaired -- the boom startles everyone, but an apology and a calmer method fix it
* scattered -- the crowd runs off, and the friends quietly rebuild trust later

The world model tracks physical state (booming, echo, scattered crowd) and
emotional state (pride, hurt, fear, relief, friendship). Prose is driven from
that state rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py
    python storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py --setting cave --boom thunder_barrel
    python storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py --setting meadow --boom pebble_stump
    python storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py --repair brag_solo
    python storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/boom_dominate_gyp_friendship_rhyme_animal_story.py --verify
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
PRIDE_INIT = 6.0
STEADY_TRAITS = {"steady", "kind", "patient", "thoughtful"}


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
        table = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return table[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    audience: str
    echo: int
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
class BoomThing:
    id: str
    label: str
    phrase: str
    strike: str
    sound: str
    loudness: int
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
class Repair:
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


@dataclass
class Species:
    id: str
    noun: str
    move: str
    cozy: str
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

    def friends(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]


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


def _r_startle(world: World) -> list[str]:
    stage = world.get("stage")
    crowd = world.get("crowd")
    friend = world.get("friend")
    if stage.meters["boom"] < THRESHOLD:
        return []
    sig = ("startle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.meters["fear"] += 1
    friend.memes["hurt"] += 1
    place = world.get("place")
    if place.attrs["echo"] >= 1:
        crowd.meters["fear"] += 1
        stage.meters["rumble"] += 1
    return ["__boom__"]


def _r_scatter(world: World) -> list[str]:
    crowd = world.get("crowd")
    if crowd.meters["fear"] < 2:
        return []
    sig = ("scatter",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.meters["scattered"] += 1
    for who in world.friends():
        who.memes["worry"] += 1
    return ["__scatter__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="startle", tag="social", apply=_r_startle),
    Rule(name="scatter", tag="physical", apply=_r_scatter),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(setting: Setting, boom: BoomThing) -> bool:
    return setting.echo + boom.loudness >= 2


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def performance_severity(setting: Setting, boom: BoomThing, delay: int) -> int:
    return setting.echo + boom.loudness + delay


def is_calmed(repair: Repair, setting: Setting, boom: BoomThing, delay: int) -> bool:
    return repair.power >= performance_severity(setting, boom, delay)


def initial_steadiness(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_share_now(respect: int, trait: str) -> bool:
    authority = initial_steadiness(trait) + (respect / 2.0)
    return authority > PRIDE_INIT


def _do_boom(world: World) -> None:
    stage = world.get("stage")
    stage.meters["boom"] += 1
    propagate(world, narrate=False)


def predict_noise(world: World) -> dict:
    sim = world.copy()
    _do_boom(sim)
    crowd = sim.get("crowd")
    return {
        "fear": crowd.meters["fear"],
        "scattered": crowd.meters["scattered"] >= THRESHOLD,
    }


def opening(world: World, lead: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.scene}, {lead.id} the {lead.type} and {friend.id} the "
        f"{friend.type} were best friends. They loved to make little rhymes for "
        f"{setting.audience}."
    )
    world.say(
        f"They tapped paws and toes and sang, "
        f'"Pebble, petal, moonlit chime; side by side we keep the time."'
    )


def plan_show(world: World, lead: Entity, friend: Entity, setting: Setting) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"That evening they carried their song to {setting.label}, where "
        f"{setting.audience} were waiting to listen."
    )
    world.say(
        f"{friend.id} smiled and whispered, "
        f'"Let us trade lines and make every rhyme shine."'
    )


def tempt(world: World, lead: Entity, boom: BoomThing) -> None:
    lead.memes["pride"] += 1
    world.say(
        f"Then {lead.id} spotted {boom.phrase}. {lead.pronoun('possessive').capitalize()} "
        f"eyes grew wide."
    )
    world.say(
        f'"If I strike {boom.label} and it goes {boom.sound}, boom, boom," '
        f"{lead.id} said, "
        f'"I can dominate the whole show."'
    )


def warn(world: World, friend: Entity, lead: Entity, boom: BoomThing) -> None:
    pred = predict_noise(world)
    friend.memes["care"] += 1
    world.facts["predicted_fear"] = int(pred["fear"])
    world.facts["predicted_scatter"] = bool(pred["scattered"])
    extra = ""
    if pred["scattered"]:
        extra = " The little crowd may jump and scatter."
    world.say(
        f'{friend.id} laid a paw on {boom.label} and said, '
        f'"Please do not gyp me out of my verse. A giant beat should not dominate '
        f'a friend.{extra}"'
    )
    world.say(
        f'{friend.id} added, "A rhyme sounds warmer when two friends share it."'
    )


def back_down(world: World, lead: Entity, friend: Entity, boom: BoomThing) -> None:
    lead.memes["pride"] = 0.0
    lead.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{lead.id} looked at {friend.id}, then at {boom.label}, and gave a small nod."
    )
    world.say(
        f'"You are right," {lead.id} said. "I will not dominate the song, and I '
        f'will not gyp my friend out of a turn."'
    )


def share_show(world: World, lead: Entity, friend: Entity, setting: Setting) -> None:
    lead.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    crowd = world.get("crowd")
    crowd.meters["calm"] += 1
    world.say(
        f"So they took turns. {lead.id} sang one line, {friend.id} answered with another, "
        f"and the rhythm skipped as lightly as leaves in a breeze."
    )
    world.say(
        f'Soon {setting.audience} were clapping along to their rhyme: '
        f'"Share the beat and share the shine; friendly hearts make music fine."'
    )


def defy(world: World, lead: Entity, friend: Entity, boom: BoomThing) -> None:
    lead.memes["defiance"] += 1
    world.say(
        f'But pride puffed up inside {lead.id}. "Just one mighty strike," '
        f"{lead.pronoun()} said, and lifted {boom.label}."
    )


def strike_boom(world: World, lead: Entity, boom: BoomThing) -> None:
    _do_boom(world)
    stage = world.get("stage")
    stage.meters["severity"] = float(world.facts["severity"])
    world.say(
        f"{boom.strike} {boom.sound}! The sound rolled across the stage like a round stone "
        f"bouncing through a tunnel."
    )


def shock_beat(world: World, friend: Entity, setting: Setting) -> None:
    crowd = world.get("crowd")
    if crowd.meters["scattered"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s ears drooped. The rhyme snapped apart, and {setting.audience} "
            f"fluttered and scurried away from the sudden boom."
        )
    else:
        world.say(
            f"{friend.id} gave a little start, and the waiting listeners shuffled closer "
            f"to one another."
        )


def repair_success(world: World, lead: Entity, friend: Entity, repair: Repair, setting: Setting) -> None:
    crowd = world.get("crowd")
    stage = world.get("stage")
    crowd.meters["fear"] = 0.0
    crowd.meters["scattered"] = 0.0
    crowd.meters["calm"] += 1
    stage.meters["boom"] = 0.0
    lead.memes["pride"] = 0.0
    lead.memes["sorry"] += 1
    lead.memes["friendship"] += 1
    friend.memes["hurt"] = 0.0
    friend.memes["friendship"] += 1
    world.say(
        f"{lead.id} saw {friend.id}'s face and felt a pinch in {lead.pronoun('possessive')} "
        f"heart."
    )
    world.say(
        f"{lead.id} {repair.text}."
    )
    world.say(
        f'Slowly the listeners came back, and the two friends finished together: '
        f'"Mine and thine can fall in line; shared rhyme makes the evening shine."'
    )


def repair_fail(world: World, lead: Entity, friend: Entity, repair: Repair, setting: Setting) -> None:
    lead.memes["sorry"] += 1
    lead.memes["loss"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"{lead.id} {repair.fail}."
    )
    world.say(
        f"But the crowd was already gone, and the empty stage felt much too big for one proud song."
    )


def sunset_rebuild(world: World, lead: Entity, friend: Entity, setting: Setting) -> None:
    lead.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    lead.memes["pride"] = 0.0
    world.say(
        f"At sunset, {lead.id} and {friend.id} sat together on a smooth stone beside "
        f"{setting.label}."
    )
    world.say(
        f'"I tried to dominate the music and gyp you out of your place," {lead.id} said. '
        f'"That was wrong."'
    )
    world.say(
        f"{friend.id} leaned close. Together they made one soft rhyme just for each other: "
        f'"No loud boom, no selfish climb; friends who share can mend in time."'
    )


def tell(
    setting: Setting,
    boom: BoomThing,
    repair: Repair,
    lead_name: str = "Pip",
    lead_species: str = "rabbit",
    friend_name: str = "Moss",
    friend_species: str = "mole",
    helper_trait: str = "steady",
    respect: int = 8,
    delay: int = 0,
) -> World:
    world = World()
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_species,
        role="lead",
        traits=["bright", "showy"],
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_species,
        role="friend",
        traits=[helper_trait],
        attrs={},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=setting.label,
        attrs={"echo": setting.echo},
    ))
    stage = world.add(Entity(
        id="stage",
        kind="thing",
        type="stage",
        label="the mossy stage",
        attrs={},
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="thing",
        type="crowd",
        label=setting.audience,
        attrs={},
    ))
    prop = world.add(Entity(
        id="boom",
        kind="thing",
        type="instrument",
        label=boom.label,
        attrs={"loudness": boom.loudness},
    ))

    lead.memes["pride"] = PRIDE_INIT
    friend.memes["steadiness"] = initial_steadiness(helper_trait)
    friend.memes["respect"] = float(respect)
    stage.meters["boom"] = 0.0
    crowd.meters["fear"] = 0.0
    crowd.meters["scattered"] = 0.0

    opening(world, lead, friend, setting)
    plan_show(world, lead, friend, setting)

    world.para()
    tempt(world, lead, boom)
    warn(world, friend, lead, boom)

    shared = would_share_now(respect, helper_trait)
    severity = performance_severity(setting, boom, delay)

    if shared:
        back_down(world, lead, friend, boom)
        world.para()
        share_show(world, lead, friend, setting)
        outcome = "shared"
    else:
        defy(world, lead, friend, boom)
        world.para()
        world.facts["severity"] = severity
        strike_boom(world, lead, boom)
        shock_beat(world, friend, setting)

        calmed = is_calmed(repair, setting, boom, delay)
        world.para()
        if calmed:
            repair_success(world, lead, friend, repair, setting)
            outcome = "repaired"
        else:
            repair_fail(world, lead, friend, repair, setting)
            world.para()
            sunset_rebuild(world, lead, friend, setting)
            outcome = "scattered"

    world.facts.update(
        lead=lead,
        friend=friend,
        setting=setting,
        boom_cfg=boom,
        repair=repair,
        respect=respect,
        trait=helper_trait,
        delay=delay,
        shared=(outcome == "shared"),
        outcome=outcome,
        severity=severity,
        crowd_scattered=world.get("crowd").meters["scattered"] >= THRESHOLD,
        prop=prop,
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        label="the moonlit meadow",
        scene="a moonlit meadow under silver grass",
        audience="field mice, crickets, and two sleepy lambs",
        echo=0,
        tags={"meadow"},
    ),
    "pond": Setting(
        id="pond",
        label="the lily pond bank",
        scene="the lily pond bank where reeds swayed slowly",
        audience="frogs, fireflies, and ducklings",
        echo=1,
        tags={"pond"},
    ),
    "cave": Setting(
        id="cave",
        label="the ferny cave mouth",
        scene="the ferny cave mouth at the edge of the wood",
        audience="bats, beetles, and moths",
        echo=2,
        tags={"cave", "echo"},
    ),
}

BOOMS = {
    "pebble_stump": BoomThing(
        id="pebble_stump",
        label="the pebble stump",
        phrase="a little stump ringed with pebbles",
        strike="Tap!",
        sound="bum",
        loudness=1,
        tags={"drum"},
    ),
    "hollow_log": BoomThing(
        id="hollow_log",
        label="the hollow log drum",
        phrase="a hollow log drum",
        strike="Bop!",
        sound="boom",
        loudness=2,
        tags={"drum", "boom"},
    ),
    "thunder_barrel": BoomThing(
        id="thunder_barrel",
        label="the thunder barrel",
        phrase="an old thunder barrel with tight bark skin",
        strike="THUMP!",
        sound="BOOM",
        loudness=3,
        tags={"drum", "boom"},
    ),
}

REPAIRS = {
    "soft_clap": Repair(
        id="soft_clap",
        sense=2,
        power=2,
        text="turned the loud drum on its side, whispered sorry, and asked for a soft paw-clap rhythm instead",
        fail="tried a quick sorry and a few soft claps, but the frightened crowd kept darting away",
        qa_text="turned the loud drum aside, apologized, and led a soft paw-clap rhythm",
        tags={"apology", "rhythm"},
    ),
    "sorry_duet": Repair(
        id="sorry_duet",
        sense=3,
        power=3,
        text="bowed to the crowd, said sorry to the friend, and invited a true duet with shared lines and gentle beats",
        fail="offered a duet at last, but the listeners were too startled to come back just then",
        qa_text="apologized and invited a true duet with shared lines",
        tags={"apology", "duet", "friendship"},
    ),
    "humming_circle": Repair(
        id="humming_circle",
        sense=3,
        power=4,
        text="set the drum down, hummed the tune softly, and circled close with the friend until the rhythm felt safe again",
        fail="started a humming circle, but even that could not gather the crowd back in time",
        qa_text="set the drum down and started a soft humming circle with the friend",
        tags={"apology", "duet", "humming"},
    ),
    "brag_solo": Repair(
        id="brag_solo",
        sense=1,
        power=0,
        text="kept playing alone and bragged that the biggest boom should win",
        fail="kept bragging alone, which only made the stage feel lonelier",
        qa_text="kept bragging alone",
        tags={"brag"},
    ),
}

SPECIES = {
    "rabbit": Species(id="rabbit", noun="rabbit", move="hopped", cozy="long ears", tags={"rabbit"}),
    "mole": Species(id="mole", noun="mole", move="patted", cozy="velvet paws", tags={"mole"}),
    "fox": Species(id="fox", noun="fox", move="trotted", cozy="brushy tail", tags={"fox"}),
    "otter": Species(id="otter", noun="otter", move="splashed", cozy="slick whiskers", tags={"otter"}),
    "badger": Species(id="badger", noun="badger", move="trundled", cozy="striped nose", tags={"badger"}),
    "hedgehog": Species(id="hedgehog", noun="hedgehog", move="scurried", cozy="round prickles", tags={"hedgehog"}),
}

NAMES = ["Pip", "Moss", "Fern", "Nib", "Tansy", "Wren", "Clover", "Bramble", "Dot", "Mallow"]
TRAITS = ["steady", "kind", "patient", "thoughtful", "quick", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_repairs():
        return combos
    for setting_id, setting in SETTINGS.items():
        for boom_id, boom in BOOMS.items():
            if hazard_at_risk(setting, boom):
                combos.append((setting_id, boom_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    boom: str
    repair: str
    lead_name: str
    lead_species: str
    friend_name: str
    friend_species: str
    trait: str
    respect: int = 8
    delay: int = 0
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
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have the same or almost the same ending sound, like bell and shell. Rhymes make songs and poems easier to remember.",
        )
    ],
    "friendship": [
        (
            "How can friends share a song?",
            "Friends can take turns, listen to each other, and leave room for both voices. Sharing the song helps both friends feel included.",
        )
    ],
    "drum": [
        (
            "Why can a drum sound loud?",
            "A drum is loud because the skin or wood shakes the air when you strike it. The shaking air reaches your ears as sound.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound bouncing back after it hits a wall, cave, or cliff. That is why noises can seem bigger in an echoey place.",
        )
    ],
    "apology": [
        (
            "Why does an apology help after hurt feelings?",
            "An apology shows that you understand you did something wrong and want to make it better. Kind actions after the apology help the other friend trust you again.",
        )
    ],
    "humming": [
        (
            "What is humming?",
            "Humming is making music with your mouth closed so the sound stays soft and gentle. It can calm a room because it is quiet and steady.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rhyme", "friendship", "drum", "echo", "apology", "humming"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    setting = f["setting"]
    boom = f["boom_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write an animal story for a 3-to-5-year-old that uses the words "boom," '
        f'"dominate," and "gyp," and centers on friendship and rhyme.'
    )
    if outcome == "shared":
        return [
            base,
            f"Tell a gentle story where {lead.id} the {lead.type} wants {boom.label} to dominate the show, but {friend.id} helps {lead.pronoun('object')} choose sharing instead.",
            f"Write a forest rhyme story set at {setting.label} where two friends take turns and end with a warm, friendly song.",
        ]
    if outcome == "repaired":
        return [
            base,
            f"Tell a story where {lead.id} the {lead.type} makes a loud boom at {setting.label}, hurts a friend's feelings, and then fixes the problem with an apology and a duet.",
            f"Write an animal friendship story where a showy friend tries to dominate a rhyme performance, but the ending proves that shared music is better.",
        ]
    return [
        base,
        f"Tell a bittersweet animal story where {lead.id} the {lead.type} tries to dominate a rhyme show with a boom, the crowd runs off, and friendship has to be repaired quietly afterward.",
        f"Write a story set at {setting.label} where a loud choice costs two friends their audience, but they still mend their bond by the end.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    setting = f["setting"]
    boom = f["boom_cfg"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} the {lead.type} and {friend.id} the {friend.type}, two animal friends making a rhyming song together. They wanted to perform for {setting.audience}.",
        ),
        (
            "What problem came up before the song?",
            f"{lead.id} wanted to use {boom.label} so the show would go boom and dominate the whole performance. That made {friend.id} worry about being gypped out of a verse and about the crowd getting startled.",
        ),
        (
            f"Why did {friend.id} warn {lead.id}?",
            f"{friend.id} warned {lead.id} because the loud boom could break their shared rhyme and scare the listeners. In this story, the kind friend understood that music works better when both friends have a turn.",
        ),
    ]
    if outcome == "shared":
        qa.append(
            (
                f"What changed {lead.id}'s mind?",
                f"{lead.id} listened to {friend.id}'s warning and realized that trying to dominate the song would hurt the friendship. Instead of using the big boom, {lead.pronoun().capitalize()} chose to share the lines and the beat.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the two friends taking turns and singing one happy rhyme together. The ending image proves the change because the audience clapped for both of them, not for one loud star.",
            )
        )
    elif outcome == "repaired":
        qa.append(
            (
                "What happened after the loud boom?",
                f"The boom startled the listeners and hurt {friend.id}'s feelings, so the rhyme nearly fell apart. Then {lead.id} used a calmer repair and brought the song back to a shared rhythm.",
            )
        )
        qa.append(
            (
                f"How did {lead.id} fix the problem?",
                f"{lead.id} {repair.qa_text}. That helped because the apology addressed the hurt, and the gentler rhythm showed that the song no longer had to dominate anyone.",
            )
        )
    else:
        qa.append(
            (
                "Did the crowd stay?",
                f"No. The crowd had already scattered because the big boom and the echo were too much all at once. The friends lost their audience before the repair could work.",
            )
        )
        qa.append(
            (
                "How did the friends make things better in the end?",
                f"They sat together at sunset and spoke honestly about what went wrong. Then they made one quiet rhyme just for each other, which showed their friendship mattered more than winning the show.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"rhyme", "friendship", "drum"}
    if f["setting"].echo >= 2:
        tags.add("echo")
    if f["repair"].id in {"soft_clap", "sorry_duet", "humming_circle"}:
        tags.add("apology")
    if f["repair"].id == "humming_circle":
        tags.add("humming")
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
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, int)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pond",
        boom="hollow_log",
        repair="sorry_duet",
        lead_name="Pip",
        lead_species="rabbit",
        friend_name="Moss",
        friend_species="mole",
        trait="steady",
        respect=8,
        delay=0,
    ),
    StoryParams(
        setting="pond",
        boom="thunder_barrel",
        repair="soft_clap",
        lead_name="Fern",
        lead_species="fox",
        friend_name="Dot",
        friend_species="hedgehog",
        trait="curious",
        respect=4,
        delay=0,
    ),
    StoryParams(
        setting="cave",
        boom="thunder_barrel",
        repair="soft_clap",
        lead_name="Clover",
        lead_species="otter",
        friend_name="Nib",
        friend_species="badger",
        trait="quick",
        respect=3,
        delay=1,
    ),
    StoryParams(
        setting="cave",
        boom="hollow_log",
        repair="humming_circle",
        lead_name="Mallow",
        lead_species="hedgehog",
        friend_name="Wren",
        friend_species="rabbit",
        trait="thoughtful",
        respect=5,
        delay=0,
    ),
    StoryParams(
        setting="meadow",
        boom="thunder_barrel",
        repair="sorry_duet",
        lead_name="Bramble",
        lead_species="badger",
        friend_name="Tansy",
        friend_species="otter",
        trait="kind",
        respect=7,
        delay=0,
    ),
]


def explain_rejection(setting: Setting, boom: BoomThing) -> str:
    return (
        f"(No story: {boom.label} is not big enough to make a real story-turn at "
        f"{setting.label}. Without enough boom and echo, nothing gets startled, so "
        f"there is no honest conflict to repair.)"
    )


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_share_now(params.respect, params.trait):
        return "shared"
    if is_calmed(REPAIRS[params.repair], SETTINGS[params.setting], BOOMS[params.boom], params.delay):
        return "repaired"
    return "scattered"


ASP_RULES = r"""
hazard(S,B) :- setting(S), boom(B), echo(S,E), loudness(B,L), E + L >= 2.
sensible(R) :- repair(R), sense(R,S), sense_min(M), S >= M.
valid(S,B) :- hazard(S,B).

steady_now(T) :- trait(T), is_steady(T).
init_steadiness(5) :- trait(T), steady_now(T).
init_steadiness(3) :- trait(T), not steady_now(T).
authority(C + R / 2) :- init_steadiness(C), respect(R).
share_now :- authority(A), pride_init(P), A > P.

severity(E + L + D) :- chosen_setting(S), echo(S,E), chosen_boom(B), loudness(B,L), delay(D).
repair_power(P) :- chosen_repair(R), power(R,P).
calmed :- repair_power(P), severity(V), P >= V.

outcome(shared) :- share_now.
outcome(repaired) :- not share_now, calmed.
outcome(scattered) :- not share_now, not calmed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("echo", setting_id, setting.echo))
    for boom_id, boom in BOOMS.items():
        lines.append(asp.fact("boom", boom_id))
        lines.append(asp.fact("loudness", boom_id, boom.loudness))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("pride_init", int(PRIDE_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("is_steady", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_boom", params.boom),
            asp.fact("chosen_repair", params.repair),
            asp.fact("trait", params.trait),
            asp.fact("respect", params.respect),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_repairs = set(asp_sensible_repairs())
    python_repairs = {r.id for r in sensible_repairs()}
    if clingo_repairs == python_repairs:
        print(f"OK: sensible repairs match ({sorted(clingo_repairs)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible repairs: clingo={sorted(clingo_repairs)} "
            f"python={sorted(python_repairs)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story storyworld: a boom, a rhyme, and a friendship test."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--boom", choices=BOOMS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--respect", type=int, choices=list(range(0, 11)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> str:
    choices = [n for n in NAMES if n != avoid]
    return rng.choice(choices)


def _pick_species(rng: random.Random) -> str:
    return rng.choice(sorted(SPECIES))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.boom:
        setting = SETTINGS[args.setting]
        boom = BOOMS[args.boom]
        if not hazard_at_risk(setting, boom):
            raise StoryError(explain_rejection(setting, boom))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.boom is None or combo[1] == args.boom)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, boom_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    lead_name = _pick_name(rng)
    friend_name = _pick_name(rng, avoid=lead_name)
    lead_species = _pick_species(rng)
    friend_species = _pick_species(rng)
    trait = args.trait or rng.choice(TRAITS)
    respect = args.respect if args.respect is not None else rng.randint(0, 10)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        boom=boom_id,
        repair=repair_id,
        lead_name=lead_name,
        lead_species=lead_species,
        friend_name=friend_name,
        friend_species=friend_species,
        trait=trait,
        respect=respect,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.boom not in BOOMS:
        raise StoryError(f"(Unknown boom item: {params.boom})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.lead_species not in SPECIES:
        raise StoryError(f"(Unknown lead species: {params.lead_species})")
    if params.friend_species not in SPECIES:
        raise StoryError(f"(Unknown friend species: {params.friend_species})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if not hazard_at_risk(SETTINGS[params.setting], BOOMS[params.boom]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], BOOMS[params.boom]))
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        setting=SETTINGS[params.setting],
        boom=BOOMS[params.boom],
        repair=REPAIRS[params.repair],
        lead_name=params.lead_name,
        lead_species=params.lead_species,
        friend_name=params.friend_name,
        friend_species=params.friend_species,
        helper_trait=params.trait,
        respect=params.respect,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        repairs = asp_sensible_repairs()
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(repairs)}\n")
        print(f"{len(combos)} compatible (setting, boom) combos:\n")
        for setting, boom in combos:
            print(f"  {setting:8} {boom}")
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
                f"### {p.lead_name} & {p.friend_name}: {p.setting}, {p.boom}, "
                f"{p.repair} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
