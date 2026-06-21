#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py
============================================================================

A standalone story world for a breezy comedy tale: two children run a silly fair
booth, one child wants to open it fast and make a prop twirl, a brief bully-ish
teasing moment pushes aside a sensible warning, and a grown-up either fixes the
wind problem or arrives too late.

The world is small on purpose:
- a booth theme (jokes / magic / dance)
- a twirling prop
- a floppy booth part that can catch wind
- a sensible or weak way to batten it down
- a small amount of background social state that decides whether the warning is
  obeyed, ignored, or ignored too long

The ending can be:
- averted: they listen and batten the booth down before anything blows loose
- contained: the booth starts to fail, but a grown-up secures it in time
- blown: the fix is too weak or too late, and the booth collapses in a funny,
  sad, messy bad ending

Run it
------
    python storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py
    python storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py --theme magic --target awning
    python storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py --target brick_wall
    python storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py --response tape
    python storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py --all --qa
    python storyworlds/worlds/gpt-5.4/twirl_bully_batten_humor_bad_ending_problem.py --verify
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
BRASH_INIT = 6.0
ORDERLY_TRAITS = {"orderly", "careful", "steady", "thoughtful"}


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
    wind_catch: bool = False
    twirls: bool = False
    # physical / emotional state
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
class Theme:
    id: str
    booth: str
    opening: str
    joke_line: str
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
class TwirlProp:
    id: str
    label: str
    phrase: str
    twirl_line: str
    laugh_line: str
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
class Target:
    id: str
    label: str
    the: str
    detail: str
    catch_phrase: str
    severity: int = 2
    wind_catch: bool = True
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"showoff", "helper"}]

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


def _r_wind_tugs(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("gust", 0) < THRESHOLD:
        return out
    for ent in list(world.entities.values()):
        if not ent.wind_catch:
            continue
        if ent.meters["loose"] < THRESHOLD:
            continue
        sig = ("wind_tugs", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["flapping"] += 1
        world.get("booth").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["alarm"] += 1
        out.append("__flap__")
    return out


def _r_flap_scatter(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["flapping"] < THRESHOLD:
            continue
        sig = ("scatter", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("prop").meters["wobble"] += 1
        world.get("booth").meters["mess"] += 1
        out.append("__scatter__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wind_tugs", tag="physical", apply=_r_wind_tugs),
    Rule(name="flap_scatter", tag="physical", apply=_r_flap_scatter),
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


def target_at_risk(target: Target) -> bool:
    return target.wind_catch


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def gust_force(target: Target, delay: int) -> int:
    return target.severity + delay


def is_held(response: Response, target: Target, delay: int) -> bool:
    return response.power >= gust_force(target, delay)


def initial_order(trait: str) -> float:
    return 5.0 if trait in ORDERLY_TRAITS else 3.0


def would_avert(relation: str, showoff_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > showoff_age
    authority = (initial_order(trait) + 1.0) + (4.0 if helper_older else 0.0)
    return helper_older and authority > BRASH_INIT


def predict_flap(world: World, target_id: str) -> dict:
    sim = world.copy()
    sim.facts["gust"] = 1.0
    tgt = sim.get(target_id)
    tgt.meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "flaps": tgt.meters["flapping"] >= THRESHOLD,
        "danger": sim.get("booth").meters["danger"],
        "mess": sim.get("booth").meters["mess"],
    }


def fair_setup(world: World, a: Entity, b: Entity, theme: Theme, prop: TwirlProp, target: Target) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On fair morning, {a.id} and {b.id} turned a folding table into {theme.booth}. "
        f"{theme.opening} Beside it stood {target.detail}."
    )
    world.say(
        f"{a.id} held {prop.phrase} and gave it a happy twirl. {prop.twirl_line} {theme.joke_line}"
    )


def windy_need(world: World, b: Entity, target: Target) -> None:
    world.facts["gust"] = 1.0
    world.say(
        f"But the day was breezy. Every little gust made {target.the} shiver and {target.catch_phrase}."
    )
    world.say(f'"Wait," {b.id} said. "Before we open, we should batten that down."')


def brag(world: World, a: Entity, b: Entity, prop: TwirlProp) -> None:
    a.memes["showing_off"] += 1
    world.say(
        f'"If the crowd sees this {prop.label} twirl, they will laugh before I even tell the first joke," '
        f"{a.id} said."
    )
    world.say("For one silly second, opening fast sounded more exciting than opening carefully.")


def warn(world: World, b: Entity, a: Entity, target: Target, grownup: Entity) -> None:
    pred = predict_flap(world, "target")
    b.memes["order"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_mess"] = pred["mess"]
    extra = ""
    if b.memes["order"] >= 6:
        extra = f" {b.pronoun().capitalize()} was already picturing napkins, signs, and jokes flying everywhere."
    world.say(
        f'{b.id} pointed at {target.the}. "If we do not batten it down first, the wind will grab it," '
        f"{b.pronoun()} said. \"Then the whole booth could wobble before {grownup.label_word} even gets here.\"{extra}"
    )


def tease(world: World, a: Entity, b: Entity) -> None:
    a.memes["mean"] += 1
    b.memes["hurt"] += 1
    world.say(
        f'"Do not be such a tiny bully about rules," {a.id} said with a grin that was trying to be funny '
        f"and landed a little mean instead."
    )
    world.say(
        f"{b.id} made a face. The joke did not feel much like a joke."
    )


def back_down(world: World, a: Entity, b: Entity, theme: Theme, grownup: Entity, prop: TwirlProp) -> None:
    a.memes["brash"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    target_ent = world.get("target")
    target_ent.meters["loose"] = 0.0
    world.say(
        f"But {b.id} was older, steadier, and impossible to rush. {a.id} huffed, looked at {target_ent.label}, "
        f"and laughed at {a.pronoun('possessive')} own hurry. \"Fine,\" {a.pronoun()} said. "
        f"\"We will batten it before we wow anybody.\""
    )
    world.say(
        f"They fetched {grownup.label_word}'s help, clipped everything snug, and only then did {a.id} twirl "
        f"{prop.phrase} again."
    )
    world.say(
        f"This time the booth stayed put, the jokes stayed on the sign, and {theme.closing}"
    )


def open_early(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f"{a.id} waved off the warning, planted one foot like a grand performer, and opened the booth anyway."
    )


def gust_hits(world: World, target_ent: Entity, target: Target, prop: TwirlProp) -> None:
    target_ent.meters["loose"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a_or_an(prop.label).capitalize()} {prop.label} began to twirl so fast it blurred. Then a harder gust hit. "
        f"{target.The} snapped, flapped, and yanked the whole booth sideways."
    )
    world.say(
        "A stack of paper noses skittered like tiny mice, and the joke jar tipped over with a clatter."
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, grownup: Entity) -> None:
    world.say(f'"{a.id}! {target.The}!" {b.id} yelped.')
    world.say(f'"{grownup.label_word.upper()}!"')


def rescue(world: World, grownup: Entity, response: Response, target_ent: Entity, target: Target, theme: Theme) -> None:
    target_ent.meters["flapping"] = 0.0
    target_ent.meters["loose"] = 0.0
    world.get("booth").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{grownup.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"In three breaths the booth stopped dancing, though one rubber chicken still bounced under the table. "
        f"Everyone laughed because it looked as if the chicken had tried to save the day."
    )
    world.say(
        f'"Next time," {grownup.label_word} said, smiling, "we solve the windy problem before the comedy starts."'
    )
    world.say(
        f"After that, {theme.closing}"
    )


def apology(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    b.memes["peace"] += 1
    world.say(
        f"{a.id} rubbed the back of {a.pronoun('possessive')} neck. "
        f'"I was trying to be funny," {a.pronoun()} said, "but I sounded like a bully. I am sorry."'
    )
    world.say(
        f'{b.id} nodded. "Funny should make people feel bigger, not smaller," {b.pronoun()} said.'
    )


def rescue_fail(world: World, grownup: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    if "booth" in world.entities:
        world.get("booth").meters["collapsed"] += 1
    target_ent.meters["flapping"] += 1
    body = response.fail.replace("{target}", target.label)
    world.say(
        f"{grownup.label_word.capitalize()} ran over and {body}."
    )
    world.say(
        f"But the gust was stronger than the plan. {target.The} whipped free, the sign spun around, "
        f"and the booth folded down with a floppy thump."
    )


def comic_loss(world: World, grownup: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["sad"] += 1
    world.say(
        "Nobody was hurt, but the whole funny booth became one big accidental joke."
    )
    world.say(
        f"A cream pie meant for the laughing game slid off a tray and landed on {grownup.label_word}'s shoe. "
        f"Even {grownup.label_word} had to blink and laugh once before sighing."
    )
    world.say(
        f"The fair helpers closed the booth for the day, and {theme.goal} had to wait for another time."
    )


def grim_but_gentle_lesson(world: World, grownup: Entity, a: Entity, b: Entity, target: Target) -> None:
    a.memes["sorry"] += 1
    b.memes["peace"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} crouched beside them. "A breezy problem does not look big at first," '
        f'{grownup.pronoun()} said, "but if you do not batten things down, small flaps turn into big messes."'
    )
    world.say(
        f"{a.id} swallowed hard and apologized for the mean joke and for not listening. "
        f"{b.id} accepted the apology, but both of them kept staring at {target.the}, now lying in a silly heap."
    )
    world.say(
        "After that, they never rushed the windy parts of a plan again."
    )


def a_or_an(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def tell(
    theme: Theme,
    prop: TwirlProp,
    target: Target,
    response: Response,
    showoff_name: str = "Max",
    showoff_gender: str = "boy",
    helper_name: str = "Lily",
    helper_gender: str = "girl",
    trait: str = "orderly",
    grownup_type: str = "teacher_woman",
    delay: int = 0,
    showoff_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id=showoff_name,
        kind="character",
        type=showoff_gender,
        role="showoff",
        age=showoff_age,
        attrs={"relation": relation},
        traits=["showy"],
    ))
    b = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grown-up",
    ))
    booth = world.add(Entity(id="booth", type="booth", label=theme.booth))
    prop_ent = world.add(Entity(id="prop", type="prop", label=prop.label, twirls=True))
    tgt = world.add(Entity(id="target", type="target", label=target.label, wind_catch=target.wind_catch))

    a.memes["brash"] = BRASH_INIT
    b.memes["trust"] = float(trust)
    b.memes["order"] = initial_order(trait)
    world.facts["pet"] = pet
    world.facts["relation"] = relation
    world.facts["gust"] = 0.0

    fair_setup(world, a, b, theme, prop, target)
    world.para()
    windy_need(world, b, target)
    brag(world, a, b, prop)
    warn(world, b, a, target, grownup)

    averted = would_avert(relation, showoff_age, helper_age, trait)

    if averted:
        world.para()
        back_down(world, a, b, theme, grownup, prop)
        severity = 0
        held = True
        outcome = "averted"
    else:
        tease(world, a, b)
        open_early(world, a, b)

        world.para()
        gust_hits(world, tgt, target, prop)
        alarm(world, b, a, target, grownup)

        severity = gust_force(target, delay)
        tgt.meters["severity"] = float(severity)
        held = is_held(response, target, delay)

        world.para()
        if held:
            rescue(world, grownup, response, tgt, target, theme)
            apology(world, a, b)
            outcome = "contained"
        else:
            rescue_fail(world, grownup, response, tgt, target)
            comic_loss(world, grownup, a, b, theme)
            grim_but_gentle_lesson(world, grownup, a, b, target)
            outcome = "blown"

    world.facts.update(
        showoff=a,
        helper=b,
        grownup=grownup,
        theme=theme,
        prop_cfg=prop,
        target_cfg=target,
        response=response,
        target=tgt,
        booth=booth,
        outcome=outcome,
        severity=severity,
        delay=delay,
        flapped=tgt.meters["flapping"] >= THRESHOLD or tgt.meters["loose"] >= THRESHOLD,
        apologized=a.memes["sorry"] >= THRESHOLD,
    )
    return world


THEMES = {
    "jokes": Theme(
        id="jokes",
        booth="a joke booth with squeaky props",
        opening="A crooked sign promised knock-knock jokes, paper mustaches, and one prize pickle for the bravest laugher.",
        joke_line="Even the table seemed ready to giggle.",
        goal="their joke booth debut",
        closing="the booth opened properly, and every laugh stayed where it belonged",
        tags={"jokes", "comedy"},
    ),
    "magic": Theme(
        id="magic",
        booth="a magic booth full of silly tricks",
        opening="A painted hat sat on the table beside a rabbit puppet with one ear folded backwards.",
        joke_line="It looked less like real magic and more like trouble in a top hat.",
        goal="their magic show",
        closing="the booth opened properly, and the fake magic finally looked almost real",
        tags={"magic", "comedy"},
    ),
    "dance": Theme(
        id="dance",
        booth="a dance booth with goofy prizes",
        opening="A hand-lettered sign promised wiggles, twirls, and the Golden Noodle Ribbon for the silliest move.",
        joke_line="The whole setup looked as if it had already started dancing without them.",
        goal="their dance contest",
        closing="the booth opened properly, and every twirl made the crowd clap instead of gasp",
        tags={"dance", "comedy"},
    ),
}

PROPS = {
    "pinwheel": TwirlProp(
        id="pinwheel",
        label="pinwheel",
        phrase="a rainbow pinwheel",
        twirl_line="It flashed red, blue, and yellow in a bright spinning blur.",
        laugh_line="Its wobble made everybody grin.",
        tags={"pinwheel", "wind"},
    ),
    "ribbon_baton": TwirlProp(
        id="ribbon_baton",
        label="ribbon baton",
        phrase="a shiny ribbon baton",
        twirl_line="The ribbon made curly loops in the air like a noodle trying ballet.",
        laugh_line="It looked grand and ridiculous at the same time.",
        tags={"ribbon", "twirl"},
    ),
    "silly_umbrella": TwirlProp(
        id="silly_umbrella",
        label="silly umbrella",
        phrase="a tiny silly umbrella",
        twirl_line="The striped top spun so quickly it looked amazed by itself.",
        laugh_line="It was exactly the sort of prop that made a crowd snort-laugh.",
        tags={"umbrella", "wind"},
    ),
}

TARGETS = {
    "awning": Target(
        id="awning",
        label="awning",
        the="the awning",
        detail="a striped awning with one lazy corner",
        catch_phrase="lift like it wanted to wave at the clouds",
        severity=3,
        wind_catch=True,
        tags={"awning", "wind"},
    ),
    "banner": Target(
        id="banner",
        label="banner",
        the="the banner",
        detail="a tall paper banner taped to two poles",
        catch_phrase="rattle and pull at the tape",
        severity=2,
        wind_catch=True,
        tags={"banner", "wind"},
    ),
    "curtain": Target(
        id="curtain",
        label="curtain",
        the="the curtain",
        detail="a velvet curtain hanging at the back of the booth",
        catch_phrase="balloon outward like a grumpy sail",
        severity=2,
        wind_catch=True,
        tags={"curtain", "wind"},
    ),
    "brick_wall": Target(
        id="brick_wall",
        label="brick wall",
        the="the brick wall",
        detail="a solid brick wall behind the booth",
        catch_phrase="do absolutely nothing at all",
        severity=0,
        wind_catch=False,
        tags={"wall"},
    ),
}

RESPONSES = {
    "clips": Response(
        id="clips",
        sense=3,
        power=3,
        text="snapped heavy clips onto the {target} and tied the loose side to the table leg",
        fail="snapped on heavy clips, but the {target} was already jerking too wildly to settle",
        qa_text="snapped heavy clips onto the {target} and tied it down",
        tags={"clips", "problem_solving"},
    ),
    "sandbags": Response(
        id="sandbags",
        sense=3,
        power=4,
        text="dropped two sandbags onto the base and fastened the {target} with cord",
        fail="lugged over sandbags, but the {target} had already pulled the booth half apart",
        qa_text="used sandbags and cord to hold the {target} steady",
        tags={"sandbags", "problem_solving"},
    ),
    "rope": Response(
        id="rope",
        sense=2,
        power=2,
        text="looped a rope around the {target} and cinched it tight to the frame",
        fail="threw a rope around the {target}, but the knot slipped under the hard gusts",
        qa_text="roped the {target} tightly to the frame",
        tags={"rope", "problem_solving"},
    ),
    "tape": Response(
        id="tape",
        sense=1,
        power=1,
        text="stuck more tape onto the {target}",
        fail="slapped on more tape, but the wind peeled it away at once",
        qa_text="tried to hold the {target} with tape",
        tags={"tape"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Finn", "Theo", "Eli", "Noah"]
TRAITS = ["orderly", "careful", "steady", "thoughtful", "curious", "cheery"]
PETS = ["the school turtle", "the class hamster", "", ""]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for prop_id in PROPS:
            for target_id, target in TARGETS.items():
                if target_at_risk(target):
                    combos.append((theme_id, prop_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    prop: str
    target: str
    response: str
    showoff: str
    showoff_gender: str
    helper: str
    helper_gender: str
    grownup: str
    trait: str
    delay: int = 0
    showoff_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    pet: str = ""
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
    "wind": [
        (
            "Why can wind be a problem for a booth?",
            "Wind pushes on loose cloth and paper, so a light booth part can flap, pull, or tear. That is why people tie things down before a gust turns a little wobble into a big mess.",
        )
    ],
    "pinwheel": [
        (
            "What is a pinwheel?",
            "A pinwheel is a toy with light blades that spin in moving air. It can twirl in even a small breeze.",
        )
    ],
    "ribbon": [
        (
            "Why does a ribbon baton twirl so much?",
            "A ribbon is light and floppy, so when a hand moves or wind blows, it makes loops and swirls. That is why it looks so lively in the air.",
        )
    ],
    "umbrella": [
        (
            "Why is a small umbrella funny in a windy story?",
            "A tiny umbrella flips and spins easily, so it can look very silly in a gust. Comedy often comes from objects acting fussier than people expect.",
        )
    ],
    "awning": [
        (
            "What is an awning?",
            "An awning is a cover that sticks out to make shade or shelter. If it is loose, wind can catch it like a sail.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long sign made from paper or cloth. Because it is broad and light, wind can tug at it easily.",
        )
    ],
    "curtain": [
        (
            "Why does a curtain puff in the wind?",
            "A curtain is hanging cloth, so air can blow into it and make it billow out. If it is not fastened well, it can flap hard.",
        )
    ],
    "clips": [
        (
            "Why do heavy clips help hold things down?",
            "Heavy clips pinch cloth or paper firmly onto a frame. They help stop flapping because they keep loose edges from lifting.",
        )
    ],
    "sandbags": [
        (
            "What do sandbags do?",
            "Sandbags add weight, so light things do not slide or tip so easily. They are useful when wind wants to push something around.",
        )
    ],
    "rope": [
        (
            "What does rope help with?",
            "Rope lets you tie something to a strong frame so it cannot wander off in the wind. A good knot matters, or the rope may slip.",
        )
    ],
    "bully": [
        (
            "What is a bully?",
            "A bully is someone who uses mean words or actions to make another person feel small. A joke stops being funny when it hurts on purpose.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking about what could help, and trying the best plan. Good problem solving often happens before the mess gets bigger.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "wind",
    "pinwheel",
    "ribbon",
    "umbrella",
    "awning",
    "banner",
    "curtain",
    "clips",
    "sandbags",
    "rope",
    "bully",
    "problem_solving",
]


def relation_pair(showoff: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if showoff.type == "boy" and helper.type == "boy":
            return "two brothers"
        if showoff.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["showoff"]
    b = f["helper"]
    theme = f["theme"]
    prop = f["prop_cfg"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short comedy story for a 3-to-5-year-old where two children open {theme.booth}, one wants to make a {prop.label} twirl right away, and the other insists they batten {target.the} down first.',
            f"Tell a funny near-miss story where {a.id} makes one bully-ish joke, then listens to {b.id} and fixes the windy problem before the booth opens.",
            f'Write a gentle problem-solving story that includes the words "twirl", "bully", and "batten" and ends with a safe, cheerful fair opening.',
        ]
    if outcome == "blown":
        return [
            f'Write a child-facing comedy with a bad ending where a windy booth problem is ignored, a prop starts to twirl, and {target.the} comes loose.',
            f"Tell a funny-but-cautionary story where {a.id} brushes off {b.id}'s warning, acts like a bully for one moment, and the booth collapses in a messy gust.",
            f'Write a problem-solving story that fails because the fix comes too late, using the words "twirl", "bully", and "batten".',
        ]
    return [
        f'Write a short comedy story where two children run {theme.booth}, a twirling {prop.label} helps start the fun, and a windy problem has to be solved fast.',
        f"Tell a gentle story where {a.id} ignores {b.id}'s warning for a moment, but a grown-up helps batten {target.the} down before the whole booth falls apart.",
        f'Write a story for a 3-to-5-year-old that includes the words "twirl", "bully", and "batten" and ends with laughter after a quick fix.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["showoff"]
    b = f["helper"]
    grownup = f["grownup"]
    theme = f["theme"]
    prop = f["prop_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    pair = relation_pair(a, b, f.get("relation", "friends"))
    pw = grownup.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were trying to open {theme.booth}. A grown-up came to help when the wind problem turned serious.",
        ),
        (
            "What made the booth feel funny at the start?",
            f"The children had silly props and planned jokes or tricks, and {a.id} was already making the {prop.label} twirl. That made the whole booth feel playful before the trouble started.",
        ),
        (
            f"Why did {b.id} want to batten {target.the} down first?",
            f"{b.id} could see that the breeze kept tugging at {target.the}. {b.pronoun().capitalize()} knew a loose, flappy part could shake the whole booth and scatter their funny things.",
        ),
        (
            f"Why did the word bully matter in this story?",
            f"{a.id} used the word during a mean little joke instead of listening kindly. That hurt {b.id}'s feelings, so the story shows that comedy should not turn into bullying.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed after {a.id} listened?",
                f"{a.id} stopped rushing and helped batten {target.the} down before opening. Because they solved the problem first, the booth stayed steady and the comedy could stay cheerful.",
            )
        )
    elif f["outcome"] == "contained":
        body = response.qa_text.replace("{target}", target.label)
        qa.append(
            (
                f"How did the grown-up solve the windy problem?",
                f"The {pw} {body}. That worked because the fix held {target.the} still before the gusts could pull the whole booth apart.",
            )
        )
        qa.append(
            (
                f"How did {a.id} act at the end?",
                f"{a.id} apologized for sounding like a bully and for not listening. The apology mattered because the real problem was not only the wind, but also the mean teasing that delayed the fix.",
            )
        )
    else:
        qa.append(
            (
                "What was the bad ending?",
                f"The booth collapsed and had to close for the day, even though nobody got hurt. The bad ending happened because they did not batten {target.the} down in time and the windy problem grew bigger than their plan.",
            )
        )
        qa.append(
            (
                f"What did {a.id} and {b.id} learn?",
                f"They learned to solve a breezy problem early instead of treating it like a joke. They also learned that acting like a bully, even for one minute, can stop people from working together when they need to.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"wind", "bully"}
    prop = f["prop_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    tags |= set(prop.tags)
    tags |= set(target.tags)
    if f["outcome"] != "averted":
        tags |= set(response.tags)
    if "problem_solving" in response.tags or f["outcome"] == "averted":
        tags.add("problem_solving")
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
        flags = []
        if e.wind_catch:
            flags.append("wind_catch")
        if e.twirls:
            flags.append("twirls")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="jokes",
        prop="pinwheel",
        target="awning",
        response="sandbags",
        showoff="Max",
        showoff_gender="boy",
        helper="Lily",
        helper_gender="girl",
        grownup="teacher_woman",
        trait="orderly",
        delay=0,
        showoff_age=6,
        helper_age=4,
        relation="siblings",
        trust=6,
        pet="the class hamster",
    ),
    StoryParams(
        theme="magic",
        prop="ribbon_baton",
        target="banner",
        response="clips",
        showoff="Mia",
        showoff_gender="girl",
        helper="Ben",
        helper_gender="boy",
        grownup="teacher_man",
        trait="careful",
        delay=0,
        showoff_age=5,
        helper_age=7,
        relation="siblings",
        trust=5,
        pet="",
    ),
    StoryParams(
        theme="dance",
        prop="silly_umbrella",
        target="curtain",
        response="rope",
        showoff="Theo",
        showoff_gender="boy",
        helper="Zoe",
        helper_gender="girl",
        grownup="mother",
        trait="cheery",
        delay=1,
        showoff_age=6,
        helper_age=5,
        relation="friends",
        trust=4,
        pet="the school turtle",
    ),
    StoryParams(
        theme="jokes",
        prop="pinwheel",
        target="awning",
        response="rope",
        showoff="Noah",
        showoff_gender="boy",
        helper="Ava",
        helper_gender="girl",
        grownup="father",
        trait="curious",
        delay=2,
        showoff_age=7,
        helper_age=5,
        relation="siblings",
        trust=3,
        pet="",
    ),
]


def explain_rejection(target: Target) -> str:
    if not target.wind_catch:
        return (
            f"(No story: {target.the} does not catch the wind, so there is no honest need to batten it down. "
            f"Pick an awning, banner, or curtain instead.)"
        )
    return "(No story: this target does not create a windy booth problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a sturdier fix such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.showoff_age, params.helper_age, params.trait):
        return "averted"
    contained = is_held(RESPONSES[params.response], TARGETS[params.target], params.delay)
    return "contained" if contained else "blown"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(Tg)       :- target(Tg), wind_catch(Tg).
sensible(R)      :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Th, P, Tg) :- theme(Th), prop(P), target(Tg), hazard(Tg).

% --- outcome model ---------------------------------------------------------
order_now(T)   :- trait(T), orderly_trait(T).
init_order(5)  :- trait(T), order_now(T).
init_order(3)  :- trait(T), not order_now(T).

helper_older   :- relation(siblings), showoff_age(SA), helper_age(HA), HA > SA.
bonus(4)       :- helper_older.
bonus(0)       :- not helper_older.
authority(O + 1 + B) :- init_order(O), bonus(B).
averted        :- helper_older, authority(A), brash_init(BR), A > BR.

severity(V + D) :- chosen_target(Tg), target_severity(Tg, V), delay(D).
resp_power(P)   :- chosen_response(R), power(R, P).
contained       :- resp_power(P), severity(S), P >= S.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(blown)     :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.wind_catch:
            lines.append(asp.fact("wind_catch", tid))
        lines.append(asp.fact("target_severity", tid, t.severity))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("brash_init", int(BRASH_INIT)))
    for tr in sorted(ORDERLY_TRAITS):
        lines.append(asp.fact("orderly_trait", tr))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("showoff_age", params.showoff_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a windy comedy booth, a twirl, a bully-ish joke, and the need to batten something down."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["mother", "father", "teacher_woman", "teacher_man"])
    ap.add_argument(
        "--delay",
        type=int,
        choices=[0, 1, 2],
        help="how long the gust gets to win before the grown-up fix; higher makes a bad ending more likely",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].wind_catch:
        raise StoryError(explain_rejection(TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.prop is None or c[1] == args.prop)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, prop, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    showoff, sg = _pick_kid(rng)
    helper, hg = _pick_kid(rng, avoid=showoff)
    grownup = args.grownup or rng.choice(["mother", "father", "teacher_woman", "teacher_man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    showoff_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(PETS)
    return StoryParams(
        theme=theme,
        prop=prop,
        target=target,
        response=response,
        showoff=showoff,
        showoff_gender=sg,
        helper=helper,
        helper_gender=hg,
        grownup=grownup,
        trait=trait,
        delay=delay,
        showoff_age=showoff_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not TARGETS[params.target].wind_catch:
        raise StoryError(explain_rejection(TARGETS[params.target]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        prop=PROPS[params.prop],
        target=TARGETS[params.target],
        response=RESPONSES[params.response],
        showoff_name=params.showoff,
        showoff_gender=params.showoff_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        grownup_type=params.grownup,
        delay=params.delay,
        showoff_age=params.showoff_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
        pet=params.pet,
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        emit(smoke_sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, prop, target) combos:\n")
        for theme, prop, target in combos:
            print(f"  {theme:8} {prop:14} {target}")
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
            header = (
                f"### {p.showoff} & {p.helper}: {p.prop} at {p.theme} booth "
                f"({p.target}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
