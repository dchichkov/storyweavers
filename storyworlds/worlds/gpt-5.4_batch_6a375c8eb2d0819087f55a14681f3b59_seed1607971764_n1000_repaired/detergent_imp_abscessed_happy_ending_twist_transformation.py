#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py
========================================================================================

A standalone story world in a mythic mode: a child meets a grimy little imp near
a sacred spring, learns that the trouble comes from an abscessed guardian wound,
and helps heal it with the right cleansing wash. In the twist, the imp is not an
enemy at all but pain given shape; once the wound is cleaned, the imp transforms
into a bright helper and the valley is restored.

Run it
------
    python storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py
    python storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py --guardian lion --cleanser soaproot
    python storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py --cleanser lye
    python storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py --all
    python storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py --qa --json
    python storyworlds/worlds/gpt-5.4/detergent_imp_abscessed_happy_ending_twist_transformation.py --verify
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
GENTLE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    living: bool = False
    material: str = ""
    # physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"priestess": "priestess", "priest": "priest", "mother": "mother", "father": "father"}.get(
            self.type, self.type
        )
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
    sacred_object: str
    sky: str
    closing: str
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
class Guardian:
    id: str
    label: str
    title: str
    material: str
    body_part: str
    track: str
    gift: str
    final_image: str
    living: bool = True
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
class Cleanser:
    id: str
    label: str
    phrase: str
    scent: str
    strength: int
    safe_materials: set[str] = field(default_factory=set)
    detergent_word: str = "detergent"
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
class Helper:
    id: str
    label: str
    title: str
    method: str
    lesson: str
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
class ImpForm:
    id: str
    dark_label: str
    bright_label: str
    motion: str
    bright_motion: str
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


def _r_abscess_leaks(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.get("guardian")
    imp = world.get("imp")
    spring = world.get("spring")
    if guardian.meters["abscessed"] < THRESHOLD:
        return out
    sig = ("abscess_leaks",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    imp.meters["manifest"] += 1
    imp.meters["soot"] += 1
    spring.meters["clouded"] += 1
    guardian.memes["pain"] += 1
    out.append("__leak__")
    return out


def _r_cloud_fear(world: World) -> list[str]:
    out: list[str] = []
    spring = world.get("spring")
    child = world.get("child")
    if spring.meters["clouded"] < THRESHOLD:
        return out
    sig = ("cloud_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__fear__")
    return out


def _r_heal_clears(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.get("guardian")
    spring = world.get("spring")
    imp = world.get("imp")
    if guardian.meters["washed"] < THRESHOLD or guardian.meters["soot_removed"] < THRESHOLD:
        return out
    sig = ("heal_clears",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guardian.meters["abscessed"] = 0.0
    guardian.meters["healed"] += 1
    spring.meters["clouded"] = 0.0
    spring.meters["clear"] += 1
    imp.meters["soot"] = 0.0
    imp.meters["bright"] += 1
    imp.memes["gratitude"] += 1
    out.append("__healed__")
    return out


CAUSAL_RULES = [
    Rule(name="abscess_leaks", tag="physical", apply=_r_abscess_leaks),
    Rule(name="cloud_fear", tag="emotional", apply=_r_cloud_fear),
    Rule(name="heal_clears", tag="physical", apply=_r_heal_clears),
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


def cleanser_fits(cleanser: Cleanser, guardian: Guardian) -> bool:
    return guardian.material in cleanser.safe_materials and cleanser.strength >= GENTLE_MIN


def explain_rejection(cleanser: Cleanser, guardian: Guardian) -> str:
    if guardian.material not in cleanser.safe_materials:
        return (
            f"(No story: {cleanser.label} is not safe for {guardian.material}. "
            f"The healing wash must fit the guardian's body, or the myth has no wise cure.)"
        )
    if cleanser.strength < GENTLE_MIN:
        return (
            f"(No story: {cleanser.label} is too harsh to cleanse an abscessed {guardian.body_part}. "
            f"A caring myth should choose a gentler wash.)"
        )
    return "(No story: this cleanser does not make a reasonable healing wash.)"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for guardian_id, guardian in GUARDIANS.items():
            for cleanser_id, cleanser in CLEANSERS.items():
                if not cleanser_fits(cleanser, guardian):
                    continue
                for helper_id in HELPERS:
                    for imp_id in IMP_FORMS:
                        combos.append((setting_id, guardian_id, cleanser_id, helper_id, imp_id))
    return combos


def predict_healing(world: World, cleanser_id: str) -> dict:
    sim = world.copy()
    cleanser = CLEANSERS[cleanser_id]
    guardian = GUARDIANS[sim.facts["guardian_cfg"].id]
    if cleanser_fits(cleanser, guardian):
        sim.get("guardian").meters["washed"] += 1
        sim.get("guardian").meters["soot_removed"] += 1
        propagate(sim, narrate=False)
    return {
        "heals": sim.get("guardian").meters["healed"] >= THRESHOLD,
        "spring_clear": sim.get("spring").meters["clear"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, setting: Setting, guardian: Guardian) -> None:
    world.say(
        f"In the old days, when {setting.sky}, a young keeper named {child.id} climbed to {setting.place}."
    )
    world.say(
        f"There stood {setting.sacred_object} and the valley's guardian, {guardian.title}, "
        f"whose {guardian.track} was said to bless every field below."
    )


def trouble(world: World, child: Entity, guardian: Entity, imp: Entity, setting: Setting, guardian_cfg: Guardian, imp_cfg: ImpForm) -> None:
    guardian.meters["abscessed"] += 1
    world.facts["wound_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"That dawn, the child saw that the guardian's {guardian_cfg.body_part} was abscessed, swollen like a bitter plum, "
        f"and the water in the basin had gone gray."
    )
    world.say(
        f"Out of the dim steam skipped {imp_cfg.dark_label}, a tiny imp that {imp_cfg.motion} along the rim and laughed at its own soot."
    )


def plea(world: World, child: Entity, helper: Entity, helper_cfg: Helper, cleanser: Cleanser) -> None:
    child.memes["resolve"] += 1
    world.say(
        f'{child.id} ran to {helper_cfg.title} of the shrine. "{helper.id}," the child cried, '
        f'"an imp is ruining the spring!"'
    )
    world.say(
        f'{helper.id} listened and shook {helper.pronoun("possessive")} head. '
        f'"Do not strike first," {helper.pronoun()} said. "Bring the {cleanser.phrase}, a {cleanser.scent} detergent wash. '
        f'{helper_cfg.lesson}"'
    )


def prepare(world: World, child: Entity, helper_cfg: Helper, cleanser: Cleanser, guardian_cfg: Guardian) -> None:
    pred = predict_healing(world, cleanser.id)
    world.facts["predicted_heals"] = pred["heals"]
    world.say(
        f"So {child.id} mixed the {cleanser.label} in a bronze bowl until the water shone pale and clean."
    )
    world.say(
        f"{helper_cfg.method} Together they walked back to the guardian, whose breath came slow with pain."
    )
    if pred["heals"]:
        world.say(
            f"The child hoped the gentle detergent would cleanse the abscessed {guardian_cfg.body_part} without hurting it."
        )


def reveal(world: World, child: Entity, helper: Entity, imp: Entity, guardian: Entity, imp_cfg: ImpForm) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"When {child.id} reached out, the imp did not bite. It trembled."
    )
    world.say(
        f'Then {helper.id} spoke the twist aloud: "Little one, this is no thief from the outer dark. '
        f'This imp was born from the guardian\'s pain."'
    )
    world.say(
        f"The tiny creature pressed itself against the swollen place, as if it belonged there all along."
    )


def heal(world: World, child: Entity, guardian: Entity, imp: Entity, cleanser: Cleanser, guardian_cfg: Guardian, imp_cfg: ImpForm) -> None:
    guardian.meters["washed"] += 1
    guardian.meters["soot_removed"] += 1
    child.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} bathed the abscessed {guardian_cfg.body_part} with the {cleanser.label}, and the dark crust loosened softly instead of tearing."
    )
    world.say(
        f"The imp spun once in a ring of steam. Its soot slid away like night from a hill."
    )
    if imp.meters["bright"] >= THRESHOLD:
        world.say(
            f"In that same breath came the transformation: the grim {imp_cfg.dark_label} became {imp_cfg.bright_label} that {imp_cfg.bright_motion}."
        )


def restoration(world: World, child: Entity, helper: Entity, guardian: Entity, setting: Setting, guardian_cfg: Guardian) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    guardian.memes["relief"] += 1
    world.say(
        f"The guardian lowered its head and drank. Clear water answered with a silver sound."
    )
    world.say(
        f'Seeing this, {helper.id} smiled. "Pain had put on a mask," {helper.pronoun()} said. '
        f'"Kind hands took the mask away."'
    )
    world.say(
        f"Before sunset, {guardian_cfg.gift}, and {setting.closing}."
    )
    world.say(guardian_cfg.final_image)


def tell(
    setting: Setting,
    guardian_cfg: Guardian,
    cleanser: Cleanser,
    helper_cfg: Helper,
    imp_cfg: ImpForm,
    child_name: str = "Nera",
    child_gender: str = "girl",
    helper_type: str = "priestess",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            living=True,
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label,
            kind="character",
            type=helper_type,
            label=helper_cfg.label,
            role="helper",
            living=True,
        )
    )
    guardian = world.add(
        Entity(
            id="guardian",
            kind="being",
            type="guardian",
            label=guardian_cfg.label,
            role="guardian",
            living=True,
            material=guardian_cfg.material,
        )
    )
    imp = world.add(
        Entity(
            id="imp",
            kind="being",
            type="imp",
            label=imp_cfg.dark_label,
            role="imp",
            living=True,
        )
    )
    spring = world.add(
        Entity(
            id="spring",
            kind="thing",
            type="spring",
            label="sacred spring",
            role="spring",
        )
    )

    world.facts.update(
        setting=setting,
        guardian_cfg=guardian_cfg,
        cleanser=cleanser,
        helper_cfg=helper_cfg,
        imp_cfg=imp_cfg,
        child=child,
        helper=helper,
    )

    # initialize rule-read values before propagation
    guardian.meters["abscessed"] = 0.0
    guardian.meters["washed"] = 0.0
    guardian.meters["soot_removed"] = 0.0
    guardian.meters["healed"] = 0.0
    imp.meters["manifest"] = 0.0
    imp.meters["soot"] = 0.0
    imp.meters["bright"] = 0.0
    spring.meters["clouded"] = 0.0
    spring.meters["clear"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["resolve"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["care"] = 0.0
    child.memes["joy"] = 0.0
    guardian.memes["pain"] = 0.0
    guardian.memes["relief"] = 0.0
    helper.memes["joy"] = 0.0
    imp.memes["gratitude"] = 0.0

    introduce(world, child, setting, guardian_cfg)
    world.para()
    trouble(world, child, guardian, imp, setting, guardian_cfg, imp_cfg)
    world.para()
    plea(world, child, helper, helper_cfg, cleanser)
    prepare(world, child, helper_cfg, cleanser, guardian_cfg)
    world.para()
    reveal(world, child, helper, imp, guardian, imp_cfg)
    heal(world, child, guardian, imp, cleanser, guardian_cfg, imp_cfg)
    world.para()
    restoration(world, child, helper, guardian, setting, guardian_cfg)

    world.facts.update(
        healed=guardian.meters["healed"] >= THRESHOLD,
        transformed=imp.meters["bright"] >= THRESHOLD,
        spring_clear=spring.meters["clear"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "laurel_spring": Setting(
        id="laurel_spring",
        place="the Laurel Spring under the hill of songs",
        sacred_object="a moon-carved basin",
        sky="stars were believed to sleep inside wells",
        closing="the women drawing water found their jars bright as mirrors",
        tags={"spring", "myth"},
    ),
    "cedar_steps": Setting(
        id="cedar_steps",
        place="the Cedar Steps above the misty valley",
        sacred_object="a cedar bowl blackened by centuries of incense",
        sky="the dawn was said to walk on the backs of cranes",
        closing="the shepherds below heard fresh water laughing in the channels",
        tags={"spring", "myth"},
    ),
    "sun_gate": Setting(
        id="sun_gate",
        place="the Sun Gate where a hidden spring rose from warm stone",
        sacred_object="a gold-rimmed cistern of old kings",
        sky="even the smallest brook was thought to remember the sun",
        closing="children ran with cups from house to house, sharing the first sweet draught",
        tags={"spring", "myth"},
    ),
}

GUARDIANS = {
    "lion": Guardian(
        id="lion",
        label="lion",
        title="Aurex the Lion of the Spring",
        material="fur",
        body_part="paw",
        track="golden pawprint",
        gift="the lion shook its mane, and the orchard leaves turned glossy with health",
        final_image="That night a lion's reflection slept in the water, untroubled and whole.",
        tags={"lion", "healing"},
    ),
    "crane": Guardian(
        id="crane",
        label="crane",
        title="Silvara the Crane of the Reed Moon",
        material="feather",
        body_part="wing joint",
        track="thin silver footprint",
        gift="the crane lifted its bright wings, and the reeds straightened as if listening to music",
        final_image="At moonrise, one white crane stood in the clear basin and looked like a piece of the moon.",
        tags={"crane", "healing"},
    ),
    "stag": Guardian(
        id="stag",
        label="stag",
        title="Theron the Stag Beneath the Pines",
        material="hide",
        body_part="shoulder",
        track="deep antler-shadow on the path",
        gift="the stag stamped once, and springs bubbled up among the roots of the pines",
        final_image="By dusk the stag's antlers held drops of water that shone like tiny stars.",
        tags={"stag", "healing"},
    ),
}

CLEANSERS = {
    "soaproot": Cleanser(
        id="soaproot",
        label="soaproot foam",
        phrase="soaproot foam from the herb jars",
        scent="green",
        strength=3,
        safe_materials={"fur", "feather", "hide"},
        detergent_word="detergent",
        tags={"soaproot", "detergent"},
    ),
    "olive": Cleanser(
        id="olive",
        label="olive-oil detergent",
        phrase="olive-oil detergent from the lamp room",
        scent="warm",
        strength=2,
        safe_materials={"fur", "hide"},
        detergent_word="detergent",
        tags={"olive", "detergent"},
    ),
    "dew": Cleanser(
        id="dew",
        label="dew-silk detergent",
        phrase="dew-silk detergent kept for holy cloth",
        scent="cool",
        strength=2,
        safe_materials={"feather", "hide"},
        detergent_word="detergent",
        tags={"dew", "detergent"},
    ),
    "lye": Cleanser(
        id="lye",
        label="lye wash",
        phrase="lye wash from the copper shelf",
        scent="sharp",
        strength=1,
        safe_materials={"stone"},
        detergent_word="detergent",
        tags={"lye", "detergent"},
    ),
}

HELPERS = {
    "priestess": Helper(
        id="priestess",
        label="Iria",
        title="Iria",
        method="The priestess wrapped clean linen around the child's hands.",
        lesson="If soot comes from pain, heal the pain and the soot will lose its home.",
        tags={"priestess", "healing"},
    ),
    "hermit": Helper(
        id="hermit",
        label="Old Sen",
        title="Old Sen",
        method="The hermit warmed the bowl between both palms and breathed a quiet blessing over it.",
        lesson="Not every dark thing is wicked; some dark things are only hurting.",
        tags={"hermit", "healing"},
    ),
}

IMP_FORMS = {
    "ember": ImpForm(
        id="ember",
        dark_label="an ember-imp",
        bright_label="a bright spark-bird",
        motion="skittered",
        bright_motion="circled the basin in rings of gold",
        tags={"imp", "transformation"},
    ),
    "soot": ImpForm(
        id="soot",
        dark_label="a soot-imp",
        bright_label="a blue moth of light",
        motion="danced",
        bright_motion="fluttered above the water like a living petal",
        tags={"imp", "transformation"},
    ),
    "cinder": ImpForm(
        id="cinder",
        dark_label="a cinder-imp",
        bright_label="a clear firefly spirit",
        motion="hopped",
        bright_motion="drifted between the reeds like a tiny lamp",
        tags={"imp", "transformation"},
    ),
}

GIRL_NAMES = ["Nera", "Lysa", "Mira", "Tala", "Eira", "Sela"]
BOY_NAMES = ["Doran", "Iven", "Tarin", "Nilo", "Pavel", "Soren"]


@dataclass
class StoryParams:
    setting: str
    guardian: str
    cleanser: str
    helper: str
    imp_form: str
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
    "detergent": [
        (
            "What is detergent?",
            "Detergent is a cleaning wash that helps loosen dirt and grease. In a healing story, a gentle detergent can clean without scraping a sore place."
        )
    ],
    "imp": [
        (
            "What is an imp in a myth?",
            "An imp is a tiny magical creature in old stories. It is often mischievous, but it is not always truly evil."
        )
    ],
    "abscessed": [
        (
            "What does abscessed mean?",
            "Abscessed means a place on the body is swollen and infected with trapped hurt inside. It is sore, and it needs careful cleaning and healing."
        )
    ],
    "soaproot": [
        (
            "What is soaproot?",
            "Soaproot is a plant whose roots can make a soft foam in water. People in stories may use it as a gentle natural cleaner."
        )
    ],
    "healing": [
        (
            "Why is gentle cleaning important for a wound?",
            "Gentle cleaning washes away dirt without making the sore place worse. That helps the body begin to heal."
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise that changes how you understand what was happening. It can make a scary problem look very different."
        )
    ],
    "transformation": [
        (
            "What is a transformation in a myth?",
            "A transformation is when a person or creature changes into a new form. In myths, the change often shows what it truly was inside."
        )
    ],
}
KNOWLEDGE_ORDER = ["detergent", "imp", "abscessed", "soaproot", "healing", "twist", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    guardian = f["guardian_cfg"]
    cleanser = f["cleanser"]
    imp_cfg = f["imp_cfg"]
    child = f["child"]
    return [
        f'Write a child-facing myth that includes the words "detergent", "imp", and "abscessed", where a sacred guardian is healed and the ending is happy.',
        f"Tell a mythic story about {child.id}, {guardian.title}, and {imp_cfg.dark_label}, where a gentle {cleanser.detergent_word} wash reveals a surprising truth.",
        "Write a short myth with a twist and a transformation: what looks like a wicked little creature is really pain in disguise, and kindness changes it."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    guardian = f["guardian_cfg"]
    cleanser = f["cleanser"]
    imp_cfg = f["imp_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and {guardian.title} at {setting.place}. It is also about {imp_cfg.dark_label}, which seemed scary at first."
        ),
        (
            "What problem did the child find at the spring?",
            f"{child.id} found that the guardian's {guardian.body_part} was abscessed and the sacred water had turned gray. The dirty spring showed that the guardian's pain was spilling into the valley."
        ),
        (
            "Why did the child bring detergent?",
            f"{child.id} brought {cleanser.phrase} to wash the sore place gently. The helper knew a careful cleaning could help the wound without harming the guardian."
        ),
        (
            "What was the twist about the imp?",
            f"The imp was not an outside enemy at all. It had been born from the guardian's pain, so healing the wound was the real way to calm it."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "How did the imp change?",
                f"After the wound was washed, the dark little creature transformed into {imp_cfg.bright_label}. The change showed that underneath the soot it was never a monster, only pain waiting to be eased."
            )
        )
    if f.get("spring_clear"):
        qa.append(
            (
                "How did the story end?",
                f"The spring ran clear again, the guardian was healed, and the valley received fresh water. The happy ending proves that kindness and wise care changed the whole place."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detergent", "imp", "abscessed", "healing", "twist", "transformation"}
    cleanser = world.facts["cleanser"]
    if cleanser.id == "soaproot":
        tags.add("soaproot")
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
        if ent.material:
            bits.append(f"material={ent.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="laurel_spring",
        guardian="lion",
        cleanser="soaproot",
        helper="priestess",
        imp_form="soot",
        child_name="Nera",
        child_gender="girl",
        helper_type="priestess",
    ),
    StoryParams(
        setting="cedar_steps",
        guardian="crane",
        cleanser="dew",
        helper="hermit",
        imp_form="cinder",
        child_name="Iven",
        child_gender="boy",
        helper_type="priest",
    ),
    StoryParams(
        setting="sun_gate",
        guardian="stag",
        cleanser="olive",
        helper="priestess",
        imp_form="ember",
        child_name="Mira",
        child_gender="girl",
        helper_type="priestess",
    ),
]


ASP_RULES = r"""
gentle(C) :- cleanser(C), strength(C,S), gentle_min(M), S >= M.
fits(C,G) :- cleanser(C), guardian(G), safe_for(C,M), guardian_material(G,M), gentle(C).
valid(S,G,C,H,I) :- setting(S), guardian(G), cleanser(C), helper(H), imp_form(I), fits(C,G).

% Deterministic outcome model for this world.
wound_leaks :- chosen_guardian(G), guardian(G).
wound_healed :- chosen_guardian(G), chosen_cleanser(C), fits(C,G).
imp_transformed :- wound_healed.
spring_clear :- wound_healed.
happy_ending :- imp_transformed, spring_clear.

#show valid/5.
#show fits/2.
#show happy_ending/0.
#show imp_transformed/0.
#show spring_clear/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for guardian_id, guardian in GUARDIANS.items():
        lines.append(asp.fact("guardian", guardian_id))
        lines.append(asp.fact("guardian_material", guardian_id, guardian.material))
    for cleanser_id, cleanser in CLEANSERS.items():
        lines.append(asp.fact("cleanser", cleanser_id))
        lines.append(asp.fact("strength", cleanser_id, cleanser.strength))
        for material in sorted(cleanser.safe_materials):
            lines.append(asp.fact("safe_for", cleanser_id, material))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for imp_id in IMP_FORMS:
        lines.append(asp.fact("imp_form", imp_id))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_happy(params: StoryParams) -> tuple[bool, bool, bool]:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_guardian", params.guardian),
            asp.fact("chosen_cleanser", params.cleanser),
        ]
    )
    model = asp.one_model(asp_program(extra))
    happy = bool(asp.atoms(model, "happy_ending"))
    transformed = bool(asp.atoms(model, "imp_transformed"))
    spring_clear = bool(asp.atoms(model, "spring_clear"))
    return happy, transformed, spring_clear


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a sacred guardian, a painful imp, and a healing transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--cleanser", choices=CLEANSERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--imp-form", dest="imp_form", choices=IMP_FORMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cleanser and args.guardian:
        cleanser = CLEANSERS[args.cleanser]
        guardian = GUARDIANS[args.guardian]
        if not cleanser_fits(cleanser, guardian):
            raise StoryError(explain_rejection(cleanser, guardian))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.guardian is None or combo[1] == args.guardian)
        and (args.cleanser is None or combo[2] == args.cleanser)
        and (args.helper is None or combo[3] == args.helper)
        and (args.imp_form is None or combo[4] == args.imp_form)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, guardian_id, cleanser_id, helper_id, imp_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["priestess", "priest"])
    return StoryParams(
        setting=setting_id,
        guardian=guardian_id,
        cleanser=cleanser_id,
        helper=helper_id,
        imp_form=imp_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.guardian not in GUARDIANS:
        raise StoryError(f"(Unknown guardian '{params.guardian}'.)")
    if params.cleanser not in CLEANSERS:
        raise StoryError(f"(Unknown cleanser '{params.cleanser}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.imp_form not in IMP_FORMS:
        raise StoryError(f"(Unknown imp form '{params.imp_form}'.)")

    guardian = GUARDIANS[params.guardian]
    cleanser = CLEANSERS[params.cleanser]
    if not cleanser_fits(cleanser, guardian):
        raise StoryError(explain_rejection(cleanser, guardian))

    world = tell(
        setting=SETTINGS[params.setting],
        guardian_cfg=guardian,
        cleanser=cleanser,
        helper_cfg=HELPERS[params.helper],
        imp_cfg=IMP_FORMS[params.imp_form],
        child_name=params.child_name,
        child_gender=params.child_gender,
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

    for params in CURATED:
        happy, transformed, spring_clear = asp_happy(params)
        try:
            sample = generate(params)
        except Exception as err:  # pragma: no cover
            print(f"Smoke test failed during generate(): {err}")
            return 1
        if not sample.story.strip():
            print("Smoke test failed: empty story.")
            return 1
        world = sample.world
        if world is None:
            print("Smoke test failed: missing world.")
            return 1
        py_happy = bool(world.facts.get("healed") and world.facts.get("transformed") and world.facts.get("spring_clear"))
        if (happy, transformed, spring_clear) != (py_happy, bool(world.facts.get("transformed")), bool(world.facts.get("spring_clear"))):
            rc = 1
            print(
                "MISMATCH in outcome for",
                params,
                "asp=",
                (happy, transformed, spring_clear),
                "python=",
                (py_happy, bool(world.facts.get("transformed")), bool(world.facts.get("spring_clear"))),
            )

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("\nOK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover
        print(f"Smoke emit failed: {err}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, guardian, cleanser, helper, imp_form) combos:\n")
        for setting_id, guardian_id, cleanser_id, helper_id, imp_id in combos:
            print(f"  {setting_id:13} {guardian_id:8} {cleanser_id:8} {helper_id:10} {imp_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.guardian} with {p.cleanser} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
