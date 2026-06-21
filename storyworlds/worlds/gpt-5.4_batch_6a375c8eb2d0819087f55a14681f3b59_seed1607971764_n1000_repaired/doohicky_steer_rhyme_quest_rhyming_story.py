#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py
=====================================================================

A standalone story world for a small rhyming quest tale: a child and a helper
launch a tiny boat on a make-believe mission, a steering doohicky comes loose,
and the right repair lets them steer safely past the obstacle.

The prose is written in a gentle rhyming-story style, but the story is still
driven by simulated state:
- typed entities with physical meters and emotional memes
- a small forward-chaining rule engine
- a reasonableness gate for which repairs actually fit which fault
- an inline ASP twin checked by --verify

Run it
------
    python storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py --json
    python storyworlds/worlds/gpt-5.4/doohicky_steer_rhyme_quest_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
BASE_CONTROL = 2
SENSE_MIN = 2


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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
    scene: str
    water: str
    obstacle: str
    destination: str
    cargo_spot: str
    difficulty: int
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
class Cargo:
    id: str
    label: str
    phrase: str
    goal_line: str
    ending_image: str
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
class Fault:
    id: str
    label: str
    doohicky: str
    problem_line: str
    loss: int
    repair_tags: set[str] = field(default_factory=set)
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
    tag: str
    sense: int
    power: int
    action_line: str
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


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    power: int
    action_line: str
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


def _r_drift(world: World) -> list[str]:
    boat = world.get("boat")
    if boat.meters["control"] >= world.facts["difficulty"]:
        return []
    sig = ("drift",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["drifting"] += 1
    boat.meters["wobble"] += 1
    for eid in ("hero", "helper"):
        world.get(eid).memes["worry"] += 1
    return ["__drift__"]


def _r_splash(world: World) -> list[str]:
    boat = world.get("boat")
    cargo = world.get("cargo")
    if boat.meters["drifting"] < THRESHOLD:
        return []
    sig = ("splash",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["damp"] += 1
    cargo.meters["late"] += 1
    return ["__splash__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="splash", tag="physical", apply=_r_splash),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(s for s in made if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def effective_control(setting: Setting, fault: Fault, fix: Fix, guide: Guide) -> int:
    return BASE_CONTROL - fault.loss + fix.power + guide.power


def is_compatible(fault: Fault, fix: Fix) -> bool:
    return fix.tag in fault.repair_tags


def sensible_fixes() -> list[Fix]:
    return [fx for fx in FIXES.values() if fx.sense >= SENSE_MIN]


def succeeds(setting: Setting, fault: Fault, fix: Fix, guide: Guide) -> bool:
    return effective_control(setting, fault, fix, guide) >= setting.difficulty


def explain_fix_rejection(fix_id: str) -> str:
    fx = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fx.sense} < {SENSE_MIN}). Try a steadier repair such as {better}.)"
    )


def explain_combo_rejection(fault: Fault, fix: Fix) -> str:
    needed = ", ".join(sorted(fault.repair_tags))
    return (
        f"(No story: {fix.label} does not fit {fault.label}. "
        f"That steering doohicky needs a repair with one of these methods: {needed}.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for fault_id, fault in FAULTS.items():
            for fix_id, fix in FIXES.items():
                if fix.sense < SENSE_MIN or not is_compatible(fault, fix):
                    continue
                for guide_id in GUIDES:
                    combos.append((setting_id, fault_id, fix_id, guide_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "drifting": sim.get("boat").meters["drifting"] >= THRESHOLD,
        "cargo_damp": sim.get("cargo").meters["damp"] >= THRESHOLD,
    }


def open_quest(world: World, hero: Entity, helper: Entity, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In {world.setting.scene}, with a shimmer and cheer, "
        f"{hero.id} and {helper.id} set a toy boat near {world.setting.water}."
    )
    world.say(
        f"They had a quest with a bright little ring: "
        f"to carry {cargo.phrase} safely to {world.setting.destination} and make the small bank sing."
    )


def launch(world: World, hero: Entity, guide: Guide, cargo: Cargo) -> None:
    world.say(
        f'"We can {guide.id.replace("_", " ")} and steer with care, '
        f'and leave {cargo.label} exactly there," {hero.id} said, all bold and bright.'
    )
    world.say(
        f"The boat slid out through the silver light, with {cargo.label} tucked in {world.setting.cargo_spot}, tidy and slight."
    )


def reveal_fault(world: World, helper: Entity, fault: Fault) -> None:
    boat = world.get("boat")
    boat.meters["control"] = float(BASE_CONTROL - fault.loss)
    pred = predict_trouble(world)
    world.facts["predicted_drifting"] = pred["drifting"]
    world.facts["predicted_damp"] = pred["cargo_damp"]
    helper.memes["notice"] += 1
    world.say(
        f"But then {helper.id} gasped, " + fault.problem_line
    )
    world.say(
        f'"The {fault.doohicky} is loose," {helper.pronoun()} cried. '
        f'"If we do not mend it, we cannot steer past {world.setting.obstacle} with pride."'
    )


def choose_fix(world: World, helper: Entity, fix: Fix, guide: Guide) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} knelt by the bank, quick but calm, and {fix.action_line}."
    )
    world.say(
        f"Then {helper.pronoun()} reached for {guide.phrase}, a gentle aid, "
        f"to keep the little boat from a careless parade."
    )


def relaunch(world: World, hero: Entity, guide: Guide, fix: Fix) -> None:
    boat = world.get("boat")
    boat.meters["repair"] += float(fix.power)
    boat.meters["guidance"] += float(guide.power)
    boat.meters["control"] = float(BASE_CONTROL - world.facts["fault"].loss + fix.power + guide.power)
    boat.meters["drifting"] = 0.0
    world.say(
        f'"Now hold it steady, low and clear. '
        f'With {fix.label} and {guide.label}, we truly can steer," said {hero.id}.'
    )


def drift_scene(world: World, hero: Entity, helper: Entity, cargo: Cargo) -> None:
    propagate(world, narrate=False)
    boat = world.get("boat")
    if boat.meters["drifting"] >= THRESHOLD:
        world.say(
            f"But the bow went wrong with a wobble and sneer, "
            f"and the boat slid sideways toward {world.setting.obstacle} instead of {world.setting.destination} near."
        )
    if world.get("cargo").meters["damp"] >= THRESHOLD:
        world.say(
            f"A splash hopped up with a cold little plop, "
            f"and {cargo.label} grew damp at the top."
        )
    hero.memes["worry"] += 1
    helper.memes["worry"] += 1


def finish_success(world: World, hero: Entity, helper: Entity, cargo: Cargo) -> None:
    boat = world.get("boat")
    boat.meters["arrived"] += 1
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    world.say(
        f"Past {world.setting.obstacle} with a swish and a sweep, "
        f"the boat kept its promise and did not veer deep."
    )
    world.say(
        f"At {world.setting.destination}, soft and clear, "
        f"they set {cargo.goal_line}, and both children gave a cheer."
    )
    world.say(
        f"{cargo.ending_image}, and the once-wild stream felt friendly and dear."
    )


def finish_fail(world: World, hero: Entity, helper: Entity, cargo: Cargo) -> None:
    boat = world.get("boat")
    boat.meters["banked"] += 1
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"The boat did not sink, and no one was in fear, "
        f"but it bumped by the bank and could not get to {world.setting.destination} that year."
    )
    world.say(
        f"{hero.id} lifted out {cargo.label}, damp but found, "
        f"and {helper.id} smoothed it gently above the ground."
    )
    world.say(
        f'"Next time we mend first, then quest," said {helper.id}. '
        f'So they carried the little thing home in their hands, wiser and sound.'
    )


def tell(
    setting: Setting,
    cargo_cfg: Cargo,
    fault: Fault,
    fix: Fix,
    guide: Guide,
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    helper_name: str = "Milo",
    helper_gender: str = "boy",
    elder_type: str = "grandmother",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    boat = world.add(Entity(id="boat", type="boat", label="toy boat"))
    cargo = world.add(Entity(id="cargo", type="cargo", label=cargo_cfg.label))
    boat.meters["control"] = float(BASE_CONTROL)
    cargo.meters["damp"] = 0.0
    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        boat=boat,
        cargo=cargo,
        cargo_cfg=cargo_cfg,
        fault=fault,
        fix=fix,
        guide=guide,
        difficulty=setting.difficulty,
        setting=setting,
    )

    open_quest(world, hero, helper, cargo_cfg)
    launch(world, hero, guide, cargo_cfg)

    world.para()
    reveal_fault(world, helper, fault)
    choose_fix(world, helper, fix, guide)
    relaunch(world, hero, guide, fix)

    world.para()
    success = succeeds(setting, fault, fix, guide)
    if success:
        finish_success(world, hero, helper, cargo_cfg)
    else:
        drift_scene(world, hero, helper, cargo_cfg)
        finish_fail(world, hero, helper, cargo_cfg)

    world.facts["outcome"] = "delivered" if success else "banked"
    world.facts["cargo_damp"] = world.get("cargo").meters["damp"] >= THRESHOLD
    return world


SETTINGS = {
    "brook_bend": Setting(
        id="brook_bend",
        scene="a backyard bright with minty breeze",
        water="the brook that bent past beanpole trees",
        obstacle="the whispering reeds",
        destination="the willow dock",
        cargo_spot="a corky nook",
        difficulty=2,
        tags={"brook", "boat", "quest"},
    ),
    "lily_loop": Setting(
        id="lily_loop",
        scene="a garden path in pearly light",
        water="the lily run that curled left and right",
        obstacle="the stone-ring whirl",
        destination="the frog-stone pier",
        cargo_spot="a ribboned hollow",
        difficulty=3,
        tags={"pond", "boat", "quest"},
    ),
    "rain_rill": Setting(
        id="rain_rill",
        scene="a yard still singing after rain",
        water="the rain rill racing by the lane",
        obstacle="the twig gate",
        destination="the puddle port",
        cargo_spot="a snug tin tray",
        difficulty=1,
        tags={"rain", "boat", "quest"},
    ),
}

CARGOES = {
    "bell": Cargo(
        id="bell",
        label="a silver bell",
        phrase="a silver bell in a nest of felt",
        goal_line="the silver bell on the dock to ring",
        ending_image="The bell gave one brave ting-a-ling",
        tags={"bell", "quest"},
    ),
    "ribbon": Cargo(
        id="ribbon",
        label="a blue ribbon",
        phrase="a blue ribbon folded neat and thin",
        goal_line="the blue ribbon on the pier to flutter",
        ending_image="The ribbon danced with a buttercup flutter",
        tags={"ribbon", "quest"},
    ),
    "crown": Cargo(
        id="crown",
        label="a pebble crown",
        phrase="a pebble crown with a clover rim",
        goal_line="the pebble crown by the port to gleam",
        ending_image="The crown sat proud in a mossy gleam",
        tags={"crown", "quest"},
    ),
}

FAULTS = {
    "peg_loose": Fault(
        id="peg_loose",
        label="a loose steering peg",
        doohicky="steering doohicky peg",
        problem_line='"Oh dear, oh dear, the peg has sprung, and the little side-rudder hangs half-unslung."',
        loss=2,
        repair_tags={"pin", "wrap"},
        tags={"doohicky", "steer"},
    ),
    "rudder_crack": Fault(
        id="rudder_crack",
        label="a cracked rudder tongue",
        doohicky="rudder doohicky tongue",
        problem_line='"Hush and hear, the back fin is slack; the tiny rudder tongue has a crack."',
        loss=1,
        repair_tags={"wrap", "wedge"},
        tags={"doohicky", "steer"},
    ),
    "handle_slip": Fault(
        id="handle_slip",
        label="a slipping tiller handle",
        doohicky="tiller doohicky handle",
        problem_line='"Look just here, the handle has slid; the tiller is wobbling where it once hid."',
        loss=1,
        repair_tags={"pin", "wedge"},
        tags={"doohicky", "steer"},
    ),
}

FIXES = {
    "clothespin": Fix(
        id="clothespin",
        label="a clothespin clip",
        tag="pin",
        sense=3,
        power=2,
        action_line="clipped the loose part snug with a clothespin clip, making the wobble hold fast instead of slip",
        qa_text="used a clothespin clip to hold the loose steering part steady",
        tags={"clothespin", "repair"},
    ),
    "twine_wrap": Fix(
        id="twine_wrap",
        label="a twine wrap",
        tag="wrap",
        sense=3,
        power=1,
        action_line="wound garden twine round and round until the shaky piece stayed tied and sound",
        qa_text="wrapped the steering part with garden twine until it held",
        tags={"twine", "repair"},
    ),
    "cork_wedge": Fix(
        id="cork_wedge",
        label="a cork wedge",
        tag="wedge",
        sense=2,
        power=1,
        action_line="pressed a cork wedge tight in the gap so the steering bit would not clap-clap-clap",
        qa_text="pressed a cork wedge into the gap to steady the steering part",
        tags={"cork", "repair"},
    ),
    "bubble_gum": Fix(
        id="bubble_gum",
        label="a blob of bubble gum",
        tag="gum",
        sense=1,
        power=0,
        action_line="stuck a blob of bubble gum on the part, a gooey idea not made for smart",
        qa_text="tried to stick the part with bubble gum",
        tags={"gum", "repair"},
    ),
}

GUIDES = {
    "twig_oar": Guide(
        id="twig_oar",
        label="twig oar",
        phrase="a slim twig oar",
        power=1,
        action_line="used a slim twig like a tiny oar",
        tags={"oar", "steer"},
    ),
    "spoon_paddle": Guide(
        id="spoon_paddle",
        label="spoon paddle",
        phrase="a little spoon paddle",
        power=2,
        action_line="used a little spoon like a paddle",
        tags={"paddle", "steer"},
    ),
    "leaf_fin": Guide(
        id="leaf_fin",
        label="leaf fin",
        phrase="a broad leaf fin",
        power=1,
        action_line="used a broad leaf like a soft back fin",
        tags={"leaf", "steer"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Ivy", "Rosa", "Pia", "June"]
BOY_NAMES = ["Milo", "Owen", "Finn", "Jude", "Theo", "Arlo", "Eli", "Ben"]
ELDERS = ["grandmother", "grandfather", "mother", "father"]


@dataclass
class StoryParams:
    setting: str
    cargo: str
    fault: str
    fix: str
    guide: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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


KNOWLEDGE = {
    "boat": [
        (
            "How do you steer a small boat?",
            "You steer a small boat by guiding its front or back so it points the way you want to go. If the steering part is loose, the boat can drift instead of turning where you mean."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special trip with a clear goal, like carrying something important to a certain place. It feels exciting because everyone is trying to finish one careful mission."
        )
    ],
    "doohicky": [
        (
            "What is a doohicky?",
            "A doohicky is a playful word for a little part when you do not know its exact name. In the story, it means the small steering piece that helps the boat turn."
        )
    ],
    "repair": [
        (
            "Why do small broken parts need to be repaired before you use something?",
            "A loose part can make a toy or tool stop working the right way. Fixing it first helps the object do its job safely and well."
        )
    ],
    "twine": [
        (
            "What is twine?",
            "Twine is a thin, strong string. People use it to tie things together so they hold in place."
        )
    ],
    "clothespin": [
        (
            "What is a clothespin?",
            "A clothespin is a small clip that can pinch and hold something. It is useful when you need a little piece to stay shut or steady."
        )
    ],
    "cork": [
        (
            "What is a cork wedge?",
            "A cork wedge is a small bit of cork pushed into a gap to hold something firm. It works best when the gap is the right shape for it."
        )
    ],
    "paddle": [
        (
            "What does a paddle do?",
            "A paddle pushes water so a boat can move or turn. Even a little paddle can help a toy boat steer."
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "boat", "doohicky", "repair", "clothespin", "twine", "cork", "paddle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_cfg"]
    setting = f["setting"]
    fault = f["fault"]
    outcome = f["outcome"]
    if outcome == "delivered":
        return [
            f'Write a short rhyming quest story for a 3-to-5-year-old that includes the words "doohicky" and "steer".',
            f"Tell a gentle rhyming story where two children send a toy boat through {setting.obstacle}, a {fault.doohicky} comes loose, and they mend it in time to deliver {cargo.label}.",
            f"Write a child-facing rhyme tale about a tiny mission on water, a wobbling steering part, and a happy ending that proves careful fixing helps."
        ]
    return [
        f'Write a short rhyming quest story for a 3-to-5-year-old that includes the words "doohicky" and "steer".',
        f"Tell a rhyming story where two children try to guide a toy boat to {setting.destination}, but a loose {fault.doohicky} keeps them from steering it there.",
        f"Write a gentle cautionary quest in rhyme where the children are safe, the cargo is saved, and they learn to mend a broken part before they begin."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cargo = f["cargo_cfg"]
    setting = f["setting"]
    fault = f["fault"]
    fix = f["fix"]
    guide = f["guide"]
    outcome = f["outcome"]
    damp = f["cargo_damp"]
    qa: list[tuple[str, str]] = [
        (
            "What was the quest in the story?",
            f"The children were trying to carry {cargo.label} by toy boat to {setting.destination}. It was a quest because they had one clear place to reach and a special thing to deliver there."
        ),
        (
            "What went wrong with the boat?",
            f"The boat's {fault.doohicky} came loose, so the children worried they could not steer properly. Without that steering part, the boat would drift toward {setting.obstacle} instead of the right path."
        ),
        (
            "How did they try to fix the problem?",
            f"They used {fix.label} and {guide.phrase} to steady and guide the boat. The repair mattered because it gave the boat enough control to turn the way they wanted."
        ),
    ]
    if outcome == "delivered":
        qa.append(
            (
                "Why did the quest succeed?",
                f"The quest succeeded because the repair fit the broken part and the children guided the boat carefully. That gave them enough control to steer past {setting.obstacle} and reach {setting.destination}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {cargo.label} delivered at {setting.destination} and the children cheering. The ending image shows the water felt friendly again because the boat was no longer wobbling out of control."
            )
        )
    else:
        answer = (
            f"The quest did not reach {setting.destination} because the boat still drifted toward {setting.obstacle}. "
            f"The children were safe, but the repair was not strong enough to give the boat all the control it needed."
        )
        if damp:
            answer += f" {cargo.label.capitalize()} got a little damp when water splashed up during the drift."
        qa.append(("Why did the quest fail?", answer))
        qa.append(
            (
                "What did the children learn?",
                f"They learned to mend the steering part before starting a quest. That lesson came from seeing how one loose doohicky changed the whole trip."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"quest", "boat", "doohicky", "repair"}
    fix = world.facts["fix"]
    guide = world.facts["guide"]
    if "clothespin" in fix.id:
        tags.add("clothespin")
    if "twine" in fix.id:
        tags.add("twine")
    if "cork" in fix.id:
        tags.add("cork")
    if guide.id in {"twig_oar", "spoon_paddle", "leaf_fin"}:
        tags.add("paddle")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  difficulty={world.facts.get('difficulty')}")
    lines.append(f"  outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="brook_bend",
        cargo="bell",
        fault="peg_loose",
        fix="clothespin",
        guide="spoon_paddle",
        hero_name="Lila",
        hero_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        setting="rain_rill",
        cargo="ribbon",
        fault="rudder_crack",
        fix="twine_wrap",
        guide="twig_oar",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        elder_type="father",
    ),
    StoryParams(
        setting="lily_loop",
        cargo="crown",
        fault="peg_loose",
        fix="twine_wrap",
        guide="leaf_fin",
        hero_name="June",
        hero_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        elder_type="mother",
    ),
    StoryParams(
        setting="lily_loop",
        cargo="bell",
        fault="handle_slip",
        fix="clothespin",
        guide="twig_oar",
        hero_name="Rosa",
        hero_gender="girl",
        helper_name="Arlo",
        helper_gender="boy",
        elder_type="grandfather",
    ),
]


def outcome_of(params: StoryParams) -> str:
    setting = SETTINGS[params.setting]
    fault = FAULTS[params.fault]
    fix = FIXES[params.fix]
    guide = GUIDES[params.guide]
    return "delivered" if succeeds(setting, fault, fix, guide) else "banked"


ASP_RULES = r"""
sensible_fix(Fx) :- fix(Fx), sense(Fx, S), sense_min(M), S >= M.
compatible(Ft, Fx) :- fault(Ft), fix(Fx), repair_need(Ft, Tag), fix_tag(Fx, Tag).
valid(St, Ft, Fx, Gd) :- setting(St), fault(Ft), fix(Fx), guide(Gd),
                         sensible_fix(Fx), compatible(Ft, Fx).

effective_control(V) :- chosen_fault(Ft), chosen_fix(Fx), chosen_guide(Gd),
                        base_control(B), loss(Ft, L), power(Fx, FP), guide_power(Gd, GP),
                        V = B - L + FP + GP.
success :- chosen_setting(St), effective_control(V), difficulty(St, D), V >= D.
outcome(delivered) :- success.
outcome(banked) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("sense_min", SENSE_MIN), asp.fact("base_control", BASE_CONTROL)]
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("difficulty", sid, setting.difficulty))
    for cid in CARGOES:
        lines.append(asp.fact("cargo", cid))
    for fid, fault in FAULTS.items():
        lines.append(asp.fact("fault", fid))
        lines.append(asp.fact("loss", fid, fault.loss))
        for tag in sorted(fault.repair_tags):
            lines.append(asp.fact("repair_need", fid, tag))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
        lines.append(asp.fact("fix_tag", fix_id, fix.tag))
    for gid, guide in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("guide_power", gid, guide.power))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_fault", params.fault),
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_guide", params.guide),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    for seed in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=False, qa=True, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming quest storyworld: a tiny boat, a steering doohicky, and a careful repair."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))
    if args.fault and args.fix:
        if not is_compatible(FAULTS[args.fault], FIXES[args.fix]):
            raise StoryError(explain_combo_rejection(FAULTS[args.fault], FIXES[args.fix]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.fault is None or combo[1] == args.fault)
        and (args.fix is None or combo[2] == args.fix)
        and (args.guide is None or combo[3] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, fault_id, fix_id, guide_id = rng.choice(sorted(combos))
    cargo_id = args.cargo or rng.choice(sorted(CARGOES))
    hero_name, hero_gender = pick_child(rng)
    helper_name, helper_gender = pick_child(rng, avoid=hero_name)
    elder_type = args.elder or rng.choice(ELDERS)
    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        fault=fault_id,
        fix=fix_id,
        guide=guide_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cargo = CARGOES[params.cargo]
        fault = FAULTS[params.fault]
        fix = FIXES[params.fix]
        guide = GUIDES[params.guide]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(params.fix))
    if not is_compatible(fault, fix):
        raise StoryError(explain_combo_rejection(fault, fix))

    world = tell(
        setting=setting,
        cargo_cfg=cargo,
        fault=fault,
        fix=fix,
        guide=guide,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        elder_type=params.elder_type,
    )
    story = world.render().replace("hero", params.hero_name).replace("helper", params.helper_name)
    story = story.replace("said hero", f"said {params.hero_name}")
    story = story.replace("said helper", f"said {params.helper_name}")
    story = story.replace("hero's", f"{params.hero_name}'s").replace("helper's", f"{params.helper_name}'s")
    story = story.replace(" hero ", f" {params.hero_name} ").replace(" helper ", f" {params.helper_name} ")
    story = story.replace("hero.", f"{params.hero_name}.").replace("helper.", f"{params.helper_name}.")
    world_named = copy.deepcopy(world)
    world_named.get("hero").id = params.hero_name
    world_named.get("helper").id = params.helper_name
    world_named.facts["hero"].id = params.hero_name
    world_named.facts["helper"].id = params.helper_name
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world_named,
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
        print(f"{len(combos)} compatible (setting, fault, fix, guide) combos:\n")
        for setting, fault, fix, guide in combos:
            print(f"  {setting:11} {fault:13} {fix:11} {guide}")
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
            header = (
                f"### {p.hero_name} & {p.helper_name}: {p.fault} with {p.fix} "
                f"at {p.setting} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
