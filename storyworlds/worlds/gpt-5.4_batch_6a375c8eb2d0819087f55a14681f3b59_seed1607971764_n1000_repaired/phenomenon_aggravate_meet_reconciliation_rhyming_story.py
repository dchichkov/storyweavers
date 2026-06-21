#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py
====================================================================================

A standalone story world for a gentle rhyming tale about two children who plan
to meet and watch a small natural phenomenon, fall into a brief quarrel when one
child aggravates the other, and then reconcile in a concrete way.

The model is intentionally narrow. A good story here needs:
- a place that really affords the phenomenon,
- an aggravation that creates a plausible social/physical problem,
- and a reconciliation method that truly repairs that problem.

Run it
------
    python storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py --trace
    python storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py --asp
    python storyworlds/worlds/gpt-5.4/phenomenon_aggravate_meet_reconciliation_rhyming_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Place:
    id: str
    label: str
    phrase: str
    path: str
    affordances: set[str] = field(default_factory=set)
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
class Phenomenon:
    id: str
    label: str
    article: str
    sky_line: str
    wonder_line: str
    appears_at: set[str] = field(default_factory=set)
    needs_clear_view: bool = True
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
class Aggravation:
    id: str
    label: str
    harm: str
    text: str
    repair_need: str
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
class Repair:
    id: str
    label: str
    fixes: set[str] = field(default_factory=set)
    action: str = ""
    result: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return [e for e in self.entities.values() if e.role in {"starter", "friend"}]

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


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    starter = world.get("starter")
    friend = world.get("friend")
    if starter.memes["aggravating"] >= THRESHOLD and friend.memes["calm"] >= 0:
        sig = ("hurt_feelings",)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["hurt"] += 1
            friend.memes["trust"] -= 1
            starter.memes["guilt"] += 1
            world.get("phenomenon").meters["missed_togetherness"] += 1
            out.append("__hurt__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    starter = world.get("starter")
    friend = world.get("friend")
    if starter.memes["apology"] >= THRESHOLD and friend.memes["helped"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            starter.memes["guilt"] = 0.0
            starter.memes["peace"] += 1
            friend.memes["hurt"] = 0.0
            friend.memes["peace"] += 1
            friend.memes["trust"] += 1
            world.get("phenomenon").meters["shared_view"] += 1
            out.append("__peace__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def place_supports(place: Place, phenomenon: Phenomenon) -> bool:
    return phenomenon.id in place.affordances and place.id in phenomenon.appears_at


def repair_fits(aggravation: Aggravation, repair: Repair) -> bool:
    return aggravation.repair_need in repair.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for ph_id, phenomenon in PHENOMENA.items():
            if not place_supports(place, phenomenon):
                continue
            for ag_id, aggravation in AGGRAVATIONS.items():
                for rep_id, repair in REPAIRS.items():
                    if repair_fits(aggravation, repair):
                        combos.append((place_id, ph_id, ag_id, rep_id))
    return combos


def predict_reconciliation(world: World, aggravation: Aggravation, repair: Repair) -> dict:
    sim = world.copy()
    do_aggravation(sim, aggravation, narrate=False)
    do_repair(sim, repair, narrate=False)
    return {
        "peace": sim.get("friend").memes["peace"] >= THRESHOLD,
        "shared_view": sim.get("phenomenon").meters["shared_view"] >= THRESHOLD,
    }


def introduction(world: World, starter: Entity, friend: Entity, parent: Entity,
                 phenomenon: Phenomenon) -> None:
    starter.memes["joy"] += 1
    friend.memes["joy"] += 1
    starter.memes["calm"] = 1.0
    friend.memes["calm"] = 1.0
    starter.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    world.say(
        f"{starter.id} woke with a skip and a hum, for {phenomenon.article} {phenomenon.label} "
        f"might soon come. {starter.pronoun('possessive').capitalize()} {parent.label_word} had said, "
        f'"At {world.place.label}, if the light is just right, a lovely {phenomenon.label} may bloom into sight."'
    )
    world.say(
        f"So {starter.id} asked {friend.id} to meet by the {world.place.path} with a grin, "
        f"to watch that bright wonder together begin."
    )


def arrival(world: World, starter: Entity, friend: Entity, phenomenon: Phenomenon) -> None:
    world.say(
        f"They tiptoed to {world.place.phrase}, all quiet and sweet, where the breeze and the grasses "
        f"made soft rhymes to meet."
    )
    world.say(
        f'Soon {friend.id} whispered, "What a sky-swirling phenomenon this might be tonight!" '
        f"And both little faces turned eager and bright."
    )
    world.say(phenomenon.sky_line)
    world.say(phenomenon.wonder_line)


def do_aggravation(world: World, aggravation: Aggravation, narrate: bool = True) -> None:
    starter = world.get("starter")
    friend = world.get("friend")
    starter.memes["aggravating"] += 1
    if aggravation.repair_need == "dry":
        friend.meters["damp"] += 1
    elif aggravation.repair_need == "reach":
        friend.meters["blocked_view"] += 1
    elif aggravation.repair_need == "feelings":
        friend.memes["left_out"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(aggravation.text)
        world.say(
            f"{friend.id}'s smile folded small, and the glow felt less great. "
            f'"Please do not aggravate me," {friend.pronoun()} said. "I came to be your mate."'
        )


def parent_guidance(world: World, parent: Entity, repair: Repair) -> None:
    pred = predict_reconciliation(world, AGGRAVATIONS[world.facts["aggravation"].id], repair)
    world.facts["predicted_peace"] = pred["peace"]
    world.say(
        f"{parent.label_word.capitalize()} came softly and looked at the two. "
        f'"A wonder shines brighter when kindness shines too."'
    )
    if repair.id == "apologize_and_share":
        world.say(
            '"Use words that are gentle, and make a kind seat. '
            'When hearts are repaired, then eyes can both meet."'
        )
    elif repair.id == "dry_and_apologize":
        world.say(
            '"Bring over a towel, then say what is true. '
            'A sorry with helping can freshen the view."'
        )
    else:
        world.say(
            '"Take one small step back, and let your friend see. '
            'A shared little wonder feels bigger to me."'
        )


def do_repair(world: World, repair: Repair, narrate: bool = True) -> None:
    starter = world.get("starter")
    friend = world.get("friend")
    starter.memes["apology"] += 1
    friend.memes["helped"] += 1
    if "dry" in repair.fixes:
        friend.meters["damp"] = 0.0
    if "reach" in repair.fixes:
        friend.meters["blocked_view"] = 0.0
    if "feelings" in repair.fixes:
        friend.memes["left_out"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(repair.action)
        world.say(repair.result)


def ending(world: World, starter: Entity, friend: Entity, phenomenon: Phenomenon) -> None:
    shared = world.get("phenomenon").meters["shared_view"] >= THRESHOLD
    if shared:
        world.say(
            f"Then {starter.id} and {friend.id} stood shoulder to shoulder, quite neat, "
            f"and watched {phenomenon.article} {phenomenon.label} spread color complete."
        )
        world.say(
            "The quarrel blew off like a dandelion seed. "
            "They had made up with care, and that changed what they could see and need."
        )
    else:
        world.say(
            f"The {phenomenon.label} still shimmered above in the air, "
            f"but it felt thin and lonely without joy to share."
        )


def tell(place: Place, phenomenon: Phenomenon, aggravation: Aggravation, repair: Repair,
         starter_name: str = "Mina", starter_gender: str = "girl",
         friend_name: str = "Theo", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(place)
    starter = world.add(Entity(id="starter", kind="character", type=starter_gender, label=starter_name, role="starter"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    world.add(Entity(id="phenomenon", kind="thing", type="phenomenon", label=phenomenon.label, role="phenomenon"))

    starter.attrs["name"] = starter_name
    friend.attrs["name"] = friend_name
    parent.attrs["name"] = parent.label_word
    starter.memes["calm"] = 1.0
    friend.memes["calm"] = 1.0
    starter.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0
    starter.memes["aggravating"] = 0.0
    starter.memes["apology"] = 0.0
    starter.memes["guilt"] = 0.0
    starter.memes["peace"] = 0.0
    friend.memes["hurt"] = 0.0
    friend.memes["helped"] = 0.0
    friend.memes["left_out"] = 0.0
    friend.memes["peace"] = 0.0
    friend.meters["damp"] = 0.0
    friend.meters["blocked_view"] = 0.0
    world.get("phenomenon").meters["shared_view"] = 0.0
    world.get("phenomenon").meters["missed_togetherness"] = 0.0

    world.facts["aggravation"] = aggravation
    world.facts["repair"] = repair
    world.facts["place"] = place
    world.facts["phenomenon_cfg"] = phenomenon

    introduction(world, starter, friend, parent, phenomenon)
    arrival(world, starter, friend, phenomenon)

    world.para()
    do_aggravation(world, aggravation)
    parent_guidance(world, parent, repair)

    world.para()
    do_repair(world, repair)
    ending(world, starter, friend, phenomenon)

    world.facts.update(
        starter=starter,
        friend=friend,
        parent=parent,
        phenomenon=world.get("phenomenon"),
        hurt=friend.memes["hurt"] < THRESHOLD and starter.memes["aggravating"] >= THRESHOLD,
        reconciled=friend.memes["peace"] >= THRESHOLD,
        shared_view=world.get("phenomenon").meters["shared_view"] >= THRESHOLD,
    )
    return world


PLACES = {
    "hill": Place(
        id="hill",
        label="the hill",
        phrase="the hill with the windy clover",
        path="stone gate",
        affordances={"rainbow", "sunbeam_halo"},
        tags={"outdoors", "sky"},
    ),
    "pond": Place(
        id="pond",
        label="the pond",
        phrase="the pond with the cattails bending",
        path="reedy bank",
        affordances={"rainbow", "fireflies"},
        tags={"outdoors", "water"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        phrase="the garden where marigolds leaned",
        path="green gate",
        affordances={"fireflies", "sunbeam_halo"},
        tags={"outdoors", "flowers"},
    ),
}

PHENOMENA = {
    "rainbow": Phenomenon(
        id="rainbow",
        label="rainbow",
        article="a",
        sky_line="A silver rain had wandered off, and sunlight stitched the blue.",
        wonder_line="Soon a rainbow arched like ribbon thread, all fresh with drops of dew.",
        appears_at={"hill", "pond"},
        tags={"rainbow", "weather"},
    ),
    "fireflies": Phenomenon(
        id="fireflies",
        label="firefly dance",
        article="a",
        sky_line="The day grew dim, the leaves grew still, and evening brushed the ground.",
        wonder_line="Soon a firefly dance blinked gold and green with lantern-jumpy sound.",
        appears_at={"pond", "garden"},
        tags={"fireflies", "night"},
    ),
    "sunbeam_halo": Phenomenon(
        id="sunbeam_halo",
        label="sunbeam halo",
        article="a",
        sky_line="The afternoon was bright and warm, with clouds as soft as cream.",
        wonder_line="Soon a sunbeam halo floated pale inside the dusty beam.",
        appears_at={"hill", "garden"},
        tags={"sunlight", "halo"},
    ),
}

AGGRAVATIONS = {
    "splash": Aggravation(
        id="splash",
        label="a muddy splash",
        harm="damp clothes",
        text="In dashing ahead, little feet gave a splash, and speckles of water flew quick as a flash.",
        repair_need="dry",
        tags={"splash", "apology"},
    ),
    "block": Aggravation(
        id="block",
        label="a blocked view",
        harm="blocked view",
        text="In eagerness, one child climbed up on the seat and spread both small elbows so no one could meet the sight.",
        repair_need="reach",
        tags={"sharing", "space"},
    ),
    "brag": Aggravation(
        id="brag",
        label="boastful words",
        harm="hurt feelings",
        text='Then pride popped out in a braggy little spout: "I found it first, so I get the best lookout!"',
        repair_need="feelings",
        tags={"feelings", "words"},
    ),
}

REPAIRS = {
    "dry_and_apologize": Repair(
        id="dry_and_apologize",
        label="dry and apologize",
        fixes={"dry"},
        action='So a towel was fetched and a warm hand held tight. "I am sorry," said the child. "I rushed without thinking right."',
        result="They dabbed every drop till the dampness was through, and the air between them turned friendly and new.",
        qa_text="brought a towel, helped dry the splash, and said sorry",
        tags={"repair", "towel"},
    ),
    "step_back_and_share": Repair(
        id="step_back_and_share",
        label="step back and share",
        fixes={"reach"},
        action='Then one child stepped back from the very best seat. "Come stand right here beside me, so our eyes both can meet."',
        result="They made a small window with shoulder and cheek, and the wonder looked wider when neither was weak.",
        qa_text="stepped back and shared the viewing spot",
        tags={"repair", "sharing"},
    ),
    "apologize_and_share": Repair(
        id="apologize_and_share",
        label="apologize and share",
        fixes={"feelings"},
        action='The boast was pulled back with a blush and a sigh. "I am sorry," said the child. "I spoke much too high."',
        result="Then hands linked together, and the last hard frown beat a soft little retreat as their smiles came to meet.",
        qa_text="apologized for the boast and welcomed the friend close again",
        tags={"repair", "apology"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ruby", "Tess", "Nora", "Ivy", "Poppy", "Elsie"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Owen", "Jude", "Nico", "Arlo", "Bram"]

KNOWLEDGE = {
    "rainbow": [(
        "What is a rainbow?",
        "A rainbow is a band of colors that can appear when sunlight shines through tiny drops of water in the air. It looks like a bright curve in the sky."
    )],
    "fireflies": [(
        "What are fireflies?",
        "Fireflies are small insects that can glow in the dark. Their tiny lights blink on and off at dusk."
    )],
    "sunlight": [(
        "What is a sunbeam?",
        "A sunbeam is a line of sunlight shining through the air. You can often see it best when the light passes through dust or mist."
    )],
    "sharing": [(
        "Why is sharing a good way to solve a problem?",
        "Sharing gives both people a fair turn or a fair place. It helps a hard feeling soften because no one is being pushed aside."
    )],
    "apology": [(
        "What does a real apology do?",
        "A real apology says the hurt was wrong and shows you want to mend it. It works even better when you also help fix what happened."
    )],
    "towel": [(
        "What does a towel do?",
        "A towel soaks up water and helps something get dry. That is why it can help after a splash."
    )],
    "feelings": [(
        "Why can bragging hurt someone's feelings?",
        "Bragging can make another person feel small or left out. Kind words make it easier to enjoy something together."
    )],
}
KNOWLEDGE_ORDER = ["rainbow", "fireflies", "sunlight", "sharing", "apology", "towel", "feelings"]


@dataclass
class StoryParams:
    place: str
    phenomenon: str
    aggravation: str
    repair: str
    starter_name: str
    starter_gender: str
    friend_name: str
    friend_gender: str
    parent: str
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


CURATED = [
    StoryParams(
        place="hill",
        phenomenon="rainbow",
        aggravation="splash",
        repair="dry_and_apologize",
        starter_name="Mina",
        starter_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="mother",
        seed=None,
    ),
    StoryParams(
        place="pond",
        phenomenon="fireflies",
        aggravation="block",
        repair="step_back_and_share",
        starter_name="Ruby",
        starter_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        parent="father",
        seed=None,
    ),
    StoryParams(
        place="garden",
        phenomenon="sunbeam_halo",
        aggravation="brag",
        repair="apologize_and_share",
        starter_name="Nora",
        starter_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        seed=None,
    ),
]


def explain_rejection(place: Optional[Place], phenomenon: Optional[Phenomenon],
                      aggravation: Optional[Aggravation], repair: Optional[Repair]) -> str:
    if place is not None and phenomenon is not None and not place_supports(place, phenomenon):
        return (
            f"(No story: {phenomenon.article} {phenomenon.label} is not a good fit for {place.label}. "
            "Pick a place where that natural sight could really appear.)"
        )
    if aggravation is not None and repair is not None and not repair_fits(aggravation, repair):
        return (
            f"(No story: '{repair.label}' does not actually fix the problem caused by '{aggravation.label}'. "
            "Choose a repair that mends the real trouble.)"
        )
    return "(No valid combination matches the given options.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    starter = f["starter"]
    friend = f["friend"]
    phenomenon = f["phenomenon_cfg"]
    aggravation = f["aggravation"]
    repair = f["repair"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "phenomenon", "aggravate", and "meet". '
        f'The story should be about two children who plan to meet and watch {phenomenon.article} {phenomenon.label}.',
        f"Tell a gentle rhyming story where {starter.attrs['name']} and {friend.attrs['name']} go to {world.place.label}, "
        f"one child causes {aggravation.label}, and they use {repair.label} to reconcile before the ending.",
        "Write a short story in couplet-like, musical language where a natural wonder brings children together, "
        "a quarrel briefly spoils the moment, and reconciliation lets them enjoy it side by side.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    starter = f["starter"]
    friend = f["friend"]
    parent = f["parent"]
    phenomenon = f["phenomenon_cfg"]
    aggravation = f["aggravation"]
    repair = f["repair"]
    starter_name = starter.attrs["name"]
    friend_name = friend.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {starter_name} and {friend_name}, two children who planned to meet at {world.place.label} and watch {phenomenon.article} {phenomenon.label}. "
            f"{parent.label_word.capitalize()} also helped them calm down and think kindly."
        ),
        (
            "What did the children hope to see?",
            f"They hoped to see {phenomenon.article} {phenomenon.label}. "
            f"That natural wonder is what brought them to the same place in the first place."
        ),
        (
            f"How did one child aggravate the other?",
            f"One child caused {aggravation.label}, which left {friend_name} upset. "
            f"The problem changed the feeling of the moment, so the wonderful sight no longer felt easy to share."
        ),
        (
            "How did they make peace again?",
            f"They used {repair.label}: they {repair.qa_text}. "
            f"That helped fix the real trouble instead of only talking around it, so the friendship could settle again."
        ),
    ]
    if f["shared_view"]:
        qa.append((
            "How did the story end?",
            f"It ended with the children standing together and watching {phenomenon.article} {phenomenon.label}. "
            f"The last image shows that reconciliation worked, because the wonder was shared instead of spoiled."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["phenomenon_cfg"].tags) | set(world.facts["repair"].tags) | set(world.facts["aggravation"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
supports(P, Ph) :- place(P), phenomenon(Ph), affords(P, Ph), appears_at(Ph, P).
fits(A, R) :- aggravation(A), repair(R), needs(A, N), fixes(R, N).
valid(P, Ph, A, R) :- supports(P, Ph), fits(A, R).

peace_after_repair :- chosen_aggravation(A), chosen_repair(R), fits(A, R).
shared_view :- peace_after_repair.
outcome(reconciled) :- shared_view.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for ph in sorted(place.affordances):
            lines.append(asp.fact("affords", pid, ph))
    for phid, phenomenon in PHENOMENA.items():
        lines.append(asp.fact("phenomenon", phid))
        for pid in sorted(phenomenon.appears_at):
            lines.append(asp.fact("appears_at", phid, pid))
    for aid, aggravation in AGGRAVATIONS.items():
        lines.append(asp.fact("aggravation", aid))
        lines.append(asp.fact("needs", aid, aggravation.repair_need))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for need in sorted(repair.fixes):
            lines.append(asp.fact("fixes", rid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_aggravation", params.aggravation),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    return "reconciled" if repair_fits(AGGRAVATIONS[params.aggravation], REPAIRS[params.repair]) else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a natural phenomenon, a small aggravation, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--phenomenon", choices=PHENOMENA)
    ap.add_argument("--aggravation", choices=AGGRAVATIONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    phenomenon = PHENOMENA.get(args.phenomenon) if args.phenomenon else None
    aggravation = AGGRAVATIONS.get(args.aggravation) if args.aggravation else None
    repair = REPAIRS.get(args.repair) if args.repair else None

    if place is not None and phenomenon is not None and not place_supports(place, phenomenon):
        raise StoryError(explain_rejection(place, phenomenon, aggravation, repair))
    if aggravation is not None and repair is not None and not repair_fits(aggravation, repair):
        raise StoryError(explain_rejection(place, phenomenon, aggravation, repair))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.phenomenon is None or c[1] == args.phenomenon)
        and (args.aggravation is None or c[2] == args.aggravation)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, phenomenon_id, aggravation_id, repair_id = rng.choice(sorted(combos))
    starter_name, starter_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=starter_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        phenomenon=phenomenon_id,
        aggravation=aggravation_id,
        repair=repair_id,
        starter_name=starter_name,
        starter_gender=starter_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.phenomenon not in PHENOMENA:
        raise StoryError(f"(Unknown phenomenon: {params.phenomenon})")
    if params.aggravation not in AGGRAVATIONS:
        raise StoryError(f"(Unknown aggravation: {params.aggravation})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    place = PLACES[params.place]
    phenomenon = PHENOMENA[params.phenomenon]
    aggravation = AGGRAVATIONS[params.aggravation]
    repair = REPAIRS[params.repair]

    if not place_supports(place, phenomenon):
        raise StoryError(explain_rejection(place, phenomenon, aggravation, repair))
    if not repair_fits(aggravation, repair):
        raise StoryError(explain_rejection(place, phenomenon, aggravation, repair))

    world = tell(
        place=place,
        phenomenon=phenomenon,
        aggravation=aggravation,
        repair=repair,
        starter_name=params.starter_name,
        starter_gender=params.starter_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
    )

    story_text = world.render()
    starter_name = params.starter_name
    friend_name = params.friend_name
    story_text = story_text.replace("starter", starter_name).replace("friend", friend_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, phenomenon, aggravation, repair) combos:\n")
        for place, phenomenon, aggravation, repair in combos:
            print(f"  {place:8} {phenomenon:13} {aggravation:8} {repair}")
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
                f"### {p.starter_name} and {p.friend_name}: "
                f"{p.phenomenon} at {p.place} ({p.aggravation} -> {p.repair})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
