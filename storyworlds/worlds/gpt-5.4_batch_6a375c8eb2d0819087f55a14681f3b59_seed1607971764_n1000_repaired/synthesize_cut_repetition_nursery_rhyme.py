#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py
=====================================================================

A standalone storyworld for a nursery-rhyme-style crafting tale built around
the words "synthesize" and "cut". A child cuts little pieces for a simple
festival craft; the pieces are loose and troublesome on their own, then a calm
helper shows how to synthesize them into one finished thing.

The domain is deliberately small and constraint-checked:
- a project needs a suitable material
- the chosen joining method must actually work for that material and project
- the story turn comes from the state of many loose cut pieces before they are
  synthesized into a whole

Run it
------
    python storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py --project garland --material paper --method paste
    python storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py --project kite_tail --material grass
    python storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/synthesize_cut_repetition_nursery_rhyme.py --verify
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    disturbance: str
    line: str
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
class Project:
    id: str
    label: str
    phrase: str
    purpose: str
    use_line: str
    challenge: str
    needs: set[str] = field(default_factory=set)
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
class Material:
    id: str
    label: str
    phrase: str
    texture: str
    bundle: str
    supports: set[str] = field(default_factory=set)
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
    verb: str
    past: str
    suited: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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


def _r_loose_pieces(world: World) -> list[str]:
    bits = world.get("bits")
    craft = world.get("craft")
    child = world.get("child")
    if bits.meters["cut"] < THRESHOLD:
        return []
    sig = ("loose",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bits.meters["loose"] += 1
    craft.meters["unfinished"] += 1
    child.memes["worry"] += 1
    return []


def _r_disturbance(world: World) -> list[str]:
    bits = world.get("bits")
    child = world.get("child")
    craft = world.get("craft")
    project = world.facts["project"]
    if bits.meters["loose"] < THRESHOLD:
        return []
    sig = ("disturb", project.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if project.challenge == "scatter":
        bits.meters["scattered"] += 1
    else:
        bits.meters["sagging"] += 1
    craft.meters["trouble"] += 1
    child.memes["worry"] += 1
    return []


def _r_whole(world: World) -> list[str]:
    bits = world.get("bits")
    craft = world.get("craft")
    child = world.get("child")
    helper = world.get("helper")
    if bits.meters["joined"] < THRESHOLD:
        return []
    sig = ("whole",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    craft.meters["whole"] += 1
    craft.meters["unfinished"] = 0.0
    craft.meters["trouble"] = 0.0
    bits.meters["loose"] = 0.0
    bits.meters["scattered"] = 0.0
    bits.meters["sagging"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    helper.memes["care"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="loose_pieces", tag="physical", apply=_r_loose_pieces),
    Rule(name="disturbance", tag="physical", apply=_r_disturbance),
    Rule(name="whole", tag="physical", apply=_r_whole),
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
            world.say(s)
    return produced


def compatible(project: Project, material: Material, method: Method) -> bool:
    return (
        project.id in material.supports
        and material.id in method.suited
        and project.id in method.fixes
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for project_id, project in PROJECTS.items():
            for material_id, material in MATERIALS.items():
                for method_id, method in METHODS.items():
                    if compatible(project, material, method):
                        combos.append((place_id, project_id, material_id, method_id))
    return combos


def explain_rejection(project: Project, material: Material, method: Method) -> str:
    if project.id not in material.supports:
        return (
            f"(No story: {material.phrase} would not make a good {project.label}. "
            f"The material does not suit that project.)"
        )
    if material.id not in method.suited:
        return (
            f"(No story: {method.label} does not work well on {material.label}. "
            f"Pick a method that really joins that material.)"
        )
    if project.id not in method.fixes:
        return (
            f"(No story: {method.label} would not finish a {project.label} in this world. "
            f"Pick a joining method that can make the project whole.)"
        )
    return "(No story: this combination is not reasonable.)"


def challenge_text(project: Project, place: Place) -> str:
    if project.challenge == "scatter":
        return (
            f"But {place.disturbance} tickled the loose pieces, and they skittered this way and that. "
            f"Little bits here, little bits there, and not yet a {project.label} anywhere."
        )
    return (
        f"But the cut pieces drooped and would not keep their shape. "
        f"They sagged this way and that, and not yet a {project.label} could sit just right."
    )


def predicted_trouble(project: Project) -> str:
    return "scatter" if project.challenge == "scatter" else "sag"


def introduce(world: World, child: Entity, helper: Entity, project: Project, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {place.scene}, {child.id} skipped to {place.label} with {helper.label_word} near by. "
        f"{place.line}"
    )
    world.say(
        f'{child.id} sang, "A {project.label}, a {project.label}, {project.phrase} for {project.purpose}!"'
    )


def gather_material(world: World, child: Entity, material: Material) -> None:
    bits = world.get("bits")
    bits.attrs["material"] = material.id
    world.say(
        f"There lay {material.bundle}, {material.texture} and bright. "
        f'{child.id} clapped and sang, "Cut and hum, cut and hum, {material.label} will do, oh yum!"'
    )


def cut_bits(world: World, child: Entity, material: Material) -> None:
    bits = world.get("bits")
    bits.meters["cut"] += 1
    child.memes["focus"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} began to cut, cut, cut the {material.label} into little pieces. "
        f"Snip for one, snip for two, snip for three, and still a few."
    )


def notice_trouble(world: World, child: Entity, project: Project, place: Place) -> None:
    world.say(challenge_text(project, place))
    if world.get("bits").meters["scattered"] >= THRESHOLD:
        world.say(
            f'{child.id} sighed, "I have cut the pieces, but the pieces will not stay."'
        )
    else:
        world.say(
            f'{child.id} sighed, "I have cut the pieces, but the pieces will not hold."'
        )


def helper_predicts(world: World, helper: Entity, child: Entity, project: Project, material: Material, method: Method) -> None:
    world.facts["predicted_trouble"] = predicted_trouble(project)
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {child.id} and said, '
        f'"Little bits alone are lonely bits. We can synthesize them with {method.label} and make one true {project.label}."'
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} touched the {material.label} gently, already seeing the whole shape in the many small parts."
    )


def synthesize_bits(world: World, helper: Entity, child: Entity, method: Method, project: Project) -> None:
    bits = world.get("bits")
    bits.meters["joined"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So they {method.past}, linked, and tucked the pieces together. "
        f'"Synthesize, synthesize," sang {helper.label_word}, "many small bits make one sweet surprise."'
    )
    world.say(
        f"Bit by bit the {project.label} came whole. No longer loose, no longer last, the little pieces held together fast."
    )


def finish_story(world: World, child: Entity, helper: Entity, project: Project) -> None:
    craft = world.get("craft")
    craft.attrs["ready"] = True
    world.say(
        f"Then {child.id} lifted the {project.label}. {project.use_line}"
    )
    world.say(
        f'{child.id} laughed, "I did cut the pieces, and then we did synthesize them!"'
    )
    world.say(
        f"And there they went, light and slow, with one fine {project.label} all in a row."
    )


def tell(
    place: Place,
    project: Project,
    material: Material,
    method: Method,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "grandmother",
) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper"))
    bits = world.add(Entity(id="bits", type="bits", label="pieces", phrase=material.bundle))
    craft = world.add(Entity(id="craft", type=project.id, label=project.label, phrase=project.phrase))
    world.facts.update(
        place=place,
        project=project,
        material=material,
        method=method,
        child=child,
        helper=helper,
        disturbance=place.disturbance,
    )

    introduce(world, child, helper, project, place)
    gather_material(world, child, material)

    world.para()
    cut_bits(world, child, material)
    notice_trouble(world, child, project, place)

    world.para()
    helper_predicts(world, helper, child, project, material, method)
    synthesize_bits(world, helper, child, method, project)

    world.para()
    finish_story(world, child, helper, project)

    world.facts.update(
        cut=bits.meters["cut"] >= THRESHOLD,
        trouble=craft.meters["whole"] < THRESHOLD,
        scattered=bits.meters["scattered"] >= THRESHOLD,
        sagging=bits.meters["sagging"] >= THRESHOLD,
        synthesized=bits.meters["joined"] >= THRESHOLD,
        whole=craft.meters["whole"] >= THRESHOLD,
    )
    return world


PLACES = {
    "nursery": Place(
        id="nursery",
        label="the nursery floor",
        scene="the warm nursery",
        disturbance="a window-breeze",
        line="The sun made a square of gold on the rug.",
        tags={"room", "breeze"},
    ),
    "garden_gate": Place(
        id="garden_gate",
        label="the garden gate",
        scene="the little garden",
        disturbance="a hedge-breeze",
        line="Poppies nodded by the path, and the gate clicked softly.",
        tags={"garden", "breeze"},
    ),
    "porch": Place(
        id="porch",
        label="the front porch step",
        scene="the shady porch",
        disturbance="a porch-breeze",
        line="A small bell chimed over the door.",
        tags={"porch", "breeze"},
    ),
}

PROJECTS = {
    "garland": Project(
        id="garland",
        label="garland",
        phrase="a looping garland",
        purpose="the gate",
        use_line="It draped from hand to hand, ready to sway on the gate.",
        challenge="scatter",
        needs={"looped"},
        tags={"garland"},
    ),
    "kite_tail": Project(
        id="kite_tail",
        label="kite tail",
        phrase="a dancing kite tail",
        purpose="the kite",
        use_line="It streamed behind the waiting kite like a row of merry fish.",
        challenge="scatter",
        needs={"linked"},
        tags={"kite"},
    ),
    "crown": Project(
        id="crown",
        label="crown",
        phrase="a round little crown",
        purpose="the rhyme-game",
        use_line="It sat on a small head as neat as a circle of song.",
        challenge="sag",
        needs={"round"},
        tags={"crown"},
    ),
}

MATERIALS = {
    "paper": Material(
        id="paper",
        label="paper",
        phrase="colored paper",
        texture="light",
        bundle="a stack of colored paper",
        supports={"garland", "kite_tail"},
        tags={"paper"},
    ),
    "cloth": Material(
        id="cloth",
        label="cloth",
        phrase="soft cloth scraps",
        texture="soft",
        bundle="a basket of soft cloth scraps",
        supports={"garland", "kite_tail", "crown"},
        tags={"cloth"},
    ),
    "grass": Material(
        id="grass",
        label="grass",
        phrase="long grass ribbons",
        texture="green",
        bundle="a bundle of long grass ribbons",
        supports={"garland", "crown"},
        tags={"grass"},
    ),
}

METHODS = {
    "paste": Method(
        id="paste",
        label="paste",
        verb="paste",
        past="pasted",
        suited={"paper"},
        fixes={"garland", "kite_tail"},
        tags={"paste"},
    ),
    "stitch": Method(
        id="stitch",
        label="stitching",
        verb="stitch",
        past="stitched",
        suited={"cloth"},
        fixes={"garland", "kite_tail", "crown"},
        tags={"stitch"},
    ),
    "weave": Method(
        id="weave",
        label="weaving",
        verb="weave",
        past="wove",
        suited={"grass", "cloth"},
        fixes={"garland", "crown"},
        tags={"weave"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Poppy", "Mabel", "Nina", "Dot", "Maisie", "Tilly"]
BOY_NAMES = ["Toby", "Milo", "Pip", "Ned", "Robin", "Benny", "Otis", "Jem"]
HELPERS = ["mother", "father", "grandmother", "grandfather", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    project: str
    material: str
    method: str
    child_name: str
    child_gender: str
    helper_type: str
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
    "paper": [
        (
            "What is paper good for in a craft?",
            "Paper is light and easy to cut into shapes and strips. It is good for simple decorations when you can paste the pieces together."
        )
    ],
    "cloth": [
        (
            "Why can cloth scraps be useful?",
            "Cloth scraps bend without snapping, so they can be stitched or woven together. Little scraps can become one bigger thing."
        )
    ],
    "grass": [
        (
            "Why can long grass be woven?",
            "Long grass bends and crosses over itself, so you can weave it. Weaving helps many thin strands act like one piece."
        )
    ],
    "paste": [
        (
            "What does paste do?",
            "Paste is sticky, so it helps paper pieces hold together. It is useful when many little cut parts need to become one whole craft."
        )
    ],
    "stitch": [
        (
            "What is stitching?",
            "Stitching joins cloth with thread and small careful loops. It helps soft pieces stay together instead of slipping apart."
        )
    ],
    "weave": [
        (
            "What is weaving?",
            "Weaving means crossing strips over and under each other. That pattern helps many pieces hold together as one."
        )
    ],
    "garland": [
        (
            "What is a garland?",
            "A garland is a long decoration made from pieces joined in a row or loop. People hang it where it can sway and look pretty."
        )
    ],
    "kite": [
        (
            "Why does a kite tail need to stay together?",
            "A kite tail trails behind the kite, so loose pieces would blow away. Joined pieces move together and make one dancing tail."
        )
    ],
    "crown": [
        (
            "Why does a crown need shape?",
            "A crown has to curve around a head, so it cannot stay as loose little bits. The parts need to be joined so the circle can hold."
        )
    ],
    "breeze": [
        (
            "What can a breeze do to small light pieces?",
            "A breeze can lift, push, or scatter small light pieces. That is why loose bits are harder to manage than one joined craft."
        )
    ],
}
KNOWLEDGE_ORDER = ["paper", "cloth", "grass", "paste", "stitch", "weave", "garland", "kite", "crown", "breeze"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    project = f["project"]
    material = f["material"]
    method = f["method"]
    place = f["place"]
    return [
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the words "cut" and "synthesize".',
        f"Tell a repetitive, sing-song story where {child.id} cuts {material.label} into little pieces at {place.label}, then a helper shows how to synthesize the pieces into a {project.label}.",
        f"Write a simple rhyme-story with repeated lines, a small craft problem, and a happy ending where many little cut pieces become one whole thing by {method.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    project = f["project"]
    material = f["material"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to make a {project.label}, and {helper.label_word} who helped. They were working together in {place.scene}."
        ),
        (
            f"What did {child.id} do first?",
            f"{child.id} first chose {material.bundle} and began to cut it into little pieces. The repeated snipping made many parts, but not yet one finished {project.label}."
        ),
        (
            f"Why did the craft become a problem after the cutting?",
            f"The pieces were only little loose bits after they were cut. Because the {project.label} was not joined yet, the pieces {('scattered in the breeze' if f.get('predicted_trouble') == 'scatter' else 'sagged and would not hold their shape')}."
        ),
        (
            f"How did {helper.label_word} solve the problem?",
            f"{helper.label_word.capitalize()} told {child.id} they could synthesize the little parts into one whole craft. Then they used {method.label} to join the pieces so the {project.label} could hold together."
        ),
        (
            "How did the story end?",
            f"It ended with the {project.label} finished and ready for {project.purpose}. The ending image shows that the many cut pieces had become one true thing."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["material"].tags) | set(f["method"].tags) | set(f["project"].tags) | set(f["place"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="nursery",
        project="garland",
        material="paper",
        method="paste",
        child_name="Mina",
        child_gender="girl",
        helper_type="grandmother",
    ),
    StoryParams(
        place="garden_gate",
        project="kite_tail",
        material="cloth",
        method="stitch",
        child_name="Toby",
        child_gender="boy",
        helper_type="father",
    ),
    StoryParams(
        place="porch",
        project="crown",
        material="grass",
        method="weave",
        child_name="Poppy",
        child_gender="girl",
        helper_type="aunt",
    ),
    StoryParams(
        place="garden_gate",
        project="garland",
        material="grass",
        method="weave",
        child_name="Robin",
        child_gender="boy",
        helper_type="grandfather",
    ),
    StoryParams(
        place="nursery",
        project="crown",
        material="cloth",
        method="stitch",
        child_name="Lulu",
        child_gender="girl",
        helper_type="mother",
    ),
]


ASP_RULES = r"""
supports_material(P, M) :- supports(M, P).
works_method(Meth, Mat) :- suited(Meth, Mat).
finishes(Meth, P) :- fixes(Meth, P).

valid(Place, P, Mat, Meth) :-
    place(Place), project(P), material(Mat), method(Meth),
    supports_material(P, Mat),
    works_method(Meth, Mat),
    finishes(Meth, P).

predicted_trouble(P, scatter) :- challenge(P, scatter).
predicted_trouble(P, sag) :- challenge(P, sag).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("challenge", project_id, predicted_trouble(project)))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        for proj in sorted(material.supports):
            lines.append(asp.fact("supports", material_id, proj))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for mat in sorted(method.suited):
            lines.append(asp.fact("suited", method_id, mat))
        for proj in sorted(method.fixes):
            lines.append(asp.fact("fixes", method_id, proj))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_predicted_trouble(project_id: str) -> str:
    import asp

    model = asp.one_model(
        asp_program(asp.fact("chosen_project", project_id), f"pred(X) :- chosen_project(P), predicted_trouble(P, X).\n#show pred/1.")
    )
    atoms = asp.atoms(model, "pred")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme craft storyworld: many cut pieces are synthesized into one whole craft."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.material and args.method:
        project = PROJECTS[args.project]
        material = MATERIALS[args.material]
        method = METHODS[args.method]
        if not compatible(project, material, method):
            raise StoryError(explain_rejection(project, material, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.project is None or combo[1] == args.project)
        and (args.material is None or combo[2] == args.material)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, project, material, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        child_name = args.name
    else:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=place,
        project=project,
        material=material,
        method=method,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper_type not in set(HELPERS):
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    project = PROJECTS[params.project]
    material = MATERIALS[params.material]
    method = METHODS[params.method]
    if not compatible(project, material, method):
        raise StoryError(explain_rejection(project, material, method))

    world = tell(
        place=PLACES[params.place],
        project=project,
        material=material,
        method=method,
        child_name=params.child_name,
        child_type=params.child_gender,
        helper_type=params.helper_type,
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

    bad_trouble = []
    for project_id, project in PROJECTS.items():
        if asp_predicted_trouble(project_id) != predicted_trouble(project):
            bad_trouble.append(project_id)
    if not bad_trouble:
        print(f"OK: predicted trouble matches for {len(PROJECTS)} projects.")
    else:
        rc = 1
        print("MISMATCH in predicted trouble for:", ", ".join(sorted(bad_trouble)))

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(0))
        params.seed = 0
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show predicted_trouble/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, project, material, method) combos:\n")
        for place, project, material, method in combos:
            print(f"  {place:12} {project:10} {material:8} {method}")
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
            header = f"### {p.child_name}: {p.project} from {p.material} at {p.place} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
