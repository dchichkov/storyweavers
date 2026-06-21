#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py
=============================================================================

A standalone storyworld for a small farm-at-dusk mystery: two children notice a
pig-themed light glowing weakly, hear a strange sound, and solve the mystery
together. The world focuses on teamwork, sound effects, and simple problem
solving in a child-facing mystery style.

The word "pig-dim" appears in-story as the family's playful nickname for the
pig-shaped light when its glow goes weak.

Run it
------
    python storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py
    python storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py --place barn --light pig_nose_lantern --source piglet_snuffle
    python storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py --solution reseat_plug
    python storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py --qa --json
    python storyworlds/worlds/gpt-5.4/pig_dim_teamwork_sound_effects_problem_solving.py --verify
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
    opening: str
    dark_corner: str
    affords_lights: set[str] = field(default_factory=set)
    affords_sources: set[str] = field(default_factory=set)
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
class LightConfig:
    id: str
    label: str
    phrase: str
    location: str
    power: str
    dim_wording: str
    bright_wording: str
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
class SourceConfig:
    id: str
    label: str
    sound: str
    sound_word: str
    cause_power: str
    clue: str
    reveal: str
    fix_hint: str
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
class Solution:
    id: str
    fix_power: str
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
        return [e for e in self.entities.values() if e.role in {"listener", "spotter"}]

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


def _r_dim_light(world: World) -> list[str]:
    out: list[str] = []
    light = world.get("light")
    if light.meters["brightness"] >= THRESHOLD:
        return out
    sig = ("dim", "light")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("place").meters["darkness"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__dim__")
    return out


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["curious"] += 1
    out.append("__noise__")
    return out


def _r_teamwork(world: World) -> list[str]:
    a = world.get("kid_a")
    b = world.get("kid_b")
    if a.meters["heard_clue"] < THRESHOLD or b.meters["saw_clue"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["brave"] += 1
    b.memes["brave"] += 1
    world.facts["team_plan_ready"] = True
    return ["__team__"]


def _r_solved(world: World) -> list[str]:
    light = world.get("light")
    if light.meters["brightness"] < THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("place").meters["darkness"] = 0.0
    world.get("source").meters["noise"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    world.facts["solved"] = True
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="dim_light", tag="physical", apply=_r_dim_light),
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="solved", tag="physical", apply=_r_solved),
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


def compatible(place: Place, light: LightConfig, source: SourceConfig, solution: Solution) -> bool:
    return (
        light.id in place.affords_lights
        and source.id in place.affords_sources
        and light.power == source.cause_power
        and solution.fix_power == light.power
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES.values():
        for light in LIGHTS.values():
            for source in SOURCES.values():
                for solution in SOLUTIONS.values():
                    if compatible(place, light, source, solution):
                        combos.append((place.id, light.id, source.id, solution.id))
    return sorted(combos)


def explain_rejection(place: Place, light: LightConfig, source: SourceConfig, solution: Solution) -> str:
    if light.id not in place.affords_lights:
        return (
            f"(No story: {light.label} does not belong in {place.label}. "
            f"Pick a light that fits that place.)"
        )
    if source.id not in place.affords_sources:
        return (
            f"(No story: the clue source {source.label} does not fit {place.label}. "
            f"Pick a sound source that could really be there.)"
        )
    if light.power != source.cause_power:
        return (
            f"(No story: {source.label} would not make a {light.label} go dim. "
            f"The cause and the kind of light must match.)"
        )
    if solution.fix_power != light.power:
        return (
            f"(No story: {solution.id} is the wrong fix for a {light.power}-powered light. "
            f"Choose the matching repair.)"
        )
    return "(No story: this combination is unreasonable.)"


def predict_fix(world: World, solution: Solution) -> dict:
    sim = world.copy()
    apply_fix(sim, solution, narrate=False)
    light = sim.get("light")
    return {
        "bright": light.meters["brightness"] >= THRESHOLD,
        "darkness": sim.get("place").meters["darkness"],
    }


def introduce(world: World, a: Entity, b: Entity, caretaker: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["curious"] += 1
    world.say(
        f"At dusk, {a.id} and {b.id} were helping {caretaker.label_word} close up {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"They loved pretending they were tiny detectives, especially when the evening felt full of little secrets."
    )


def present_mystery(world: World, a: Entity, b: Entity, light_cfg: LightConfig, source_cfg: SourceConfig) -> None:
    light = world.get("light")
    source = world.get("source")
    light.meters["brightness"] = 0.3
    source.meters["noise"] = 1.0
    world.facts["sound_word"] = source_cfg.sound_word
    propagate(world, narrate=False)
    world.say(
        f"But when they reached {light_cfg.location}, {light_cfg.dim_wording}. "
        f'"There it is again," whispered {b.id}, as a strange sound went {source_cfg.sound} from the shadows.'
    )
    world.say(
        f"{a.id} had a nickname for the weak little glow: pig-dim. "
        f"It made the place feel more mysterious than scary."
    )


def choose_jobs(world: World, a: Entity, b: Entity) -> None:
    a.memes["focus"] += 1
    b.memes["focus"] += 1
    world.say(
        f'"Let\'s solve it together," said {a.id}. "{a.id}, you listen. I\'ll look," said {b.id}.'
        if random.choice([True, False])
        else f'"Let\'s solve it together," said {a.id}. "{b.id}, you listen. I\'ll look," said {a.id}.'
    )


def investigate(world: World, a: Entity, b: Entity, source_cfg: SourceConfig) -> None:
    a.meters["heard_clue"] += 1
    b.meters["saw_clue"] += 1
    world.facts["heard_direction"] = source_cfg.sound_word
    world.facts["spotted_clue"] = source_cfg.clue
    propagate(world, narrate=False)
    world.say(
        f"{a.id} stood still and listened. {source_cfg.sound.capitalize()} came from {source_cfg.clue}."
    )
    world.say(
        f"{b.id} crouched low, peered under a board, and spotted what the sound meant: {source_cfg.reveal}."
    )


def reason_together(world: World, a: Entity, b: Entity, light_cfg: LightConfig, source_cfg: SourceConfig, solution: Solution) -> None:
    pred = predict_fix(world, solution)
    world.facts["predicted_bright"] = pred["bright"]
    world.say(
        f'"The sound is the clue," said {a.id}. "{source_cfg.fix_hint}"'
    )
    if pred["bright"]:
        world.say(
            f'{b.id} nodded. "If we do that, {light_cfg.label} should shine bright again."'
        )


def apply_fix(world: World, solution: Solution, narrate: bool = True) -> None:
    light = world.get("light")
    source = world.get("source")
    light.meters["brightness"] = 1.2
    source.meters["noise"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(solution.text)


def finish_story(world: World, a: Entity, b: Entity, light_cfg: LightConfig, caretaker: Entity) -> None:
    world.say(
        f"{light_cfg.bright_wording}. The mystery sound was gone, and the dark corner no longer seemed puzzling at all."
    )
    world.say(
        f'{caretaker.label_word.capitalize()} smiled when {a.id} and {b.id} explained what they had found. '
        f'"You used careful eyes, careful ears, and teamwork," {caretaker.pronoun()} said.'
    )
    world.say(
        f"Hand in hand, the two detectives walked back through the warm evening glow, proud that they had solved the little mystery together."
    )


def tell(
    place: Place,
    light_cfg: LightConfig,
    source_cfg: SourceConfig,
    solution: Solution,
    kid_a_name: str = "Mina",
    kid_a_type: str = "girl",
    kid_b_name: str = "Theo",
    kid_b_type: str = "boy",
    caretaker_type: str = "father",
) -> World:
    world = World(place)
    a = world.add(Entity(id="kid_a", kind="character", type=kid_a_type, label=kid_a_name, role="listener"))
    a.id = kid_a_name
    world.entities["kid_a"] = a
    del world.entities[kid_a_name]
    b = world.add(Entity(id="kid_b", kind="character", type=kid_b_type, label=kid_b_name, role="spotter"))
    b.id = kid_b_name
    world.entities["kid_b"] = b
    del world.entities[kid_b_name]
    caretaker = world.add(Entity(id="caretaker", kind="character", type=caretaker_type, label="the caretaker", role="caretaker"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    light = world.add(Entity(id="light", kind="thing", type="light", label=light_cfg.label, attrs={"power": light_cfg.power}))
    source = world.add(Entity(id="source", kind="thing", type="source", label=source_cfg.label))
    world.facts["solved"] = False
    world.facts["team_plan_ready"] = False
    world.facts["sound_word"] = ""
    world.facts["heard_direction"] = ""
    world.facts["spotted_clue"] = ""

    introduce(world, a, b, caretaker, place)
    present_mystery(world, a, b, light_cfg, source_cfg)

    world.para()
    choose_jobs(world, a, b)
    investigate(world, a, b, source_cfg)
    reason_together(world, a, b, light_cfg, source_cfg, solution)

    world.para()
    apply_fix(world, solution, narrate=True)
    finish_story(world, a, b, light_cfg, caretaker)

    world.facts.update(
        place=place,
        light_cfg=light_cfg,
        source_cfg=source_cfg,
        solution=solution,
        kid_a=a,
        kid_b=b,
        caretaker=caretaker,
        sound=source_cfg.sound,
    )
    return world


PLACES = {
    "barn": Place(
        id="barn",
        label="the hay barn",
        opening="The rafters smelled of sweet hay, and the last gold light from outside made long stripes on the floor.",
        dark_corner="the pig pen door",
        affords_lights={"pig_pen_lamp", "pig_nose_lantern"},
        affords_sources={"chain_clink", "piglet_snuffle"},
        tags={"barn", "farm"},
    ),
    "shed": Place(
        id="shed",
        label="the tool shed",
        opening="Hooks, boots, and little wooden boxes made neat rows along the walls, but the back shelf was already turning dusky.",
        dark_corner="the back shelf",
        affords_lights={"pig_nose_lantern", "pig_sign_light"},
        affords_sources={"piglet_snuffle", "cart_rattle"},
        tags={"shed", "tools"},
    ),
    "gate": Place(
        id="gate",
        label="the farm gate",
        opening="The path home curled past the fence, and evening wind brushed the tall grass with a hush-hush sound.",
        dark_corner="the latch post",
        affords_lights={"pig_sign_light", "pig_pen_lamp"},
        affords_sources={"chain_clink", "cart_rattle"},
        tags={"gate", "path"},
    ),
}

LIGHTS = {
    "pig_pen_lamp": LightConfig(
        id="pig_pen_lamp",
        label="the pig-pen lamp",
        phrase="a round lamp above the pig pen with pink painted ears",
        location="the little pig pen door",
        power="plug",
        dim_wording="the pig-pen lamp was only making a weak peach-colored blur",
        bright_wording="The pig-pen lamp bloomed into a warm, steady light above the straw",
        tags={"lamp", "plug"},
    ),
    "pig_nose_lantern": LightConfig(
        id="pig_nose_lantern",
        label="the pig-nose lantern",
        phrase="a lantern with a pig snout painted on the front glass",
        location="the peg by the wall",
        power="battery",
        dim_wording="the pig-nose lantern glowed as faintly as a sleepy firefly",
        bright_wording="The pig-nose lantern shone bright and round, lighting the floorboards all the way to the wall",
        tags={"lantern", "battery"},
    ),
    "pig_sign_light": LightConfig(
        id="pig_sign_light",
        label="the pig sign light",
        phrase="a small light clipped above the painted pig sign",
        location="the painted pig sign",
        power="plug",
        dim_wording="the pig sign light flickered in tiny tired blinks",
        bright_wording="The pig sign light steadied into a cheerful glow over the gate",
        tags={"sign", "plug"},
    ),
}

SOURCES = {
    "chain_clink": SourceConfig(
        id="chain_clink",
        label="the loose gate chain",
        sound="clink-clink",
        sound_word="clinking",
        cause_power="plug",
        clue="the hook where the cord crossed the chain",
        reveal="the chain had tugged the cord loose from its socket",
        fix_hint="The chain must have pulled the plug."
        ,
        tags={"sound", "chain", "plug"},
    ),
    "cart_rattle": SourceConfig(
        id="cart_rattle",
        label="the bumping feed cart",
        sound="rattle-rattle",
        sound_word="rattling",
        cause_power="plug",
        clue="the wheel tracks near the wall outlet",
        reveal="the little cart had bumped the cord until the plug slipped halfway out",
        fix_hint="That rattly cart must have knocked the plug loose.",
        tags={"sound", "cart", "plug"},
    ),
    "piglet_snuffle": SourceConfig(
        id="piglet_snuffle",
        label="the snuffling piglet",
        sound="snuffle-snuffle",
        sound_word="snuffling",
        cause_power="battery",
        clue="the tiny hoofprints under the lantern peg",
        reveal="a curious piglet had bumped the lantern, and its battery door had popped loose",
        fix_hint="The lantern needs its battery door snapped back tight.",
        tags={"sound", "piglet", "battery"},
    ),
}

SOLUTIONS = {
    "reseat_plug": Solution(
        id="reseat_plug",
        fix_power="plug",
        text="Together they followed the cord, pushed the plug in snug, and watched the weak light gather itself into a glow.",
        qa_text="They pushed the loose plug back in snugly.",
        tags={"plug", "fix"},
    ),
    "snap_battery": Solution(
        id="snap_battery",
        fix_power="battery",
        text="Together they held the lantern still, pressed the battery door closed with a click, and the pale glow brightened at once.",
        qa_text="They snapped the loose battery door shut.",
        tags={"battery", "fix"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "June", "Poppy", "Nora", "Ava", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Eli", "Noah", "Sam", "Leo", "Max"]


@dataclass
class StoryParams:
    place: str = ""
    light: str = ""
    source: str = ""
    solution: str = ""
    kid_a_name: str = ""
    kid_a_type: str = "girl"
    kid_b_name: str = ""
    kid_b_type: str = "boy"
    caretaker_type: str = "father"
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
    f = world.facts
    a = f["kid_a"]
    b = f["kid_b"]
    place = f["place"]
    light = f["light_cfg"]
    source = f["source_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "pig-dim" and takes place in {place.label}.',
        f"Tell a teamwork story where {a.id} and {b.id} hear {source.sound} near {light.label}, investigate together, and solve the problem.",
        f"Write a child-facing mystery with sound effects, clue finding, and a bright ending where two children figure out why a pig-themed light has gone dim.",
    ]


KNOWLEDGE = {
    "plug": [
        (
            "What does a plug do?",
            "A plug carries electricity from the wall to a lamp or other machine. If the plug is loose, the lamp may not work right."
        )
    ],
    "battery": [
        (
            "What does a battery do?",
            "A battery stores energy inside it and gives that energy to a light or toy. If the battery connection is loose, the light can grow dim."
        )
    ],
    "sound": [
        (
            "Why can sounds help you solve a mystery?",
            "Sounds can tell you where something is and what it might be doing. Listening carefully gives you clues before you even see the answer."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful when solving a problem?",
            "One person may notice something the other person misses. When people share clues and ideas, they can solve the problem faster and more carefully."
        )
    ],
    "piglet": [
        (
            "Why do piglets make snuffling sounds?",
            "Piglets use their noses to sniff and explore. Their snuffling sound happens when they puff air in and out while they search around."
        )
    ],
    "chain": [
        (
            "Why does a chain make a clinking sound?",
            "A chain is made of hard metal links. When the links tap each other, they make a clink-clink sound."
        )
    ],
    "cart": [
        (
            "Why does a cart rattle?",
            "A small cart can rattle when its wheels bump over boards or stones. Loose parts shake and make a noisy sound."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet. You solve it by noticing clues and thinking carefully about what they mean."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "sound", "teamwork", "plug", "battery", "piglet", "chain", "cart"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["kid_a"]
    b = f["kid_b"]
    place = f["place"]
    light = f["light_cfg"]
    source = f["source_cfg"]
    solution = f["solution"]
    caretaker = f["caretaker"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children helping in {place.label}. They become little detectives when they notice the light and the strange sound."
        ),
        (
            "What was the mystery?",
            f"The mystery was why {light.label} had gone dim and why they kept hearing {source.sound} nearby. The weak glow and the odd noise seemed connected, so the children treated them as one puzzle."
        ),
        (
            f"How did {a.id} and {b.id} work together?",
            f"They split the job instead of guessing. One listened carefully for the sound, and the other searched for a clue, so their teamwork turned a spooky moment into a solvable problem."
        ),
        (
            "What clue helped them solve it?",
            f"They noticed {source.clue}, and that clue led them to the real cause: {source.reveal}. The sound pointed them in the right direction before they ever touched the light."
        ),
        (
            "How did they fix the problem?",
            f"{solution.qa_text} That worked because the trouble matched the kind of power the light used, so the glow came back strong."
        ),
        (
            "How did the story end?",
            f"It ended with {light.label} shining brightly again while the mystery sound stopped. {caretaker.label_word.capitalize()} praised the children for using careful ears, careful eyes, and teamwork."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery", "sound", "teamwork"}
    tags |= set(f["light_cfg"].tags)
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["solution"].tags)
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
    for key, ent in world.entities.items():
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
        lines.append(f"  {key:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="barn",
        light="pig_nose_lantern",
        source="piglet_snuffle",
        solution="snap_battery",
        kid_a_name="Mina",
        kid_a_type="girl",
        kid_b_name="Theo",
        kid_b_type="boy",
        caretaker_type="father",
    ),
    StoryParams(
        place="gate",
        light="pig_sign_light",
        source="chain_clink",
        solution="reseat_plug",
        kid_a_name="Nora",
        kid_a_type="girl",
        kid_b_name="Ben",
        kid_b_type="boy",
        caretaker_type="mother",
    ),
    StoryParams(
        place="shed",
        light="pig_sign_light",
        source="cart_rattle",
        solution="reseat_plug",
        kid_a_name="Ivy",
        kid_a_type="girl",
        kid_b_name="Max",
        kid_b_type="boy",
        caretaker_type="father",
    ),
    StoryParams(
        place="barn",
        light="pig_pen_lamp",
        source="chain_clink",
        solution="reseat_plug",
        kid_a_name="Lila",
        kid_a_type="girl",
        kid_b_name="Finn",
        kid_b_type="boy",
        caretaker_type="mother",
    ),
]

ASP_RULES = r"""
compatible(Place, Light, Source, Solution) :-
    place(Place), light(Light), source(Source), solution(Solution),
    affords_light(Place, Light),
    affords_source(Place, Source),
    light_power(Light, P),
    source_power(Source, P),
    solution_power(Solution, P).

chosen_valid :- chosen_place(P), chosen_light(L), chosen_source(S), chosen_solution(Sol),
                compatible(P, L, S, Sol).

outcome(solved) :- chosen_valid.
outcome(stumped) :- not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES.values():
        lines.append(asp.fact("place", place.id))
        for light_id in sorted(place.affords_lights):
            lines.append(asp.fact("affords_light", place.id, light_id))
        for source_id in sorted(place.affords_sources):
            lines.append(asp.fact("affords_source", place.id, source_id))
    for light in LIGHTS.values():
        lines.append(asp.fact("light", light.id))
        lines.append(asp.fact("light_power", light.id, light.power))
    for source in SOURCES.values():
        lines.append(asp.fact("source", source.id))
        lines.append(asp.fact("source_power", source.id, source.cause_power))
    for solution in SOLUTIONS.values():
        lines.append(asp.fact("solution", solution.id))
        lines.append(asp.fact("solution_power", solution.id, solution.fix_power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_solution", params.solution),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES.get(params.place)
    light = LIGHTS.get(params.light)
    source = SOURCES.get(params.source)
    solution = SOLUTIONS.get(params.solution)
    if not place or not light or not source or not solution:
        return "stumped"
    return "solved" if compatible(place, light, source, solution) else "stumped"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for:", params)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny teamwork mystery about a dim pig-themed light, strange sounds, and a shared solution."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--solution", choices=sorted(SOLUTIONS))
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--kid-a")
    ap.add_argument("--kid-b")
    ap.add_argument("--kid-a-type", choices=["girl", "boy"])
    ap.add_argument("--kid-b-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    light_id = args.light
    source_id = args.source
    solution_id = args.solution

    if place_id and place_id not in PLACES:
        raise StoryError(f"(Unknown place: {place_id})")
    if light_id and light_id not in LIGHTS:
        raise StoryError(f"(Unknown light: {light_id})")
    if source_id and source_id not in SOURCES:
        raise StoryError(f"(Unknown source: {source_id})")
    if solution_id and solution_id not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {solution_id})")

    if place_id and light_id and source_id and solution_id:
        place = PLACES[place_id]
        light = LIGHTS[light_id]
        source = SOURCES[source_id]
        solution = SOLUTIONS[solution_id]
        if not compatible(place, light, source, solution):
            raise StoryError(explain_rejection(place, light, source, solution))

    combos = [
        combo
        for combo in valid_combos()
        if (place_id is None or combo[0] == place_id)
        and (light_id is None or combo[1] == light_id)
        and (source_id is None or combo[2] == source_id)
        and (solution_id is None or combo[3] == solution_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, light_id, source_id, solution_id = rng.choice(combos)
    kid_a_type = args.kid_a_type or rng.choice(["girl", "boy"])
    kid_b_type = args.kid_b_type or rng.choice(["girl", "boy"])
    kid_a_name = args.kid_a or _pick_name(rng, kid_a_type)
    kid_b_name = args.kid_b or _pick_name(rng, kid_b_type, avoid=kid_a_name)
    caretaker = args.caretaker or rng.choice(["mother", "father"])

    return StoryParams(
        place=place_id,
        light=light_id,
        source=source_id,
        solution=solution_id,
        kid_a_name=kid_a_name,
        kid_a_type=kid_a_type,
        kid_b_name=kid_b_name,
        kid_b_type=kid_b_type,
        caretaker_type=caretaker,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")

    place = PLACES[params.place]
    light = LIGHTS[params.light]
    source = SOURCES[params.source]
    solution = SOLUTIONS[params.solution]
    if not compatible(place, light, source, solution):
        raise StoryError(explain_rejection(place, light, source, solution))

    world = tell(
        place=place,
        light_cfg=light,
        source_cfg=source,
        solution=solution,
        kid_a_name=params.kid_a_name,
        kid_a_type=params.kid_a_type,
        kid_b_name=params.kid_b_name,
        kid_b_type=params.kid_b_type,
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
        print(asp_program("", "#show compatible/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, light, source, solution) combos:\n")
        for place, light, source, solution in combos:
            print(f"  {place:6} {light:17} {source:15} {solution}")
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
            header = f"### {p.kid_a_name} & {p.kid_b_name}: {p.light} at {p.place} ({p.source}, {p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
