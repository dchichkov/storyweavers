#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py
===============================================================================

A standalone storyworld about two children helping the rover Curiosity in a
small space-science bay. One child gets too curious about a glowing sample,
something goes wrong, and a calm grown-up teaches the careful way to explore.

The world is built around a simple physical model:

    nudge unstable sample        -> sample starts rolling
    rolling fragile sample       -> sample cracks and spills glittering dust
    room danger                  -> children become scared

The story then branches:

* an older sibling may successfully stop the risky move first (averted)
* otherwise the sample rolls, and a grown-up may contain the problem
* if the response is too weak or too late, the sample is lost and the bay seals

All stories include the words "pure", "depressor", and "dedicate", and keep the
tone close to a child-facing space adventure.

Run it
------
    python storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py
    python storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py --sample comet_ice
    python storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py --response catch_glove
    python storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/pure_depressor_dedicate_curiosity_space_adventure.py --verify
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
CURIOSITY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    slippery: bool = False
    # Physical meters and emotional memes.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "scientist_f"}
        male = {"boy", "father", "man", "scientist_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"mother", "father"}:
            return "parent"
        if self.type in {"scientist_f", "scientist_m"}:
            return "captain"
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
    glow: str
    afford_samples: set[str] = field(default_factory=set)
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


@dataclass
class Sample:
    id: str
    label: str
    phrase: str
    color: str
    shell: str
    spread: int
    fragile: bool = True
    slippery: bool = True
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
class SafeTool:
    id: str
    label: str
    phrase: str
    use_text: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_roll(world: World) -> list[str]:
    out: list[str] = []
    sample = world.get("sample")
    if sample.meters["nudged"] < THRESHOLD or sample.meters["held"] >= THRESHOLD:
        return out
    if not sample.slippery:
        return out
    sig = ("roll", sample.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sample.meters["rolling"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__roll__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    sample = world.get("sample")
    if sample.meters["rolling"] < THRESHOLD or not sample.fragile:
        return out
    sig = ("crack", sample.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sample.meters["cracked"] += 1
    sample.meters["spilled"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__crack__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="roll", tag="physical", apply=_r_roll),
    Rule(name="crack", tag="physical", apply=_r_crack),
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


def sample_at_risk(sample: Sample) -> bool:
    return sample.slippery


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(sample: Sample, delay: int) -> int:
    return sample.spread + delay


def is_contained(response: Response, sample: Sample, delay: int) -> bool:
    return response.power >= severity_of(sample, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > CURIOSITY_INIT


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    sample = sim.get("sample")
    sample.meters["nudged"] += 1
    propagate(sim, narrate=False)
    return {
        "rolling": sample.meters["rolling"] >= THRESHOLD,
        "cracked": sample.meters["cracked"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def intro(world: World, a: Entity, b: Entity, mentor: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On {setting.place}, {a.id} and {b.id} hurried into the rover bay where "
        f"Curiosity waited under {setting.glow}."
    )
    world.say(
        f"A ribbon of pure white light slid across the floor, and the silver wheels "
        f"of the rover looked ready for a brand-new adventure."
    )
    world.say(
        f'{mentor.id}, the station captain, smiled and said, "Today we help Curiosity '
        f'check one tiny mystery from the stars."'
    )


def sample_setup(world: World, b: Entity, sample_cfg: Sample) -> None:
    world.say(
        f"On the work tray sat {sample_cfg.phrase}. Its {sample_cfg.color} shine made "
        f"it look as if a little moon had landed indoors."
    )
    world.say(
        f'{b.id} leaned closer. "{sample_cfg.label.capitalize()} from space!" '
        f'{b.pronoun().capitalize()} whispered.'
    )


def tempt(world: World, a: Entity, sample_cfg: Sample) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"{a.id}'s curiosity bubbled over. "
        f'"What if I just tap the {sample_cfg.label} and see what is inside?" '
        f'{a.pronoun().capitalize()} asked.'
    )
    world.say("For one excited moment, touching it seemed faster than waiting for the instruments.")


def warn(world: World, b: Entity, a: Entity, sample_cfg: Sample, tool: SafeTool, mentor: Entity) -> None:
    pred = predict_mishap(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["cracked"]:
        extra = f" If it rolled, its {sample_cfg.shell} shell could crack and spill sparkling dust."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, don\'t touch it with bare fingers," '
        f'{b.pronoun()} said. "Captain {mentor.id} said we use the {tool.label} first so the sample '
        f"stays still.{extra}\""
    )


def back_down(world: World, a: Entity, b: Entity, tool: SafeTool) -> None:
    a.memes["curiosity"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id}, who was older and sounded very sure. Then '
        f'{a.pronoun()} pulled {a.pronoun("possessive")} hand back and nodded.'
    )
    world.say(
        f'"Okay," {a.pronoun()} said. "We will do it the science way with the {tool.label}."'
    )


def defy(world: World, a: Entity, b: Entity, sample_cfg: Sample) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Just one tiny tap," {a.id} said, before {b.id} could stop {a.pronoun("object")}.'
    )
    world.say(
        f"{a.id}'s finger brushed the {sample_cfg.label}, and the little sample skipped across the tray."
    )


def mishap(world: World, sample_cfg: Sample) -> None:
    sample = world.get("sample")
    sample.meters["nudged"] += 1
    propagate(world, narrate=False)
    if sample.meters["cracked"] >= THRESHOLD:
        world.say(
            f"The {sample_cfg.label} rolled, struck the tray wall, and its {sample_cfg.shell} shell split "
            f"with a soft tick. A bright puff of star-dust shimmered into the air."
        )
    elif sample.meters["rolling"] >= THRESHOLD:
        world.say(
            f"The {sample_cfg.label} rolled in a fast silver circle, racing toward the edge of the tray."
        )
    else:
        world.say(
            f"The {sample_cfg.label} wobbled, and both children jumped back."
        )


def alarm(world: World, b: Entity, mentor: Entity, sample_cfg: Sample) -> None:
    if world.get("sample").meters["cracked"] >= THRESHOLD:
        world.say(f'"Captain {mentor.id}! The {sample_cfg.label} cracked!" {b.id} cried.')
    else:
        world.say(f'"Captain {mentor.id}! It is getting away!" {b.id} cried.')


def rescue(world: World, mentor: Entity, response: Response, sample_cfg: Sample) -> None:
    sample = world.get("sample")
    sample.meters["rolling"] = 0.0
    sample.meters["spilled"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{sample}", sample_cfg.label)
    world.say(
        f"Captain {mentor.id} moved as calmly as a pilot docking in the dark and {body}."
    )
    world.say(
        "The bay hummed softly again. The scary moment was over, and the children could breathe normally."
    )


def rescue_fail(world: World, mentor: Entity, response: Response, sample_cfg: Sample) -> None:
    body = response.fail.replace("{sample}", sample_cfg.label)
    world.get("room").meters["sealed"] += 1
    world.say(
        f"Captain {mentor.id} {body}."
    )
    world.say(
        f"Red safety lights blinked, and the rover bay sealed itself to protect Curiosity and the rest of the station."
    )


def lesson(world: World, mentor: Entity, a: Entity, b: Entity, tool: SafeTool, sample_cfg: Sample) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"Captain {mentor.id} knelt beside them. "
        f'"Curiosity is wonderful," {mentor.pronoun()} said, "but space asks for careful hands. '
        f'First we steady a mystery, then we study it."'
    )
    world.say(
        f'{mentor.pronoun().capitalize()} lifted the {tool.label}. "This sample depressor is for holding small '
        f'things gently, not for rushing them."'
    )
    world.say(
        f'"Let us dedicate the next page in the Curiosity log to what this little {sample_cfg.label} taught us," '
        f'{mentor.pronoun()} said.'
    )


def safe_finish(world: World, a: Entity, b: Entity, mentor: Entity, tool: SafeTool, sample_cfg: Sample) -> None:
    sample = world.get("sample")
    sample.meters["held"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["safety"] += 1
    b.memes["safety"] += 1
    world.say(
        f"Together they set the {tool.label} over the tiny find, and it held the sample as softly as a pillow holds a feather."
    )
    world.say(
        f"Then Curiosity's scanner painted {sample_cfg.color} lines across the screen, and the mystery opened in pictures instead of cracks."
    )
    world.say(
        f"{a.id} grinned, {b.id} wrote in the log, and Captain {mentor.id} clipped the page beside a bright star sticker."
    )
    world.say(
        "Under the dome, the rover bay felt like a true space adventure again—quiet, careful, and full of wonder."
    )


def sad_finish(world: World, a: Entity, b: Entity, mentor: Entity, sample_cfg: Sample) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"The sample was gone for now, but Curiosity was safe. Captain {mentor.id} hugged both children and reminded them that a lost rock was better than a hurt explorer."
    )
    world.say(
        f"{a.id} and {b.id} promised that next time they would wait for tools and careful instructions before touching any new space treasure."
    )
    world.say(
        f"Later, they still dedicated a page in the log to the little {sample_cfg.label}, drawing it from memory under the soft station lights."
    )


def tell(
    setting: Setting,
    sample_cfg: Sample,
    tool: SafeTool,
    response: Response,
    *,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    cautioner: str = "Eli",
    cautioner_gender: str = "boy",
    mentor_name: str = "Mira",
    mentor_type: str = "scientist_f",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation, "trust": trust},
    ))
    mentor = world.add(Entity(
        id=mentor_name,
        kind="character",
        type=mentor_type,
        role="mentor",
        label="the captain",
    ))
    world.add(Entity(id="room", type="bay", label="the rover bay"))
    world.add(Entity(
        id="sample",
        type="sample",
        label=sample_cfg.label,
        fragile=sample_cfg.fragile,
        slippery=sample_cfg.slippery,
    ))
    world.add(Entity(id="rover", type="rover", label="Curiosity"))

    a.memes["curiosity"] = CURIOSITY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    world.facts["predicted_danger"] = 0
    world.facts["relation"] = relation

    intro(world, a, b, mentor, setting)
    sample_setup(world, b, sample_cfg)

    world.para()
    tempt(world, a, sample_cfg)
    warn(world, b, a, sample_cfg, tool, mentor)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, tool)
        world.para()
        lesson(world, mentor, a, b, tool, sample_cfg)
        safe_finish(world, a, b, mentor, tool, sample_cfg)
        severity = 0
        contained = True
    else:
        defy(world, a, b, sample_cfg)
        world.para()
        mishap(world, sample_cfg)
        alarm(world, b, mentor, sample_cfg)
        severity = severity_of(sample_cfg, delay)
        world.get("sample").meters["severity"] = float(severity)
        contained = is_contained(response, sample_cfg, delay)
        world.para()
        if contained:
            rescue(world, mentor, response, sample_cfg)
            lesson(world, mentor, a, b, tool, sample_cfg)
            world.para()
            safe_finish(world, a, b, mentor, tool, sample_cfg)
        else:
            rescue_fail(world, mentor, response, sample_cfg)
            sad_finish(world, a, b, mentor, sample_cfg)

    outcome = "averted" if averted else ("contained" if contained else "lost")
    world.facts.update(
        instigator=a,
        cautioner=b,
        mentor=mentor,
        setting=setting,
        sample_cfg=sample_cfg,
        tool=tool,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        sample_broke=world.get("sample").meters["cracked"] >= THRESHOLD,
        promise=world.kids()[0].memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_base": Setting(
        id="moon_base",
        place="the moon base",
        glow="the blue curve of Earth in the window",
        afford_samples={"comet_ice", "moon_pearl"},
    ),
    "mars_dome": Setting(
        id="mars_dome",
        place="the Mars dome",
        glow="the rosy shine of evening dust outside the glass",
        afford_samples={"comet_ice", "sun_seed", "moon_pearl"},
    ),
    "orbital_lab": Setting(
        id="orbital_lab",
        place="the orbital lab",
        glow="a slow sweep of stars beyond the round window",
        afford_samples={"sun_seed", "moon_pearl"},
    ),
}

SAMPLES = {
    "comet_ice": Sample(
        id="comet_ice",
        label="comet ice",
        phrase="a bead of comet ice in a clear dish",
        color="silver-blue",
        shell="thin",
        spread=3,
        fragile=True,
        slippery=True,
        tags={"ice", "sample"},
    ),
    "moon_pearl": Sample(
        id="moon_pearl",
        label="moon pearl",
        phrase="a round moon pearl no bigger than a marble",
        color="soft white",
        shell="hard",
        spread=1,
        fragile=False,
        slippery=True,
        tags={"moon", "sample"},
    ),
    "sun_seed": Sample(
        id="sun_seed",
        label="sun seed",
        phrase="a warm golden sun seed resting in a tiny ring",
        color="gold",
        shell="papery",
        spread=2,
        fragile=True,
        slippery=True,
        tags={"seed", "sample"},
    ),
}

SAFE_TOOLS = {
    "depressor": SafeTool(
        id="depressor",
        label="sample depressor",
        phrase="the sample depressor",
        use_text="held the sample still with the sample depressor",
        tags={"depressor", "science_tool"},
    ),
    "scanner": SafeTool(
        id="scanner",
        label="soft scanner ring",
        phrase="the soft scanner ring",
        use_text="settled the scanner ring around the sample",
        tags={"scanner", "science_tool"},
    ),
}

RESPONSES = {
    "vacuum_dome": Response(
        id="vacuum_dome",
        sense=3,
        power=4,
        text="dropped a clear vacuum dome over the tray and drew every sparkling bit back into the filter",
        fail="dropped a clear vacuum dome over the tray, but the spill had already drifted too far through the bay",
        qa_text="used a clear vacuum dome to trap the spill",
        tags={"vacuum", "cleanup"},
    ),
    "catch_glove": Response(
        id="catch_glove",
        sense=2,
        power=2,
        text="snapped on a padded catch glove and scooped the {sample} back to safety",
        fail="snapped on a padded catch glove, but the {sample} slipped past and the warning doors began to close",
        qa_text="used a padded catch glove to scoop the sample up",
        tags={"glove", "cleanup"},
    ),
    "boot_tap": Response(
        id="boot_tap",
        sense=1,
        power=1,
        text="tried to stop the sample with the toe of a space boot",
        fail="tried to stop the sample with the toe of a space boot, which only knocked it farther away",
        qa_text="tried to stop it with a space boot",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zoe", "Ava", "Nia", "Iris", "Mina"]
BOY_NAMES = ["Eli", "Leo", "Kai", "Noah", "Finn", "Milo", "Theo", "Arlo"]
TRAITS = ["careful", "steady", "patient", "thoughtful", "curious", "bright"]


@dataclass
class StoryParams:
    setting: str
    sample: str
    tool: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    mentor_name: str
    mentor_type: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
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
    "Curiosity": [
        (
            "What is Curiosity in this story world?",
            "Curiosity is a rover that explores and studies strange places. A rover is a robot with wheels and tools that helps people learn about space."
        )
    ],
    "depressor": [
        (
            "What does a sample depressor do?",
            "A sample depressor holds a tiny object still so it does not slide or bounce away. It helps scientists look carefully before touching anything else."
        )
    ],
    "vacuum": [
        (
            "What is a vacuum dome for?",
            "A vacuum dome covers a small area and traps loose dust or crumbs so they cannot drift around. In a lab, that keeps the room cleaner and safer."
        )
    ],
    "glove": [
        (
            "Why would a padded catch glove help with a rolling sample?",
            "A padded glove can scoop up a small rolling thing without squeezing it too hard. That makes it useful for a sample that is moving but not breaking into dust."
        )
    ],
    "ice": [
        (
            "Why can comet ice be tricky to hold?",
            "Comet ice can be very cold and slippery. If it slides, it can bump into something and crack."
        )
    ],
    "seed": [
        (
            "Why should you be gentle with a tiny seed from a lab tray?",
            "A tiny seed can be delicate, so rough hands may crush or scatter it. Gentle tools help scientists learn without ruining what they found."
        )
    ],
    "moon": [
        (
            "Why do round things roll away easily?",
            "Round things have curved sides, so they can start moving with only a little push. That is why marbles and beads can surprise you."
        )
    ],
    "sample": [
        (
            "What is a sample?",
            "A sample is a small piece taken for studying. Scientists use samples to learn about bigger things, like rocks, ice, soil, or seeds."
        )
    ],
}
KNOWLEDGE_ORDER = ["Curiosity", "sample", "depressor", "vacuum", "glove", "ice", "seed", "moon"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id, setting in SETTINGS.items():
        for sample_id in sorted(setting.afford_samples):
            sample = SAMPLES[sample_id]
            if sample_at_risk(sample):
                combos.append((setting_id, sample_id))
    return combos


def explain_sample(sample: Sample, setting: Setting) -> str:
    return (
        f"(No story: {sample.label} is not part of the sample list for {setting.place}. "
        f"Pick one of: {', '.join(sorted(setting.afford_samples))}.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    if is_contained(RESPONSES[params.response], SAMPLES[params.sample], params.delay):
        return "contained"
    return "lost"


CURATED = [
    StoryParams(
        setting="mars_dome",
        sample="comet_ice",
        tool="depressor",
        response="vacuum_dome",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Eli",
        cautioner_gender="boy",
        mentor_name="Mira",
        mentor_type="scientist_f",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        setting="orbital_lab",
        sample="moon_pearl",
        tool="depressor",
        response="catch_glove",
        instigator="Kai",
        instigator_gender="boy",
        cautioner="Luna",
        cautioner_gender="girl",
        mentor_name="Sol",
        mentor_type="scientist_m",
        trait="bright",
        delay=0,
        instigator_age=6,
        cautioner_age=6,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        setting="moon_base",
        sample="comet_ice",
        tool="depressor",
        response="catch_glove",
        instigator="Arlo",
        instigator_gender="boy",
        cautioner="Mina",
        cautioner_gender="girl",
        mentor_name="Mira",
        mentor_type="scientist_f",
        trait="steady",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        setting="orbital_lab",
        sample="sun_seed",
        tool="depressor",
        response="vacuum_dome",
        instigator="Iris",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        mentor_name="Sol",
        mentor_type="scientist_m",
        trait="patient",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    sample_cfg = f["sample_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short space-adventure story for a 3-to-5-year-old that includes the words "pure", "depressor", and "dedicate".',
            f"Tell a gentle story where {a.id} gets curious about a {sample_cfg.label}, but {b.id} stops the risky touch before anything breaks.",
            f"Write a rover-bay story about Curiosity where careful science wins over rushing."
        ]
    if outcome == "lost":
        return [
            'Write a cautionary space-adventure story for a 3-to-5-year-old that includes the words "pure", "depressor", and "dedicate".',
            f"Tell a story where {a.id} touches a {sample_cfg.label} too soon, the problem grows too big, and the room has to seal to keep Curiosity safe.",
            "Write a child-facing science story with a sad but safe ending where the children learn to wait for the right tools."
        ]
    return [
        'Write a short space-adventure story for a 3-to-5-year-old that includes the words "pure", "depressor", and "dedicate".',
        f"Tell a story where {a.id} is too curious about a {sample_cfg.label}, but a calm captain fixes the problem and teaches careful exploration.",
        "Write a rover-bay adventure about Curiosity that ends with a safer way to study a mystery from space."
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    mentor = f["mentor"]
    sample_cfg = f["sample_cfg"]
    tool = f["tool"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, helping Curiosity in the rover bay with Captain {mentor.id}. They begin the story excited to study something tiny from space."
        ),
        (
            "What did the children find?",
            f"They found {sample_cfg.phrase}. It looked so special and bright that it made {a.id} want to touch it right away."
        ),
        (
            f"Why did {b.id} warn {a.id} not to touch the sample?",
            f"{b.id} knew the sample could slide if someone tapped it with bare fingers. In this world, that kind of rolling can quickly become a bigger problem, especially with something delicate."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed the story before anything went wrong?",
                f"{a.id} listened when {b.id} spoke firmly and pulled a hand back in time. Because they paused, the captain could bring out the {tool.label} and the mystery stayed safe."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with careful science instead of a mishap. The children used the {tool.label}, wrote in the Curiosity log, and felt proud of exploring the gentle way."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened after the sample was touched?",
                f"The sample rolled, and in this story it even cracked and spilled a little glittering dust. That scary turn happened because curiosity moved faster than the plan."
            )
        )
        qa.append(
            (
                f"How did Captain {mentor.id} fix the problem?",
                f"Captain {mentor.id} {response.qa_text.replace('{sample}', sample_cfg.label)}. That quick response stopped the danger before the whole bay had to shut down."
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that curiosity is good when it walks beside care. The captain even said they would dedicate a page in the log to that lesson, so they would remember it later."
            )
        )
    else:
        qa.append(
            (
                "Why was the ending sad?",
                f"The grown-up could not stop the problem in time, so the bay had to seal and the sample was lost. Everyone stayed safe, but the little space mystery was gone."
            )
        )
        qa.append(
            (
                "What did the children learn at the end?",
                f"They learned to wait for tools and instructions before touching new samples. The story shows that being patient can protect both explorers and discoveries."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"Curiosity"} | set(world.facts["sample_cfg"].tags) | set(world.facts["tool"].tags)
    outcome = world.facts["outcome"]
    if outcome != "averted":
        tags |= set(world.facts["response"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if ent.fragile:
            flags.append("fragile")
        if ent.slippery:
            flags.append("slippery")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reasonableness gate
at_risk(S) :- sample(S), slippery(S).
valid(Place,S) :- setting(Place), affords(Place,S), at_risk(S).

sensible(R) :- response(R), sense(R,N), sense_min(M), N >= M.

% outcome model
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), curiosity_init(K), A > K.

severity(V + D) :- chosen_sample(S), spread(S,V), delay(D).
resp_power(P) :- chosen_response(R), power(R,P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for sample_id in sorted(setting.afford_samples):
            lines.append(asp.fact("affords", setting_id, sample_id))
    for sample_id, sample in SAMPLES.items():
        lines.append(asp.fact("sample", sample_id))
        lines.append(asp.fact("spread", sample_id, sample.spread))
        if sample.slippery:
            lines.append(asp.fact("slippery", sample_id))
        if sample.fragile:
            lines.append(asp.fact("fragile", sample_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_sample", params.sample),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome predictions differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Curiosity, a tiny space sample, and the careful way to explore."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sample", choices=SAMPLES)
    ap.add_argument("--tool", choices=SAFE_TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--mentor", choices=["scientist_f", "scientist_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start for the mishap before the grown-up response")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.sample:
        if args.sample not in SETTINGS[args.setting].afford_samples:
            raise StoryError(explain_sample(SAMPLES[args.sample], SETTINGS[args.setting]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.tool and args.tool not in SAFE_TOOLS:
        raise StoryError("(Unknown tool.)")

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sample is None or combo[1] == args.sample)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sample_id = rng.choice(sorted(combos))
    tool_id = args.tool or "depressor"
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    mentor_type = args.mentor or rng.choice(["scientist_f", "scientist_m"])
    mentor_name = rng.choice(["Mira", "Sol", "Aster", "Juno"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        setting=setting_id,
        sample=sample_id,
        tool=tool_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.sample not in SAMPLES:
        raise StoryError(f"(Unknown sample: {params.sample})")
    if params.tool not in SAFE_TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.sample not in SETTINGS[params.setting].afford_samples:
        raise StoryError(explain_sample(SAMPLES[params.sample], SETTINGS[params.setting]))

    world = tell(
        SETTINGS[params.setting],
        SAMPLES[params.sample],
        SAFE_TOOLS[params.tool],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        mentor_name=params.mentor_name,
        mentor_type=params.mentor_type,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, sample) combos:\n")
        for setting_id, sample_id in combos:
            print(f"  {setting_id:11} {sample_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.sample} at {p.setting} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
