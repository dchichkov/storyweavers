#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py
================================================================

A standalone storyworld for a tiny mythic domain: a curious child meddles with
festival pasta dough, the dough changes in a physically meaningful way, a wise
elder repairs it with the right method, and the story ends in a joyful feast.

The world is intentionally small and constraint-driven. Different myths vary
the sacred spring, the kind of pasta, the curious mistake, and the remedy. The
reasonableness gate refuses silly repair choices: resting a salty dough will
not remove salt, and adding a fresh piece of dough will not fix a dry skin.

Run it
------
    python storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py
    python storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py --origin moon_spring --mishap extra_flour
    python storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py --mishap extra_salt --remedy cover_and_rest
    python storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py --all
    python storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pasta_happy_ending_curiosity_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
class Origin:
    id: str
    place: str
    spring_name: str
    blessing: str
    sky_image: str
    closing_image: str
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
class PastaKind:
    id: str
    label: str
    dough_name: str
    shape_line: str
    serving_line: str
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
class Mishap:
    id: str
    act_line: str
    consequence_line: str
    problem: str
    severity: int
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
class Remedy:
    id: str
    label: str
    works_for: set[str]
    action_line: str
    qa_line: str
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


def _r_dough_trouble(world: World) -> list[str]:
    dough = world.get("dough")
    child = world.get("child")
    elder = world.get("elder")
    out: list[str] = []
    if dough.meters["dry"] >= THRESHOLD:
        sig = ("trouble", "dry")
        if sig not in world.fired:
            world.fired.add(sig)
            dough.meters["troubled"] += 1
            child.memes["worry"] += 1
            elder.memes["concern"] += 1
            out.append("__dry__")
    if dough.meters["crumbly"] >= THRESHOLD:
        sig = ("trouble", "crumbly")
        if sig not in world.fired:
            world.fired.add(sig)
            dough.meters["troubled"] += 1
            child.memes["worry"] += 1
            elder.memes["concern"] += 1
            out.append("__crumbly__")
    if dough.meters["salty"] >= THRESHOLD:
        sig = ("trouble", "salty")
        if sig not in world.fired:
            world.fired.add(sig)
            dough.meters["troubled"] += 1
            child.memes["worry"] += 1
            elder.memes["concern"] += 1
            out.append("__salty__")
    return out


def _r_repaired(world: World) -> list[str]:
    dough = world.get("dough")
    child = world.get("child")
    elder = world.get("elder")
    if dough.meters["troubled"] < THRESHOLD:
        return []
    if dough.meters["dry"] >= THRESHOLD or dough.meters["crumbly"] >= THRESHOLD or dough.meters["salty"] >= THRESHOLD:
        return []
    sig = ("repaired",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dough.meters["smooth"] += 1
    child.memes["relief"] += 1
    elder.memes["relief"] += 1
    return ["__repaired__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="dough_trouble", tag="physical", apply=_r_dough_trouble),
    Rule(name="repaired", tag="physical", apply=_r_repaired),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


ORIGINS = {
    "moon_spring": Origin(
        id="moon_spring",
        place="the white hill village",
        spring_name="the Moon Spring",
        blessing="old people said its water listened to gentle hands",
        sky_image="Above the roofs, the evening moon looked like a silver bowl.",
        closing_image="the moon shone in the broth like a quiet coin",
        tags={"spring", "moon"},
    ),
    "sun_cistern": Origin(
        id="sun_cistern",
        place="the stone town by the terraces",
        spring_name="the Sun Cistern",
        blessing="old people said its water kept the warmth of dawn",
        sky_image="High above the terraces, the last gold of day still clung to the sky.",
        closing_image="the last gold of evening trembled in every spoonful",
        tags={"water", "sun"},
    ),
    "sea_grotto": Origin(
        id="sea_grotto",
        place="the cliff village above the blue sea",
        spring_name="the Sea Grotto",
        blessing="old people said its water remembered songs from under the waves",
        sky_image="Far below, the sea flashed blue under a sky already turning violet.",
        closing_image="the sea wind slipped through the doorway while everyone ate smiling",
        tags={"water", "sea"},
    ),
}

PASTAS = {
    "ribbons": PastaKind(
        id="ribbons",
        label="long ribbon pasta",
        dough_name="the ribbon dough",
        shape_line="Soon the dough would be rolled into long shining ribbons, fit for a feast.",
        serving_line="The bowls filled with long ribbon pasta curling like little streams.",
        tags={"pasta", "dough"},
    ),
    "shells": PastaKind(
        id="shells",
        label="little shell pasta",
        dough_name="the shell dough",
        shape_line="Soon the dough would be pinched into little shell pasta for the festival table.",
        serving_line="The bowls filled with little shell pasta that held bright drops of sauce.",
        tags={"pasta", "shape"},
    ),
    "stars": PastaKind(
        id="stars",
        label="star pasta",
        dough_name="the star dough",
        shape_line="Soon the dough would be cut into tiny stars, as children always hoped on feast night.",
        serving_line="The bowls filled with star pasta, and each piece looked ready to carry a wish.",
        tags={"pasta", "stars"},
    ),
}

MISHAPS = {
    "peek_cloth": Mishap(
        id="peek_cloth",
        act_line="When the elder stepped out to greet a neighbor, the child lifted the warm resting cloth to see whether the dough truly breathed.",
        consequence_line="Cool air kissed the top of the dough, and a thin dry skin tightened over it.",
        problem="dry",
        severity=1,
        tags={"patience", "dough"},
    ),
    "extra_flour": Mishap(
        id="extra_flour",
        act_line="The child, wondering how softness was made, tipped in an extra cloud of flour to learn whether more white dust meant better pasta.",
        consequence_line="At once the dough lost its easy stretch and broke into tired, crumbly pieces.",
        problem="crumbly",
        severity=1,
        tags={"flour", "dough"},
    ),
    "extra_salt": Mishap(
        id="extra_salt",
        act_line="The child, curious about the bright jar by the bowl, shook in another pinch of salt to see whether the dough would grow wiser.",
        consequence_line="The elder touched the dough and tasted a grain from her fingertip; the dough had become far too salty for the feast.",
        problem="salty",
        severity=1,
        tags={"salt", "dough"},
    ),
}

REMEDIES = {
    "warm_water_knead": Remedy(
        id="warm_water_knead",
        label="warm spring water and kneading",
        works_for={"dry", "crumbly"},
        action_line="The elder poured in a little warm water from the sacred spring and kneaded slowly until the dough turned supple again.",
        qa_line="The elder added warm water and kneaded the dough until it grew soft and smooth again.",
        tags={"water", "knead"},
    ),
    "cover_and_rest": Remedy(
        id="cover_and_rest",
        label="covering and resting",
        works_for={"dry"},
        action_line="The elder brushed the top with a little water, laid the cloth back over it, and let the dough rest in quiet warmth until the dry skin softened.",
        qa_line="The elder covered the dough again and let it rest so the dry top could soften.",
        tags={"patience", "rest"},
    ),
    "fresh_piece": Remedy(
        id="fresh_piece",
        label="mixing in a fresh piece of dough",
        works_for={"salty"},
        action_line="The elder mixed a new, unsalted piece of dough and folded it in, so the sharp salt spread out and became gentle enough for supper.",
        qa_line="The elder mixed in a fresh piece of unsalted dough to balance the salt.",
        tags={"salt", "balance"},
    ),
    "song_only": Remedy(
        id="song_only",
        label="singing over the bowl",
        works_for=set(),
        action_line="The elder sang to the bowl alone.",
        qa_line="The elder only sang to the bowl.",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tala", "Nia", "Elia", "Sora", "Vera", "Dina"]
BOY_NAMES = ["Ivo", "Tomas", "Niko", "Pavel", "Leo", "Sami", "Rian", "Milo"]


def problem_of(mishap_id: str) -> str:
    return MISHAPS[mishap_id].problem


def remedy_works(mishap_id: str, remedy_id: str) -> bool:
    if mishap_id not in MISHAPS or remedy_id not in REMEDIES:
        return False
    return MISHAPS[mishap_id].problem in REMEDIES[remedy_id].works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for origin_id in ORIGINS:
        for pasta_id in PASTAS:
            for mishap_id in MISHAPS:
                for remedy_id in REMEDIES:
                    if remedy_works(mishap_id, remedy_id):
                        combos.append((origin_id, pasta_id, mishap_id, remedy_id))
    return combos


@dataclass
class StoryParams:
    origin: str
    pasta: str
    mishap: str
    remedy: str
    child_name: str
    child_gender: str
    elder_type: str
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
        origin="moon_spring",
        pasta="ribbons",
        mishap="peek_cloth",
        remedy="cover_and_rest",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        origin="sun_cistern",
        pasta="shells",
        mishap="extra_flour",
        remedy="warm_water_knead",
        child_name="Leo",
        child_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        origin="sea_grotto",
        pasta="stars",
        mishap="extra_salt",
        remedy="fresh_piece",
        child_name="Tala",
        child_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        origin="moon_spring",
        pasta="stars",
        mishap="peek_cloth",
        remedy="warm_water_knead",
        child_name="Niko",
        child_gender="boy",
        elder_type="grandfather",
    ),
]


def explain_rejection(mishap_id: str, remedy_id: str) -> str:
    mishap = MISHAPS[mishap_id]
    remedy = REMEDIES[remedy_id]
    if remedy.id == "song_only":
        return (
            "(No story: singing alone may be lovely, but it does not physically repair "
            "festival pasta dough. Pick a remedy that actually changes the dough.)"
        )
    return (
        f"(No story: {remedy.label} does not honestly fix dough made {mishap.problem} "
        f"by this mistake. Choose a remedy that matches the problem.)"
    )


def introduce(world: World, child: Entity, elder: Entity, origin: Origin, pasta: PastaKind) -> None:
    child.memes["curiosity"] += 1
    child.memes["love"] += 1
    world.say(
        f"In {origin.place}, people told an old kitchen myth: when water from {origin.spring_name} met patient hands, supper carried a blessing. "
        f"{origin.blessing}."
    )
    world.say(
        f"{origin.sky_image} In one small house, {child.id} stood beside {child.pronoun('possessive')} {elder.label_word} while they prepared {pasta.label} for the feast."
    )
    world.say(pasta.shape_line)


def warning(world: World, child: Entity, elder: Entity, origin: Origin) -> None:
    world.say(
        f'"Watch with your eyes first," {elder.label_word.capitalize()} said. "The dough listens to hands, but it also listens to waiting. Water from {origin.spring_name} helps best when we do not rush it."'
    )


def curiosity_act(world: World, child: Entity, mishap: Mishap) -> None:
    dough = world.get("dough")
    child.memes["curiosity"] += 1
    child.memes["guilt"] = 0.0
    world.say(mishap.act_line)
    if mishap.problem == "dry":
        dough.meters["dry"] += 1
    elif mishap.problem == "crumbly":
        dough.meters["crumbly"] += 1
    elif mishap.problem == "salty":
        dough.meters["salty"] += 1
    propagate(world, narrate=False)
    child.memes["guilt"] += 1
    world.say(mishap.consequence_line)


def discover(world: World, child: Entity, elder: Entity, mishap: Mishap) -> None:
    if mishap.problem == "dry":
        detail = "It no longer looked glossy and alive. It looked shy and tight."
    elif mishap.problem == "crumbly":
        detail = "Instead of bending together, the pieces fell apart like pale sand."
    else:
        detail = "One taste was enough to tell the trouble; no one would want a bowl that sharp with salt."
    world.say(
        f"{child.id}'s heart sank. {detail} {child.pronoun().capitalize()} told {elder.label_word} the truth instead of hiding it."
    )


def repair(world: World, child: Entity, elder: Entity, remedy: Remedy, mishap: Mishap) -> None:
    dough = world.get("dough")
    elder.memes["care"] += 1
    world.say(
        f"{elder.label_word.capitalize()} did not scold. {elder.pronoun().capitalize()} smiled a little and said, "
        f'"Curiosity can open a door, but then we must learn how to mend what we touch."'
    )
    if remedy.id == "warm_water_knead":
        dough.meters["dry"] = 0.0
        dough.meters["crumbly"] = 0.0
    elif remedy.id == "cover_and_rest":
        dough.meters["dry"] = 0.0
        dough.meters["rested"] += 1
    elif remedy.id == "fresh_piece":
        dough.meters["salty"] = 0.0
        dough.meters["fresh_added"] += 1
    propagate(world, narrate=False)
    world.say(remedy.action_line)


def finish_feast(world: World, child: Entity, elder: Entity, origin: Origin, pasta: PastaKind) -> None:
    dough = world.get("dough")
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0.0
    child.memes["guilt"] = 0.0
    dough.meters["cut"] += 1
    dough.meters["cooked"] += 1
    dough.meters["served"] += 1
    world.say(
        f"Together they rolled, cut, and cooked the pasta at last. {pasta.serving_line}"
    )
    world.say(
        f"When the family gathered, {child.id} carried the first bowl carefully to the table. {origin.closing_image}, and the child understood that asking, waiting, and fixing were all part of wisdom."
    )


def tell(
    origin: Origin,
    pasta: PastaKind,
    mishap: Mishap,
    remedy: Remedy,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={},
        )
    )
    dough = world.add(
        Entity(
            id="dough",
            kind="thing",
            type="dough",
            label=pasta.dough_name,
            attrs={},
        )
    )

    dough.meters["dry"] = 0.0
    dough.meters["crumbly"] = 0.0
    dough.meters["salty"] = 0.0
    dough.meters["troubled"] = 0.0
    dough.meters["smooth"] = 1.0
    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["guilt"] = 0.0
    elder.memes["concern"] = 0.0
    elder.memes["relief"] = 0.0
    elder.memes["care"] = 0.0

    world.facts["origin"] = origin
    world.facts["pasta"] = pasta
    world.facts["mishap"] = mishap
    world.facts["remedy"] = remedy
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["dough"] = dough

    introduce(world, child, elder, origin, pasta)
    warning(world, child, elder, origin)

    world.para()
    curiosity_act(world, child, mishap)
    discover(world, child, elder, mishap)

    world.para()
    repair(world, child, elder, remedy, mishap)
    finish_feast(world, child, elder, origin, pasta)

    world.facts.update(
        problem=mishap.problem,
        repaired=(dough.meters["dry"] < THRESHOLD and dough.meters["crumbly"] < THRESHOLD and dough.meters["salty"] < THRESHOLD),
        happy_end=(dough.meters["served"] >= THRESHOLD),
    )
    return world


KNOWLEDGE = {
    "pasta": [
        (
            "What is pasta?",
            "Pasta is food made from dough, usually with flour and water. People shape it into noodles or little pieces and cook it until it is soft."
        )
    ],
    "dough": [
        (
            "What is dough?",
            "Dough is a soft mixture that can be rolled, stretched, or shaped. If it gets too dry or too crumbly, it is harder to use."
        )
    ],
    "flour": [
        (
            "What does flour do in dough?",
            "Flour helps build the body of the dough. But too much flour can make dough dry and crumbly instead of smooth."
        )
    ],
    "salt": [
        (
            "Why do people put salt in food?",
            "A little salt can help food taste better. Too much salt makes the taste too sharp and unpleasant."
        )
    ],
    "water": [
        (
            "Why can water help dough?",
            "Water helps dry dough soften and come together. That is why a cook may add a little warm water when dough feels stiff or crumbly."
        )
    ],
    "patience": [
        (
            "Why does waiting matter in cooking?",
            "Some foods need time to rest so their texture can change gently. Waiting can be part of cooking, not just something that happens before it."
        )
    ],
    "rest": [
        (
            "What does it mean to let dough rest?",
            "Letting dough rest means leaving it quietly for a little while. This can help it soften and become easier to shape."
        )
    ],
    "knead": [
        (
            "What does kneading do?",
            "Kneading means pressing and folding dough again and again. It helps the dough come together and feel smoother."
        )
    ],
}
KNOWLEDGE_ORDER = ["pasta", "dough", "flour", "salt", "water", "patience", "rest", "knead"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mishap = f["mishap"]
    pasta = f["pasta"]
    origin = f["origin"]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the word "pasta" and follows a curious child who makes a small mistake in the kitchen.',
        f"Tell a gentle myth set near {origin.spring_name} where {child.id} is curious about festival {pasta.label}, causes a problem by {mishap.id.replace('_', ' ')}, and learns how to help fix it.",
        "Write a warm story with curiosity, a wise elder, a simple cooking problem, and a happy ending that ends with a shared meal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    pasta = f["pasta"]
    origin = f["origin"]
    mishap = f["mishap"]
    remedy = f["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {child.pronoun('possessive')} {elder.label_word}, who is making festival {pasta.label}. They live in a place where people tell stories about {origin.spring_name}."
        ),
        (
            "Why did the child touch the dough?",
            f"{child.id} was curious and wanted to understand how the festival pasta was made. The mistake came from wanting to know more, not from wanting to spoil supper."
        ),
        (
            "What went wrong with the dough?",
            f"The dough became {mishap.problem}. That happened because {mishap.act_line.lower()} {mishap.consequence_line.lower()}"
        ),
        (
            "How did the elder fix the problem?",
            f"{elder.label_word.capitalize()} used {remedy.label}. {remedy.qa_line} That worked because the dough's real problem was that it had become {mishap.problem}."
        ),
        (
            "How did the story end?",
            f"It ended happily with the pasta cooked and shared at the table. The ending shows that curiosity can lead to wisdom when people tell the truth and help mend a mistake."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["pasta"].tags) | set(world.facts["mishap"].tags) | set(world.facts["remedy"].tags) | set(world.facts["origin"].tags)
    mapped: set[str] = set()
    if "pasta" in tags:
        mapped.add("pasta")
    if "dough" in tags or "shape" in tags:
        mapped.add("dough")
    if "flour" in tags:
        mapped.add("flour")
    if "salt" in tags or "balance" in tags:
        mapped.add("salt")
    if "water" in tags or "spring" in tags or "sea" in tags or "sun" in tags:
        mapped.add("water")
    if "patience" in tags:
        mapped.add("patience")
    if "rest" in tags:
        mapped.add("rest")
    if "knead" in tags:
        mapped.add("knead")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in mapped:
            out.extend(KNOWLEDGE[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(M, P) :- mishap(M), causes(M, P).
valid(O, Pa, M, R) :- origin(O), pasta(Pa), mishap(M), remedy(R), problem(M, P), fixes(R, P).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for origin_id in ORIGINS:
        lines.append(asp.fact("origin", origin_id))
    for pasta_id in PASTAS:
        lines.append(asp.fact("pasta", pasta_id))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        lines.append(asp.fact("causes", mishap_id, mishap.problem))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for problem in sorted(remedy.works_for):
            lines.append(asp.fact("fixes", remedy_id, problem))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story or "pasta" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic pasta storyworld: a curious child makes a small dough mistake, a wise elder fixes it, and supper ends happily."
    )
    ap.add_argument("--origin", choices=ORIGINS)
    ap.add_argument("--pasta", choices=PASTAS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mishap and args.remedy and not remedy_works(args.mishap, args.remedy):
        raise StoryError(explain_rejection(args.mishap, args.remedy))

    combos = [
        c for c in valid_combos()
        if (args.origin is None or c[0] == args.origin)
        and (args.pasta is None or c[1] == args.pasta)
        and (args.mishap is None or c[2] == args.mishap)
        and (args.remedy is None or c[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    origin_id, pasta_id, mishap_id, remedy_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        origin=origin_id,
        pasta=pasta_id,
        mishap=mishap_id,
        remedy=remedy_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.origin not in ORIGINS:
        raise StoryError(f"(Unknown origin: {params.origin})")
    if params.pasta not in PASTAS:
        raise StoryError(f"(Unknown pasta: {params.pasta})")
    if params.mishap not in MISHAPS:
        raise StoryError(f"(Unknown mishap: {params.mishap})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if not remedy_works(params.mishap, params.remedy):
        raise StoryError(explain_rejection(params.mishap, params.remedy))
    world = tell(
        origin=ORIGINS[params.origin],
        pasta=PASTAS[params.pasta],
        mishap=MISHAPS[params.mishap],
        remedy=REMEDIES[params.remedy],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (origin, pasta, mishap, remedy) combos:\n")
        for origin_id, pasta_id, mishap_id, remedy_id in combos:
            print(f"  {origin_id:11} {pasta_id:8} {mishap_id:12} {remedy_id}")
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
            header = f"### {p.child_name}: {p.pasta} / {p.mishap} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
