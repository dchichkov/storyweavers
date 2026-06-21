#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py
===========================================================

A standalone story world about a small mythic problem at a hilltop convention:
a young helper drinks too much fizzy nectar before a sky-ritual, a giant burp
blows out the sacred lanterns, and a group must work together to relight the
path before the moon cloud drifts away.

The world model is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate over valid (realm, drink, task) combinations
- a forward-chained rule engine for burp -> lanterns out -> darkness -> urgency
- a state-driven renderer with a beginning, turn, and proving ending image
- grounded Q&A from the simulated state, not from parsing English

Run it
------
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py --all
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py --trace --seed 42
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py --json
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py --asp
    python storyworlds/worlds/gpt-5.4/convention_burp_teamwork_myth.py --verify
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
    glowing: bool = False
    sparkling: bool = False
    fizzy: bool = False
    carries_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "goddess", "mother"}
        male = {"boy", "man", "god", "father"}
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
class Realm:
    id: str
    place: str
    opening: str
    people: str
    high_place: str
    sky_sign: str
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
class Drink:
    id: str
    label: str
    phrase: str
    fizz: int
    manner: str
    plural: bool = False
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
class Task:
    id: str
    title: str
    object_label: str
    object_phrase: str
    needs_light: bool
    fix_phrase: str
    end_line: str
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
class Aid:
    id: str
    label: str
    phrase: str
    use_text: str
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
class Response:
    id: str
    sense: int
    teamwork_need: int
    text: str
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

    def helpers(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"helper", "hero"}]

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


def _r_darkness(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "lantern" or ent.meters["out"] < THRESHOLD:
            continue
        sig = ("darkness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "path" in world.entities:
            world.get("path").meters["dark"] += 1
        for ch in world.helpers():
            ch.memes["worry"] += 1
        out.append("__dark__")
    return out


def _r_urgency(world: World) -> list[str]:
    if "path" not in world.entities:
        return []
    path = world.get("path")
    if path.meters["dark"] < THRESHOLD:
        return []
    sig = ("urgency", "path")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ch in world.helpers():
        ch.memes["resolve"] += 1
    return ["__urgency__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="darkness", tag="physical", apply=_r_darkness),
    Rule(name="urgency", tag="social", apply=_r_urgency),
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


def task_reasonable(task: Task) -> bool:
    return task.needs_light


def hazard_happens(drink: Drink, task: Task) -> bool:
    return drink.fizz > 0 and task.needs_light


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def teamwork_ready(helper_count: int, response: Response) -> bool:
    return helper_count >= response.teamwork_need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for realm_id in REALMS:
        for drink_id, drink in DRINKS.items():
            for task_id, task in TASKS.items():
                if hazard_happens(drink, task) and task_reasonable(task):
                    combos.append((realm_id, drink_id, task_id))
    return combos


def explain_rejection(drink: Drink, task: Task) -> str:
    if not task.needs_light:
        return (
            f"(No story: {task.title} does not depend on lamp-light, so a burp blowing out "
            f"lanterns would not truly block the task. Pick a task that needs light.)"
        )
    if drink.fizz <= 0:
        return (
            f"(No story: {drink.label} is not fizzy enough to cause the windy burp that turns "
            f"this little myth. Pick a fizzy festival drink.)"
        )
    return "(No story: this combination does not create the mythic problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a teamwork response like {better}.)"
    )


def predict_burp(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    lantern = sim.get("lantern")
    hero.meters["full"] += 1
    hero.meters["burp_power"] += sim.facts["drink"].fizz
    lantern.meters["out"] += 1
    propagate(sim, narrate=False)
    return {
        "dark": sim.get("path").meters["dark"] >= THRESHOLD,
        "worry": sum(ch.memes["worry"] for ch in sim.helpers()),
    }


def introduce(world: World, realm: Realm, hero: Entity, elder: Entity, task: Task) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In the age when hills still listened, {realm.opening}. On that night, "
        f"{realm.people} climbed to {realm.high_place} for the yearly convention of songs and promises."
    )
    world.say(
        f"{hero.id}, the youngest lantern-helper, walked beside {elder.id} and carried "
        f"{task.object_phrase} with both hands."
    )


def need(world: World, realm: Realm, task: Task) -> None:
    world.say(
        f"The people had gathered to {task.title}, for {realm.sky_sign} would only be seen "
        f"if the path of lanterns kept shining."
    )


def offer_drink(world: World, hero: Entity, friend: Entity, drink: Drink) -> None:
    hero.meters["full"] += 1
    hero.meters["burp_power"] += drink.fizz
    hero.memes["pleasure"] += 1
    world.say(
        f'Before the first chant began, {friend.id} handed {hero.id} {drink.phrase}. '
        f'"Drink, little keeper," {friend.pronoun()} said. "It {drink.manner}."'
    )


def warning(world: World, elder: Entity, hero: Entity, task: Task) -> None:
    pred = predict_burp(world)
    world.facts["predicted_dark"] = pred["dark"]
    world.facts["predicted_worry"] = pred["worry"]
    elder.memes["care"] += 1
    world.say(
        f'{elder.id} looked at the bright cups and then at the lantern line. '
        f'"Sip slowly," {elder.pronoun()} warned. "If the wind in your belly leaps out at the wrong moment, '
        f'the path may go dark, and {task.object_label} will be lost in shadow."'
    )


def accident(world: World, hero: Entity, task: Task) -> None:
    lantern = world.get("lantern")
    lantern.meters["out"] += 1
    lantern.glowing = False
    hero.memes["embarrassment"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the moon edged over the ridge and all grew still, {hero.id} felt the fizz rise like a tiny storm. "
        f'A great burp burst from {hero.pronoun("object")}, louder than {task.object_label} should ever hear, '
        f"and the nearest lantern went out with a little sigh."
    )


def darkness_turn(world: World, task: Task) -> None:
    if world.get("path").meters["dark"] >= THRESHOLD:
        world.say(
            f"At once the shining path broke. The stones near {task.object_label} turned dim, "
            f"and the people murmured because the work could not go on in darkness."
        )


def gather_team(world: World, hero: Entity, friend: Entity, elder: Entity, response: Response) -> None:
    for ch in (hero, friend, elder):
        ch.memes["teamwork"] += 1
    hero.memes["shame"] = 0.0
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id}'s cheeks grew hot, but {friend.id} touched {hero.pronoun('possessive')} sleeve and {elder.id} "
        f"lifted the spare flame-bowl. No one left {hero.pronoun('object')} alone with the mistake."
    )
    world.say(
        f'Together they said, "We will mend the path together," and {response.text}.'
    )


def restore(world: World, hero: Entity, friend: Entity, elder: Entity, aid: Aid, task: Task) -> None:
    lantern = world.get("lantern")
    path = world.get("path")
    lantern.meters["out"] = 0.0
    lantern.meters["lit"] += 1
    lantern.glowing = True
    path.meters["dark"] = 0.0
    for ch in (hero, friend, elder):
        ch.memes["relief"] += 1
        ch.memes["joy"] += 1
    world.say(
        f"{friend.id} used {aid.phrase}, {elder.id} steadied the old wick, and {hero.id} held both palms around the new spark "
        f"so the hill-wind could not steal it. Soon the lantern shone again."
    )
    world.say(
        f"Then {task.end_line} {realm_ending_line(world)}"
    )


def realm_ending_line(world: World) -> str:
    realm = world.facts["realm"]
    return realm.ending_image


def closing_lesson(world: World, hero: Entity, elder: Entity, task: Task, drink: Drink) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f'After the song was finished, {elder.id} smiled at {hero.id}. '
        f'"Even in a myth, small troubles come," {elder.pronoun()} said. '
        f'"What matters is this: one {burp_word()} can scatter a light, but many caring hands can call it back."'
    )
    world.say(
        f"{hero.id} nodded and set down the last drop of {drink.label}. From then on, {hero.pronoun()} drank slowly at every convention "
        f"and always looked first to the friends beside {hero.pronoun('object')}."
    )


def burp_word() -> str:
    return "burp"


def tell(
    realm: Realm,
    drink: Drink,
    task: Task,
    aid: Aid,
    response: Response,
    hero_name: str = "Ivo",
    hero_gender: str = "boy",
    friend_name: str = "Rhea",
    friend_gender: str = "girl",
    elder_name: str = "Thale",
    elder_gender: str = "woman",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="helper", label=friend_name))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="helper", label=elder_name))
    lantern = world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern", glowing=True, carries_light=True))
    path = world.add(Entity(id="path", kind="thing", type="path", label="path"))
    world.facts.update(
        realm=realm,
        drink=drink,
        task=task,
        aid=aid,
        response=response,
        helper_count=3,
    )
    world.facts["predicted_dark"] = False
    world.facts["predicted_worry"] = 0.0
    hero.meters["full"] += 0.0
    hero.meters["burp_power"] += 0.0
    lantern.meters["out"] += 0.0
    lantern.meters["lit"] += 1.0
    path.meters["dark"] += 0.0

    introduce(world, realm, hero, elder, task)
    need(world, realm, task)

    world.para()
    offer_drink(world, hero, friend, drink)
    warning(world, elder, hero, task)
    accident(world, hero, task)
    darkness_turn(world, task)

    world.para()
    gather_team(world, hero, friend, elder, response)
    restore(world, hero, friend, elder, aid, task)

    world.para()
    closing_lesson(world, hero, elder, task, drink)

    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        lantern=lantern,
        path=path,
        dark_happened=world.get("path").fired if hasattr(world.get("path"), "fired") else False,
        restored=lantern.glowing,
        teamwork_used=True,
    )
    return world


REALMS = {
    "moonhill": Realm(
        id="moonhill",
        place="Moonhill",
        opening="the silver goats of Moonhill stamped bright hoofprints in the dew",
        people="singers, keepers, and goat-herds",
        high_place="the round stone ring above Moonhill",
        sky_sign="the moon's white ladder in the sky",
        ending_image="The white road of light lay whole from the first stone to the last.",
        tags={"moon", "hill", "myth"},
    ),
    "cedarpeak": Realm(
        id="cedarpeak",
        place="Cedarpeak",
        opening="the old cedars of Cedarpeak whispered the names of patient stars",
        people="drummers, lamp-bearers, and cedar-keepers",
        high_place="the cedar court on the high peak",
        sky_sign="the star-thread between the dark branches",
        ending_image="The lantern line gleamed like a necklace laid across the mountain.",
        tags={"stars", "mountain", "myth"},
    ),
    "seacrown": Realm(
        id="seacrown",
        place="Seacrown",
        opening="the tide around Seacrown hummed against the black rocks like a sleeping harp",
        people="shell-readers, tide-watchers, and young torch-bearers",
        high_place="the sea gate above the foaming cliff",
        sky_sign="the moon-path on the sea",
        ending_image="Below them the water answered with a second silver path.",
        tags={"sea", "moon", "myth"},
    ),
}

DRINKS = {
    "spark_nectar": Drink(
        id="spark_nectar",
        label="spark nectar",
        phrase="a cup of spark nectar",
        fizz=2,
        manner="tickles like tiny bells",
        tags={"drink", "fizzy"},
    ),
    "cloud_soda": Drink(
        id="cloud_soda",
        label="cloud soda",
        phrase="a shell-cup of cloud soda",
        fizz=3,
        manner="bubbles all the way to your nose",
        tags={"drink", "fizzy"},
    ),
    "hush_tea": Drink(
        id="hush_tea",
        label="hush tea",
        phrase="a warm bowl of hush tea",
        fizz=0,
        manner="moves softly and quietly",
        tags={"drink", "calm"},
    ),
}

TASKS = {
    "moon_ribbon": Task(
        id="moon_ribbon",
        title="thread the moon ribbon through the standing stones",
        object_label="the moon ribbon",
        object_phrase="the moon ribbon spool",
        needs_light=True,
        fix_phrase="relight the lantern and guide the ribbon home",
        end_line="the moon ribbon slipped through the stones without a knot, and the gathered people cheered softly.",
        tags={"lantern", "ritual"},
    ),
    "star_tablet": Task(
        id="star_tablet",
        title="read the star tablet aloud",
        object_label="the star tablet",
        object_phrase="the flat star tablet",
        needs_light=True,
        fix_phrase="relight the lantern so the carved signs can be read",
        end_line="the star tablet shone clear enough for every carved mark to be read.",
        tags={"lantern", "reading"},
    ),
    "drum_circle": Task(
        id="drum_circle",
        title="begin the drum circle",
        object_label="the drum circle",
        object_phrase="the little hand drum",
        needs_light=False,
        fix_phrase="start the drumming anyway",
        end_line="the drums rolled over the hill without needing any lamp at all.",
        tags={"music"},
    ),
}

AIDS = {
    "glow_coal": Aid(
        id="glow_coal",
        label="glow coal",
        phrase="a glow coal from the spare bowl",
        use_text="to wake a wick",
        tags={"fire", "light"},
    ),
    "sun_mirror": Aid(
        id="sun_mirror",
        label="sun mirror",
        phrase="the small sun mirror",
        use_text="to catch a hidden gleam",
        tags={"light", "mirror"},
    ),
    "amber_twig": Aid(
        id="amber_twig",
        label="amber twig",
        phrase="an amber twig",
        use_text="to carry a safe little ember",
        tags={"fire", "light"},
    ),
}

RESPONSES = {
    "three_hands": Response(
        id="three_hands",
        sense=3,
        teamwork_need=3,
        text="they knelt by the dark lantern, one to bring a coal, one to shield the wick, and one to lift the light high again",
        qa_text="They worked in three parts: one brought the new spark, one shielded the wick, and one raised the lantern.",
        tags={"teamwork", "light"},
    ),
    "chain_of_light": Response(
        id="chain_of_light",
        sense=3,
        teamwork_need=3,
        text="they made a little chain of light from bowl to wick, passing flame carefully from hand to hand until the dark place glowed again",
        qa_text="They formed a careful chain, passing the light from one helper to the next until the lantern was lit again.",
        tags={"teamwork", "light"},
    ),
    "hero_alone": Response(
        id="hero_alone",
        sense=1,
        teamwork_need=1,
        text="the child tried to fix everything alone in a hurry",
        qa_text="The child tried to fix it alone.",
        tags={"alone"},
    ),
}

GIRL_NAMES = ["Rhea", "Mira", "Nysa", "Elia", "Tala", "Iris"]
BOY_NAMES = ["Ivo", "Lior", "Phel", "Daro", "Niko", "Orin"]
ELDER_NAMES = ["Thale", "Sera", "Myr", "Eidon", "Luma", "Beren"]


@dataclass
class StoryParams:
    realm: str
    drink: str
    task: str
    aid: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    elder_name: str
    elder_gender: str
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
    "convention": [
        (
            "What is a convention?",
            "A convention is a gathering where people come together for a shared purpose. They might sing, learn, trade ideas, or keep an old custom together."
        )
    ],
    "burp": [
        (
            "What is a burp?",
            "A burp is air coming up from your stomach through your mouth. Fizzy drinks can make burps happen more easily."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another to do one job together. A hard job can become easier when each person does one careful part."
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in the dark?",
            "A lantern makes light that helps people see where to walk or work. When a path is dark, light can keep everyone calm and safe."
        )
    ],
    "fizzy": [
        (
            "Why do fizzy drinks make your mouth feel bubbly?",
            "Fizzy drinks have tiny bubbles of gas inside them. Those bubbles can tickle your mouth and sometimes lead to a burp."
        )
    ],
}
KNOWLEDGE_ORDER = ["convention", "burp", "teamwork", "lantern", "fizzy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    realm = f["realm"]
    task = f["task"]
    drink = f["drink"]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the words "convention" and "burp".',
        f"Tell a gentle myth set at a hilltop convention in {realm.place}, where {hero.id} makes a mistake with {drink.label} and must use teamwork to save {task.object_label}.",
        f'Write a child-friendly myth where one noisy burp causes trouble during a sacred gathering, but friends work together to bring the light back.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    drink = f["drink"]
    task = f["task"]
    realm = f["realm"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young lantern-helper, along with {friend.id} and {elder.id} on {realm.place}. They gather for a yearly convention high above the world."
        ),
        (
            "What problem started the trouble?",
            f"{hero.id} drank {drink.label}, and a sudden burp blew out the nearest lantern. That made the path go dark right when the people needed light for {task.title}."
        ),
        (
            "Why was the dark lantern a big problem?",
            f"The task needed lamp-light to go on, so darkness stopped the work at an important moment. The whole gathering had to pause until the light returned."
        ),
        (
            "How did the others treat the child after the mistake?",
            f"They did not leave {hero.id} alone with the mistake. Instead, {friend.id} and {elder.id} stayed close and helped turn the trouble into a job they could share."
        ),
        (
            "How did they fix the problem?",
            f"{response.qa_text} Because they worked together instead of panicking, the lantern shone again and the task could continue."
        ),
        (
            "What changed by the end of the story?",
            f"At first, one burp broke the shining path and filled everyone with worry. By the end, the light was whole again, and {hero.id} had learned to be careful and trust the team beside {hero.pronoun('object')}."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"convention", "burp", "teamwork", "lantern"}
    if world.facts["drink"].fizz > 0:
        tags.add("fizzy")
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
        flags = [name for name, on in (
            ("glowing", e.glowing),
            ("fizzy", e.fizzy),
            ("carries_light", e.carries_light),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="moonhill",
        drink="spark_nectar",
        task="moon_ribbon",
        aid="glow_coal",
        response="three_hands",
        hero_name="Ivo",
        hero_gender="boy",
        friend_name="Rhea",
        friend_gender="girl",
        elder_name="Thale",
        elder_gender="woman",
    ),
    StoryParams(
        realm="cedarpeak",
        drink="cloud_soda",
        task="star_tablet",
        aid="sun_mirror",
        response="chain_of_light",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Orin",
        friend_gender="boy",
        elder_name="Luma",
        elder_gender="woman",
    ),
    StoryParams(
        realm="seacrown",
        drink="spark_nectar",
        task="moon_ribbon",
        aid="amber_twig",
        response="three_hands",
        hero_name="Niko",
        hero_gender="boy",
        friend_name="Iris",
        friend_gender="girl",
        elder_name="Beren",
        elder_gender="man",
    ),
]


ASP_RULES = r"""
hazard(D, T) :- drink(D), task(T), fizz(D, F), F > 0, needs_light(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Realm, D, T) :- realm(Realm), hazard(D, T).

teamwork_ready :- chosen_response(R), response_need(R, N), helper_count(H), H >= N.
outcome(fixed) :- teamwork_ready, chosen_response(R), sensible(R), chosen_task(T), needs_light(T), chosen_drink(D), fizz(D, F), F > 0.
outcome(invalid) :- not outcome(fixed).

#show valid/3.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for did, drink in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("fizz", did, drink.fizz))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        if task.needs_light:
            lines.append(asp.fact("needs_light", tid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("response_need", rid, response.teamwork_need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_drink", params.drink),
        asp.fact("chosen_response", params.response),
        asp.fact("helper_count", 3),
    ])
    model = asp.one_model(asp_program(scenario))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a hilltop convention, a noisy burp, and teamwork that brings the light back."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and not TASKS[args.task].needs_light:
        drink = DRINKS[args.drink] if args.drink else next(iter(DRINKS.values()))
        raise StoryError(explain_rejection(drink, TASKS[args.task]))
    if args.drink and args.task:
        drink = DRINKS[args.drink]
        task = TASKS[args.task]
        if not hazard_happens(drink, task):
            raise StoryError(explain_rejection(drink, task))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.drink is None or combo[1] == args.drink)
        and (args.task is None or combo[2] == args.task)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, drink, task = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS.keys()))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    elder_gender = rng.choice(["woman", "man"])
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    elder_name = rng.choice([n for n in ELDER_NAMES if n not in {hero_name, friend_name}])
    return StoryParams(
        realm=realm,
        drink=drink,
        task=task,
        aid=aid,
        response=response,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        elder_name=elder_name,
        elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.drink not in DRINKS:
        raise StoryError(f"(Unknown drink: {params.drink})")
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    drink = DRINKS[params.drink]
    task = TASKS[params.task]
    response = RESPONSES[params.response]
    if not (hazard_happens(drink, task) and task_reasonable(task)):
        raise StoryError(explain_rejection(drink, task))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not teamwork_ready(3, response):
        raise StoryError("(No story: this fix requires more helpers than the world provides.)")

    world = tell(
        realm=REALMS[params.realm],
        drink=drink,
        task=task,
        aid=AIDS[params.aid],
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        elder_name=params.elder_name,
        elder_gender=params.elder_gender,
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    for params in CURATED:
        asp_res = asp_outcome(params)
        py_res = "fixed"
        if asp_res != py_res:
            rc = 1
            print(f"MISMATCH outcome for curated case {params}: asp={asp_res} python={py_res}")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_params.seed = 0
        sample = generate(smoke_params)
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (realm, drink, task) combos:\n")
        for realm, drink, task in combos:
            print(f"  {realm:10} {drink:12} {task}")
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
            header = f"### {p.hero_name}: {p.drink} at {p.realm} for {p.task}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
