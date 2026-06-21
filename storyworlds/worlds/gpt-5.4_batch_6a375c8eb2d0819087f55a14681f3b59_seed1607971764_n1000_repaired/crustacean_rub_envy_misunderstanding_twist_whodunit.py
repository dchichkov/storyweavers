#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py
=================================================================================

A standalone storyworld for a gentle child-facing whodunit:
someone seems to have spoiled a shiny parade prize, one child had a clear reason
for envy, and a quick accusation grows from a misunderstanding. The twist is
that the "culprit" really did rub the prize, but only to help after a little
crustacean caused the mess.

Run it
------
    python storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py
    python storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py --prize brass_badge --spill jam --cleaner damp_cloth
    python storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py --spill paint --cleaner dry_sleeve
    python storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crustacean_rub_envy_misunderstanding_twist_whodunit.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    display: str
    snack: str
    water: str
    affords: set[str] = field(default_factory=set)
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
class Mascot:
    id: str
    label: str
    phrase: str
    track_word: str
    motion: str
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
class Prize:
    id: str
    label: str
    phrase: str
    material: str
    gleam: str
    role_text: str
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
class Spill:
    id: str
    label: str
    phrase: str
    clue: str
    smell: str
    source_line: str
    messy: str
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
class Cleaner:
    id: str
    label: str
    phrase: str
    action: str
    suited_materials: set[str] = field(default_factory=set)
    risky_materials: set[str] = field(default_factory=set)
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
class StoryParams:
    setting: str
    mascot: str
    prize: str
    spill: str
    cleaner: str
    detective: str
    detective_gender: str
    suspect: str
    suspect_gender: str
    winner: str
    winner_gender: str
    adult: str
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


def _r_smear_from_mascot(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    mascot = world.get("mascot")
    if mascot.meters["through_spill"] < THRESHOLD:
        return out
    if prize.meters["smudged"] >= THRESHOLD:
        return out
    sig = ("smear_from_mascot",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["smudged"] += 1
    prize.attrs["clue_visible"] = True
    out.append("__smudge__")
    return out


def _r_wrong_rub_clouds(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    suspect = world.get("suspect")
    if prize.meters["smudged"] < THRESHOLD:
        return out
    if suspect.meters["rub_attempt"] < THRESHOLD:
        return out
    if world.facts.get("cleaner_ok", False):
        return out
    sig = ("wrong_rub_clouds",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["cloudy"] += 1
    out.append("__cloud__")
    return out


def _r_right_rub_lifts_smudge(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    suspect = world.get("suspect")
    if prize.meters["smudged"] < THRESHOLD:
        return out
    if suspect.meters["rub_attempt"] < THRESHOLD:
        return out
    if not world.facts.get("cleaner_ok", False):
        return out
    sig = ("right_rub_lifts",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["smudged"] = 0.0
    prize.meters["shine"] += 1
    out.append("__helped__")
    return out


def _r_envy_feeds_suspicion(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    prize = world.get("prize")
    if suspect.memes["envy"] < THRESHOLD:
        return out
    if prize.meters["cloudy"] < THRESHOLD and prize.meters["smudged"] < THRESHOLD:
        return out
    sig = ("envy_feeds_suspicion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] += 1
    suspect.memes["hurt"] += 1
    out.append("__suspect__")
    return out


def _r_clue_clears_blame(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    prize = world.get("prize")
    if detective.memes["suspicion"] < THRESHOLD:
        return out
    if not prize.attrs.get("clue_visible"):
        return out
    if not world.facts.get("truth_told", False):
        return out
    sig = ("clue_clears_blame",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] = 0.0
    detective.memes["remorse"] += 1
    suspect.memes["relief"] += 1
    out.append("__cleared__")
    return out


CAUSAL_RULES = [
    Rule(name="smear_from_mascot", tag="physical", apply=_r_smear_from_mascot),
    Rule(name="wrong_rub_clouds", tag="physical", apply=_r_wrong_rub_clouds),
    Rule(name="right_rub_lifts_smudge", tag="physical", apply=_r_right_rub_lifts_smudge),
    Rule(name="envy_feeds_suspicion", tag="social", apply=_r_envy_feeds_suspicion),
    Rule(name="clue_clears_blame", tag="social", apply=_r_clue_clears_blame),
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


SETTINGS = {
    "pier_shed": Setting(
        id="pier_shed",
        place="the little pier shed",
        display="a blue table under paper fish",
        snack="strawberry jam sandwiches",
        water="a pail of clean harbor water",
        affords={"crab", "lobster"},
    ),
    "tidepool_room": Setting(
        id="tidepool_room",
        place="the tide-pool room at the nature center",
        display="a low table beside the touch tank",
        snack="blueberry buns",
        water="a bowl of fresh rinse water",
        affords={"crab", "shrimp"},
    ),
    "beach_tent": Setting(
        id="beach_tent",
        place="the striped beach tent",
        display="a driftwood stand by the flap",
        snack="raspberry cakes",
        water="a tin cup of clean water",
        affords={"crab", "shrimp"},
    ),
}

MASCOTS = {
    "crab": Mascot(
        id="crab",
        label="crab",
        phrase="a little crab, a cheerful crustacean with sideways feet",
        track_word="tiny claw dots",
        motion="scuttled sideways",
        tags={"crustacean", "clue"},
    ),
    "lobster": Mascot(
        id="lobster",
        label="lobster",
        phrase="a baby lobster, a careful crustacean with bright eyes",
        track_word="small tail flick marks",
        motion="wiggled and clicked",
        tags={"crustacean", "clue"},
    ),
    "shrimp": Mascot(
        id="shrimp",
        label="shrimp",
        phrase="a glassy shrimp, a quick little crustacean",
        track_word="tiny wet hops",
        motion="flicked in quick hops",
        tags={"crustacean", "clue"},
    ),
}

PRIZES = {
    "shell_crown": Prize(
        id="shell_crown",
        label="shell crown",
        phrase="a shell crown looped with ribbon",
        material="shell",
        gleam="pearled in the light",
        role_text="wear the shell crown at the front of the parade",
        tags={"shell", "parade"},
    ),
    "brass_badge": Prize(
        id="brass_badge",
        label="brass badge",
        phrase="a brass crab badge on a velvet pad",
        material="brass",
        gleam="glowed like a tiny sun",
        role_text="pin the brass badge on the parade banner",
        tags={"brass", "parade"},
    ),
    "pearl_sign": Prize(
        id="pearl_sign",
        label="pearl sign",
        phrase="a pearl-painted sign that said CRUSTACEAN CLUB",
        material="painted",
        gleam="shone with milky swirls",
        role_text="carry the pearl sign into the parade",
        tags={"painted", "parade"},
    ),
}

SPILLS = {
    "jam": Spill(
        id="jam",
        label="jam",
        phrase="a sticky ribbon of berry jam",
        clue="a sweet red smear",
        smell="sweet berries",
        source_line="A fallen snack had left a sticky ribbon of jam near the display.",
        messy="sticky",
        tags={"jam", "sticky"},
    ),
    "paint": Spill(
        id="paint",
        label="paint",
        phrase="a dab of blue poster paint",
        clue="a bright blue streak",
        smell="chalky paint",
        source_line="Someone had left a dab of blue poster paint open beside the display cards.",
        messy="painty",
        tags={"paint", "art"},
    ),
    "sea_mud": Spill(
        id="sea_mud",
        label="sea mud",
        phrase="a splash of gray sea mud",
        clue="a gray-green smear",
        smell="salty mud",
        source_line="A drip of sea mud had slid from a bucket onto the edge of the display.",
        messy="muddy",
        tags={"mud", "sticky"},
    ),
}

CLEANERS = {
    "damp_cloth": Cleaner(
        id="damp_cloth",
        label="damp cloth",
        phrase="a soft damp cloth",
        action="gently rubbed the mark with a soft damp cloth",
        suited_materials={"shell", "brass"},
        risky_materials={"painted"},
        tags={"cleaning", "cloth"},
    ),
    "dry_sleeve": Cleaner(
        id="dry_sleeve",
        label="dry sleeve",
        phrase="a dry sleeve",
        action="rubbed at the mark with a dry sleeve in a hurry",
        suited_materials=set(),
        risky_materials={"shell", "brass", "painted"},
        tags={"cleaning", "mistake"},
    ),
    "soft_brush": Cleaner(
        id="soft_brush",
        label="soft brush",
        phrase="a soft brush",
        action="brushed the mark away with a soft brush",
        suited_materials={"painted"},
        risky_materials={"shell"},
        tags={"cleaning", "brush"},
    ),
}

GIRL_NAMES = ["Mira", "Tess", "Lina", "Ruby", "June", "Nora", "Esme", "Ava"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Eli", "Finn", "Noah", "Sam"]


def cleaner_works(prize: Prize, cleaner: Cleaner) -> bool:
    return prize.material in cleaner.suited_materials


def risky_cleaner(prize: Prize, cleaner: Cleaner) -> bool:
    return prize.material in cleaner.risky_materials


def mascot_fits(setting: Setting, mascot: Mascot) -> bool:
    return mascot.id in setting.affords


def valid_combo(setting: Setting, mascot: Mascot, prize: Prize, spill: Spill, cleaner: Cleaner) -> bool:
    del spill
    return mascot_fits(setting, mascot) and cleaner_works(prize, cleaner)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, mascot in MASCOTS.items():
            if not mascot_fits(setting, mascot):
                continue
            for pid, prize in PRIZES.items():
                for spid, spill in SPILLS.items():
                    for cid, cleaner in CLEANERS.items():
                        if valid_combo(setting, mascot, prize, spill, cleaner):
                            combos.append((sid, mid, pid, spid, cid))
    return combos


def explain_rejection(setting: Setting, mascot: Mascot, prize: Prize, cleaner: Cleaner) -> str:
    if not mascot_fits(setting, mascot):
        return (
            f"(No story: {setting.place} is not set up for a {mascot.label} mascot, "
            f"so that crustacean would not be there to leave the clue.)"
        )
    if risky_cleaner(prize, cleaner):
        return (
            f"(No story: {cleaner.phrase} is a poor way to clean a {prize.label}. "
            f"A good misunderstanding twist still needs a believable happy ending, "
            f"so pick a gentler cleaner for {prize.material}.)"
        )
    return (
        f"(No story: {cleaner.phrase} does not sensibly clean a {prize.label}. "
        f"Pick a cleaner that fits {prize.material}.)"
    )


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def choose_roles(world: World, detective: Entity, suspect: Entity, winner: Entity, prize: Prize) -> None:
    winner.memes["pride"] += 1
    suspect.memes["envy"] += 1
    world.say(
        f"On parade morning in {world.setting.place}, the children of the Crustacean Club "
        f"set out {prize.phrase} on {world.setting.display}. It {prize.gleam}."
    )
    world.say(
        f"{winner.id} was chosen to {prize.role_text}. {suspect.id} smiled as hard as {suspect.pronoun()} could, "
        f"but a small pinch of envy sat in {suspect.pronoun('possessive')} chest because {suspect.pronoun()} had wanted that turn."
    )
    world.say(
        f"{detective.id}, who loved little mysteries, decided to keep an eye on everything."
    )


def mascot_escape(world: World, mascot: Mascot, spill: Spill) -> None:
    m = world.get("mascot")
    world.say(
        f"Then the club mascot, {mascot.phrase}, {mascot.motion} out of its tank for one surprising moment."
    )
    world.say(spill.source_line)
    m.meters["through_spill"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the children turned back, there was {spill.clue} on the prize."
    )


def suspect_tries_to_help(world: World, suspect: Entity, cleaner: Cleaner) -> None:
    suspect.meters["rub_attempt"] += 1
    world.say(
        f"{suspect.id} gasped, grabbed {cleaner.phrase}, and {cleaner.action}."
    )
    propagate(world, narrate=False)


def accusation(world: World, detective: Entity, suspect: Entity, spill: Spill, cleaner: Cleaner) -> None:
    prize = world.get("prize")
    if prize.meters["cloudy"] >= THRESHOLD:
        damage = "The shine went dull in one spot"
    else:
        damage = "The mark looked smaller, but it was still there"
    world.say(
        f"{damage}. {detective.id} saw {suspect.id} beside the display with {cleaner.phrase} and remembered that pinch of envy."
    )
    propagate(world, narrate=False)
    if detective.memes["suspicion"] >= THRESHOLD:
        world.say(
            f'"I know who did it," whispered {detective.id}. "It was {suspect.id}. {suspect.pronoun().capitalize()} was jealous and tried to spoil it."'
        )
        world.say(
            f"{suspect.id}'s face fell. {suspect.pronoun().capitalize()} opened {suspect.pronoun('possessive')} mouth, then closed it again."
        )


def investigate(world: World, detective: Entity, suspect: Entity, mascot: Mascot, spill: Spill) -> None:
    prize = world.get("prize")
    adult = world.get("adult")
    world.say(
        f"{adult.label_word.capitalize()} knelt by the display instead of scolding anyone."
    )
    world.say(
        f'{adult.pronoun().capitalize()} pointed to {mascot.track_word} leading across the table. "A clue first," {adult.pronoun()} said.'
    )
    smell = spill.smell
    if prize.attrs.get("clue_visible"):
        world.say(
            f"There was the smell of {smell}, and the tiny trail led from the spill to the prize, not from {suspect.id}'s hands."
        )
    world.facts["truth_told"] = True
    world.say(
        f'"I did rub it," {suspect.id} said quickly, "but only because I saw the mess and wanted to clean it before {winner_name(world)} had to carry it."'
    )
    propagate(world, narrate=False)
    if detective.memes["remorse"] >= THRESHOLD:
        world.say(
            f"{detective.id} felt heat rush into {detective.pronoun('possessive')} cheeks. The mystery had not been envy making trouble. It had been envy making the wrong guess."
        )


def winner_name(world: World) -> str:
    return world.get("winner").id


def restore_and_resolve(world: World, prize_cfg: Prize, cleaner: Cleaner, spill: Spill) -> None:
    adult = world.get("adult")
    detective = world.get("detective")
    suspect = world.get("suspect")
    winner = world.get("winner")
    prize = world.get("prize")

    prize.meters["smudged"] = 0.0
    prize.meters["cloudy"] = 0.0
    prize.meters["shine"] += 1
    suspect.memes["relief"] += 1
    detective.memes["relief"] += 1
    winner.memes["kindness"] += 1

    tool = "a fresh careful cloth" if cleaner.id != "soft_brush" else "the soft brush and a steady hand"
    world.say(
        f"{adult.label_word.capitalize()} used {tool} and cleaned the last of the {spill.label} away until the {prize_cfg.label} shone again."
    )
    world.say(
        f'"I am sorry," said {detective.id}. "I saw the envy on your face, {suspect.id}, and I thought it meant you had done something mean."'
    )
    world.say(
        f'"I was envious," {suspect.id} admitted, "but I still wanted it to look beautiful."'
    )
    world.say(
        f"Then {winner.id} moved over and patted the place beside {winner.pronoun('object')}. "
        f'"Help me carry it," {winner.pronoun()} said. "Mysteries are better when we solve them together."'
    )
    world.say(
        f"So the parade began with the little crustacean safe in its tank, the {prize_cfg.label} bright once more, and three children walking side by side instead of peering at one another with doubt."
    )


def tell(
    setting: Setting,
    mascot_cfg: Mascot,
    prize_cfg: Prize,
    spill_cfg: Spill,
    cleaner_cfg: Cleaner,
    detective_name: str = "Mira",
    detective_gender: str = "girl",
    suspect_name: str = "Ben",
    suspect_gender: str = "boy",
    winner_name_value: str = "Lina",
    winner_gender: str = "girl",
    adult_type: str = "mother",
) -> World:
    world = World(setting)
    world.facts["cleaner_ok"] = cleaner_works(prize_cfg, cleaner_cfg)
    world.facts["truth_told"] = False

    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    suspect = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect"))
    winner = world.add(Entity(id=winner_name_value, kind="character", type=winner_gender, role="winner"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    mascot = world.add(Entity(id="mascot", kind="thing", type=mascot_cfg.label, role="mascot", label=mascot_cfg.label))
    prize = world.add(
        Entity(
            id="prize",
            kind="thing",
            type=prize_cfg.material,
            role="prize",
            label=prize_cfg.label,
            attrs={"clue_visible": False},
        )
    )
    prize.meters["shine"] = 1.0

    choose_roles(world, detective, suspect, winner, prize_cfg)
    world.para()
    mascot_escape(world, mascot_cfg, spill_cfg)
    suspect_tries_to_help(world, suspect, cleaner_cfg)
    accusation(world, detective, suspect, spill_cfg, cleaner_cfg)
    world.para()
    investigate(world, detective, suspect, mascot_cfg, spill_cfg)
    restore_and_resolve(world, prize_cfg, cleaner_cfg, spill_cfg)

    world.facts.update(
        setting=setting,
        mascot_cfg=mascot_cfg,
        prize_cfg=prize_cfg,
        spill_cfg=spill_cfg,
        cleaner_cfg=cleaner_cfg,
        detective=detective,
        suspect=suspect,
        winner=winner,
        adult=adult,
        prize=prize,
        misunderstanding=detective.memes["remorse"] >= THRESHOLD,
        restored=prize.meters["shine"] >= THRESHOLD and prize.meters["cloudy"] < THRESHOLD,
        envy=suspect.memes["envy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "crustacean": [
        (
            "What is a crustacean?",
            "A crustacean is an animal with a hard outer covering, like a crab, lobster, or shrimp. Many crustaceans live in the sea or near water."
        )
    ],
    "jam": [
        (
            "Why is jam sticky?",
            "Jam is made from fruit and sugar cooked together, so it clings to things. That is why a jam smear can leave a sticky mark."
        )
    ],
    "paint": [
        (
            "Why should wet paint be left alone for a moment?",
            "Wet paint smears easily when you touch it. If you rub it too fast, the mark usually gets bigger instead of smaller."
        )
    ],
    "mud": [
        (
            "What is sea mud?",
            "Sea mud is soft muddy stuff from the shore or the bottom of shallow water. It can leave gray or green smears when it splashes."
        )
    ],
    "cloth": [
        (
            "Why can a soft cloth help clean something shiny?",
            "A soft cloth can lift dirt without scratching. Gentle cleaning is better for shiny things than rough rubbing."
        )
    ],
    "brush": [
        (
            "What is a soft brush good for?",
            "A soft brush can sweep loose dust or dry bits away. It helps when something is delicate and should not be wiped hard."
        )
    ],
    "envy": [
        (
            "What is envy?",
            "Envy is the feeling you get when someone else has a turn or a thing you wanted. It is a feeling, but it does not have to decide what you do next."
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you understand what really happened. Good detectives look for clues before they blame someone."
        )
    ],
}
KNOWLEDGE_ORDER = ["crustacean", "clue", "envy", "jam", "paint", "mud", "cloth", "brush"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    mascot = f["mascot_cfg"]
    prize = f["prize_cfg"]
    spill = f["spill_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that uses the words "crustacean", "rub", and "envy".',
        f"Tell a mystery where {detective.id} sees a shiny {prize.label} marked with {spill.clue} and wrongly suspects {suspect.id}, even though the real clue comes from a little {mascot.label}.",
        f"Write a story with a misunderstanding and a twist: a child seems to have spoiled a parade prize, but the truth is that {suspect.id} tried to rub the mess away and was only trying to help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    suspect = f["suspect"]
    winner = f["winner"]
    adult = f["adult"]
    mascot = f["mascot_cfg"]
    prize = f["prize_cfg"]
    spill = f["spill_cfg"]
    cleaner = f["cleaner_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, who tries to solve a little mystery, {suspect.id}, who is misunderstood, and {winner.id}, who was meant to carry the {prize.label} in the parade."
        ),
        (
            f"Why did {suspect.id} feel envy at first?",
            f"{suspect.id} felt envy because {winner.id} was chosen to {prize.role_text}. {suspect.pronoun().capitalize()} wanted that special turn too, even though {suspect.pronoun()} tried to hide the feeling."
        ),
        (
            f"What made {detective.id} think {suspect.id} was guilty?",
            f"{detective.id} saw that {suspect.id} had been envious, and then saw {suspect.pronoun('object')} beside the prize with {cleaner.phrase}. That made the wrong idea feel true before {detective.id} had checked the clues."
        ),
        (
            "What was the twist in the mystery?",
            f"The twist was that {suspect.id} really had touched the prize, but not to spoil it. {suspect.pronoun().capitalize()} gave it a rub because the little {mascot.label}, a crustacean, had carried {spill.label} onto it and {suspect.pronoun()} wanted to help."
        ),
        (
            f"How did they learn the truth?",
            f"{adult.label_word.capitalize()} noticed {mascot.track_word} and the smell of {spill.smell}. Those clues showed that the mess had come from the mascot's path, not from a mean trick."
        ),
        (
            "How did the story end?",
            f"{adult.label_word.capitalize()} cleaned the prize properly until it shone again, and {detective.id} apologized. Then {winner.id} invited {suspect.id} to help carry it, which proved the misunderstanding was over."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"crustacean", "clue", "envy"}
    spill = f["spill_cfg"]
    cleaner = f["cleaner_cfg"]
    if spill.id == "jam":
        tags.add("jam")
    elif spill.id == "paint":
        tags.add("paint")
    else:
        tags.add("mud")
    if cleaner.id == "soft_brush":
        tags.add("brush")
    else:
        tags.add("cloth")

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


CURATED = [
    StoryParams(
        setting="pier_shed",
        mascot="crab",
        prize="brass_badge",
        spill="jam",
        cleaner="damp_cloth",
        detective="Mira",
        detective_gender="girl",
        suspect="Ben",
        suspect_gender="boy",
        winner="Lina",
        winner_gender="girl",
        adult="mother",
    ),
    StoryParams(
        setting="tidepool_room",
        mascot="shrimp",
        prize="pearl_sign",
        spill="paint",
        cleaner="soft_brush",
        detective="Theo",
        detective_gender="boy",
        suspect="Ruby",
        suspect_gender="girl",
        winner="Nora",
        winner_gender="girl",
        adult="father",
    ),
    StoryParams(
        setting="pier_shed",
        mascot="lobster",
        prize="shell_crown",
        spill="sea_mud",
        cleaner="damp_cloth",
        detective="Ava",
        detective_gender="girl",
        suspect="Finn",
        suspect_gender="boy",
        winner="June",
        winner_gender="girl",
        adult="uncle",
    ),
    StoryParams(
        setting="beach_tent",
        mascot="crab",
        prize="pearl_sign",
        spill="paint",
        cleaner="soft_brush",
        detective="Esme",
        detective_gender="girl",
        suspect="Max",
        suspect_gender="boy",
        winner="Tess",
        winner_gender="girl",
        adult="aunt",
    ),
]


ASP_RULES = r"""
fits_mascot(S, M) :- affords(S, M).
works(P, C) :- prize(P), cleaner(C), material(P, Mat), suits(C, Mat).
valid(S, M, P, Sp, C) :- setting(S), mascot(M), prize(P), spill(Sp), cleaner(C),
                         fits_mascot(S, M), works(P, C).
#show valid/5.
#show works/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for mid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, mid))
    for mid in MASCOTS:
        lines.append(asp.fact("mascot", mid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("material", pid, prize.material))
    for spid in SPILLS:
        lines.append(asp.fact("spill", spid))
    for cid, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cid))
        for mat in sorted(cleaner.suited_materials):
            lines.append(asp.fact("suits", cid, mat))
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
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle whodunit storyworld: a shiny parade prize, a misleading clue, envy, and a misunderstanding with a twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mascot", choices=MASCOTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mascot:
        setting = SETTINGS[args.setting]
        mascot = MASCOTS[args.mascot]
        if not mascot_fits(setting, mascot):
            prize = PRIZES[args.prize] if args.prize else next(iter(PRIZES.values()))
            cleaner = CLEANERS[args.cleaner] if args.cleaner else next(iter(CLEANERS.values()))
            raise StoryError(explain_rejection(setting, mascot, prize, cleaner))

    if args.prize and args.cleaner:
        prize = PRIZES[args.prize]
        cleaner = CLEANERS[args.cleaner]
        setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        mascot = MASCOTS[args.mascot] if args.mascot else MASCOTS[next(iter(setting.affords))]
        if not valid_combo(setting, mascot, prize, SPILLS[args.spill] if args.spill else next(iter(SPILLS.values())), cleaner):
            raise StoryError(explain_rejection(setting, mascot, prize, cleaner))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.mascot is None or c[1] == args.mascot)
        and (args.prize is None or c[2] == args.prize)
        and (args.spill is None or c[3] == args.spill)
        and (args.cleaner is None or c[4] == args.cleaner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mascot_id, prize_id, spill_id, cleaner_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    suspect_gender = rng.choice(["girl", "boy"])
    winner_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    detective = pick_name(rng, detective_gender, used)
    used.add(detective)
    suspect = pick_name(rng, suspect_gender, used)
    used.add(suspect)
    winner = pick_name(rng, winner_gender, used)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])

    return StoryParams(
        setting=setting_id,
        mascot=mascot_id,
        prize=prize_id,
        spill=spill_id,
        cleaner=cleaner_id,
        detective=detective,
        detective_gender=detective_gender,
        suspect=suspect,
        suspect_gender=suspect_gender,
        winner=winner,
        winner_gender=winner_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mascot = MASCOTS[params.mascot]
        prize = PRIZES[params.prize]
        spill = SPILLS[params.spill]
        cleaner = CLEANERS[params.cleaner]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]} is not in this storyworld.)") from None

    if not valid_combo(setting, mascot, prize, spill, cleaner):
        raise StoryError(explain_rejection(setting, mascot, prize, cleaner))

    world = tell(
        setting=setting,
        mascot_cfg=mascot,
        prize_cfg=prize,
        spill_cfg=spill,
        cleaner_cfg=cleaner,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        suspect_name=params.suspect,
        suspect_gender=params.suspect_gender,
        winner_name_value=params.winner,
        winner_gender=params.winner_gender,
        adult_type=params.adult,
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
        print(f"{len(combos)} compatible (setting, mascot, prize, spill, cleaner) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
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
            header = f"### {p.detective}: {p.mascot} / {p.prize} / {p.spill} / {p.cleaner}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
