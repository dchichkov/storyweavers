#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kiss_dim_surprise_magic_cautionary_myth.py
=====================================================================

A standalone storyworld for a tiny mythic domain: a child seeks sacred light at a
moon shrine, reaches for a magical shortcut, disturbs a sleeping spirit, and
learns that old rites are safer than greedy hands.

The seed called for:
- the exact word "kiss-dim"
- Surprise
- Magic
- Cautionary
- a style close to myth

This world models a sacred place, a forbidden magical act, a spirit-bound source
of light, an elder's calming rite, and a safer alternative for later nights.
Its reasonableness gate prefers pairings where the forbidden act truly would
disturb a spirit, and it refuses weak "responses" that do not fit the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/kiss_dim_surprise_magic_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4/kiss_dim_surprise_magic_cautionary_myth.py --all
    python storyworlds/worlds/gpt-5.4/kiss_dim_surprise_magic_cautionary_myth.py --qa
    python storyworlds/worlds/gpt-5.4/kiss_dim_surprise_magic_cautionary_myth.py --trace
    python storyworlds/worlds/gpt-5.4/kiss_dim_surprise_magic_cautionary_myth.py --verify
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
NERVE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "patient", "reverent", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    spirit_bound: bool = False
    wild_magic: bool = False
    gives_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother", "priestess"}
        male = {"boy", "man", "grandfather", "father", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "keeper": "keeper",
            "priestess": "priestess",
        }.get(self.type, self.type)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Sanctuary:
    id: str
    place: str
    path: str
    sky: str
    source_line: str
    need_line: str
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
class Forbidden:
    id: str
    label: str
    phrase: str
    grab_line: str
    warning: str
    touch_word: str
    makes_magic: bool = True
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
class Source:
    id: str
    label: str
    the: str
    resting: str
    glow: str
    guardian: str
    stir_text: str
    spread: int = 2
    spirit_bound: bool = True
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
class SafeLight:
    id: str
    label: str
    phrase: str
    shine: str
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


def _r_awaken(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    shrine = world.entities.get("shrine")
    child = world.entities.get("child")
    if source is None or shrine is None or child is None:
        return out
    if source.meters["disturbed"] < THRESHOLD:
        return out
    sig = ("awaken", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shrine.meters["danger"] += 1
    shrine.meters["darkness"] += 1
    child.memes["fear"] += 1
    out.append("__spirit__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="awaken", tag="magic", apply=_r_awaken),
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


def hazard_at_risk(forbidden: Forbidden, source: Source) -> bool:
    return forbidden.makes_magic and source.spirit_bound


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spirit_severity(source: Source, delay: int) -> int:
    return source.spread + delay


def is_calmed(response: Response, source: Source, delay: int) -> bool:
    return response.power >= spirit_severity(source, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_resist(elder_type: str, trait: str, trust: int) -> bool:
    elder_bonus = 2.0 if elder_type in {"grandmother", "grandfather", "priestess"} else 1.0
    authority = initial_caution(trait) + elder_bonus + (trust / 4.0)
    return authority > NERVE_INIT + 1.0


def predict_disturbance(world: World, source_id: str) -> dict:
    sim = world.copy()
    source = sim.get(source_id)
    _do_forbidden(sim, source, narrate=False)
    return {
        "danger": sim.get("shrine").meters["danger"],
        "darkness": sim.get("shrine").meters["darkness"],
        "awakened": sim.get("source").meters["disturbed"] >= THRESHOLD,
    }


def _do_forbidden(world: World, source: Entity, narrate: bool = True) -> None:
    source.meters["disturbed"] += 1
    source.meters["glow_spilled"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, elder: Entity, sanctuary: Sanctuary, source: Source) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In the old days, when hills still listened, {child.id} walked {sanctuary.path} "
        f"with {child.pronoun('possessive')} {elder.title_word}."
    )
    world.say(
        f"{sanctuary.sky} {sanctuary.source_line} {source.glow}."
    )
    world.say(
        f"{sanctuary.need_line} {child.id} stared upward and thought the shrine looked full of sleeping treasure."
    )


def need_light(world: World, child: Entity, elder: Entity, sanctuary: Sanctuary) -> None:
    child.memes["desire"] += 1
    world.say(
        f'"If we had a little light before the moon climbed higher," {child.id} said, '
        f'"we could walk home without stumbling."'
    )
    world.say(
        f'{elder.title_word.capitalize()} smiled, but kept {elder.pronoun("possessive")} voice low. '
        f'"At a holy place, we ask before we take."'
    )


def tempt(world: World, child: Entity, forbidden: Forbidden, source: Source) -> None:
    child.memes["nerve"] += 1
    world.say(
        f"{child.id} looked at {source.the} and whispered, {forbidden.grab_line}"
    )
    world.say(
        f"For one bright heartbeat, the shortcut seemed wiser than waiting."
    )


def warn(world: World, child: Entity, elder: Entity, forbidden: Forbidden, source: Source) -> None:
    pred = predict_disturbance(world, "source")
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_darkness"] = pred["darkness"]
    child.memes["caution"] += 1
    extra = ""
    if child.memes["caution"] >= 6:
        extra = f" {child.id} knew the old stories were seldom empty."
    world.say(
        f'{elder.title_word.capitalize()} touched {child.pronoun("possessive")} shoulder. '
        f'"Do not {forbidden.touch_word} {source.the}," {elder.pronoun()} warned. '
        f'"{forbidden.warning} {source.The} is kept by {source.guardian}."{extra}'
    )


def defy(world: World, child: Entity, forbidden: Forbidden) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Only for a moment," {child.id} said, and reached out anyway.'
    )


def back_down(world: World, child: Entity, elder: Entity, forbidden: Forbidden, source: Source) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id}'s hand stopped in the air. The warning felt older than the stones, "
        f"and {child.pronoun()} let the thought of {forbidden.label} go."
    )
    world.say(
        f"Instead, {child.pronoun()} stepped back from {source.the} and waited beside "
        f"{elder.title_word}."
    )


def disturb(world: World, child: Entity, forbidden: Forbidden, source_ent: Entity, source: Source) -> None:
    _do_forbidden(world, source_ent)
    world.say(
        f"The moment {child.id} {forbidden.touch_word} {source.the}, a surprise leapt out of the silence. "
        f"{source.stir_text}"
    )


def alarm(world: World, child: Entity, elder: Entity, source: Source) -> None:
    world.say(
        f'"{elder.title_word.capitalize()}!" {child.id} cried. "The {source.label} is waking!"'
    )


def calm_success(world: World, elder: Entity, response: Response, source_ent: Entity, source: Source) -> None:
    source_ent.meters["disturbed"] = 0.0
    world.get("shrine").meters["danger"] = 0.0
    world.get("shrine").meters["darkness"] = 0.0
    world.say(
        f"{elder.title_word.capitalize()} did not run. {elder.pronoun().capitalize()} {response.text.replace('{source}', source.label)}."
    )
    world.say(
        f"At once the air softened, and {source.the} settled back into its patient glow."
    )


def lesson(world: World, child: Entity, elder: Entity, forbidden: Forbidden) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["love"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'Then {elder.title_word} drew {child.id} close. '
        f'"Magic is not cruel," {elder.pronoun()} said, "but greedy hands wake what careful hands could have honored. '
        f'Remember this: {forbidden.label} must never be taken by snatching."'
    )
    world.say(
        f"{child.id} nodded, still trembling a little, and promised to ask before touching holy things again."
    )


def safe_gift(world: World, child: Entity, elder: Entity, safe1: SafeLight, safe2: SafeLight) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    world.say(
        f"On the next evening, {elder.title_word} brought {safe1.phrase} and {safe2.phrase}. "
        f"One {safe1.shine}, and the other {safe2.shine}."
    )
    world.say(
        f'"These are for walking paths," {elder.pronoun()} said. "Sacred light is greeted. Household light is carried."'
    )
    world.say(
        f"{child.id} held them carefully and went down the hill without reaching for any sleeping wonder."
    )


def calm_fail(world: World, elder: Entity, response: Response, source_ent: Entity, source: Source) -> None:
    shrine = world.get("shrine")
    shrine.meters["danger"] += 1
    shrine.meters["darkness"] += 1
    source_ent.meters["disturbed"] += 1
    world.say(
        f"{elder.title_word.capitalize()} {response.fail.replace('{source}', source.label)}."
    )
    world.say(
        f"But the unrest only widened. The shrine wind turned cold, and {source.the} lost its gentle glow."
    )


def dark_ending(world: World, child: Entity, elder: Entity, sanctuary: Sanctuary) -> None:
    child.memes["fear"] += 1
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f"That night the people of the valley lit no songs on their doorsteps, for the hill stayed dark."
    )
    world.say(
        f"{child.id} walked home beside {elder.title_word} under a plain black sky, and every stone on {sanctuary.path} "
        f"felt like part of the warning."
    )
    world.say(
        f"From then on, {child.pronoun()} never called a shortcut clever just because it glittered."
    )


def tell(
    sanctuary: Sanctuary,
    forbidden: Forbidden,
    source: Source,
    lights: tuple[SafeLight, SafeLight],
    response: Response,
    hero_name: str = "Nia",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
    trust: int = 7,
) -> World:
    world = World()
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="child",
        traits=[trait],
        attrs={"trust": trust},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    shrine = world.add(Entity(
        id="shrine",
        type="place",
        label=sanctuary.place,
        attrs={"path": sanctuary.path},
    ))
    source_ent = world.add(Entity(
        id="source",
        type="source",
        label=source.label,
        spirit_bound=source.spirit_bound,
        gives_light=True,
        wild_magic=True,
    ))

    child.memes["nerve"] = NERVE_INIT
    child.memes["caution"] = initial_caution(trait)
    child.memes["trust"] = float(trust)
    shrine.meters["danger"] = 0.0
    shrine.meters["darkness"] = 0.0
    source_ent.meters["disturbed"] = 0.0
    source_ent.meters["glow_spilled"] = 0.0

    opening(world, child, elder, sanctuary, source)
    need_light(world, child, elder, sanctuary)

    world.para()
    tempt(world, child, forbidden, source)
    warn(world, child, elder, forbidden, source)

    resisted = would_resist(elder_type, trait, trust)
    if resisted:
        back_down(world, child, elder, forbidden, source)
        world.para()
        safe_gift(world, child, elder, lights[0], lights[1])
        severity = 0
        calmed = True
    else:
        defy(world, child, forbidden)
        world.para()
        disturb(world, child, forbidden, source_ent, source)
        alarm(world, child, elder, source)
        severity = spirit_severity(source, delay)
        source_ent.meters["severity"] = float(severity)
        calmed = is_calmed(response, source, delay)

        world.para()
        if calmed:
            calm_success(world, elder, response, source_ent, source)
            lesson(world, child, elder, forbidden)
            world.para()
            safe_gift(world, child, elder, lights[0], lights[1])
        else:
            calm_fail(world, elder, response, source_ent, source)
            dark_ending(world, child, elder, sanctuary)

    outcome = "averted" if resisted else ("calmed" if calmed else "darkened")
    world.facts.update(
        child=child,
        elder=elder,
        sanctuary=sanctuary,
        forbidden=forbidden,
        source_cfg=source,
        source=source_ent,
        lights=lights,
        response=response,
        delay=delay,
        severity=severity,
        disturbed=source_ent.meters["glow_spilled"] >= THRESHOLD,
        outcome=outcome,
        trust=trust,
    )
    return world


SANCTUARIES = {
    "moon_grove": Sanctuary(
        id="moon_grove",
        place="the moon grove",
        path="the white path above the cedar roots",
        sky="Above them the leaves hardly moved, and among them hung moon-fruit in a kiss-dim silver, like stars remembering how to sleep.",
        source_line="The oldest boughs bowed over a round altar of stone,",
        need_line="The valley below was waiting for night, and the last of the daylight was thinning.",
        tags={"moon", "grove"},
    ),
    "star_well": Sanctuary(
        id="star_well",
        place="the star well",
        path="the worn steps circling the old well",
        sky="The well court lay quiet under dusk, and little sparks drifted over the water in a kiss-dim shimmer.",
        source_line="At the center stood a black well ringed with carved stones,",
        need_line="Far below, the first cooking fires were waking in the valley, but the hill itself had gone dim.",
        tags={"star", "well"},
    ),
    "shell_cave": Sanctuary(
        id="shell_cave",
        place="the shell cave",
        path="the tide-worn stairs inside the cliff",
        sky="Inside the cave the walls held pearl-light, kiss-dim and soft, as if the sea had learned to whisper in silver.",
        source_line="In a niche above the tide line rested the old shrine-shells,",
        need_line="Outside, the sea was darkening, and the path home would soon be slick and shadowed.",
        tags={"sea", "cave"},
    ),
}

FORBIDDEN = {
    "pluck": Forbidden(
        id="pluck",
        label="sacred light",
        phrase="pluck one for a quick lamp",
        grab_line='"I could just pluck one and carry it home,"',
        warning="What is taken before it is greeted turns restless.",
        touch_word="plucked",
        makes_magic=True,
        tags={"respect", "magic"},
    ),
    "cup": Forbidden(
        id="cup",
        label="holy glow",
        phrase="cup it in bare hands",
        grab_line='"I could cup the glow in my hands,"',
        warning="Holy glow does not like to be closed inside fists.",
        touch_word="cupped",
        makes_magic=True,
        tags={"respect", "magic"},
    ),
    "hide": Forbidden(
        id="hide",
        label="shrine light",
        phrase="hide it in a sleeve",
        grab_line='"I could hide a little light in my sleeve,"',
        warning="A hidden blessing grows wild instead of useful.",
        touch_word="snatched",
        makes_magic=True,
        tags={"respect", "magic"},
    ),
}

SOURCES = {
    "moon_fruit": Source(
        id="moon_fruit",
        label="moon-fruit",
        the="the moon-fruit",
        resting="on the oldest branch",
        glow="Each fruit held its light deep inside, as if dawn had been folded into milk.",
        guardian="the white moth spirits",
        stir_text="White moth spirits burst from the leaves in a spinning cloud, and the silver on the branch ran like water.",
        spread=2,
        spirit_bound=True,
        tags={"moon_fruit", "moth", "spirit"},
    ),
    "well_star": Source(
        id="well_star",
        label="well-star",
        the="the well-star",
        resting="above the dark water",
        glow="It floated over the water with the steady shine of a promise kept for generations.",
        guardian="the deep-water whisper",
        stir_text="The well-star shook, and a whisper rose from the shaft below, circling the stones like a voice without a mouth.",
        spread=1,
        spirit_bound=True,
        tags={"well_star", "well", "spirit"},
    ),
    "pearl_shell": Source(
        id="pearl_shell",
        label="pearl-shell",
        the="the pearl-shell",
        resting="in the salt-worn niche",
        glow="Its inner curve burned softly with sea-light, pale and watchful.",
        guardian="the ash-blue gull spirits",
        stir_text="Ash-blue gull spirits wheeled through the cave in a storm of cries, and the pearl-light flashed against the rock.",
        spread=3,
        spirit_bound=True,
        tags={"shell", "gull", "spirit"},
    ),
    "plain_stone": Source(
        id="plain_stone",
        label="plain stone",
        the="the plain stone",
        resting="beside the path",
        glow="It had no light in it at all, only old rain marks.",
        guardian="nothing but silence",
        stir_text="Nothing happened.",
        spread=0,
        spirit_bound=False,
        tags={"stone"},
    ),
}

SAFE_LIGHTS = {
    "reed_lamp": SafeLight(
        id="reed_lamp",
        label="reed lamp",
        phrase="a little reed lamp",
        shine="burned with a homely yellow ring",
        tags={"lamp"},
    ),
    "shell_lantern": SafeLight(
        id="shell_lantern",
        label="shell lantern",
        phrase="a shell lantern",
        shine="glowed through carved slits like warm honey",
        tags={"lantern"},
    ),
    "wax_candle": SafeLight(
        id="wax_candle",
        label="wax candle",
        phrase="a wax candle in a clay cup",
        shine="stood steady even when the wind touched it",
        tags={"candle"},
    ),
    "glow_bowl": SafeLight(
        id="glow_bowl",
        label="glow bowl",
        phrase="a little bowl of safe fire",
        shine="made a neat circle on the stones",
        tags={"bowl_light"},
    ),
}

RESPONSES = {
    "naming_song": Response(
        id="naming_song",
        sense=3,
        power=3,
        text="sang the old naming song and laid both palms open beneath the {source} until the stirred spirits remembered their places",
        fail="sang the old naming song, but the {source} had already grown too restless to heed it",
        qa_text="sang the old naming song to settle the spirits around the source",
        tags={"song", "spirit"},
    ),
    "mirror_bowl": Response(
        id="mirror_bowl",
        sense=3,
        power=2,
        text="set down a mirror bowl of spring water so the frightened magic could see itself and grow still again",
        fail="set down a mirror bowl of spring water, but the {source} was shaking too hard for the reflection to calm it",
        qa_text="used a mirror bowl of spring water to calm the frightened magic",
        tags={"water_bowl", "spirit"},
    ),
    "bread_offering": Response(
        id="bread_offering",
        sense=2,
        power=1,
        text="crumbled a round of bread on the altar and spoke the peace-words until the smallest fluttering eased",
        fail="offered bread and peace-words, but the {source} had woken more than bread could soothe",
        qa_text="made a bread offering and spoke peace-words",
        tags={"offering", "spirit"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        power=0,
        text="shouted at the spirits to go away",
        fail="shouted at the spirits, which only made the shrine echo harder",
        qa_text="shouted at the spirits",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nia", "Asha", "Mira", "Tala", "Ira", "Luma", "Sena", "Riva"]
BOY_NAMES = ["Oren", "Sami", "Tarin", "Ivo", "Daro", "Milan", "Rian", "Tomas"]
TRAITS = ["careful", "patient", "reverent", "curious", "bold", "restless", "gentle"]
ELDERS = ["grandmother", "grandfather", "keeper", "priestess"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for sanctuary_id in SANCTUARIES:
        for forbidden_id, forbidden in FORBIDDEN.items():
            for source_id, source in SOURCES.items():
                if hazard_at_risk(forbidden, source):
                    combos.append((sanctuary_id, forbidden_id, source_id))
    return combos


@dataclass
class StoryParams:
    sanctuary: str
    forbidden: str
    source: str
    light1: str
    light2: str
    response: str
    hero_name: str
    hero_gender: str
    elder_type: str
    trait: str
    delay: int = 0
    trust: int = 7
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
    "moon_fruit": [
        (
            "What is moon-fruit in this kind of myth?",
            "Moon-fruit is a magical fruit said to hold a little stored light. In myths, such things are often guarded and must be approached with respect.",
        )
    ],
    "well_star": [
        (
            "What is a well-star?",
            "A well-star is a magical light hovering over a sacred well. Stories treat it like a holy sign, not an ordinary lamp.",
        )
    ],
    "shell": [
        (
            "Why might a pearl-shell glow in a myth?",
            "A glowing pearl-shell is a magical object tied to sea spirits or old blessings. Myths often use shining shells to show that the sea remembers ancient powers.",
        )
    ],
    "spirit": [
        (
            "Why should people be careful with spirits in stories?",
            "Spirits in stories guard places, gifts, or promises. If people act greedily or rudely, the spirits may grow restless and cause trouble.",
        )
    ],
    "song": [
        (
            "Why would a song calm magic in a myth?",
            "In myths, names and songs can remind magic what it is meant to do. A calming song can restore order because it treats the magic with respect instead of force.",
        )
    ],
    "water_bowl": [
        (
            "Why might a bowl of still water matter in a magical story?",
            "Still water can reflect things clearly, so many old stories use it for truth, calm, and seeing rightly. That makes it a fitting way to soothe frightened magic.",
        )
    ],
    "offering": [
        (
            "What is an offering?",
            "An offering is a gift given with respect, often at a holy place. In stories, offerings show humility and thanks.",
        )
    ],
    "lamp": [
        (
            "What is a reed lamp?",
            "A reed lamp is a small hand-carried lamp made for ordinary light. It helps people walk safely without touching sacred magic.",
        )
    ],
    "lantern": [
        (
            "What is a lantern for?",
            "A lantern carries safe light from place to place. It is useful because it is meant to be carried by people.",
        )
    ],
    "candle": [
        (
            "What does a candle do in a story?",
            "A candle gives a small steady light. It is an ordinary tool, not a sacred wonder.",
        )
    ],
    "bowl_light": [
        (
            "What is a bowl of safe fire?",
            "It is a little household fire kept in a bowl or cup so people can carry light carefully. Stories use it to contrast ordinary help with forbidden magic.",
        )
    ],
    "respect": [
        (
            "Why is respect important in myths?",
            "Myths often teach that power should be met with humility. Respect keeps people from turning gifts into dangers.",
        )
    ],
    "magic": [
        (
            "Why can magical shortcuts be dangerous?",
            "A shortcut can ignore the rules that keep magic gentle and balanced. When someone grabs at power too quickly, the trouble may be bigger than the gain.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "moon_fruit",
    "well_star",
    "shell",
    "spirit",
    "song",
    "water_bowl",
    "offering",
    "lamp",
    "lantern",
    "candle",
    "bowl_light",
    "respect",
    "magic",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    source = f["source_cfg"]
    forbidden = f["forbidden"]
    lights = f["lights"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short myth for a 3-to-5-year-old that includes the word "kiss-dim" and tells of a child who almost grabs sacred light, but listens to an elder in time.',
            f"Tell a magical cautionary story where {child.id} wants to {forbidden.phrase} from {source.the}, yet stops after hearing a wise warning from {elder.title_word}.",
            f"Write a gentle mythic story with surprise, sacred magic, and a safe ending where ordinary lamps are chosen instead of a dangerous shortcut.",
        ]
    if outcome == "darkened":
        return [
            f'Write a cautionary myth for a 3-to-5-year-old that includes the word "kiss-dim", a sacred light, and a dark consequence after a child ignores a warning.',
            f"Tell a magical surprise story where {child.id} reaches for {source.the}, wakes its guardian, and learns too late that holy things should not be snatched.",
            f"Write a mythic story with a sad ending in which an elder tries to calm offended magic, but the hill stays dark for the night.",
        ]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "kiss-dim", a sacred glow, and a warning about greedy hands.',
        f"Tell a magical cautionary story where {child.id} disturbs {source.the}, a wise {elder.title_word} calms the trouble, and the child learns to respect holy light.",
        f"Write a myth-style story with surprise, living magic, and an ending where {lights[0].label} and {lights[1].label} replace a dangerous shortcut.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    sanctuary = f["sanctuary"]
    forbidden = f["forbidden"]
    source = f["source_cfg"]
    response = f["response"]
    light1, light2 = f["lights"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who wanted quick light, and {child.pronoun('possessive')} {elder.title_word}, who knew the old ways of the shrine.",
        ),
        (
            "Where does the story happen?",
            f"It happens at {sanctuary.place}. The place feels holy and old, which is why the warning matters so much.",
        ),
        (
            f"Why did {child.id} want to touch {source.the}?",
            f"{child.id} wanted a little light for the walk home and thought a shortcut would help. The shining magic made taking it seem easy for one moment.",
        ),
        (
            f"What warning did the {elder.title_word} give?",
            f"{elder.title_word.capitalize()} warned that {source.the} was guarded and that sacred light must be greeted, not grabbed. The warning came before the trouble, which makes the story cautionary.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {child.id} stop before touching the sacred light?",
                f"{child.id} believed the elder's warning and pulled back in time. Trust and caution were stronger than the wish for a quick prize.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with {light1.phrase} and {light2.phrase} lighting the way home. That ending shows {child.id} learned the difference between sacred wonder and ordinary help.",
            )
        )
    elif f["outcome"] == "calmed":
        qa.append(
            (
                f"What surprising thing happened when {child.id} touched {source.the}?",
                f"{source.guardian.capitalize()} woke and the shrine suddenly changed. The surprise came because the magic had been sleeping quietly until it was handled the wrong way.",
            )
        )
        qa.append(
            (
                f"How did the {elder.title_word} fix the problem?",
                f"{elder.title_word.capitalize()} {response.qa_text}. That worked because the elder used respect and old knowledge instead of grabbing harder at the magic.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that shining things are not always meant to be taken. Sacred gifts must be approached carefully, or they can become dangerous very fast.",
            )
        )
    else:
        qa.append(
            (
                f"Could the {elder.title_word} calm the trouble in time?",
                f"No. {elder.title_word.capitalize()} tried, but the magic had grown too restless, so the hill stayed dark that night.",
            )
        )
        qa.append(
            (
                "What was the consequence at the end?",
                f"The valley lost the hill's holy glow for the night, and everyone walked under a plain dark sky. That ending proves the warning was true and the shortcut was not worth it.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn from the dark night?",
                f"{child.id} learned that a glittering shortcut can bring a bigger loss. After that, {child.pronoun()} stopped treating sacred things like toys or prizes.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["forbidden"].tags) | set(f["source_cfg"].tags)
    outcome = f["outcome"]
    if outcome == "calmed":
        tags |= set(f["response"].tags)
        for light in f["lights"]:
            tags |= set(light.tags)
    elif outcome == "averted":
        for light in f["lights"]:
            tags |= set(light.tags)
    else:
        tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("spirit_bound", ent.spirit_bound),
            ("wild_magic", ent.wild_magic),
            ("gives_light", ent.gives_light),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sanctuary="moon_grove",
        forbidden="pluck",
        source="moon_fruit",
        light1="reed_lamp",
        light2="shell_lantern",
        response="naming_song",
        hero_name="Nia",
        hero_gender="girl",
        elder_type="grandmother",
        trait="careful",
        delay=0,
        trust=9,
    ),
    StoryParams(
        sanctuary="star_well",
        forbidden="cup",
        source="well_star",
        light1="wax_candle",
        light2="glow_bowl",
        response="mirror_bowl",
        hero_name="Oren",
        hero_gender="boy",
        elder_type="keeper",
        trait="curious",
        delay=0,
        trust=5,
    ),
    StoryParams(
        sanctuary="shell_cave",
        forbidden="hide",
        source="pearl_shell",
        light1="reed_lamp",
        light2="wax_candle",
        response="bread_offering",
        hero_name="Tala",
        hero_gender="girl",
        elder_type="priestess",
        trait="bold",
        delay=1,
        trust=4,
    ),
    StoryParams(
        sanctuary="moon_grove",
        forbidden="cup",
        source="moon_fruit",
        light1="glow_bowl",
        light2="shell_lantern",
        response="naming_song",
        hero_name="Rian",
        hero_gender="boy",
        elder_type="grandfather",
        trait="patient",
        delay=0,
        trust=8,
    ),
]


def explain_rejection(forbidden: Forbidden, source: Source) -> str:
    if not source.spirit_bound:
        return (
            f"(No story: {source.the} is not spirit-bound, so {forbidden.phrase} would not wake any magical trouble. "
            f"Pick a sacred source like moon_fruit, well_star, or pearl_shell.)"
        )
    if not forbidden.makes_magic:
        return (
            f"(No story: {forbidden.label} would not disturb sacred magic here.)"
        )
    return "(No story: this combination has no meaningful magical hazard.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too weak or foolish for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_resist(params.elder_type, params.trait, params.trust):
        return "averted"
    return "calmed" if is_calmed(RESPONSES[params.response], SOURCES[params.source], params.delay) else "darkened"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(F, S) :- makes_magic(F), spirit_bound(S).
sensible(R)  :- response(R), sense(R, V), sense_min(M), V >= M.
valid(P, F, S) :- sanctuary(P), forbidden(F), source(S), hazard(F, S).

% --- resistance model ------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

elder_bonus(2) :- elder_type(grandmother).
elder_bonus(2) :- elder_type(grandfather).
elder_bonus(2) :- elder_type(priestess).
elder_bonus(1) :- elder_type(keeper).

authority(C * 4 + E * 4 + Tr) :- init_caution(C), elder_bonus(E), trust(Tr).
resisted :- authority(A), nerve_limit(N), A > N.

% --- disturbance outcome ---------------------------------------------------
severity(Sp + D) :- chosen_source(S), spread(S, Sp), delay(D).
resp_power(P)    :- chosen_response(R), power(R, P).
calmed           :- resp_power(P), severity(V), P >= V.

outcome(averted)  :- resisted.
outcome(calmed)   :- not resisted, calmed.
outcome(darkened) :- not resisted, not calmed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sanctuary_id in SANCTUARIES:
        lines.append(asp.fact("sanctuary", sanctuary_id))
    for forbidden_id, forbidden in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", forbidden_id))
        if forbidden.makes_magic:
            lines.append(asp.fact("makes_magic", forbidden_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.spirit_bound:
            lines.append(asp.fact("spirit_bound", source_id))
        lines.append(asp.fact("spread", source_id, source.spread))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for light_id in SAFE_LIGHTS:
        lines.append(asp.fact("light", light_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_limit", int((NERVE_INIT + 1.0) * 4)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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

    scenario = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("elder_type", params.elder_type),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a mythic child, sacred light, and a cautionary magical surprise."
    )
    ap.add_argument("--sanctuary", choices=SANCTUARIES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--elder", dest="elder_type", choices=ELDERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the magic grows restless before the elder acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and not SOURCES[args.source].spirit_bound:
        forbidden = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        raise StoryError(explain_rejection(forbidden, SOURCES[args.source]))
    if args.forbidden and args.source:
        forbidden = FORBIDDEN[args.forbidden]
        source = SOURCES[args.source]
        if not hazard_at_risk(forbidden, source):
            raise StoryError(explain_rejection(forbidden, source))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.sanctuary is None or combo[0] == args.sanctuary)
        and (args.forbidden is None or combo[1] == args.forbidden)
        and (args.source is None or combo[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sanctuary_id, forbidden_id, source_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    hero_name, hero_gender = _pick_child(rng)
    elder_type = args.elder_type or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trust = rng.randint(2, 10)

    return StoryParams(
        sanctuary=sanctuary_id,
        forbidden=forbidden_id,
        source=source_id,
        light1=light1,
        light2=light2,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        trait=trait,
        delay=delay,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        sanctuary = SANCTUARIES[params.sanctuary]
        forbidden = FORBIDDEN[params.forbidden]
        source = SOURCES[params.source]
        light1 = SAFE_LIGHTS[params.light1]
        light2 = SAFE_LIGHTS[params.light2]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]}.)") from err

    if not hazard_at_risk(forbidden, source):
        raise StoryError(explain_rejection(forbidden, source))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.delay not in {0, 1, 2}:
        raise StoryError("(Invalid delay: choose 0, 1, or 2.)")

    world = tell(
        sanctuary=sanctuary,
        forbidden=forbidden,
        source=source,
        lights=(light1, light2),
        response=response,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        elder_type=params.elder_type,
        trait=params.trait,
        delay=params.delay,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sanctuary, forbidden, source) combos:\n")
        for sanctuary_id, forbidden_id, source_id in combos:
            print(f"  {sanctuary_id:11} {forbidden_id:8} {source_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### {params.hero_name}: {params.forbidden} at {params.sanctuary} "
                f"({params.source}, {params.response}, {outcome_of(params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
