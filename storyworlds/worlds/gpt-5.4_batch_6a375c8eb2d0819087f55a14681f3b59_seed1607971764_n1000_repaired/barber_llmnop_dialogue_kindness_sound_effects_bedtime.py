#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barber_llmnop_dialogue_kindness_sound_effects_bedtime.py
===================================================================================

A standalone storyworld for a gentle bedtime-style barber visit. A child feels
nervous about the sound of a haircut tool, and a kind barber uses a fitting,
sound-aware comfort move to help. The silly bedtime word "llmnop" becomes part
of the reassurance.

This world models:
- physical state with meters (noise, hair_neat, tool_used)
- emotional state with memes (fear, trust, calm, pride)
- a small reasonableness gate:
    * a tool must suit the requested haircut
    * the chosen comfort must actually help with that tool's kind of sound
- a simple outcome model:
    * some combinations finish easily
    * some need a pause and an extra gentle choice before finishing

Run it
------
    python storyworlds/worlds/gpt-5.4/barber_llmnop_dialogue_kindness_sound_effects_bedtime.py
    python storyworlds/worlds/gpt-5.4/barber_llmnop_dialogue_kindness_sound_effects_bedtime.py --job bangs --tool clippers
    python storyworlds/worlds/gpt-5.4/barber_llmnop_dialogue_kindness_sound_effects_bedtime.py --qa --json
    python storyworlds/worlds/gpt-5.4/barber_llmnop_dialogue_kindness_sound_effects_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/barber_llmnop_dialogue_kindness_sound_effects_bedtime.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "barber_man"}
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
class Setting:
    id: str
    place: str
    glow: str
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
class HairJob:
    id: str
    label: str
    phrase: str
    needs_precision: int
    needs_mist: bool
    ending: str
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
class Tool:
    id: str
    label: str
    sound: str
    sound_kind: str
    loudness: int
    precision: int
    can_mist: bool = False
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
class Comfort:
    id: str
    label: str
    soothe: int
    helps: set[str]
    offer: str
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


def _r_startle(world: World) -> list[str]:
    child = world.get("child")
    tool = world.get("tool")
    if tool.meters["used"] < THRESHOLD:
        return []
    sig = ("startle", int(tool.meters["used"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    loudness = int(tool.attrs["loudness"])
    room = world.get("room")
    room.meters["noise"] += loudness
    child.memes["fear"] += loudness
    return ["__sound__"]


def _r_settle(world: World) -> list[str]:
    child = world.get("child")
    barber = world.get("barber")
    if barber.memes["kindness"] < THRESHOLD or child.memes["fear"] <= 0:
        return []
    sig = ("settle", int(barber.memes["kindness"]), int(child.memes["choice_bonus"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trust_gain = barber.memes["kindness"] + child.memes["choice_bonus"]
    child.memes["trust"] += trust_gain
    child.memes["calm"] += max(1.0, trust_gain - 1.0)
    child.memes["fear"] = max(0.0, child.memes["fear"] - trust_gain)
    return []


def _r_finish(world: World) -> list[str]:
    child = world.get("child")
    hair = world.get("hair")
    tool = world.get("tool")
    if tool.meters["used"] < THRESHOLD:
        return []
    if hair.meters["done"] >= THRESHOLD:
        return []
    needed = world.facts["finish_need"]
    if child.memes["calm"] + child.memes["trust"] < needed:
        return []
    sig = ("finish", int(tool.meters["used"]), int(child.memes["calm"]), int(child.memes["trust"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hair.meters["trimmed"] += 1
    hair.meters["done"] += 1
    child.memes["pride"] += 1
    return ["__finish__"]


CAUSAL_RULES = [
    Rule(name="startle", tag="emotional", apply=_r_startle),
    Rule(name="settle", tag="emotional", apply=_r_settle),
    Rule(name="finish", tag="physical", apply=_r_finish),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def tool_suits_job(tool: Tool, job: HairJob) -> bool:
    if tool.precision < job.needs_precision:
        return False
    if job.needs_mist and not tool.can_mist:
        return False
    return True


def comfort_helps_tool(comfort: Comfort, tool: Tool) -> bool:
    return tool.sound_kind in comfort.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for job_id, job in HAIR_JOBS.items():
            for tool_id, tool in TOOLS.items():
                if not tool_suits_job(tool, job):
                    continue
                for comfort_id, comfort in COMFORTS.items():
                    if comfort_helps_tool(comfort, tool):
                        combos.append((setting_id, job_id, tool_id, comfort_id))
    return combos


def easy_threshold(tool: Tool, sensitivity: int) -> float:
    return float(tool.loudness + sensitivity + 1)


def outcome_of(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    comfort = COMFORTS[params.comfort]
    direct_score = float((comfort.soothe * 2) + 1)
    return "easy_finish" if direct_score >= easy_threshold(tool, params.sensitivity) else "pause_finish"


def predict_after_comfort(world: World) -> dict:
    sim = world.copy()
    barber = sim.get("barber")
    child = sim.get("child")
    barber.memes["kindness"] += sim.facts["comfort_strength"]
    child.memes["choice_bonus"] += 0.0
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "trust": sim.get("child").memes["trust"],
        "calm": sim.get("child").memes["calm"],
        "done": sim.get("hair").meters["done"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, caregiver: Entity, setting: Setting) -> None:
    world.say(
        f"On a soft evening, {child.id} walked with {child.pronoun('possessive')} "
        f"{caregiver.label_word} to {setting.place}. {setting.glow}"
    )


def meet_barber(world: World, child: Entity, barber: Entity, job: HairJob) -> None:
    world.say(
        f'The barber smiled and patted the tall chair. "Good evening, {child.id}," '
        f'{barber.pronoun()} said. "We will make your {job.label} neat, and we will go gently."'
    )


def notice_need(world: World, child: Entity, job: HairJob) -> None:
    world.say(
        f"{child.id} touched {child.pronoun('possessive')} hair. It needed {job.phrase}, "
        f"but the big chair still looked a little strange before bedtime."
    )


def demonstrate_sound(world: World, child: Entity, barber: Entity, tool: Tool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The barber lifted {tool.label}. "{tool.sound}," it went. '
        f"The sound was small to the barber, but to {child.id} it felt much bigger."
    )


def child_reacts(world: World, child: Entity) -> None:
    fear = world.get("child").memes["fear"]
    if fear >= 3:
        world.say(
            f'{child.id} pulled {child.pronoun("possessive")} chin down into the cape. '
            f'"That sound is too loud for me," {child.pronoun()} whispered.'
        )
    else:
        world.say(
            f'{child.id} blinked at the sound. "I am not sure I like that," '
            f'{child.pronoun()} said.'
        )


def offer_comfort(world: World, child: Entity, barber: Entity, comfort: Comfort, tool: Tool) -> None:
    pred = predict_after_comfort(world)
    world.facts["predicted_done_after_comfort"] = pred["done"]
    world.say(
        f'The barber knelt so {barber.pronoun()} was eye to eye with {child.id}. '
        f'"{comfort.offer}"'
    )
    if comfort.id == "llmnop_song":
        world.say(
            f'"We can say llmnop together, nice and slow," {barber.pronoun()} added. '
            f'"The sound can have a friend."'
        )


def do_comfort(world: World, child: Entity, barber: Entity, comfort: Comfort) -> None:
    barber.memes["kindness"] += comfort.soothe
    world.say(comfort.action.replace("{child}", child.id))
    propagate(world, narrate=False)


def easy_finish_scene(world: World, child: Entity, barber: Entity, tool: Tool, job: HairJob) -> None:
    world.say(
        f'Soon the sound did not feel so sharp. "{tool.sound}," it went again, '
        f"and this time {child.id} stayed still and brave."
    )
    world.say(
        f"The barber worked carefully until {job.ending}. Tiny hairs drifted down like sleepy feathers."
    )


def pause_scene(world: World, child: Entity, barber: Entity, caregiver: Entity, tool: Tool) -> None:
    world.say(
        f"The barber stopped at once. {tool.label.capitalize()} went quiet. "
        f'"We can pause," {barber.pronoun()} said. "Nothing has to hurry."'
    )
    child.memes["choice_bonus"] += 1
    caregiver.memes["support"] += 1
    world.say(
        f'{child.id} took one hand from under the cape and found {child.pronoun("possessive")} '
        f'{caregiver.label_word}\'s fingers. Together they took three slow breaths.'
    )
    world.say(
        f'"Would you like one more listen, or shall we start with the softest touch?" '
        f'the barber asked.'
    )
    world.say(
        f'"The softest touch," said {child.id}.'
    )
    propagate(world, narrate=False)


def bedtime_end(world: World, child: Entity, caregiver: Entity, barber: Entity, job: HairJob, comfort: Comfort) -> None:
    world.say(
        f"When the haircut was done, {child.id} looked in the mirror and saw {job.ending}."
    )
    world.say(
        f'"I did it," {child.pronoun()} said, sounding surprised and pleased. '
        f'The barber smiled. "You did, and you told us what helped."'
    )
    if comfort.id == "llmnop_song":
        world.say(
            f'On the walk home, {child.id} softly sang "llmnop" into the sleepy dark, '
            f"and the whole evening felt gentler."
        )
    else:
        world.say(
            f"On the walk home, the night felt quiet again, and {setting_closing(world.setting)}"
        )


def setting_closing(setting: Setting) -> str:
    return setting.closing_image


def tell(
    setting: Setting,
    job: HairJob,
    tool: Tool,
    comfort: Comfort,
    child_name: str = "Mina",
    child_gender: str = "girl",
    caregiver_type: str = "mother",
    barber_name: str = "Nico",
    barber_type: str = "barber_man",
    sensitivity: int = 1,
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    child.id = child_name
    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, label="the caregiver", role="caregiver"))
    barber_ent = world.add(Entity(id="barber", kind="character", type=barber_type, label=barber_name, role="barber"))
    barber_ent.id = barber_name
    room = world.add(Entity(id="room", type="room", label="the barber shop"))
    hair = world.add(Entity(id="hair", type="hair", label="hair"))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        attrs={"loudness": tool.loudness, "sound_kind": tool.sound_kind},
    ))

    child.memes["fear"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["choice_bonus"] = 0.0
    caregiver.memes["support"] = 0.0
    barber_ent.memes["kindness"] = 0.0
    room.meters["noise"] = 0.0
    hair.meters["trimmed"] = 0.0
    hair.meters["done"] = 0.0
    tool_ent.meters["used"] = 0.0

    world.facts.update(
        setting=setting,
        job=job,
        tool_cfg=tool,
        comfort=comfort,
        child=child,
        caregiver=caregiver,
        barber=barber_ent,
        comfort_strength=comfort.soothe,
        sensitivity=sensitivity,
        finish_need=easy_threshold(tool, sensitivity),
    )

    introduce(world, child, caregiver, setting)
    meet_barber(world, child, barber_ent, job)
    notice_need(world, child, job)

    world.para()
    demonstrate_sound(world, child, barber_ent, tool)
    child_reacts(world, child)

    world.para()
    offer_comfort(world, child, barber_ent, comfort, tool)
    do_comfort(world, child, barber_ent, comfort)

    if hair.meters["done"] >= THRESHOLD:
        outcome = "easy_finish"
        easy_finish_scene(world, child, barber_ent, tool, job)
    else:
        outcome = "pause_finish"
        pause_scene(world, child, barber_ent, caregiver, tool)
        if hair.meters["done"] >= THRESHOLD:
            world.say(
                f'Snip by snip, or buzz by little buzz, the haircut went on until {job.ending}.'
            )
        else:
            raise StoryError("(Internal world error: the gentle pause should have been enough to finish the haircut.)")

    world.para()
    bedtime_end(world, child, caregiver, barber_ent, job, comfort)

    world.facts.update(
        outcome=outcome,
        sound=tool.sound,
        noise=world.get("room").meters["noise"],
        done=world.get("hair").meters["done"] >= THRESHOLD,
        fear_left=world.get("child").memes["fear"],
        trust=world.get("child").memes["trust"],
        calm=world.get("child").memes["calm"],
        pride=world.get("child").memes["pride"],
    )
    return world


SETTINGS = {
    "moon_shop": Setting(
        id="moon_shop",
        place="the little barber shop at the end of the lane",
        glow="A round lamp shone in the window like a low moon.",
        closing_image="the moon followed them home above the roofs.",
        tags={"barber_shop", "bedtime"},
    ),
    "corner_shop": Setting(
        id="corner_shop",
        place="the corner barber shop with the blue window shade",
        glow="Inside, the mirrors held a warm gold shine.",
        closing_image="the street looked calm, as if it were ready to yawn.",
        tags={"barber_shop", "bedtime"},
    ),
}

HAIR_JOBS = {
    "bangs": HairJob(
        id="bangs",
        label="bangs",
        phrase="a careful trim across the front",
        needs_precision=2,
        needs_mist=False,
        ending="short, tidy bangs above bright eyes",
        tags={"haircut"},
    ),
    "sides": HairJob(
        id="sides",
        label="sides",
        phrase="the sides to be tidied",
        needs_precision=1,
        needs_mist=False,
        ending="neat sides and a smooth little line around the ears",
        tags={"haircut"},
    ),
    "curls": HairJob(
        id="curls",
        label="curls",
        phrase="sleepy curls to be shaped without tugging",
        needs_precision=1,
        needs_mist=True,
        ending="soft curls sitting neatly in a springy row",
        tags={"haircut"},
    ),
}

TOOLS = {
    "scissors": Tool(
        id="scissors",
        label="the silver scissors",
        sound="snip snip",
        sound_kind="snip",
        loudness=1,
        precision=2,
        can_mist=False,
        tags={"scissors", "sound"},
    ),
    "clippers": Tool(
        id="clippers",
        label="the barber clippers",
        sound="bzzzz",
        sound_kind="buzz",
        loudness=3,
        precision=1,
        can_mist=False,
        tags={"clippers", "sound"},
    ),
    "spray_comb": Tool(
        id="spray_comb",
        label="the spray bottle and comb",
        sound="psst psst",
        sound_kind="mist",
        loudness=2,
        precision=1,
        can_mist=True,
        tags={"spray", "sound"},
    ),
}

COMFORTS = {
    "llmnop_song": Comfort(
        id="llmnop_song",
        label="the llmnop song",
        soothe=2,
        helps={"snip", "buzz", "mist"},
        offer="Would it help if we made a tiny song for the sound?",
        action='{child} listened while the barber tapped a slow rhythm on the chair and sang, "llmnop, llmnop," until the sound felt less lonely.',
        qa_text="turned the sound into a slow llmnop song",
        tags={"llmnop", "song", "kindness"},
    ),
    "mirror_moon": Comfort(
        id="mirror_moon",
        label="the moon mirror game",
        soothe=1,
        helps={"snip", "mist"},
        offer="Would it help if I drew a little moon on the mirror and told you each sound before it came?",
        action='{child} watched the moon shape in the mirror and heard each sound named before it happened.',
        qa_text="named each sound ahead of time and used a moon drawing in the mirror",
        tags={"mirror", "kindness"},
    ),
    "soft_demo": Comfort(
        id="soft_demo",
        label="the soft demo",
        soothe=2,
        helps={"buzz", "mist"},
        offer="Would it help if I let the tool whisper on my own sleeve first, so you can hear it from far away?",
        action='The barber let the tool whisper on {child}\'s sleeve from far away first, then set it quiet again so {child} could decide.',
        qa_text="gave a soft far-away demonstration first",
        tags={"demo", "kindness"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tessa", "June", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Sam", "Noah", "Finn"]
BARBER_NAMES = ["Nico", "Rosa", "Marlon", "Asha", "Toni", "Mira"]


@dataclass
class StoryParams:
    setting: str
    job: str
    tool: str
    comfort: str
    child_name: str
    child_gender: str
    caregiver: str
    barber_name: str
    barber_gender: str
    sensitivity: int = 1
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
    "barber": [
        (
            "What does a barber do?",
            "A barber cuts and tidies hair. A kind barber also helps people feel safe while it happens."
        )
    ],
    "clippers": [
        (
            "Why do clippers make a buzzing sound?",
            "Clippers have a tiny moving part inside that goes very fast. That fast motion makes the buzzing sound you hear."
        )
    ],
    "scissors": [
        (
            "Why do scissors sound like snip snip?",
            "The blades slide past each other and cut the hair in little bites. That movement makes the snip snip sound."
        )
    ],
    "spray": [
        (
            "Why does a spray bottle say psst psst?",
            "A spray bottle pushes out tiny drops of water through a small opening. The little burst of air makes the psst psst sound."
        )
    ],
    "kindness": [
        (
            "How can kindness help when a sound feels scary?",
            "Kindness can slow things down, explain what is happening, and help your body feel calmer. When you feel safer, the same sound can seem smaller."
        )
    ],
    "llmnop": [
        (
            "What is llmnop in this story?",
            "llmnop is a silly made-up bedtime word the barber and child say together. It turns a worrying moment into a playful one."
        )
    ],
}
KNOWLEDGE_ORDER = ["barber", "clippers", "scissors", "spray", "kindness", "llmnop"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    job = f["job"]
    tool = f["tool_cfg"]
    comfort = f["comfort"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "barber" and "llmnop".',
        f"Tell a gentle story where a child named {child.id} needs {job.label} at a barber shop, feels nervous about a {tool.sound} sound, and is helped by kindness.",
        f"Write a soft, dialogue-rich story where the comfort move is {comfort.label} and the ending proves the child feels braver than at the start.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    barber = f["barber"]
    caregiver = f["caregiver"]
    job = f["job"]
    tool = f["tool_cfg"]
    comfort = f["comfort"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child getting ready for a haircut, a kind barber named {barber.id}, and {child.pronoun('possessive')} {caregiver.label_word}. The story stays close to their small feelings in the shop."
        ),
        (
            f"Why did {child.id} feel worried?",
            f"{child.id} felt worried because {tool.label} made the sound {tool.sound}, and that sound seemed too big at first. The fear came from the noise before the haircut even really began."
        ),
        (
            f"How did the barber help {child.id}?",
            f"The barber {comfort.qa_text}. That kindness gave {child.id} a way to understand the sound instead of just enduring it."
        ),
    ]
    if outcome == "easy_finish":
        qa.append(
            (
                f"Did the haircut become easy right away?",
                f"Almost right away, yes. After the kind help, {child.id} stayed calm enough for the haircut to continue smoothly."
            )
        )
    else:
        qa.append(
            (
                f"What happened when the first comfort was not quite enough?",
                f"The barber paused instead of pushing on, and everything went quiet again. Then {child.id} got to breathe, hold {child.pronoun('possessive')} {caregiver.label_word}'s hand, and choose the softest way to continue."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {child.id} looking in the mirror and seeing {job.ending}. On the walk home, the night felt softer because the scary sound had become manageable."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"barber", "kindness"}
    tool_id = world.facts["tool_cfg"].id
    comfort_id = world.facts["comfort"].id
    if tool_id == "clippers":
        tags.add("clippers")
    if tool_id == "scissors":
        tags.add("scissors")
    if tool_id == "spray_comb":
        tags.add("spray")
    if comfort_id == "llmnop_song":
        tags.add("llmnop")
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_shop",
        job="bangs",
        tool="scissors",
        comfort="llmnop_song",
        child_name="Mina",
        child_gender="girl",
        caregiver="mother",
        barber_name="Nico",
        barber_gender="barber_man",
        sensitivity=1,
    ),
    StoryParams(
        setting="corner_shop",
        job="sides",
        tool="clippers",
        comfort="soft_demo",
        child_name="Owen",
        child_gender="boy",
        caregiver="father",
        barber_name="Rosa",
        barber_gender="woman",
        sensitivity=2,
    ),
    StoryParams(
        setting="moon_shop",
        job="curls",
        tool="spray_comb",
        comfort="mirror_moon",
        child_name="Lila",
        child_gender="girl",
        caregiver="mother",
        barber_name="Asha",
        barber_gender="woman",
        sensitivity=2,
    ),
    StoryParams(
        setting="corner_shop",
        job="sides",
        tool="clippers",
        comfort="llmnop_song",
        child_name="Theo",
        child_gender="boy",
        caregiver="mother",
        barber_name="Mira",
        barber_gender="woman",
        sensitivity=3,
    ),
]


def explain_tool_job(tool: Tool, job: HairJob) -> str:
    if tool.precision < job.needs_precision:
        return (
            f"(No story: {tool.label} is not precise enough for {job.label}. "
            f"That haircut needs a more careful tool.)"
        )
    return (
        f"(No story: {job.label} needs a little mist before shaping, but {tool.label} "
        f"cannot do that.)"
    )


def explain_comfort(tool: Tool, comfort: Comfort) -> str:
    kinds = ", ".join(sorted(comfort.helps))
    return (
        f"(No story: {comfort.label} does not fit the {tool.sound_kind} sound from {tool.label}. "
        f"It helps with {kinds}, so choose a comfort that actually matches the sound.)"
    )


ASP_RULES = r"""
suitable_tool(J,T) :- job(J), tool(T), precision(T,P), need_precision(J,N), P >= N,
                      not need_mist(J).
suitable_tool(J,T) :- job(J), tool(T), precision(T,P), need_precision(J,N), P >= N,
                      need_mist(J), can_mist(T).

matching_comfort(C,T) :- comfort(C), tool(T), sound_kind(T,K), helps(C,K).
valid(S,J,T,C) :- setting(S), suitable_tool(J,T), matching_comfort(C,T).

direct_score(V) :- chosen_comfort(C), soothe(C,S), V = S * 2 + 1.
easy_need(V) :- chosen_tool(T), loudness(T,L), sensitivity(SN), V = L + SN + 1.

outcome(easy_finish) :- direct_score(D), easy_need(N), D >= N.
outcome(pause_finish) :- direct_score(D), easy_need(N), D < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for jid, job in HAIR_JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("need_precision", jid, job.needs_precision))
        if job.needs_mist:
            lines.append(asp.fact("need_mist", jid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("precision", tid, tool.precision))
        lines.append(asp.fact("sound_kind", tid, tool.sound_kind))
        lines.append(asp.fact("loudness", tid, tool.loudness))
        if tool.can_mist:
            lines.append(asp.fact("can_mist", tid))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("soothe", cid, comfort.soothe))
        for kind in sorted(comfort.helps):
            lines.append(asp.fact("helps", cid, kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_comfort", params.comfort),
        asp.fact("sensitivity", params.sensitivity),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad.append((params, asp_outcome(params), outcome_of(params)))
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} scenario outcomes differ.")
        for params, a_out, p_out in bad[:5]:
            print(" ", params, a_out, p_out)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a kind barber, a nervous child, and a bedtime-soft haircut."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--job", choices=HAIR_JOBS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--barber-name")
    ap.add_argument("--barber-gender", choices=["woman", "barber_man"])
    ap.add_argument("--sensitivity", type=int, choices=[1, 2, 3])
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
    if args.job and args.tool:
        job = HAIR_JOBS[args.job]
        tool = TOOLS[args.tool]
        if not tool_suits_job(tool, job):
            raise StoryError(explain_tool_job(tool, job))
    if args.tool and args.comfort:
        tool = TOOLS[args.tool]
        comfort = COMFORTS[args.comfort]
        if not comfort_helps_tool(comfort, tool):
            raise StoryError(explain_comfort(tool, comfort))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.job is None or combo[1] == args.job)
        and (args.tool is None or combo[2] == args.tool)
        and (args.comfort is None or combo[3] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, job_id, tool_id, comfort_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    barber_gender = args.barber_gender or rng.choice(["woman", "barber_man"])
    barber_name = args.barber_name or rng.choice([n for n in BARBER_NAMES if n != child_name])
    sensitivity = args.sensitivity if args.sensitivity is not None else rng.choice([1, 2, 3])

    return StoryParams(
        setting=setting_id,
        job=job_id,
        tool=tool_id,
        comfort=comfort_id,
        child_name=child_name,
        child_gender=gender,
        caregiver=caregiver,
        barber_name=barber_name,
        barber_gender=barber_gender,
        sensitivity=sensitivity,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.job not in HAIR_JOBS:
        raise StoryError(f"(Unknown job: {params.job})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")

    setting = SETTINGS[params.setting]
    job = HAIR_JOBS[params.job]
    tool = TOOLS[params.tool]
    comfort = COMFORTS[params.comfort]

    if not tool_suits_job(tool, job):
        raise StoryError(explain_tool_job(tool, job))
    if not comfort_helps_tool(comfort, tool):
        raise StoryError(explain_comfort(tool, comfort))

    world = tell(
        setting=setting,
        job=job,
        tool=tool,
        comfort=comfort,
        child_name=params.child_name,
        child_gender=params.child_gender,
        caregiver_type=params.caregiver,
        barber_name=params.barber_name,
        barber_type=params.barber_gender,
        sensitivity=params.sensitivity,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, job, tool, comfort) combos:\n")
        for setting_id, job_id, tool_id, comfort_id in combos:
            print(f"  {setting_id:11} {job_id:7} {tool_id:10} {comfort_id}")
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
            header = f"### {p.child_name}: {p.job} with {p.tool} and {p.comfort} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
