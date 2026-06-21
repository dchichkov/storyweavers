#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trouser_patriotic_yank_transformation_reconciliation_suspense_space.py
=================================================================================================

A standalone story world about two young cadets preparing a patriotic space
celebration. In their hurry, one child gives a line a yank, a precious parade
item slips from a trouser pocket, suspense rises as it drifts into danger, a
little robot transforms to help, and the friends reconcile in the end.

Run it
------
    python storyworlds/worlds/gpt-5.4/trouser_patriotic_yank_transformation_reconciliation_suspense_space.py
    python storyworlds/worlds/gpt-5.4/trouser_patriotic_yank_transformation_reconciliation_suspense_space.py --setting ring_station --item parade_flag --form wing
    python storyworlds/worlds/gpt-5.4/trouser_patriotic_yank_transformation_reconciliation_suspense_space.py --setting moon_hangar --form wing
    python storyworlds/worlds/gpt-5.4/trouser_patriotic_yank_transformation_reconciliation_suspense_space.py --all
    python storyworlds/worlds/gpt-5.4/trouser_patriotic_yank_transformation_reconciliation_suspense_space.py --verify
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    celebration: str
    zone: str
    suspense_line: str
    sky_line: str
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
class ParadeItem:
    id: str
    label: str
    phrase: str
    difficulty: int
    fits: set[str]
    ending_use: str
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
class Form:
    id: str
    label: str
    reaches: set[str]
    power: int
    transform_text: str
    move_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "zone": setting.zone,
            "delay": 0,
            "retrieved": False,
            "predicted_drift": False,
            "apology": False,
            "forgiven": False,
            "outcome": "",
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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


def _r_drift_alarm(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["drifting"] < THRESHOLD:
        return out
    sig = ("drift_alarm", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("station").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__suspense__")
    return out


def _r_robot_retrieve(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    robot = world.get("robot")
    if item.meters["drifting"] < THRESHOLD or robot.meters["transformed"] < THRESHOLD:
        return out
    sig = ("robot_retrieve", item.id, robot.attrs.get("form"))
    if sig in world.fired:
        return out
    if robot.attrs.get("zone") != item.attrs.get("zone"):
        return out
    need = int(item.attrs.get("difficulty", 0)) + int(world.facts.get("delay", 0))
    if int(robot.attrs.get("power", 0)) < need:
        return out
    world.fired.add(sig)
    item.meters["drifting"] = 0.0
    item.meters["rescued"] += 1
    world.get("station").meters["danger"] = 0.0
    robot.meters["charge"] -= need
    for kid in world.kids():
        kid.memes["relief"] += 1
    out.append("__retrieved__")
    return out


CAUSAL_RULES = [
    Rule(name="drift_alarm", tag="physical", apply=_r_drift_alarm),
    Rule(name="robot_retrieve", tag="physical", apply=_r_robot_retrieve),
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


def item_fits(setting: Setting, item: ParadeItem) -> bool:
    return setting.zone in item.fits


def form_fits(setting: Setting, form: Form) -> bool:
    return setting.zone in form.reaches


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            if not item_fits(setting, item):
                continue
            for fid, form in FORMS.items():
                if form_fits(setting, form):
                    combos.append((sid, iid, fid))
    return combos


def rescue_success(item: ParadeItem, form: Form, delay: int) -> bool:
    return form.power >= item.difficulty + delay


def outcome_of(params: "StoryParams") -> str:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.form not in FORMS:
        raise StoryError("(No story: one of the requested options is unknown.)")
    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    form = FORMS[params.form]
    if not item_fits(setting, item):
        raise StoryError(explain_item_rejection(setting, item))
    if not form_fits(setting, form):
        raise StoryError(explain_form_rejection(setting, form))
    return "retrieved" if rescue_success(item, form, params.delay) else "delayed"


def predict_drift(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["drifting"] += 1
    propagate(sim, narrate=False)
    return {
        "drifting": item.meters["drifting"] >= THRESHOLD,
        "danger": sim.get("station").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting, item: ParadeItem) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"Far above the clouds, {a.id} and {b.id} were helping decorate {setting.place} "
        f"for {setting.celebration}. It was a patriotic day on the station, and every window "
        f"showed tiny stars blinking beyond the glass."
    )
    world.say(
        f"{a.id} kept {item.phrase} tucked in a trouser pocket so it would be ready at the right moment, "
        f"while {b.id} checked the ribbons and little lights."
    )
    world.say(
        f"Their helper robot, Pip, rolled beside them on quiet wheels, waiting for instructions from "
        f"{a.id}'s {parent.label_word}."
    )


def build_tension(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["impatience"] += 1
    world.say(
        f"A silver streamer had snagged above the deck, and the launch bell for {setting.celebration} "
        f"was almost ready to ring."
    )
    world.say(
        f'"If I give the line one quick yank, it will straighten," {a.id} said.'
    )
    pred = predict_drift(world)
    world.facts["predicted_drift"] = pred["drifting"]
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "Please do not. If the line jerks, something could '
        f'slip loose and drift toward the {setting.zone.replace("_", " ")}."'
    )


def accident(world: World, a: Entity, b: Entity, item: ParadeItem, setting: Setting) -> None:
    a.memes["defiance"] += 1
    a.memes["guilt"] += 1
    b.memes["hurt"] += 1
    item_ent = world.get("item")
    item_ent.meters["drifting"] += 1
    item_ent.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the bell gave a tiny warning chime, and {a.id} hurried anyway. {a.pronoun().capitalize()} gave the line a yank."
    )
    world.say(
        f"At once, {item.phrase} popped from {a.pronoun('possessive')} trouser pocket, spun in the air, "
        f"and drifted toward the {setting.zone.replace('_', ' ')}."
    )
    world.say(setting.suspense_line)


def transform_robot(world: World, a: Entity, b: Entity, form: Form) -> None:
    robot = world.get("robot")
    robot.meters["transformed"] += 1
    robot.attrs["form"] = form.id
    robot.attrs["zone"] = world.facts["zone"]
    robot.attrs["power"] = form.power
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(
        f'"Pip, {form.label} mode!" {b.id} cried.'
    )
    world.say(
        f"{form.transform_text} {form.move_text}"
    )
    propagate(world, narrate=False)


def rescue_scene(world: World, form: Form, item: ParadeItem) -> None:
    item_ent = world.get("item")
    if item_ent.meters["rescued"] >= THRESHOLD:
        world.facts["retrieved"] = True
        world.say(
            f"For one long second, nobody breathed. Then Pip reached {item.phrase}, caught it neatly, "
            f"and brought it back before it could vanish."
        )
        world.say(
            f"{breeze_end(world.setting)} The little robot set {item.label} gently into {breeze_holder(world)} hands."
        )
        return
    world.facts["retrieved"] = False
    world.say(
        f"Pip darted after {item.phrase}, but the chase took too long. The tiny machine stretched as far as it could, "
        f"then blinked a low-charge light."
    )
    world.say(
        f"The item slipped beyond reach, and an adult crew member sealed the area before anyone could try again."
    )


def apology_and_reconciliation(world: World, a: Entity, b: Entity) -> None:
    a.memes["remorse"] += 1
    b.memes["forgiveness"] += 1
    a.memes["fear"] = 0.0
    b.memes["fear"] = 0.0
    world.facts["apology"] = True
    world.facts["forgiven"] = True
    world.say(
        f'"I should have listened," {a.id} said softly. "I wanted to hurry, and my yank made the trouble."'
    )
    world.say(
        f"{b.id} looked at {a.id} for a moment, then gave {a.pronoun('object')} a small nod. "
        f'"I was scared," {b.pronoun()} said, "but we can fix the rest together."'
    )


def bright_ending(world: World, a: Entity, b: Entity, item: ParadeItem, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"Together they clipped {item.phrase} into place, and when the parade lights came on, "
        f"{item.ending_use}."
    )
    world.say(
        f"{parent.label_word.capitalize()} squeezed both their shoulders. {world.setting.sky_line} "
        f"{a.id} and {b.id} waved at the ships outside, no longer pulling against each other, but working side by side."
    )


def mended_ending(world: World, a: Entity, b: Entity, item: ParadeItem, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"So {a.id} and {b.id} hurried to the craft table and made a new parade piece from foil stars and bright ribbon. "
        f"It was not the same {item.label}, but they built it together."
    )
    world.say(
        f"When the parade lights rose, their handmade piece shimmered just as proudly. "
        f"{parent.label_word.capitalize()} smiled, and {world.setting.sky_line} "
        f"The friends stood shoulder to shoulder, wiser now and close again."
    )


def breeze_end(setting: Setting) -> str:
    return {
        "ring_station": "Outside the window, a blue planet turned slowly below.",
        "moon_hangar": "Beyond the hangar glass, the moon dust shone like silver flour.",
        "comet_bridge": "Past the bridge dome, a comet tail glimmered in the dark.",
    }.get(setting.id, "Outside, the stars waited in the dark.")


def breeze_holder(world: World) -> str:
    return world.get("friend").id


def tell(
    setting: Setting,
    item_cfg: ParadeItem,
    form_cfg: Form,
    instigator_name: str = "Nova",
    instigator_gender: str = "girl",
    friend_name: str = "Orin",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(setting)
    world.facts["delay"] = delay

    a = world.add(Entity(id=instigator_name, kind="character", type=instigator_gender, role="instigator"))
    b = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    station = world.add(Entity(id="station", type="station", label=setting.place))
    item = world.add(
        Entity(
            id="item",
            type="parade_item",
            label=item_cfg.label,
            attrs={"difficulty": item_cfg.difficulty, "zone": setting.zone},
        )
    )
    robot = world.add(
        Entity(
            id="robot",
            type="robot",
            label="Pip",
            attrs={"form": "rolled", "zone": "", "power": 0},
        )
    )
    robot.meters["charge"] = float(form_cfg.power)

    introduce(world, a, b, parent, setting, item_cfg)
    world.para()
    build_tension(world, a, b, setting)
    accident(world, a, b, item_cfg, setting)
    world.para()
    transform_robot(world, a, b, form_cfg)
    rescue_scene(world, form_cfg, item_cfg)
    world.para()
    apology_and_reconciliation(world, a, b)
    world.para()
    if world.facts["retrieved"]:
        bright_ending(world, a, b, item_cfg, parent)
        outcome = "retrieved"
    else:
        mended_ending(world, a, b, item_cfg, parent)
        outcome = "delayed"

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        form_cfg=form_cfg,
        instigator=a,
        friend=b,
        parent=parent,
        robot=robot,
        outcome=outcome,
        transformed=robot.meters["transformed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "ring_station": Setting(
        id="ring_station",
        place="the Ring Station promenade",
        celebration="Orbit Day",
        zone="airlock_lane",
        suspense_line="Red safety lights blinked along the floor, and the open practice lane beyond the rail looked very far away.",
        sky_line="Outside the glass, little shuttles looped in bright circles around the station.",
        tags={"space", "station", "airlock"},
    ),
    "moon_hangar": Setting(
        id="moon_hangar",
        place="the Moon Hangar gallery",
        celebration="Home-World Song Night",
        zone="vent_tunnel",
        suspense_line="The small vent tunnel hummed softly, and the dark opening seemed ready to swallow the drifting prize.",
        sky_line="Past the high dome, the moon plain stretched pale and quiet under the stars.",
        tags={"space", "moon", "vent"},
    ),
    "comet_bridge": Setting(
        id="comet_bridge",
        place="the Comet Bridge hall",
        celebration="Star Banner Evening",
        zone="antenna_rig",
        suspense_line="Thin bridge lights flashed, and beyond them the antenna rig trembled over the deep dark of space.",
        sky_line="Far away, the comet tail streamed like a glowing scarf across the sky.",
        tags={"space", "comet", "antenna"},
    ),
}

ITEMS = {
    "parade_flag": ParadeItem(
        id="parade_flag",
        label="parade flag",
        phrase="the little parade flag",
        difficulty=1,
        fits={"airlock_lane", "antenna_rig"},
        ending_use="its bright colors floated over the children like a happy wave",
        tags={"flag", "patriotic"},
    ),
    "anthem_chip": ParadeItem(
        id="anthem_chip",
        label="anthem chip",
        phrase="the anthem chip",
        difficulty=2,
        fits={"vent_tunnel", "airlock_lane"},
        ending_use="the station speakers played the warm anthem tune right on time",
        tags={"anthem", "music", "patriotic"},
    ),
    "star_patch": ParadeItem(
        id="star_patch",
        label="star patch",
        phrase="the stitched star patch",
        difficulty=1,
        fits={"vent_tunnel", "antenna_rig", "airlock_lane"},
        ending_use="the glowing patch shone from the front banner like a tiny brave moon",
        tags={"patch", "patriotic"},
    ),
    "trophy_orb": ParadeItem(
        id="trophy_orb",
        label="trophy orb",
        phrase="the heavy trophy orb",
        difficulty=3,
        fits={"antenna_rig"},
        ending_use="the polished orb gleamed at the head of the parade",
        tags={"trophy"},
    ),
}

FORMS = {
    "wing": Form(
        id="wing",
        label="wing",
        reaches={"airlock_lane"},
        power=2,
        transform_text="Pip unfolded bright silver wings from its sides and became a tiny darting flyer.",
        move_text="Its little engine whirred as it zipped into the lane.",
        qa_text="changed into a flying form and zipped after the drifting item",
        tags={"robot", "flying"},
    ),
    "crawler": Form(
        id="crawler",
        label="crawler",
        reaches={"vent_tunnel"},
        power=2,
        transform_text="Pip tucked in its wheels and stretched into a long crawler with soft magnetic pads.",
        move_text="It clicked into the tunnel and hugged the metal walls.",
        qa_text="changed into a crawler form and climbed through the vent",
        tags={"robot", "crawler"},
    ),
    "climber": Form(
        id="climber",
        label="climber",
        reaches={"antenna_rig"},
        power=3,
        transform_text="Pip opened four neat gripping legs and turned into a careful climber.",
        move_text="It stepped out along the rig, holding tight the whole way.",
        qa_text="changed into a climber form and walked out along the rig",
        tags={"robot", "climber"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Lumi", "Tala", "Ari", "Zia", "Vela", "Rin"]
BOY_NAMES = ["Orin", "Jax", "Kian", "Sol", "Taro", "Nico", "Pax", "Leo"]


@dataclass
class StoryParams:
    setting: str
    item: str
    form: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    parent: str
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


def explain_item_rejection(setting: Setting, item: ParadeItem) -> str:
    return (
        f"(No story: {item.phrase} would not plausibly drift into the {setting.zone.replace('_', ' ')} at "
        f"{setting.place}. Pick an item that fits that kind of space hazard.)"
    )


def explain_form_rejection(setting: Setting, form: Form) -> str:
    zones = ", ".join(sorted(z.replace("_", " ") for z in form.reaches))
    return (
        f"(No story: the {form.label} form can reach {zones}, not the "
        f"{setting.zone.replace('_', ' ')} in this setting.)"
    )


KNOWLEDGE = {
    "patriotic": [
        (
            "What does patriotic mean?",
            "Patriotic means showing love and pride for your home place. In a story like this, it can mean songs, flags, and happy colors for a special day."
        )
    ],
    "airlock": [
        (
            "What is an airlock?",
            "An airlock is a special room or passage on a spaceship or station. It helps people move safely between inside air and outer space."
        )
    ],
    "vent": [
        (
            "What is a vent tunnel?",
            "A vent tunnel is a small passage that lets air move through a place. Small things can slip inside if people are not careful."
        )
    ],
    "antenna": [
        (
            "What does an antenna do in space?",
            "An antenna helps a ship or station send and receive signals. It is an important piece of space equipment."
        )
    ],
    "robot": [
        (
            "What is a transforming robot?",
            "A transforming robot is a machine that can change shape to do different jobs. One form might fly, while another crawls or climbs."
        )
    ],
    "flag": [
        (
            "What is a parade flag for?",
            "A parade flag is waved or hung up during a celebration. Its colors help people feel proud and festive."
        )
    ],
    "anthem": [
        (
            "What is an anthem?",
            "An anthem is a special song for a place or a group. People sing or play it on important days."
        )
    ],
    "patch": [
        (
            "What is a patch on clothing?",
            "A patch is a small piece sewn onto clothes or a uniform. It can show a team sign, a star, or a special badge."
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry matters because it shows you understand the hurt or trouble you caused. A true apology helps people begin to trust each other again."
        )
    ],
}
KNOWLEDGE_ORDER = ["patriotic", "airlock", "vent", "antenna", "robot", "flag", "anthem", "patch", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    setting = f["setting"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short Space Adventure story for a 3-to-5-year-old that includes the words '
        f'"trouser", "patriotic", and "yank".'
    )
    if outcome == "retrieved":
        return [
            base,
            f"Tell a gentle suspense story where {a.id} and {b.id} are getting ready for {setting.celebration}, "
            f"{a.id} gives a line a yank, a drifting {item.label} causes worry, a robot transforms, and the friends reconcile.",
            f"Write a space-station celebration story with transformation, suspense, and reconciliation, ending with the children using the rescued {item.label} in the parade.",
        ]
    return [
        base,
        f"Tell a Space Adventure where {a.id}'s hurry sends a {item.label} drifting into danger, a robot transforms to help but is too late, and the children reconcile by making something new together.",
        f"Write a child-facing story with suspense and reconciliation in which a patriotic celebration nearly goes wrong after one quick yank.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two young cadets"
    if a.type == "boy" and b.type == "boy":
        return "two young cadets"
    return "two young cadets"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    parent = f["parent"]
    setting = f["setting"]
    item = f["item_cfg"]
    form = f["form_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, plus their helper robot Pip. They were getting ready for {setting.celebration} on {setting.place}."
        ),
        (
            f"Why was the day called patriotic?",
            f"It was a patriotic celebration because the children were honoring their home world with parade lights, songs, and special decorations. The proud mood made the missing {item.label} feel even more important."
        ),
        (
            f"What mistake did {a.id} make?",
            f"{a.id} tried to hurry and gave the line a yank after {b.id} warned against it. That sudden pull made {item.phrase} slip from a trouser pocket and drift toward danger."
        ),
        (
            "Why did the story feel suspenseful?",
            f"It felt suspenseful because the item was drifting toward the {setting.zone.replace('_', ' ')}, and nobody knew if Pip could reach it in time. The blinking lights and waiting parade bell made the danger feel close."
        ),
        (
            "How did the robot transform?",
            f"Pip {form.qa_text}. The transformation mattered because that form was the right shape for the {setting.zone.replace('_', ' ')}."
        ),
    ]
    if f["outcome"] == "retrieved":
        qa.append(
            (
                f"How was the problem solved?",
                f"Pip brought the {item.label} back before it was lost. After that, {a.id} apologized and {b.id} forgave {a.pronoun('object')}, so the friends could finish the celebration together."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the rescued {item.label} shining in the parade. The ending image shows that the danger passed and the friendship was mended too."
            )
        )
    else:
        qa.append(
            (
                "What happened when Pip could not get the item back in time?",
                f"The original {item.label} was lost, so the children made a new parade piece together. That changed the ending from a rescue story into a making-things-right story."
            )
        )
        qa.append(
            (
                "How did the friends reconcile?",
                f"{a.id} admitted the mistake and said sorry, and {b.id} chose to help instead of staying upset. Working side by side on the new decoration brought them close again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"patriotic", "robot", "apology"}
    setting = f["setting"]
    item = f["item_cfg"]
    if setting.zone == "airlock_lane":
        tags.add("airlock")
    elif setting.zone == "vent_tunnel":
        tags.add("vent")
    elif setting.zone == "antenna_rig":
        tags.add("antenna")
    tags |= item.tags
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_setting(S, I) :- zone_of(S, Z), fits(I, Z).
form_ok(S, F)      :- zone_of(S, Z), reaches(F, Z).
valid(S, I, F)     :- setting(S), item(I), form(F), fits_setting(S, I), form_ok(S, F).

need(I, D, Need)   :- difficulty(I, D), delay(Dly), Need = D + Dly.
retrieved          :- chosen_setting(S), chosen_item(I), chosen_form(F),
                      valid(S, I, F), difficulty(I, D), delay(Dly), power(F, P), P >= D + Dly.
outcome(retrieved) :- retrieved.
outcome(delayed)   :- not retrieved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("zone_of", sid, setting.zone))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("difficulty", iid, item.difficulty))
        for z in sorted(item.fits):
            lines.append(asp.fact("fits", iid, z))
    for fid, form in FORMS.items():
        lines.append(asp.fact("form", fid))
        lines.append(asp.fact("power", fid, form.power))
        for z in sorted(form.reaches):
            lines.append(asp.fact("reaches", fid, z))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_form", params.form),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="ring_station",
        item="parade_flag",
        form="wing",
        instigator="Nova",
        instigator_gender="girl",
        friend="Orin",
        friend_gender="boy",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        setting="moon_hangar",
        item="anthem_chip",
        form="crawler",
        instigator="Mira",
        instigator_gender="girl",
        friend="Jax",
        friend_gender="boy",
        parent="father",
        delay=1,
    ),
    StoryParams(
        setting="comet_bridge",
        item="star_patch",
        form="climber",
        instigator="Sol",
        instigator_gender="boy",
        friend="Lumi",
        friend_gender="girl",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        setting="antenna_rig" if False else "comet_bridge",
        item="trophy_orb",
        form="climber",
        instigator="Pax",
        instigator_gender="boy",
        friend="Tala",
        friend_gender="girl",
        parent="father",
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a patriotic space celebration, a rash yank, a transforming robot, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time pressure before the robot can reach the item")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item:
        if not item_fits(SETTINGS[args.setting], ITEMS[args.item]):
            raise StoryError(explain_item_rejection(SETTINGS[args.setting], ITEMS[args.item]))
    if args.setting and args.form:
        if not form_fits(SETTINGS[args.setting], FORMS[args.form]):
            raise StoryError(explain_form_rejection(SETTINGS[args.setting], FORMS[args.form]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.form is None or combo[2] == args.form)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, item, form = rng.choice(sorted(combos))
    instigator_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    instigator = pick_name(rng, instigator_gender)
    friend = pick_name(rng, friend_gender, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        item=item,
        form=form,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.form not in FORMS:
        raise StoryError(f"(No story: unknown form '{params.form}'.)")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    form = FORMS[params.form]

    if not item_fits(setting, item):
        raise StoryError(explain_item_rejection(setting, item))
    if not form_fits(setting, form):
        raise StoryError(explain_form_rejection(setting, form))

    world = tell(
        setting=setting,
        item_cfg=item,
        form_cfg=form,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
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

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        try:
            py = outcome_of(p)
            cl = asp_outcome(p)
        except StoryError:
            bad += 1
            continue
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Smoke test failed: generated sample was incomplete.)")
        with io.StringIO() as buf:
            old_stdout = sys.stdout
            try:
                sys.stdout = buf
                emit(sample, trace=False, qa=False, header="")
            finally:
                sys.stdout = old_stdout
        print("OK: generation smoke test passed.")
    except Exception as err:  # pragma: no cover
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
        print(f"{len(combos)} compatible (setting, item, form) combos:\n")
        for setting, item, form in combos:
            out = "retrieved" if rescue_success(ITEMS[item], FORMS[form], args.delay or 0) else "delayed"
            print(f"  {setting:12} {item:12} {form:8} [{out} if delay={args.delay or 0}]")
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
            header = f"### {p.instigator} & {p.friend}: {p.setting}, {p.item}, {p.form}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
