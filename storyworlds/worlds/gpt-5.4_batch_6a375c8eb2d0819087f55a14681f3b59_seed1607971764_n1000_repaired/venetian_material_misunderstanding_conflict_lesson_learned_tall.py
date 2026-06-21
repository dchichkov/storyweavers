#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py
================================================================================================

A standalone storyworld for a tall-tale flavored misunderstanding story:

A braggy child wants to build something enormous for a windy-day show. An elder
asks for "the venetian material," meaning a special striped fabric from a
Venetian trader. The child misunderstands and fetches parts from an actual
venetian blind instead. The wrong choice sparks a quarrel, a comic disaster,
and then a calmer rebuild with the right fabric. The ending proves the lesson:
ask what a strange phrase means before arguing about it.

Run it
------
    python storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py
    python storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py --project kite --intended striped_silk --mistaken blind_slats
    python storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py --project sailcart --intended tissue_laminate
    python storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py --all
    python storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/venetian_material_misunderstanding_conflict_lesson_learned_tall.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return {"mother": "mom", "father": "dad", "uncle": "uncle", "aunt": "aunt"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    boast: str
    stage: str
    launch_place: str
    sky_line: str
    needs_light: int
    needs_flex: int
    needs_strength: int
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
    stripes: str
    weight: int
    flex: int
    strength: int
    source: str
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
class MistakenItem:
    id: str
    label: str
    phrase: str
    mistaken_reason: str
    clatter: str
    drag_text: str
    weight: int
    flex: int
    strength: int
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
class Wind:
    id: str
    label: str
    gust: str
    exaggeration: str
    force: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def suitable_for_project(material_weight: int, material_flex: int, material_strength: int,
                         project: Project) -> bool:
    return (
        material_weight <= project.needs_light
        and material_flex >= project.needs_flex
        and material_strength >= project.needs_strength
    )


def material_suits_project(material: Material, project: Project) -> bool:
    return suitable_for_project(material.weight, material.flex, material.strength, project)


def mistake_fails_project(item: MistakenItem, project: Project) -> bool:
    return not suitable_for_project(item.weight, item.flex, item.strength, project)


def _r_quarrel(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.memes["warning_ignored"] < THRESHOLD or hero.memes["boast"] < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["anger"] += 1
    helper.memes["anger"] += 1
    hero.meters["conflict"] += 1
    helper.meters["conflict"] += 1
    return ["__quarrel__"]


def _r_bad_launch(world: World) -> list[str]:
    project = world.get("project")
    if project.meters["launched"] < THRESHOLD or project.attrs.get("suitable", True):
        return []
    sig = ("bad_launch",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["crashed"] += 1
    project.meters["racket"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["shock"] += 1
    return ["__bad_launch__"]


def _r_good_launch(world: World) -> list[str]:
    project = world.get("project")
    if project.meters["launched"] < THRESHOLD or not project.attrs.get("suitable", False):
        return []
    sig = ("good_launch",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    project.meters["flying"] += 1
    for kid in world.kids():
        kid.memes["joy"] += 1
            # intentional indentation preserved for style
    return ["__good_launch__"]


CAUSAL_RULES = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="bad_launch", tag="physical", apply=_r_bad_launch),
    Rule(name="good_launch", tag="physical", apply=_r_good_launch),
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


PROJECTS = {
    "kite": Project(
        id="kite",
        label="kite",
        phrase="a kite so big it could have shaded a barn",
        boast="the biggest kite the county had ever squinted at",
        stage="for the Wind-Day Show",
        launch_place="the hill above the fairground",
        sky_line="rose into the blue like a painted fish learning to sing",
        needs_light=2,
        needs_flex=2,
        needs_strength=1,
        tags={"kite", "wind"},
    ),
    "sailcart": Project(
        id="sailcart",
        label="sailcart",
        phrase="a sailcart with wheels taller than butter churns",
        boast="the fastest sailcart ever to chase a cloud",
        stage="for the Dusty Prairie Race",
        launch_place="the long dirt track by the hay field",
        sky_line="leaned into the wind and skimmed the ground like a skipping plate",
        needs_light=3,
        needs_flex=1,
        needs_strength=2,
        tags={"sail", "wind"},
    ),
    "banner": Project(
        id="banner",
        label="parade banner",
        phrase="a parade banner long enough to tickle three chimneys at once",
        boast="the grandest parade banner in two counties and a rumor",
        stage="for the Brass-Bell Parade",
        launch_place="the main street between the feed store and the bakery",
        sky_line="streamed out bright and straight, snapping above the crowd like a happy river",
        needs_light=2,
        needs_flex=2,
        needs_strength=1,
        tags={"banner", "parade", "wind"},
    ),
}

MATERIALS = {
    "striped_silk": Material(
        id="striped_silk",
        label="striped silk",
        phrase="a roll of striped silk",
        stripes="thin blue and gold stripes",
        weight=1,
        flex=3,
        strength=2,
        source="a trader from Venice years ago",
        tags={"material", "cloth", "venetian"},
    ),
    "waxed_canvas": Material(
        id="waxed_canvas",
        label="waxed canvas",
        phrase="a sheet of waxed canvas",
        stripes="broad green stripes painted down the middle",
        weight=2,
        flex=2,
        strength=3,
        source="the old workshop chest",
        tags={"material", "cloth"},
    ),
    "paper_laminate": Material(
        id="paper_laminate",
        label="paper laminate",
        phrase="a roll of paper laminate",
        stripes="silver stripes that winked in the sun",
        weight=1,
        flex=2,
        strength=1,
        source="the shelf above the glue jars",
        tags={"material", "paper"},
    ),
}

MISTAKEN_ITEMS = {
    "blind_slats": MistakenItem(
        id="blind_slats",
        label="venetian blind slats",
        phrase="a stack of venetian blind slats",
        mistaken_reason="because they really were from a venetian blind",
        clatter="They clacked and rattled like a drawer full of spoons in a thunderstorm.",
        drag_text="The hard slats caught the gust sideways and dragged the whole contraption crooked",
        weight=5,
        flex=0,
        strength=2,
        tags={"venetian_blind", "misunderstanding"},
    ),
    "blind_rail": MistakenItem(
        id="blind_rail",
        label="the venetian blind rail",
        phrase="the long metal rail from a venetian blind",
        mistaken_reason="because the word venetian was stamped right on the dusty box",
        clatter="It sang and banged like a church bell tied to a wagon wheel.",
        drag_text="The rail made the whole thing nose-dive before the wind had even chosen a direction",
        weight=6,
        flex=0,
        strength=3,
        tags={"venetian_blind", "metal", "misunderstanding"},
    ),
    "blind_cord": MistakenItem(
        id="blind_cord",
        label="venetian blind cord",
        phrase="a fistful of venetian blind cord",
        mistaken_reason="because it looked stringy and useful enough for anything in a hurry",
        clatter="The cords whipped in knots and snapped at the air like angry noodles.",
        drag_text="The skinny cords bunched together and left more holes than sail",
        weight=1,
        flex=3,
        strength=0,
        tags={"venetian_blind", "cord", "misunderstanding"},
    ),
}

WINDS = {
    "breezy": Wind(
        id="breezy",
        label="a breezy afternoon",
        gust="a steady puff",
        exaggeration="The wind was lively enough to flip hats and turn laundry into flags.",
        force=1,
        tags={"wind"},
    ),
    "gusty": Wind(
        id="gusty",
        label="a gusty afternoon",
        gust="a barn-shoving gust",
        exaggeration="The wind came stomping over the fields as if it had boots on.",
        force=2,
        tags={"wind", "tall_tale"},
    ),
    "wild": Wind(
        id="wild",
        label="a wild afternoon",
        gust="a mountain-sized whoosh",
        exaggeration="The wind blew so hard even the scarecrows looked busy.",
        force=3,
        tags={"wind", "tall_tale"},
    ),
}

GIRL_NAMES = ["Mabel", "Cora", "June", "Lottie", "Pearl", "Tess", "Nell", "Ivy"]
BOY_NAMES = ["Hank", "Eli", "Beau", "Jasper", "Finn", "Otis", "Cal", "Ned"]
TRAITS = ["careful", "plainspoken", "steady", "thoughtful", "patient", "sensible"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id, project in PROJECTS.items():
        for material_id, material in MATERIALS.items():
            if not material_suits_project(material, project):
                continue
            for mistake_id, mistake in MISTAKEN_ITEMS.items():
                if mistake_fails_project(mistake, project):
                    combos.append((project_id, material_id, mistake_id))
    return combos


@dataclass
class StoryParams:
    project: str
    intended: str
    mistaken: str
    wind: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    helper_trait: str
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


def explain_rejection(project: Project, material: Material, mistake: MistakenItem) -> str:
    if not material_suits_project(material, project):
        return (
            f"(No story: {material.label} is not strong or well-suited enough for the "
            f"{project.label}. Pick a material that can honestly do the job.)"
        )
    if not mistake_fails_project(mistake, project):
        return (
            f"(No story: {mistake.label} would not actually cause the misunderstanding "
            f"disaster here, so the conflict would be weak. Pick a clearly unsuitable mistake.)"
        )
    return "(No story: this combination does not fit the world's misunderstanding logic.)"


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity,
              project: Project, wind: Wind) -> None:
    hero.memes["pride"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"In a town where the weather bragged louder than the people, {hero.id} "
        f"announced that {hero.pronoun()} would build {project.boast} {project.stage}."
    )
    world.say(
        f"{helper.id}, {hero.pronoun('possessive')} {next(iter(helper.traits), 'steady')} friend, "
        f"came to help, and {elder.label_word} worked at the bench with a tape measure tucked behind "
        f"{elder.pronoun('possessive')} ear. {wind.exaggeration}"
    )


def assign_task(world: World, hero: Entity, elder: Entity, material: Material, project: Project) -> None:
    world.say(
        f'At sunrise, {elder.label_word.capitalize()} pointed to the half-built {project.label} and said, '
        f'"Bring me the venetian material from the blue chest. It is {material.phrase}, '
        f'light enough for wind and strong enough for work."'
    )
    hero.memes["certainty"] += 1


def misunderstand(world: World, hero: Entity, helper: Entity, mistake: MistakenItem) -> None:
    hero.attrs["understanding"] = "wrong"
    hero.memes["boast"] += 1
    world.say(
        f"But {hero.id} heard only the word venetian and marched off to fetch {mistake.phrase}, "
        f"{mistake.mistaken_reason}."
    )
    world.say(
        f'"There," {hero.pronoun()} said proudly. "If this is not venetian material, then a mule is a teacup."'
    )
    helper.memes["doubt"] += 1


def warn(world: World, helper: Entity, hero: Entity, mistake: MistakenItem, project: Project) -> None:
    helper.memes["warning"] += 1
    world.say(
        f'{helper.id} frowned at the pile. "That is blind stuff, not cloth for a {project.label}," '
        f'{helper.pronoun()} said. "It looks too stiff, too heavy, and too wrong by half."'
    )
    world.say(
        f"But {hero.id} only hugged the mistake closer and said the wind would admire bold thinking."
    )
    hero.memes["warning_ignored"] += 1
    world.facts["warning_text"] = f"{mistake.label} looked too stiff and too heavy for the {project.label}"
    propagate(world, narrate=False)


def build_wrong(world: World, hero: Entity, helper: Entity, project: Project, mistake: MistakenItem) -> None:
    proj = world.get("project")
    proj.attrs["using"] = "wrong"
    proj.attrs["suitable"] = False
    proj.attrs["mistake"] = mistake.id
    proj.meters["assembled"] += 1
    world.say(
        f"So they tied and tugged and fastened the wrong pieces onto the {project.label} until it looked "
        f"as grand and troublesome as a porch trying to learn to fly."
    )
    world.say(mistake.clatter)


def quarrel(world: World, hero: Entity, helper: Entity) -> None:
    if hero.meters["conflict"] >= THRESHOLD:
        world.say(
            f'{helper.id} said they should stop and ask again, but {hero.id} crossed {hero.pronoun("possessive")} arms. '
            f'"No need," {hero.pronoun()} huffed. "I know what words mean."'
        )


def launch_wrong(world: World, hero: Entity, helper: Entity, project: Project, wind: Wind, mistake: MistakenItem) -> None:
    proj = world.get("project")
    proj.meters["launched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They hauled the {project.label} to {project.launch_place}, and the first {wind.gust} hit it."
    )
    if proj.meters["crashed"] >= THRESHOLD:
        world.say(
            f"{mistake.drag_text}. In one blink the great machine swung, bucked, and scattered dust like a herd of surprised chickens."
        )
        world.say(
            f"{helper.id} grabbed the tail rope, {hero.id} grabbed the frame, and both of them skidded until their shoes wrote long complaints in the dirt."
        )


def explain(world: World, elder: Entity, hero: Entity, helper: Entity, material: Material, mistake: MistakenItem) -> None:
    hero.memes["embarrassment"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{elder.label_word.capitalize()} came puffing after them and stared at the heap. "
        f'"Mercy on the workshop," {elder.pronoun()} said. "I asked for the venetian material, not pieces from a venetian blind."'
    )
    world.say(
        f'{elder.pronoun().capitalize()} held up {material.phrase}. "This is the material I meant. It came from {material.source}, '
        f'and the stripes are for beauty, not for blinds."'
    )
    world.say(
        f"{hero.id}'s ears turned pink. {helper.id} did not say I told you so, though it danced in the air between them."
    )


def rebuild_right(world: World, hero: Entity, helper: Entity, project: Project, material: Material) -> None:
    proj = world.get("project")
    proj.meters["launched"] = 0.0
    proj.attrs["using"] = "right"
    proj.attrs["suitable"] = True
    proj.attrs["material"] = material.id
    hero.memes["humility"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Back at the bench, they cut {material.phrase} with slow hands and careful eyes. "
        f"The {material.stripes} lay smooth across the frame, and this time even {hero.id} checked each knot twice."
    )


def launch_right(world: World, hero: Entity, helper: Entity, elder: Entity, project: Project, wind: Wind) -> None:
    proj = world.get("project")
    proj.meters["launched"] += 1
    propagate(world, narrate=False)
    if proj.meters["flying"] >= THRESHOLD:
        world.say(
            f"When they carried the rebuilt {project.label} out again, the same {wind.gust} caught it kindly. "
            f"It {project.sky_line}."
        )
        world.say(
            f"Folks at the edge of town tipped back their heads and laughed, and even {elder.label_word} looked pleased enough to iron a rainbow."
        )


def lesson(world: World, elder: Entity, hero: Entity, helper: Entity) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'Then {elder.label_word.capitalize()} rested a hand on {hero.id}\'s shoulder. '
        f'"Big plans need more than big talk," {elder.pronoun()} said. "When words sound strange, ask what they mean before you argue with a friend."'
    )
    world.say(
        f'{hero.id} nodded. "Next time I will ask first," {hero.pronoun()} said. '
        f'{helper.id} smiled, because the quarrel had blown away at last.'
    )
    world.say(
        f"And from then on, whenever a new word rolled into the workshop, {hero.id} asked about it before touching a single nail, knot, or scrap of material."
    )


def tell(project: Project, material: Material, mistake: MistakenItem, wind: Wind,
         hero_name: str = "Mabel", hero_gender: str = "girl",
         helper_name: str = "Hank", helper_gender: str = "boy",
         elder_type: str = "uncle", helper_trait: str = "careful") -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["boastful"],
        attrs={"display_name": hero_name, "understanding": "right"},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=[helper_trait],
        attrs={"display_name": helper_name},
        tags={"child"},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        role="elder",
        attrs={"display_name": elder_type},
        tags={"adult"},
    ))
    proj = world.add(Entity(
        id="project",
        kind="thing",
        type=project.id,
        label=project.label,
        role="project",
        attrs={"suitable": False, "using": "", "material": "", "mistake": ""},
        tags=set(project.tags),
    ))

    world.facts.update(
        project_cfg=project,
        material_cfg=material,
        mistake_cfg=mistake,
        wind_cfg=wind,
        hero=hero,
        helper=helper,
        elder=elder,
        project=proj,
    )

    introduce(world, hero, helper, elder, project, wind)
    assign_task(world, hero, elder, material, project)

    world.para()
    misunderstand(world, hero, helper, mistake)
    warn(world, helper, hero, mistake, project)
    build_wrong(world, hero, helper, project, mistake)
    quarrel(world, hero, helper)

    world.para()
    launch_wrong(world, hero, helper, project, wind, mistake)
    explain(world, elder, hero, helper, material, mistake)

    world.para()
    rebuild_right(world, hero, helper, project, material)
    launch_right(world, hero, helper, elder, project, wind)
    lesson(world, elder, hero, helper)

    world.facts.update(
        conflict=hero.meters["conflict"] >= THRESHOLD or helper.meters["conflict"] >= THRESHOLD,
        crashed=proj.meters["crashed"] >= THRESHOLD,
        succeeded=proj.meters["flying"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "venetian_blind": [
        (
            "What is a venetian blind?",
            "A venetian blind is a window covering made from many slats. You can tilt the slats to let in more or less light.",
        )
    ],
    "material": [
        (
            "What does the word material mean?",
            "Material means the stuff something is made from, like cloth, wood, paper, or metal. Different materials work better for different jobs.",
        )
    ],
    "kite": [
        (
            "Why does a kite need light material?",
            "A kite has to be light enough for the wind to lift. If it is too heavy or too stiff, it will pull down instead of rising up.",
        )
    ],
    "sail": [
        (
            "Why does a sail need strong material?",
            "A sail has to catch wind without tearing apart. Strong material helps it hold its shape while the wind pushes on it.",
        )
    ],
    "banner": [
        (
            "Why should a parade banner bend a little?",
            "A banner needs to bend and ripple so the wind can move through it. If it is too rigid, it jerks and twists instead of streaming nicely.",
        )
    ],
    "ask": [
        (
            "What should you do if you do not understand a word?",
            "You should ask what the word means. Asking a calm question can stop a mistake before it turns into a problem.",
        )
    ],
    "wind": [
        (
            "What can wind do to cloth and heavy objects?",
            "Wind can lift cloth that is light and shaped well, but it can shove or drag heavy awkward things. That is why builders choose materials carefully.",
        )
    ],
}
KNOWLEDGE_ORDER = ["venetian_blind", "material", "kite", "sail", "banner", "ask", "wind"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display_name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    project = world.facts["project_cfg"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a tall tale for a young child that includes the words "venetian" and "material" and centers on a misunderstanding about building a {project.label}.',
        f"Tell a windy story where {display_name(hero)} mistakes the phrase 'venetian material,' argues with {display_name(helper)}, and learns to ask questions before boasting.",
        f"Write a child-friendly story with a misunderstanding, a quarrel, and a lesson learned, ending with a giant {project.label} working the right way at last.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    elder = world.facts["elder"]
    project = world.facts["project_cfg"]
    material = world.facts["material_cfg"]
    mistake = world.facts["mistake_cfg"]
    wind = world.facts["wind_cfg"]
    hero_name = display_name(hero)
    helper_name = display_name(helper)
    elder_word = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, who wanted to build {project.boast}, with help from {helper_name} and {elder_word}. The story follows how a big misunderstanding turned into a better choice.",
        ),
        (
            f"What misunderstanding started the trouble?",
            f"{hero_name} heard the phrase 'venetian material' and thought it meant parts from a venetian blind, so {hero.pronoun()} fetched {mistake.label} instead of {material.label}. The mistake happened because {hero.pronoun()} grabbed one familiar meaning of the word venetian and never asked what {elder_word} meant.",
        ),
        (
            f"Why did {helper_name} object?",
            f"{helper_name} could see that {mistake.label} was too stiff or heavy for the {project.label}. That warning mattered because wind can only help when the material fits the job.",
        ),
    ]
    if world.facts.get("conflict"):
        qa.append(
            (
                f"How did the misunderstanding cause a conflict?",
                f"The children argued because {hero_name} felt sure {hero.pronoun()} was right, while {helper_name} wanted to stop and ask again. Their quarrel grew from pride on one side and worry on the other.",
            )
        )
    if world.facts.get("crashed"):
        qa.append(
            (
                f"What happened when they tried to use the wrong material?",
                f"The first launch went badly, and the {project.label} dragged and bucked instead of working. That happened because the wrong pieces could not bend and catch the wind the way real building material should.",
            )
        )
    if world.facts.get("succeeded"):
        qa.append(
            (
                f"How did they finally fix the problem?",
                f"{elder_word.capitalize()} explained the phrase, and they rebuilt with {material.label} instead. Once the right material was on the frame, the same wind helped the {project.label} work beautifully.",
            )
        )
    if world.facts.get("learned"):
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero_name} learned to ask what a strange word means before arguing or showing off. The happy ending came only after {hero.pronoun()} listened, asked, and tried again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    project = world.facts["project_cfg"]
    tags = {"material", "ask", "wind", "venetian_blind"}
    if "kite" in project.tags:
        tags.add("kite")
    if "sail" in project.tags:
        tags.add("sail")
    if "banner" in project.tags:
        tags.add("banner")
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
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="kite",
        intended="striped_silk",
        mistaken="blind_slats",
        wind="gusty",
        hero="Mabel",
        hero_gender="girl",
        helper="Hank",
        helper_gender="boy",
        elder="uncle",
        helper_trait="careful",
    ),
    StoryParams(
        project="sailcart",
        intended="waxed_canvas",
        mistaken="blind_rail",
        wind="wild",
        hero="Jasper",
        hero_gender="boy",
        helper="June",
        helper_gender="girl",
        elder="aunt",
        helper_trait="steady",
    ),
    StoryParams(
        project="banner",
        intended="paper_laminate",
        mistaken="blind_cord",
        wind="breezy",
        hero="Pearl",
        hero_gender="girl",
        helper="Otis",
        helper_gender="boy",
        elder="uncle",
        helper_trait="thoughtful",
    ),
    StoryParams(
        project="banner",
        intended="striped_silk",
        mistaken="blind_slats",
        wind="wild",
        hero="Cal",
        hero_gender="boy",
        helper="Lottie",
        helper_gender="girl",
        elder="aunt",
        helper_trait="patient",
    ),
]


ASP_RULES = r"""
valid(P, M, X) :-
    project(P),
    material(M),
    mistaken(X),
    mat_weight(M, W), mat_flex(M, F), mat_strength(M, S),
    needs_light(P, LW), needs_flex(P, LF), needs_strength(P, LS),
    W <= LW, F >= LF, S >= LS,
    wrong_weight(X, WW), wrong_flex(X, WF), wrong_strength(X, WS),
    (WW > LW; WF < LF; WS < LS).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("needs_light", pid, p.needs_light))
        lines.append(asp.fact("needs_flex", pid, p.needs_flex))
        lines.append(asp.fact("needs_strength", pid, p.needs_strength))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("mat_weight", mid, m.weight))
        lines.append(asp.fact("mat_flex", mid, m.flex))
        lines.append(asp.fact("mat_strength", mid, m.strength))
    for xid, x in MISTAKEN_ITEMS.items():
        lines.append(asp.fact("mistaken", xid))
        lines.append(asp.fact("wrong_weight", xid, x.weight))
        lines.append(asp.fact("wrong_flex", xid, x.flex))
        lines.append(asp.fact("wrong_strength", xid, x.strength))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale misunderstanding world: the wrong venetian material, a quarrel, and a lesson."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--intended", choices=MATERIALS)
    ap.add_argument("--mistaken", choices=MISTAKEN_ITEMS)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--elder", choices=["uncle", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.intended:
        project = PROJECTS[args.project]
        material = MATERIALS[args.intended]
        mistake = MISTAKEN_ITEMS[args.mistaken] if args.mistaken else next(iter(MISTAKEN_ITEMS.values()))
        if not material_suits_project(material, project):
            raise StoryError(explain_rejection(project, material, mistake))
    if args.project and args.mistaken:
        project = PROJECTS[args.project]
        material = MATERIALS[args.intended] if args.intended else next(iter(MATERIALS.values()))
        mistake = MISTAKEN_ITEMS[args.mistaken]
        if not mistake_fails_project(mistake, project):
            raise StoryError(explain_rejection(project, material, mistake))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.intended is None or combo[1] == args.intended)
        and (args.mistaken is None or combo[2] == args.mistaken)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, intended_id, mistaken_id = rng.choice(sorted(combos))
    wind_id = args.wind or rng.choice(sorted(WINDS))
    hero_name, hero_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=hero_name)
    elder = args.elder or rng.choice(["uncle", "aunt"])
    helper_trait = rng.choice(TRAITS)
    return StoryParams(
        project=project_id,
        intended=intended_id,
        mistaken=mistaken_id,
        wind=wind_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        elder=elder,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.intended not in MATERIALS:
        raise StoryError(f"(Unknown intended material: {params.intended})")
    if params.mistaken not in MISTAKEN_ITEMS:
        raise StoryError(f"(Unknown mistaken item: {params.mistaken})")
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind: {params.wind})")
    if params.elder not in {"uncle", "aunt"}:
        raise StoryError(f"(Unknown elder type: {params.elder})")

    project = PROJECTS[params.project]
    material = MATERIALS[params.intended]
    mistake = MISTAKEN_ITEMS[params.mistaken]
    if not (material_suits_project(material, project) and mistake_fails_project(mistake, project)):
        raise StoryError(explain_rejection(project, material, mistake))

    world = tell(
        project=project,
        material=material,
        mistake=mistake,
        wind=WINDS[params.wind],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
        helper_trait=params.helper_trait,
    )

    story = world.render()
    hero_name = params.hero
    helper_name = params.helper
    story = story.replace("hero", hero_name).replace("helper", helper_name)
    story = story.replace("elder", params.elder.capitalize())

    return StorySample(
        params=params,
        story=story,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        default_params.seed = 123
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print("SMOKE FAIL: resolve_params() crashed on defaults:", err)

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if not sample.prompts or not sample.story_qa or not sample.world_qa:
                raise StoryError("missing prompts or QA")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL: generate() crashed for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (project, intended, mistaken) combos:\n")
        for project, intended, mistaken in combos:
            print(f"  {project:9} {intended:15} {mistaken}")
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
            header = f"### {p.hero} and {p.helper}: {p.project} with {p.intended} after {p.mistaken}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
