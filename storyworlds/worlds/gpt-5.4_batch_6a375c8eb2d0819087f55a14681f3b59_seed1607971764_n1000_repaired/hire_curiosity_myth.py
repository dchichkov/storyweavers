#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py
=================================================

A standalone story world in a gentle mythic style: a thirsty village chooses to
hire a guide, but the real turning point comes from a curious child who notices
a living clue in the land.

The domain is intentionally small and reasoned:
- a village has a water trouble in one mythic place
- the elders may hire only a guide who can travel that place
- the payment must be one that guide would honestly accept
- the curious child notices a clue tied to the hidden water
- if the guide listens to curiosity, the village is saved that day
- if the guide is too proud, the village loses a day, learns a lesson, and
  returns at dawn to follow the child's clue

Run it
------
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --realm sun_hill --guide goat_tracker
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --guide tide_reader --realm mist_forest
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --all
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --json
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --asp
    python storyworlds/worlds/gpt-5.4/hire_curiosity_myth.py --verify
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
CURIOSITY_NEEDS = 5
TRUST_NEEDS = 4


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
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "elder": "elder"}.get(self.type, self.type)
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
class Realm:
    id: str
    village: str
    sky: str
    approach: str
    hidden_place: str
    source_name: str
    source_phrase: str
    sign: str
    sign_detail: str
    sign_topic: str
    terrain_tags: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    title: str
    opening: str
    need: str
    loss: str
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
class Guide:
    id: str
    label: str
    phrase: str
    route_verb: str
    skill_text: str
    terrains: set[str] = field(default_factory=set)
    accepts: set[str] = field(default_factory=set)
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
class Payment:
    id: str
    phrase: str
    kind: str
    value_text: str
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
class Temperament:
    id: str
    label: str
    listens: bool
    boast: str
    turn_line: str
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


def _r_thirst(world: World) -> list[str]:
    village = world.get("village")
    source = world.get("source")
    if village.meters["thirst"] < THRESHOLD or source.meters["flowing"] >= THRESHOLD:
        return []
    sig = ("thirst",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in [e for e in world.entities.values() if e.role == "child"]:
        kid.memes["worry"] += 1
    village.memes["urgency"] += 1
    return ["__thirst__"]


def _r_notice(world: World) -> list[str]:
    child = world.get("child")
    sign = world.get("sign")
    if child.memes["curiosity"] < THRESHOLD or sign.meters["visible"] < THRESHOLD:
        return []
    sig = ("notice",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["clue_seen"] += 1
    child.memes["wonder"] += 1
    return ["__notice__"]


def _r_share(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    if child.meters["clue_seen"] < THRESHOLD or child.memes["speaks"] < THRESHOLD:
        return []
    sig = ("share",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["trust_child"] += 1
    world.facts["clue_shared"] = True
    return ["__share__"]


def _r_find(world: World) -> list[str]:
    guide = world.get("guide")
    child = world.get("child")
    elder = world.get("elder")
    source = world.get("source")
    if source.meters["flowing"] >= THRESHOLD:
        return []
    if child.meters["clue_seen"] < THRESHOLD:
        return []
    if not (guide.memes["listening"] >= THRESHOLD or elder.memes["trust_child"] >= TRUST_NEEDS):
        return []
    sig = ("find",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["found"] += 1
    source.meters["flowing"] += 1
    world.get("village").meters["thirst"] = 0.0
    child.memes["joy"] += 1
    elder.memes["relief"] += 1
    guide.memes["respect"] += 1
    return ["__found__"]


CAUSAL_RULES = [
    Rule(name="thirst", tag="physical", apply=_r_thirst),
    Rule(name="notice", tag="perception", apply=_r_notice),
    Rule(name="share", tag="social", apply=_r_share),
    Rule(name="find", tag="physical", apply=_r_find),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(s for s in produced if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def guide_fits(realm: Realm, guide: Guide) -> bool:
    return realm.id in guide.terrains


def payment_fits(guide: Guide, payment: Payment) -> bool:
    return payment.id in guide.accepts


def valid_combo(realm: Realm, guide: Guide, payment: Payment) -> bool:
    return guide_fits(realm, guide) and payment_fits(guide, payment)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for guide_id, guide in GUIDES.items():
            for payment_id, payment in PAYMENTS.items():
                if valid_combo(realm, guide, payment):
                    combos.append((realm_id, guide_id, payment_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    temper = TEMPERAMENTS[params.temperament]
    if temper.listens or params.curiosity >= CURIOSITY_NEEDS:
        return "same_day"
    return "next_dawn"


def predict_success(world: World, temperament: Temperament) -> dict:
    sim = world.copy()
    sim.get("guide").memes["listening"] = 1.0 if temperament.listens else 0.0
    sim.get("child").memes["speaks"] = 1.0
    if sim.get("child").memes["curiosity"] >= CURIOSITY_NEEDS:
        sim.get("elder").memes["trust_child"] = TRUST_NEEDS
    propagate(sim, narrate=False)
    return {
        "flowing": sim.get("source").meters["flowing"] >= THRESHOLD,
        "trust_child": sim.get("elder").memes["trust_child"],
    }


def opening(world: World, realm: Realm, trouble: Trouble, child: Entity, elder: Entity) -> None:
    world.say(
        f"In the days when hills answered prayers and springs remembered names, "
        f"the people of {realm.village} lived beneath {realm.sky}."
    )
    world.say(
        f"Then {trouble.opening} {trouble.loss} The jars in every doorway sounded hollow."
    )
    world.say(
        f"Among the villagers was {child.id}, a curious {child.type} who never stopped asking why, "
        f"and {child.pronoun('possessive')} {elder.label_word}, who kept the village keys."
    )


def village_needs_help(world: World, trouble: Trouble, elder: Entity) -> None:
    world.say(
        f'At last {elder.label_word} stood in the square and said, '
        f'"We must find {trouble.need}, or the village will have nothing to pour into its cups."'
    )


def hire_guide(world: World, guide_cfg: Guide, payment: Payment, elder: Entity) -> None:
    world.say(
        f"So the villagers chose to hire {guide_cfg.phrase} and promised {payment.phrase} in return. "
        f"{guide_cfg.skill_text}"
    )
    world.say(
        f'{elder.label_word.capitalize()} laid out the promise and asked for help. '
        f'"Lead us true, and the gift will be yours."'
    )


def set_out(world: World, realm: Realm, guide_cfg: Guide, child: Entity, guide: Entity) -> None:
    world.say(
        f"At dawn they followed {guide.label} along {realm.approach}, while {child.id} walked beside the grown-ups, "
        f"looking at everything."
    )
    world.say(
        f"{guide_cfg.boast}"
    )


def child_notices(world: World, realm: Realm, child: Entity) -> None:
    child.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} saw {realm.sign_detail} and tugged at a sleeve. "
        f'"Why would {realm.sign} be here when the ground looks thirsty?"'
    )


def guide_turn(world: World, temper: Temperament, child: Entity, elder: Entity, guide: Entity) -> None:
    guide.memes["listening"] = 1.0 if temper.listens else 0.0
    world.say(temper.turn_line.format(child=child.id, elder=elder.label_word, guide=guide.label))
    if temper.listens:
        guide.memes["respect"] += 1
    else:
        guide.memes["pride"] += 1


def child_persists(world: World, child: Entity, elder: Entity, realm: Realm) -> None:
    child.memes["speaks"] += 1
    if child.memes["curiosity"] >= CURIOSITY_NEEDS:
        elder.memes["trust_child"] = TRUST_NEEDS
    propagate(world, narrate=False)
    if elder.memes["trust_child"] >= TRUST_NEEDS:
        world.say(
            f"But {child.id} kept looking back at {realm.sign_detail}. "
            f"{elder.label_word.capitalize()} saw that {child.pronoun('possessive')} questions were not empty noise but a thread worth following."
        )
    else:
        world.say(
            f"{child.id} whispered about {realm.sign} again, but the party walked on while the light grew thin."
        )


def same_day_finding(world: World, realm: Realm, child: Entity, guide: Entity, elder: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"They turned toward {realm.sign_detail}, and soon {guide.label} pushed aside a hanging root of stone and found {realm.hidden_place}."
    )
    world.say(
        f"There, hidden in shadow, lay {realm.source_phrase}. Water leapt out with a bright sound, and every cup in the village seemed to answer from far away."
    )
    world.say(
        f'{guide.label.capitalize()} bowed to {child.id}. "A sharp pair of eyes found what my feet had missed," {guide.pronoun()} said.'
    )
    world.say(
        f"By sunset the people of {realm.village} were filling jars again, and they told one another that curiosity had walked before them like a little lamp."
    )


def next_dawn_loss(world: World, realm: Realm, child: Entity, guide: Entity) -> None:
    world.say(
        f"The party searched until sunset and found only hot stones and tired echoes. "
        f"{guide.label.capitalize()} had taken the wrong bend, and the jars of {realm.village} stayed empty for one more night."
    )
    world.say(
        f"{child.id} could not sleep. {child.pronoun().capitalize()} kept thinking of {realm.sign_detail}, which had not looked like a mistake at all."
    )


def next_dawn_finding(world: World, realm: Realm, child: Entity, elder: Entity, guide: Entity) -> None:
    guide.memes["listening"] = 1.0
    child.memes["speaks"] += 1
    elder.memes["trust_child"] = TRUST_NEEDS
    propagate(world, narrate=False)
    world.say(
        f"Before dawn, {child.id} went to {elder.label_word} and spoke plainly about {realm.sign}. "
        f"This time the grown-ups listened."
    )
    world.say(
        f"They followed the child's question back to {realm.sign_detail}, and behind a seam of rock they found {realm.source_phrase}."
    )
    world.say(
        f"The spring ran free at last. The first drink was cool as moonlight, and even {guide.label} bowed {guide.pronoun('possessive')} head in shame and thanks."
    )
    world.say(
        f"From then on, whenever the people of {realm.village} set out to solve a hard thing, they made room for the smallest question in the group."
    )
def tell(
    trouble: Trouble,
    guide_cfg: Guide,
    payment: Payment,
    temperament: Temperament,
    child_name: str,
    child_gender: str,
    elder_type: ElderType,
    curiosity: Curiosity,
    realm=None,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name, role="child"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder", role="elder"))
    guide = world.add(Entity(id="guide", kind="character", type="person", label=guide_cfg.label, role="guide"))
    village = world.add(Entity(id="village", type="village", label=realm.village))
    source = world.add(Entity(id="source", type="spring", label=realm.source_name))
    sign = world.add(Entity(id="sign", type="sign", label=realm.sign))

    child.memes["curiosity"] = float(curiosity)
    child.memes["speaks"] = 0.0
    elder.memes["trust_child"] = 1.0
    guide.memes["listening"] = 0.0
    village.meters["thirst"] = 1.0
    source.meters["flowing"] = 0.0
    sign.meters["visible"] = 1.0

    world.facts.update(
        realm=realm,
        trouble=trouble,
        guide_cfg=guide_cfg,
        payment=payment,
        temperament=temperament,
        child=child,
        elder=elder,
        guide=guide,
        village=village,
        source=source,
        sign=sign,
        clue_shared=False,
    )

    propagate(world, narrate=False)

    opening(world, realm, trouble, child, elder)
    village_needs_help(world, trouble, elder)
    world.para()
    hire_guide(world, guide_cfg, payment, elder)
    set_out(world, realm, guide_cfg, child, guide)
    world.para()
    child_notices(world, realm, child)
    guide_turn(world, temperament, child, elder, guide)
    child_persists(world, child, elder, realm)
    world.para()

    if outcome_of(
        StoryParams(
            realm=realm.id,
            trouble=trouble.id,
            guide=guide_cfg.id,
            payment=payment.id,
            temperament=temperament.id,
            child_name=child_name,
            child_gender=child_gender,
            elder_type=elder_type,
            curiosity=curiosity,
            seed=None,
        )
    ) == "same_day":
        same_day_finding(world, realm, child, guide, elder)
        outcome = "same_day"
    else:
        next_dawn_loss(world, realm, child, guide)
        world.para()
        next_dawn_finding(world, realm, child, elder, guide)
        outcome = "next_dawn"

    world.facts["outcome"] = outcome
    return world
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


REALMS = {
    "sun_hill": Realm(
        id="sun_hill",
        village="Amber Hollow",
        sky="a copper sky",
        approach="the goat paths of Sun Hill",
        hidden_place="a crack behind the lion-stone",
        source_name="the Hidden Spring",
        source_phrase="the Hidden Spring, silver and cold",
        sign="wet moss",
        sign_detail="a strip of wet moss under a dry cliff",
        sign_topic="moss",
        terrain_tags={"hill", "stone", "spring"},
    ),
    "mist_forest": Realm(
        id="mist_forest",
        village="Hazel Mere",
        sky="a pale sky tangled in mist",
        approach="the fern-dark paths of Mist Forest",
        hidden_place="a pool beneath the elder roots",
        source_name="the Root Pool",
        source_phrase="the Root Pool, still as a mirror until it stirred",
        sign="bees",
        sign_detail="a ring of bees turning over one patch of fern",
        sign_topic="bees",
        terrain_tags={"forest", "roots", "pool"},
    ),
    "shell_shore": Realm(
        id="shell_shore",
        village="Pearl Step",
        sky="a blue sky over singing waves",
        approach="the white shelves above Shell Shore",
        hidden_place="a cave where the tide forgot to close its door",
        source_name="the Sea-Cup Spring",
        source_phrase="the Sea-Cup Spring, sweet though it slept beside the sea",
        sign="an echo",
        sign_detail="a hollow echo under one shell-bright ledge",
        sign_topic="echo",
        terrain_tags={"shore", "cave", "tide"},
    ),
}

TROUBLES = {
    "dry_jars": Trouble(
        id="dry_jars",
        title="dry jars",
        opening="the village spring slipped back into the earth",
        need="the lost water",
        loss="Children tipped their cups and found only a shining drop.",
        tags={"water", "thirst"},
    ),
    "silent_channel": Trouble(
        id="silent_channel",
        title="silent channel",
        opening="the stone channel that fed the village went silent",
        need="the sleeping stream",
        loss="Garden leaves folded in on themselves, waiting for a drink.",
        tags={"water", "garden"},
    ),
}

GUIDES = {
    "goat_tracker": Guide(
        id="goat_tracker",
        label="the goat-tracker",
        phrase="a goat-tracker from the high paths",
        route_verb="climb",
        skill_text="The tracker knew how to read hoof marks and the language of stone.",
        terrains={"sun_hill", "mist_forest"},
        accepts={"bread", "bell"},
        tags={"tracker", "path"},
    ),
    "reed_reader": Guide(
        id="reed_reader",
        label="the reed-reader",
        phrase="a reed-reader from the marsh edge",
        route_verb="listen",
        skill_text="The reader could tell where hidden water slept by the bending of green stems.",
        terrains={"mist_forest", "shell_shore"},
        accepts={"song", "silver"},
        tags={"water", "reader"},
    ),
    "tide_reader": Guide(
        id="tide_reader",
        label="the tide-reader",
        phrase="a tide-reader who knew the moods of caves and coasts",
        route_verb="walk",
        skill_text="The tide-reader could hear a cave behind a wall of sound.",
        terrains={"shell_shore", "sun_hill"},
        accepts={"silver", "bell"},
        tags={"tide", "cave"},
    ),
}

PAYMENTS = {
    "bread": Payment(
        id="bread",
        phrase="three round loaves warm from the oven",
        kind="food",
        value_text="bread for the road",
        tags={"bread"},
    ),
    "silver": Payment(
        id="silver",
        phrase="a small silver ring from the village chest",
        kind="metal",
        value_text="a silver ring",
        tags={"silver"},
    ),
    "song": Payment(
        id="song",
        phrase="a whole evening of praise-songs in the square",
        kind="honor",
        value_text="songs of honor",
        tags={"song"},
    ),
    "bell": Payment(
        id="bell",
        phrase="a little bell cast with the village mark",
        kind="gift",
        value_text="a bronze bell",
        tags={"bell"},
    ),
}

TEMPERAMENTS = {
    "humble": Temperament(
        id="humble",
        label="humble",
        listens=True,
        boast='"Every path hides a second thought," the guide said. "I will listen for it."',
        turn_line='"Look closely," said {guide}. "A child who asks why may be hearing the hill better than I am."',
    ),
    "proud": Temperament(
        id="proud",
        label="proud",
        listens=False,
        boast='"No spring can hide from me," the guide said, and walked with long, certain steps.',
        turn_line='"It is only a child\'s wondering," said {guide}. Even {elder} could not turn the guide at once.',
    ),
}

GIRL_NAMES = ["Iria", "Nessa", "Luma", "Tali", "Mira", "Sena"]
BOY_NAMES = ["Orin", "Tarin", "Selo", "Pavel", "Niko", "Daren"]


KNOWLEDGE = {
    "water": [
        (
            "Why is water important to a village?",
            "People need water to drink, cook, and help plants grow. When water is hard to find, daily life becomes much harder."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that rises naturally from the ground. It can feed pools, streams, and village wells."
        )
    ],
    "moss": [
        (
            "Why can wet moss be a clue to water?",
            "Moss likes damp places. If moss stays wet when the ground around it is dry, water may be hidden nearby."
        )
    ],
    "bees": [
        (
            "Why might bees lead someone toward water?",
            "Bees need water as well as flowers. If many bees circle one spot, it can mean there is moisture close by."
        )
    ],
    "echo": [
        (
            "What can an echo tell you in a cave or on a cliff?",
            "An echo can show that there is hollow space nearby. Sometimes it hints at a hidden opening behind rock."
        )
    ],
    "tracker": [
        (
            "What does a tracker do?",
            "A tracker notices small signs and follows them carefully. Good trackers look at the ground and the world around them."
        )
    ],
    "curiosity": [
        (
            "Why can curiosity help solve problems?",
            "Curiosity makes people ask why something looks strange or different. Those questions can lead to clues others miss."
        )
    ],
    "hire": [
        (
            "What does it mean to hire someone?",
            "To hire someone means to ask them to do a job and promise payment in return. The payment might be money, food, or another agreed gift."
        )
    ],
}
KNOWLEDGE_ORDER = ["hire", "water", "spring", "moss", "bees", "echo", "tracker", "curiosity"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    realm = f["realm"]
    guide_cfg = f["guide_cfg"]
    child = f["child"]
    payment = f["payment"]
    outcome = f["outcome"]
    if outcome == "same_day":
        return [
            f'Write a short myth for a 3-to-5-year-old where a village must hire {guide_cfg.phrase} to find lost water, but a curious child notices {realm.sign} and helps save the day.',
            f'Tell a gentle mythic story set in {realm.village} where {child.id} keeps asking questions, and those questions lead the grown-ups to a hidden spring.',
            f'Write a story that includes the word "hire" and shows curiosity as a gift, with {payment.phrase} promised to a guide and a bright ending with water flowing again.',
        ]
    return [
        f'Write a short myth for a 3-to-5-year-old where a village decides to hire {guide_cfg.phrase}, but the guide is too proud to listen to a curious child at first.',
        f'Tell a mythic story set in {realm.village} where {child.id} notices {realm.sign}, the grown-ups miss the clue for one night, and then learn to listen.',
        f'Write a story that includes the word "hire" and shows that curiosity can be small in size but big in power, ending with a hidden spring found at dawn.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    guide_cfg = f["guide_cfg"]
    payment = f["payment"]
    realm = f["realm"]
    trouble = f["trouble"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious {child.type}, the village elder, and {guide_cfg.phrase}. They all set out because the village had a water problem."
        ),
        (
            "Why did the villagers decide to hire a guide?",
            f"They chose to hire the guide because {trouble.opening}. The village needed help finding water before the jars stayed empty any longer."
        ),
        (
            f"What clue did {child.id} notice?",
            f"{child.id} noticed {realm.sign_detail}. That strange little sign mattered because it pointed toward hidden water."
        ),
    ]
    if outcome == "same_day":
        qa.append(
            (
                f"How did curiosity help save {realm.village}?",
                f"{child.id}'s curiosity made {child.pronoun('object')} stop and ask why {realm.sign} was there. When the guide listened, that question led everyone to {realm.source_name} the very same day."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The hidden spring began to flow again, and the people of {realm.village} filled their jars by sunset. The ending shows that a small question can change a whole village."
            )
        )
    else:
        qa.append(
            (
                f"Why did the village have to wait until the next dawn?",
                f"The guide was too proud to listen at first, so the party followed the wrong path and lost a day. The spring was only found after the grown-ups came back and trusted {child.id}'s clue."
            )
        )
        qa.append(
            (
                "What did the villagers learn?",
                f"They learned that curiosity should not be brushed aside just because it comes from a child. Listening to {child.id}'s question finally led them to the hidden water."
            )
        )
    qa.append(
        (
            "What was promised to the guide?",
            f"The villagers promised {payment.phrase}. That is how they meant to pay the guide for the job."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    realm = f["realm"]
    guide_cfg = f["guide_cfg"]
    tags = {"hire", "water", "spring", "curiosity", realm.sign_topic}
    if "tracker" in guide_cfg.tags or guide_cfg.id == "goat_tracker":
        tags.add("tracker")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    realm: str
    trouble: str
    guide: str
    payment: str
    temperament: str
    child_name: str
    child_gender: str
    elder_type: str
    curiosity: int = 5
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        realm="sun_hill",
        trouble="dry_jars",
        guide="goat_tracker",
        payment="bread",
        temperament="humble",
        child_name="Iria",
        child_gender="girl",
        elder_type="mother",
        curiosity=5,
        seed=None,
    ),
    StoryParams(
        realm="mist_forest",
        trouble="silent_channel",
        guide="reed_reader",
        payment="silver",
        temperament="proud",
        child_name="Orin",
        child_gender="boy",
        elder_type="father",
        curiosity=3,
        seed=None,
    ),
    StoryParams(
        realm="shell_shore",
        trouble="dry_jars",
        guide="tide_reader",
        payment="bell",
        temperament="humble",
        child_name="Luma",
        child_gender="girl",
        elder_type="mother",
        curiosity=4,
        seed=None,
    ),
    StoryParams(
        realm="sun_hill",
        trouble="silent_channel",
        guide="tide_reader",
        payment="silver",
        temperament="proud",
        child_name="Tarin",
        child_gender="boy",
        elder_type="father",
        curiosity=6,
        seed=None,
    ),
    StoryParams(
        realm="mist_forest",
        trouble="dry_jars",
        guide="goat_tracker",
        payment="bell",
        temperament="proud",
        child_name="Mira",
        child_gender="girl",
        elder_type="mother",
        curiosity=2,
        seed=None,
    ),
]


def explain_rejection(realm: Realm, guide: Guide, payment: Payment) -> str:
    if not guide_fits(realm, guide):
        return (
            f"(No story: {guide.label} does not truly know the ways of {realm.id}. "
            f"Choose a guide who can travel that place.)"
        )
    if not payment_fits(guide, payment):
        return (
            f"(No story: {guide.label} would not honestly take {payment.value_text} for this work. "
            f"Choose a payment the guide would accept.)"
        )
    return "(No story: this hire arrangement does not fit the world.)"


ASP_RULES = r"""
valid(R,G,P) :- realm(R), guide(G), payment(P), fits_realm(G,R), accepts(G,P).

same_day :- chosen_temperament(T), listens(T).
same_day :- curiosity(C), curiosity_needs(N), C >= N.
next_dawn :- not same_day.

outcome(same_day) :- same_day.
outcome(next_dawn) :- next_dawn.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for gid, guide in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        for realm_id in sorted(guide.terrains):
            lines.append(asp.fact("fits_realm", gid, realm_id))
        for payment_id in sorted(guide.accepts):
            lines.append(asp.fact("accepts", gid, payment_id))
    for pid in PAYMENTS:
        lines.append(asp.fact("payment", pid))
    for tid, temper in TEMPERAMENTS.items():
        lines.append(asp.fact("temperament", tid))
        if temper.listens:
            lines.append(asp.fact("listens", tid))
    lines.append(asp.fact("curiosity_needs", CURIOSITY_NEEDS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_temperament", params.temperament),
            asp.fact("curiosity", params.curiosity),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _check_params(params: StoryParams) -> None:
    if params.realm not in REALMS:
        raise StoryError(f"(No story: unknown realm '{params.realm}')")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(No story: unknown trouble '{params.trouble}')")
    if params.guide not in GUIDES:
        raise StoryError(f"(No story: unknown guide '{params.guide}')")
    if params.payment not in PAYMENTS:
        raise StoryError(f"(No story: unknown payment '{params.payment}')")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(No story: unknown temperament '{params.temperament}')")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown child gender '{params.child_gender}')")
    if params.elder_type not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown elder type '{params.elder_type}')")
    if not (1 <= params.curiosity <= 7):
        raise StoryError("(No story: curiosity must be between 1 and 7.)")
    realm = REALMS[params.realm]
    guide = GUIDES[params.guide]
    payment = PAYMENTS[params.payment]
    if not valid_combo(realm, guide, payment):
        raise StoryError(explain_rejection(realm, guide, payment))


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

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a village hires a guide, and curiosity changes the search."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--payment", choices=PAYMENTS)
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["mother", "father"])
    ap.add_argument("--curiosity", type=int, choices=[1, 2, 3, 4, 5, 6, 7])
    ap.add_argument("--child-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible hire arrangements from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.guide and args.payment:
        realm = REALMS[args.realm]
        guide = GUIDES[args.guide]
        payment = PAYMENTS[args.payment]
        if not valid_combo(realm, guide, payment):
            raise StoryError(explain_rejection(realm, guide, payment))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.guide is None or combo[1] == args.guide)
        and (args.payment is None or combo[2] == args.payment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, guide_id, payment_id = rng.choice(sorted(combos))
    trouble = args.trouble or rng.choice(sorted(TROUBLES))
    temperament = args.temperament or rng.choice(sorted(TEMPERAMENTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["mother", "father"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    curiosity = args.curiosity if args.curiosity is not None else rng.randint(2, 6)

    return StoryParams(
        realm=realm_id,
        trouble=trouble,
        guide=guide_id,
        payment=payment_id,
        temperament=temperament,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        curiosity=curiosity,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        realm=REALMS[params.realm],
        trouble=TROUBLES[params.trouble],
        guide_cfg=GUIDES[params.guide],
        payment=PAYMENTS[params.payment],
        temperament=TEMPERAMENTS[params.temperament],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        curiosity=params.curiosity,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, guide, payment) hire arrangements:\n")
        for realm, guide, payment in combos:
            print(f"  {realm:12} {guide:12} {payment}")
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
            header = f"### {p.child_name}: {p.realm} / {p.guide} / {p.payment} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
