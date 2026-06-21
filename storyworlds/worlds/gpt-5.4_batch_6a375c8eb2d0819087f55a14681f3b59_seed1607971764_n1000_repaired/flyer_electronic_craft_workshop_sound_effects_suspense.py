#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py
====================================================================================

A standalone story world for a tiny fairy-tale-like craft-workshop domain:
a child makes a flyer with an electronic sound piece, a strange noise brings
suspense, and a careful grown-up helps solve the real problem.

This world models a simple common-sense constraint:

- each flyer has moving parts (wings or tail),
- each decoration trouble belongs to one physical zone,
- only some fixes honestly solve that trouble,
- and some flyers do not even have that moving zone.

So the generator refuses weak stories where the chosen trouble could not happen
or the chosen fix would not truly help.

Run it
------
    python storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py
    python storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py --flyer moon_moth --trouble ribbon_wing
    python storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py --trouble foil_switch --fix trim_ribbon
    python storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py --all
    python storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/flyer_electronic_craft_workshop_sound_effects_suspense.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Flyer:
    id: str
    label: str
    phrase: str
    moving_zone: str
    launch_line: str
    sky_line: str
    fragility: int
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
class ElectronicPiece:
    id: str
    label: str
    phrase: str
    sound: str
    switch_text: str
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
class Trouble:
    id: str
    label: str
    phrase: str
    zone: str
    noise: str
    danger_line: str
    snag_line: str
    severity: int
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
class Fix:
    id: str
    label: str
    sense: int
    zone: str
    power: int
    action: str
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

    def copy(self) -> "World":
        clone = World()
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


def _r_noise(world: World) -> list[str]:
    flyer = world.get("flyer")
    module = world.get("module")
    trouble = world.get("trouble")
    if module.meters["on"] < THRESHOLD or trouble.meters["active"] < THRESHOLD:
        return []
    sig = ("noise", flyer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flyer.meters["stuck"] += 1
    flyer.meters["wobble"] += 1
    flyer.memes["alarm"] += 1
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["fear"] += 1
    helper.memes["concern"] += 1
    return ["__noise__"]


def _r_wear(world: World) -> list[str]:
    flyer = world.get("flyer")
    if flyer.meters["stuck"] < THRESHOLD:
        return []
    sig = ("wear", flyer.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flyer.meters["strain"] += 1
    if world.facts.get("delay", 0) >= 1:
        flyer.meters["strain"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="wear", tag="physical", apply=_r_wear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def trouble_possible(flyer: Flyer, trouble: Trouble) -> bool:
    return flyer.moving_zone == trouble.zone


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_matches(trouble: Trouble, fix: Fix) -> bool:
    return trouble.zone == fix.zone and fix.sense >= SENSE_MIN


def strain_level(flyer: Flyer, trouble: Trouble, delay: int) -> int:
    return flyer.fragility + trouble.severity + delay


def fully_repaired(flyer: Flyer, trouble: Trouble, fix: Fix, delay: int) -> bool:
    return fix_matches(trouble, fix) and fix.power >= strain_level(flyer, trouble, delay)


def predict_noise(world: World) -> dict:
    sim = world.copy()
    sim.get("module").meters["on"] += 1
    sim.get("trouble").meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("flyer").meters["stuck"] >= THRESHOLD,
        "strain": sim.get("flyer").meters["strain"],
    }


def introduce(world: World, hero: Entity, helper: Entity, flyer: Flyer) -> None:
    world.say(
        f"In the craft workshop, where jars of beads shone like treasure and paper scraps slept in rainbow piles, "
        f"{hero.id} was making {flyer.phrase}. {helper.id}, the workshop teacher, moved nearby as softly as a moonlit owl."
    )
    world.say(
        f"{hero.id} wanted the flyer to feel almost enchanted, the sort of little creation that might seem ready to lift itself "
        f"toward the rafters if someone believed hard enough."
    )


def choose_magic(world: World, hero: Entity, module: ElectronicPiece) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On the table lay {module.phrase}. \"If I tuck in this electronic piece,\" {hero.id} whispered, "
        f"\"my flyer might sing when it flies.\""
    )


def decorate(world: World, hero: Entity, trouble: Trouble) -> None:
    world.say(
        f"So {hero.id} added {trouble.phrase}, because it looked lovely in the lamplight and seemed just right for a fairy-tale craft."
    )


def warning(world: World, helper: Entity, hero: Entity, trouble: Trouble) -> None:
    pred = predict_noise(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_strain"] = pred["strain"]
    helper.memes["care"] += 1
    world.say(
        f"But {helper.id} tilted {helper.pronoun('possessive')} head. \"Before we switch it on,\" {helper.pronoun()} said, "
        f"\"let us look closely. {trouble.danger_line}\""
    )


def switch_on(world: World, hero: Entity, module: ElectronicPiece, trouble: Trouble) -> None:
    module_ent = world.get("module")
    trouble_ent = world.get("trouble")
    module_ent.meters["on"] += 1
    trouble_ent.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} touched the tiny switch. {module.switch_text} "
        f"At first came a bright little sound — {module.sound}! — and then, all at once, {trouble.noise}"
    )
    world.say(
        f"{trouble.snag_line} The whole craft workshop seemed to hold its breath."
    )


def suspense(world: World, hero: Entity, helper: Entity, flyer: Flyer) -> None:
    world.say(
        f"{hero.id} froze with wide eyes. The {flyer.label} trembled in {hero.pronoun('possessive')} hands, and even the scissors and glue sticks "
        f"on the table felt suddenly still."
    )
    world.say(
        f"Then {helper.id} stepped closer, calm as candlelight. \"Do not tug,\" {helper.pronoun()} murmured. "
        f"\"A patient look is stronger than a panicked pull.\""
    )


def mend(world: World, helper: Entity, fix: Fix, flyer: Flyer) -> None:
    world.get("flyer").meters["stuck"] = 0.0
    world.get("flyer").meters["wobble"] = 0.0
    world.get("trouble").meters["active"] = 0.0
    world.get("module").meters["on"] = 0.0
    hero = world.get("hero")
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} clicked the little switch off, {fix.action}, and tested the moving part with one careful finger. "
        f"Nothing caught. Nothing scraped. The frightened moment began to loosen."
    )
    world.say(
        f"When the electronic piece was switched on again, the sound came out clean and small, and the {flyer.label} moved as it should."
    )


def patch_and_keep(world: World, helper: Entity, fix: Fix, flyer: Flyer) -> None:
    world.get("flyer").meters["torn"] += 1
    world.get("flyer").meters["stuck"] = 0.0
    world.get("trouble").meters["active"] = 0.0
    world.get("module").meters["on"] = 0.0
    hero = world.get("hero")
    hero.memes["fear"] = 0.0
    hero.memes["sadness"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{helper.id} clicked the switch off and {fix.action}, but the strain had already nipped a tear into the delicate paper. "
        f"The trouble stopped, yet a small rip showed where the suspense had bitten hardest."
    )
    world.say(
        f"Still, {helper.id} fetched a golden patch from the repair box and smoothed it over the tear. "
        f"\"Even fairy-tale things may be mended,\" {helper.pronoun()} said."
    )


def ending_bright(world: World, hero: Entity, helper: Entity, flyer: Flyer, module: ElectronicPiece) -> None:
    world.say(
        f"Soon {hero.id} lifted the finished flyer and gave it a gentle send. {flyer.launch_line} "
        f"The workshop answered with a happy {module.sound}, soft and true."
    )
    world.say(
        f"{flyer.sky_line} And from then on, whenever {hero.id} added something glittering to a craft, "
        f"{hero.pronoun()} looked twice to be sure beauty and motion could be friends."
    )


def ending_mended(world: World, hero: Entity, flyer: Flyer) -> None:
    world.say(
        f"When {hero.id} launched the flyer at last, it did not dance quite as boldly as before, but it still rose in a brave little curve beneath the workshop lamps."
    )
    world.say(
        f"The golden patch gleamed like a tiny badge of wisdom. {hero.id} smiled at it, remembering that quick hands can cause trouble, "
        f"but careful hands can carry a story home."
    )


def tell(
    flyer: Flyer,
    module: ElectronicPiece,
    trouble: Trouble,
    fix: Fix,
    *,
    hero_name: str = "Lina",
    hero_type: str = "girl",
    helper_name: str = "Marrow",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type="teacher", label=helper_name, role="helper"))
    flyer_ent = world.add(Entity(id="flyer", type="flyer", label=flyer.label, phrase=flyer.phrase))
    module_ent = world.add(Entity(id="module", type="module", label=module.label, phrase=module.phrase))
    trouble_ent = world.add(Entity(id="trouble", type="trouble", label=trouble.label, phrase=trouble.phrase))

    hero.attrs["name"] = hero_name
    helper.attrs["name"] = helper_name
    flyer_ent.attrs["zone"] = flyer.moving_zone
    trouble_ent.attrs["zone"] = trouble.zone
    module_ent.meters["on"] = 0.0
    trouble_ent.meters["active"] = 0.0
    flyer_ent.meters["stuck"] = 0.0
    flyer_ent.meters["strain"] = 0.0
    flyer_ent.meters["torn"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["joy"] = 0.0
    helper.memes["care"] = 0.0
    world.facts["delay"] = delay

    introduce(world, hero, helper, flyer)
    choose_magic(world, hero, module)
    decorate(world, hero, trouble)

    world.para()
    warning(world, helper, hero, trouble)
    switch_on(world, hero, module, trouble)
    suspense(world, hero, helper, flyer)

    level = strain_level(flyer, trouble, delay)
    outcome = "smooth" if fully_repaired(flyer, trouble, fix, delay) else "patched"
    flyer_ent.meters["strain"] = float(level)

    world.para()
    if outcome == "smooth":
        mend(world, helper, fix, flyer)
        ending_bright(world, hero, helper, flyer, module)
    else:
        patch_and_keep(world, helper, fix, flyer)
        ending_mended(world, hero, flyer)

    world.facts.update(
        hero=hero,
        helper=helper,
        flyer_cfg=flyer,
        module_cfg=module,
        trouble_cfg=trouble,
        fix_cfg=fix,
        outcome=outcome,
        strain=level,
        scary_noise=True,
        flyer_name=flyer.label,
        electronic_name=module.label,
    )
    return world


FLYERS = {
    "firebird": Flyer(
        id="firebird",
        label="firebird flyer",
        phrase="a scarlet firebird flyer with bright paper wings",
        moving_zone="wings",
        launch_line="It swooped over the workbench like a bright leaf learning a secret dance.",
        sky_line="The little firebird looked almost alive, not because of wild magic, but because careful making had given it room to move.",
        fragility=1,
        tags={"flyer", "wings"},
    ),
    "moon_moth": Flyer(
        id="moon_moth",
        label="moon-moth flyer",
        phrase="a silver moon-moth flyer with long shimmering wings",
        moving_zone="wings",
        launch_line="It floated past the spools of thread as gently as if moonbeams had learned to flutter.",
        sky_line="The moon-moth flyer glided in a pale loop above the workshop table, graceful now that nothing snagged its wings.",
        fragility=2,
        tags={"flyer", "wings"},
    ),
    "comet_kite": Flyer(
        id="comet_kite",
        label="comet-tail flyer",
        phrase="a blue comet-tail flyer with a streaming paper tail",
        moving_zone="tail",
        launch_line="It skimmed through the warm workshop air, its tail whispering behind like a tiny comet.",
        sky_line="The comet-tail flyer flashed once under the lamps and then sailed straight, with its tail free and light.",
        fragility=1,
        tags={"flyer", "tail"},
    ),
}

MODULES = {
    "chirper": ElectronicPiece(
        id="chirper",
        label="chirper",
        phrase="a tiny electronic chirper with a button switch",
        sound="peep-peep",
        switch_text="Click!",
        tags={"electronic", "sound"},
    ),
    "whistler": ElectronicPiece(
        id="whistler",
        label="whistler",
        phrase="a slim electronic whistle box with a silver switch",
        sound="wheee",
        switch_text="Tick!",
        tags={"electronic", "sound"},
    ),
    "hummer": ElectronicPiece(
        id="hummer",
        label="hummer",
        phrase="a little electronic hummer tucked inside a paper pocket",
        sound="bmmm",
        switch_text="Tap!",
        tags={"electronic", "sound"},
    ),
}

TROUBLES = {
    "ribbon_wing": Trouble(
        id="ribbon_wing",
        label="ribbon on the wing hinge",
        phrase="a velvet ribbon too close to the wing hinge",
        zone="wings",
        noise='came a scratchy "bzzzt-clack! bzzzt-clack!"',
        danger_line="That ribbon may brush the wing hinge when the moving part starts.",
        snag_line="The ribbon twitched, caught, and made one wing jerk instead of flutter",
        severity=1,
        tags={"ribbon", "suspense"},
    ),
    "sequin_wing": Trouble(
        id="sequin_wing",
        label="sequin chain on the wing edge",
        phrase="a line of sequins dangling along the wing edge",
        zone="wings",
        noise='the workshop filled with a tinny "zzip-zzt! zzip-zzt!"',
        danger_line="Those sequins are lovely, but they may scrape the moving wing edge.",
        snag_line="The sequins shivered and dragged, making the wings quiver unevenly",
        severity=2,
        tags={"sequins", "suspense"},
    ),
    "bead_tail": Trouble(
        id="bead_tail",
        label="bead knot in the tail path",
        phrase="a bead knot tied in the middle of the tail path",
        zone="tail",
        noise='there burst a nervous "rrrk-tik! rrrk-tik!"',
        danger_line="That bead knot may bump where the tail is meant to swing free.",
        snag_line="The bead knot knocked against the tail path and made the tail twitch crookedly",
        severity=1,
        tags={"beads", "suspense"},
    ),
}

FIXES = {
    "trim_ribbon": Fix(
        id="trim_ribbon",
        label="trim the ribbon",
        sense=3,
        zone="wings",
        power=3,
        action="trimmed the ribbon back from the moving part",
        qa_text="trimmed the ribbon so the wing could move freely again",
        tags={"repair", "ribbon"},
    ),
    "move_sequins": Fix(
        id="move_sequins",
        label="move the sequins",
        sense=3,
        zone="wings",
        power=4,
        action="peeled the sequins loose and set them farther from the moving edge",
        qa_text="moved the sequins away from the moving wing edge",
        tags={"repair", "sequins"},
    ),
    "untie_bead": Fix(
        id="untie_bead",
        label="untie the bead knot",
        sense=3,
        zone="tail",
        power=3,
        action="untied the bead knot and slid the tail smooth again",
        qa_text="untied the bead knot so the tail could swing freely",
        tags={"repair", "beads"},
    ),
    "press_harder": Fix(
        id="press_harder",
        label="press the switch harder",
        sense=1,
        zone="switch",
        power=1,
        action="pressed the switch harder and hoped it would sort itself out",
        qa_text="pressed the switch harder",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Wren", "Nora", "Elsie", "Pia", "Della"]
BOY_NAMES = ["Oren", "Finn", "Milo", "Tobin", "Rowan", "Jules", "Nico", "Bram"]
HELPER_NAMES = ["Marrow", "Aster", "Bramble", "Willow"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for flyer_id, flyer in FLYERS.items():
        for trouble_id, trouble in TROUBLES.items():
            if not trouble_possible(flyer, trouble):
                continue
            for fix_id, fix in FIXES.items():
                if fix_matches(trouble, fix):
                    combos.append((flyer_id, trouble_id, fix_id))
    return combos


@dataclass
class StoryParams:
    flyer: str
    module: str
    trouble: str
    fix: str
    hero_name: str
    hero_type: str
    helper_name: str
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


KNOWLEDGE = {
    "flyer": [(
        "What is a flyer in this story?",
        "A flyer is a light craft made to glide or flutter through the air. It needs room to move so its wings or tail do not catch."
    )],
    "electronic": [(
        "What does electronic mean?",
        "Electronic means a tiny device uses electricity from a small battery or circuit to do something. In this story, the electronic piece makes a sound when it is switched on."
    )],
    "sound": [(
        "Why can a small craft make sound?",
        "A craft can make sound if it has a little speaker, buzzer, or sound chip inside. When the battery powers it, the part can chirp, hum, or whistle."
    )],
    "repair": [(
        "Why do crafters fix a moving part instead of forcing it?",
        "Forcing a stuck part can bend or tear the craft. A careful fix removes what is catching so the piece can move the way it was meant to."
    )],
    "ribbon": [(
        "Why can a ribbon cause trouble on a moving wing?",
        "A ribbon is soft, but it can still get in the way if it lies across a hinge or moving edge. Then the wing may snag instead of fluttering."
    )],
    "sequins": [(
        "Why can sequins make a scratchy sound?",
        "Sequins are shiny little pieces, and if they scrape against a moving part they can rattle or scratch. That noise can warn you that something is catching."
    )],
    "beads": [(
        "Why can a bead knot trouble a tail?",
        "A bead knot is thicker and heavier than plain paper or string. If it sits in the path of a moving tail, it can bump and block the motion."
    )],
}
KNOWLEDGE_ORDER = ["flyer", "electronic", "sound", "ribbon", "sequins", "beads", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    flyer = f["flyer_cfg"]
    trouble = f["trouble_cfg"]
    module = f["module_cfg"]
    outcome = f["outcome"]
    if outcome == "smooth":
        return [
            f'Write a fairy-tale style story set in a craft workshop about a child making a flyer with an electronic sound piece. Include suspense from a strange noise and end with a careful repair.',
            f'Tell a gentle workshop story where a {flyer.label} makes {module.sound} at first, then a snag causes a scary sound because of {trouble.label}, and a calm teacher solves it.',
            'Write a child-facing story that includes the words "flyer" and "electronic", uses sound effects, and shows that careful crafting is better than panicking.',
        ]
    return [
        f'Write a fairy-tale style story set in a craft workshop where a child makes a flyer with an electronic sound piece, hears a worrying noise, and learns to mend a small tear after a snag.',
        f'Tell a suspenseful but gentle craft-workshop story where {trouble.label} troubles a {flyer.label}, and the ending image shows a repaired craft still flying.',
        'Write a story for young children using the words "flyer" and "electronic", with sound effects and a soft lesson about patient hands.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    flyer = f["flyer_cfg"]
    module = f["module_cfg"]
    trouble = f["trouble_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child in a craft workshop, and {helper.label}, the workshop teacher. Together they make a {flyer.label} with an electronic sound piece."
        ),
        (
            "What was special about the flyer?",
            f"It was not only pretty; it also had {module.phrase} inside. That electronic part was meant to make a small sound when the flyer moved."
        ),
        (
            "Why did the workshop feel suspenseful?",
            f"When the switch was touched, the flyer made a strange, scratchy noise instead of only its nice little sound. The odd noise meant something was catching, so everyone had to stop and look carefully."
        ),
        (
            f"What caused the trouble in the {flyer.label}?",
            f"The trouble came from {trouble.phrase}. It sat too close to the moving {trouble.zone}, so when the electronic piece started, that part snagged and made the scary noise."
        ),
    ]
    if outcome == "smooth":
        qa.append((
            "How did they fix the problem?",
            f"{helper.label} first turned the switch off and then {fix.qa_text}. That careful fix removed what was catching, so the flyer could move properly again."
        ))
        qa.append((
            "How did the story end?",
            f"The flyer flew cleanly through the craft workshop and answered with a happy little {module.sound}. The ending shows that beauty and motion worked together once the craft was made safe."
        ))
    else:
        qa.append((
            "Did the flyer stay perfect?",
            f"No. The trouble stopped, but the strain had already made a small tear in the paper. Even so, {helper.label} patched it, and the flyer still rose when {hero.label} launched it."
        ))
        qa.append((
            "What did the child learn?",
            f"{hero.label} learned not to yank at a frightened-making problem. Looking closely and fixing the real snag was what saved the flyer from worse damage."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"flyer", "electronic", "sound", "repair"}
    tags |= set(world.facts["trouble_cfg"].tags)
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        flyer="firebird",
        module="chirper",
        trouble="ribbon_wing",
        fix="trim_ribbon",
        hero_name="Lina",
        hero_type="girl",
        helper_name="Aster",
        delay=0,
    ),
    StoryParams(
        flyer="moon_moth",
        module="whistler",
        trouble="sequin_wing",
        fix="move_sequins",
        hero_name="Milo",
        hero_type="boy",
        helper_name="Willow",
        delay=0,
    ),
    StoryParams(
        flyer="comet_kite",
        module="hummer",
        trouble="bead_tail",
        fix="untie_bead",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Marrow",
        delay=1,
    ),
    StoryParams(
        flyer="moon_moth",
        module="chirper",
        trouble="sequin_wing",
        fix="trim_ribbon",
        hero_name="Finn",
        hero_type="boy",
        helper_name="Bramble",
        delay=2,
    ),
]


def explain_rejection(flyer: Flyer, trouble: Trouble, fix: Optional[Fix] = None) -> str:
    if not trouble_possible(flyer, trouble):
        return (
            f"(No story: {flyer.label} moves at the {flyer.moving_zone}, but {trouble.label} belongs to the {trouble.zone}. "
            f"That trouble would not honestly affect this flyer.)"
        )
    if fix is not None and not fix_matches(trouble, fix):
        return (
            f"(No story: '{fix.id}' is not a sensible fix for {trouble.label}. "
            f"Choose a fix that really clears the {trouble.zone} trouble.)"
        )
    return "(No story: this combination does not describe a real workshop problem and fix.)"


def outcome_of(params: StoryParams) -> str:
    flyer = FLYERS[params.flyer]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    return "smooth" if fully_repaired(flyer, trouble, fix, params.delay) else "patched"


ASP_RULES = r"""
possible(F, T) :- flyer(F), trouble(T), moving_zone(F, Z), trouble_zone(T, Z).
sensible_fix(X) :- fix(X), sense(X, S), sense_min(M), S >= M.
compatible(T, X) :- trouble(T), fix(X), trouble_zone(T, Z), fix_zone(X, Z), sensible_fix(X).

valid(F, T, X) :- possible(F, T), compatible(T, X).

strain(V) :- chosen_flyer(F), chosen_trouble(T), fragility(F, A), severity(T, B), delay(D), V = A + B + D.
smooth :- chosen_flyer(F), chosen_trouble(T), chosen_fix(X), valid(F, T, X), power(X, P), strain(V), P >= V.
outcome(smooth) :- smooth.
outcome(patched) :- not smooth.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid, flyer in FLYERS.items():
        lines.append(asp.fact("flyer", fid))
        lines.append(asp.fact("moving_zone", fid, flyer.moving_zone))
        lines.append(asp.fact("fragility", fid, flyer.fragility))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_zone", tid, trouble.zone))
        lines.append(asp.fact("severity", tid, trouble.severity))
    for xid, fix in FIXES.items():
        lines.append(asp.fact("fix", xid))
        lines.append(asp.fact("fix_zone", xid, fix.zone))
        lines.append(asp.fact("sense", xid, fix.sense))
        lines.append(asp.fact("power", xid, fix.power))
    for mid in MODULES:
        lines.append(asp.fact("module", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_flyer", params.flyer),
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fairy-tale craft workshop, a flyer, an electronic sound, and a careful repair."
    )
    ap.add_argument("--flyer", choices=FLYERS)
    ap.add_argument("--module", choices=MODULES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the snag strains the flyer before the fix")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.flyer and args.trouble:
        flyer = FLYERS[args.flyer]
        trouble = TROUBLES[args.trouble]
        if not trouble_possible(flyer, trouble):
            raise StoryError(explain_rejection(flyer, trouble))
    if args.trouble and args.fix:
        trouble = TROUBLES[args.trouble]
        fix = FIXES[args.fix]
        if not fix_matches(trouble, fix):
            flyer = FLYERS[args.flyer] if args.flyer else next(iter(FLYERS.values()))
            raise StoryError(explain_rejection(flyer, trouble, fix))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        trouble = TROUBLES[args.trouble] if args.trouble else next(iter(TROUBLES.values()))
        flyer = FLYERS[args.flyer] if args.flyer else next(iter(FLYERS.values()))
        raise StoryError(explain_rejection(flyer, trouble, FIXES[args.fix]))

    combos = [
        c for c in valid_combos()
        if (args.flyer is None or c[0] == args.flyer)
        and (args.trouble is None or c[1] == args.trouble)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    flyer_id, trouble_id, fix_id = rng.choice(sorted(combos))
    module_id = args.module or rng.choice(sorted(MODULES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        flyer=flyer_id,
        module=module_id,
        trouble=trouble_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.flyer not in FLYERS:
        raise StoryError(f"(Unknown flyer: {params.flyer})")
    if params.module not in MODULES:
        raise StoryError(f"(Unknown module: {params.module})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    flyer = FLYERS[params.flyer]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    if not trouble_possible(flyer, trouble):
        raise StoryError(explain_rejection(flyer, trouble))
    if not fix_matches(trouble, fix):
        raise StoryError(explain_rejection(flyer, trouble, fix))

    world = tell(
        flyer=flyer,
        module=MODULES[params.module],
        trouble=trouble,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
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
    parser = build_parser()
    for s in range(80):
        try:
            ns = parser.parse_args([])
            p = resolve_params(ns, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (flyer, trouble, fix) combos:\n")
        for flyer, trouble, fix in combos:
            print(f"  {flyer:11} {trouble:12} {fix}")
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
            header = f"### {p.hero_name}: {p.flyer} with {p.trouble} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
