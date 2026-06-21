#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gear_cobra_transformation_lesson_learned_detective_story.py
======================================================================================

A standalone story world for a tiny child-facing detective story domain:

A child detective spots what looks like a cobra in a dim place. With a small set
of detective gear and a calm grown-up helper, the child follows clues, changes
the light, and watches the scary "cobra" transform into the harmless thing it
really was. The world model tracks fear, curiosity, caution, and clarity, so the
turn and resolution come from simulated state rather than noun swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/gear_cobra_transformation_lesson_learned_detective_story.py
    python storyworlds/worlds/gpt-5.4/gear_cobra_transformation_lesson_learned_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gear_cobra_transformation_lesson_learned_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/gear_cobra_transformation_lesson_learned_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/gear_cobra_transformation_lesson_learned_detective_story.py --verify
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
CLARITY_NEEDED = 2
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    dim_source: str
    mood: str
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
class MistakenThing:
    id: str
    label: str
    phrase: str
    real_phrase: str
    base_shape: str
    clue: str
    clue_reveal: str
    coiled: bool = True
    striped: bool = False
    harmless: bool = True
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
class Distorter:
    id: str
    label: str
    phrase: str
    effect_text: str
    striped_bonus: int
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
class RevealMethod:
    id: str
    label: str
    phrase: str
    clarity: int
    sense: int
    action_text: str
    result_text: str
    qa_text: str
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


def suspicion_score(thing: MistakenThing, distorter: Distorter) -> int:
    base = 1 if thing.coiled else 0
    base += distorter.striped_bonus if thing.striped else 0
    return base


def looks_like_cobra(thing: MistakenThing, distorter: Distorter) -> bool:
    return suspicion_score(thing, distorter) >= 2


def sensible_methods() -> list[RevealMethod]:
    return [m for m in REVEAL_METHODS.values() if m.sense >= SENSE_MIN]


def reveal_success(method: RevealMethod) -> bool:
    return method.clarity >= CLARITY_NEEDED


def _r_false_alarm(world: World) -> list[str]:
    shape = world.facts["apparent_shape"]
    method = world.facts["reveal_method_cfg"]
    suspect = world.get("suspect")
    if shape != "cobra" or method.clarity < CLARITY_NEEDED:
        return []
    sig = ("false_alarm", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.meters["identified"] += 1
    suspect.meters["danger"] = 0.0
    suspect.memes["monster"] = 0.0
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["fear"] = 0.0
    detective.memes["relief"] += 1
    detective.memes["lesson"] += 1
    helper.memes["pride"] += 1
    world.facts["apparent_shape"] = "ordinary"
    world.facts["lesson_learned"] = True
    return ["__transformation__"]


CAUSAL_RULES = [
    Rule(name="false_alarm", tag="reasoning", apply=_r_false_alarm),
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


SETTINGS = {
    "shed": Setting(
        id="shed",
        place="the backyard shed",
        opening="At the far end of the yard stood a little shed with one cloudy window.",
        dim_source="The late light slipped through the dusty glass in thin gray stripes.",
        mood="Every shelf looked full of secrets.",
        tags={"shed", "dark_place"},
    ),
    "garage": Setting(
        id="garage",
        place="the garage",
        opening="Beside the house was a garage where rakes, boxes, and boots slept in neat rows.",
        dim_source="Only a narrow ribbon of evening light lay across the floor.",
        mood="The corners looked deeper than they really were.",
        tags={"garage", "dark_place"},
    ),
    "greenhouse": Setting(
        id="greenhouse",
        place="the greenhouse",
        opening="Behind the garden stood a warm greenhouse fogged with tiny drops of water.",
        dim_source="Leaf shadows crossed the floor and moved whenever the wind touched the panes.",
        mood="The pots and tools made twisty little shapes.",
        tags={"greenhouse", "dark_place"},
    ),
}

THINGS = {
    "hose": MistakenThing(
        id="hose",
        label="hose",
        phrase="a green garden hose",
        real_phrase="the curled garden hose",
        base_shape="a soft coil on the floor",
        clue="one end disappeared behind a watering can",
        clue_reveal="The round metal nozzle looked nothing like a snake's mouth.",
        coiled=True,
        striped=False,
        harmless=True,
        tags={"hose", "garden"},
    ),
    "rope": MistakenThing(
        id="rope",
        label="rope",
        phrase="a striped skipping rope",
        real_phrase="the skipping rope with faded stripes",
        base_shape="a loose loop near the wall",
        clue="its handle was half-hidden in the dust",
        clue_reveal="The little handle peeped out once the light reached it.",
        coiled=True,
        striped=True,
        harmless=True,
        tags={"rope", "stripes"},
    ),
    "scarf": MistakenThing(
        id="scarf",
        label="scarf",
        phrase="a rolled striped scarf",
        real_phrase="the striped scarf someone had rolled into a bundle",
        base_shape="a lumpy coil on a crate",
        clue="a tassel hung over the edge like a tiny tail",
        clue_reveal="The soft tassels sagged when the breeze stopped.",
        coiled=True,
        striped=True,
        harmless=True,
        tags={"scarf", "stripes"},
    ),
    "cord": MistakenThing(
        id="cord",
        label="extension cord",
        phrase="an orange extension cord",
        real_phrase="the looped extension cord",
        base_shape="a long loop under the bench",
        clue="its plug was tucked in shadow",
        clue_reveal="The plastic plug shone when the brighter light found it.",
        coiled=True,
        striped=False,
        harmless=True,
        tags={"cord", "electric"},
    ),
    "rake": MistakenThing(
        id="rake",
        label="rake",
        phrase="a rake",
        real_phrase="the old rake",
        base_shape="a straight handle against the wall",
        clue="its teeth were hidden in a flowerpot",
        clue_reveal="The long handle never had the curved body a snake would have.",
        coiled=False,
        striped=False,
        harmless=True,
        tags={"rake", "tool"},
    ),
}

DISTORTERS = {
    "leaf_shadow": Distorter(
        id="leaf_shadow",
        label="leaf shadow",
        phrase="leaf shadows",
        effect_text="moving leaf shadows slid across the shape and made it seem to ripple",
        striped_bonus=1,
        tags={"shadow"},
    ),
    "slat_shadow": Distorter(
        id="slat_shadow",
        label="slat shadow",
        phrase="thin slat shadows",
        effect_text="thin shadows from the boards laid dark bands over it, like snake marks",
        striped_bonus=1,
        tags={"shadow", "stripes"},
    ),
    "curtain_breeze": Distorter(
        id="curtain_breeze",
        label="breeze",
        phrase="a small breeze",
        effect_text="a small breeze stirred the loose end and made it lift for a second",
        striped_bonus=0,
        tags={"wind"},
    ),
}

REVEAL_METHODS = {
    "porch_light": RevealMethod(
        id="porch_light",
        label="porch light",
        phrase="the porch light",
        clarity=3,
        sense=3,
        action_text="clicked on the porch light and opened the door wide",
        result_text="Clean yellow light filled the place and flattened the spooky shadows.",
        qa_text="turned on the porch light and flooded the place with steady light",
        tags={"light", "electric_light"},
    ),
    "flashlight": RevealMethod(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        clarity=2,
        sense=3,
        action_text="took out a flashlight from the detective gear pouch and shone it low across the floor",
        result_text="The narrow beam picked out edges, handles, and dusty corners one by one.",
        qa_text="used a flashlight from the detective gear to inspect the shape closely",
        tags={"light", "flashlight", "gear"},
    ),
    "lantern": RevealMethod(
        id="lantern",
        label="camp lantern",
        phrase="a small camp lantern",
        clarity=2,
        sense=2,
        action_text="set down a small camp lantern and turned its round glow toward the shape",
        result_text="The gentler light steadied the whole scene so the shape stopped seeming alive.",
        qa_text="set down a camp lantern to steady the light and see the shape clearly",
        tags={"light", "lantern", "gear"},
    ),
    "magnifier": RevealMethod(
        id="magnifier",
        label="magnifying glass",
        phrase="a magnifying glass",
        clarity=0,
        sense=1,
        action_text="held up a magnifying glass even though the corner was still too dim to read properly",
        result_text="The glass made one patch bigger, but it did not fix the shadows.",
        qa_text="tried using a magnifying glass in the dark",
        tags={"gear", "magnifier"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "Zoe", "Ava", "Tess"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "curious", "brave", "patient", "thoughtful"]
HELPERS = ["mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for thing_id, thing in THINGS.items():
            for distorter_id, distorter in DISTORTERS.items():
                if looks_like_cobra(thing, distorter):
                    combos.append((setting_id, thing_id, distorter_id))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    thing: str
    distorter: str
    reveal_method: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None
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


def explain_combo_rejection(thing: MistakenThing, distorter: Distorter) -> str:
    return (
        f"(No story: {thing.phrase} with {distorter.phrase} would not reasonably look "
        f"like a cobra in this tiny mystery world. Pick a coiled object or a stronger "
        f"shadow effect so the detective has a real puzzle to solve.)"
    )


def explain_method_rejection(method_id: str) -> str:
    method = REVEAL_METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing reveal method '{method_id}': it is too weak or not sensible enough "
        f"for a calm detective solution (sense={method.sense} < {SENSE_MIN}). "
        f"Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    method = REVEAL_METHODS[params.reveal_method]
    return "solved" if reveal_success(method) else "spooked"


def predict_reveal(world: World, method: RevealMethod) -> dict:
    sim = world.copy()
    sim.facts["reveal_method_cfg"] = method
    sim.facts["apparent_shape"] = "cobra"
    propagate(sim, narrate=False)
    suspect = sim.get("suspect")
    return {
        "identified": suspect.meters["identified"] >= THRESHOLD,
        "fear_after": sim.get("detective").memes["fear"],
    }


def introduce(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"{detective.id} was a little {detective.type} who loved detective stories and kept "
        f"a tiny belt of gear with a notebook, a stubby pencil, and one special pocket for clues."
    )
    world.say(
        f"Whenever something looked odd, {detective.pronoun()} tried to solve it before supper, "
        f"with {detective.pronoun('possessive')} {helper.label_word} never far away."
    )


def arrive(world: World, detective: Entity, setting: Setting) -> None:
    world.say(setting.opening)
    world.say(setting.dim_source)
    world.say(setting.mood)
    detective.memes["curiosity"] += 1


def spot_shape(world: World, detective: Entity, thing: MistakenThing, distorter: Distorter) -> None:
    suspect = world.get("suspect")
    suspect.meters["danger"] = 1.0
    suspect.memes["monster"] = 1.0
    detective.memes["fear"] += 1
    world.say(
        f"As {detective.id} peered inside, {detective.pronoun()} saw {thing.base_shape}. "
        f"Then {distorter.effect_text}."
    )
    world.say(
        f'At once, {detective.pronoun("possessive")} heart gave a jump. '
        f'"A cobra!" {detective.pronoun()} whispered.'
    )


def inspect_clues(world: World, detective: Entity, thing: MistakenThing) -> None:
    detective.memes["care"] += 1
    world.say(
        f"But {detective.id} did not run closer. {detective.pronoun().capitalize()} crouched by the doorway, "
        f"opened the little notebook from the detective gear, and wrote down two clues: "
        f"the shape stayed low, and {thing.clue}."
    )


def call_helper(world: World, detective: Entity, helper: Entity) -> None:
    helper.memes["calm"] += 1
    detective.memes["trust"] += 1
    world.say(
        f'Instead of touching anything, {detective.id} called, "{helper.label_word.capitalize()}, '
        f'please come see. I found something that looks like a cobra."'
    )
    world.say(
        f"{helper.label_word.capitalize()} came over at once, but did not laugh. "
        f'"Good detectives use their eyes before their hands," {helper.pronoun()} said.'
    )


def reason_together(world: World, detective: Entity, helper: Entity, method: RevealMethod) -> None:
    pred = predict_reveal(world, method)
    world.facts["predicted_identified"] = pred["identified"]
    world.say(
        f"{detective.id} pointed to the clues, and together they made a plan to use {method.phrase}."
    )
    if pred["identified"]:
        world.say(
            f'"If we make the light steadier," {helper.label_word} said, '
            f'"the shape will tell us what it really is."'
        )
    else:
        world.say(
            f'"This may not be enough light yet," {helper.label_word} said, '
            f'"but we can still stay back and think carefully."'
        )


def reveal(world: World, detective: Entity, helper: Entity, thing: MistakenThing, method: RevealMethod) -> None:
    world.facts["reveal_method_cfg"] = method
    world.say(
        f"Very slowly, {helper.label_word} {method.action_text}. {method.result_text}"
    )
    propagate(world, narrate=False)
    if world.get("suspect").meters["identified"] >= THRESHOLD:
        world.say(
            f"The terrible cobra changed right before {detective.id}'s eyes. It was not a snake at all, "
            f"but {thing.real_phrase}. {thing.clue_reveal}"
        )
    else:
        detective.memes["fear"] += 1
        world.say(
            f"The shape still looked too strange to trust. They backed away, closed the door, "
            f"and decided to ask another grown-up before going near it again."
        )


def lesson(world: World, detective: Entity, helper: Entity, thing: MistakenThing) -> None:
    world.say(
        f'{helper.label_word.capitalize()} smiled and tapped the notebook. "You solved the case by slowing down," '
        f'{helper.pronoun()} said. "Shadows can dress an ordinary thing in a scary costume."'
    )
    world.say(
        f"{detective.id} nodded and wrote the lesson neatly under the clues: "
        f"Look twice, use good light, and ask for help before calling something dangerous."
    )
    world.say(
        f"After that, {detective.pronoun()} put the gear away carefully, and {thing.label} no longer seemed spooky at all."
    )


def uncertain_ending(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"That night, {detective.id} still felt proud for staying back and getting help instead of poking at the shape."
    )
    world.say(
        f"{helper.label_word.capitalize()} promised they would come back with better light in the morning. "
        f"Even an unfinished case had taught {detective.pronoun('object')} to be careful."
    )


def tell(
    setting: Setting,
    thing: MistakenThing,
    distorter: Distorter,
    method: RevealMethod,
    name: str,
    gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        role="detective",
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="thing",
        type=thing.label,
        label=thing.label,
        phrase=thing.phrase,
        role="suspect",
    ))

    world.facts["setting_cfg"] = setting
    world.facts["thing_cfg"] = thing
    world.facts["distorter_cfg"] = distorter
    world.facts["reveal_method_cfg"] = method
    world.facts["apparent_shape"] = "cobra"
    world.facts["lesson_learned"] = False

    introduce(world, detective, helper)
    arrive(world, detective, setting)

    world.para()
    spot_shape(world, detective, thing, distorter)
    inspect_clues(world, detective, thing)
    call_helper(world, detective, helper)

    world.para()
    reason_together(world, detective, helper, method)
    reveal(world, detective, helper, thing, method)

    world.para()
    if world.get("suspect").meters["identified"] >= THRESHOLD:
        lesson(world, detective, helper, thing)
        outcome = "solved"
    else:
        uncertain_ending(world, detective, helper)
        outcome = "spooked"

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        outcome=outcome,
        transformed=world.get("suspect").meters["identified"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "cobra": [(
        "What is a cobra?",
        "A cobra is a kind of snake. Some cobras can raise the front of their bodies and spread the skin near their necks, which makes them look bigger."
    )],
    "shadow": [(
        "Why can shadows make things look scary?",
        "Shadows hide some parts and stretch other parts, so your brain may guess the wrong shape. A harmless thing can look strange when the light is dim."
    )],
    "flashlight": [(
        "What does a flashlight help you do?",
        "A flashlight gives you a steady beam so you can see details in a dark place. Seeing details helps you make safer choices."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern spreads light around a whole area. That can make shadows look less tricky."
    )],
    "gear": [(
        "What is gear?",
        "Gear is the useful equipment you bring for a job, like a notebook or a flashlight for a detective. Good gear helps you look carefully instead of guessing."
    )],
    "rope": [(
        "Why might a rope be mistaken for a snake?",
        "A rope can curl and bend like a snake when you only see part of it. In dim light, your eyes may miss the handle or loose fibers that show what it really is."
    )],
    "hose": [(
        "Why might a hose look like a snake in the dark?",
        "A garden hose can lie in coils on the floor. If shadows move over it, the curves can seem alive for a moment."
    )],
}

KNOWLEDGE_ORDER = ["gear", "cobra", "shadow", "flashlight", "lantern", "rope", "hose"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    thing = f["thing_cfg"]
    setting = f["setting_cfg"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the words "gear" and "cobra".',
        f"Tell a gentle mystery where {detective.id} thinks there is a cobra in {setting.place}, but the scary clue transforms into {thing.real_phrase}.",
        "Write a child-facing detective tale with a lesson learned: slow down, use better light, and ask a grown-up for help before deciding something is dangerous.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    thing = f["thing_cfg"]
    setting = f["setting_cfg"]
    distorter = f["distorter_cfg"]
    method = f["reveal_method_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {detective.pronoun('possessive')} {helper.label_word}. Together they solve a spooky-looking mystery in {setting.place}."
        ),
        (
            f"Why did {detective.id} think there was a cobra?",
            f"{detective.id} saw {thing.base_shape} in dim light, and {distorter.effect_text}. That made the harmless shape seem alive and snake-like."
        ),
        (
            f"What did {detective.id} do with the detective gear?",
            f"{detective.pronoun().capitalize()} used the notebook from the detective gear to write down clues instead of rushing in. That helped {detective.pronoun('object')} think before acting."
        ),
    ]
    if outcome == "solved":
        qa.append((
            f"How did they solve the mystery?",
            f"They used {method.phrase} to make the light clearer. Once the shadows stopped tricking them, the 'cobra' transformed into {thing.real_phrase}."
        ))
        qa.append((
            "What lesson did the detective learn?",
            "The detective learned to look twice, use better light, and ask for help before deciding something is dangerous. Slowing down turned fear into a solved case."
        ))
        qa.append((
            "How did the story end?",
            f"It ended peacefully, with the mystery solved and the scary cobra gone. {detective.id} put the gear away neatly because the case had become an ordinary object again."
        ))
    else:
        qa.append((
            "Did they touch the strange shape?",
            f"No. They stayed back and chose to get more help because the light was still too poor to be sure."
        ))
        qa.append((
            "What lesson did the detective learn even before the case was finished?",
            "The detective learned that being careful matters more than being fast. Asking for help and waiting for better light was the safe choice."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"gear", "cobra", "shadow"}
    thing = world.facts["thing_cfg"]
    method = world.facts["reveal_method_cfg"]
    tags |= set(thing.tags) | set(method.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  apparent_shape={world.facts.get('apparent_shape')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A convincing false cobra needs a coiled object and enough shadow-stripe effect.
suspicion(T, D, 1) :- thing(T), distorter(D), coiled(T), not striped(T).
suspicion(T, D, 2) :- thing(T), distorter(D), coiled(T), striped(T), striped_bonus(D, 1).
suspicion(T, D, 1) :- thing(T), distorter(D), coiled(T), striped(T), striped_bonus(D, 0).

looks_like_cobra(T, D) :- suspicion(T, D, S), cobra_threshold(M), S >= M.
sensible(M) :- method(M), sense(M, S), sense_min(MN), S >= MN.
solved(M) :- method(M), clarity(M, C), clarity_needed(N), C >= N.
valid(S, T, D) :- setting(S), thing(T), distorter(D), looks_like_cobra(T, D).

outcome(solved) :- chosen_method(M), solved(M).
outcome(spooked) :- chosen_method(M), not solved(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if thing.coiled:
            lines.append(asp.fact("coiled", tid))
        if thing.striped:
            lines.append(asp.fact("striped", tid))
    for did, distorter in DISTORTERS.items():
        lines.append(asp.fact("distorter", did))
        lines.append(asp.fact("striped_bonus", did, distorter.striped_bonus))
    for mid, method in REVEAL_METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("clarity", mid, method.clarity))
        lines.append(asp.fact("sense", mid, method.sense))
    lines.append(asp.fact("cobra_threshold", 2))
    lines.append(asp.fact("clarity_needed", CLARITY_NEEDED))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_method", params.reveal_method)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="shed",
        thing="rope",
        distorter="slat_shadow",
        reveal_method="flashlight",
        name="Mira",
        gender="girl",
        helper="father",
        trait="careful",
    ),
    StoryParams(
        setting="garage",
        thing="scarf",
        distorter="leaf_shadow",
        reveal_method="porch_light",
        name="Theo",
        gender="boy",
        helper="mother",
        trait="patient",
    ),
    StoryParams(
        setting="greenhouse",
        thing="hose",
        distorter="slat_shadow",
        reveal_method="lantern",
        name="Nora",
        gender="girl",
        helper="aunt",
        trait="curious",
    ),
    StoryParams(
        setting="shed",
        thing="cord",
        distorter="curtain_breeze",
        reveal_method="flashlight",
        name="Eli",
        gender="boy",
        helper="uncle",
        trait="thoughtful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective, a false cobra, and a lesson about careful looking."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--distorter", choices=DISTORTERS)
    ap.add_argument("--reveal-method", choices=REVEAL_METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.thing and args.distorter:
        thing = THINGS[args.thing]
        distorter = DISTORTERS[args.distorter]
        if not looks_like_cobra(thing, distorter):
            raise StoryError(explain_combo_rejection(thing, distorter))
    if args.reveal_method and REVEAL_METHODS[args.reveal_method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.reveal_method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.thing is None or combo[1] == args.thing)
        and (args.distorter is None or combo[2] == args.distorter)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, thing_id, distorter_id = rng.choice(combos)
    reveal_method = args.reveal_method or rng.choice(sorted(m.id for m in sensible_methods()))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        thing=thing_id,
        distorter=distorter_id,
        reveal_method=reveal_method,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.thing not in THINGS:
        raise StoryError(f"(Unknown thing: {params.thing})")
    if params.distorter not in DISTORTERS:
        raise StoryError(f"(Unknown distorter: {params.distorter})")
    if params.reveal_method not in REVEAL_METHODS:
        raise StoryError(f"(Unknown reveal method: {params.reveal_method})")

    setting = SETTINGS[params.setting]
    thing = THINGS[params.thing]
    distorter = DISTORTERS[params.distorter]
    method = REVEAL_METHODS[params.reveal_method]

    if not looks_like_cobra(thing, distorter):
        raise StoryError(explain_combo_rejection(thing, distorter))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.reveal_method))

    world = tell(
        setting=setting,
        thing=thing,
        distorter=distorter,
        method=method,
        name=params.name,
        gender=params.gender,
        helper_type=params.helper,
        trait=params.trait,
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

    clingo_methods = set(asp_sensible_methods())
    python_methods = {m.id for m in sensible_methods()}
    if clingo_methods == python_methods:
        print(f"OK: sensible methods match ({sorted(clingo_methods)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  clingo:", sorted(clingo_methods))
        print("  python:", sorted(python_methods))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        methods = asp_sensible_methods()
        print(f"sensible reveal methods: {', '.join(methods)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, thing, distorter) combos:\n")
        for setting_id, thing_id, distorter_id in combos:
            print(f"  {setting_id:10} {thing_id:8} {distorter_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
                f"### {p.name}: {p.thing} in {p.setting} "
                f"({p.distorter}, {p.reveal_method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
