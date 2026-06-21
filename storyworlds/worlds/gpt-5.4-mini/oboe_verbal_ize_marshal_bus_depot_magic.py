#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oboe_verbal_ize_marshal_bus_depot_magic.py
===========================================================================

A standalone story world for a tiny bus-depot adventure with magic, suspense,
and kindness. Children are waiting at a busy bus depot when a magical oboe cue
goes missing, a marshal has to verbal-ize the plan, and a kind act turns worry
into a safe, bright ending.

The world is built from a small simulation: typed entities carry physical meters
and emotional memes, events change state, and the prose is rendered from that
state rather than from a frozen template.

Seed words:
- oboe
- verbal-ize
- marshal

Setting:
- bus depot

Features:
- Magic
- Suspense
- Kindness

Style:
- Space Adventure
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
BRAVERY_INIT = 5.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    partner: str
    goal: str
    dark_spot: str
    voyage: str
    ending: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    where: str
    has_magic: bool = False
    makes_sound: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    risk: str
    spread: int
    dangerous: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["danger"] >= THRESHOLD and ("spook", ent.id) not in world.fired:
            world.fired.add(("spook", ent.id))
            ent.memes["fear"] += 1
            out.append("__spook__")
    return out


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["magic"] >= THRESHOLD and ("shine", ent.id) not in world.fired:
            world.fired.add(("shine", ent.id))
            ent.memes["wonder"] += 1
            out.append("__shine__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("shine", "magic", _r_shine)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def hazard_at_risk(signal: Signal, hazard: Hazard) -> bool:
    return signal.has_magic and hazard.dangerous


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def fire_severity(hazard: Hazard, delay: int) -> int:
    return hazard.spread + delay


def is_contained(remedy: Remedy, hazard: Hazard, delay: int) -> bool:
    return remedy.power >= fire_severity(hazard, delay)


def tell_theme(world: World, hero: Entity, partner: Entity, theme: Theme) -> None:
    hero.memes["curiosity"] += 1
    partner.memes["care"] += 1
    world.say(
        f"The {theme.id} crew had parked the bus depot like a tiny launch bay. "
        f"{theme.rig}"
    )
    world.say(
        f'{hero.id} pointed at the sky-high signs and grinned. "{theme.captain} '
        f'{hero.id} and {theme.partner} {partner.id}!" {hero.id} said. '
        f'"Let us find {theme.goal}!"'
    )


def need_signal(world: World, partner: Entity, theme: Theme, hazard: Hazard) -> None:
    world.say(
        f"But the {theme.dark_spot} at the edge of the depot felt hush-quiet, as if "
        f"it were hiding a moon cave."
    )
    world.say(
        f'{partner.id} peered inside and whispered, "We need a signal."'
    )


def tempt(world: World, hero: Entity, signal: Signal) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'{hero.id} leaned forward. "{signal.phrase} I saw the {signal.label} '
        f"{signal.where}."
    )
    world.say("For one shaky second, the idea looked clever and grand.")


def warn(world: World, partner: Entity, hero: Entity, signal: Signal, hazard: Hazard) -> None:
    partner.memes["kindness"] += 1
    world.say(
        f'{partner.id} shook {partner.pronoun("possessive")} head. '
        f'"We should not touch {signal.label}. It can make real magic noise, '
        f'and {hazard.phrase} can turn a little spark into trouble."'
    )


def defy(world: World, hero: Entity, signal: Signal) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I know," {hero.id} said, and still reached for {signal.label}.'
    )


def seize_and_signal(world: World, signal_ent: Entity) -> None:
    signal_ent.meters["used"] += 1
    signal_ent.meters["magic"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A soft {signal_ent.label} note floated up, bright as a tiny star. "
        f'Then the magic flickered too near the depot lamp, and a sharp hush fell.'
    )


def alarm(world: World, partner: Entity, hero: Entity, hazard: Hazard, parent: Entity) -> None:
    world.say(
        f'"{hero.id}! {hazard.label}!" {partner.id} cried. '
        f'"{parent.label_word.capitalize()}!"'
    )


def rescue(world: World, parent: Entity, remedy: Remedy, hazard: Hazard, theme: Theme) -> None:
    world.get("lamp").meters["danger"] = 0.0
    world.get("lamp").meters["smoke"] = 0.0
    body = remedy.text.replace("{hazard}", hazard.label)
    world.say(
        f"{parent.label_word.capitalize()} came running, and in one calm move "
        f"{parent.pronoun()} {body}."
    )
    world.say(
        f"The danger faded into a silver puff, and the bus depot felt safe again."
    )


def lesson(world: World, parent: Entity, hero: Entity, partner: Entity, signal: Signal) -> None:
    for kid in (hero, partner):
        kid.memes["relief"] += 1
        kid.memes["kindness"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"Thank you for calling me," {parent.pronoun()} said softly. '
        f'"Magic tools are not toys, and kindness means asking for help before fear grows."'
    )
    world.say(f'"We promise," whispered {hero.id} and {partner.id} together.')


def safe_gift(world: World, parent: Entity, hero: Entity, partner: Entity, theme: Theme, safe: Signal) -> None:
    for kid in (hero, partner):
        kid.memes["joy"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} had a surprise: "
        f"{parent.pronoun()} handed them a safe little beacon and a glittering map."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what does a space crew use to explore '
        f"a dark depot?"
    )
    world.say(
        f'{hero.id} held up the beacon, and {partner.id} clicked on the map light. '
        f'"Safe light!" they cheered.'
    )
    world.say(
        f"This time, the crew {theme.ending} -- bright, brave, and kind."
    )


def salvage_fail(world: World, parent: Entity, remedy: Remedy, hazard: Hazard) -> None:
    world.get("lamp").meters["danger"] += 1
    world.get("lamp").meters["smoke"] += 1
    body = remedy.fail.replace("{hazard}", hazard.label)
    world.say(
        f"{parent.label_word.capitalize()} came running, but {parent.pronoun()} {body}."
    )
    world.say(
        f"The little trouble grew into a bigger, smoky mess, and everyone had to move back."
    )


def escape_and_lesson(world: World, parent: Entity, hero: Entity, partner: Entity, signal: Signal) -> None:
    for kid in (hero, partner):
        kid.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} grabbed both children and led them out to the night air."
    )
    world.say(
        f"From the curb they watched the depot lights blink on, and the story ended with a quiet warning: "
        f"never touch a magic {signal.label} without a grown-up."
    )


def tell(theme: Theme, signal: Signal, hazard: Hazard, remedy: Remedy,
         hero_name: str = "Mila", hero_gender: str = "girl",
         partner_name: str = "Nico", partner_gender: str = "boy",
         parent_type: str = "marshal", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    parent = world.add(Entity(id="Marshal", kind="character", type=parent_type, role="parent", label="the marshal"))
    world.add(Entity(id="lamp", type="lamp"))
    world.add(Entity(id="signal", type="signal", label=signal.label))
    world.add(Entity(id="hazard", type="hazard", label=hazard.label))

    hero.memes["bravery"] = BRAVERY_INIT
    partner.memes["kindness"] = 5.0
    world.facts["delay"] = delay

    tell_theme(world, hero, partner, theme)
    need_signal(world, partner, theme, hazard)
    world.para()
    tempt(world, hero, signal)
    warn(world, partner, hero, signal, hazard)

    aversion = partner.memes["kindness"] >= 5.0 and hero.memes["bravery"] <= BRAVERY_INIT
    if aversion:
        world.say(
            f'{hero.id} listened, lowered {hero.pronoun("possessive")} hand, and gave up the idea.'
        )
        world.para()
        safe_gift(world, parent, hero, partner, theme, signal)
        outcome = "averted"
        contained = True
    else:
        defy(world, hero, signal)
        world.para()
        seize_and_signal(world, world.get("signal"))
        alarm(world, partner, hero, hazard, parent)
        contained = is_contained(remedy, hazard, delay)
        if contained:
            world.para()
            rescue(world, parent, remedy, hazard, theme)
            lesson(world, parent, hero, partner, signal)
            world.para()
            safe_gift(world, parent, hero, partner, theme, signal)
        else:
            world.para()
            salvage_fail(world, parent, remedy, hazard)
            escape_and_lesson(world, parent, hero, partner, signal)
        outcome = "contained" if contained else "burned"

    world.facts.update(
        hero=hero,
        partner=partner,
        parent=parent,
        theme=theme,
        signal=signal,
        hazard=hazard,
        remedy=remedy,
        outcome=outcome,
        contained=contained,
    )
    return world


THEMES = {
    "space": Theme(
        "space",
        "a tiny launch bay",
        "The bus depot had blinking route signs, a shiny floor, and a row of seats that looked like rocket pods.",
        "Commander",
        "Navigator",
        "the starlight line",
        "the shadow under the last timetable",
        "voyage",
        "set off toward the moon route",
    ),
    "orbit": Theme(
        "orbit",
        "a moon-station dock",
        "The bus depot looked like a station dock, with doors that whooshed and a map board that glowed blue.",
        "Captain",
        "Pilot",
        "the comet stop",
        "the quiet corner by the lost-ticket desk",
        "sail",
        "rolled onward like a bright comet",
    ),
}

SIGNALS = {
    "oboe": Signal("oboe", "oboe", "an oboe", "on a high shelf", has_magic=True, tags={"oboe", "magic", "sound"}),
    "chime": Signal("chime", "chime flute", "a chime flute", "near the map board", has_magic=True, tags={"magic", "sound"}),
    "lantern": Signal("lantern", "lantern", "a little lantern", "by the bench", has_magic=True, tags={"magic", "light"}),
}

HAZARDS = {
    "shadow": Hazard("shadow", "shadow drift", "shadow drift", "the dark shadow drift", 2, tags={"suspense"}),
    "spark": Hazard("spark", "spark leak", "spark leak", "the spark leak", 3, tags={"suspense", "magic"}),
}

REMEDIES = {
    "marshal_talk": Remedy("marshal_talk", 3, 3, "verbal-ized a calm plan and told everyone to step back", "tried to speak over the rush, but the trouble got louder", "verbal-ized a calm plan"),
    "shield": Remedy("shield", 2, 2, "pulled down the safety screen and covered the lamp", "pulled down the screen too late to help", "pulled down the safety screen"),
    "signal_off": Remedy("signal_off", 3, 4, "switched off the depot lights and led everyone to the safe side", "switched off the lights, but the hazard had already spread", "switched off the depot lights"),
}

GIRL_NAMES = ["Mila", "Zoe", "Ava", "Nia", "Luna", "Iris"]
BOY_NAMES = ["Nico", "Eli", "Theo", "Jude", "Owen", "Kai"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    signal: str
    hazard: str
    remedy: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(t, s, h) for t in THEMES for s in SIGNALS for h in HAZARDS if hazard_at_risk(SIGNALS[s], HAZARDS[h])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure style story for a young child set in a bus depot, using the word "{f["signal"].label}".',
        f"Tell a suspenseful but kind story where {f['hero'].id} wants to use {f['signal'].label} at the depot, and a marshal says no and verbal-izes a safer plan.",
        f'Write a magic-and-kindness story in a bus depot where a hidden hazard is found near a {f["signal"].label} and everyone ends safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, parent = f["hero"], f["partner"], f["parent"]
    signal, hazard, remedy = f["signal"], f["hazard"], f["remedy"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {partner.id}, with the marshal helping when the bus depot gets tense. They turn a scary moment into a safer one together.",
        ),
        QAItem(
            question="Why did they need help?",
            answer=f"They needed help because {signal.label} was tempting, but it was not safe near {hazard.label}. The marshal had to verbal-ize a calm plan before the trouble could grow.",
        ),
        QAItem(
            question=f"What did {parent.label_word} do?",
            answer=f"{parent.label_word.capitalize()} came running and {remedy.qa_text}. That stopped the danger and showed kindness under pressure.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            QAItem(
                question=f"What happened after {partner.id} warned {hero.id}?",
                answer=f"{hero.id} listened, gave up the idea, and the story skipped the accident entirely. They used safe light instead, so the depot stayed calm.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            QAItem(
                question="How did the ending change the mood?",
                answer="At first it felt suspenseful, but the marshal solved the problem and the children got a bright, safe ending. The last image is of them feeling brave again.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What was the final outcome?",
                answer="The trouble grew too big for the first fix, so everyone moved back and got out safely. They learned to call for help sooner next time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["signal"].tags) | set(world.facts["hazard"].tags) | {"kindness", "magic"}
    out = []
    if "oboe" in tags:
        out.append(QAItem("What is an oboe?", "An oboe is a woodwind instrument that makes a bright, reedy sound when someone plays it. In a story it can feel magical because its note is so sharp and clear."))
    out.append(QAItem("What does verbal-ize mean?", "To verbal-ize means to put thoughts into words. A marshal who verbal-izes a plan is speaking calmly and clearly so everyone knows what to do."))
    out.append(QAItem("Who is a marshal?", "A marshal is a person who keeps order and helps people stay safe. In this world, the marshal uses calm words to guide everyone through a tense moment."))
    out.append(QAItem("Why is kindness important in a scary moment?", "Kindness helps people listen, stay calm, and help each other instead of panicking. That can turn suspense into safety."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="] + [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)] + ["", "== story qa =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines += ["", "== world qa =="]
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("space", "oboe", "spark", "marshal_talk", "Mila", "girl", "Nico", "boy", "marshal", 0),
    StoryParams("orbit", "chime", "shadow", "shield", "Kai", "boy", "Luna", "girl", "marshal", 1),
]


def explain_rejection(signal: Signal, hazard: Hazard) -> str:
    return f"(No story: {signal.label} is magical, but {hazard.label} does not make a good suspense hazard here.)"


def explain_response(rid: str) -> str:
    r = REMEDIES[rid]
    better = ", ".join(sorted(x.id for x in sensible_remedies()))
    return f"(Refusing response '{rid}': sense={r.sense} < {SENSE_MIN}. Try {better}.)"


def outcome_of(params: StoryParams) -> str:
    if params.remedy not in REMEDIES:
        return "?"
    return "contained" if is_contained(REMEDIES[params.remedy], HAZARDS[params.hazard], params.delay) else "burned"


ASP_RULES = r"""
hazard(F, H) :- signal(F), danger(H), magic_signal(F), dangerous(H).
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(T, F, H) :- theme(T), signal(F), danger(H), hazard(F, H).
contained :- chosen_remedy(R), chosen_hazard(H), power(R, P), spread(H, S), delay(D), P >= S + D.
outcome(averted) :- no_accident.
outcome(contained) :- not no_accident, contained.
outcome(burned) :- not no_accident, not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for s in SIGNALS.values():
        lines.append(asp.fact("signal", s.id))
        if s.has_magic:
            lines.append(asp.fact("magic_signal", s.id))
    for h in HAZARDS.values():
        lines.append(asp.fact("danger", h.id))
        if h.dangerous:
            lines.append(asp.fact("dangerous", h.id))
        lines.append(asp.fact("spread", h.id, h.spread))
    for r in REMEDIES.values():
        lines.append(asp.fact("remedy", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
        lines.append(asp.fact("power", r.id, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combo gate.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_remedies()}:
        rc = 1
        print("MISMATCH in sensible remedies.")
    else:
        print("OK: sensible remedies match.")
    # smoke test
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    cases = list(CURATED)
    rng = random.Random(777)
    for i in range(20):
        cases.append(resolve_params(build_parser().parse_args([]), random.Random(rng.randint(0, 10**9))))
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches:
        rc = 1
        print(f"MISMATCH: {mismatches} outcomes disagree.")
    else:
        print("OK: outcome model matches.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bus depot magic storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=["marshal"])
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.signal and args.hazard and not hazard_at_risk(SIGNALS[args.signal], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(SIGNALS[args.signal], HAZARDS[args.hazard]))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_response(args.remedy))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.signal is None or c[1] == args.signal)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, signal, hazard = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    hero_gender = "girl" if rng.random() < 0.5 else "boy"
    partner_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(GIRL_NAMES if partner_gender == "girl" else BOY_NAMES)
    return StoryParams(theme, signal, hazard, remedy, hero, hero_gender, partner, partner_gender, "marshal", rng.randint(0, 2))


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], SIGNALS[params.signal], HAZARDS[params.hazard], REMEDIES[params.remedy],
                 params.hero, params.hero_gender, params.partner, params.partner_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}")
        print(f"compatible combos: {len(asp_valid_combos())}")
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
            header = f"### {p.hero} & {p.partner}: {p.signal} near {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
