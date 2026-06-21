#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/convenience_twist_pirate_tale.py
=================================================================

A small storyworld in a pirate-tale style: a crew wants convenience, but a
twist changes what "easy" means, and the crew ends with a clever, safer, better
shortcut.

Premise:
- A young pirate and a helper are trying to get something done on a ship or at
  a harbor.
- They want convenience: less carrying, less climbing, fewer steps.
- A twist reveals the obvious shortcut is awkward, risky, or not actually
  convenient.
- A wiser move turns the same need into a real convenience, and the ending shows
  what changed.

This world keeps the domain tiny and simulation-driven:
- physical meters: distance, strain, risk, tidiness, cargo
- emotional memes: eagerness, worry, relief, pride, trust

The story is not a frozen paragraph; the state drives the prose.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
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
    dark_spot: str
    convenience_need: str
    twist: str
    deck_detail: str
    dock_detail: str
    risk_phrase: str
    safe_hint: str
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
class Goal:
    id: str
    label: str
    phrase: str
    benefit: str
    burden: str
    twist_burden: str
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
class Shortcut:
    id: str
    label: str
    phrase: str
    speed: int
    risk: int
    convenience: int
    safe: bool = False
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
class Fix:
    id: str
    label: str
    phrase: str
    convenience: int
    risk_reduction: int
    text: str
    qa_text: str
    safe: bool = True
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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("risk", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ship" in world.entities:
            world.get("ship").meters["strain"] += 1
        for x in list(world.entities.values()):
            if x.role in {"pirate", "helper"}:
                x.memes["worry"] += 1
        out.append("__risk__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["risk"] < THRESHOLD or e.meters["risk"] >= 2.0:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for x in list(world.entities.values()):
            if x.role in {"pirate", "helper"}:
                x.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("risk", "physical", _r_risk),
    Rule("relief", "physical", _r_relief),
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


def need_at_risk(goal: Goal, shortcut: Shortcut) -> bool:
    return goal.id in shortcut.tags or goal.benefit in shortcut.tags or shortcut.convenience > 0


def valid_fix(shortcut: Shortcut, goal: Goal, fix: Fix) -> bool:
    return shortcut.risk > 0 and fix.safe and fix.risk_reduction >= shortcut.risk


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.safe and f.convenience >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.convenience)


def travel_cost(shortcut: Shortcut, twist_level: int) -> int:
    return shortcut.risk + twist_level


def can_contain(shortcut: Shortcut, twist_level: int, fix: Fix) -> bool:
    return fix.risk_reduction >= travel_cost(shortcut, twist_level)


def predict(world: World, shortcut_id: str, twist_level: int) -> dict:
    sim = world.copy()
    sc = SHORTCUTS[shortcut_id]
    _use_shortcut(sim, sc, twist_level, narrate=False)
    ship = sim.entities.get("ship")
    return {
        "risk": ship.meters["risk"] if ship else 0,
        "strain": ship.meters["strain"] if ship else 0,
    }


def _use_shortcut(world: World, shortcut: Shortcut, twist_level: int, narrate: bool = True) -> None:
    ship = world.get("ship")
    ship.meters["risk"] += shortcut.risk + twist_level
    ship.meters["strain"] += max(0, shortcut.risk - 1)
    propagate(world, narrate=narrate)


def open_scene(world: World, hero: Entity, helper: Entity, place: Place, goal: Goal) -> None:
    hero.memes["eagerness"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"On a breezy morning aboard the {place.label}, {hero.id} and {helper.id} "
        f"were busy with {goal.phrase}."
    )
    world.say(
        f"The deck was busy and salty, and {place.deck_detail}."
    )
    world.say(
        f"They needed {place.convenience_need}, because {goal.benefit} but {goal.burden}."
    )


def ask_for_convenience(world: World, hero: Entity, helper: Entity, goal: Goal) -> None:
    world.say(
        f'"If we had a bit more convenience, this would be easy," {hero.id} said, '
        f"watching the ropes and crates."
    )
    world.say(
        f'{helper.id} nodded. "Aye, but every easy path has a twist at sea."'
    )
    hero.memes["hope"] += 1
    helper.memes["trust"] += 1


def tempt(world: World, hero: Entity, shortcut: Shortcut, place: Place) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f'{hero.id} spotted {shortcut.phrase} and grinned. "That would be convenient," '
        f"{hero.pronoun()} said. "
        f"It looked like the shortest way across the {place.label}."
    )


def warn(world: World, helper: Entity, shortcut: Shortcut, goal: Goal, place: Place, twist_level: int) -> None:
    pred = predict(world, shortcut.id, twist_level)
    helper.memes["worry"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{helper.id} squinted at the plan. "{shortcut.label.capitalize()} seems quick, '
        f'but it can turn awkward fast near {place.risk_phrase}."'
    )
    world.say(
        f'"If we choose that, the {goal.label} may lose the very convenience we wanted."'
    )


def twist_reveal(world: World, place: Place, goal: Goal, twist_level: int) -> None:
    if twist_level >= 2:
        world.say(
            f"Then came the twist: {place.twist}. What looked like a shortcut was not a shortcut at all."
        )
    else:
        world.say(
            f"But the sea had a little twist in store: {place.twist}."
        )


def choose_safe(world: World, hero: Entity, helper: Entity, fix: Fix, place: Place, goal: Goal) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{helper.id} pointed to a better way. "{fix.phrase}," {helper.id} said. '
        f"{fix.text}"
    )
    world.say(
        f"{hero.id} nodded, and the pair kept their hands free and their heads clear."
    )
    world.say(
        f"That gave them real convenience: {goal.label} went faster, but the deck stayed safe."
    )


def finish(world: World, hero: Entity, helper: Entity, place: Place, goal: Goal, fix: Fix) -> None:
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"By the time the sun leaned low, {hero.id} could finish {goal.phrase} "
        f"without any wild hauling."
    )
    world.say(
        f"{place.safe_hint.capitalize()}, and the crew sailed on with an easy laugh."
    )


def fail_branch(world: World, hero: Entity, helper: Entity, shortcut: Shortcut, goal: Goal, place: Place) -> None:
    hero.memes["worry"] += 2
    helper.memes["worry"] += 1
    world.say(
        f"{hero.id} tried it anyway, and the easy choice turned clumsy on the rolling deck."
    )
    world.say(
        f"The {goal.label} took longer, not shorter, and the crew had to slow down and clean up the mess."
    )
    world.say(
        f"In the end, they learned that not every fast path is convenient."
    )


def tell(place: Place, goal: Goal, shortcut: Shortcut, fix: Fix, hero_name: str = "Finn",
         hero_gender: str = "boy", helper_name: str = "Mira", helper_gender: str = "girl",
         twist_level: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="pirate"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    world.facts["twist_level"] = twist_level

    open_scene(world, hero, helper, place, goal)
    world.para()
    ask_for_convenience(world, hero, helper, goal)
    tempt(world, hero, shortcut, place)
    warn(world, helper, shortcut, goal, place, twist_level)
    twist_reveal(world, place, goal, twist_level)

    contained = can_contain(shortcut, twist_level, fix)
    world.facts["contained"] = contained
    world.para()
    if contained:
        _use_shortcut(world, shortcut, twist_level, narrate=True)
        choose_safe(world, hero, helper, fix, place, goal)
        world.para()
        finish(world, hero, helper, place, goal, fix)
        outcome = "safe"
    else:
        _use_shortcut(world, shortcut, twist_level, narrate=True)
        fail_branch(world, hero, helper, shortcut, goal, place)
        outcome = "awkward"

    world.facts.update(
        hero=hero, helper=helper, ship=ship, place=place, goal=goal, shortcut=shortcut,
        fix=fix, outcome=outcome, hero_gender=hero_gender, helper_gender=helper_gender,
    )
    return world


PLACES = {
    "harbor": Place(
        id="harbor",
        label="harbor",
        dark_spot="the far end of the dock",
        convenience_need="a quicker way to carry the cargo",
        twist="a rope bridge had been rolled up and tied loose across the gap",
        deck_detail="the gulls were circling the masts",
        dock_detail="the dock glittered with spray",
        risk_phrase="the wet planks",
        safe_hint="the crates were stacked neatly by the hatch",
        tags={"sea", "dock"},
    ),
    "ship": Place(
        id="ship",
        label="ship",
        dark_spot="the narrow hold",
        convenience_need="an easier way to move supplies",
        twist="the captain had already marked a safer path with bright chalk",
        deck_detail="the lanterns swung gently in the breeze",
        dock_detail="the harbor was only a memory behind them",
        risk_phrase="the swaying stairs",
        safe_hint="the chalk line stayed bright on the deck",
        tags={"sea", "hold"},
    ),
    "island": Place(
        id="island",
        label="island",
        dark_spot="the palm-shadowed path",
        convenience_need="a shortcut through the sand",
        twist="the shorter path cut straight through a patch of sticky mud",
        deck_detail="the tide whispered around the rocks",
        dock_detail="the boat bobbed at the shore",
        risk_phrase="the hidden mud",
        safe_hint="the tide washed the footprints clean",
        tags={"island", "sand"},
    ),
}

GOALS = {
    "cargo": Goal(
        id="cargo",
        label="cargo",
        phrase="moving the cargo",
        benefit="it had to reach the captain's cabin",
        burden="it was heavy enough to tire small arms",
        twist_burden="it could slip on a slope",
        tags={"cargo", "sea"},
    ),
    "supplies": Goal(
        id="supplies",
        label="supplies",
        phrase="sorting the supplies",
        benefit="the galley needed them fast",
        burden="they were stacked in far-away crates",
        twist_burden="they were easy to spill",
        tags={"supplies", "hold"},
    ),
    "map": Goal(
        id="map",
        label="map",
        phrase="delivering the map",
        benefit="the captain needed it before noon",
        burden="it had to stay dry and flat",
        twist_burden="it could wrinkle in a rush",
        tags={"map", "dock"},
    ),
}

SHORTCUTS = {
    "slide": Shortcut(
        id="slide",
        label="slide",
        phrase="the cargo slide",
        speed=3,
        risk=1,
        convenience=2,
        safe=False,
        tags={"cargo", "slide"},
    ),
    "pulley": Shortcut(
        id="pulley",
        label="pulley",
        phrase="the pulley line",
        speed=2,
        risk=2,
        convenience=3,
        safe=False,
        tags={"supplies", "rope"},
    ),
    "shortcut_path": Shortcut(
        id="shortcut_path",
        label="shortcut path",
        phrase="the shortcut path",
        speed=3,
        risk=2,
        convenience=2,
        safe=False,
        tags={"map", "path"},
    ),
}

FIXES = {
    "chalk_line": Fix(
        id="chalk_line",
        label="chalk line",
        phrase="Follow the chalk line instead of cutting across the swaying stairs",
        convenience=3,
        risk_reduction=3,
        text="it kept the route simple without any slipping or spooking.",
        qa_text="followed the chalk line and kept the route simple",
        safe=True,
        tags={"ship", "safe"},
    ),
    "trolley": Fix(
        id="trolley",
        label="trolley",
        phrase="Use the little trolley by the hatch",
        convenience=3,
        risk_reduction=3,
        text="it rolled the load along without dragging it by hand.",
        qa_text="used the little trolley by the hatch",
        safe=True,
        tags={"cargo", "safe"},
    ),
    "dry_case": Fix(
        id="dry_case",
        label="dry case",
        phrase="Put the map in a dry case and carry it flat",
        convenience=2,
        risk_reduction=2,
        text="it kept the map smooth, dry, and easy to hand over.",
        qa_text="put the map in a dry case and carried it flat",
        safe=True,
        tags={"map", "safe"},
    ),
    "water_bucket": Fix(
        id="water_bucket",
        label="bucket",
        phrase="A bucket of water will help",
        convenience=1,
        risk_reduction=0,
        text="it did not really help with the ropes at all.",
        qa_text="used a bucket of water",
        safe=False,
        tags={"unsafe"},
    ),
}

TRAITS = ["cheerful", "clever", "practical", "brave", "patient", "curious"]
NAMES_B = ["Finn", "Tom", "Jack", "Ben", "Noah"]
NAMES_G = ["Mira", "Lena", "Rose", "Ivy", "Nia"]


@dataclass
class StoryParams:
    place: str
    goal: str
    shortcut: str
    fix: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    twist_level: int = 1
    trait: str = "clever"
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
    StoryParams(place="harbor", goal="cargo", shortcut="slide", fix="trolley", hero="Finn", hero_gender="boy", helper="Mira", helper_gender="girl", twist_level=1, trait="practical"),
    StoryParams(place="ship", goal="supplies", shortcut="pulley", fix="chalk_line", hero="Tom", hero_gender="boy", helper="Rose", helper_gender="girl", twist_level=2, trait="curious"),
    StoryParams(place="island", goal="map", shortcut="shortcut_path", fix="dry_case", hero="Ivy", hero_gender="girl", helper="Jack", helper_gender="boy", twist_level=1, trait="cheerful"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for goal in GOALS.values():
            for sc in SHORTCUTS.values():
                if need_at_risk(goal, sc):
                    combos.append((place.id, goal.id, sc.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale that includes the word "convenience" and a twist at sea.',
        f"Tell a short story where {f['hero'].id} wants convenience while moving {f['goal'].phrase}, but the shortcut turns out to be trickier than it looked.",
        f"Write a pirate story where a clever helper notices a twist, offers a better way, and the crew ends with a real convenience.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    goal: Goal = f["goal"]
    shortcut: Shortcut = f["shortcut"]
    fix: Fix = f["fix"]
    qa = [
        ("What did the crew want?", f"They wanted convenience while {goal.phrase}. They hoped to do the job with fewer hard steps."),
        ("What was the twist?", f"{place.twist.capitalize()}. That meant the easy-looking shortcut was not as easy as it first seemed."),
        (f"What did {helper.id} notice?", f"{helper.id} noticed that {shortcut.label} would not stay handy near {place.risk_phrase}. {helper.pronoun().capitalize()} warned that a quick path at sea can become a troublesome one."),
    ]
    if f["outcome"] == "safe":
        qa.append((
            "How did they solve the problem?",
            f"They used {fix.label} and kept the work tidy and safe. That gave them true convenience because the job stayed easy without causing trouble."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the cargo moved smoothly and the deck still safe. The crew learned that a good shortcut is one that helps without making new trouble."
        ))
    else:
        qa.append((
            "What happened when they tried the shortcut?",
            f"The shortcut turned awkward and slowed them down. Instead of giving convenience, it made extra work on the rolling deck."
        ))
        qa.append((
            "What did they learn?",
            f"They learned that not every fast path is really convenient. On a pirate ship, the safer way can be the shorter way in the end."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["goal"].tags) | set(world.facts["shortcut"].tags) | set(world.facts["fix"].tags)
    out = []
    if "sea" in tags:
        out.append(("Why do pirates use the word 'aye'?", "Pirates say 'aye' to mean yes. It is a ship-shaped way of agreeing quickly."))
    if "dock" in tags:
        out.append(("What is a dock?", "A dock is a place where boats stop so people can load and unload things."))
    if "cargo" in tags:
        out.append(("What is cargo?", "Cargo is the stuff a ship carries, like crates, sacks, or barrels."))
    if "map" in tags:
        out.append(("Why do pirates like maps?", "Pirates like maps because maps show where to go. A good map helps the crew find the right place without wandering."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(shortcut: Shortcut, fix: Fix) -> str:
    return f"(No story: {shortcut.label} and {fix.label} do not make a believable convenience twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.fix == "water_bucket":
        raise StoryError("(Refusing fix 'water_bucket': it is not a sensible pirate convenience solution.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goal is None or c[1] == args.goal)
              and (args.shortcut is None or c[2] == args.shortcut)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal, shortcut = rng.choice(sorted(combos))
    fix = args.fix or rng.choice([f.id for f in sensible_fixes()])
    if fix not in FIXES:
        raise StoryError("(Unknown fix.)")
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if hero_gender == "boy" else "boy")
    hero_pool = NAMES_B if hero_gender == "boy" else NAMES_G
    helper_pool = NAMES_G if helper_gender == "girl" else NAMES_B
    hero = args.hero or rng.choice(hero_pool)
    helper = args.helper or rng.choice([n for n in helper_pool if n != hero] or helper_pool)
    twist_level = args.twist_level if args.twist_level is not None else rng.randint(1, 2)
    return StoryParams(place=place, goal=goal, shortcut=shortcut, fix=fix, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, twist_level=twist_level, trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.goal not in GOALS or params.shortcut not in SHORTCUTS or params.fix not in FIXES:
        raise StoryError("Invalid StoryParams for this world.")
    world = tell(PLACES[params.place], GOALS[params.goal], SHORTCUTS[params.shortcut], FIXES[params.fix], params.hero, params.hero_gender, params.helper, params.helper_gender, params.twist_level)
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


ASP_RULES = r"""
valid(P,G,S) :- place(P), goal(G), shortcut(S), need_at_risk(G,S).
safe_fix(S,F) :- shortcut(S), fix(F), risk(S,R), risk_reduce(F,RR), RR >= R, safe(F).
outcome(safe) :- chosen_fix(F), chosen_shortcut(S), chosen_twist(T), safe_fix(S,F), twist(T), threshold(T,Th), Th <= 2.
outcome(awkward) :- chosen_fix(F), chosen_shortcut(S), chosen_twist(T), not safe_fix(S,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for g in GOALS.values():
        lines.append(asp.fact("goal", g.id))
    for s in SHORTCUTS.values():
        lines.append(asp.fact("shortcut", s.id))
        lines.append(asp.fact("need_at_risk", s.id, 1))
        lines.append(asp.fact("risk", s.id, s.risk))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        lines.append(asp.fact("risk_reduce", f.id, f.risk_reduction))
        if f.safe:
            lines.append(asp.fact("safe", f.id))
    for t in [1, 2]:
        lines.append(asp.fact("twist", t))
        lines.append(asp.fact("threshold", t, t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combo sets differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale convenience world with a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--twist-level", type=int, choices=[1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
