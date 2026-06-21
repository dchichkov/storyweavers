#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py
==============================================================

A standalone storyworld for a child-friendly tall tale about a runaway wheel of
cheese and the kind choice that turns trouble into help.

Premise
-------
In a braggy, bigger-than-big town, an enormous wheel of cheese breaks loose and
starts rolling toward something people care about. The child hero cannot stop
it alone. Instead of barking orders, the hero notices a hungry oversized helper
and offers the right cheese kindly. In this world, kindness is not decoration:
the helper's trust and effort depend on it, and the ending follows from that
state.

Run it
------
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py --place prairie --threat bridge --helper mouse --snack cheddar
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py --helper heron --snack pepperjack
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py --trace --seed 11
    python storyworlds/worlds/gpt-5.4/happen_cheese_kindness_tall_tale.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KINDNESS_MIN = 1


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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


@dataclass
class Place:
    id: str
    label: str
    opener: str
    sky: str
    helper_ids: set[str] = field(default_factory=set)
    roll_bonus: int = 0
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
    label: str
    article: str
    risk: int
    path: str
    fear_text: str
    safe_image: str
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
class HelperKind:
    id: str
    label: str
    phrase: str
    likes: set[str] = field(default_factory=set)
    places: set[str] = field(default_factory=set)
    power: int = 0
    method: str = ""
    finish: str = ""
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
class Snack:
    id: str
    label: str
    phrase: str
    scent: str
    kindness_line: str
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
class World:
    place: Place

    def __post_init__(self) -> None:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_rolling_danger(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    town = world.get("town")
    hero = world.get("hero")
    if wheel.meters["rolling"] >= THRESHOLD:
        sig = ("rolling_danger",)
        if sig not in world.fired:
            world.fired.add(sig)
            town.meters["danger"] += 1
            hero.memes["worry"] += 1
            out.append("__danger__")
    return out


def _r_kindness_trust(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.memes["fed"] >= THRESHOLD and helper.memes["kindness_seen"] >= THRESHOLD:
        sig = ("kindness_trust",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["trust"] += 1
            helper.memes["helpful"] += 1
            out.append("__trust__")
    return out


def _r_help_strength(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.memes["helpful"] >= THRESHOLD:
        sig = ("help_strength",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.meters["effort"] += 1
            out.append("__effort__")
    return out


CAUSAL_RULES = [
    Rule(name="rolling_danger", tag="physical", apply=_r_rolling_danger),
    Rule(name="kindness_trust", tag="social", apply=_r_kindness_trust),
    Rule(name="help_strength", tag="physical", apply=_r_help_strength),
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


PLACES = {
    "prairie": Place(
        id="prairie",
        label="the prairie",
        opener="On the prairie, the hills were so round they looked as if somebody had ironed them with the moon.",
        sky="The sky sat high and blue, and the wind had room to brag.",
        helper_ids={"mouse", "cow"},
        roll_bonus=1,
        tags={"prairie"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside",
        opener="By the riverside, the water talked all day long and the reeds nodded as if they agreed with every splash.",
        sky="Even the clouds seemed to drift downstream.",
        helper_ids={"heron", "cow"},
        roll_bonus=0,
        tags={"river"},
    ),
    "canyon": Place(
        id="canyon",
        label="the canyon",
        opener="Out by the canyon, the red walls were so tall they could have borrowed hats from the sunset.",
        sky="Every sound came back twice, just to make itself seem important.",
        helper_ids={"mouse", "heron"},
        roll_bonus=2,
        tags={"canyon"},
    ),
}

THREATS = {
    "bridge": Threat(
        id="bridge",
        label="bridge",
        article="the bridge",
        risk=2,
        path="down the lane toward the little wooden bridge",
        fear_text="If the bridge cracked, the whole town would have to hop the creek like frogs.",
        safe_image="The bridge stayed standing, neat as a comb over the creek.",
        tags={"bridge"},
    ),
    "picnic": Threat(
        id="picnic",
        label="picnic",
        article="the picnic",
        risk=1,
        path="straight toward the town picnic under the cottonwoods",
        fear_text="If it hit the picnic, biscuits, jam, and hats would all fly together in one mighty lunch storm.",
        safe_image="The picnic cloths stayed spread and the lemonade kept its manners.",
        tags={"picnic"},
    ),
    "garden": Threat(
        id="garden",
        label="garden",
        article="the school garden",
        risk=2,
        path="right for the school garden where the bean poles stood like tiny fishing masts",
        fear_text="If the garden got flattened, the children would have no giant beans to measure against their summer.",
        safe_image="The bean poles still stood straight, and not one carrot had to move house.",
        tags={"garden"},
    ),
}

HELPERS = {
    "mouse": HelperKind(
        id="mouse",
        label="mouse",
        phrase="a barn mouse as big as a wheelbarrow",
        likes={"cheddar", "swiss"},
        places={"prairie", "canyon"},
        power=3,
        method="dug in all four feet, caught the runaway wheel with both paws, and skidded a furrow long enough to plant potatoes in",
        finish="Then it sat on its haunches and nibbled politely, as if stopping giant cheese was everyday work.",
        tags={"mouse", "animal"},
    ),
    "cow": HelperKind(
        id="cow",
        label="cow",
        phrase="a kind longhorn cow with horns curved wider than porch swings",
        likes={"cheddar", "pepperjack"},
        places={"prairie", "riverside"},
        power=2,
        method="lowered its horns, met the wheel with a solid thunk, and shoved it sideways as easy as nudging a gate",
        finish="Afterward it flicked its tail and looked pleased to have helped.",
        tags={"cow", "animal"},
    ),
    "heron": HelperKind(
        id="heron",
        label="heron",
        phrase="a blue heron tall enough to peep into second-story windows",
        likes={"swiss", "pepperjack"},
        places={"riverside", "canyon"},
        power=3,
        method="spread its great wings, stepped in front of the wheel, and steered it with one careful kick into a patch of soft reeds",
        finish="When the fuss was done, it folded its wings like two blue umbrellas.",
        tags={"heron", "bird"},
    ),
}

SNACKS = {
    "cheddar": Snack(
        id="cheddar",
        label="cheddar",
        phrase="a bright cheddar wedge",
        scent="It smelled sunny and sharp.",
        kindness_line="Please have this cheddar first. A hungry helper deserves a bite before a big job.",
        tags={"cheese", "cheddar"},
    ),
    "swiss": Snack(
        id="swiss",
        label="swiss",
        phrase="a holey slice of swiss cheese",
        scent="It smelled mild and buttery.",
        kindness_line="Here is some swiss cheese. I would rather share than shout.",
        tags={"cheese", "swiss"},
    ),
    "pepperjack": Snack(
        id="pepperjack",
        label="pepperjack",
        phrase="a pepperjack piece with red specks",
        scent="It smelled warm and zippy.",
        kindness_line="Would you like this pepperjack cheese? Kind words happen faster when mouths are not growling.",
        tags={"cheese", "pepperjack"},
    ),
}

GIRL_NAMES = ["Mabel", "Daisy", "Nell", "Tess", "Lula", "Pearl"]
BOY_NAMES = ["Eli", "Jasper", "Beau", "Otis", "Cal", "Rudy"]
TRAITS = ["steady", "cheerful", "observant", "brave", "patient", "quick-thinking"]


def helper_available(place_id: str, helper_id: str) -> bool:
    return helper_id in PLACES[place_id].helper_ids and place_id in HELPERS[helper_id].places


def snack_fits(helper_id: str, snack_id: str) -> bool:
    return snack_id in HELPERS[helper_id].likes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for threat_id in THREATS:
            for helper_id in HELPERS:
                for snack_id in SNACKS:
                    if helper_available(place_id, helper_id) and snack_fits(helper_id, snack_id):
                        combos.append((place_id, threat_id, helper_id, snack_id))
    return combos


def stopping_difficulty(place: Place, threat: Threat, delay: int) -> int:
    return 1 + place.roll_bonus + threat.risk + delay


def stop_success(helper: HelperKind, delay: int, place: Place, threat: Threat) -> bool:
    base = helper.power + KINDNESS_MIN
    return base >= stopping_difficulty(place, threat, delay)


def predict_outcome(place: Place, threat: Threat, helper: HelperKind, snack: Snack, delay: int) -> dict:
    helpful = snack.id in helper.likes and helper.id in place.helper_ids
    success = helpful and stop_success(helper, delay, place, threat)
    return {
        "helpful": helpful,
        "success": success,
        "difficulty": stopping_difficulty(place, threat, delay),
    }


def introduce(world: World, hero: Entity, place: Place) -> None:
    trait = hero.traits[0] if hero.traits else "steady"
    world.say(place.opener)
    world.say(place.sky)
    world.say(
        f"In that outsized country lived {hero.id}, a {trait} little {hero.type} with a heart so roomy it could have lent space to the sky."
    )


def setup_fair(world: World, hero: Entity, threat: Threat) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"That morning the town had gathered near {threat.article}, because the dairy folk were showing off a wheel of cheese so big it needed its own shadow."
    )
    world.say(
        "People said the cheese had taken six wagons of milk, three songs, and one extra sunrise to make."
    )


def start_rolling(world: World, threat: Threat) -> None:
    wheel = world.get("wheel")
    wheel.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the giant wheel gave a wobble, slipped its chocks, and came bowling {threat.path}."
    )
    world.say(
        f'"What will happen now?" cried the townsfolk. {threat.fear_text}'
    )


def notice_helper(world: World, hero: Entity, helper_kind: HelperKind, snack: Snack) -> None:
    helper = world.get("helper")
    helper.memes["hunger"] += 1
    hero.memes["notice"] += 1
    world.say(
        f"{hero.id} spotted {helper_kind.phrase} nearby, sniffing the air at {snack.phrase}."
    )
    world.say(snack.scent)


def offer_kindness(world: World, hero: Entity, helper_kind: HelperKind, snack: Snack) -> None:
    helper = world.get("helper")
    hero.memes["kindness"] += 1
    helper.memes["kindness_seen"] += 1
    helper.memes["fed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Instead of hollering, {hero.id} held up {snack.phrase} and said, "{snack.kindness_line}"'
    )
    world.say(
        f"The big {helper_kind.label} blinked once, then twice, as if kindness was the very thing it had been hoping would happen."
    )


def rush_to_help(world: World, helper_kind: HelperKind) -> None:
    helper = world.get("helper")
    helper.meters["moving"] += 1
    world.say(
        f"With one grateful gulp and a mighty snort of courage, the {helper_kind.label} rushed after the runaway cheese."
    )


def stop_cleanly(world: World, hero: Entity, helper_kind: HelperKind, threat: Threat) -> None:
    wheel = world.get("wheel")
    town = world.get("town")
    helper = world.get("helper")
    wheel.meters["rolling"] = 0.0
    wheel.meters["stopped"] += 1
    town.meters["danger"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"It {helper_kind.method}. The huge wheel shivered, rocked once, and stopped with its rind pointed as harmless as a sleepy moon."
    )
    world.say(helper_kind.finish)
    world.say(
        f"{threat.safe_image} Folks cheered so loudly even the fence posts seemed to clap."
    )


def stop_messily(world: World, hero: Entity, helper_kind: HelperKind, threat: Threat) -> None:
    wheel = world.get("wheel")
    town = world.get("town")
    helper = world.get("helper")
    wheel.meters["rolling"] = 0.0
    wheel.meters["burst"] += 1
    town.meters["danger"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"It {helper_kind.method}, but the wheel had gathered too much downhill hurry."
    )
    world.say(
        f"The cheese popped apart in a grand yellow puff and rained crumbs everywhere except on {threat.article}."
    )
    world.say(
        f"{threat.safe_image} The townsfolk were safe, though they spent the rest of the afternoon brushing cheese out of their hats."
    )


def closing_kindness(world: World, hero: Entity, helper_kind: HelperKind, snack: Snack, outcome: str) -> None:
    hero.memes["love"] += 1
    helper = world.get("helper")
    helper.memes["belonging"] += 1
    if outcome == "clean":
        world.say(
            f"After that, the town always saved the first good bite of cheese for the {helper_kind.label}, and {hero.id} always shared the second."
        )
    else:
        world.say(
            f"After that, nobody grumbled about sweeping up cheese, because kindness had saved the day and given them a story worth retelling."
        )
    world.say(
        f"And whenever strangers asked how such a big thing could happen in such a small town, folks answered, \"Around here, a kind word can stop almost anything.\""
    )


def tell(
    *,
    place: Place,
    threat: Threat,
    helper_kind: HelperKind,
    snack: Snack,
    hero_name: str,
    hero_gender: str,
    parent_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"name": hero_name},
        tags={"hero"},
    ))
    world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
        tags={"parent"},
    ))
    wheel = world.add(Entity(
        id="wheel",
        kind="thing",
        type="cheese_wheel",
        label="the giant wheel of cheese",
        role="wheel",
        attrs={"cheese_kind": snack.label},
        tags={"cheese"},
    ))
    town = world.add(Entity(
        id="town",
        kind="thing",
        type="town",
        label="the town",
        role="town",
        attrs={},
        tags={"town"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="animal",
        label=helper_kind.label,
        role="helper",
        attrs={"favorite": sorted(helper_kind.likes)},
        tags=set(helper_kind.tags),
    ))
    world.facts.update(
        place=place,
        threat=threat,
        helper_kind=helper_kind,
        snack=snack,
        delay=delay,
        hero=hero,
        hero_name=hero_name,
        parent=world.get("parent"),
        predicted=predict_outcome(place, threat, helper_kind, snack, delay),
    )

    introduce(world, hero, place)
    setup_fair(world, hero, threat)

    world.para()
    start_rolling(world, threat)
    notice_helper(world, hero, helper_kind, snack)
    offer_kindness(world, hero, helper_kind, snack)
    rush_to_help(world, helper_kind)

    world.para()
    success = stop_success(helper_kind, delay, place, threat)
    if success:
        stop_cleanly(world, hero, helper_kind, threat)
        outcome = "clean"
    else:
        stop_messily(world, hero, helper_kind, threat)
        outcome = "messy"

    world.para()
    closing_kindness(world, hero, helper_kind, snack, outcome)
    world.facts.update(
        outcome=outcome,
        succeeded=success,
        stopped=wheel.meters["stopped"] >= THRESHOLD,
        burst=wheel.meters["burst"] >= THRESHOLD,
        kindness_used=hero.memes["kindness"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    threat: str
    helper: str
    snack: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    threat = world.facts["threat"]
    helper_kind = world.facts["helper_kind"]
    snack = world.facts["snack"]
    place = world.facts["place"]
    outcome = world.facts["outcome"]
    ending = "stops a runaway cheese wheel before it causes trouble" if outcome == "clean" else "keeps a runaway cheese wheel from hurting anyone, even though it bursts into crumbs"
    return [
        'Write a short Tall Tale for a 3-to-5-year-old that includes the words "happen" and "cheese" and shows Kindness solving a big problem.',
        f"Tell a tall tale set at {place.label} where a child named {hero.attrs['name']} kindly shares {snack.label} with {helper_kind.phrase}, who then {ending}.",
        f"Write a funny exaggerated story about a runaway wheel of cheese rolling toward {threat.article}, where kindness matters more than shouting.",
    ]


def pair_subject(hero: Entity) -> str:
    return f"{hero.attrs['name']}, a little {hero.type}"


KNOWLEDGE = {
    "cheese": [
        (
            "What is cheese?",
            "Cheese is a food made from milk. It can be soft or firm, and people slice it, melt it, or eat it in chunks.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing what someone needs and choosing to help gently. A kind choice can calm fear and make others want to help too.",
        )
    ],
    "mouse": [
        (
            "Do mice like cheese in stories?",
            "In many stories, mice are shown loving cheese very much. Real mice eat many foods, but cheese has become a famous story snack for them.",
        )
    ],
    "cow": [
        (
            "Why does a cow belong in a cheese story?",
            "Cheese comes from milk, and cows give milk. That makes cows a natural part of many farm and dairy stories.",
        )
    ],
    "heron": [
        (
            "What is a heron?",
            "A heron is a tall bird with long legs and a long neck. It often stands near water and moves carefully.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge important?",
            "A bridge helps people cross over water or a dip in the ground. If a bridge breaks, it becomes much harder to get from one side to the other.",
        )
    ],
    "picnic": [
        (
            "What is a picnic?",
            "A picnic is a meal people eat outside, often on a blanket. Families and friends bring food to share together.",
        )
    ],
    "garden": [
        (
            "Why do people care about a garden?",
            "A garden is where people grow flowers or food. It takes time and care, so people do not want it trampled or crushed.",
        )
    ],
    "prairie": [
        (
            "What is a prairie?",
            "A prairie is a wide open grassland with lots of sky. Wind can sweep across it without many trees in the way.",
        )
    ],
    "river": [
        (
            "What is a riverside?",
            "A riverside is the land beside a river. It is where water, mud, grass, and birds often meet.",
        )
    ],
    "canyon": [
        (
            "What is a canyon?",
            "A canyon is a deep place in the land with high sides of rock. Sounds can echo there because the walls throw the sound back.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "kindness",
    "cheese",
    "mouse",
    "cow",
    "heron",
    "bridge",
    "picnic",
    "garden",
    "prairie",
    "river",
    "canyon",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    threat = world.facts["threat"]
    helper_kind = world.facts["helper_kind"]
    snack = world.facts["snack"]
    place = world.facts["place"]
    predicted = world.facts["predicted"]
    outcome = world.facts["outcome"]
    name = hero.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_subject(hero)} in a tall-tale town at {place.label}. The story also features {helper_kind.phrase} and a runaway wheel of cheese.",
        ),
        (
            "What big problem happened?",
            f"A giant wheel of cheese broke loose and rolled toward {threat.article}. The townsfolk worried because {threat.fear_text.lower()}",
        ),
        (
            f"How did {name} show kindness?",
            f"{name} did not yell at the hungry {helper_kind.label}. {hero.pronoun('subject').capitalize()} offered {snack.phrase} first and spoke gently, which made the helper feel trusted and ready to help.",
        ),
    ]
    if outcome == "clean":
        qa.append(
            (
                f"How was {threat.article} saved?",
                f"The {helper_kind.label} helped after being treated kindly, and together they stopped the wheel before it hit {threat.article}. The world model predicted the helper had enough strength for the rolling danger there, so the ending stayed tidy.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when the helper tried to stop the cheese?",
                f"The helper kept anyone from getting hurt, but the wheel had too much downhill hurry and burst into crumbs. That happened because the rolling difficulty was stronger than a clean stop, even after kindness brought help.",
            )
        )
    qa.append(
        (
            "What changed by the end of the story?",
            f"At the start, the town was scared of what might happen next. At the end, the danger was gone and everyone remembered that kindness had turned a hungry bystander into a proud helper.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"kindness", "cheese"} | set(world.facts["place"].tags) | set(world.facts["threat"].tags)
    helper_id = world.facts["helper_kind"].id
    tags.add(helper_id)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="prairie",
        threat="bridge",
        helper="mouse",
        snack="cheddar",
        hero_name="Mabel",
        hero_gender="girl",
        parent="mother",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        place="riverside",
        threat="picnic",
        helper="cow",
        snack="pepperjack",
        hero_name="Jasper",
        hero_gender="boy",
        parent="father",
        trait="cheerful",
        delay=0,
    ),
    StoryParams(
        place="canyon",
        threat="garden",
        helper="heron",
        snack="swiss",
        hero_name="Tess",
        hero_gender="girl",
        parent="mother",
        trait="patient",
        delay=1,
    ),
    StoryParams(
        place="prairie",
        threat="garden",
        helper="cow",
        snack="cheddar",
        hero_name="Otis",
        hero_gender="boy",
        parent="father",
        trait="brave",
        delay=1,
    ),
    StoryParams(
        place="canyon",
        threat="bridge",
        helper="mouse",
        snack="swiss",
        hero_name="Pearl",
        hero_gender="girl",
        parent="mother",
        trait="observant",
        delay=2,
    ),
]


def explain_rejection(place_id: str, helper_id: str, snack_id: str) -> str:
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    if snack_id not in SNACKS:
        return f"(No story: unknown snack '{snack_id}'.)"
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if not helper_available(place_id, helper_id):
        return (
            f"(No story: the {HELPERS[helper_id].label} does not belong at {PLACES[place_id].label} in this world. "
            f"Pick a helper that actually appears there.)"
        )
    if not snack_fits(helper_id, snack_id):
        likes = ", ".join(sorted(HELPERS[helper_id].likes))
        return (
            f"(No story: the {HELPERS[helper_id].label} would not stop for {SNACKS[snack_id].label}. "
            f"In this world it helps for: {likes}.)"
        )
    return "(No story: this combination does not fit the world.)"


def outcome_of(params: StoryParams) -> str:
    return "clean" if stop_success(HELPERS[params.helper], params.delay, PLACES[params.place], THREATS[params.threat]) else "messy"


ASP_RULES = r"""
% --- world compatibility ---------------------------------------------------
valid(P,T,H,S) :- place(P), threat(T), helper(H), snack(S),
                  available(P,H), likes(H,S).

% --- outcome model ---------------------------------------------------------
difficulty(P,T,D,Value) :- roll_bonus(P,RB), risk(T,R), delay(D),
                           Value = 1 + RB + R + D.
strength(H,Value) :- power(H,P), kindness_min(K), Value = P + K.
clean :- chosen_place(P), chosen_threat(T), chosen_helper(H), chosen_delay(D),
         difficulty(P,T,D,V), strength(H,S), S >= V.
messy :- chosen_place(P), chosen_threat(T), chosen_helper(H), chosen_delay(D),
         difficulty(P,T,D,V), strength(H,S), S < V.
outcome(clean) :- clean.
outcome(messy) :- messy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("roll_bonus", place_id, place.roll_bonus))
        for helper_id in sorted(place.helper_ids):
            lines.append(asp.fact("available", place_id, helper_id))
    for threat_id, threat in THREATS.items():
        lines.append(asp.fact("threat", threat_id))
        lines.append(asp.fact("risk", threat_id, threat.risk))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
        for snack_id in sorted(helper.likes):
            lines.append(asp.fact("likes", helper_id, snack_id))
    for snack_id in SNACKS:
        lines.append(asp.fact("snack", snack_id))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_threat", params.threat),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a runaway cheese wheel, a giant helper, and kindness that changes the ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much extra downhill hurry the wheel gains before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.helper and not helper_available(args.place, args.helper):
        raise StoryError(explain_rejection(args.place, args.helper, args.snack or next(iter(SNACKS))))
    if args.helper and args.snack:
        place_for_msg = args.place or next(iter(PLACES))
        if not snack_fits(args.helper, args.snack):
            raise StoryError(explain_rejection(place_for_msg, args.helper, args.snack))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.threat is None or combo[1] == args.threat)
        and (args.helper is None or combo[2] == args.helper)
        and (args.snack is None or combo[3] == args.snack)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, threat_id, helper_id, snack_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        threat=threat_id,
        helper=helper_id,
        snack=snack_id,
        hero_name=hero_name,
        hero_gender=gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}').")
    if params.threat not in THREATS:
        raise StoryError(f"(No story: unknown threat '{params.threat}').")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}').")
    if params.snack not in SNACKS:
        raise StoryError(f"(No story: unknown snack '{params.snack}').")
    if not helper_available(params.place, params.helper) or not snack_fits(params.helper, params.snack):
        raise StoryError(explain_rejection(params.place, params.helper, params.snack))

    world = tell(
        place=PLACES[params.place],
        threat=THREATS[params.threat],
        helper_kind=HELPERS[params.helper],
        snack=SNACKS[params.snack],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
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
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=True, header="### smoke")
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, threat, helper, snack) combos:\n")
        for place_id, threat_id, helper_id, snack_id in combos:
            print(f"  {place_id:10} {threat_id:8} {helper_id:8} {snack_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place}, {p.threat}, {p.helper}, {p.snack} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
