#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flattery_prominent_mumps_flashback_rhyme_repetition_rhyming.py
==========================================================================================

A standalone storyworld for a small rhyming domain:

A child longs for a prominent place in a rhyme-day celebration, tries a little
flattery to get it, then wakes up with mumps and must stay home. A flashback
helps the child see the difference between sweet words and true kindness. With
an honest apology and a fitting plan, the child still joins the celebration in
a gentle, child-facing way.

The world is deliberately narrow. It models:
- a showcase and a coveted prominent role,
- a flattery attempt that strains trust,
- mumps causing a stay-home turn,
- a flashback that changes the hero's feelings,
- a resolution method that must actually fit the setting.

Run it
------
    python storyworlds/worlds/gpt-5.4/flattery_prominent_mumps_flashback_rhyme_repetition_rhyming.py
    python storyworlds/worlds/gpt-5.4/flattery_prominent_mumps_flashback_rhyme_repetition_rhyming.py --showcase parade --resolution window_wave
    python storyworlds/worlds/gpt-5.4/flattery_prominent_mumps_flashback_rhyme_repetition_rhyming.py --showcase recital --resolution window_wave
    python storyworlds/worlds/gpt-5.4/flattery_prominent_mumps_flashback_rhyme_repetition_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/flattery_prominent_mumps_flashback_rhyme_repetition_rhyming.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_woman"}
        male = {"boy", "father", "man", "teacher_man"}
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
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
        }.get(self.type, self.label or self.type)
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
    outdoor: bool
    pass_home: bool
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
class Showcase:
    id: str
    label: str
    chant: str
    opening: str
    phrase: str
    roles: set[str]
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
class RoleCfg:
    id: str
    label: str
    prop: str
    prominent_text: str
    rhyme_line: str
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
class Resolution:
    id: str
    label: str
    needs_outdoor: bool = False
    needs_indoor: bool = False
    needs_pass_home: bool = False
    text: str = ""
    ending: str = ""
    qa_text: str = ""
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


def _r_mumps_rest(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["mumps"] < THRESHOLD:
        return out
    sig = ("mumps_rest", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["at_home"] += 1
    hero.meters["cannot_attend"] += 1
    hero.memes["disappointment"] += 1
    out.append("__mumps__")
    return out


def _r_flattery_strain(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return out
    if hero.memes["used_flattery"] < THRESHOLD:
        return out
    sig = ("flattery_strain", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["uneasy"] += 1
    friend.memes["trust"] -= 1
    hero.memes["vanity"] += 1
    out.append("__strain__")
    return out


def _r_apology_heals(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if hero is None or friend is None:
        return out
    if hero.memes["honest_apology"] < THRESHOLD:
        return out
    sig = ("apology_heals", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["trust"] += 2
    friend.memes["care"] += 1
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    out.append("__healed__")
    return out


def _r_included(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero is None:
        return out
    if hero.meters["at_home"] < THRESHOLD or world.facts.get("resolution_ready", 0.0) < THRESHOLD:
        return out
    sig = ("included", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["included"] += 1
    hero.memes["sadness"] = 0.0
    out.append("__included__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="mumps_rest", tag="physical", apply=_r_mumps_rest),
    Rule(name="flattery_strain", tag="social", apply=_r_flattery_strain),
    Rule(name="apology_heals", tag="social", apply=_r_apology_heals),
    Rule(name="included", tag="social", apply=_r_included),
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


def role_fits(showcase: Showcase, role: RoleCfg) -> bool:
    return role.id in showcase.roles


def resolution_fits(setting: Setting, resolution: Resolution) -> bool:
    if resolution.needs_outdoor and not setting.outdoor:
        return False
    if resolution.needs_indoor and setting.outdoor:
        return False
    if resolution.needs_pass_home and not setting.pass_home:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for showcase_id, showcase in SHOWCASES.items():
            for role_id, role in ROLES.items():
                for resolution_id, resolution in RESOLUTIONS.items():
                    if role_fits(showcase, role) and resolution_fits(setting, resolution):
                        combos.append((setting_id, showcase_id, role_id, resolution_id))
    return sorted(combos)


def explain_role(showcase: Showcase, role: RoleCfg) -> str:
    allowed = ", ".join(sorted(showcase.roles))
    return (
        f"(No story: {role.label} does not fit the {showcase.label}. "
        f"That celebration only supports: {allowed}.)"
    )


def explain_resolution(setting: Setting, resolution: Resolution) -> str:
    if resolution.needs_outdoor and not setting.outdoor:
        return (
            f"(No story: {resolution.label} only makes sense for an outdoor celebration, "
            f"but {setting.place} is indoors.)"
        )
    if resolution.needs_indoor and setting.outdoor:
        return (
            f"(No story: {resolution.label} needs an indoor room and wall space, "
            f"but {setting.place} is outdoors.)"
        )
    if resolution.needs_pass_home and not setting.pass_home:
        return (
            f"(No story: {resolution.label} only works when the event passes the child's home.)"
        )
    return "(No story: that setting and resolution do not fit each other.)"


def predict_missing_out(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["mumps"] += 1
    propagate(sim, narrate=False)
    return {
        "at_home": hero.meters["at_home"] >= THRESHOLD,
        "cannot_attend": hero.meters["cannot_attend"] >= THRESHOLD,
        "disappointment": hero.memes["disappointment"],
    }


def introduce(world: World, hero: Entity, showcase: Showcase, role: RoleCfg, teacher: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["want_prominent"] += 1
    world.say(
        f"{hero.id} loved {showcase.label}, where small voices chimed in time. "
        f'"{showcase.chant}, {showcase.chant}," {hero.pronoun()} sang, a bright and bobbing rhyme.'
    )
    world.say(
        f"When {teacher.label_word.capitalize()} announced the {role.label}, "
        f"{hero.id}'s eyes grew round. It was a prominent place, {role.prominent_text}, "
        f"and {hero.pronoun()} wanted it very much."
    )


def ask_with_flattery(world: World, hero: Entity, friend: Entity, role: RoleCfg) -> None:
    hero.memes["used_flattery"] += 1
    hero.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f'So {hero.id} hurried to {friend.id} and poured out flattery in a sugary stream: '
        f'"You are the neatest, sweetest, brightest one I know. '
        f'Your step is light, your smile is bright, your {role.prop} would glow and glow!"'
    )
    world.say(
        f"But {friend.id} blinked. The words sounded polished, not quite true, "
        f"and the shiny wish inside them showed through."
    )


def decline(world: World, friend: Entity, hero: Entity) -> None:
    world.say(
        f'"I like kind words," said {friend.id}, "but kind words should be real. '
        f'Please ask me plain, not just to make a deal."'
    )
    hero.memes["shame"] += 1
    hero.memes["sadness"] += 1


def night_turn(world: World, hero: Entity, parent: Entity) -> None:
    hero.meters["mumps"] += 1
    hero.meters["swollen_cheeks"] += 1
    hero.meters["fever"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That night, the song went quiet. {hero.id}'s cheeks felt sore and plump, "
        f"and {parent.label_word} touched {hero.pronoun('possessive')} forehead with a worried thumb."
    )
    world.say(
        f'"Oh, duck," said {parent.label_word}, "you have mumps, so home is where you stay. '
        f"You must rest, sip, and skip the crowd until another day."
    )


def lament(world: World, hero: Entity, showcase: Showcase, role: RoleCfg) -> None:
    world.say(
        f'{hero.id} whispered, "{showcase.chant}, {showcase.chant}," but softly now, not bold. '
        f"The dream of the {role.label} felt far away and cold."
    )


def flashback(world: World, hero: Entity, friend: Entity, showcase: Showcase) -> None:
    hero.memes["remembering"] += 1
    world.say(
        "Then a flashback fluttered in, gentle as a paper kite. "
        f"{hero.id} remembered another day, another little light."
    )
    world.say(
        f"Back then, a rhyme sheet slid from {hero.pronoun('possessive')} hands and skated to the floor. "
        f"{friend.id} had picked it up, smoothed the page, and shared a line or more."
    )
    world.say(
        f"{friend.id} had not asked for praise. {friend.pronoun().capitalize()} had simply been kind. "
        f"That memory made the flattery taste sticky in {hero.id}'s mind."
    )
    hero.memes["understanding"] += 1
    hero.memes["vanity"] = 0.0


def apology(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["honest_apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} called {friend.id} and spoke in a plain, small way: "
        f'"I was trying to tug the bright part toward myself today."'
    )
    world.say(
        f'"I am sorry for the flattery. I should have said what was true: '
        f'I felt left out, and I was jealous, and I still care about you."'
    )


def comfort_and_plan(
    world: World,
    hero: Entity,
    friend: Entity,
    teacher: Entity,
    resolution: Resolution,
    showcase: Showcase,
    role: RoleCfg,
) -> None:
    world.facts["resolution_ready"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'"Thank you for telling the truth," said {friend.id}. "{friend.pronoun().capitalize()} can still have a part, even from bed."'
    )
    world.say(
        f"{teacher.label_word.capitalize()} agreed at once and {resolution.text}. "
        f"The plan could not cure the mumps, but it could keep the song from feeling shut away."
    )
    world.say(
        f'Soon {showcase.phrase} began, and {resolution.ending} '
        f'"{role.rhyme_line}" went the rhyme, and back came the rhyme, '
        f'"{role.rhyme_line}," one more time.'
    )


def tell(
    setting: Setting,
    showcase: Showcase,
    role: RoleCfg,
    resolution: Resolution,
    *,
    hero_name: str = "Pip",
    hero_type: str = "boy",
    friend_name: str = "Nell",
    friend_type: str = "girl",
    parent_type: str = "mother",
    teacher_type: str = "teacher_woman",
    trait: str = "eager",
) -> World:
    world = World(setting)
    world.facts["resolution_ready"] = 0.0

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"display_name": hero_name},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_type,
            label=friend_name,
            role="friend",
            traits=["steady"],
            attrs={"display_name": friend_name},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            attrs={},
        )
    )
    teacher = world.add(
        Entity(
            id="teacher",
            kind="character",
            type=teacher_type,
            label="the teacher",
            role="teacher",
            attrs={},
        )
    )

    hero.meters["mumps"] = 0.0
    hero.meters["swollen_cheeks"] = 0.0
    hero.meters["fever"] = 0.0
    hero.meters["at_home"] = 0.0
    hero.meters["cannot_attend"] = 0.0
    hero.memes["used_flattery"] = 0.0
    hero.memes["honest_apology"] = 0.0
    hero.memes["included"] = 0.0
    hero.memes["shame"] = 0.0
    hero.memes["sadness"] = 0.0
    hero.memes["gratitude"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["vanity"] = 0.0
    hero.memes["understanding"] = 0.0
    hero.memes["remembering"] = 0.0
    friend.memes["trust"] = 6.0
    friend.memes["uneasy"] = 0.0
    friend.memes["care"] = 0.0

    introduce(world, hero, showcase, role, teacher)
    world.para()
    ask_with_flattery(world, hero, friend, role)
    decline(world, friend, hero)

    world.para()
    pred = predict_missing_out(world)
    world.facts["predicted_miss"] = pred["cannot_attend"]
    night_turn(world, hero, parent)
    lament(world, hero, showcase, role)

    world.para()
    flashback(world, hero, friend, showcase)
    apology(world, hero, friend)
    comfort_and_plan(world, hero, friend, teacher, resolution, showcase, role)

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        teacher=teacher,
        setting=setting,
        showcase=showcase,
        role_cfg=role,
        resolution=resolution,
        missed_event=hero.meters["cannot_attend"] >= THRESHOLD,
        mumps=hero.meters["mumps"] >= THRESHOLD,
        apologised=hero.memes["honest_apology"] >= THRESHOLD,
        included=hero.memes["included"] >= THRESHOLD,
        trust_after=friend.memes["trust"],
    )
    return world


SETTINGS = {
    "street": Setting(
        id="street",
        place="the little street by the school",
        outdoor=True,
        pass_home=True,
        tags={"outdoor", "street"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the bright classroom",
        outdoor=False,
        pass_home=False,
        tags={"indoor", "room"},
    ),
    "garden": Setting(
        id="garden",
        place="the school garden",
        outdoor=True,
        pass_home=False,
        tags={"outdoor", "garden"},
    ),
}

SHOWCASES = {
    "parade": Showcase(
        id="parade",
        label="Rhyme Parade Day",
        chant="clap and tap, rhyme and rap",
        opening="the line of children looped down the lane",
        phrase="the parade line",
        roles={"banner_leader", "bell_ringer"},
        tags={"parade", "rhyme"},
    ),
    "recital": Showcase(
        id="recital",
        label="Rhyme Recital Morning",
        chant="chime time, rhyme time",
        opening="the chairs faced the little reading rug",
        phrase="the recital",
        roles={"bell_ringer", "crown_wearer"},
        tags={"recital", "rhyme"},
    ),
    "fair": Showcase(
        id="fair",
        label="Garden Rhyme Fair",
        chant="skip and sip, chip and chirp",
        opening="the bunting flickered over the flower beds",
        phrase="the garden fair",
        roles={"banner_leader", "crown_wearer"},
        tags={"fair", "rhyme"},
    ),
}

ROLES = {
    "banner_leader": RoleCfg(
        id="banner_leader",
        label="banner leader",
        prop="banner",
        prominent_text="right at the front where every ribbon could be seen",
        rhyme_line="Lead with care, and share the air",
        tags={"front", "banner"},
    ),
    "bell_ringer": RoleCfg(
        id="bell_ringer",
        label="bell ringer",
        prop="silver bell",
        prominent_text="near the middle where each bright ring told the group when to begin",
        rhyme_line="Ring it light, ring it bright",
        tags={"bell", "sound"},
    ),
    "crown_wearer": RoleCfg(
        id="crown_wearer",
        label="crown wearer",
        prop="paper crown",
        prominent_text="on the little stool where the gold paper shone above the rest",
        rhyme_line="Crown or no crown, kindness will not fall down",
        tags={"crown", "high"},
    ),
}

RESOLUTIONS = {
    "window_wave": Resolution(
        id="window_wave",
        label="window wave",
        needs_outdoor=True,
        needs_pass_home=True,
        text="promised that the children would pass slowly by the house so the rhyme could reach the open window",
        ending="the parade slowed under the window, and the children waved while the verse floated out to meet them.",
        qa_text="the parade passed the house so the child could join from the window",
        tags={"window", "outdoor"},
    ),
    "rhyme_card": Resolution(
        id="rhyme_card",
        label="rhyme card",
        text="hung a large card with the child's verse in a prominent place so everyone could speak it aloud together",
        ending="the class pointed to the card and read the missing child's verse together.",
        qa_text="the teacher hung the child's verse on a big card for everyone to read",
        tags={"card", "display"},
    ),
    "bulletin_star": Resolution(
        id="bulletin_star",
        label="bulletin star",
        needs_indoor=True,
        text="pinned the child's couplet on a golden star high on the classroom board where every eye could find it",
        ending="the golden star gleamed on the board, and the room spoke the verse in one warm breath.",
        qa_text="the teacher pinned the child's couplet on a golden star on the classroom board",
        tags={"board", "display", "indoor"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Lila", "Tess", "June", "Cora", "Pia", "Ruby"]
BOY_NAMES = ["Pip", "Milo", "Ben", "Toby", "Finn", "Ned", "Evan", "Leo"]
TRAITS = ["eager", "proud", "bouncy", "hopeful"]


@dataclass
class StoryParams:
    setting: str
    showcase: str
    role: str
    resolution: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    teacher: str
    trait: str
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
    "flattery": [
        (
            "What is flattery?",
            "Flattery is praise that is said mostly to get something. Kind words should be honest, not tricky."
        )
    ],
    "prominent": [
        (
            "What does prominent mean?",
            "Prominent means easy to notice or in an important place. In a parade or show, a prominent spot is one many people can see."
        )
    ],
    "mumps": [
        (
            "What are mumps?",
            "Mumps is an illness that can make cheeks swell and feel sore. A child with mumps needs rest and should stay home from a crowd."
        )
    ],
    "window": [
        (
            "Why can a window help someone join from home?",
            "An open window lets voices and waves travel between inside and outside. It can help someone who must stay home still feel included."
        )
    ],
    "display": [
        (
            "Why does hanging a rhyme on a card help?",
            "A large card lets everyone see the words together. It gives the missing child a real part in the celebration."
        )
    ],
    "apology": [
        (
            "Why does an honest apology help friendship?",
            "An honest apology tells the truth about what went wrong. That helps trust grow again because the other person feels respected."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like bright and light. Rhymes can make a chant easy to remember."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story pauses to remember something from before. It can help a character understand what to do next."
        )
    ],
}
KNOWLEDGE_ORDER = ["flattery", "prominent", "mumps", "window", "display", "apology", "rhyme", "flashback"]


CURATED = [
    StoryParams(
        setting="street",
        showcase="parade",
        role="banner_leader",
        resolution="window_wave",
        hero_name="Pip",
        hero_gender="boy",
        friend_name="Nell",
        friend_gender="girl",
        parent="mother",
        teacher="teacher_woman",
        trait="eager",
    ),
    StoryParams(
        setting="classroom",
        showcase="recital",
        role="crown_wearer",
        resolution="bulletin_star",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="father",
        teacher="teacher_man",
        trait="proud",
    ),
    StoryParams(
        setting="garden",
        showcase="fair",
        role="banner_leader",
        resolution="rhyme_card",
        hero_name="Toby",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        parent="mother",
        teacher="teacher_woman",
        trait="hopeful",
    ),
    StoryParams(
        setting="classroom",
        showcase="recital",
        role="bell_ringer",
        resolution="rhyme_card",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="father",
        teacher="teacher_man",
        trait="bouncy",
    ),
    StoryParams(
        setting="street",
        showcase="parade",
        role="bell_ringer",
        resolution="rhyme_card",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        parent="mother",
        teacher="teacher_woman",
        trait="eager",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    showcase = f["showcase"]
    role = f["role_cfg"]
    resolution = f["resolution"]
    return [
        (
            'Write a short rhyming story for a 3-to-5-year-old that includes the words '
            '"flattery," "prominent," and "mumps," and uses a flashback.'
        ),
        (
            f"Tell a gentle story where {hero.label} wants the prominent role of {role.label} "
            f"at {showcase.label}, uses flattery, then has mumps and must stay home."
        ),
        (
            f"Write a rhyming story with repetition where a child learns that honest words are "
            f"better than flattery, and the ending uses {resolution.label} to include the child."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    teacher = f["teacher"]
    showcase = f["showcase"]
    role = f["role_cfg"]
    resolution = f["resolution"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who wanted the {role.label} at {showcase.label}. "
            f"It is also about {friend.label}, {parent.label_word}, and {teacher.label_word}, who helped the child learn a kinder way."
        ),
        (
            f"Why did {hero.label} use flattery?",
            f"{hero.label} wanted the {role.label}, which felt like a prominent place in the celebration. "
            f"The sweet words were meant to pull that bright part closer, not just to tell the truth."
        ),
        (
            f"Why could {hero.label} not go to {showcase.label}?",
            f"{hero.label} woke up with mumps, with sore swollen cheeks, so {parent.label_word} said {hero.pronoun('subject')} had to stay home and rest. "
            f"That illness changed the plan because crowds were no longer safe for {hero.pronoun('object')}."
        ),
        (
            "What happened in the flashback, and why did it matter?",
            f"In the flashback, {hero.label} remembered that {friend.label} had kindly helped with a dropped rhyme sheet on an earlier day. "
            f"That memory showed the difference between true kindness and flattery, so it pushed {hero.label} toward an honest apology."
        ),
        (
            f"How was the problem solved?",
            f"{teacher.label_word.capitalize()} and {friend.label} used {resolution.label}. "
            f"{resolution.qa_text.capitalize()}, so {hero.label} still had a real place in the rhyme even while resting at home."
        ),
        (
            f"How did {hero.label} change by the end?",
            f"{hero.label} began the story wanting a bright part for selfish reasons. "
            f"By the end, {hero.pronoun('subject')} cared more about truthful words and shared joy, and that made the ending feel warm instead of lonely."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"flattery", "prominent", "mumps", "apology", "rhyme", "flashback"}
    resolution = world.facts["resolution"]
    if "window" in resolution.tags:
        tags.add("window")
    if "display" in resolution.tags or "board" in resolution.tags:
        tags.add("display")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_role(SH,R) :- showcase(SH), role(R), allowed_role(SH,R).

fits_resolution(ST,RS) :- setting(ST), resolution(RS),
                          not need_outdoor(RS).
fits_resolution(ST,RS) :- setting(ST), resolution(RS),
                          need_outdoor(RS), outdoor(ST),
                          not need_pass_home(RS).
fits_resolution(ST,RS) :- setting(ST), resolution(RS),
                          need_outdoor(RS), outdoor(ST),
                          need_pass_home(RS), pass_home(ST).
fits_resolution(ST,RS) :- setting(ST), resolution(RS),
                          need_indoor(RS), indoor(ST).

valid(ST,SH,R,RS) :- fits_role(SH,R), fits_resolution(ST,RS).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.outdoor:
            lines.append(asp.fact("outdoor", setting_id))
        else:
            lines.append(asp.fact("indoor", setting_id))
        if setting.pass_home:
            lines.append(asp.fact("pass_home", setting_id))
    for showcase_id, showcase in SHOWCASES.items():
        lines.append(asp.fact("showcase", showcase_id))
        for role_id in sorted(showcase.roles):
            lines.append(asp.fact("allowed_role", showcase_id, role_id))
    for role_id in ROLES:
        lines.append(asp.fact("role", role_id))
    for resolution_id, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", resolution_id))
        if resolution.needs_outdoor:
            lines.append(asp.fact("need_outdoor", resolution_id))
        if resolution.needs_indoor:
            lines.append(asp.fact("need_indoor", resolution_id))
        if resolution.needs_pass_home:
            lines.append(asp.fact("need_pass_home", resolution_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


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
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    rng = random.Random(17)
    args = build_parser().parse_args([])
    try:
        params = resolve_params(args, rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated empty default story in verify test.")
        print("OK: default resolve/generate succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: flattery, a prominent role, mumps, and a flashback."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--showcase", choices=SHOWCASES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--teacher", choices=["teacher_woman", "teacher_man"])
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.showcase and args.role:
        showcase = SHOWCASES[args.showcase]
        role = ROLES[args.role]
        if not role_fits(showcase, role):
            raise StoryError(explain_role(showcase, role))
    if args.setting and args.resolution:
        setting = SETTINGS[args.setting]
        resolution = RESOLUTIONS[args.resolution]
        if not resolution_fits(setting, resolution):
            raise StoryError(explain_resolution(setting, resolution))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.showcase is None or combo[1] == args.showcase)
        and (args.role is None or combo[2] == args.role)
        and (args.resolution is None or combo[3] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, showcase_id, role_id, resolution_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    teacher = args.teacher or rng.choice(["teacher_woman", "teacher_man"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        showcase=showcase_id,
        role=role_id,
        resolution=resolution_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        teacher=teacher,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        showcase = SHOWCASES[params.showcase]
        role = ROLES[params.role]
        resolution = RESOLUTIONS[params.resolution]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not role_fits(showcase, role):
        raise StoryError(explain_role(showcase, role))
    if not resolution_fits(setting, resolution):
        raise StoryError(explain_resolution(setting, resolution))

    world = tell(
        setting,
        showcase,
        role,
        resolution,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        parent_type=params.parent,
        teacher_type=params.teacher,
        trait=params.trait,
    )

    story = world.render().replace("hero", params.hero_name).replace("friend", params.friend_name)

    story = story.replace("hero", params.hero_name)
    story = story.replace("friend", params.friend_name)
    story = story.replace("parent", "parent")
    story = story.replace("teacher", "teacher")

    hero_label = params.hero_name
    friend_label = params.friend_name
    story = story.replace("hero", hero_label).replace("friend", friend_label)

    # Replace entity labels that were stored separately from ids.
    story = story.replace("hero", hero_label).replace("friend", friend_label)
    story = story.replace("the parent", {"mother": "mom", "father": "dad"}[params.parent])
    story = story.replace("the teacher", "teacher")

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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, showcase, role, resolution) combos:\n")
        for setting_id, showcase_id, role_id, resolution_id in combos:
            print(f"  {setting_id:10} {showcase_id:8} {role_id:14} {resolution_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.showcase} / {p.role} / {p.resolution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
