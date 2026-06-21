#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/parliament_calendar_tuvwx_teamwork_fairy_tale.py
============================================================================

A standalone story world about a tiny fairy-tale parliament that must change a
great hall calendar before a feast begins. The turning point is always about
teamwork: one small helper tries to solve a problem alone, the hall wobbles with
danger, and the right two-person method restores order.

Run it
------
    python storyworlds/worlds/gpt-5.4/parliament_calendar_tuvwx_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/parliament_calendar_tuvwx_teamwork_fairy_tale.py --snag wind_flap --method dew_cloth
    python storyworlds/worlds/gpt-5.4/parliament_calendar_tuvwx_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/parliament_calendar_tuvwx_teamwork_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/parliament_calendar_tuvwx_teamwork_fairy_tale.py --verify
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
        female = {"girl", "fairy_girl", "queen", "mother", "woman"}
        male = {"boy", "fairy_boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")
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
class Chamber:
    id: str
    label: str
    scene: str
    detail: str
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
class Festival:
    id: str
    title: str
    page_name: str
    cheer: str
    ending_image: str
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
class Snag:
    id: str
    label: str
    problem_text: str
    warning_text: str
    solo_trouble: str
    solve_need: str
    risk: int
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
class Method:
    id: str
    label: str
    solve_types: set[str]
    setup_text: str
    action_text: str
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
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
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
        clone = World(self.chamber)
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    partner = world.get("partner")
    if hero.meters["off_balance"] >= THRESHOLD:
        sig = ("wobble", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("stool").meters["wobble"] += 1
            hero.memes["fear"] += 1
            partner.memes["fear"] += 1
            out.append("__wobble__")
    return out


def _r_restore(world: World) -> list[str]:
    out: list[str] = []
    calendar = world.get("calendar")
    if calendar.meters["turned"] >= THRESHOLD:
        sig = ("restore", "calendar")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hall").meters["order"] += 1
            for eid in ("hero", "partner", "speaker"):
                world.get(eid).memes["relief"] += 1
                world.get(eid).memes["joy"] += 1
            out.append("__restore__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="risk", apply=_r_wobble),
    Rule(name="restore", tag="resolution", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CHAMBERS = {
    "acorn": Chamber(
        id="acorn",
        label="the Acorn Parliament",
        scene="deep in the roots of an old oak",
        detail="Amber lamps glowed on polished nut-wood benches, and a moon-round table shone at the center.",
        tags={"parliament"},
    ),
    "lily": Chamber(
        id="lily",
        label="the Lily Parliament",
        scene="inside a ring of giant lily cups",
        detail="Pearl drops trembled on the green walls, and the silver seats looked as if they had grown from the pond itself.",
        tags={"parliament"},
    ),
    "crystal": Chamber(
        id="crystal",
        label="the Crystal Parliament",
        scene="under a hill of blue glass stone",
        detail="Every candlefly spark doubled in the crystal, so the chamber seemed full of patient stars.",
        tags={"parliament"},
    ),
}

FESTIVALS = {
    "bells": Festival(
        id="bells",
        title="Bell Blossom Day",
        page_name="Bell Blossom Day",
        cheer="the little silver bells rang from the rafters",
        ending_image="petals drifting over the parliament steps",
        tags={"calendar", "festival"},
    ),
    "lanterns": Festival(
        id="lanterns",
        title="Lantern River Night",
        page_name="Lantern River Night",
        cheer="tiny lanterns floated up like sleepy fireflies",
        ending_image="warm lights gliding over dark water",
        tags={"calendar", "festival"},
    ),
    "snowberry": Festival(
        id="snowberry",
        title="Snowberry Sharing Feast",
        page_name="Snowberry Sharing Feast",
        cheer="every spoon in the hall tapped the table in glad rhythm",
        ending_image="red berries shining in white bowls",
        tags={"calendar", "festival"},
    ),
}

SNAGS = {
    "high_hook": Snag(
        id="high_hook",
        label="high hook",
        problem_text="The heavy page loop had slipped onto a brass hook far above the floor.",
        warning_text="If someone reached for it alone, the stool would dance under small feet.",
        solo_trouble="The stool gave a sharp wobble, and the great brass bell above the speaker's chair began to tremble.",
        solve_need="One friend had to hold steady from below while the other reached carefully from above.",
        risk=2,
        tags={"height", "teamwork"},
    ),
    "sap_stick": Snag(
        id="sap_stick",
        label="sap stick",
        problem_text="A dot of golden tree sap had glued the calendar page to the one behind it.",
        warning_text="If someone yanked alone, the paper could tear crooked across the feast day.",
        solo_trouble="The page stretched with a sad crackle, and the painted numbers leaned all askew.",
        solve_need="One friend had to soften the sticky place while the other eased the page free.",
        risk=1,
        tags={"sticky", "teamwork"},
    ),
    "wind_flap": Snag(
        id="wind_flap",
        label="wind flap",
        problem_text="A cheeky wind from the tall window kept flapping the page back against the calendar board.",
        warning_text="If one pair of hands fought the gust alone, the page would slap away again and again.",
        solo_trouble="The page flew from the little hands like a white bird and brushed dust over the front bench.",
        solve_need="One friend had to tame the wind while the other turned the page.",
        risk=1,
        tags={"wind", "teamwork"},
    ),
}

METHODS = {
    "stool_hold": Method(
        id="stool_hold",
        label="stool hold",
        solve_types={"high_hook"},
        setup_text="Together they fetched the round footstool with the braided legs.",
        action_text="One braced the stool with both hands while the other climbed only one careful step, lifted the loop from the hook, and turned the page.",
        qa_text="One helper held the stool still while the other reached up and freed the page from the high hook.",
        tags={"teamwork", "balance"},
    ),
    "dew_cloth": Method(
        id="dew_cloth",
        label="dew cloth",
        solve_types={"sap_stick"},
        setup_text="Together they brought a soft moss cloth dipped in morning dew.",
        action_text="One pressed the cool cloth to the sticky sap while the other peeled the page slowly, corner by corner, until it came free without tearing.",
        qa_text="One helper softened the sap with a damp cloth while the other peeled the page free gently.",
        tags={"teamwork", "calendar"},
    ),
    "window_latch": Method(
        id="window_latch",
        label="window latch",
        solve_types={"wind_flap"},
        setup_text="Together they ran to the tall window where the latch clicked like a tiny shell.",
        action_text="One caught and fastened the wandering window while the other held the page flat and turned it before the wind could steal it again.",
        qa_text="One helper latched the window to stop the wind while the other turned the page.",
        tags={"teamwork", "wind"},
    ),
    "ribbon_line": Method(
        id="ribbon_line",
        label="ribbon line",
        solve_types={"high_hook", "wind_flap"},
        setup_text="Together they unwound a narrow blue ribbon kept for careful hall work.",
        action_text="One guided the ribbon from below while the other looped it over the page ring, drew the page down into easy reach, and held it still long enough to turn.",
        qa_text="The two friends used a ribbon together to bring the page under control and turn it safely.",
        tags={"teamwork", "calendar"},
    ),
}

GIRL_NAMES = ["Luma", "Poppy", "Nell", "Ivy", "Mira", "Tansy", "Wren", "Daisy"]
BOY_NAMES = ["Finn", "Orrin", "Milo", "Tobin", "Rowan", "Pip", "Alder", "Bram"]
TRAITS = ["eager", "brisk", "hopeful", "careful", "bright", "earnest"]

KNOWLEDGE = {
    "parliament": [
        (
            "What is a parliament?",
            "A parliament is a place where a group gathers to talk, plan, and make decisions together. In this fairy tale, it is the meeting hall of the little kingdom.",
        )
    ],
    "calendar": [
        (
            "What is a calendar for?",
            "A calendar helps people keep track of days and special events. It shows when a feast or holiday is meant to happen.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another to do something better than one person could do alone. Each person does a part, and the parts fit together.",
        )
    ],
    "wind": [
        (
            "Why can wind make paper hard to hold?",
            "Wind pushes on light paper and makes it flap away. That is why someone may need to hold the paper or close a window first.",
        )
    ],
    "sticky": [
        (
            "Why is sticky sap hard to clean off?",
            "Sap is thick and tacky, so it clings to things. If you pull too fast, it can make paper bend or tear.",
        )
    ],
    "balance": [
        (
            "Why should someone steady a stool?",
            "A stool can wobble if a person reaches too far from the top. Holding it still helps keep the climber safe and balanced.",
        )
    ],
}
KNOWLEDGE_ORDER = ["parliament", "calendar", "teamwork", "wind", "sticky", "balance"]


def method_solves(snag: Snag, method: Method) -> bool:
    return snag.id in method.solve_types


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for chamber_id in CHAMBERS:
        for festival_id in FESTIVALS:
            for snag_id, snag in SNAGS.items():
                for method_id, method in METHODS.items():
                    if method_solves(snag, method):
                        combos.append((chamber_id, festival_id, snag_id, method_id))
    return combos


@dataclass
class StoryParams:
    chamber: str = "acorn"
    festival: str = "bells"
    snag: str = "high_hook"
    method: str = "stool_hold"
    hero: str = "Luma"
    hero_gender: str = "girl"
    partner: str = "Finn"
    partner_gender: str = "boy"
    speaker: str = "Speaker Owl"
    trait: str = "eager"
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


def explain_rejection(snag: Snag, method: Method) -> str:
    good = ", ".join(sorted(mid for mid, m in METHODS.items() if method_solves(snag, m)))
    return (
        f"(No story: the method '{method.id}' does not sensibly solve the snag '{snag.id}'. "
        f"This problem needs teamwork of a different kind. Try: {good}.)"
    )


def predict_solo_trouble(world: World, snag: Snag) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    calendar = sim.get("calendar")
    hero.memes["defiance"] += 1
    hero.meters["off_balance"] += 1 if snag.risk >= 2 else 0
    calendar.meters["crooked"] += 1 if snag.id == "sap_stick" else 0
    calendar.meters["flapping"] += 1 if snag.id == "wind_flap" else 0
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("stool").meters["wobble"],
        "crooked": calendar.meters["crooked"],
        "flapping": calendar.meters["flapping"],
    }


def introduce(world: World, hero: Entity, partner: Entity, speaker: Entity,
              chamber: Chamber, festival: Festival) -> None:
    world.say(
        f"Once, {chamber.scene}, there stood {chamber.label}. {chamber.detail}"
    )
    world.say(
        f"On that morning, the whole parliament was waiting for {festival.title}, "
        f"and above the moon-round table hung a giant calendar painted with curling vines."
    )
    world.say(
        'Along its gold border ran the old practice letters "tuvwx," '
        "bright as if a patient scribe had written them there for luck."
    )
    hero.memes["duty"] += 1
    partner.memes["duty"] += 1
    speaker.memes["calm"] += 1


def announce_task(world: World, hero: Entity, partner: Entity, speaker: Entity,
                  snag: Snag, festival: Festival) -> None:
    world.say(
        f'"Little friends," said {speaker.id}, "the calendar must be turned to '
        f'{festival.page_name} before the first guests arrive."'
    )
    world.say(
        f"{hero.id} and {partner.id} looked up. {snag.problem_text}"
    )


def volunteer(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["eagerness"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'"I can do it at once," said {hero.id}, whose heart was always the first to run toward a task.'
    )
    world.say(
        f'{partner.id} came close beside {hero.pronoun("object")}, ready to help if help was wanted.'
    )


def warn(world: World, hero: Entity, partner: Entity, snag: Snag) -> None:
    pred = predict_solo_trouble(world, snag)
    partner.memes["care"] += 1
    world.facts["predicted"] = pred
    extra = ""
    if pred["wobble"] >= THRESHOLD:
        extra = " The stool would wobble."
    elif pred["crooked"] >= THRESHOLD:
        extra = " The page might tear crooked."
    elif pred["flapping"] >= THRESHOLD:
        extra = " The wind would only slap the page away."
    world.say(
        f'"Wait," said {partner.id}. "{snag.warning_text}{extra} Let us do it together."'
    )


def hasty_attempt(world: World, hero: Entity, snag: Snag) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} was so eager to be useful that {hero.pronoun()} tried first with only {hero.pronoun('possessive')} own two hands."
    )
    if snag.id == "high_hook":
        world.get("stool").meters["used"] += 1
        hero.meters["off_balance"] += 1
    elif snag.id == "sap_stick":
        world.get("calendar").meters["crooked"] += 1
    elif snag.id == "wind_flap":
        world.get("calendar").meters["flapping"] += 1
    propagate(world, narrate=False)
    world.say(snag.solo_trouble)


def call_for_teamwork(world: World, speaker: Entity, hero: Entity, partner: Entity, snag: Snag) -> None:
    hero.memes["humility"] += 1
    partner.memes["resolve"] += 1
    world.say(
        f'"No blame," said {speaker.id} in a soft old voice. "Small hands need not work alone in this parliament."'
    )
    world.say(
        f"{hero.id} climbed down, cheeks warm, and at last nodded to {partner.id}. {snag.solve_need}"
    )


def teamwork_fix(world: World, hero: Entity, partner: Entity, method: Method, festival: Festival) -> None:
    hero.memes["trust"] += 1
    partner.memes["trust"] += 1
    world.say(method.setup_text)
    world.say(method.action_text)
    calendar = world.get("calendar")
    calendar.meters["turned"] += 1
    calendar.meters["crooked"] = 0.0
    calendar.meters["flapping"] = 0.0
    world.get("stool").meters["wobble"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"There, shining at the front of the great calendar, was the page for {festival.page_name}."
    )


def ending(world: World, hero: Entity, partner: Entity, speaker: Entity, festival: Festival) -> None:
    hero.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f"{speaker.id} spread {speaker.pronoun('possessive')} wings and smiled. Soon {festival.cheer}."
    )
    world.say(
        f"{hero.id} and {partner.id} stood shoulder to shoulder and felt bigger than either of them had felt alone."
    )
    world.say(
        f"And when evening came, the tale ended with {festival.ending_image}, while the calendar page gleamed overhead as proof that teamwork had set the day right."
    )


def tell(chamber: Chamber, festival: Festival, snag: Snag, method: Method,
         hero_name: str = "Luma", hero_gender: str = "girl",
         partner_name: str = "Finn", partner_gender: str = "boy",
         speaker_name: str = "Speaker Owl", trait: str = "eager") -> World:
    world = World(chamber=chamber)
    hero_type = "fairy_girl" if hero_gender == "girl" else "fairy_boy"
    partner_type = "fairy_girl" if partner_gender == "girl" else "fairy_boy"
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero", traits=[trait], attrs={}))
    partner = world.add(Entity(id="partner", kind="character", type=partner_type, label=partner_name, role="partner", traits=["steady"], attrs={}))
    speaker = world.add(Entity(id="speaker", kind="character", type="owl", label=speaker_name, role="speaker", traits=["wise"], attrs={}))
    world.add(Entity(id="hall", type="hall", label="the hall", attrs={}))
    world.add(Entity(id="calendar", type="calendar", label="the calendar", attrs={}))
    world.add(Entity(id="stool", type="stool", label="the stool", attrs={}))

    world.facts["predicted"] = {"wobble": 0.0, "crooked": 0.0, "flapping": 0.0}

    introduce(world, hero, partner, speaker, chamber, festival)
    announce_task(world, hero, partner, speaker, snag, festival)

    world.para()
    volunteer(world, hero, partner)
    warn(world, hero, partner, snag)
    hasty_attempt(world, hero, snag)

    world.para()
    call_for_teamwork(world, speaker, hero, partner, snag)
    teamwork_fix(world, hero, partner, method, festival)
    ending(world, hero, partner, speaker, festival)

    world.facts.update(
        chamber=chamber,
        festival=festival,
        snag=snag,
        method=method,
        hero=hero,
        partner=partner,
        speaker=speaker,
        teamwork=True,
        turned=world.get("calendar").meters["turned"] >= THRESHOLD,
        wobble_happened=world.get("stool").meters["used"] >= THRESHOLD or world.facts["predicted"]["wobble"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chamber = f["chamber"]
    festival = f["festival"]
    snag = f["snag"]
    hero = f["hero"]
    partner = f["partner"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "parliament", "calendar", and "tuvwx".',
        f"Tell a gentle fairy tale where {hero.label} and {partner.label} help a tiny parliament get ready for {festival.title}, but {snag.label} makes the calendar hard to turn.",
        "Write a story about teamwork where a child-sized helper first tries alone, then succeeds only after accepting a friend's help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    speaker = f["speaker"]
    chamber = f["chamber"]
    festival = f["festival"]
    snag = f["snag"]
    method = f["method"]
    pred = f["predicted"]
    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            f"It happens in {chamber.label}, a fairy-tale meeting hall where the little kingdom gathers. The great calendar hangs there because the parliament uses it to keep the feast days in order.",
        ),
        (
            "What job did the helpers need to do?",
            f"They needed to turn the giant calendar to {festival.page_name} before the guests arrived. That mattered because the whole parliament was waiting for the right feast day to begin.",
        ),
        (
            "What was written on the calendar border?",
            'The old practice letters "tuvwx" were painted along the gold border. They made the calendar feel ancient and special.',
        ),
        (
            f"Why did {partner.label} ask {hero.label} to wait?",
            f"{partner.label} could see that {snag.warning_text.lower()} "
            f'{"The stool would wobble." if pred["wobble"] >= THRESHOLD else ""}'
            f'{" The page might tear crooked." if pred["crooked"] >= THRESHOLD else ""}'
            f'{" The wind would only slap it away." if pred["flapping"] >= THRESHOLD else ""}'.strip(),
        ),
        (
            f"How did they finally solve the problem?",
            f"They used teamwork instead of hurry. {method.qa_text} That let the page turn neatly to {festival.page_name}.",
        ),
        (
            "How did the story end?",
            f"The parliament was ready for the feast at last, and the shining calendar proved that the day had been set right. The ending image shows that working together changed worry into celebration.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["chamber"].tags) | set(world.facts["festival"].tags)
    tags |= set(world.facts["snag"].tags) | set(world.facts["method"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        chamber="acorn",
        festival="bells",
        snag="high_hook",
        method="stool_hold",
        hero="Luma",
        hero_gender="girl",
        partner="Finn",
        partner_gender="boy",
        speaker="Speaker Owl",
        trait="eager",
    ),
    StoryParams(
        chamber="lily",
        festival="lanterns",
        snag="sap_stick",
        method="dew_cloth",
        hero="Mira",
        hero_gender="girl",
        partner="Pip",
        partner_gender="boy",
        speaker="Speaker Owl",
        trait="bright",
    ),
    StoryParams(
        chamber="crystal",
        festival="snowberry",
        snag="wind_flap",
        method="window_latch",
        hero="Rowan",
        hero_gender="boy",
        partner="Daisy",
        partner_gender="girl",
        speaker="Speaker Owl",
        trait="hopeful",
    ),
    StoryParams(
        chamber="acorn",
        festival="lanterns",
        snag="wind_flap",
        method="ribbon_line",
        hero="Nell",
        hero_gender="girl",
        partner="Alder",
        partner_gender="boy",
        speaker="Speaker Owl",
        trait="careful",
    ),
]


ASP_RULES = r"""
valid(C,F,S,M) :- chamber(C), festival(F), snag(S), method(M), solves(M,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for chamber_id in CHAMBERS:
        lines.append(asp.fact("chamber", chamber_id))
    for festival_id in FESTIVALS:
        lines.append(asp.fact("festival", festival_id))
    for snag_id in SNAGS:
        lines.append(asp.fact("snag", snag_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for snag_id in sorted(method.solve_types):
            lines.append(asp.fact("solves", method_id, snag_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a tiny parliament, a giant calendar, and teamwork."
    )
    ap.add_argument("--chamber", choices=CHAMBERS)
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snag and args.method:
        snag = SNAGS[args.snag]
        method = METHODS[args.method]
        if not method_solves(snag, method):
            raise StoryError(explain_rejection(snag, method))

    combos = [
        combo for combo in valid_combos()
        if (args.chamber is None or combo[0] == args.chamber)
        and (args.festival is None or combo[1] == args.festival)
        and (args.snag is None or combo[2] == args.snag)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    chamber_id, festival_id, snag_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner_pool = GIRL_NAMES if partner_gender == "girl" else BOY_NAMES
    partner_candidates = [name for name in partner_pool if name != hero_name]
    partner_name = args.partner or rng.choice(partner_candidates)
    trait = rng.choice(TRAITS)
    return StoryParams(
        chamber=chamber_id,
        festival=festival_id,
        snag=snag_id,
        method=method_id,
        hero=hero_name,
        hero_gender=hero_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        speaker="Speaker Owl",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.chamber not in CHAMBERS:
        raise StoryError(f"(Unknown chamber: {params.chamber})")
    if params.festival not in FESTIVALS:
        raise StoryError(f"(Unknown festival: {params.festival})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    chamber = CHAMBERS[params.chamber]
    festival = FESTIVALS[params.festival]
    snag = SNAGS[params.snag]
    method = METHODS[params.method]
    if not method_solves(snag, method):
        raise StoryError(explain_rejection(snag, method))

    world = tell(
        chamber=chamber,
        festival=festival,
        snag=snag,
        method=method,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        speaker_name=params.speaker,
        trait=params.trait,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = [CURATED[0]]
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"Smoke setup failed: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story or "parliament" not in sample.story or "calendar" not in sample.story or "tuvwx" not in sample.story:
                raise StoryError("story text missing required words or is empty")
            print(f"OK: smoke story {i} generated ({params.chamber}, {params.festival}, {params.snag}, {params.method}).")
        except Exception as err:
            rc = 1
            print(f"Smoke generation failed for case {i}: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (chamber, festival, snag, method) combos:\n")
        for chamber, festival, snag, method in combos:
            print(f"  {chamber:8} {festival:10} {snag:10} {method}")
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
            header = f"### {p.hero} and {p.partner}: {p.snag} in {p.chamber} ({p.festival}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
