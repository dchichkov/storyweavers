#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py
===========================================================================

A standalone story world for a child-facing ghost story with humor, sound
effects, and a quest. A child "agent" hears spooky noises, follows them with a
light, discovers a friendly ghost with a simple problem, and solves it.

The world enforces two common-sense constraints:

1. The place must actually support the kind of spooky problem.
2. The chosen fix must solve that problem, and the chosen gear must be bright
   enough for that place.

The story text is driven by simulated state: spooky trouble raises fear and
need; a good light raises bravery; the right fix clears the trouble and changes
the ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py
    python storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py --place attic --trouble sneeze --fix handkerchief --gear solar_lantern
    python storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py --place attic --gear candle_stub
    python storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py --all
    python storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/agent_solar_humor_sound_effects_quest_ghost.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "witch"}
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
    intro: str
    path: str
    darkness: int
    affords: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    sound: str
    open_line: str
    cause: str
    need: str
    fix_hint: str
    funny_detail: str
    fear_boost: int
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
class Fix:
    id: str
    label: str
    phrase: str
    cures: set[str] = field(default_factory=set)
    action: str = ""
    result: str = ""
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
class Gear:
    id: str
    label: str
    phrase: str
    glow: str
    brightness: int
    solar: bool = False
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
    def __init__(self, place: Place) -> None:
        self.place_cfg = place
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
        clone = World(self.place_cfg)
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


def _r_spooky(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    place = world.get("place")
    hero = world.get("hero")
    if ghost.meters["trouble"] >= THRESHOLD:
        sig = ("spooky", world.facts["trouble"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["spooky"] += 1
            hero.memes["fear"] += float(world.facts["trouble"].fear_boost)
            ghost.memes["need"] += 1
            out.append("__spooky__")
    return out


def _r_light(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    gear = world.get("gear")
    if gear.meters["lit"] >= THRESHOLD:
        sig = ("light", world.facts["gear"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["bravery"] += 1
            if hero.memes["fear"] >= THRESHOLD:
                hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
            out.append("__light__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    place = world.get("place")
    hero = world.get("hero")
    if ghost.meters["helped"] >= THRESHOLD and ghost.meters["trouble"] >= THRESHOLD:
        trouble = world.facts["trouble"]
        fix = world.facts["fix"]
        sig = ("fix", trouble.id, fix.id)
        if sig not in world.fired and trouble.id in fix.cures:
            world.fired.add(sig)
            ghost.meters["trouble"] = 0.0
            place.meters["spooky"] = 0.0
            ghost.memes["relief"] += 1
            ghost.memes["giggles"] += 1
            hero.memes["pride"] += 1
            hero.memes["fear"] = 0.0
            out.append("__fixed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spooky", tag="social", apply=_r_spooky),
    Rule(name="light", tag="social", apply=_r_light),
    Rule(name="fix", tag="social", apply=_r_fix),
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


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        intro="At the top of the old house was an attic with slanted beams and moon-pale dust.",
        path="up the narrow stairs",
        darkness=3,
        affords={"sneeze", "cold"},
        tags={"attic", "dark"},
    ),
    "hallway": Place(
        id="hallway",
        label="the long hallway",
        intro="The hallway had a crooked runner rug and portraits that looked extra serious at night.",
        path="along the long hallway",
        darkness=2,
        affords={"hiccup", "cold"},
        tags={"hallway", "dark"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse",
        intro="Beyond the kitchen stood a greenhouse where moonlight drew silver squares on the floor.",
        path="through the back door to the greenhouse",
        darkness=1,
        affords={"echo", "hiccup"},
        tags={"greenhouse", "moonlight"},
    ),
}

TROUBLES = {
    "sneeze": Trouble(
        id="sneeze",
        sound="A-CHOO-BOO! A-CHOO-BOO!",
        open_line='"A-CHOO-BOO! A-CHOO-BOO!"',
        cause="dust tickling the ghost's tiny nose",
        need="a soft handkerchief",
        fix_hint="something soft for a sneezy nose",
        funny_detail="Each sneeze made the ghost spin once like a loose napkin in the wind.",
        fear_boost=2,
        tags={"sneeze", "ghost"},
    ),
    "hiccup": Trouble(
        id="hiccup",
        sound="BUP! Boo-bup! BUP!",
        open_line='"BUP! Boo-bup! BUP!"',
        cause="moonberry soda bubbles stuck in the ghost's middle",
        need="a sip of warm tea",
        fix_hint="something warm to settle hiccups",
        funny_detail="Every hiccup made the ghost jump an inch and apologize to the wallpaper.",
        fear_boost=1,
        tags={"hiccup", "ghost"},
    ),
    "cold": Trouble(
        id="cold",
        sound="Wooo-ooo-brrr!",
        open_line='"Wooo-ooo-brrr!"',
        cause="a cold draft sliding through the boards",
        need="a striped scarf",
        fix_hint="something cozy for a shivery neck",
        funny_detail="The ghost's teeth chattered so fast they sounded like tiny castanets.",
        fear_boost=2,
        tags={"cold", "ghost"},
    ),
    "echo": Trouble(
        id="echo",
        sound="BONG... boing... booing...",
        open_line='"BONG... boing... booing..."',
        cause="a bent watering can that made every drip echo like a moan",
        need="a cork for the watering can spout",
        fix_hint="something that can plug a drippy spout",
        funny_detail="The ghost kept glaring at the can as if it were telling jokes too loudly.",
        fear_boost=1,
        tags={"echo", "ghost"},
    ),
}

FIXES = {
    "handkerchief": Fix(
        id="handkerchief",
        label="handkerchief",
        phrase="a soft spotted handkerchief",
        cures={"sneeze"},
        action="held out the handkerchief with both hands",
        result="The ghost dabbed its nose, took one careful sniff, and the giant sneezes stopped.",
        tags={"handkerchief", "care"},
    ),
    "tea": Fix(
        id="tea",
        label="warm tea",
        phrase="a tiny cup of warm tea",
        cures={"hiccup"},
        action="offered the tiny cup very carefully",
        result="The ghost sipped the tea. After one last polite 'bup,' the hiccups melted away.",
        tags={"tea", "care"},
    ),
    "scarf": Fix(
        id="scarf",
        label="scarf",
        phrase="a long striped scarf",
        cures={"cold"},
        action="wrapped the scarf around the ghost's neck like a little comet tail",
        result="At once the ghost floated warmer and rounder, no longer shivering in the draft.",
        tags={"scarf", "care"},
    ),
    "cork": Fix(
        id="cork",
        label="cork",
        phrase="a snug cork",
        cures={"echo"},
        action="pushed the cork into the watering can spout",
        result="Plink. Silence. Then only a happy little greenhouse hush remained.",
        tags={"cork", "care"},
    ),
    "cookie": Fix(
        id="cookie",
        label="cookie",
        phrase="a buttery cookie",
        cures=set(),
        action="offered a cookie hopefully",
        result="It smelled nice, but it did not solve the problem.",
        tags={"cookie"},
    ),
}

GEAR = {
    "solar_lantern": Gear(
        id="solar_lantern",
        label="solar lantern",
        phrase="a small solar lantern",
        glow="glowed lemon-yellow after charging on the windowsill all day",
        brightness=3,
        solar=True,
        tags={"solar", "lantern", "light"},
    ),
    "flashlight": Gear(
        id="flashlight",
        label="flashlight",
        phrase="a pocket flashlight",
        glow="made a brave white beam that bounced from wall to wall",
        brightness=2,
        solar=False,
        tags={"flashlight", "light"},
    ),
    "glow_jar": Gear(
        id="glow_jar",
        label="glow jar",
        phrase="a jar full of glow beads",
        glow="shone soft green like bottled fireflies",
        brightness=1,
        solar=False,
        tags={"jar", "light"},
    ),
    "candle_stub": Gear(
        id="candle_stub",
        label="candle stub",
        phrase="a tired little candle stub",
        glow="flickered so weakly it mostly scared its own shadow",
        brightness=1,
        solar=False,
        tags={"candle", "light"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Tess", "Ava", "Ivy", "June"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Max", "Leo", "Jude", "Eli"]
HELPER_NAMES = ["Pip", "Dot", "Bean", "Kit", "Moss", "Rue"]
TRAITS = ["brave", "curious", "careful", "funny", "quick", "thoughtful"]


def fix_works(trouble: Trouble, fix: Fix) -> bool:
    return trouble.id in fix.cures


def gear_suits(place: Place, gear: Gear) -> bool:
    return gear.brightness >= place.darkness


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for trouble_id in sorted(place.affords):
            trouble = TROUBLES[trouble_id]
            for fix_id, fix in FIXES.items():
                if not fix_works(trouble, fix):
                    continue
                for gear_id, gear in GEAR.items():
                    if gear_suits(place, gear):
                        combos.append((place_id, trouble.id, fix_id, gear_id))
    return sorted(combos)


def predict_unhelped(world: World) -> dict:
    sim = world.copy()
    ghost = sim.get("ghost")
    ghost.meters["trouble"] += 1
    propagate(sim, narrate=False)
    return {
        "spooky": sim.get("place").meters["spooky"],
        "fear": sim.get("hero").memes["fear"],
        "need": sim.get("ghost").memes["need"],
    }


def introduce(world: World, hero: Entity, helper: Entity, parent: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} loved secret games so much that {hero.pronoun()} had made up a title for {hero.pronoun('object')}: "
        f"Agent {hero.id}. {helper.id}, {hero.pronoun('possessive')} little helper, thought this was the grandest thing in the world."
    )
    world.say(
        f"That evening, {parent.label_word.capitalize()} tucked the blankets smooth and said the old house was only old, not scary. "
        f"But outside the room, {place.intro}"
    )


def hear_sound(world: World, hero: Entity, helper: Entity, trouble: Trouble, place: Place) -> None:
    ghost = world.get("ghost")
    ghost.meters["trouble"] += 1
    world.para()
    world.say(
        f"Then a sound floated {place.path}: {trouble.open_line} {helper.id} grabbed {hero.pronoun('possessive')} sleeve so fast that both of them nearly bounced."
    )
    world.say(
        f'"Did the house just say boo with a sneeze in it?" {helper.id} whispered. '
        f'It was a silly question, which only made the hall feel spookier.'
    )
    propagate(world, narrate=False)


def choose_gear(world: World, hero: Entity, helper: Entity, gear: Gear) -> None:
    gear_ent = world.get("gear")
    gear_ent.meters["lit"] += 1
    propagate(world, narrate=False)
    solar_note = " Because it was solar, it had been quietly drinking sunshine all day." if gear.solar else ""
    world.say(
        f'Agent {hero.id} reached for {gear.phrase} that {gear.glow}.{solar_note}'
    )
    if hero.memes["bravery"] >= THRESHOLD:
        world.say(
            f'"A real night agent takes a good light," {hero.id} said, trying to sound calm. '
            f'The beam made the corners look less hungry.'
        )
    else:
        world.say(
            f'The weak glow did not help much, and even the dust looked suspicious.'
        )
    helper.memes["trust"] += 1


def quest_vow(world: World, hero: Entity, helper: Entity, trouble: Trouble, place: Place) -> None:
    pred = predict_unhelped(world)
    world.facts["predicted_spooky"] = pred["spooky"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"{hero.id} listened again. The sound did not seem mean. It seemed miserable. "
        f"If no one helped, the spooky feeling would only grow."
    )
    world.say(
        f'"Then this is a quest," {hero.pronoun()} said. "We will follow the noise, ask polite questions, and fix whatever is wrong." '
        f'{helper.id} nodded so hard that {helper.pronoun("possessive")} hair flopped.'
    )


def meet_ghost(world: World, hero: Entity, helper: Entity, trouble: Trouble, place: Place) -> None:
    ghost = world.get("ghost")
    ghost.memes["shy"] += 1
    world.para()
    world.say(
        f"They crept {place.path} until the light found a small white ghost curled in a corner. "
        f"It was not the roaring sort from stories. It looked more like a floating pillowcase with worried eyes."
    )
    world.say(
        f"{trouble.funny_detail} When the ghost noticed them, it gave a tiny bow and made the sound again: {trouble.open_line}"
    )
    world.say(
        f'"Oh dear," said the ghost. "I am trying to be mysterious, but really it is just {trouble.cause}."'
    )


def solve(world: World, hero: Entity, helper: Entity, trouble: Trouble, fix: Fix) -> None:
    ghost = world.get("ghost")
    world.para()
    world.say(
        f'Agent {hero.id} remembered the clue at once: this ghost needed {trouble.need}. '
        f'{helper.id} opened the little quest satchel and found {fix.phrase}.'
    )
    world.say(
        f"{hero.id} {fix.action}. The ghost blinked in surprise, then smiled the way a cloud might smile."
    )
    ghost.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(fix.result)


def celebrate(world: World, hero: Entity, helper: Entity, parent: Entity, place: Place, trouble: Trouble, fix: Fix, gear: Gear) -> None:
    ghost = world.get("ghost")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    ghost.memes["gratitude"] += 1
    world.say(
        f'The ghost spun in one happy circle and said, "Thank you, Agent {hero.id}. I was trying to sound grand and ghostly, '
        f'but I kept sounding ridiculous."'
    )
    world.say(
        f'{helper.id} giggled. "You sounded like a goose in slippers." For the first time that night, everyone laughed.'
    )
    world.say(
        f"Soon {parent.label_word} came to see what the whispering was about. Instead of finding a fright, "
        f"{parent.pronoun()} found two proud children, one relieved ghost, and {gear.phrase} shining kindly in {place.label}."
    )
    world.say(
        f"After that, whenever a funny sound drifted through the house, {hero.id} did not hide under the blanket. "
        f"{hero.pronoun().capitalize()} sat up, listened first, and remembered that even a ghostly problem might only need a little help."
    )


def tell(
    *,
    place: Place,
    trouble: Trouble,
    fix: Fix,
    gear: Gear,
    hero_name: str,
    hero_type: str,
    helper_name: str,
    parent_type: str,
    hero_trait: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=[hero_trait]))
    helper = world.add(Entity(id="helper", kind="character", type="child", label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", role="ghost"))
    gear_ent = world.add(Entity(id="gear", kind="thing", type="gear", label=gear.label))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))

    hero.attrs["display_name"] = hero_name
    helper.attrs["display_name"] = helper_name
    parent.attrs["display_name"] = parent.label_word
    ghost.attrs["display_name"] = "Puff"

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        ghost=ghost,
        place=place,
        trouble=trouble,
        fix=fix,
        gear=gear,
        resolved=False,
    )

    introduce(world, hero, helper, parent, place)
    hear_sound(world, hero, helper, trouble, place)
    choose_gear(world, hero, helper, gear)
    quest_vow(world, hero, helper, trouble, place)
    meet_ghost(world, hero, helper, trouble, place)
    solve(world, hero, helper, trouble, fix)
    celebrate(world, hero, helper, parent, place, trouble, fix, gear)

    world.facts["resolved"] = ghost.memes["relief"] >= THRESHOLD
    world.facts["spooky_before"] = world.facts.get("predicted_spooky", 0) >= THRESHOLD
    world.facts["agent_name"] = hero_name
    world.facts["helper_name"] = helper_name
    return world


KNOWLEDGE = {
    "solar": [
        (
            "What does solar mean?",
            "Solar means something uses energy from sunlight. A solar lantern charges in the light and can shine later when it is dark."
        )
    ],
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with spooky feelings, strange sounds, or a ghost. In child-friendly ghost stories, the spooky part often turns out gentler than it first seems."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you carry with you. It helps people see in dark places."
        )
    ],
    "sneeze": [
        (
            "Why do dust and sneezes go together?",
            "Dust can tickle your nose and make you sneeze. Sneezes happen when your body tries to push the tickle out."
        )
    ],
    "hiccup": [
        (
            "What is a hiccup?",
            "A hiccup is a sudden little jump in your breathing that makes a funny sound. They usually go away after a short while."
        )
    ],
    "cold": [
        (
            "Why does a scarf help when someone feels cold?",
            "A scarf helps keep warmth close to the neck. That can make a chilly person feel cozy."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after it hits something. That is why one drip or shout can sound bigger than it really is."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a purpose. Someone goes looking for an answer, a person, or a way to solve a problem."
        )
    ],
    "bravery": [
        (
            "What does bravery mean?",
            "Bravery means doing the next helpful thing even when you feel afraid. It does not mean never feeling scared."
        )
    ],
}
KNOWLEDGE_ORDER = ["solar", "ghost", "lantern", "quest", "sneeze", "hiccup", "cold", "echo", "bravery"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    fix: str
    gear: str
    hero_name: str
    hero_type: str
    helper_name: str
    parent_type: str
    hero_trait: str
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
        place="attic",
        trouble="sneeze",
        fix="handkerchief",
        gear="solar_lantern",
        hero_name="Mina",
        hero_type="girl",
        helper_name="Pip",
        parent_type="mother",
        hero_trait="curious",
        seed=101,
    ),
    StoryParams(
        place="hallway",
        trouble="cold",
        fix="scarf",
        gear="flashlight",
        hero_name="Owen",
        hero_type="boy",
        helper_name="Dot",
        parent_type="father",
        hero_trait="brave",
        seed=102,
    ),
    StoryParams(
        place="greenhouse",
        trouble="echo",
        fix="cork",
        gear="glow_jar",
        hero_name="Lila",
        hero_type="girl",
        helper_name="Bean",
        parent_type="mother",
        hero_trait="funny",
        seed=103,
    ),
    StoryParams(
        place="hallway",
        trouble="hiccup",
        fix="tea",
        gear="flashlight",
        hero_name="Theo",
        hero_type="boy",
        helper_name="Kit",
        parent_type="father",
        hero_trait="thoughtful",
        seed=104,
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero_name = world.facts["agent_name"]
    place = world.facts["place"]
    trouble = world.facts["trouble"]
    gear = world.facts["gear"]
    return [
        f'Write a child-friendly ghost story with humor, sound effects, and a quest. Include the words "agent" and "solar".',
        f"Tell a spooky-but-gentle story where Agent {hero_name} follows the sound {trouble.sound} into {place.label} and discovers that the ghost needs help, not fear.",
        f"Write a funny night quest in which a child uses {gear.phrase} to investigate a ghostly noise and turns the scare into kindness."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero_name = world.facts["agent_name"]
    helper_name = world.facts["helper_name"]
    parent = world.facts["parent"]
    place = world.facts["place"]
    trouble = world.facts["trouble"]
    fix = world.facts["fix"]
    gear = world.facts["gear"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, who likes pretending to be an agent, and {helper_name}, who joins the night quest. They meet a small ghost who sounds spooky but really needs help."
        ),
        (
            "What sound started the quest?",
            f"The quest began when the children heard {trouble.sound} drifting from {place.label}. The noise sounded eerie at first, so they went to investigate instead of guessing."
        ),
        (
            f"Why did {hero_name} bring {gear.phrase}?",
            f"{hero_name} brought it because {place.label} was dark. The light made the search safer and helped {hero_name} feel brave enough to keep going."
        ),
        (
            "What was really wrong with the ghost?",
            f"The ghost was not trying to scare anyone on purpose. The trouble came from {trouble.cause}, which made the ghost sound strange and miserable."
        ),
        (
            f"How did the children solve the problem?",
            f"They figured out that the ghost needed {trouble.need}, and they offered {fix.phrase}. {fix.result}"
        ),
        (
            "How did the story end?",
            f"It ended with laughter instead of fear. The children, the parent, and the relieved ghost stood together while the spooky place felt calm again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "quest", "bravery"}
    gear = world.facts["gear"]
    trouble = world.facts["trouble"]
    if gear.solar:
        tags.add("solar")
    if "lantern" in gear.tags:
        tags.add("lantern")
    if trouble.id in {"sneeze", "hiccup", "cold", "echo"}:
        tags.add(trouble.id)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_bad_trouble(place: Place, trouble: Trouble) -> str:
    return (
        f"(No story: {trouble.id} is not a good fit for {place.label}. "
        f"That place supports {sorted(place.affords)}, so choose a trouble that belongs there.)"
    )


def explain_bad_fix(trouble: Trouble, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not solve {trouble.id}. "
        f"The ghost needs {trouble.fix_hint}, so pick a matching fix.)"
    )


def explain_bad_gear(place: Place, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} is too dim for {place.label}. "
        f"That place has darkness level {place.darkness}, but this gear only reaches {gear.brightness}.)"
    )


ASP_RULES = r"""
place_has_trouble(P, T) :- affords(P, T).
fix_works(T, F) :- cures(F, T).
gear_suits(P, G) :- darkness(P, D), brightness(G, B), B >= D.
valid(P, T, F, G) :- place(P), trouble(T), fix(F), gear(G),
                     place_has_trouble(P, T), fix_works(T, F), gear_suits(P, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("darkness", place_id, place.darkness))
        for trouble_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, trouble_id))
    for trouble_id in TROUBLES:
        lines.append(asp.fact("trouble", trouble_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for trouble_id in sorted(fix.cures):
            lines.append(asp.fact("cures", fix_id, trouble_id))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("brightness", gear_id, gear.brightness))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child agent, a spooky sound, and a kind quest."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--gear", choices=sorted(GEAR))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.trouble:
        place = PLACES[args.place]
        trouble = TROUBLES[args.trouble]
        if trouble.id not in place.affords:
            raise StoryError(explain_bad_trouble(place, trouble))
    if args.trouble and args.fix:
        trouble = TROUBLES[args.trouble]
        fix = FIXES[args.fix]
        if not fix_works(trouble, fix):
            raise StoryError(explain_bad_fix(trouble, fix))
    if args.place and args.gear:
        place = PLACES[args.place]
        gear = GEAR[args.gear]
        if not gear_suits(place, gear):
            raise StoryError(explain_bad_gear(place, gear))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.fix is None or combo[2] == args.fix)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, trouble_id, fix_id, gear_id = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        trouble=trouble_id,
        fix=fix_id,
        gear=gear_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        parent_type=parent_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.gear not in GEAR:
        raise StoryError(f"(Unknown gear: {params.gear})")

    place = PLACES[params.place]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    gear = GEAR[params.gear]

    if trouble.id not in place.affords:
        raise StoryError(explain_bad_trouble(place, trouble))
    if not fix_works(trouble, fix):
        raise StoryError(explain_bad_fix(trouble, fix))
    if not gear_suits(place, gear):
        raise StoryError(explain_bad_gear(place, gear))

    world = tell(
        place=place,
        trouble=trouble,
        fix=fix,
        gear=gear,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        parent_type=params.parent_type,
        hero_trait=params.hero_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, trouble, fix, gear) combos:\n")
        for place, trouble, fix, gear in combos:
            print(f"  {place:10} {trouble:8} {fix:14} {gear}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.trouble} in {p.place} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
