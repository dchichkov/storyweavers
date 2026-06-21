#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py
==================================================================

A standalone story world in a gentle mythic mode: a child who carries a secret
mistake, a storm relic full of holy voltage, a flashback that reveals the hidden
cause, and a brave confession that lets a wise keeper choose the safe repair.

The domain is small on purpose. A hilltop or harbor shrine keeps watch over a
village with a storm beacon, a thunder bell, or a cloud mast. The hero feels
guilt because yesterday's careless play damaged the relic. When a storm rises,
the relic hums with dangerous voltage. The child must decide whether to hide the
truth or speak with bravery.

Run it
------
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --place harbor_shrine --relic storm_beacon --fault cracked_glass
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --fix bare_hands
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --all
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --json
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --asp
    python storyworlds/worlds/gpt-5.4/voltage_guilt_flashback_bravery_myth.py --verify
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
        female = {"girl", "woman", "keeper", "priestess"}
        male = {"boy", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "keeper":
            return "keeper"
        return self.type
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
    opening: str
    storm_line: str
    village_line: str
    affords: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    purpose: str
    voltage_line: str
    ending_line: str
    parts: set[str] = field(default_factory=set)
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
    the: str
    part: str
    severity: int
    requires: str
    sign: str
    flashback: str
    risk_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    sense: int
    power: int
    kinds: set[str]
    inspect_text: str
    success_text: str
    fail_text: str
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


def _r_voltage_risk(world: World) -> list[str]:
    relic = world.get("relic")
    hero = world.get("hero")
    fault_ent = world.get("fault")
    if relic.meters["damaged"] < THRESHOLD or world.facts.get("storm_force", 0) < THRESHOLD:
        return []
    sig = ("voltage_risk", world.facts.get("fault_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    added = world.facts.get("storm_force", 0) + fault_ent.meters["severity"]
    relic.meters["danger"] += added
    hero.memes["fear"] += 1
    hero.memes["guilt"] += 1
    return ["__risk__"]


def _r_guilt_to_bravery(world: World) -> list[str]:
    hero = world.get("hero")
    keeper = world.get("keeper")
    if hero.memes["guilt"] < THRESHOLD or world.get("relic").meters["danger"] < THRESHOLD:
        return []
    sig = ("guilt_to_bravery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1 + keeper.memes["kindness"]
    return ["__bravery__"]


def _r_repair_calm(world: World) -> list[str]:
    relic = world.get("relic")
    hero = world.get("hero")
    if relic.meters["repaired"] < THRESHOLD:
        return []
    sig = ("repair_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relic.meters["danger"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["guilt"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="voltage_risk", tag="physical", apply=_r_voltage_risk),
    Rule(name="guilt_to_bravery", tag="emotional", apply=_r_guilt_to_bravery),
    Rule(name="repair_calm", tag="resolution", apply=_r_repair_calm),
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


def compatible_fix(fault: Fault, fix: Fix) -> bool:
    return fault.requires in fix.kinds


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def select_fix(fault: Fault) -> Optional[Fix]:
    options = [f for f in sensible_fixes() if compatible_fix(fault, f)]
    if not options:
        return None
    return sorted(options, key=lambda f: (-f.sense, -f.power, f.id))[0]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for relic_id in sorted(setting.affords):
            relic = RELICS[relic_id]
            for fault_id, fault in FAULTS.items():
                if fault.part in relic.parts and select_fix(fault) is not None:
                    combos.append((place_id, relic_id, fault_id))
    return sorted(combos)


def severity_of(fault: Fault, storm_force: int, delay: int) -> int:
    return fault.severity + storm_force + delay


def is_contained(fix: Fix, fault: Fault, storm_force: int, delay: int) -> bool:
    return fix.power >= severity_of(fault, storm_force, delay)


def predict_danger(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("relic").meters["danger"],
        "bravery": sim.get("hero").memes["bravery"],
    }


def introduce(world: World, hero: Entity, keeper: Entity, relic: Relic) -> None:
    world.say(
        f"In the old days, when clouds were said to keep their own counsel, "
        f"{hero.id} served beside the shrine's {keeper.label_word}. "
        f"{world.setting.opening}"
    )
    world.say(
        f"At the heart of that high place stood {relic.phrase}, and its duty was "
        f"simple and grand: {relic.purpose}."
    )


def festival_warning(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["wonder"] += 1
    world.say(world.setting.village_line)
    world.say(
        f"But by dusk the wind changed. {world.setting.storm_line} "
        f"{relic.voltage_line}"
    )


def hesitate(world: World, hero: Entity, fault: Fault) -> None:
    pred = predict_danger(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_bravery"] = pred["bravery"]
    world.say(
        f"{hero.id} saw {fault.the} and felt guilt move inside {hero.pronoun('object')} "
        f"like a cold pebble in a shoe. {fault.risk_line}"
    )
    if pred["danger"] >= 4:
        world.say(
            f"The air around the relic felt too sharp to trust. Even before a spark jumped, "
            f"{hero.id} could imagine the danger growing."
        )


def flashback(world: World, hero: Entity, fault: Fault) -> None:
    world.say(
        f"Then memory opened like a small door in {hero.pronoun('possessive')} mind. "
        f"Yesterday, while the afternoon was still bright, {fault.flashback}"
    )
    world.say(
        f"{hero.id} had seen {fault.the} afterward and told no one. Ever since then, "
        f"{hero.pronoun('possessive')} guilt had been waiting for the storm."
    )


def confess(world: World, hero: Entity, keeper: Entity, fault: Fault) -> None:
    hero.memes["confessed"] += 1
    world.say(
        f'"Keeper," {hero.id} said, and though {hero.pronoun("possessive")} voice shook, '
        f'it did not break, "I must tell the truth. {fault.The} is my fault. '
        f'I saw it, and I hid it."'
    )
    world.say(
        f"The {keeper.label_word} turned at once. {keeper.pronoun().capitalize()} did not shout. "
        f'{keeper.pronoun().capitalize()} laid a calm hand on {hero.id}\'s shoulder and said, '
        f'"Truth told in time is a brave lantern. Show me."'
    )


def inspect(world: World, keeper: Entity, fix: Fix, fault: Fault) -> None:
    world.say(
        f"Together they went to the relic. The {keeper.label_word} bent close to {fault.the} "
        f"and {fix.inspect_text}"
    )


def repair_success(world: World, hero: Entity, keeper: Entity, relic: Entity,
                   relic_cfg: Relic, fault: Fault, fix: Fix) -> None:
    relic.meters["repaired"] += 1
    propagate(world, narrate=False)
    hero.memes["bravery"] += 1
    world.say(
        f"{keeper.pronoun().capitalize()} {fix.success_text} {fault.the}. "
        f"{hero.id} held the lamp steady and did not step back."
    )
    world.say(
        f"Soon the hard humming eased. The dangerous voltage no longer snapped in the air, "
        f"and {relic_cfg.ending_line}"
    )


def repair_fail(world: World, hero: Entity, keeper: Entity, relic_cfg: Relic,
                fault: Fault, fix: Fix) -> None:
    world.get("relic").meters["dark"] += 1
    hero.memes["relief"] += 1
    hero.memes["guilt"] = 0.0
    world.say(
        f"The {keeper.label_word} {fix.fail_text} {fault.the}, then drew back. "
        f'"Not tonight," {keeper.pronoun()} said. "The storm has grown too fierce."'
    )
    world.say(
        f"So instead of forcing the relic awake, {keeper.pronoun()} lowered its power, covered "
        f"the damaged place, and let the holy fire sleep. {relic_cfg.label.capitalize()} went dark, "
        f"but the people below stayed safe."
    )


def lesson(world: World, hero: Entity, keeper: Entity, contained: bool) -> None:
    if contained:
        world.say(
            f'Afterward the {keeper.label_word} looked at {hero.id} and smiled a little. '
            f'"Bravery is not the same as never making a mistake," {keeper.pronoun()} said. '
            f'"Bravery is telling the truth before harm can grow."'
        )
    else:
        world.say(
            f'On the stone steps, the {keeper.label_word} wrapped a warm cloak around {hero.id}. '
            f'"Bravery came late tonight," {keeper.pronoun()} said softly, '
            f'"but it still kept the storm from taking more."'
        )


def ending(world: World, hero: Entity, relic_cfg: Relic, contained: bool) -> None:
    if contained:
        hero.memes["joy"] += 1
        world.say(
            f"Below the shrine, windows shone one by one, and the village lifted its face to the hill. "
            f"{hero.id}'s guilt was gone at last, not because the past had changed, but because "
            f"{hero.pronoun()} had met it with bravery."
        )
        world.say(
            f"From that night on, whenever the sky began to mutter, {hero.id} checked each sacred part "
            f"carefully and spoke up at the smallest crack. Thus {relic_cfg.label} kept watch, and so did {hero.id}."
        )
    else:
        world.say(
            f"All that night the village used small oil lamps instead of {relic_cfg.label}, and every child "
            f"could see that safety mattered more than pride."
        )
        world.say(
            f"When dawn returned, {hero.id} helped mend the relic properly in the clear morning light. "
            f"The guilt was lighter then, because the truth was no longer hidden."
        )


def tell(setting: Setting, relic_cfg: Relic, fault_cfg: Fault, fix_cfg: Fix,
         hero_name: str = "Iris", hero_gender: str = "girl", keeper_type: str = "keeper",
         delay: int = 0, storm_force: int = 1) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the keeper", role="keeper"))
    relic = world.add(Entity(id="relic", kind="thing", type="relic", label=relic_cfg.label))
    fault = world.add(Entity(id="fault", kind="thing", type="fault", label=fault_cfg.label))

    hero.attrs["name"] = hero_name
    keeper.memes["kindness"] = 1.0
    hero.memes["guilt"] = 1.0
    hero.memes["bravery"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] = 0.0
    relic.meters["damaged"] = 1.0
    relic.meters["danger"] = 0.0
    relic.meters["repaired"] = 0.0
    relic.meters["dark"] = 0.0
    fault.meters["severity"] = float(fault_cfg.severity)

    world.facts["hero_name"] = hero_name
    world.facts["storm_force"] = float(storm_force)
    world.facts["delay"] = delay
    world.facts["fault_id"] = fault_cfg.id
    world.facts["flashback_used"] = True

    introduce(world, hero, keeper, relic_cfg)
    festival_warning(world, hero, relic_cfg)

    world.para()
    propagate(world, narrate=False)
    hesitate(world, hero, fault_cfg)

    world.para()
    flashback(world, hero, fault_cfg)
    confess(world, hero, keeper, fault_cfg)

    world.para()
    inspect(world, keeper, fix_cfg, fault_cfg)
    contained = is_contained(fix_cfg, fault_cfg, storm_force, delay)
    if contained:
        repair_success(world, hero, keeper, relic, relic_cfg, fault_cfg, fix_cfg)
    else:
        repair_fail(world, hero, keeper, relic_cfg, fault_cfg, fix_cfg)

    world.para()
    lesson(world, hero, keeper, contained)
    ending(world, hero, relic_cfg, contained)

    world.facts.update(
        hero=hero,
        keeper=keeper,
        relic_cfg=relic_cfg,
        fault_cfg=fault_cfg,
        fix_cfg=fix_cfg,
        relic=relic,
        fault=fault,
        contained=contained,
        outcome="restored" if contained else "dark_for_the_night",
        severity=severity_of(fault_cfg, storm_force, delay),
        confessed=hero.memes["confessed"] >= THRESHOLD,
        brave=hero.memes["bravery"] >= THRESHOLD,
        voltage_word=True,
        guilt_word=True,
    )
    return world


SETTINGS = {
    "harbor_shrine": Setting(
        id="harbor_shrine",
        place="the harbor shrine",
        opening="Sea-winds circled the white tower above the harbor, and gulls wheeled around its bronze roof.",
        storm_line="Far off over the water, thunder rolled like a slow cart over hollow boards.",
        village_line="Below, the fishing village was tying bright ribbons to doors for the Night of Returning Light.",
        affords={"storm_beacon", "thunder_bell"},
        tags={"storm", "harbor"},
    ),
    "cedar_hill": Setting(
        id="cedar_hill",
        place="cedar hill",
        opening="On Cedar Hill, old trees leaned toward a ring of stones where the sky's gifts were guarded.",
        storm_line="Clouds braided themselves over the hill, and their shadows made the cedar needles shine darkly.",
        village_line="At the foot of the hill, families lit supper fires and waited for the first blessing-flash of evening.",
        affords={"storm_beacon", "cloud_mast"},
        tags={"storm", "hill"},
    ),
    "moon_steps": Setting(
        id="moon_steps",
        place="the moon steps",
        opening="The Moon Steps climbed above the valley in silver terraces where even whispers sounded sacred.",
        storm_line="The western sky drew on a deep purple robe, and thunder answered from behind the peaks.",
        village_line="In the valley below, children had set little bowls of flowers by the doors to greet the night's protection.",
        affords={"thunder_bell", "cloud_mast"},
        tags={"storm", "mountain"},
    ),
}

RELICS = {
    "storm_beacon": Relic(
        id="storm_beacon",
        label="storm beacon",
        phrase="the storm beacon, a tall lamp caged in copper vines",
        purpose="to shine over roofs and boats whenever the heavens grew wild",
        voltage_line="Inside the beacon, blue light gathered along the wires with a whisper of voltage.",
        ending_line="the beacon shone clear over the roofs and the dark water",
        parts={"glass", "wire"},
        tags={"voltage", "beacon"},
    ),
    "thunder_bell": Relic(
        id="thunder_bell",
        label="thunder bell",
        phrase="the thunder bell, a bronze bell hung with bright sky-wires",
        purpose="to sing one deep note that told the valley the shrine was still awake",
        voltage_line="Along the bell's hanging wires ran a bright thread of voltage, sharp enough to sting the eye.",
        ending_line="the bell gave one deep note, and the valley listened in peace",
        parts={"wire", "pin"},
        tags={"voltage", "bell"},
    ),
    "cloud_mast": Relic(
        id="cloud_mast",
        label="cloud mast",
        phrase="the cloud mast, a cedar pole crowned with a bowl of silver light",
        purpose="to gather storm-fire safely and send a calm glow down the hill paths",
        voltage_line="At its crown, pale sparks traced the mast with holy voltage.",
        ending_line="the mast poured a mild glow down the hill path like milk from the moon",
        parts={"glass", "pin"},
        tags={"voltage", "mast"},
    ),
}

FAULTS = {
    "cracked_glass": Fault(
        id="cracked_glass",
        label="cracked glass",
        the="the cracked glass",
        part="glass",
        severity=1,
        requires="insulate",
        sign="a silver crack running like frost",
        flashback="while racing a reed hoop around the platform, "
                  "hero had let it skip from hero's hand and strike the glass cage with a sharp clink",
        risk_line="If storm-fire touched that broken edge, the relic could spit wild sparks instead of steady light.",
        tags={"glass", "guilt"},
    ),
    "frayed_wire": Fault(
        id="frayed_wire",
        label="frayed wire",
        the="the frayed wire",
        part="wire",
        severity=2,
        requires="sleeve",
        sign="fine copper threads lifting like tiny whiskers",
        flashback="yesterday hero had tugged at the dangling prayer ribbons, and one hidden wire had scraped hard against a hook",
        risk_line="A frayed wire could let the running voltage leap where no hand or roof wanted it.",
        tags={"wire", "guilt", "voltage"},
    ),
    "loose_pin": Fault(
        id="loose_pin",
        label="loose bronze pin",
        the="the loose bronze pin",
        part="pin",
        severity=1,
        requires="anchor",
        sign="a fastening pin rocking with each gust",
        flashback="during play, hero had climbed where no apprentice should climb and knocked the pin sideways with one careless heel",
        risk_line="If the storm shook that pin free, the whole singing part could lurch out of place.",
        tags={"pin", "guilt"},
    ),
}

FIXES = {
    "amber_gloves": Fix(
        id="amber_gloves",
        label="amber gloves",
        sense=3,
        power=3,
        kinds={"insulate"},
        inspect_text="slipped on amber gloves before touching the broken edge",
        success_text="wrapped the crack in resin-cloth and settled a bright amber guard around",
        fail_text="tried to shield",
        qa_text="used amber gloves and resin-cloth to insulate the broken part",
        tags={"insulate", "voltage"},
    ),
    "clay_sleeve": Fix(
        id="clay_sleeve",
        label="clay sleeve",
        sense=3,
        power=4,
        kinds={"sleeve"},
        inspect_text="fitted a clay sleeve around the damaged place so the wire could be covered before the next surge",
        success_text="slid a cool clay sleeve over",
        fail_text="started to fit a clay sleeve over",
        qa_text="covered the damaged wire with a clay sleeve",
        tags={"wire", "voltage"},
    ),
    "cedar_wedge": Fix(
        id="cedar_wedge",
        label="cedar wedge",
        sense=2,
        power=2,
        kinds={"anchor"},
        inspect_text="tested the swaying fitting with a cedar wedge and a patient hand",
        success_text="set the pin firm with a cedar wedge beneath",
        fail_text="pressed a cedar wedge against",
        qa_text="secured the loose bronze pin with a cedar wedge",
        tags={"anchor"},
    ),
    "bare_hands": Fix(
        id="bare_hands",
        label="bare hands",
        sense=1,
        power=1,
        kinds={"insulate", "sleeve", "anchor"},
        inspect_text="reached straight toward the fault with bare hands",
        success_text="grabbed at",
        fail_text="reached for",
        qa_text="tried to touch the damaged part with bare hands",
        tags={"unsafe", "voltage"},
    ),
}

GIRL_NAMES = ["Iris", "Mira", "Nia", "Leda", "Tala", "Asha", "Rhea", "Dara", "Elia", "Sena"]
BOY_NAMES = ["Orin", "Tarin", "Niko", "Leor", "Pavel", "Soren", "Cael", "Ivo", "Milo", "Ren"]


@dataclass
class StoryParams:
    place: str
    relic: str
    fault: str
    fix: str
    hero_name: str
    hero_gender: str
    keeper_type: str
    delay: int = 0
    storm_force: int = 1
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
    "voltage": [
        (
            "What is voltage?",
            "Voltage is the push that makes electric charge want to move. When the push is strong, it can be dangerous, so grown-ups use safe tools and careful rules around it.",
        )
    ],
    "guilt": [
        (
            "What is guilt?",
            "Guilt is the heavy feeling you get when you know you did something wrong. That feeling can help you tell the truth and fix the problem.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when your body still feels scared. Telling the truth can be a brave act.",
        )
    ],
    "storm": [
        (
            "Why can storms be dangerous around tall metal things?",
            "Storms can send strong electricity through the air and into tall objects. That is why special towers and tools must be built and repaired carefully.",
        )
    ],
    "insulate": [
        (
            "What does it mean to insulate something?",
            "To insulate something means to cover it with a material that helps stop electricity from passing where it should not. That makes touching nearby parts safer.",
        )
    ],
    "wire": [
        (
            "Why is a frayed wire dangerous?",
            "A frayed wire has broken or loose strands, so electricity can escape the safe path. That can cause shocks, sparks, or fire.",
        )
    ],
    "anchor": [
        (
            "Why does a loose pin matter in a machine or tower?",
            "A loose pin can let an important part wobble or fall out of place. Small loose parts can lead to bigger trouble when wind or movement shakes them.",
        )
    ],
}
KNOWLEDGE_ORDER = ["voltage", "guilt", "bravery", "storm", "insulate", "wire", "anchor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic_cfg"]
    fault = f["fault_cfg"]
    outcome = f["outcome"]
    if outcome == "restored":
        return [
            'Write a child-facing myth that uses the words "voltage" and "guilt" and includes a flashback.',
            f"Tell a gentle myth about {hero.attrs['name']}, who hides a mistake at a shrine until a storm makes the danger real, and bravery means telling the truth.",
            f"Write a mythic story where {fault.the} threatens a sacred {relic.label}, but a brave confession leads to a safe repair and a bright ending.",
        ]
    return [
        'Write a child-facing myth that uses the words "voltage" and "guilt" and includes a flashback.',
        f"Tell a myth about {hero.attrs['name']}, whose hidden mistake leaves a sacred {relic.label} too dangerous to use during a storm.",
        f"Write a story where bravery comes through confession, even though the shrine must let the relic rest for the night instead of forcing a risky repair.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    relic = f["relic_cfg"]
    fault = f["fault_cfg"]
    fix = f["fix_cfg"]
    hero_name = hero.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a young shrine helper, and the keeper who watched over the sacred {relic.label}. Together they had to face a storm and a hidden mistake.",
        ),
        (
            f"Why did {hero_name} feel guilt?",
            f"{hero_name} felt guilt because the flashback shows that {hero.pronoun()} had caused {fault.the} the day before and then kept silent. The storm made that old mistake dangerous instead of small.",
        ),
        (
            "How does the flashback change the story?",
            f"The flashback reveals that the problem did not come from nowhere. It shows the real cause of the danger, so {hero_name}'s later confession feels brave and necessary.",
        ),
        (
            f"Why was {fault.the} dangerous?",
            f"{fault.risk_line} In this story, the relic was already gathering voltage from the storm, so the broken part mattered right away.",
        ),
        (
            f"How did {hero_name} show bravery?",
            f"{hero_name} showed bravery by telling the keeper the truth even while feeling scared. The confession came before more harm could grow, which is why the keeper called truth a brave lantern.",
        ),
    ]
    if f["contained"]:
        qa.append(
            (
                "How was the problem solved?",
                f"The keeper {fix.qa_text}. That safe repair calmed the relic before the storm could turn the fault into a bigger danger.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The sacred {relic.label} worked again, and the village saw its light or heard its signal. The ending proves that courage and honesty changed the night.",
            )
        )
    else:
        qa.append(
            (
                "Did they use the relic that night?",
                f"No. The keeper decided the storm was too fierce and let the relic rest in darkness for the night. That choice kept everyone safe, even though the shrine lost its bright sign until morning.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The relic stayed dark for the night, but the village was safe and {hero_name} was no longer hiding the truth. The ending shows that bravery can still matter even when a mistake cannot be fully fixed at once.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"voltage", "guilt", "bravery", "storm"}
    fault = world.facts["fault_cfg"]
    fix = world.facts["fix_cfg"]
    tags |= set(fault.tags)
    tags |= set(fix.tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} severity={world.facts.get('severity')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="harbor_shrine",
        relic="storm_beacon",
        fault="cracked_glass",
        fix="amber_gloves",
        hero_name="Iris",
        hero_gender="girl",
        keeper_type="keeper",
        delay=0,
        storm_force=1,
    ),
    StoryParams(
        place="cedar_hill",
        relic="cloud_mast",
        fault="loose_pin",
        fix="cedar_wedge",
        hero_name="Orin",
        hero_gender="boy",
        keeper_type="keeper",
        delay=1,
        storm_force=1,
    ),
    StoryParams(
        place="moon_steps",
        relic="thunder_bell",
        fault="frayed_wire",
        fix="clay_sleeve",
        hero_name="Mira",
        hero_gender="girl",
        keeper_type="keeper",
        delay=1,
        storm_force=1,
    ),
    StoryParams(
        place="harbor_shrine",
        relic="thunder_bell",
        fault="frayed_wire",
        fix="clay_sleeve",
        hero_name="Ren",
        hero_gender="boy",
        keeper_type="keeper",
        delay=2,
        storm_force=1,
    ),
    StoryParams(
        place="cedar_hill",
        relic="storm_beacon",
        fault="cracked_glass",
        fix="amber_gloves",
        hero_name="Tala",
        hero_gender="girl",
        keeper_type="keeper",
        delay=2,
        storm_force=1,
    ),
]


def explain_rejection(setting: Setting, relic: Relic, fault: Fault) -> str:
    if relic.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not keep a {relic.label}. "
            f"Choose a relic that belongs in that place.)"
        )
    if fault.part not in relic.parts:
        return (
            f"(No story: {fault.the} does not fit a {relic.label}. "
            f"That relic has different parts, so the flashback and repair would not make sense.)"
        )
    if select_fix(fault) is None:
        return (
            f"(No story: this world has no sensible repair for {fault.the}. "
            f"A story needs a safe fix the keeper could honestly try.)"
        )
    return "(No story: this combination is not supported by the shrine's logic.)"


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the sensible fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.fix not in FIXES or params.fault not in FAULTS:
        raise StoryError("(No story: invalid fix or fault id.)")
    fix = FIXES[params.fix]
    fault = FAULTS[params.fault]
    return "restored" if is_contained(fix, fault, params.storm_force, params.delay) else "dark_for_the_night"


ASP_RULES = r"""
valid(P, R, F) :- setting(P), affords(P, R), relic(R), fault(F), has_part(R, Part), needs_part(F, Part), sensible_fix_for(F).
sensible_fix_for(F) :- fault(F), fix(X), sense(X, S), sense_min(M), S >= M, repairs(X, K), needs_kind(F, K).

severity(FS + ST + D) :- chosen_fault(F), fault_severity(F, FS), storm_force(ST), delay(D).
fix_power(P) :- chosen_fix(X), power(X, P).
contained :- fix_power(P), severity(S), P >= S.
outcome(restored) :- contained.
outcome(dark_for_the_night) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for rid in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, rid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for part in sorted(relic.parts):
            lines.append(asp.fact("has_part", rid, part))
    for fid, fault in FAULTS.items():
        lines.append(asp.fact("fault", fid))
        lines.append(asp.fact("fault_severity", fid, fault.severity))
        lines.append(asp.fact("needs_part", fid, fault.part))
        lines.append(asp.fact("needs_kind", fid, fault.requires))
    for xid, fix in FIXES.items():
        lines.append(asp.fact("fix", xid))
        lines.append(asp.fact("sense", xid, fix.sense))
        lines.append(asp.fact("power", xid, fix.power))
        for kind in sorted(fix.kinds):
            lines.append(asp.fact("repairs", xid, kind))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_fault", params.fault),
            asp.fact("chosen_fix", params.fix),
            asp.fact("storm_force", params.storm_force),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=False, header="smoke")


def asp_verify() -> int:
    rc = 0

    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params unexpectedly failed for seed {seed}.")
            break

    bad = 0
    for params in cases:
        try:
            py_outcome = outcome_of(params)
            asp_result = asp_outcome(params)
        except StoryError as err:
            rc = 1
            print(f"Outcome check failed: {err}")
            bad += 1
            continue
        if py_outcome != asp_result:
            bad += 1
            print(
                f"MISMATCH outcome for {params.place}/{params.relic}/{params.fault}/{params.fix}: "
                f"python={py_outcome} asp={asp_result}"
            )
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        _smoke_generation()
        print("OK: smoke generation/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: mythic shrine, hidden guilt, brave confession, and safe repair."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the truth waits after the storm rises")
    ap.add_argument("--storm-force", type=int, choices=[1, 2], dest="storm_force")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    if args.place and args.relic and args.fault:
        setting = SETTINGS[args.place]
        relic = RELICS[args.relic]
        fault = FAULTS[args.fault]
        if (args.place, args.relic, args.fault) not in valid_combos():
            raise StoryError(explain_rejection(setting, relic, fault))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.relic is None or combo[1] == args.relic)
        and (args.fault is None or combo[2] == args.fault)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, relic_id, fault_id = rng.choice(sorted(combos))
    fault = FAULTS[fault_id]

    possible_fixes = [
        fid
        for fid, fix in FIXES.items()
        if fix.sense >= SENSE_MIN and compatible_fix(fault, fix)
    ]
    if args.fix is not None:
        if args.fix not in possible_fixes:
            raise StoryError(
                f"(No story: {FIXES[args.fix].label} does not properly repair {fault.the}. "
                f"Choose a fix that matches the fault.)"
            )
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(possible_fixes))

    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    storm_force = args.storm_force if args.storm_force is not None else rng.choice([1, 2])

    return StoryParams(
        place=place,
        relic=relic_id,
        fault=fault_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=gender,
        keeper_type="keeper",
        delay=delay,
        storm_force=storm_force,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError("(No story: invalid place id.)")
    if params.relic not in RELICS:
        raise StoryError("(No story: invalid relic id.)")
    if params.fault not in FAULTS:
        raise StoryError("(No story: invalid fault id.)")
    if params.fix not in FIXES:
        raise StoryError("(No story: invalid fix id.)")

    setting = SETTINGS[params.place]
    relic = RELICS[params.relic]
    fault = FAULTS[params.fault]
    fix = FIXES[params.fix]

    if (params.place, params.relic, params.fault) not in valid_combos():
        raise StoryError(explain_rejection(setting, relic, fault))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not compatible_fix(fault, fix):
        raise StoryError(
            f"(No story: {fix.label} does not match {fault.the}. Choose a proper repair.)"
        )

    world = tell(
        setting=setting,
        relic_cfg=relic,
        fault_cfg=fault,
        fix_cfg=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        keeper_type=params.keeper_type,
        delay=params.delay,
        storm_force=params.storm_force,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, relic, fault) combos:\n")
        for place, relic, fault in combos:
            repairs = sorted(
                fid for fid, fix in FIXES.items()
                if fix.sense >= SENSE_MIN and compatible_fix(FAULTS[fault], fix)
            )
            print(f"  {place:14} {relic:13} {fault:13}  [{', '.join(repairs)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.hero_name}: {p.relic} at {p.place} "
                f"({p.fault}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
