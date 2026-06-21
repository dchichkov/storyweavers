#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fighter_driver_quest_space_adventure.py
=======================================================================

A standalone storyworld about a small space quest: a brave fighter and a careful
driver travel together, get lost among stars, and choose a wise route back to
their mission. The world is built from state, not fixed prose, so different seeds
can swap the ship, the quest goal, the hazard, and the safe solution.

The core premise is simple and child-facing:
- a fighter wants to rush ahead toward a quest goal,
- a driver notices a navigation problem or space hazard,
- they must choose between speed and safety,
- a fix changes the ship's state, and the ending proves they completed the quest.

This file follows the Storyweavers storyworld contract:
- stdlib only
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of results.py for QAItem, StoryError, StorySample
- lazy import of asp.py inside ASP helpers only
- Python reasonableness gate plus inline ASP_RULES twin
- generate-based story + grounded Q&A from world state
"""

from __future__ import annotations

import argparse
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
BRAVE_START = 5.0
CAREFUL_TRAITS = {"careful", "cautious", "steady", "thoughtful"}


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
        female = {"girl", "mother", "woman", "pilot"}
        male = {"boy", "father", "man", "fighter", "driver"}
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
class Setting:
    id: str
    scene: str
    ship: str
    quest_word: str
    mission: str
    stars: str
    dark_place: str
    sendoff: str
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
class QuestGoal:
    id: str
    label: str
    need: str
    distance: int
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
class Hazard:
    id: str
    label: str
    clue: str
    danger: int
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
    method: str
    power: int
    sense: int
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
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


def _r_drift(world: World) -> list[str]:
    out = []
    ship = world.get("ship")
    if ship.meters["drifting"] >= THRESHOLD and ("drift",) not in world.fired:
        world.fired.add(("drift",))
        ship.meters["lost"] += 1
        world.get("fighter").memes["worry"] += 1
        world.get("driver").memes["worry"] += 1
        out.append("__drift__")
    return out


def _r_alert(world: World) -> list[str]:
    out = []
    if world.get("hazard").meters["near"] >= THRESHOLD and ("alert",) not in world.fired:
        world.fired.add(("alert",))
        world.get("fighter").memes["surprised"] += 1
        world.get("driver").memes["alert"] += 1
        out.append("__alert__")
    return out


CAUSAL_RULES = [Rule("drift", _r_drift), Rule("alert", _r_alert)]


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


def problem_is_real(goal: QuestGoal, hazard: Hazard) -> bool:
    return goal.need == "navigation" and hazard.danger >= 1


def can_fixer_help(fix: Fix, hazard: Hazard) -> bool:
    return fix.power >= hazard.danger


def caution_wins(trait: str, driver_age: int, fighter_age: int) -> bool:
    return trait in CAREFUL_TRAITS and driver_age >= fighter_age


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for gid, goal in QUESTS.items():
            for hid, hz in HAZARDS.items():
                if problem_is_real(goal, hz):
                    combos.append((sid, gid, hid))
    return combos


def _do_hazard(world: World, hazard: Hazard, narrate: bool = True) -> None:
    world.get("hazard").meters["near"] += 1
    world.get("ship").meters["drifting"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, quest: QuestGoal, hazard: Hazard, fix: Fix,
         fighter_name: str = "Nova", fighter_type: str = "fighter",
         driver_name: str = "Milo", driver_type: str = "driver",
         parent_name: str = "Captain", parent_type: str = "pilot",
         trait: str = "careful", delay: int = 0,
         fighter_age: int = 6, driver_age: int = 7) -> World:
    world = World()
    fighter = world.add(Entity(id=fighter_name, kind="character", type=fighter_type,
                               role="fighter", traits=["bold"], attrs={"age": fighter_age}))
    driver = world.add(Entity(id=driver_name, kind="character", type=driver_type,
                              role="driver", traits=[trait], attrs={"age": driver_age}))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type,
                              role="guide", label="the captain"))
    ship = world.add(Entity(id="ship", type="ship", label=setting.ship))
    q = world.add(Entity(id="quest", type="quest", label=quest.label))
    hz = world.add(Entity(id="hazard", type="hazard", label=hazard.label))

    fighter.memes["bravery"] = BRAVE_START
    driver.memes["caution"] = 4.0 if trait in CAREFUL_TRAITS else 2.0
    world.facts["setting"] = setting
    world.facts["quest"] = quest
    world.facts["hazard_cfg"] = hazard
    world.facts["fix"] = fix

    world.say(f"On a bright day in space, {fighter.id} and {driver.id} rode on {setting.ship}.")
    world.say(f"{setting.ship.capitalize()} was their {setting.scene}. {setting.mission}")

    world.para()
    world.say(f"{fighter.id} wanted to chase {quest.label} at once.")
    world.say(f"But the sky had {hazard.clue}, and {driver.id} could tell that was not safe.")

    if caution_wins(trait, driver_age, fighter_age):
        world.say(f'{driver.id} shook {driver.pronoun("possessive")} head and said, "Let\'s slow down and stay on course."')
        world.say(f"{fighter.id} listened, and the two friends chose the safe map.")
        world.para()
        world.say(f"They followed the map all the way to {quest.label}.")
        world.say(f"At the end, {setting.sendoff}, bright and calm, with {quest.label} glowing ahead of them.")
        outcome = "avoided"
    else:
        world.say(f'{fighter.id} said, "I can do it fast!" and pushed forward anyway.')
        _do_hazard(world, hazard, narrate=False)
        world.para()
        world.say(f"{hazard.label.capitalize()} jolted the ship, and {setting.dark_place} went dark.")
        world.say(f"{driver.id} pointed to the controls and called for a fix.")
        if can_fixer_help(fix, hazard):
            world.say(f"{parent.label_word.capitalize()} came in, used the {fix.label}, and {fix.method}.")
            world.say(f"The ship steadied, the drift stopped, and the quest could continue.")
            world.para()
            world.say(f"After that, {fighter.id} and {driver.id} reached {quest.label} together.")
            world.say(f"They finished the quest with the ship humming safely under the stars.")
            outcome = "fixed"
        else:
            world.say(f"{parent.label_word.capitalize()} tried to help, but the {fix.label} was not strong enough.")
            world.say(f"The ship kept drifting until the crew had to turn back and save it for later.")
            world.para()
            world.say(f"Even so, everyone stayed safe, and they learned to pick the right path before rushing.")
            outcome = "failed"

    world.facts.update(
        fighter=fighter,
        driver=driver,
        parent=parent,
        ship=ship,
        quest_entity=q,
        hazard_entity=hz,
        outcome=outcome,
        delay=delay,
        used_fix=(outcome == "fixed"),
    )
    return world


SETTINGS = {
    "orbit": Setting(id="orbit", scene="little moon-jump ship", ship="the moon ship",
                     quest_word="quest", mission="They were on a quest to deliver a star key.",
                     stars="the stars winked like tiny lamps", dark_place="cargo bay",
                     sendoff="they sailed on"),
    "asteroid": Setting(id="asteroid", scene="tiny asteroid rover", ship="the rover",
                        quest_word="quest", mission="They were on a quest to rescue a lost beacon.",
                        stars="the stars floated like silver pebbles", dark_place="rock tunnel",
                        sendoff="they rolled onward"),
    "comet": Setting(id="comet", scene="fast comet skiff", ship="the skiff",
                     quest_word="quest", mission="They were on a quest to bring home a comet map.",
                     stars="the stars streaked by in bright lines", dark_place="shadowed deck",
                     sendoff="they sped away"),
}

QUESTS = {
    "star_key": QuestGoal(id="star_key", label="the star key", need="navigation", distance=2, tags={"key", "quest"}),
    "beacon": QuestGoal(id="beacon", label="the lost beacon", need="navigation", distance=3, tags={"beacon", "quest"}),
    "map": QuestGoal(id="map", label="the comet map", need="navigation", distance=2, tags={"map", "quest"}),
}

HAZARDS = {
    "meteor": Hazard(id="meteor", label="meteor dust", clue="a storm of meteor dust ahead", danger=2, tags={"meteor", "space"}),
    "rift": Hazard(id="rift", label="a drifting rift", clue="a glowing rift in the route", danger=3, tags={"rift", "space"}),
    "signal": Hazard(id="signal", label="a broken signal tower", clue="a broken signal tower blinking wrong", danger=1, tags={"signal", "space"}),
}

FIXES = {
    "stabilizer": Fix(id="stabilizer", label="stabilizer", method="re-tuned the ship and held the route steady", power=3, sense=3, tags={"fix"}),
    "rewind": Fix(id="rewind", label="course rewind switch", method="reset the course and pulled them back on track", power=2, sense=2, tags={"fix"}),
    "patch": Fix(id="patch", label="nav patch", method="patched the map and made the stars line up again", power=1, sense=1, tags={"fix"}),
}

GIRL_NAMES = ["Nova", "Iris", "Mira", "Lyra", "Zuri", "Ada", "Luna"]
BOY_NAMES = ["Milo", "Kai", "Jett", "Rex", "Arlo", "Finn", "Tate"]
TRAITS = ["careful", "steady", "thoughtful", "cautious", "bold"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    hazard: str
    fix: str
    fighter: str
    fighter_type: str
    driver: str
    driver_type: str
    parent: str
    trait: str
    delay: int = 0
    fighter_age: int = 6
    driver_age: int = 7
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
    StoryParams(setting="orbit", quest="star_key", hazard="meteor", fix="stabilizer",
                fighter="Nova", fighter_type="fighter", driver="Milo", driver_type="driver",
                parent="Captain", trait="careful", delay=0, fighter_age=6, driver_age=8),
    StoryParams(setting="asteroid", quest="beacon", hazard="rift", fix="rewind",
                fighter="Kai", fighter_type="fighter", driver="Mira", driver_type="driver",
                parent="Captain", trait="thoughtful", delay=0, fighter_age=7, driver_age=7),
    StoryParams(setting="comet", quest="map", hazard="signal", fix="patch",
                fighter="Lyra", fighter_type="fighter", driver="Rex", driver_type="driver",
                parent="Captain", trait="cautious", delay=1, fighter_age=5, driver_age=6),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    quest: QuestGoal = f["quest"]
    hazard: Hazard = f["hazard_cfg"]
    return [
        f'Write a space adventure story for a child that includes the words "fighter" and "driver" and is about a quest to reach {quest.label}.',
        f"Tell a small quest story set on {setting.ship} where a fighter wants to hurry, a driver spots {hazard.label}, and they choose safety first.",
        f"Write a gentle space story where the quest stays exciting but the crew solves a navigation problem and keeps going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fighter: Entity = f["fighter"]
    driver: Entity = f["driver"]
    setting: Setting = f["setting"]
    quest: QuestGoal = f["quest"]
    hazard: Hazard = f["hazard_cfg"]
    fix: Fix = f["fix"]
    outcome = f["outcome"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {fighter.id}, the fighter, and {driver.id}, the driver. They travel together on {setting.ship} during a quest."
        ),
        QAItem(
            question="What were they trying to do?",
            answer=f"They were trying to complete a quest to reach {quest.label}. The whole trip was about getting there without getting lost."
        ),
        QAItem(
            question=f"What did the driver notice?",
            answer=f"{driver.id} noticed {hazard.clue}. That warning mattered because the ship was in space and the wrong turn could send them drifting."
        ),
    ]
    if outcome == "avoided":
        qa.append(QAItem(
            question="How did they finish the quest?",
            answer=f"{driver.id} slowed things down, so they stayed on course and reached {quest.label} safely. The fighter listened, and the ship kept flying straight under the stars."
        ))
    elif outcome == "fixed":
        qa.append(QAItem(
            question="How did the crew fix the problem?",
            answer=f"{world.get('Parent').label_word.capitalize()} used the {fix.label} and {fix.method}. That made the ship steady again, so the quest could continue."
        ))
        qa.append(QAItem(
            question="What changed by the end?",
            answer=f"The ship stopped drifting and the crew reached {quest.label}. At the end, the stars were calm again and the mission was back on track."
        ))
    else:
        qa.append(QAItem(
            question="Why did the crew turn back?",
            answer=f"The {fix.label} was not strong enough to stop the drifting. Because of that, the crew turned back to keep everyone safe and try the quest again later."
        ))
    return qa


WORLD_KNOWLEDGE = {
    "fighter": [QAItem(
        question="What is a fighter in a space adventure?",
        answer="A fighter is a brave space traveler who acts fast and helps protect the crew. The word can sound strong, but here it is just a role in the story."
    )],
    "driver": [QAItem(
        question="What does a driver do in this story world?",
        answer="A driver steers the vehicle and keeps the group on the right path. In space, that means watching the route and helping the ship stay safe."
    )],
    "quest": [QAItem(
        question="What is a quest?",
        answer="A quest is a mission to find, deliver, or reach something important. It usually has a goal and a challenge along the way."
    )],
    "space": [QAItem(
        question="Why can space trips be tricky?",
        answer="Space can be tricky because there are no roads, and small mistakes can send a ship off course. Travelers have to watch their route carefully."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for topic in ("fighter", "driver", "quest", "space") for q in WORLD_KNOWLEDGE[topic]]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
hazard(H) :- hazard_cfg(H).
real_quest(Q) :- quest(Q).
valid(S,Q,H) :- setting(S), quest(Q), hazard(H), hazard_clue(H), quest_need(Q, navigation).
outcome(avoided) :- careful_driver.
outcome(fixed) :- not careful_driver, can_fix.
outcome(failed) :- not careful_driver, not can_fix.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_need", qid, q.need))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_clue", hid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if fx.sense >= 2:
            lines.append(asp.fact("can_fix", fid))
    lines.append(asp.fact("careful_driver"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested story generation.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure quest with a fighter and a driver.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--driver")
    ap.add_argument("--parent")
    ap.add_argument("--trait", choices=sorted(CAREFUL_TRAITS | {"bold"}))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, hazard = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    fighter = args.name or rng.choice(GIRL_NAMES := ["Nova", "Iris", "Mira", "Lyra", "Zuri", "Ada", "Luna"] + BOY_NAMES := ["Milo", "Kai", "Jett", "Rex", "Arlo", "Finn", "Tate"])
    driver = args.driver or rng.choice([n for n in (["Nova", "Iris", "Mira", "Lyra", "Zuri", "Ada", "Luna"] + ["Milo", "Kai", "Jett", "Rex", "Arlo", "Finn", "Tate"]) if n != fighter])
    parent = args.parent or "Captain"
    trait = args.trait or rng.choice(sorted(CAREFUL_TRAITS | {"bold"}))
    return StoryParams(
        setting=setting, quest=quest, hazard=hazard, fix=fix,
        fighter=fighter, fighter_type="fighter", driver=driver, driver_type="driver",
        parent=parent, trait=trait, delay=rng.randint(0, 1),
        fighter_age=rng.randint(5, 7), driver_age=rng.randint(5, 8)
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("quest", QUESTS), ("hazard", HAZARDS), ("fix", FIXES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting], QUESTS[params.quest], HAZARDS[params.hazard], FIXES[params.fix],
        fighter_name=params.fighter, fighter_type=params.fighter_type,
        driver_name=params.driver, driver_type=params.driver_type,
        parent_name=params.parent, trait=params.trait, delay=params.delay,
        fighter_age=params.fighter_age, driver_age=params.driver_age,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
