#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sensitive_happy_ending_inner_monologue_conflict_comedy.py
====================================================================================

A standalone story world about a comedy act that almost turns mean, then becomes
kind and fun instead. The engine models a child who wants a laugh, a sensitive
partner who gets embarrassed, and a repair that must actually fit the problem.

Reference seed tale (rebuilt here as a world model, not a fixed template):
---------------------------------------------------------------------------
A child and a friend plan a silly comedy act. One child chooses a prank that
would make the other child the joke. The partner is sensitive and feels hurt.
There is conflict, some nervous inner monologue, and then a fix: the joke is
changed so the laugh belongs to both children, not at one child's expense. The
show ends with a happy, warm image.

Reasonableness constraint
-------------------------
Not every "funny" idea is a good children's story. A repair must address the
actual social problem:

* If the prank points at the partner, it can cause embarrassment.
* A real fix must reduce embarrassment and restore trust.
* Some repairs are known to the world but refused because they do not really fix
  the hurt (for example, "ignore it" or "double down").

The model prefers a gentle, child-facing comedy where the laugh turns shared.
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
        female = {"girl", "mother", "mom", "woman", "teacher_woman"}
        male = {"boy", "father", "dad", "man", "teacher_man"}
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
    place: str
    audience: str
    stage_detail: str
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
class ActTheme:
    id: str
    intro: str
    goal: str
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
class Prank:
    id: str
    label: str
    phrase: str
    setup: str
    effect: str
    can_target_partner: bool
    silliness: int
    sting: int
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
class Repair:
    id: str
    label: str
    sense: int
    lowers_embarrassment: int
    restores_trust: int
    shares_laugh: bool
    text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_embarrassment_breaks_trust(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    partner = world.get("partner")
    if partner.meters["embarrassment"] >= THRESHOLD:
        sig = ("trust_drop",)
        if sig not in world.fired:
            world.fired.add(sig)
            partner.memes["hurt"] += 1
            performer.memes["worry"] += 1
            performer.memes["conflict"] += 1
            partner.memes["conflict"] += 1
            performer.memes["inner_alarm"] += 1
            partner.memes["trust"] = max(0.0, partner.memes["trust"] - 1.0)
            out.append("__hurt__")
    return out


def _r_shared_laugh_heals(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    partner = world.get("partner")
    if world.facts.get("shared_laugh_ready") and partner.memes["apology_heard"] >= THRESHOLD:
        sig = ("healed",)
        if sig not in world.fired:
            world.fired.add(sig)
            partner.meters["embarrassment"] = 0.0
            performer.memes["conflict"] = 0.0
            partner.memes["conflict"] = 0.0
            partner.memes["trust"] += 2
            performer.memes["relief"] += 1
            partner.memes["relief"] += 1
            performer.memes["joy"] += 1
            partner.memes["joy"] += 1
            out.append("__heal__")
    return out


CAUSAL_RULES = [
    Rule(name="embarrassment_breaks_trust", tag="social", apply=_r_embarrassment_breaks_trust),
    Rule(name="shared_laugh_heals", tag="social", apply=_r_shared_laugh_heals),
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


def prank_can_hurt(prank: Prank) -> bool:
    return prank.can_target_partner and prank.sting > 0


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_fits(prank: Prank, repair: Repair) -> bool:
    if not prank_can_hurt(prank):
        return repair.shares_laugh
    return (
        repair.lowers_embarrassment >= prank.sting
        and repair.restores_trust >= 1
        and repair.shares_laugh
        and repair.sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for theme in ACT_THEMES:
            for prank_id, prank in PRANKS.items():
                if not prank_can_hurt(prank):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(prank, repair):
                        combos.append((setting, theme, prank_id, repair_id))
    return combos


def predict_hurt(world: World, prank: Prank) -> dict:
    sim = world.copy()
    sim.facts["shared_laugh_ready"] = False
    sim.get("partner").meters["embarrassment"] += prank.sting
    propagate(sim, narrate=False)
    return {
        "embarrassed": sim.get("partner").meters["embarrassment"] >= THRESHOLD,
        "trust": sim.get("partner").memes["trust"],
        "conflict": sim.get("partner").memes["conflict"],
    }


def introduce(world: World, performer: Entity, partner: Entity, teacher: Entity, theme: ActTheme) -> None:
    performer.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"On talent-show afternoon, {performer.id} and {partner.id} stood in {world.setting.place}, "
        f"getting ready for {theme.goal}. {world.setting.stage_detail}"
    )
    world.say(
        f"They had planned {theme.intro}, because making each other laugh usually made the waiting feel shorter."
    )
    world.say(
        f"{teacher.label_word.capitalize()} {teacher.id} was pinning up the sign for {world.setting.audience} and telling everyone to keep the act kind."
    )


def choose_prank(world: World, performer: Entity, prank: Prank) -> None:
    performer.memes["showoff"] += 1
    world.say(
        f"{performer.id} pulled out {prank.phrase} and whispered, "
        f'"This will be hilarious. {prank.setup}"'
    )
    world.say(
        f'Inside, {performer.id} thought, "If the room laughs right away, our act will sparkle."'
    )


def warn(world: World, partner: Entity, performer: Entity, prank: Prank) -> None:
    pred = predict_hurt(world, prank)
    world.facts["predicted_embarrassed"] = pred["embarrassed"]
    partner.memes["sensitivity"] += 1
    world.say(
        f"{partner.id} looked at {prank.label} and went quiet. "
        f'"Please do not aim that at me," {partner.pronoun()} said. '
        f'"I know people think I am sensitive, but that joke would make me feel tiny."'
    )
    world.say(
        f'Inside, {partner.id} thought, "I want to be funny, not the funny thing."'
    )


def defy(world: World, performer: Entity, partner: Entity, prank: Prank) -> None:
    performer.memes["defiance"] += 1
    world.say(
        f'{performer.id} gave a brave little grin. "It is only one silly surprise," '
        f"{performer.pronoun()} said."
    )
    world.say(
        f'But inside, {performer.pronoun()} also thought, "What if I am about to be the sort of funny nobody likes?"'
    )
    partner.meters["embarrassment"] += prank.sting
    propagate(world, narrate=False)
    world.say(
        prank.effect.replace("{partner}", partner.id)
    )


def conflict_beat(world: World, performer: Entity, partner: Entity) -> None:
    if partner.meters["embarrassment"] >= THRESHOLD:
        world.say(
            f"{partner.id}'s cheeks went warm, and {partner.pronoun()} folded {partner.pronoun('possessive')} arms. "
            f'"I said not to do that," {partner.pronoun()} said.'
        )
        world.say(
            f"The room did not feel funny anymore. It felt small."
        )


def adult_pause(world: World, teacher: Entity, performer: Entity, partner: Entity) -> None:
    world.say(
        f"{teacher.label_word.capitalize()} {teacher.id} stepped over before the trouble could grow bigger. "
        f'"Comedy is supposed to lift people up," {teacher.pronoun()} said. '
        f'"Try again, but make the laugh belong to both of you."'
    )
    performer.memes["reflection"] += 1
    partner.memes["hope"] += 1
    world.say(
        f'Inside, {performer.id} thought, "Oh. I wanted a big laugh, but I do not want to lose {partner.id}."'
    )


def repair_scene(world: World, performer: Entity, partner: Entity, repair: Repair, prank: Prank, theme: ActTheme) -> None:
    performer.memes["kindness"] += 1
    partner.memes["listening"] += 1
    partner.memes["apology_heard"] += 1
    partner.meters["embarrassment"] = max(0.0, partner.meters["embarrassment"] - repair.lowers_embarrassment)
    partner.memes["trust"] += repair.restores_trust
    world.facts["shared_laugh_ready"] = repair.shares_laugh
    world.say(
        repair.text.replace("{partner}", partner.id).replace("{prank}", prank.label).replace("{closing}", theme.closing)
    )
    propagate(world, narrate=False)
    if partner.meters["embarrassment"] < THRESHOLD:
        world.say(
            f"{partner.id} let out a surprised puff of laughter. The knot in {partner.pronoun('possessive')} chest began to loosen."
        )


def happy_show(world: World, performer: Entity, partner: Entity, prank: Prank, theme: ActTheme) -> None:
    world.say(
        f"When their turn came, {performer.id} used {prank.label} on {performer.pronoun('object')} instead, then bowed so hard that both children nearly tipped into a giggling heap."
    )
    world.say(
        f"The laugh that burst from {world.setting.audience} was round and warm, not sharp. It sounded like everyone was in on the same bright joke."
    )
    world.say(
        f"{partner.id} took {performer.id}'s hand for the final bit, and together they {theme.closing}. "
        f"They walked off the stage still laughing, and this time the funny feeling was safe."
    )


def tell(
    setting: Setting,
    theme: ActTheme,
    prank: Prank,
    repair: Repair,
    performer_name: str = "Milo",
    performer_type: str = "boy",
    partner_name: str = "Lena",
    partner_type: str = "girl",
    teacher_type: str = "teacher_woman",
    partner_trait: str = "sensitive",
) -> World:
    world = World(setting)
    performer = world.add(Entity(
        id="performer",
        kind="character",
        type=performer_type,
        label=performer_name,
        role="performer",
        traits=["silly"],
        attrs={"display_name": performer_name},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_type,
        label=partner_name,
        role="partner",
        traits=[partner_trait],
        attrs={"display_name": partner_name},
    ))
    teacher = world.add(Entity(
        id="teacher",
        kind="character",
        type=teacher_type,
        label="the teacher",
        role="adult",
        attrs={"display_name": "Ms. Bell" if teacher_type == "teacher_woman" else "Mr. Bell"},
    ))

    performer.memes["trust"] = 2.0
    partner.memes["trust"] = 2.0
    performer.memes["inner_alarm"] = 0.0
    partner.memes["apology_heard"] = 0.0
    world.facts["shared_laugh_ready"] = False

    introduce(world, performer, partner, teacher, theme)
    world.para()
    choose_prank(world, performer, prank)
    warn(world, partner, performer, prank)
    defy(world, performer, partner, prank)
    conflict_beat(world, performer, partner)
    world.para()
    adult_pause(world, teacher, performer, partner)
    repair_scene(world, performer, partner, repair, prank, theme)
    world.para()
    happy_show(world, performer, partner, prank, theme)

    world.facts.update(
        performer=performer,
        partner=partner,
        teacher=teacher,
        setting=setting,
        theme=theme,
        prank=prank,
        repair=repair,
        embarrassed=partner.meters["embarrassment"] < THRESHOLD,
        healed=partner.memes["trust"] >= 2.0 and partner.memes["conflict"] < THRESHOLD,
        outcome="happy",
        performer_name=performer_name,
        partner_name=partner_name,
        teacher_name=teacher.attrs["display_name"],
        partner_trait=partner_trait,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        audience="parents on folding chairs and children with shiny shoes",
        stage_detail="A paper curtain kept wobbling every time someone brushed past it",
        tags={"school"},
    ),
    "library": Setting(
        id="library",
        place="the library meeting room",
        audience="families sitting between carts of books",
        stage_detail="The microphone kept leaning sideways as if it wanted to hear the joke first",
        tags={"library"},
    ),
    "hall": Setting(
        id="hall",
        place="the little community hall",
        audience="neighbors packed onto squeaky chairs",
        stage_detail="A crooked spotlight made the floor look like a giant egg yolk",
        tags={"community"},
    ),
}

ACT_THEMES = {
    "detectives": ActTheme(
        id="detectives",
        intro="a tiny detective sketch with much too much sneaking",
        goal="their two-person comedy act",
        closing="solved the world's silliest mystery with one magnifying glass and two serious faces",
        tags={"show"},
    ),
    "space": ActTheme(
        id="space",
        intro="a space routine about very brave astronauts and one nervous moon rock",
        goal="their two-person comedy act",
        closing="saluted the moon rock and marched away in slow-motion space steps",
        tags={"show"},
    ),
    "chefs": ActTheme(
        id="chefs",
        intro="a chef sketch about a soup pot with dramatic feelings",
        goal="their two-person comedy act",
        closing="stirred an invisible soup and announced it tasted exactly like victory",
        tags={"show"},
    ),
}

PRANKS = {
    "whoopee": Prank(
        id="whoopee",
        label="a whoopee cushion",
        phrase="a flat red whoopee cushion",
        setup="You sit, it squeaks, everyone explodes",
        effect="{partner} sat down for rehearsal, the cushion squeaked like a startled duck, and three waiting children barked out startled laughs.",
        can_target_partner=True,
        silliness=3,
        sting=2,
        tags={"prank", "whoopee"},
    ),
    "mustache": Prank(
        id="mustache",
        label="a giant sticky mustache",
        phrase="a giant sticky mustache on a paper card",
        setup="I will slap it on your face at the big reveal",
        effect="{partner} turned just in time for the mustache to land sideways across {partner}'s nose, and a burst of laughter jumped across the room before {partner} could smile.",
        can_target_partner=True,
        silliness=2,
        sting=1,
        tags={"prank", "mustache"},
    ),
    "chicken": Prank(
        id="chicken",
        label="a squeaky rubber chicken",
        phrase="a squeaky rubber chicken with a bent neck",
        setup="I wave it over your head like it is giving stage directions",
        effect="The rubber chicken bobbed over {partner}'s head and let out a shriek so odd that the waiting line laughed first and asked questions later.",
        can_target_partner=True,
        silliness=3,
        sting=1,
        tags={"prank", "chicken"},
    ),
}

REPAIRS = {
    "apology_swap": Repair(
        id="apology_swap",
        label="apology and self-joke",
        sense=3,
        lowers_embarrassment=2,
        restores_trust=2,
        shares_laugh=True,
        text='"{partner}, I am sorry," the performer said at once. Then {performer} put the {prank} on {performer_pronoun} instead and said, "There. If anyone gets surprised, let it be me."',
        qa_text="apologized and turned the joke onto themself",
        tags={"apology", "kindness"},
    ),
    "rewrite_together": Repair(
        id="rewrite_together",
        label="rewrite the bit together",
        sense=3,
        lowers_embarrassment=2,
        restores_trust=1,
        shares_laugh=True,
        text='The performer took a breath. "I am sorry. Let us change it," {performer_pronoun} said. Together they rewrote the bit so both children got a silly turn before they {closing}.',
        qa_text="apologized and rewrote the joke together",
        tags={"apology", "teamwork"},
    ),
    "ignore_it": Repair(
        id="ignore_it",
        label="ignore the hurt",
        sense=1,
        lowers_embarrassment=0,
        restores_trust=0,
        shares_laugh=False,
        text='The performer shrugged and said everyone would forget in a minute.',
        qa_text="shrugged and ignored the hurt",
        tags={"bad_fix"},
    ),
    "double_down": Repair(
        id="double_down",
        label="do it again, louder",
        sense=0,
        lowers_embarrassment=0,
        restores_trust=0,
        shares_laugh=False,
        text='The performer announced that the second time would probably be even funnier.',
        qa_text="tried the same mean joke again",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Lena", "Mia", "Nora", "Ava", "Ivy", "Ruby", "Ella", "June"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Finn", "Eli", "Max", "Owen", "Sam"]
TRAITS = ["sensitive", "gentle", "careful", "tenderhearted"]


def _text_repair(world: World, repair: Repair, performer: Entity, partner: Entity, prank: Prank, theme: ActTheme) -> str:
    return (
        repair.text
        .replace("{partner}", partner.attrs["display_name"])
        .replace("{prank}", prank.label)
        .replace("{closing}", theme.closing)
        .replace("{performer}", performer.attrs["display_name"])
        .replace("{performer_pronoun}", performer.pronoun())
    )


@dataclass
class StoryParams:
    setting: str
    theme: str
    prank: str
    repair: str
    performer_name: str
    performer_gender: str
    partner_name: str
    partner_gender: str
    teacher_type: str
    partner_trait: str = "sensitive"
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
    "prank": [(
        "What is a prank?",
        "A prank is a trick meant to surprise someone. It should never be used to make a person feel small or left out."
    )],
    "apology": [(
        "Why does an apology help after a hurt joke?",
        "An apology shows that you noticed the hurt and want to make it right. That helps trust begin to grow back."
    )],
    "kindness": [(
        "What does kind comedy mean?",
        "Kind comedy makes people laugh without turning one person into the target. The best joke leaves everyone feeling safe enough to laugh too."
    )],
    "teamwork": [(
        "Why is working together good in a performance?",
        "Working together helps both people know what is coming and share the fun. That makes the act smoother and kinder."
    )],
    "whoopee": [(
        "What is a whoopee cushion?",
        "A whoopee cushion is a rubber toy that makes a silly noise when someone sits on it. It is only funny when everyone is comfortable with the joke."
    )],
    "mustache": [(
        "Why can a silly costume piece still hurt feelings?",
        "Even a silly prop can hurt if it is slapped onto someone who did not agree to it. Surprise is fun only when it feels safe."
    )],
    "chicken": [(
        "Why do strange noises make people laugh?",
        "Unexpected sounds can surprise the brain in a funny way. But the laugh stays kinder when the sound is part of a shared joke."
    )],
}
KNOWLEDGE_ORDER = ["prank", "apology", "kindness", "teamwork", "whoopee", "mustache", "chicken"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prank = f["prank"]
    setting = f["setting"]
    partner = f["partner"]
    performer = f["performer"]
    return [
        f'Write a short comedy story for a 3-to-5-year-old that uses the word "sensitive" and takes place in {setting.place}.',
        f"Tell a funny but gentle story where {performer.attrs['display_name']} almost makes {partner.attrs['display_name']} the joke with {prank.label}, then fixes the mistake and turns the laugh into a shared one.",
        "Write a story with conflict, inner thoughts, and a happy ending where a child learns that comedy should be kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    performer = f["performer"]
    partner = f["partner"]
    teacher = f["teacher"]
    prank = f["prank"]
    repair = f["repair"]
    theme = f["theme"]
    performer_name = performer.attrs["display_name"]
    partner_name = partner.attrs["display_name"]
    teacher_name = teacher.attrs["display_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {performer_name} and {partner_name}, two children getting ready for a comedy act, and {teacher_name}, the grown-up who helps them pause and fix the problem."
        ),
        (
            f"What caused the conflict between {performer_name} and {partner_name}?",
            f"The conflict started when {performer_name} used {prank.label} in a way that made {partner_name} the target of the joke. {partner_name} had already warned that the prank would feel hurtful, so the laugh landed as embarrassment instead of fun."
        ),
        (
            f"Why did {partner_name} say {partner.pronoun()} was sensitive?",
            f"{partner_name} knew the prank would make {partner.pronoun('object')} feel small in front of other people. {partner.pronoun().capitalize()} wanted to be part of the funny act, not the person everyone laughed at."
        ),
        (
            f"What was {performer_name} thinking inside after the prank went wrong?",
            f"Inside, {performer_name} worried that the big laugh had become the wrong kind of laugh. {performer.pronoun().capitalize()} realized that being funny was not worth hurting {partner_name}'s feelings."
        ),
        (
            f"How did {teacher_name} help?",
            f"{teacher_name} reminded them that comedy should lift people up. That gave {performer_name} a clear way to repair the hurt instead of pretending nothing had happened."
        ),
    ]
    repair_answer = repair.qa_text
    qa.append((
        f"How did {performer_name} fix the problem?",
        f"{performer_name} {repair_answer}. That lowered {partner_name}'s embarrassment and helped trust come back, because the joke became shared instead of pointed."
    ))
    qa.append((
        "How did the story end?",
        f"It ended happily at the show, with both children laughing together on stage. The final laugh was warm because nobody was being picked on anymore."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["prank"].tags) | set(world.facts["repair"].tags)
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
    for eid, e in world.entities.items():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {eid:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        theme="detectives",
        prank="whoopee",
        repair="apology_swap",
        performer_name="Milo",
        performer_gender="boy",
        partner_name="Lena",
        partner_gender="girl",
        teacher_type="teacher_woman",
        partner_trait="sensitive",
    ),
    StoryParams(
        setting="library",
        theme="space",
        prank="mustache",
        repair="rewrite_together",
        performer_name="Ava",
        performer_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        teacher_type="teacher_man",
        partner_trait="gentle",
    ),
    StoryParams(
        setting="hall",
        theme="chefs",
        prank="chicken",
        repair="apology_swap",
        performer_name="Theo",
        performer_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
        teacher_type="teacher_woman",
        partner_trait="tenderhearted",
    ),
]


def explain_rejection(prank: Prank, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        return (
            f"(No story: repair '{repair.id}' is known to the world, but it does not really fix the hurt. "
            f"A children's comedy here must use a repair that lowers embarrassment and restores trust.)"
        )
    return (
        f"(No story: {repair.label} does not address the harm caused by {prank.label}. "
        f"The repair has to turn the laugh into a shared one, not just keep the act moving.)"
    )


def explain_gender(gender: str) -> str:
    return f"(No story: gender must be girl or boy, not {gender!r}.)"


ASP_RULES = r"""
hurtful(P) :- prank(P), can_target_partner(P), sting(P, S), S > 0.
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
fits(P, R) :- hurtful(P), repair(R), sting(P, S), lowers_embarrassment(R, E), E >= S,
              restores_trust(R, T), T >= 1, shares_laugh(R), sensible(R).
valid(Se, Th, P, R) :- setting(Se), theme(Th), hurtful(P), fits(P, R).

outcome(happy) :- chosen_prank(P), chosen_repair(R), fits(P, R).
:- chosen_prank(P), chosen_repair(R), not fits(P, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in ACT_THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, prank in PRANKS.items():
        lines.append(asp.fact("prank", pid))
        if prank.can_target_partner:
            lines.append(asp.fact("can_target_partner", pid))
        lines.append(asp.fact("sting", pid, prank.sting))
        lines.append(asp.fact("silliness", pid, prank.silliness))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("lowers_embarrassment", rid, repair.lowers_embarrassment))
        lines.append(asp.fact("restores_trust", rid, repair.restores_trust))
        if repair.shares_laugh:
            lines.append(asp.fact("shares_laugh", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_prank", params.prank),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comedy act, a hurtful prank, and a kind repair."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--theme", choices=ACT_THEMES)
    ap.add_argument("--prank", choices=PRANKS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--performer-name")
    ap.add_argument("--performer-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-type", choices=["teacher_woman", "teacher_man"])
    ap.add_argument("--partner-trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    if gender not in {"girl", "boy"}:
        raise StoryError(explain_gender(gender))
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prank and not prank_can_hurt(PRANKS[args.prank]):
        raise StoryError("(No story: that prank would not create the needed hurtful conflict here.)")
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        prank = PRANKS[args.prank] if args.prank else next(iter(PRANKS.values()))
        raise StoryError(explain_rejection(prank, REPAIRS[args.repair]))
    if args.prank and args.repair and not repair_fits(PRANKS[args.prank], REPAIRS[args.repair]):
        raise StoryError(explain_rejection(PRANKS[args.prank], REPAIRS[args.repair]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.theme is None or c[1] == args.theme)
        and (args.prank is None or c[2] == args.prank)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, theme, prank, repair = rng.choice(sorted(combos))
    performer_gender = args.performer_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    performer_name = args.performer_name or _pick_name(rng, performer_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=performer_name)
    teacher_type = args.teacher_type or rng.choice(["teacher_woman", "teacher_man"])
    partner_trait = args.partner_trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        theme=theme,
        prank=prank,
        repair=repair,
        performer_name=performer_name,
        performer_gender=performer_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        teacher_type=teacher_type,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        ("setting", SETTINGS),
        ("theme", ACT_THEMES),
        ("prank", PRANKS),
        ("repair", REPAIRS),
    ):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(No story: unknown {key} {value!r}.)")

    prank = PRANKS[params.prank]
    repair = REPAIRS[params.repair]
    if not repair_fits(prank, repair):
        raise StoryError(explain_rejection(prank, repair))

    world = tell(
        setting=SETTINGS[params.setting],
        theme=ACT_THEMES[params.theme],
        prank=prank,
        repair=repair,
        performer_name=params.performer_name,
        performer_type=params.performer_gender,
        partner_name=params.partner_name,
        partner_type=params.partner_gender,
        teacher_type=params.teacher_type,
        partner_trait=params.partner_trait,
    )

    performer = world.get("performer")
    partner = world.get("partner")
    teacher = world.get("teacher")
    for old, new in (
        ("performer", performer.attrs["display_name"]),
        ("partner", partner.attrs["display_name"]),
        ("teacher", teacher.attrs["display_name"]),
    ):
        world.paragraphs = [[sent.replace(old, new) for sent in para] for para in world.paragraphs]

    repair_text = _text_repair(world, repair, performer, partner, prank, ACT_THEMES[params.theme])
    world.paragraphs = [[sent if sent != repair.text else repair_text for sent in para] for para in world.paragraphs]

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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_repairs()}
    asp_sensible = set(asp_sensible_repairs())
    if py_sensible == asp_sensible:
        print(f"OK: sensible repairs match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

    bad = 0
    for params in cases:
        py_out = "happy"
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python expectations on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-tested ordinary generation.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, theme, prank, repair) combos:\n")
        for setting, theme, prank, repair in combos:
            print(f"  {setting:10} {theme:10} {prank:10} {repair}")
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
            header = f"### {p.performer_name} & {p.partner_name}: {p.prank} in {p.setting} ({p.theme}, {p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
