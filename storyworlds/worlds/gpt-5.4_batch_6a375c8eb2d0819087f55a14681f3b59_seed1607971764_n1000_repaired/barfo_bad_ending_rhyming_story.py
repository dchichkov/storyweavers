#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barfo_bad_ending_rhyming_story.py
============================================================

A standalone storyworld for a small, child-facing rhyming tale about Barfo, a
greedy little pet monster who eats too many rich treats before a moonlit parade
and ends the night with a sore tummy and a missed celebration.

The domain is intentionally narrow and constraint-checked: not every snack makes
a reasonable cautionary story, and not every number of stolen treats causes the
bad ending this world is built to tell. The simulation tracks physical meters
(fullness, crumbs, sickness, lateness) and emotional memes (eagerness, greed,
worry, regret), then renders a short rhyming story from that state.

Run it
------
    python storyworlds/worlds/gpt-5.4/barfo_bad_ending_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/barfo_bad_ending_rhyming_story.py --snack jam_bun --count 3
    python storyworlds/worlds/gpt-5.4/barfo_bad_ending_rhyming_story.py --snack apple_slice
    python storyworlds/worlds/gpt-5.4/barfo_bad_ending_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/barfo_bad_ending_rhyming_story.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GREED_MIN = 2
SICK_FULLNESS = 4


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        monsterish = {"monster", "pet"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in monsterish:
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
class Parade:
    id: str
    title: str
    glow: str
    sound: str
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
class Snack:
    id: str
    label: str
    phrase: str
    plural: str
    rich: bool
    richness: int
    sticky: bool
    crumbs_word: str
    warning: str
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
class Stash:
    id: str
    place: str
    climb: str
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
class Comfort:
    id: str
    phrase: str
    action: str
    soothe: str
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


def _r_sick(world: World) -> list[str]:
    out: list[str] = []
    barfo = world.get("barfo")
    snack = world.facts["snack"]
    if barfo.meters["fullness"] >= SICK_FULLNESS and snack.richness >= 2:
        sig = ("sick",)
        if sig not in world.fired:
            world.fired.add(sig)
            barfo.meters["sick"] += 1
            world.get("child").memes["worry"] += 1
            out.append("__sick__")
    return out


def _r_missed(world: World) -> list[str]:
    out: list[str] = []
    barfo = world.get("barfo")
    if barfo.meters["sick"] >= THRESHOLD and world.facts["parade_started"]:
        sig = ("missed",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").meters["lateness"] += 1
            world.get("barfo").memes["regret"] += 1
            world.facts["missed_parade"] = True
            out.append("__missed__")
    return out


CAUSAL_RULES = [
    Rule(name="sick", tag="physical", apply=_r_sick),
    Rule(name="missed", tag="social", apply=_r_missed),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def bad_combo(snack: Snack, count: int) -> bool:
    return snack.rich and count >= GREED_MIN


def severity_of(snack: Snack, count: int) -> int:
    return snack.richness + count


def ending_of(snack: Snack, count: int) -> str:
    return "missed_and_messy" if severity_of(snack, count) >= 6 else "missed_and_sad"


def predict_tummy(world: World, snack: Snack, count: int) -> dict:
    sim = world.copy()
    sim.facts["snack"] = snack
    sim.facts["count"] = count
    sim.get("barfo").meters["fullness"] += count * snack.richness
    sim.get("barfo").meters["crumbs"] += 1
    propagate(sim, narrate=False)
    sim.facts["parade_started"] = True
    propagate(sim, narrate=False)
    return {
        "sick": sim.get("barfo").meters["sick"] >= THRESHOLD,
        "missed": bool(sim.facts.get("missed_parade")),
        "severity": severity_of(snack, count),
    }


def opening(world: World, child: Entity, barfo: Entity, parade: Parade) -> None:
    child.memes["eagerness"] += 1
    barfo.memes["eagerness"] += 1
    world.say(
        f"{child.id} brushed a lantern till it made a silver show, "
        f"and barfo bounced beside {child.pronoun('object')} with toes all set to go."
    )
    world.say(
        f"Tonight was {parade.title}, with {parade.glow} in a row; "
        f"the lane would ring with {parade.sound}, all soft and bright below."
    )


def setup_treats(world: World, child: Entity, snack: Snack, stash: Stash) -> None:
    world.say(
        f"On {stash.place} sat {snack.phrase}, still warm with sugared steam; "
        f"they waited for the walk to start, like snacks inside a dream."
    )
    world.say(
        f'"Not yet," said {child.id}. "{snack.warning} '
        f'We march first, then we munch, and home will smell just so."'
    )


def temptation(world: World, child: Entity, barfo: Entity, snack: Snack, stash: Stash, count: int) -> None:
    pred = predict_tummy(world, snack, count)
    world.facts["predicted_sick"] = pred["sick"]
    world.facts["predicted_missed"] = pred["missed"]
    world.facts["predicted_severity"] = pred["severity"]
    barfo.memes["greed"] += 1
    world.say(
        f"But Barfo watched the tray and licked the sugar from the air; "
        f"{stash.climb}, and soon his paws were sneaking over there."
    )
    world.say(
        f'{child.id} frowned. "Please wait for me. Too many will not be fair." '
        f'But greed can make a noisy drum that drowns a careful prayer.'
    )


def steal_and_gobble(world: World, barfo: Entity, snack: Snack, count: int) -> None:
    barfo.meters["fullness"] += count * snack.richness
    barfo.meters["crumbs"] += 1
    if snack.sticky:
        barfo.meters["sticky"] += 1
    propagate(world, narrate=False)
    world.say(
        f"He gobbled {count} {snack.plural} quick — gulp-gulp, puff, and poof — "
        f"till {snack.crumbs_word} dotted chin and chest and even one ear's roof."
    )
    if barfo.meters["sick"] >= THRESHOLD:
        world.say(
            "At first he gave a pleased small hum and strutted very tall; "
            "then deep inside his round little belly came a grumble, low and small."
        )


def parade_begins(world: World, parade: Parade) -> None:
    world.facts["parade_started"] = True
    propagate(world, narrate=False)
    world.say(
        f"Outside, the first bright lanterns bobbed and painted gold on stone; "
        f"{parade.sound.capitalize()} drifted down the lane, inviting everyone."
    )


def tummy_turn(world: World, child: Entity, barfo: Entity) -> None:
    barfo.memes["regret"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Barfo tried to hop toward the door, but folded with a groan; "
        f"he clutched his middle, pale and still, and would not walk alone."
    )
    world.say(
        f'{child.id} set the lantern down and rubbed his back with care. '
        f'"Oh, Barfo, now the march is starting, and we are stranded here."'
    )


def comfort_scene(world: World, child: Entity, comfort: Comfort) -> None:
    world.say(
        f"{child.id} brought {comfort.phrase} and {comfort.action}; "
        f"it helped a little with the ache, but not enough to go."
    )
    world.say(comfort.soothe)


def bad_ending_scene(world: World, child: Entity, barfo: Entity, parade: Parade, snack: Snack, ending: str) -> None:
    if ending == "missed_and_messy":
        world.say(
            f"While {child.id} wiped {snack.crumbs_word} from Barfo's furry jaw, "
            f"the lantern's candle tipped and drew a waxy, crooked flaw."
        )
        world.say(
            f"So {parade.title} passed without them, and the lantern looked all wrong; "
            f"the house stayed dim, the tray stayed bare, and silence took the song."
        )
    else:
        world.say(
            f"So {parade.title} passed the gate without one Barfo cheer; "
            f"its glow went sliding down the road, while he stayed moaning here."
        )
        world.say(
            "No marching feet, no moonlit treat, no proud and twinkly tread — "
            "just crumbs, a cooling window tray, and one small sorrow bed."
        )


def closing_image(world: World, child: Entity, barfo: Entity) -> None:
    child.memes["sadness"] += 1
    world.say(
        f"At last Barfo slept, still sorry, with a blanket to his chin; "
        f"{child.id} watched the moon climb past the glass and wished they had not given in."
    )


def tell(
    parade: Parade,
    snack: Snack,
    stash: Stash,
    comfort: Comfort,
    count: int,
    child_name: str = "Mina",
    child_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    barfo = world.add(Entity(id="Barfo", kind="character", type="monster", role="pet", label="barfo"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))

    world.facts["parade"] = parade
    world.facts["snack"] = snack
    world.facts["stash"] = stash
    world.facts["comfort"] = comfort
    world.facts["count"] = count
    world.facts["parade_started"] = False
    world.facts["missed_parade"] = False
    world.facts["ending"] = ending_of(snack, count)

    opening(world, child, barfo, parade)
    setup_treats(world, child, snack, stash)

    world.para()
    temptation(world, child, barfo, snack, stash, count)
    steal_and_gobble(world, barfo, snack, count)

    world.para()
    parade_begins(world, parade)
    if barfo.meters["sick"] >= THRESHOLD:
        tummy_turn(world, child, barfo)
        comfort_scene(world, child, comfort)
        world.para()
        bad_ending_scene(world, child, barfo, parade, snack, world.facts["ending"])
        closing_image(world, child, barfo)

    world.facts.update(
        child=child,
        barfo=barfo,
        parent=parent,
        sick=barfo.meters["sick"] >= THRESHOLD,
        fullness=barfo.meters["fullness"],
        sticky=barfo.meters["sticky"] >= THRESHOLD,
        crumbs=barfo.meters["crumbs"] >= THRESHOLD,
        missed=bool(world.facts.get("missed_parade")),
    )
    return world


PARADES = {
    "moonwalk": Parade(
        id="moonwalk",
        title="the Moon Ribbon Walk",
        glow="paper moons and ribbon lights",
        sound="tin bells and humming feet",
        tags={"moon", "parade"},
    ),
    "firefly": Parade(
        id="firefly",
        title="the Firefly Line",
        glow="jar-lights blinking green and gold",
        sound="soft pipes and slipper steps",
        tags={"firefly", "parade"},
    ),
    "starlane": Parade(
        id="starlane",
        title="the Star Lane March",
        glow="star lamps swinging blue and white",
        sound="drums tapped low and slow",
        tags={"stars", "parade"},
    ),
}

SNACKS = {
    "jam_bun": Snack(
        id="jam_bun",
        label="jam bun",
        phrase="a plate of jam buns",
        plural="jam buns",
        rich=True,
        richness=2,
        sticky=True,
        crumbs_word="sticky red smears",
        warning="Those buns are rich and sweet.",
        tags={"jam", "sweet", "tummy"},
    ),
    "cream_puff": Snack(
        id="cream_puff",
        label="cream puff",
        phrase="a dish of cream puffs",
        plural="cream puffs",
        rich=True,
        richness=2,
        sticky=False,
        crumbs_word="powdery crumbs",
        warning="Those puffs are rich and airy.",
        tags={"cream", "sweet", "tummy"},
    ),
    "honey_cake": Snack(
        id="honey_cake",
        label="honey cake",
        phrase="a stack of honey cakes",
        plural="honey cakes",
        rich=True,
        richness=3,
        sticky=True,
        crumbs_word="honey crumbs",
        warning="Those cakes are heavy and sweet.",
        tags={"honey", "sweet", "tummy"},
    ),
    "apple_slice": Snack(
        id="apple_slice",
        label="apple slice",
        phrase="a bowl of apple slices",
        plural="apple slices",
        rich=False,
        richness=1,
        sticky=False,
        crumbs_word="pale peels",
        warning="Those slices are for sharing later.",
        tags={"apple"},
    ),
}

STASHES = {
    "windowsill": Stash(
        id="windowsill",
        place="the cool windowsill",
        climb="He dragged a stool beneath the sill",
        tags={"window"},
    ),
    "pantry_step": Stash(
        id="pantry_step",
        place="the pantry step",
        climb="He padded to the pantry shelf",
        tags={"pantry"},
    ),
    "porch_box": Stash(
        id="porch_box",
        place="the porch cake box",
        climb="He nudged the porch box with his nose",
        tags={"porch"},
    ),
}

COMFORTS = {
    "mint_tea": Comfort(
        id="mint_tea",
        phrase="warm mint tea",
        action="sat beside him on the rug",
        soothe="The steam rose kind and curly, but the ache still made him slow.",
        tags={"tea", "care"},
    ),
    "cool_cloth": Comfort(
        id="cool_cloth",
        phrase="a cool cloth",
        action="held it softly to his head",
        soothe="The cloth felt nice and gentle, but his middle hurt below.",
        tags={"care"},
    ),
    "blanket": Comfort(
        id="blanket",
        phrase="a soft blanket",
        action="tucked it round him by the chair",
        soothe="The blanket made him cozy, but it could not cure the ache.",
        tags={"care", "blanket"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ruby", "Ivy", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Toby", "Noah", "Eli", "Jude", "Theo"]
TRAITS = ["careful", "gentle", "hopeful", "patient"]


@dataclass
class StoryParams:
    parade: str
    snack: str
    stash: str
    comfort: str
    count: int
    child_name: str
    child_type: str
    parent_type: str
    trait: str = "careful"
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
    "tummy": [
        (
            "Why can eating too many rich sweets make your tummy hurt?",
            "Rich sweets can be heavy, and eating too many at once can upset your stomach. Your body needs time to handle food, especially when it is very sugary.",
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a line of people moving together, often with music, lights, or costumes. People watch or join as it goes down a street or path.",
        )
    ],
    "mint_tea": [
        (
            "What can warm tea do when someone feels a little sick?",
            "Warm tea can feel soothing and gentle on the body. It may help someone feel calmer, though it cannot fix every tummy ache right away.",
        )
    ],
    "blanket": [
        (
            "Why does a blanket help when someone feels bad?",
            "A blanket can help a person feel warm, safe, and rested. Comfort can make being sick easier, even when the problem still needs time to pass.",
        )
    ],
    "apple": [
        (
            "Are apple slices the same as rich cakes and buns?",
            "No. Apple slices are fruit and are usually lighter than heavy cakes full of sugar and cream. Different foods can affect your body in different ways.",
        )
    ],
    "care": [
        (
            "What should you do when a friend or pet feels sick?",
            "Stay with them, speak gently, and get a grown-up if needed. Comfort and help matter more than games when someone does not feel well.",
        )
    ],
}
KNOWLEDGE_ORDER = ["tummy", "parade", "mint_tea", "blanket", "apple", "care"]


CURATED = [
    StoryParams(
        parade="moonwalk",
        snack="jam_bun",
        stash="windowsill",
        comfort="mint_tea",
        count=3,
        child_name="Mina",
        child_type="girl",
        parent_type="mother",
        trait="careful",
    ),
    StoryParams(
        parade="firefly",
        snack="cream_puff",
        stash="pantry_step",
        comfort="cool_cloth",
        count=2,
        child_name="Owen",
        child_type="boy",
        parent_type="father",
        trait="gentle",
    ),
    StoryParams(
        parade="starlane",
        snack="honey_cake",
        stash="porch_box",
        comfort="blanket",
        count=2,
        child_name="Ruby",
        child_type="girl",
        parent_type="mother",
        trait="patient",
    ),
    StoryParams(
        parade="moonwalk",
        snack="honey_cake",
        stash="pantry_step",
        comfort="blanket",
        count=3,
        child_name="Theo",
        child_type="boy",
        parent_type="father",
        trait="hopeful",
    ),
]


def valid_combos() -> list[tuple[str, str, int]]:
    combos: list[tuple[str, str, int]] = []
    for parade_id in PARADES:
        for snack_id, snack in SNACKS.items():
            for count in [1, 2, 3]:
                if bad_combo(snack, count):
                    combos.append((parade_id, snack_id, count))
    return combos


def explain_rejection(snack: Snack, count: int) -> str:
    if not snack.rich:
        return (
            f"(No story: {snack.phrase} is not a rich enough treat to plausibly give Barfo "
            f"the bad tummy ache this cautionary tale needs. Pick a richer snack like jam_bun, "
            f"cream_puff, or honey_cake.)"
        )
    if count < GREED_MIN:
        return (
            f"(No story: stealing only {count} {snack.plural} does not make a strong enough "
            f"problem for this bad-ending world. Pick at least {GREED_MIN}.)"
        )
    return "(No story: this combination does not fit the world's cautionary logic.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parade = f["parade"]
    snack = f["snack"]
    count = f["count"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "barfo" and ends sadly.',
        f"Tell a rhyming cautionary tale where {child.id} and Barfo are getting ready for {parade.title}, but Barfo sneaks {count} {snack.plural} and ends up missing the parade.",
        f"Write a simple poem-story about greed and tummy trouble, where Barfo eats too much before a special night and the ending is bad instead of happy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    barfo = f["barfo"]
    parade = f["parade"]
    snack = f["snack"]
    comfort = f["comfort"]
    count = f["count"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and Barfo getting ready for {parade.title}. They were excited to go together before the trouble began.",
        ),
        (
            f"What did Barfo do wrong?",
            f"Barfo sneaked {count} {snack.plural} before the parade. He did it after being told to wait, because he wanted the sweet treat right away.",
        ),
        (
            "Why did Barfo miss the parade?",
            f"Barfo missed the parade because eating too many rich sweets made his tummy hurt. Once he felt sick, he could not walk out and join when the lights and music started.",
        ),
        (
            f"How did {child.id} try to help Barfo?",
            f"{child.id} brought {comfort.phrase} and stayed close to comfort him. That helped him feel a little safer, but it did not make the tummy ache go away in time.",
        ),
    ]
    if f["ending"] == "missed_and_messy":
        qa.append(
            (
                "What made the ending feel even worse?",
                f"The night was not only missed; the lantern was spoiled too. While {child.id} cared for Barfo, the special parade things were left behind and the room felt quiet and wrong.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                "It ended sadly, with the parade going on without them while Barfo lay still at home. The last image shows that a greedy choice can spoil a special night.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"tummy", "parade", "care"}
    comfort = f["comfort"]
    snack = f["snack"]
    if comfort.id == "mint_tea":
        tags.add("mint_tea")
    if comfort.id == "blanket":
        tags.add("blanket")
    if snack.id == "apple_slice":
        tags.add("apple")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: ending={world.facts.get('ending')} missed={world.facts.get('missed_parade')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, S, N) :- parade(P), snack(S), rich(S), count(N), greed_min(M), N >= M.

severity(S, N, R + N) :- chosen_snack(S), richness(S, R), chosen_count(N).
bad_ending(missed_and_messy) :- severity(_, _, V), messy_cutoff(C), V >= C.
bad_ending(missed_and_sad) :- severity(_, _, V), messy_cutoff(C), V < C.

% Python world makes Barfo sick when richness*count reaches the fullness gate.
fullness(R * N) :- chosen_snack(S), richness(S, R), chosen_count(N).
sick :- fullness(F), sick_fullness(M), F >= M.
missed :- sick, parade_started.

outcome(missed_and_messy) :- missed, bad_ending(missed_and_messy).
outcome(missed_and_sad) :- missed, bad_ending(missed_and_sad).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PARADES:
        lines.append(asp.fact("parade", pid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("richness", sid, snack.richness))
        if snack.rich:
            lines.append(asp.fact("rich", sid))
    for n in [1, 2, 3]:
        lines.append(asp.fact("count", n))
    lines.append(asp.fact("greed_min", GREED_MIN))
    lines.append(asp.fact("sick_fullness", SICK_FULLNESS))
    lines.append(asp.fact("messy_cutoff", 6))
    lines.append(asp.fact("parade_started"))
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
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_count", params.count),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming cautionary storyworld: Barfo eats too many sweets, gets a tummy ache, and misses a special parade."
    )
    ap.add_argument("--parade", choices=PARADES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--stash", choices=STASHES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--count", type=int, choices=[1, 2, 3])
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack is not None and args.count is not None:
        snack = SNACKS[args.snack]
        if not bad_combo(snack, args.count):
            raise StoryError(explain_rejection(snack, args.count))

    combos = [
        combo
        for combo in valid_combos()
        if (args.parade is None or combo[0] == args.parade)
        and (args.snack is None or combo[1] == args.snack)
        and (args.count is None or combo[2] == args.count)
    ]
    if not combos:
        if args.snack is not None and args.count is not None:
            raise StoryError(explain_rejection(SNACKS[args.snack], args.count))
        raise StoryError("(No valid combination matches the given options.)")

    parade, snack, count = rng.choice(sorted(combos))
    stash = args.stash or rng.choice(sorted(STASHES))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        parade=parade,
        snack=snack,
        stash=stash,
        comfort=comfort,
        count=count,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.parade not in PARADES:
        raise StoryError(f"(Unknown parade: {params.parade})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.stash not in STASHES:
        raise StoryError(f"(Unknown stash: {params.stash})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if not bad_combo(SNACKS[params.snack], params.count):
        raise StoryError(explain_rejection(SNACKS[params.snack], params.count))

    world = tell(
        parade=PARADES[params.parade],
        snack=SNACKS[params.snack],
        stash=STASHES[params.stash],
        comfort=COMFORTS[params.comfort],
        count=params.count,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure on seed {s}.")
            break

    outcome_mismatch = 0
    for p in cases:
        py_out = ending_of(SNACKS[p.snack], p.count)
        cl_out = asp_outcome(p)
        if py_out != cl_out:
            outcome_mismatch += 1
    if outcome_mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {outcome_mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        json.loads(sample.to_json())
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (parade, snack, count) combos:\n")
        for parade, snack, count in combos:
            print(f"  {parade:9} {snack:11} {count}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.snack} x{p.count} before {p.parade}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
