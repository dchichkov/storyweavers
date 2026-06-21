#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py
====================================================================

A standalone storyworld about a child detective hearing a scary sound at night,
arguing with a sibling or friend about whether a bogey is hiding nearby, and
resolving the conflict by investigating the real cause.

The world model tracks:
- physical meters: noise, shadow, alarm, light
- emotional memes: fear, courage, trust, relief, conflict, curiosity

The core shape is a tiny detective story:
1. Setup: a pretend detective game and a nighttime clue.
2. Conflict: one child is sure there is a bogey; another disagrees or worries.
3. Investigation: they gather a safe tool and check the clue.
4. Resolution: the real cause is found and the conflict is resolved.
5. Ending image: the room looks different because knowledge replaced fear.

Run it
------
python storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py
python storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py --cause branch --tool flashlight
python storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py --cause cat --location attic
python storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py --all
python storyworlds/worlds/gpt-5.4/bogey_resolve_conflict_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
    clue_spot: str
    approach: str
    hiding_spot: str
    adult_path: str
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
class Cause:
    id: str
    source: str
    sound: str
    shadow: str
    reveal: str
    method: str
    safe_spot: str
    needs_window: bool = False
    needs_high_place: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    beam: str
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
    arrive: str
    calm: str
    method: str
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
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]

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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["noise"] < THRESHOLD and clue.meters["shadow"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("alarm", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        kid.meters["alarm"] += 1
    out.append("__alarm__")
    return out


def _r_conflict(world: World) -> list[str]:
    lead = world.get("lead")
    partner = world.get("partner")
    if lead.memes["accuses_bogey"] < THRESHOLD:
        return []
    if partner.memes["disagrees"] < THRESHOLD and partner.memes["worries"] < THRESHOLD:
        return []
    sig = ("conflict", "kids")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.memes["conflict"] += 1
    partner.memes["conflict"] += 1
    return ["__conflict__"]


def _r_resolve(world: World) -> list[str]:
    lead = world.get("lead")
    partner = world.get("partner")
    clue = world.get("clue")
    if world.facts.get("cause_found") and clue.meters["noise"] < THRESHOLD:
        sig = ("resolved", "kids")
        if sig in world.fired:
            return []
        world.fired.add(sig)
        lead.memes["relief"] += 1
        partner.memes["relief"] += 1
        lead.memes["conflict"] = 0.0
        partner.memes["conflict"] = 0.0
        return ["__resolved__"]
    return []


CAUSAL_RULES = [
    Rule(name="alarm", tag="emotional", apply=_r_alarm),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="resolve", tag="social", apply=_r_resolve),
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


def cause_fits(setting: Setting, cause: Cause) -> bool:
    if cause.needs_window and "window" not in setting.tags:
        return False
    if cause.needs_high_place and "high" not in setting.tags:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, cause in CAUSES.items():
            if cause_fits(setting, cause):
                combos.append((sid, cid))
    return combos


def predict_clue(world: World, cause: Cause) -> dict:
    sim = world.copy()
    clue = sim.get("clue")
    clue.meters["noise"] += 1
    clue.meters["shadow"] += 1
    sim.facts["cause_present"] = cause.id
    propagate(sim, narrate=False)
    lead = sim.get("lead")
    partner = sim.get("partner")
    return {
        "noise": clue.meters["noise"],
        "shadow": clue.meters["shadow"],
        "fear": lead.memes["fear"] + partner.memes["fear"],
    }


def introduce(world: World, lead: Entity, partner: Entity, setting: Setting) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"At bedtime, {lead.id} and {partner.id} were still whispering about their detective club. "
        f"They had promised to notice every clue in {setting.place}."
    )
    world.say(
        f"{lead.id} kept a pretend notebook under the pillow, and {partner.id} said a real detective always listened twice."
    )


def first_clue(world: World, lead: Entity, partner: Entity, setting: Setting, cause: Cause) -> None:
    clue = world.get("clue")
    clue.meters["noise"] += 1
    clue.meters["shadow"] += 1
    world.facts["suspected_cause"] = "bogey"
    propagate(world, narrate=False)
    world.say(
        f"Then a small sound came from {setting.clue_spot}: {cause.sound}. "
        f"A crooked shadow slid over the wall like {cause.shadow}."
    )
    world.say(
        f"{partner.id} sat up so fast that the blanket bunched around {partner.pronoun('object')}. "
        f"Both children stared at the dark shape and listened."
    )


def accuse_bogey(world: World, lead: Entity) -> None:
    lead.memes["accuses_bogey"] += 1
    world.say(
        f'"This is a real case," {lead.id} whispered. "I think a bogey is hiding there."'
    )


def disagree(world: World, lead: Entity, partner: Entity, cause: Cause) -> None:
    if partner.attrs.get("stance") == "skeptical":
        partner.memes["disagrees"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"Or maybe not," {partner.id} whispered back. "{cause.source.capitalize()} can make strange sounds at night."'
        )
    else:
        partner.memes["worries"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{partner.id} grabbed {lead.id}\'s sleeve. "Do not go close," {partner.pronoun()} said. '
            f'"What if it really is a bogey?"'
        )


def choose_tool(world: World, lead: Entity, partner: Entity, tool: Tool) -> None:
    world.get("tool").meters["light"] += 1
    lead.memes["courage"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'{lead.id} took {tool.phrase} and whispered, "A detective checks first and decides after."'
    )
    world.say(
        f"{partner.id} nodded, even though {partner.pronoun('possessive')} knees still felt shaky."
    )


def investigate(world: World, lead: Entity, partner: Entity, setting: Setting, tool: Tool, helper: Helper) -> None:
    world.say(
        f"Step by step, they went {setting.approach}. {tool.action.capitalize()}, and {tool.beam}."
    )
    world.say(
        f"When the sound came again, {lead.id} stopped, and {helper.label_word.capitalize()} {helper.arrive}."
    )
    for kid in (lead, partner):
        kid.memes["fear"] += 0.0
        kid.memes["curiosity"] += 1


def reveal(world: World, lead: Entity, partner: Entity, setting: Setting, cause: Cause, helper: Helper) -> None:
    clue = world.get("clue")
    clue.meters["noise"] = 0.0
    clue.meters["shadow"] = 0.0
    world.facts["cause_found"] = cause.id
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {helper.method}, and the mystery opened at once: {cause.reveal}."
    )
    world.say(
        f'"So that was the noise," {partner.id} said. "Not a bogey at all."'
    )
    world.say(
        f'{lead.id} let out a long breath. "Case solved," {lead.pronoun()} said. "We can resolve a scary idea by checking the clue."'
    )


def ending(world: World, lead: Entity, partner: Entity, setting: Setting, tool: Tool, helper: Helper, cause: Cause) -> None:
    for kid in (lead, partner):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f"{helper.calm} The room did not feel like a hiding place anymore."
    )
    world.say(
        f"{tool.phrase.capitalize()} rested on the blanket, and {setting.safe_spot if hasattr(setting, 'safe_spot') else cause.safe_spot} looked ordinary again."
    )
    world.say(
        f"Soon {lead.id} and {partner.id} were smiling at their solved case, while {cause.source} sounded small and harmless in the night."
    )


def tell(
    setting: Setting,
    cause: Cause,
    tool: Tool,
    helper: Helper,
    lead_name: str = "Nora",
    lead_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    stance: str = "skeptical",
    helper_type: str = "mother",
) -> World:
    world = World(setting)
    lead = world.add(Entity(id="lead", kind="character", type=lead_gender, label=lead_name, role="lead"))
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            type=partner_gender,
            label=partner_name,
            role="partner",
            attrs={"stance": stance},
        )
    )
    adult = world.add(Entity(id="adult", kind="character", type=helper_type, label="the adult", role="adult"))
    world.add(Entity(id="clue", type="clue", label="the clue"))
    world.add(Entity(id="tool", type="tool", label=tool.label))

    world.facts.update(
        lead=lead,
        partner=partner,
        adult=adult,
        setting=setting,
        cause=cause,
        tool=tool,
        helper=helper,
        cause_found="",
        suspected_cause="",
        stance=stance,
    )

    introduce(world, lead, partner, setting)
    first_clue(world, lead, partner, setting, cause)

    world.para()
    accuse_bogey(world, lead)
    disagree(world, lead, partner, cause)
    choose_tool(world, lead, partner, tool)

    world.para()
    investigate(world, lead, partner, setting, tool, adult)
    reveal(world, lead, partner, setting, cause, adult)
    ending(world, lead, partner, setting, tool, adult, cause)

    world.facts.update(
        conflict_started=world.get("lead").memes["accuses_bogey"] >= THRESHOLD
        and (world.get("partner").memes["disagrees"] >= THRESHOLD or world.get("partner").memes["worries"] >= THRESHOLD),
        resolved=world.facts["cause_found"] == cause.id,
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="their shared bedroom",
        clue_spot="the closet door",
        approach="across the striped rug toward the closet",
        hiding_spot="the closet",
        adult_path="from the hall",
        tags={"closet", "window"},
    ),
    "attic": Setting(
        id="attic",
        place="the little attic room",
        clue_spot="the wooden trunk",
        approach="past the old boxes toward the trunk",
        hiding_spot="the trunk corner",
        adult_path="up the narrow stairs",
        tags={"high"},
    ),
    "hall": Setting(
        id="hall",
        place="the upstairs hall",
        clue_spot="the coat rack",
        approach="past the night-light toward the coat rack",
        hiding_spot="the coat rack",
        adult_path="through the bathroom door",
        tags={"window"},
    ),
}

CAUSES = {
    "branch": Cause(
        id="branch",
        source="a branch in the wind",
        sound="tap-tap against the window",
        shadow="long fingers",
        reveal="a branch was brushing the glass and wobbling in the moonlight",
        method="pulled the curtain back",
        safe_spot="the window",
        needs_window=True,
        tags={"wind", "window"},
    ),
    "cat": Cause(
        id="cat",
        source="the cat",
        sound="a bump and a scratch",
        shadow="two quick ears and a tail",
        reveal="the cat had squeezed behind the basket and was batting a lost sock",
        method="lifted the laundry basket a little",
        safe_spot="the basket",
        tags={"cat", "pet"},
    ),
    "hanger": Cause(
        id="hanger",
        source="a loose hanger",
        sound="clack-clack from a small swing",
        shadow="a crooked dancing hook",
        reveal="one loose hanger was knocking against the rod each time the air moved",
        method="opened the closet door and held the swaying hanger still",
        safe_spot="the closet rod",
        tags={"closet"},
    ),
    "pigeon": Cause(
        id="pigeon",
        source="a pigeon on the roof",
        sound="soft thumps overhead",
        shadow="a bobbing shape sliding along the ceiling",
        reveal="a pigeon was pacing on the roof and making a moving shadow near the beam",
        method="pointed up to the roofline",
        safe_spot="the roof",
        needs_high_place=True,
        tags={"bird", "roof"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        action="it clicked on",
        beam="a yellow beam ran ahead of them",
        tags={"flashlight", "light"},
    ),
    "lantern": Tool(
        id="lantern",
        label="camping lantern",
        phrase="a little camping lantern",
        action="it glowed warm and steady",
        beam="a round pool of light spread over the floorboards",
        tags={"lantern", "light"},
    ),
    "nightlight": Tool(
        id="nightlight",
        label="night-light",
        phrase="the plug-in night-light from the hall",
        action="it shone softly",
        beam="its small light was enough to turn sharp shadows gentle",
        tags={"nightlight", "light"},
    ),
}

HELPERS = {
    "mother": Helper(
        id="mother",
        label="mom",
        arrive="came in from the hall in her slippers",
        calm="Mom tucked the blanket smooth and left the curtain tied back",
        method="checked the place calmly",
        tags={"adult"},
    ),
    "father": Helper(
        id="father",
        label="dad",
        arrive="came up the stairs with a sleepy smile",
        calm="Dad patted the doorframe and left the room a little brighter",
        method="looked carefully where they pointed",
        tags={"adult"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lena", "Ivy", "Rose", "Tess", "Maya", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Max", "Eli", "Sam", "Theo", "Finn", "Noah"]
STANCES = ["skeptical", "worried"]


@dataclass
class StoryParams:
    setting: str
    cause: str
    tool: str
    helper: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    stance: str
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
    "bogey": [
        (
            "What is a bogey in a scary story?",
            "A bogey is an imaginary scary creature people talk about in stories. It feels real when someone is frightened, but it is not a real animal or person.",
        )
    ],
    "flashlight": [
        (
            "What does a flashlight help you do?",
            "A flashlight helps you see in a dark place. Good light can make a confusing shadow easier to understand.",
        )
    ],
    "lantern": [
        (
            "What is a camping lantern?",
            "A camping lantern is a lamp that spreads light all around. It helps people see safely without guessing in the dark.",
        )
    ],
    "nightlight": [
        (
            "Why can a night-light make a room feel less scary?",
            "A night-light makes the room less dark, so corners and shadows are easier to see. When you can see better, your brain has less space to invent scary ideas.",
        )
    ],
    "window": [
        (
            "Why can a branch make scary sounds at night?",
            "Wind can push a branch against a window or wall and make tapping noises. In dim light, the branch can also throw a shadow that looks strange.",
        )
    ],
    "cat": [
        (
            "Why do cats make mystery noises at night?",
            "Cats can bump, scratch, and chase small things when a house is quiet. Those little sounds can seem much bigger at bedtime.",
        )
    ],
    "closet": [
        (
            "Why do closets look spooky in the dark?",
            "Closets hold hanging clothes and shapes that are hard to read in dim light. When shadows move, your eyes may mistake them for something else.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and checks what is really happening. A good detective does not decide the answer before investigating.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "bogey", "flashlight", "lantern", "nightlight", "window", "cat", "closet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    setting = f["setting"]
    cause = f["cause"]
    tool = f["tool"]
    stance = f["stance"]
    conflict_line = (
        f"{partner.label} argues that the clue has an ordinary cause"
        if stance == "skeptical"
        else f"{partner.label} is too scared to let {lead.label} investigate alone"
    )
    return [
        f'Write a short detective story for a 3-to-5-year-old where two children hear a nighttime clue, worry about a bogey, and resolve the mystery safely.',
        f"Tell a gentle mystery set in {setting.place} where {lead.label} and {partner.label} use {tool.phrase} to investigate a strange sound caused by {cause.source}.",
        f"Write a child-facing detective story with Conflict: {conflict_line}, but the children and a grown-up solve the case calmly in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    adult = f["adult"]
    setting = f["setting"]
    cause = f["cause"]
    tool = f["tool"]
    stance = f["stance"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.label} and {partner.label}, two children playing detective at bedtime, and their {adult.label_word} who helps check the clue. The story follows how they turn a scary guess into a solved mystery.",
        ),
        (
            "What made the children think something scary was there?",
            f"They heard {cause.sound} from {setting.clue_spot} and saw a shadow that looked strange on the wall. In the dark, those clues felt big enough to make {lead.label} whisper about a bogey.",
        ),
        (
            f"Why was there a conflict between {lead.label} and {partner.label}?",
            (
                f"There was a conflict because {lead.label} quickly guessed that a bogey was hiding nearby, "
                f"while {partner.label} "
                + (
                    f"thought there might be an ordinary cause instead."
                    if stance == "skeptical"
                    else f"was frightened and did not want {lead.pronoun('object')} to go closer."
                )
                + " They were reacting to the same clue in different ways."
            ),
        ),
        (
            f"How did they investigate safely?",
            f"They used {tool.phrase} and walked carefully while a grown-up came to help. The light let them inspect the clue instead of only imagining what it might be.",
        ),
        (
            "What was really making the noise?",
            f"It was {cause.source}. {cause.reveal[0].upper()}{cause.reveal[1:]}.",
        ),
        (
            "How did they resolve the mystery and the conflict?",
            f"They resolved both by checking the clue and learning the real cause. Once they understood what was there, the bogey idea disappeared and the argument melted away.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bogey", "detective"}
    tags |= set(f["tool"].tags)
    tags |= set(f["cause"].tags)
    if "closet" in f["setting"].tags:
        tags.add("closet")
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
    lines.append(f"  facts: cause_found={world.facts.get('cause_found')} stance={world.facts.get('stance')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="bedroom",
        cause="branch",
        tool="flashlight",
        helper="mother",
        lead_name="Nora",
        lead_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        stance="skeptical",
    ),
    StoryParams(
        setting="bedroom",
        cause="hanger",
        tool="nightlight",
        helper="father",
        lead_name="Maya",
        lead_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        stance="worried",
    ),
    StoryParams(
        setting="attic",
        cause="pigeon",
        tool="lantern",
        helper="father",
        lead_name="Ivy",
        lead_gender="girl",
        partner_name="Sam",
        partner_gender="boy",
        stance="skeptical",
    ),
    StoryParams(
        setting="hall",
        cause="cat",
        tool="flashlight",
        helper="mother",
        lead_name="Finn",
        lead_gender="boy",
        partner_name="Rose",
        partner_gender="girl",
        stance="worried",
    ),
]


def explain_rejection(setting: Setting, cause: Cause) -> str:
    if cause.needs_window and "window" not in setting.tags:
        return (
            f"(No story: {cause.source} needs a window, but {setting.place} has no window clue in this world. "
            f"Pick a setting like bedroom or hall.)"
        )
    if cause.needs_high_place and "high" not in setting.tags:
        return (
            f"(No story: {cause.source} makes sense only in a higher place, but {setting.place} is not modeled that way. "
            f"Pick the attic.)"
        )
    return "(No story: this setting and cause do not make a reasonable mystery.)"


ASP_RULES = r"""
fits(S, C) :- setting(S), cause(C), needs_window(C), has_window(S).
fits(S, C) :- setting(S), cause(C), needs_high(C), high_place(S).
fits(S, C) :- setting(S), cause(C), not needs_window(C), not needs_high(C).
fits(S, C) :- setting(S), cause(C), needs_window(C), has_window(S), not needs_high(C).
fits(S, C) :- setting(S), cause(C), needs_high(C), high_place(S), not needs_window(C).

valid(S, C) :- fits(S, C).

conflict_present :- stance(skeptical).
conflict_present :- stance(worried).
resolved         :- conflict_present, chosen_setting(S), chosen_cause(C), valid(S, C).
outcome(resolved) :- resolved.

#show valid/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "window" in setting.tags:
            lines.append(asp.fact("has_window", sid))
        if "high" in setting.tags:
            lines.append(asp.fact("high_place", sid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.needs_window:
            lines.append(asp.fact("needs_window", cid))
        if cause.needs_high_place:
            lines.append(asp.fact("needs_high", cid))
    for stance in STANCES:
        lines.append(asp.fact("stance_kind", stance))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_cause", params.cause),
            asp.fact("stance", params.stance),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if not cause_fits(SETTINGS[params.setting], CAUSES[params.cause]):
        return "?"
    return "resolved"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
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
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime detective mystery about a supposed bogey and a calm resolve."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--stance", choices=STANCES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible setting/cause combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cause:
        if not cause_fits(SETTINGS[args.setting], CAUSES[args.cause]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], CAUSES[args.cause]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, cause = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    lead_name, lead_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=lead_name)
    stance = args.stance or rng.choice(STANCES)
    return StoryParams(
        setting=setting,
        cause=cause,
        tool=tool,
        helper=helper,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        stance=stance,
    )


def _checked_lookup(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    setting = _checked_lookup(SETTINGS, params.setting, "setting")
    cause = _checked_lookup(CAUSES, params.cause, "cause")
    tool = _checked_lookup(TOOLS, params.tool, "tool")
    helper = _checked_lookup(HELPERS, params.helper, "helper")

    if not cause_fits(setting, cause):
        raise StoryError(explain_rejection(setting, cause))
    if params.stance not in STANCES:
        raise StoryError(f"(No story: unknown stance '{params.stance}'.)")

    world = tell(
        setting=setting,
        cause=cause,
        tool=tool,
        helper=helper,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        stance=params.stance,
        helper_type=params.helper,
    )
    return StorySample(
        params=params,
        story=world.render().replace("lead", params.lead_name).replace("partner", params.partner_name),
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
        print(f"{len(combos)} compatible (setting, cause) combos:\n")
        for setting, cause in combos:
            print(f"  {setting:8} {cause}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.lead_name} & {p.partner_name}: {p.cause} in {p.setting} ({p.tool}, {p.stance})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
