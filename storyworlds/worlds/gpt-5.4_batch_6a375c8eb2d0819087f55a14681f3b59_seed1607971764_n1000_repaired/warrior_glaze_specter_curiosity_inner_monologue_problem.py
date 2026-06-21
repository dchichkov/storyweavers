#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/warrior_glaze_specter_curiosity_inner_monologue_problem.py
=====================================================================================

A standalone storyworld for a tiny detective-style tale: a curious child sees a
"specter" in an old room, notices a warrior-shaped clue, studies a strange
glaze, and solves the mystery by testing the world.

The model is classical and state-driven:
- typed entities with physical meters and emotional memes
- a small forward-chaining rule engine
- explicit reasonableness gates over which illusions are plausible
- an inline ASP twin for parity checks
- three world-grounded Q&A sets

Run it
------
python storyworlds/worlds/gpt-5.4/warrior_glaze_specter_curiosity_inner_monologue_problem.py
python storyworlds/worlds/gpt-5.4/warrior_glaze_specter_curiosity_inner_monologue_problem.py --all
python storyworlds/worlds/gpt-5.4/warrior_glaze_specter_curiosity_inner_monologue_problem.py --qa
python storyworlds/worlds/gpt-5.4/warrior_glaze_specter_curiosity_inner_monologue_problem.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    reflective: bool = False
    shape_source: bool = False
    movable_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Setting:
    id: str
    place: str
    mood: str
    rumor: str
    lights: set[str] = field(default_factory=set)
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
class SourceShape:
    id: str
    label: str
    phrase: str
    eerie: str
    clue: str
    size: int
    shape_source: bool = True
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
class GlazeSurface:
    id: str
    label: str
    phrase: str
    shine: str
    difficulty: int
    reflective: bool = True
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
class LightKind:
    id: str
    label: str
    phrase: str
    movement: str
    movable: bool
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
class Method:
    id: str
    label: str
    sense: int
    power: int
    text: str
    reveal: str
    partial: str
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


def _r_specter(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    glaze = world.get("glaze")
    light = world.get("light")
    if room.meters["active_light"] < THRESHOLD:
        return []
    if not source.shape_source or not glaze.reflective:
        return []
    sig = ("specter", world.setting.id, source.id, glaze.id, light.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["specter"] += 1
    room.meters["mystery"] += 1
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["fear"] += 1
    detective.memes["curiosity"] += 2
    helper.memes["wonder"] += 1
    return ["__specter__"]


def _r_solution(world: World) -> list[str]:
    room = world.get("room")
    detective = world.get("detective")
    if detective.meters["identified_cause"] < THRESHOLD:
        return []
    sig = ("solution",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["specter"] = 0.0
    room.meters["mystery"] = 0.0
    detective.memes["relief"] += 1
    detective.memes["pride"] += 1
    helper = world.get("helper")
    helper.memes["relief"] += 1
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="specter", tag="physical", apply=_r_specter),
    Rule(name="solution", tag="epistemic", apply=_r_solution),
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
        for sent in produced:
            world.say(sent)
    return produced


def plausible_illusion(setting: Setting, source: SourceShape, glaze: GlazeSurface,
                       light: LightKind) -> bool:
    return glaze.reflective and source.shape_source and light.id in setting.lights


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_succeeds(method: Method, glaze: GlazeSurface) -> bool:
    return method.power >= glaze.difficulty


def explain_combo_rejection(setting: Setting, source: SourceShape,
                            glaze: GlazeSurface, light: LightKind) -> str:
    if light.id not in setting.lights:
        return (
            f"(No story: {setting.place} does not honestly provide {light.phrase}, "
            f"so the mystery effect would have no believable light source.)"
        )
    if not glaze.reflective:
        return (
            f"(No story: {glaze.phrase} does not throw back enough light to make "
            f"a specter-like image.)"
        )
    if not source.shape_source:
        return (
            f"(No story: {source.phrase} does not make a strong silhouette, so it "
            f"cannot become a spooky clue on the wall.)"
        )
    return "(No story: this combination does not make a believable specter illusion.)"


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it is too weak or careless for this world "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_specter(world: World) -> dict:
    sim = world.copy()
    sim.get("room").meters["active_light"] = 1
    propagate(sim, narrate=False)
    return {
        "specter": sim.get("room").meters["specter"] >= THRESHOLD,
        "mystery": sim.get("room").meters["mystery"],
    }


def introduce(world: World, detective: Entity, helper: Entity, caretaker: Entity) -> None:
    world.say(
        f"{detective.id} loved old rooms the way other children loved toy boxes. "
        f"When {detective.pronoun()} visited {world.setting.place} with {helper.id} "
        f"and {detective.pronoun('possessive')} {caretaker.label_word}, "
        f"{detective.pronoun()} noticed every crack, every shadow, and every little clue."
    )
    world.say(
        f"The place felt {world.setting.mood}, and {caretaker.label_word} quietly said "
        f"that people whispered about {world.setting.rumor}."
    )


def notice_clues(world: World, detective: Entity, helper: Entity,
                 source: SourceShape, glaze: GlazeSurface) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"Near the far wall stood {source.phrase}. Beside it was {glaze.phrase}, "
        f"and its {glaze.shine} kept catching {detective.id}'s eye."
    )
    world.say(
        f'{helper.id} leaned close and whispered, "Do you think the specter is real?"'
    )


def inner_monologue(world: World, detective: Entity, source: SourceShape,
                    glaze: GlazeSurface) -> None:
    detective.memes["inner_voice"] += 1
    world.say(
        f'{detective.id} did not answer at once. Inside, {detective.pronoun()} thought, '
        f'"A specter in a room full of clues? Maybe. But {source.label} and that '
        f'{glaze.label} look as if they are trying to tell me something."'
    )


def light_arrives(world: World, detective: Entity, helper: Entity,
                  source: SourceShape, light: LightKind) -> None:
    world.get("room").meters["active_light"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Then {light.phrase} slipped across the room. It {light.movement}, and suddenly "
        f"{source.eerie} stretched over the wall like a tall specter."
    )
    if detective.memes["fear"] >= THRESHOLD:
        world.say(
            f"{helper.id} grabbed {detective.id}'s sleeve, but {detective.id} stared harder "
            f"instead of running."
        )


def inspect(world: World, detective: Entity, source: SourceShape, glaze: GlazeSurface) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} walked closer, step by careful step. On the surface of the "
        f"{glaze.label}, {detective.pronoun()} saw a bent little copy of {source.clue}."
    )


def choose_method(world: World, detective: Entity, method: Method,
                  light: LightKind, glaze: GlazeSurface) -> None:
    detective.memes["problem_solving"] += 1
    world.say(
        f'{detective.id} took a slow breath. Inside, {detective.pronoun()} thought, '
        f'"If I change one clue at a time, the room will answer me."'
    )
    world.say(method.text.format(light=light.label, glaze=glaze.label, detective=detective.id))


def apply_method(world: World, detective: Entity, helper: Entity, caretaker: Entity,
                 source: SourceShape, glaze: GlazeSurface, light: LightKind,
                 method: Method) -> None:
    world.facts["test_method"] = method.id
    if method.id == "mirror_test":
        detective.meters["tested_light"] += 1
        if light.movable:
            detective.meters["moved_light"] += 1
    elif method.id == "cover_glaze":
        detective.meters["covered_glaze"] += 1
    elif method.id == "follow_beam":
        detective.meters["traced_beam"] += 1

    solved = method_succeeds(method, glaze)
    if solved:
        detective.meters["identified_cause"] += 1
        propagate(world, narrate=False)
        world.say(method.reveal.format(source=source.label, glaze=glaze.label, light=light.label))
        world.say(
            f'"It is not a specter," {detective.id} said. "It is {source.clue} bouncing '
            f'off the glaze when the {light.label} hits it just so."'
        )
        caretaker.memes["pride"] += 1
        helper.memes["admiration"] += 1
    else:
        detective.meters["partial_cause"] += 1
        room = world.get("room")
        room.meters["specter"] = 0.0
        room.meters["mystery"] = 1.0
        world.say(method.partial.format(source=source.label, glaze=glaze.label, light=light.label))
        world.say(
            f"{caretaker.label_word.capitalize()} drew the curtain and made the room bright again. "
            f'The shape was gone, and {detective.id} knew the answer was close, even if not every part '
            f"of it had been named yet."
        )


def ending(world: World, detective: Entity, helper: Entity, caretaker: Entity,
           source: SourceShape, glaze: GlazeSurface, light: LightKind,
           solved: bool) -> None:
    if solved:
        world.say(
            f"{helper.id} laughed with relief. {caretaker.label_word.capitalize()} called "
            f"{detective.id} a fine little detective, and even {world.setting.place} stopped "
            f"feeling haunted."
        )
        world.say(
            f"On the way out, {detective.id} glanced back once more. The warrior was only a statue, "
            f"the glaze was only glaze, and the old specter had turned into a solved clue."
        )
    else:
        world.say(
            f"{helper.id} stayed close, but not because of fear anymore. The room felt quieter now, "
            f"as if it had agreed to wait for daylight and one more clever look."
        )
        world.say(
            f"On the way out, {detective.id} glanced back at the warrior and the glaze and smiled a small, "
            f"serious smile. A good detective did not have to know everything at once to know where the truth lived."
        )


def tell(setting: Setting, source_cfg: SourceShape, glaze_cfg: GlazeSurface,
         light_cfg: LightKind, method_cfg: Method,
         detective_name: str = "Nia", detective_type: str = "girl",
         helper_name: str = "Owen", helper_type: str = "boy",
         caretaker_type: str = "mother") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label=detective_name,
        role="detective",
        traits=["curious", "careful"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["loyal"],
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        label="the grown-up",
        role="caretaker",
        traits=["calm"],
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=setting.place,
    ))
    source = world.add(Entity(
        id="source",
        type="source",
        label=source_cfg.label,
        shape_source=source_cfg.shape_source,
    ))
    glaze = world.add(Entity(
        id="glaze",
        type="surface",
        label=glaze_cfg.label,
        reflective=glaze_cfg.reflective,
    ))
    light = world.add(Entity(
        id="light",
        type="light",
        label=light_cfg.label,
        movable_light=light_cfg.movable,
    ))

    room.meters["active_light"] = 0.0
    room.meters["specter"] = 0.0
    room.meters["mystery"] = 0.0
    detective.meters["identified_cause"] = 0.0
    detective.meters["partial_cause"] = 0.0
    detective.meters["tested_light"] = 0.0
    detective.meters["covered_glaze"] = 0.0
    detective.meters["traced_beam"] = 0.0
    detective.meters["moved_light"] = 0.0
    detective.memes["curiosity"] = 1.0
    detective.memes["fear"] = 0.0
    detective.memes["inner_voice"] = 0.0
    detective.memes["problem_solving"] = 0.0
    helper.memes["wonder"] = 0.0
    helper.memes["admiration"] = 0.0
    caretaker.memes["pride"] = 0.0

    world.facts.update(
        detective=detective,
        helper=helper,
        caretaker=caretaker,
        setting=setting,
        source_cfg=source_cfg,
        glaze_cfg=glaze_cfg,
        light_cfg=light_cfg,
        method_cfg=method_cfg,
    )

    introduce(world, detective, helper, caretaker)
    notice_clues(world, detective, helper, source_cfg, glaze_cfg)

    world.para()
    inner_monologue(world, detective, source_cfg, glaze_cfg)
    pred = predict_specter(world)
    world.facts["predicted_specter"] = pred["specter"]
    light_arrives(world, detective, helper, source_cfg, light_cfg)

    world.para()
    inspect(world, detective, source_cfg, glaze_cfg)
    choose_method(world, detective, method_cfg, light_cfg, glaze_cfg)
    apply_method(world, detective, helper, caretaker, source_cfg, glaze_cfg, light_cfg, method_cfg)

    world.para()
    solved = detective.meters["identified_cause"] >= THRESHOLD
    ending(world, detective, helper, caretaker, source_cfg, glaze_cfg, light_cfg, solved)

    world.facts.update(
        outcome="solved" if solved else "secured",
        solved=solved,
        specter_seen=pred["specter"],
        method_success=solved,
        room=room,
        source=source,
        glaze=glaze,
        light=light,
    )
    return world


SETTINGS = {
    "gallery": Setting(
        id="gallery",
        place="the old gallery",
        mood="hushed and dusty",
        rumor="a night specter near the back wall",
        lights={"moonbeam", "hall_lantern"},
        tags={"gallery", "mystery"},
    ),
    "tower_room": Setting(
        id="tower_room",
        place="the stone tower room",
        mood="echoey and cold",
        rumor="a pale specter that appears by the stairs",
        lights={"moonbeam", "hall_lantern"},
        tags={"tower", "mystery"},
    ),
    "museum_hall": Setting(
        id="museum_hall",
        place="the little museum hall",
        mood="quiet and watchful",
        rumor="a whispering specter after sunset",
        lights={"hall_lantern", "window_glow"},
        tags={"museum", "mystery"},
    ),
}

SOURCES = {
    "warrior_statue": SourceShape(
        id="warrior_statue",
        label="warrior statue",
        phrase="a stone warrior statue with a chipped spear",
        eerie="the warrior's long shadow",
        clue="the warrior statue's outline",
        size=3,
        tags={"warrior", "statue"},
    ),
    "warrior_painting": SourceShape(
        id="warrior_painting",
        label="painted warrior",
        phrase="a painting of a warrior in dark red armor",
        eerie="the painted warrior's sharp helmet shape",
        clue="the painted warrior's helmet and shoulders",
        size=2,
        tags={"warrior", "painting"},
    ),
    "armor_stand": SourceShape(
        id="armor_stand",
        label="armor stand",
        phrase="an old armor stand with a crooked plume",
        eerie="the armor's narrow face and plume",
        clue="the armor stand's plume and shoulders",
        size=2,
        tags={"armor", "warrior"},
    ),
}

GLAZES = {
    "blue_tiles": GlazeSurface(
        id="blue_tiles",
        label="blue glaze",
        phrase="a row of tiles painted with a glassy blue glaze",
        shine="blue glaze shimmer",
        difficulty=1,
        tags={"glaze", "tiles"},
    ),
    "jar_glaze": GlazeSurface(
        id="jar_glaze",
        label="green glaze jar",
        phrase="a tall jar sealed in green glaze",
        shine="green glaze shine",
        difficulty=2,
        tags={"glaze", "jar"},
    ),
    "crackle_glaze": GlazeSurface(
        id="crackle_glaze",
        label="crackle glaze cabinet",
        phrase="a cabinet door coated in pale crackle glaze",
        shine="pale crackle-glaze gleam",
        difficulty=3,
        tags={"glaze", "cabinet"},
    ),
}

LIGHTS = {
    "moonbeam": LightKind(
        id="moonbeam",
        label="moonbeam",
        phrase="a moonbeam",
        movement="slid through the high window",
        movable=False,
        tags={"moon", "light"},
    ),
    "hall_lantern": LightKind(
        id="hall_lantern",
        label="hall lantern",
        phrase="the hall lantern",
        movement="swung from a hook when the door opened",
        movable=True,
        tags={"lantern", "light"},
    ),
    "window_glow": LightKind(
        id="window_glow",
        label="window glow",
        phrase="the last window glow",
        movement="thinned and shifted across the floorboards",
        movable=False,
        tags={"window", "light"},
    ),
}

METHODS = {
    "mirror_test": Method(
        id="mirror_test",
        label="mirror test",
        sense=3,
        power=3,
        text="{detective} raised and lowered the {light}, watching the wall and the {glaze} together.",
        reveal="As the light changed, the specter stretched and shrank exactly with the shape of the {source}. The {glaze} was throwing the picture back into the room.",
        partial="The shape wavered when the light changed, which told {detective} that light and the {glaze} mattered. But the whole trick was still too quick to name at once.",
        qa_text="tested the changing light against the glaze",
        tags={"detective", "reflection"},
    ),
    "cover_glaze": Method(
        id="cover_glaze",
        label="cover glaze",
        sense=3,
        power=2,
        text="{detective} asked for a scarf, then gently covered part of the {glaze} and looked back at the wall.",
        reveal="The specter broke apart the moment the {glaze} was covered. That proved the shiny glaze was the sneaky middle part of the trick.",
        partial="Part of the shape disappeared when the {glaze} was covered, but some dim edges still confused the room. {detective} had found the hiding place of the clue, though not every step of it.",
        qa_text="covered the glaze to see what changed",
        tags={"detective", "glaze"},
    ),
    "follow_beam": Method(
        id="follow_beam",
        label="follow beam",
        sense=2,
        power=1,
        text="{detective} crouched low and followed the path of the {light} from the floor to the wall, then back toward the {glaze}.",
        reveal="By tracing the beam carefully, {detective} saw that the light reached the {source} first and the {glaze} second. The room was making a picture, not hiding a ghost.",
        partial="Following the beam led {detective} near the truth, but the last jump from the {source} to the strange wall shape stayed slippery in the dim light.",
        qa_text="followed the beam of light to its clues",
        tags={"detective", "light"},
    ),
    "shout_at_it": Method(
        id="shout_at_it",
        label="shout at it",
        sense=1,
        power=0,
        text="{detective} shouted at the wall, but shouting was not a real test.",
        reveal="",
        partial="",
        qa_text="",
        tags={"bad"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    source: str
    glaze: str
    light: str
    method: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    caretaker_type: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for source_id, source in SOURCES.items():
            for glaze_id, glaze in GLAZES.items():
                for light_id, light in LIGHTS.items():
                    if plausible_illusion(setting, source, glaze, light):
                        combos.append((setting_id, source_id, glaze_id, light_id))
    return combos


KNOWLEDGE = {
    "specter": [
        (
            "What is a specter?",
            "A specter is a spooky-looking figure people talk about in stories. Sometimes it is only a shadow or reflection that looks strange."
        )
    ],
    "glaze": [
        (
            "What is glaze?",
            "Glaze is a shiny coating baked onto clay or tile. It can catch and bounce light because it is smooth and glossy."
        )
    ],
    "reflection": [
        (
            "How can a shiny surface make a strange shape on a wall?",
            "A shiny surface can bounce light in a new direction. If the light hits an object first, the bounced light can carry part of that object's shape."
        )
    ],
    "lantern": [
        (
            "Why do moving lights make shadows change?",
            "When a light moves, the angle of the light changes too. That makes shadows and reflections stretch, shrink, or slide across a wall."
        )
    ],
    "moon": [
        (
            "Can moonlight make shadows indoors?",
            "Yes. If moonlight comes through a window, it can make long shadows and bright patches inside a dark room."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tests ideas. A good detective does not just guess; a good detective checks what really happened."
        )
    ],
    "warrior": [
        (
            "What is a warrior?",
            "A warrior is a fighter from long ago or from a story. In a museum or picture, a warrior can be shown with armor, a shield, or a spear."
        )
    ],
}
KNOWLEDGE_ORDER = ["specter", "glaze", "reflection", "lantern", "moon", "detective", "warrior"]

CURATED = [
    StoryParams(
        setting="gallery",
        source="warrior_statue",
        glaze="blue_tiles",
        light="moonbeam",
        method="cover_glaze",
        detective_name="Nia",
        detective_type="girl",
        helper_name="Owen",
        helper_type="boy",
        caretaker_type="mother",
    ),
    StoryParams(
        setting="tower_room",
        source="armor_stand",
        glaze="jar_glaze",
        light="hall_lantern",
        method="mirror_test",
        detective_name="Milo",
        detective_type="boy",
        helper_name="June",
        helper_type="girl",
        caretaker_type="father",
    ),
    StoryParams(
        setting="museum_hall",
        source="warrior_painting",
        glaze="crackle_glaze",
        light="window_glow",
        method="follow_beam",
        detective_name="Ava",
        detective_type="girl",
        helper_name="Ben",
        helper_type="boy",
        caretaker_type="mother",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    source = f["source_cfg"]
    glaze = f["glaze_cfg"]
    light = f["light_cfg"]
    outcome = f["outcome"]
    if outcome == "solved":
        return [
            f'Write a detective story for a young child that includes the words "warrior", "glaze", and "specter".',
            f"Tell a mystery where {detective.id} sees a specter in {world.setting.place}, studies {source.phrase} and {glaze.phrase}, and solves the puzzle by testing the {light.label}.",
            "Write a gentle detective tale with curiosity, inner monologue, and problem solving, ending with a spooky clue explained in a calm way.",
        ]
    return [
        f'Write a detective story for a young child that includes the words "warrior", "glaze", and "specter".',
        f"Tell a mystery where {detective.id} nearly solves a specter sighting in {world.setting.place} by following clues from {source.label} and {glaze.label}.",
        "Write a child-friendly mystery with curiosity and inner monologue, where the room grows calm even before every detail is fully explained.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    caretaker = f["caretaker"]
    source = f["source_cfg"]
    glaze = f["glaze_cfg"]
    light = f["light_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a curious child who acts like a little detective, with {helper.id} nearby and {caretaker.label_word} watching calmly."
        ),
        (
            "What made the room seem spooky?",
            f"The room looked spooky when {light.phrase} crossed it and turned {source.clue} into a tall wall shape. That shape looked like a specter because the light and the shiny glaze changed it."
        ),
        (
            f"Why did {detective.id} pay attention to the glaze?",
            f"{detective.id} noticed that the glaze was especially shiny and kept catching the eye. That made {detective.pronoun('object')} suspect it was part of the trick, not just part of the room."
        ),
        (
            f"What method did {detective.id} use to investigate?",
            f"{detective.id} {method.qa_text}. {detective.pronoun().capitalize()} used a real test instead of guessing, which is why the mystery began to open up."
        ),
    ]
    if outcome == "solved":
        qa.append(
            (
                "What was the specter really?",
                f"It was not a real ghost at all. The shape came from {source.clue} and bounced off the {glaze.label} when the {light.label} hit it the right way."
            )
        )
        qa.append(
            (
                f"How did {detective.id} feel at the end?",
                f"{detective.id} felt relieved and proud. The room stopped feeling haunted because the scary shape had turned into a clue with an answer."
            )
        )
    else:
        qa.append(
            (
                "Did the children make the room safe?",
                f"Yes. They made the shape disappear and learned that the light and glaze were involved, even though the whole trick was not fully named yet. That turned fear into careful thinking."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with the room calm again and {detective.id} still thinking like a detective. The mystery shrank because the clues had been narrowed down to the warrior, the light, and the glaze."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"specter", "glaze", "detective"}
    if "warrior" in f["source_cfg"].tags:
        tags.add("warrior")
    if f["light_cfg"].id == "hall_lantern":
        tags.add("lantern")
    if f["light_cfg"].id == "moonbeam":
        tags.add("moon")
    tags.add("reflection")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("reflective", ent.reflective),
                                 ("shape_source", ent.shape_source),
                                 ("movable_light", ent.movable_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
plausible(S, So, G, L) :- setting(S), source(So), glaze(G), light(L),
                          allows(S, L), reflective(G), shape_source(So).

sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.

solved(M, G) :- method(M), glaze(G), power(M, P), difficulty(G, D), P >= D.
secured(M, G) :- sensible(M), glaze(G), not solved(M, G).

outcome(solved) :- chosen_method(M), chosen_glaze(G), solved(M, G).
outcome(secured) :- chosen_method(M), chosen_glaze(G), not solved(M, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for light in sorted(setting.lights):
            lines.append(asp.fact("allows", setting_id, light))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.shape_source:
            lines.append(asp.fact("shape_source", source_id))
    for glaze_id, glaze in GLAZES.items():
        lines.append(asp.fact("glaze", glaze_id))
        if glaze.reflective:
            lines.append(asp.fact("reflective", glaze_id))
        lines.append(asp.fact("difficulty", glaze_id, glaze.difficulty))
    for light_id in LIGHTS:
        lines.append(asp.fact("light", light_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show plausible/4."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_glaze", params.glaze),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    method = METHODS[params.method]
    glaze = GLAZES[params.glaze]
    return "solved" if method_succeeds(method, glaze) else "secured"


def asp_verify() -> int:
    rc = 0

    py_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py_combos == clingo_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in plausible combo gate:")
        if clingo_combos - py_combos:
            print("  only in clingo:", sorted(clingo_combos - py_combos))
        if py_combos - clingo_combos:
            print("  only in python:", sorted(py_combos - clingo_combos))

    py_methods = {m.id for m in sensible_methods()}
    clingo_methods = set(asp_sensible_methods())
    if py_methods == clingo_methods:
        print(f"OK: sensible methods match ({sorted(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(clingo_methods)} python={sorted(py_methods)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during verify seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style specter mystery storyworld. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--glaze", choices=GLAZES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the plausible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nia", "Ava", "Mira", "Lila", "Ruby", "Tess", "June", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Finn", "Leo", "Eli", "Max"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))

    if args.setting and args.source and args.glaze and args.light:
        setting = SETTINGS[args.setting]
        source = SOURCES[args.source]
        glaze = GLAZES[args.glaze]
        light = LIGHTS[args.light]
        if not plausible_illusion(setting, source, glaze, light):
            raise StoryError(explain_combo_rejection(setting, source, glaze, light))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.source is None or c[1] == args.source)
        and (args.glaze is None or c[2] == args.glaze)
        and (args.light is None or c[3] == args.light)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, glaze_id, light_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    helper_pool = GIRL_NAMES if helper_type == "girl" else BOY_NAMES
    helper_choices = [n for n in helper_pool if n != detective_name] or list(helper_pool)
    helper_name = args.helper_name or rng.choice(helper_choices)
    caretaker_type = args.caretaker_type or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting_id,
        source=source_id,
        glaze=glaze_id,
        light=light_id,
        method=method_id,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        caretaker_type=caretaker_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.glaze not in GLAZES:
        raise StoryError(f"(Unknown glaze: {params.glaze})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    setting = SETTINGS[params.setting]
    source = SOURCES[params.source]
    glaze = GLAZES[params.glaze]
    light = LIGHTS[params.light]
    method = METHODS[params.method]

    if not plausible_illusion(setting, source, glaze, light):
        raise StoryError(explain_combo_rejection(setting, source, glaze, light))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))

    world = tell(
        setting=setting,
        source_cfg=source,
        glaze_cfg=glaze,
        light_cfg=light,
        method_cfg=method,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        caretaker_type=params.caretaker_type,
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
        print(asp_program("", "#show plausible/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} plausible (setting, source, glaze, light) combos:\n")
        for setting, source, glaze, light in combos:
            print(f"  {setting:11} {source:16} {glaze:14} {light}")
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
            header = f"### {p.detective_name}: {p.setting}, {p.source}, {p.glaze}, {p.light}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
