#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py
========================================================================

A standalone storyworld for a small cautionary myth:

In an old european village, children know that the Stone Bridge keeps a lantern,
a rope, or a bell for honest travelers. The bridge is watched by a quiet river
spirit. Anyone who borrows one of the bridge-gifts must leave a proper deposit
on the mossy post first. A child is tempted to skip the deposit "just for now."
The spirit answers with fog, slipping, or lost echoes, until the child mends the
wrong by returning the gift, leaving the deposit, and speaking an apology.

The world models a simple mythic rule:
    need + sacred borrowed aid + missing deposit -> bridge displeasure -> danger
    proper deposit + apology + return/respect    -> calm water -> safe ending

Run it
------
    python storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py --aid lantern --deposit silver_coin
    python storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py --task crossing --aid bell
    python storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py --all
    python storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/yesterday_deposit_european_cautionary_myth.py --verify
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
RESPECT_MIN = 2


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
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
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
class Setting:
    id: str
    village: str
    landmark: str
    path: str
    water: str
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
class Task:
    id: str
    need: str
    opening: str
    danger: str
    safe_end: str
    required_tags: set[str] = field(default_factory=set)
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
    comfort_text: str
    capability_tags: set[str] = field(default_factory=set)
    spirit_sign: str = ""
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
class Deposit:
    id: str
    label: str
    phrase: str
    respect: int
    matches: set[str] = field(default_factory=set)
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
    label: str
    phrase: str
    power: int
    action_text: str = ""
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_offense(world: World) -> list[str]:
    bridge = world.get("bridge")
    child = world.get("child")
    if child.meters["borrowed"] < THRESHOLD:
        return []
    if child.meters["deposit_left"] >= THRESHOLD:
        return []
    sig = ("offense", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["displeasure"] += 1
    child.memes["guilt"] += 1
    child.memes["fear"] += 1
    return ["__offense__"]


def _r_hazard(world: World) -> list[str]:
    bridge = world.get("bridge")
    child = world.get("child")
    if bridge.meters["displeasure"] < THRESHOLD:
        return []
    sig = ("hazard", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["hazard"] += 1
    child.meters["stumble"] += 1
    return ["__hazard__"]


def _r_calm(world: World) -> list[str]:
    bridge = world.get("bridge")
    child = world.get("child")
    if child.meters["deposit_left"] < THRESHOLD:
        return []
    if child.meters["apologized"] < THRESHOLD:
        return []
    sig = ("calm", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bridge.meters["displeasure"] = 0.0
    bridge.meters["calm"] += 1
    child.meters["hazard"] = 0.0
    child.memes["relief"] += 1
    child.memes["respect"] += 1
    return ["__calm__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="offense", tag="mythic", apply=_r_offense),
    Rule(name="hazard", tag="physical", apply=_r_hazard),
    Rule(name="calm", tag="mythic", apply=_r_calm),
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


def aid_fits_task(aid: Aid, task: Task) -> bool:
    return task.required_tags <= aid.capability_tags


def proper_deposit(aid: Aid, deposit: Deposit) -> bool:
    return aid.id in deposit.matches and deposit.respect >= RESPECT_MIN


def can_repair(repair: Repair, deposit: Deposit) -> bool:
    return repair.power >= deposit.respect


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for task_id, task in TASKS.items():
            for aid_id, aid in AIDS.items():
                if not aid_fits_task(aid, task):
                    continue
                for dep_id, deposit in DEPOSITS.items():
                    if proper_deposit(aid, deposit):
                        combos.append((setting_id, task_id, aid_id, dep_id))
    return combos


def explain_aid(task: Task, aid: Aid) -> str:
    return (
        f"(No story: {aid.phrase} does not honestly solve the need to {task.need}. "
        f"The borrowed aid must match the task, or the old bridge custom makes no sense.)"
    )


def explain_deposit(aid: Aid, deposit: Deposit) -> str:
    if deposit.respect < RESPECT_MIN:
        return (
            f"(No story: {deposit.phrase} is too slight a deposit for the Stone Bridge. "
            f"The village custom calls for a more respectful token.)"
        )
    return (
        f"(No story: {deposit.phrase} is not the right kind of deposit for borrowing "
        f"{aid.phrase}. The token must fit the bridge-gift in this myth.)"
    )


def explain_repair(repair: Repair, deposit: Deposit) -> str:
    return (
        f"(No story: {repair.phrase} is too small to mend the broken custom after "
        f"such a deposit was skipped. A stronger repair is needed.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["borrowed"] += 1
    propagate(sim, narrate=False)
    return {
        "hazard": sim.get("child").meters["hazard"],
        "displeasure": sim.get("bridge").meters["displeasure"],
    }


def outcome_of(params: "StoryParams") -> str:
    if params.choice == "heed":
        return "averted"
    repaired = can_repair(REPAIRS[params.repair], DEPOSITS[params.deposit])
    return "mended" if repaired else "lost"


def introduce(world: World, child: Entity, elder: Entity) -> None:
    setting = world.setting
    world.say(
        f"In a small european village beside {setting.water}, there stood {setting.landmark}. "
        f"People said the stones listened better than people did."
    )
    world.say(
        f"{child.id} walked there with {child.pronoun('possessive')} {elder.label_word}, "
        f"following {setting.path}. Yesterday the baker had told them once more that the bridge "
        f"kept old gifts for honest need, but only after a proper deposit was laid upon the mossy post."
    )


def establish_custom(world: World, child: Entity, task: Task, aid: Aid, deposit: Deposit) -> None:
    world.say(
        f"That evening's need was plain: {task.opening}. Under the arch of the bridge rested "
        f"{aid.phrase}, ready for any traveler who truly needed it."
    )
    world.say(
        f'"Remember," said {world.get("elder").id}, "whoever borrows the bridge-gift leaves '
        f'{deposit.phrase} as a deposit first. Stones are old, and old things like to be respected."'
    )


def tempt(world: World, child: Entity, aid: Aid, deposit: Deposit) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} looked at {aid.phrase} and then at {deposit.phrase} in {child.pronoun('possessive')} palm. "
        f"The gift seemed near; the custom felt slow."
    )
    world.say(
        f'"It is only for a little while," {child.pronoun()} whispered. '
        f'"I can bring {aid.label} back later and leave the deposit then."'
    )


def warn(world: World, elder: Entity, aid: Aid) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_hazard"] = pred["hazard"]
    world.facts["predicted_displeasure"] = pred["displeasure"]
    child = world.get("child")
    child.memes["warning_heard"] += 1
    world.say(
        f'{elder.id} shook {elder.pronoun("possessive")} head. "Not later. First. '
        f'The river-spirit hears the taking before it hears the excuse. '
        f'If you borrow {aid.label} with empty hands, the bridge will answer."'
    )


def heed(world: World, child: Entity, deposit: Deposit, task: Task, aid: Aid) -> None:
    child.meters["deposit_left"] += 1
    child.memes["respect"] += 1
    world.say(
        f"{child.id} stood still. The cold sound of the water made the warning feel true. "
        f"So {child.pronoun()} laid {deposit.phrase} on the mossy post before touching {aid.label}."
    )
    world.say(
        f"The bridge stayed quiet. No mist rose, no stone shifted, and soon {task.safe_end} with "
        f"{aid.comfort_text} beside {child.pronoun('object')}."
    )


def take_without_deposit(world: World, child: Entity, aid: Aid) -> None:
    child.meters["borrowed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But hurry won. {child.id} snatched up {aid.phrase} without leaving any deposit at all."
    )
    world.say(
        f"At once {aid.spirit_sign}, as if the bridge had opened one old eye."
    )


def trouble(world: World, task: Task) -> None:
    child = world.get("child")
    world.say(
        f"{task.danger}. {child.id} felt the path turn strange under {child.pronoun('possessive')} feet, "
        f"and even the safe part of the world seemed to lean away."
    )


def counsel(world: World, elder: Entity, child: Entity, deposit: Deposit, repair: Repair) -> None:
    child.memes["trust"] += 1
    world.say(
        f'{elder.id} caught {child.id} by the sleeve before the fear could grow bigger. '
        f'"The bridge is not hungry for gold," {elder.pronoun()} said softly. '
        f'"It is hungry for honesty. We mend this by returning what was taken, laying '
        f'{deposit.phrase}, and making {repair.phrase}."'
    )


def mend(world: World, child: Entity, aid: Aid, deposit: Deposit, repair: Repair, task: Task) -> None:
    child.meters["deposit_left"] += 1
    child.meters["apologized"] += 1
    child.meters["repaired"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {child.id} went back to the mossy post, set down {deposit.phrase}, returned {aid.phrase} for one breath, "
        f"and spoke an apology into the cracks between the stones."
    )
    world.say(
        f"Then {child.pronoun()} {repair.action_text}. The water loosened its hard whisper, and the bridge grew calm again."
    )
    world.say(
        f"Only after that did {child.id} borrow {aid.label} the right way, and soon {task.safe_end}."
    )


def fail_to_mend(world: World, child: Entity, repair: Repair, task: Task) -> None:
    world.say(
        f"But fear made {child.id} try the smallest fix. {child.pronoun().capitalize()} {repair.action_text}, "
        f"yet the stones did not forgive so lightly."
    )
    world.say(
        f"The trouble deepened until {task.danger.lower()}, and {child.id} had to turn back empty-handed. "
        f"All night {child.pronoun()} remembered that customs older than people should not be tested for sport."
    )


def ending_image(world: World, child: Entity, deposit: Deposit, aid: Aid, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"Since then, whenever {child.id} passes the bridge, {child.pronoun()} touches the mossy post first. "
            f"Children in the village say even the moonlight falls more gently on stones that are given their due deposit."
        )
    elif outcome == "mended":
        world.say(
            f"After that night, {child.id} never called a promise 'later' when it should be 'now.' "
            f"And in the european village, mothers told the story whenever a child curled a hand too quickly around a borrowed thing."
        )
    else:
        world.say(
            f"By morning the mist had gone, but the lesson remained. In that european village they still say the bridge remembers yesterday, "
            f"and it trusts only the hands that learn respect before need turns sharp."
        )


def tell(
    setting: Setting,
    task: Task,
    aid: Aid,
    deposit: Deposit,
    repair: Repair,
    child_name: str = "Mira",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    choice: str = "skip",
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=["quick", "curious"],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        traits=["patient", "wise"],
    ))
    bridge = world.add(Entity(
        id="bridge",
        kind="thing",
        type="bridge",
        label=setting.landmark,
        role="guardian",
        attrs={"water": setting.water},
    ))
    world.facts["predicted_hazard"] = 0.0
    world.facts["predicted_displeasure"] = 0.0

    introduce(world, child, elder)
    establish_custom(world, child, task, aid, deposit)

    world.para()
    tempt(world, child, aid, deposit)
    warn(world, elder, aid)

    if choice == "heed":
        world.para()
        heed(world, child, deposit, task, aid)
        outcome = "averted"
    else:
        world.para()
        take_without_deposit(world, child, aid)
        trouble(world, task)
        world.para()
        counsel(world, elder, child, deposit, repair)
        if can_repair(repair, deposit):
            mend(world, child, aid, deposit, repair, task)
            outcome = "mended"
        else:
            fail_to_mend(world, child, repair, task)
            outcome = "lost"

    world.para()
    ending_image(world, child, deposit, aid, outcome)

    world.facts.update(
        child=child,
        elder=elder,
        bridge=bridge,
        setting=setting,
        task=task,
        aid=aid,
        deposit=deposit,
        repair=repair,
        choice=choice,
        outcome=outcome,
        bridge_displeased=bridge.meters["displeasure"] >= THRESHOLD,
        deposit_left=child.meters["deposit_left"] >= THRESHOLD,
        apologized=child.meters["apologized"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "alpine_bridge": Setting(
        id="alpine_bridge",
        village="Brunwald",
        landmark="the Stone Bridge of Brunwald",
        path="the goat path above the mill",
        water="the green river",
        tags={"bridge", "river", "european"},
    ),
    "forest_bridge": Setting(
        id="forest_bridge",
        village="Velen",
        landmark="the elder-oak bridge of Velen",
        path="the fern path beneath the pines",
        water="the black stream",
        tags={"bridge", "forest", "european"},
    ),
    "sea_bridge": Setting(
        id="sea_bridge",
        village="Liora",
        landmark="the white bridge over the sea inlet",
        path="the salt path above the harbor",
        water="the silver tide",
        tags={"bridge", "sea", "european"},
    ),
}

TASKS = {
    "crossing": Task(
        id="crossing",
        need="cross the wet bridge at dusk",
        opening="A lamb had strayed to the far bank, and it had to be fetched before full dark",
        danger="Mist rolled across the stones until the far bank vanished",
        safe_end="the lamb was led home across the shining stones",
        required_tags={"light"},
        tags={"crossing", "river", "safety"},
    ),
    "calling": Task(
        id="calling",
        need="call across the valley for help",
        opening="An old cart wheel had sunk in the mud below, and help was needed from the hill farm",
        danger="The child's voice came back in crooked echoes and no helper heard the cry",
        safe_end="the call rang cleanly through the valley and strong hands soon arrived",
        required_tags={"sound"},
        tags={"calling", "echo", "help"},
    ),
    "climbing": Task(
        id="climbing",
        need="climb the steep bank safely",
        opening="A basket of herbs had tipped onto the lower bank, and it had to be gathered before the dew spoiled it",
        danger="The stones grew slick, and the steep bank seemed to slide away from every step",
        safe_end="the herbs were gathered and carried home without a fall",
        required_tags={"grip"},
        tags={"climbing", "bank", "safety"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="the bridge lantern",
        use_text="lit the dark stones with a warm ring of gold",
        comfort_text="its warm circle of light",
        capability_tags={"light"},
        spirit_sign="a pale fog breathed up from the water and swallowed the path-lamps one by one",
        tags={"lantern", "light"},
    ),
    "bell": Aid(
        id="bell",
        label="bell",
        phrase="the bronze bridge bell",
        use_text="sent a clean sound over water and field",
        comfort_text="its brave little ringing",
        capability_tags={"sound"},
        spirit_sign="the river gave back every sound in a bent and mocking voice",
        tags={"bell", "sound"},
    ),
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="the bridge rope",
        use_text="gave the hands something honest to hold",
        comfort_text="the rough rope steady in hand",
        capability_tags={"grip"},
        spirit_sign="the stones slicked over with cold shine, and even the rail felt untrue",
        tags={"rope", "grip"},
    ),
}

DEPOSITS = {
    "silver_coin": Deposit(
        id="silver_coin",
        label="silver coin",
        phrase="a silver coin",
        respect=2,
        matches={"lantern", "bell"},
        tags={"coin", "deposit"},
    ),
    "red_thread": Deposit(
        id="red_thread",
        label="red thread",
        phrase="a braid of red thread",
        respect=2,
        matches={"rope"},
        tags={"thread", "deposit"},
    ),
    "river_bread": Deposit(
        id="river_bread",
        label="river bread",
        phrase="a heel of river bread wrapped in clean cloth",
        respect=3,
        matches={"lantern", "rope", "bell"},
        tags={"bread", "deposit"},
    ),
    "dry_leaf": Deposit(
        id="dry_leaf",
        label="dry leaf",
        phrase="a dry leaf",
        respect=1,
        matches={"lantern"},
        tags={"leaf", "deposit"},
    ),
}

REPAIRS = {
    "apology": Repair(
        id="apology",
        label="apology",
        phrase="an apology",
        power=1,
        action_text="bowed and whispered sorry only once",
        tags={"apology"},
    ),
    "song": Repair(
        id="song",
        label="song",
        phrase="a river-song",
        power=2,
        action_text="sang the old river-song the elders used on feast nights",
        tags={"song"},
    ),
    "candle": Repair(
        id="candle",
        label="candle",
        phrase="a vigil candle",
        power=3,
        action_text="set a vigil candle in the niche by the first stone and waited until the flame held steady",
        tags={"candle"},
    ),
}

GIRL_NAMES = ["Mira", "Elka", "Toma", "Nera", "Sofi", "Lina", "Ana", "Vesa"]
BOY_NAMES = ["Ivo", "Marek", "Niko", "Tarin", "Pavel", "Milan", "Stef", "Luka"]
CHOICES = ["heed", "skip"]


@dataclass
class StoryParams:
    setting: str
    task: str
    aid: str
    deposit: str
    repair: str
    child_name: str
    child_type: str
    elder_type: str
    choice: str
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
    "deposit": [
        (
            "What is a deposit?",
            "A deposit is something you leave behind to show you will return what you borrowed. It is a promise made with an object instead of only with words.",
        )
    ],
    "bridge": [
        (
            "Why do stories give old bridges rules?",
            "In myths, old bridges often stand between safety and danger, so people imagine them as places that remember promises. The rule makes children think before they take a shortcut.",
        )
    ],
    "lantern": [
        (
            "What does a lantern help with?",
            "A lantern helps people see in the dark. Light keeps paths, steps, and edges easier to notice.",
        )
    ],
    "bell": [
        (
            "Why would a bell help someone far away hear you?",
            "A bell makes a sharp ringing sound that travels farther than one small voice. That can help people notice a call for help.",
        )
    ],
    "rope": [
        (
            "Why can a rope make climbing safer?",
            "A rope gives your hands something firm to hold. That can help you keep your balance on a steep or slippery place.",
        )
    ],
    "apology": [
        (
            "Why is an apology important after a wrong choice?",
            "An apology shows that you know the choice was wrong. It is the first step in making trust steady again.",
        )
    ],
    "respect": [
        (
            "What does respect mean in an old custom?",
            "Respect means treating a rule, place, or person as important. In a custom, it means you do the right thing before you take what you want.",
        )
    ],
}
KNOWLEDGE_ORDER = ["deposit", "bridge", "lantern", "bell", "rope", "apology", "respect"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    aid = f["aid"]
    deposit = f["deposit"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a cautionary myth for young children set in a european village, using the words "yesterday" and "deposit".',
            f"Tell a mythic story where {child.id} is tempted to borrow {aid.label} before leaving {deposit.phrase}, but listens to an elder and chooses respect first.",
            f"Write a gentle old-style warning tale about a child who nearly breaks a bridge custom while trying to {task.need}, then does the right thing before trouble begins.",
        ]
    if outcome == "mended":
        return [
            f'Write a cautionary myth for young children that includes the words "yesterday," "deposit," and "european."',
            f"Tell a myth where {child.id} borrows {aid.label} without leaving {deposit.phrase}, angers an old bridge-spirit, and then must mend the wrong with honesty.",
            f"Write an old village warning tale in which a broken custom causes danger until a child returns, apologizes, and leaves the proper deposit.",
        ]
    return [
        f'Write a cautionary myth for young children that includes "yesterday," "deposit," and "european."',
        f"Tell a darker village myth where {child.id} ignores the rule of the bridge, borrows {aid.label} without leaving {deposit.phrase}, and learns that a weak apology cannot mend everything.",
        f"Write a mythic warning story about a child who tests an ancient custom while trying to {task.need} and must turn back after the bridge refuses forgiveness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    task = f["task"]
    aid = f["aid"]
    deposit = f["deposit"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            f"It happens in a small european village beside {world.setting.water}, at {world.setting.landmark}. The old bridge matters because the villagers believe it listens to promises.",
        ),
        (
            "What custom did the elder teach?",
            f"The elder taught that anyone who borrows {aid.phrase} must leave {deposit.phrase} as a deposit first. The custom turns borrowing into a promise instead of a grab.",
        ),
        (
            f"Why did {child.id} want the {aid.label}?",
            f"{child.id} wanted it to {task.need}. That need made the gift tempting enough to challenge the rule.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Why did {child.id} decide to leave the deposit before borrowing the {aid.label}?",
                f"{child.id} listened when {elder.id} warned that the bridge would answer an empty-handed taking. The sound of the water and the old rule made the danger feel real before anything bad happened.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the custom kept and the need met. The quiet bridge itself shows what changed, because no mist or trouble came at all.",
            )
        )
    elif outcome == "mended":
        qa.append(
            (
                f"What happened when {child.id} took the {aid.label} without a deposit?",
                f"{aid.spirit_sign[0].upper()}{aid.spirit_sign[1:]}, and trouble followed at once. The myth says the danger came because the bridge heard the taking before it heard any apology.",
            )
        )
        qa.append(
            (
                f"How was the wrong mended?",
                f"{child.id} returned to the bridge, laid down {deposit.phrase}, and made {repair.phrase}. After that, the bridge grew calm, which showed the old promise had finally been honored.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned not to call a duty 'later' when it should be done now. The danger ended only after honesty came before convenience.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the bridge stay angry?",
                f"It stayed angry because {child.id} had broken the custom and then tried too small a repair. In this myth, old promises are mended by real respect, not by the quickest excuse.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the child turning back empty-handed and wiser. The failed journey proves that some old rules in myths are warnings, not decorations.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"deposit", "bridge", "respect"}
    tags |= set(f["aid"].tags)
    tags |= set(f["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="alpine_bridge",
        task="crossing",
        aid="lantern",
        deposit="silver_coin",
        repair="song",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
        choice="skip",
    ),
    StoryParams(
        setting="forest_bridge",
        task="climbing",
        aid="rope",
        deposit="red_thread",
        repair="apology",
        child_name="Ivo",
        child_type="boy",
        elder_type="grandfather",
        choice="skip",
    ),
    StoryParams(
        setting="sea_bridge",
        task="calling",
        aid="bell",
        deposit="river_bread",
        repair="candle",
        child_name="Lina",
        child_type="girl",
        elder_type="grandmother",
        choice="heed",
    ),
    StoryParams(
        setting="forest_bridge",
        task="calling",
        aid="bell",
        deposit="silver_coin",
        repair="song",
        child_name="Marek",
        child_type="boy",
        elder_type="grandfather",
        choice="skip",
    ),
    StoryParams(
        setting="sea_bridge",
        task="climbing",
        aid="rope",
        deposit="river_bread",
        repair="candle",
        child_name="Sofi",
        child_type="girl",
        elder_type="grandmother",
        choice="skip",
    ),
]


ASP_RULES = r"""
fits(Task, Aid) :- task(Task), aid(Aid), required(Task, Tag), has_tag(Aid, Tag).
needs_all(Task, Aid) :- task(Task), aid(Aid), not missing_req(Task, Aid).
missing_req(Task, Aid) :- required(Task, Tag), not has_tag(Aid, Tag).

proper_deposit(Aid, Deposit) :- deposit(Deposit), aid(Aid),
                                matches(Deposit, Aid),
                                respect(Deposit, R), respect_min(M), R >= M.

valid(Setting, Task, Aid, Deposit) :- setting(Setting), task(Task), aid(Aid), deposit(Deposit),
                                      not missing_req(Task, Aid),
                                      proper_deposit(Aid, Deposit).

outcome(averted) :- choice(heed).
strong_enough :- chosen_repair(Rp), chosen_deposit(Dp), power(Rp, P), respect(Dp, R), P >= R.
outcome(mended) :- choice(skip), strong_enough.
outcome(lost) :- choice(skip), not strong_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        for tag in sorted(task.required_tags):
            lines.append(asp.fact("required", task_id, tag))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for tag in sorted(aid.capability_tags):
            lines.append(asp.fact("has_tag", aid_id, tag))
    for dep_id, deposit in DEPOSITS.items():
        lines.append(asp.fact("deposit", dep_id))
        lines.append(asp.fact("respect", dep_id, deposit.respect))
        for aid_id in sorted(deposit.matches):
            lines.append(asp.fact("matches", dep_id, aid_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("power", repair_id, repair.power))
    lines.append(asp.fact("respect_min", RESPECT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("choice", params.choice),
            asp.fact("chosen_repair", params.repair),
            asp.fact("chosen_deposit", params.deposit),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: valid_combos parity holds ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            mismatches.append((params, py, cl))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, cl in mismatches[:5]:
            print(" ", params, py, cl)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a cautionary myth about borrowing from an old bridge without a proper deposit."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--deposit", choices=DEPOSITS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--choice", choices=CHOICES, help="heed the warning or skip the deposit")
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.aid:
        if not aid_fits_task(AIDS[args.aid], TASKS[args.task]):
            raise StoryError(explain_aid(TASKS[args.task], AIDS[args.aid]))
    if args.aid and args.deposit:
        if not proper_deposit(AIDS[args.aid], DEPOSITS[args.deposit]):
            raise StoryError(explain_deposit(AIDS[args.aid], DEPOSITS[args.deposit]))
    if args.deposit and args.repair:
        if args.choice == "skip" and not can_repair(REPAIRS[args.repair], DEPOSITS[args.deposit]):
            pass

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.task is None or combo[1] == args.task)
        and (args.aid is None or combo[2] == args.aid)
        and (args.deposit is None or combo[3] == args.deposit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, task_id, aid_id, deposit_id = rng.choice(sorted(combos))
    choice = args.choice or rng.choice(CHOICES)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])

    deposit = DEPOSITS[deposit_id]
    repair_options = list(REPAIRS.keys())
    if choice == "skip":
        if args.repair:
            repair_id = args.repair
        else:
            repair_id = rng.choice(sorted(repair_options))
    else:
        if args.repair:
            repair_id = args.repair
        else:
            repair_id = rng.choice(sorted(repair_options))

    if choice == "skip" and args.repair and args.deposit and args.aid:
        if not can_repair(REPAIRS[repair_id], deposit) and args.choice == "skip":
            # allowed: this creates the "lost" ending, so do not reject
            pass

    return StoryParams(
        setting=setting_id,
        task=task_id,
        aid=aid_id,
        deposit=deposit_id,
        repair=repair_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        choice=choice,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        task = TASKS[params.task]
        aid = AIDS[params.aid]
        deposit = DEPOSITS[params.deposit]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not aid_fits_task(aid, task):
        raise StoryError(explain_aid(task, aid))
    if not proper_deposit(aid, deposit):
        raise StoryError(explain_deposit(aid, deposit))
    if params.choice not in CHOICES:
        raise StoryError("(Invalid choice: must be 'heed' or 'skip'.)")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("(Invalid child type.)")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError("(Invalid elder type.)")

    world = tell(
        setting=setting,
        task=task,
        aid=aid,
        deposit=deposit,
        repair=repair,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        choice=params.choice,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, task, aid, deposit) combos:\n")
        for setting_id, task_id, aid_id, deposit_id in combos:
            print(f"  {setting_id:14} {task_id:9} {aid_id:8} {deposit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.task} with {p.aid} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
