#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py
============================================================================

A standalone story world for a tiny superhero-style farm adventure: a child
wants to do an "elite" stunt around stacked hay, a wiser friend or sibling
warns them, and the story turns toward the lesson that real heroes choose the
safe plan.

Features from the seed:
- includes the words "elite" and "hay"
- uses sound effects in the prose
- includes inner monologue
- ends with a lesson learned

Run it
------
    python storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py
    python storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py --shortcut rope_swing --hazard frayed_rope
    python storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py --hazard loose_hay --response boast_pose
    python storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py --all
    python storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py --qa --json
    python storyworlds/worlds/gpt-5.4/elite_hay_sound_effects_inner_monologue_lesson.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "sensible"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Theme:
    id: str
    scene: str
    base_line: str
    titles: tuple[str, str]
    mission: str
    sendoff: str
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
class Shortcut:
    id: str
    label: str
    shout: str
    thought: str
    move_line: str
    accident_line: str
    base_risk: int
    applicable_hazards: set[str] = field(default_factory=set)
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
class Hazard:
    id: str
    label: str
    detail: str
    warning: str
    accident: str
    bonus: int
    applicable_shortcuts: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    place: str
    need: str
    safe_finish: str
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
        return [e for e in self.entities.values() if e.role in {"hero", "partner"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["wobbling"] < THRESHOLD:
            continue
        sig = ("wobble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "yard" in world.entities:
            world.get("yard").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__danger__")
    return out


def _r_tumble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    costume = world.entities.get("costume")
    if hero is None or costume is None:
        return out
    if hero.meters["slipped"] < THRESHOLD:
        return out
    sig = ("tumble", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    costume.meters["dusty"] += 1
    hero.memes["embarrassment"] += 1
    out.append("__dusty__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="tumble", tag="physical", apply=_r_tumble),
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


def hazard_at_risk(shortcut: Shortcut, hazard: Hazard) -> bool:
    return hazard.id in shortcut.applicable_hazards and shortcut.id in hazard.applicable_shortcuts


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def stunt_severity(shortcut: Shortcut, hazard: Hazard, delay: int) -> int:
    return shortcut.base_risk + hazard.bonus + delay


def is_controlled(response: Response, shortcut: Shortcut, hazard: Hazard, delay: int) -> bool:
    return response.power >= stunt_severity(shortcut, hazard, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > hero_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if partner_older else 0.0)
    return partner_older and authority > BRAVERY_INIT


def _do_stunt(world: World, hazard: Hazard, narrate: bool = True) -> None:
    hero = world.get("hero")
    stack = world.get("stack")
    hero.meters["slipped"] += 1
    stack.meters["wobbling"] += 1
    stack.meters["messy"] += 1
    propagate(world, narrate=narrate)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hazard = sim.facts["hazard"]
    _do_stunt(sim, hazard=hazard, narrate=False)
    return {
        "danger": sim.get("yard").meters["danger"],
        "slipped": sim.get("hero").meters["slipped"] >= THRESHOLD,
        "dusty": sim.get("costume").meters["dusty"] >= THRESHOLD,
    }


def opening(world: World, hero: Entity, partner: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    title_a, title_b = theme.titles
    world.say(
        f"After chores, {hero.id} and {partner.id} turned the barn into {theme.scene}. "
        f"{theme.base_line}"
    )
    world.say(
        f'"{title_a} {hero.id} and {title_b} {partner.id}!" {hero.id} cried. '
        f'"Today we {theme.mission}!"'
    )


def need(world: World, partner: Entity, goal: Goal) -> None:
    world.say(
        f"Up near {goal.place}, {goal.need}. The mission suddenly felt real."
    )
    world.say(
        f'{partner.id} pointed up. "There it is," {partner.pronoun()} said. '
        f'"We have to reach the {goal.label}."'
    )


def tempt(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["bravado"] += 1
    world.say(f'"{shortcut.shout}" {hero.id} said.')
    world.say(
        f'{hero.id} looked at the high hay and had a brave little thought: '
        f'"{shortcut.thought}"'
    )
    world.say("For a moment, the plan felt bright and thunder-fast.")


def warn(world: World, partner: Entity, hero: Entity, shortcut: Shortcut, hazard: Hazard, parent: Entity) -> None:
    pred = predict_trouble(world)
    partner.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["dusty"]:
        extra = f" {partner.pronoun().capitalize()} could almost hear the cape hit the hay with a soft fwump."
    world.say(
        f'{partner.id} frowned. "{hero.id}, wait. {hazard.warning} {shortcut.warning_line if hasattr(shortcut, "warning_line") else ""}"'
    )
    world.say(
        f'"{parent.label_word.capitalize()} said real heroes think first. If you try that, somebody could slip."{extra}'
    )


def defy(world: World, hero: Entity, partner: Entity, shortcut: Shortcut) -> None:
    hero.memes["defiance"] += 1
    older = hero.attrs.get("relation") == "siblings" and hero.age > partner.age
    if older:
        world.say(
            f'"I can do it," {hero.id} said. Because {hero.pronoun()} was the older one, '
            f"{partner.id} could not stop {hero.pronoun('object')} in time."
        )
    else:
        world.say(f'"I can do it," {hero.id} said, and dashed forward before {partner.id} could grab a sleeve.')


def back_down(world: World, hero: Entity, partner: Entity, theme: Theme, goal: Goal, response: Response, parent: Entity) -> None:
    hero.memes["bravery"] = 0.0
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'{hero.id} stopped with one boot on the hay bale. Inside, {hero.pronoun()} thought, '
        f'"Maybe elite heroes are the ones who do not show off."'
    )
    world.say(
        f'{hero.pronoun().capitalize()} climbed back down, and the two children went to get {parent.label_word} for a better plan.'
    )
    world.para()
    safe_finish(world, hero, partner, theme, goal, response, parent, averted=True)


def stunt(world: World, hero: Entity, shortcut: Shortcut, hazard: Hazard) -> None:
    _do_stunt(world, hazard=hazard, narrate=False)
    world.say(f"{shortcut.move_line} WHOOSH!")
    world.say(
        f"Then {hazard.accident} {shortcut.accident_line} FWUMP!"
    )


def alarm(world: World, partner: Entity, hero: Entity, parent: Entity) -> None:
    world.say(f'"{hero.id}!" {partner.id} gasped. "Hold still!"')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, goal: Goal, theme: Theme) -> None:
    hero = world.get("hero")
    stack = world.get("stack")
    hero.meters["slipped"] = 0.0
    world.get("yard").meters["danger"] = 0.0
    stack.meters["wobbling"] = 0.0
    body = response.text.replace("{goal}", goal.label)
    world.say(
        f"{parent.label_word.capitalize()} came fast and {body}."
    )
    world.say(
        f"In another minute, the {goal.label} was safe and the barn was quiet again except for a tiny rustle of hay."
    )
    world.say(
        f'{hero.id} let out a long breath and thought, "That did not feel elite at all. It felt lucky."'
    )
    world.facts["goal_reached"] = True
    world.facts["hero_rescued"] = True


def rescue_fail(world: World, parent: Entity, response: Response, goal: Goal) -> None:
    hero = world.get("hero")
    costume = world.get("costume")
    body = response.fail.replace("{goal}", goal.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f'{hero.id} tumbled into the hay instead. THUMP! The fall was soft, but {hero.pronoun("possessive")} cape came up dusty and crooked.'
    )
    hero.memes["fear"] += 1
    hero.memes["relief"] += 1
    costume.meters["dusty"] += 1
    world.facts["goal_reached"] = False
    world.facts["hero_rescued"] = False


def lesson(world: World, parent: Entity, hero: Entity, partner: Entity, response: Response) -> None:
    hero.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    hero.memes["love"] += 1
    partner.memes["love"] += 1
    hero.memes["fear"] = 0.0
    partner.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt in the hay and hugged them close. '
        f'"Strong hearts are good," {parent.pronoun()} said, "but the best heroes choose the safe plan first."'
    )
    world.say(
        f'{hero.id} nodded. "{response.id.replace("_", " ")} was smarter than showing off," {hero.pronoun()} said.'
    )


def afterglow(world: World, hero: Entity, partner: Entity, theme: Theme, goal: Goal) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"Soon they were back in the game, only slower and wiser. {goal.safe_finish}"
    )
    world.say(
        f"The barn no longer felt like a place for wild stunts. It felt like a headquarters where heroes made careful plans."
    )
    world.say(
        f"And when {hero.id} lifted {hero.pronoun('possessive')} chin, {hero.pronoun()} no longer wanted to look elite. "
        f"{hero.pronoun().capitalize()} wanted to be trustworthy."
    )
    world.say(theme.sendoff)


def safe_finish(
    world: World,
    hero: Entity,
    partner: Entity,
    theme: Theme,
    goal: Goal,
    response: Response,
    parent: Entity,
    averted: bool = False,
) -> None:
    body = response.text.replace("{goal}", goal.label)
    if averted:
        world.say(
            f"{parent.label_word.capitalize()} smiled, {body}, and showed them where to put their feet one at a time."
        )
        world.say(
            f"With the safe plan, {goal.safe_finish.lower()}"
        )
        world.say(
            f'{hero.id} grinned and thought, "That was quieter than a stunt, but it worked better."'
        )
    lesson(world, parent, hero, partner, response)
    afterglow(world, hero, partner, theme, goal)


def tell(
    theme: Theme,
    shortcut: Shortcut,
    hazard: Hazard,
    goal: Goal,
    response: Response,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    partner_name: str = "Jax",
    partner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    hero_age: int = 6,
    partner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    yard = world.add(Entity(id="yard", type="place", label="the barn yard"))
    stack = world.add(Entity(id="stack", type="hay", label="the hay stack"))
    costume = world.add(Entity(id="costume", type="cape", label="the cape"))

    hero.memes["bravery"] = BRAVERY_INIT
    partner.memes["caution"] = initial_caution(trait)
    partner.memes["trust"] = float(trust)
    world.facts["goal_reached"] = False
    world.facts["hero_rescued"] = False
    world.facts["predicted_danger"] = 0.0

    world.facts.update(
        theme=theme,
        shortcut=shortcut,
        hazard=hazard,
        goal=goal,
        response=response,
        relation=relation,
    )

    opening(world, hero, partner, theme)
    need(world, partner, goal)

    world.para()
    tempt(world, hero, shortcut)
    warn(world, partner, hero, shortcut, hazard, parent)

    averted = would_avert(relation, hero_age, partner_age, trait)
    severity = stunt_severity(shortcut, hazard, delay)
    contained = is_controlled(response, shortcut, hazard, delay)

    if averted:
        back_down(world, hero, partner, theme, goal, response, parent)
        outcome = "averted"
    else:
        defy(world, hero, partner, shortcut)
        world.para()
        stunt(world, hero, shortcut, hazard)
        alarm(world, partner, hero, parent)
        world.para()
        if contained:
            rescue(world, parent, response, goal, theme)
            lesson(world, parent, hero, partner, response)
            world.para()
            afterglow(world, hero, partner, theme, goal)
            outcome = "assisted"
        else:
            rescue_fail(world, parent, response, goal)
            lesson(world, parent, hero, partner, response)
            world.para()
            world.say(
                f"Later, {parent.label_word} brushed the hay out of the cape while {hero.id} stood very still."
            )
            world.say(
                f'{hero.id} looked at the dusty hem and thought, "Next time I will pick the safe hero move first."'
            )
            world.say(
                f"By sunset, the children were laughing again, but no one called the tumble elite anymore."
            )
            outcome = "tumbled"

    world.facts.update(
        hero=hero,
        partner=partner,
        parent=parent,
        costume=costume,
        outcome=outcome,
        severity=severity,
        delay=delay,
        goal_reached=world.facts["goal_reached"],
        hero_rescued=world.facts["hero_rescued"],
    )
    return world


THEMES = {
    "thunder_team": Theme(
        id="thunder_team",
        scene="a golden superhero headquarters between the bales",
        base_line="A feed scoop became a rescue beacon, an old blue blanket became a cape, and every tall pile of hay looked like a secret tower.",
        titles=("Captain", "Scout"),
        mission="guard the barn and answer every rescue signal",
        sendoff="The Thunder Team ran their next patrol with careful feet and bright, steady hearts.",
        tags={"superhero", "barn"},
    ),
    "comet_club": Theme(
        id="comet_club",
        scene="the Comet Club's farm base",
        base_line="The wagon was their launch pad, the broom was their signal staff, and the hay bales looked like city rooftops under the evening light.",
        titles=("Comet", "Beacon"),
        mission="save the day before supper",
        sendoff="The Comet Club marched on, not noisier than before, but much wiser.",
        tags={"superhero", "wagon"},
    ),
    "sun_shield": Theme(
        id="sun_shield",
        scene="a bright hero station beside the loft",
        base_line="A grain bucket became a siren tower, two red scarves became hero belts, and the hay made soft yellow walls all around them.",
        titles=("Shield", "Spark"),
        mission="keep the whole farm safe",
        sendoff="The Sun Shield heroes finished the day by choosing smart steps over flashy ones.",
        tags={"superhero", "loft"},
    ),
}

SHORTCUTS = {
    "wagon_jump": Shortcut(
        id="wagon_jump",
        label="wagon jump",
        shout="Elite sky-jump!",
        thought="If I leap from the wagon to the hay, I will look like the fastest hero in the county.",
        move_line="Hero boots pounded across the wagon board and {hero} sprang toward the hay",
        accident_line="One boot slid sideways, and the whole move crumpled into a clumsy flop",
        base_risk=2,
        applicable_hazards={"loose_hay", "muddy_boots"},
        tags={"jump", "wagon"},
    ),
    "rope_swing": Shortcut(
        id="rope_swing",
        label="rope swing",
        shout="Elite rope rescue!",
        thought="If I swing from the loft rope, everyone will see a real flying hero.",
        move_line="Small hands grabbed the rope and the cape flew out behind like a banner",
        accident_line="The swing wobbled crooked and the landing came all wrong",
        base_risk=3,
        applicable_hazards={"frayed_rope", "loose_hay"},
        tags={"rope", "swing"},
    ),
    "bale_climb": Shortcut(
        id="bale_climb",
        label="bale climb",
        shout="Elite tower climb!",
        thought="If I scamper up the hay tower alone, I will look brave enough for any mission.",
        move_line="Boots scrambled up the stacked bales as bits of hay fluttered down",
        accident_line="The top bale shifted and the brave climb turned into a shaky slide",
        base_risk=2,
        applicable_hazards={"loose_hay", "rolling_bale"},
        tags={"climb", "hay"},
    ),
}

HAZARDS = {
    "loose_hay": Hazard(
        id="loose_hay",
        label="loose hay",
        detail="the hay stack was fluffy and uneven",
        warning="That hay is loose.",
        accident="The loose hay sagged under the landing",
        bonus=1,
        applicable_shortcuts={"wagon_jump", "rope_swing", "bale_climb"},
        tags={"hay", "slip"},
    ),
    "muddy_boots": Hazard(
        id="muddy_boots",
        label="muddy boots",
        detail="mud clung to the boots from the yard",
        warning="Your boots are muddy.",
        accident="A muddy sole skidded on the board",
        bonus=1,
        applicable_shortcuts={"wagon_jump"},
        tags={"mud", "slip"},
    ),
    "frayed_rope": Hazard(
        id="frayed_rope",
        label="frayed rope",
        detail="the old rope had fuzzy worn spots",
        warning="That rope is frayed.",
        accident="The rope gave a scratchy twist in little hands",
        bonus=1,
        applicable_shortcuts={"rope_swing"},
        tags={"rope", "wear"},
    ),
    "rolling_bale": Hazard(
        id="rolling_bale",
        label="rolling bale",
        detail="one round bale nearby had not been chocked in place",
        warning="That round bale can roll.",
        accident="A round bale nudged free and made the stack wobble",
        bonus=2,
        applicable_shortcuts={"bale_climb"},
        tags={"bale", "roll"},
    ),
}

GOALS = {
    "bell": Goal(
        id="bell",
        label="silver barn bell",
        place="the loft rail",
        need="a silver barn bell hung just out of easy reach, the sign that a new pretend rescue had begun",
        safe_finish="The silver barn bell was rung the safe way, and its neat ding-ding sounded better than any stunt.",
        tags={"bell"},
    ),
    "mask": Goal(
        id="mask",
        label="red rescue mask",
        place="a peg above the hay loft",
        need="their red rescue mask was stuck high on a peg, waiting for the day's next mission",
        safe_finish="The red rescue mask came down without a tumble, and the mission could begin at last.",
        tags={"mask"},
    ),
    "banner": Goal(
        id="banner",
        label="blue hero banner",
        place="the top beam",
        need="their blue hero banner had caught on the top beam and fluttered there like a trapped flag",
        safe_finish="The blue hero banner came free at last, and it waved proudly from safe hands instead of a risky leap.",
        tags={"banner"},
    ),
}

RESPONSES = {
    "ladder": Response(
        id="ladder",
        sense=3,
        power=4,
        text="set the farm ladder in place, held it steady, and reached the {goal} without any jumping",
        fail="tried to set the ladder quickly, but the child had already slipped before the safe plan could begin",
        qa_text="used the farm ladder and held it steady",
        tags={"ladder", "adult_help"},
    ),
    "hook_pole": Response(
        id="hook_pole",
        sense=2,
        power=3,
        text="took down the long hook pole and guided the {goal} safely toward waiting hands",
        fail="reached with the hook pole, but the shaky stunt had already gone wrong",
        qa_text="used a long hook pole to guide the object down safely",
        tags={"tool", "adult_help"},
    ),
    "hold_wagon": Response(
        id="hold_wagon",
        sense=2,
        power=2,
        text="held the wagon still and helped the children climb down before anyone tried another jump, then fetched the {goal} the slow way",
        fail="grabbed for the wagon, but the slip happened before the plan could settle",
        qa_text="stopped the wagon play and helped everyone climb down carefully",
        tags={"wagon", "adult_help"},
    ),
    "boast_pose": Response(
        id="boast_pose",
        sense=1,
        power=1,
        text="called for a superhero pose and hoped the wobble would somehow stop",
        fail="called for a superhero pose, but posing did not stop the slip",
        qa_text="told them to strike a pose",
        tags={"showoff"},
    ),
}

GIRL_NAMES = ["Nova", "Mia", "Ava", "Zoe", "Luna", "Ruby", "Skye", "Ella", "Nora", "Ivy"]
BOY_NAMES = ["Jax", "Leo", "Max", "Finn", "Kai", "Theo", "Eli", "Owen", "Milo", "Ben"]
TRAITS = ["careful", "steady", "thoughtful", "sensible", "curious", "cheerful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for shortcut_id, shortcut in SHORTCUTS.items():
            for hazard_id, hazard in HAZARDS.items():
                if hazard_at_risk(shortcut, hazard):
                    for goal_id in GOALS:
                        combos.append((theme_id, shortcut_id, hazard_id, goal_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    shortcut: str
    hazard: str
    goal: str
    response: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    parent: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    partner_age: int = 4
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
    "hay": [(
        "What is hay?",
        "Hay is dried grass that farmers keep for animals to eat. It is soft to touch, but tall piles of hay can still be tricky to climb."
    )],
    "superhero": [(
        "What makes a real hero?",
        "A real hero helps people and thinks about safety, not just looking brave. Good heroes use smart plans as well as strong hearts."
    )],
    "ladder": [(
        "Why should a ladder be held steady?",
        "A ladder is safer when a grown-up sets it in the right place and holds it steady. That helps keep it from slipping while someone climbs."
    )],
    "rope": [(
        "Why is a frayed rope unsafe?",
        "A frayed rope is worn out and weak in spots. It can twist, scratch, or break when someone puts weight on it."
    )],
    "mud": [(
        "Why can muddy boots make you slip?",
        "Mud makes the bottoms of boots slick. Slick boots do not grip the ground or wood as well, so feet can slide."
    )],
    "bale": [(
        "Why can a round bale roll?",
        "A round bale is shaped like a giant wheel. If it is not blocked in place, it can roll when it is pushed."
    )],
    "adult_help": [(
        "Why is it good to call a grown-up for a high object?",
        "Grown-ups can bring the right tool and make a safer plan. Asking for help can be the fastest way to solve the problem well."
    )],
    "tool": [(
        "What is a hook pole for?",
        "A hook pole is a long tool that can pull or guide something down from a high place. It lets a grown-up reach without climbing onto shaky things."
    )],
}

KNOWLEDGE_ORDER = ["superhero", "hay", "rope", "mud", "bale", "ladder", "tool", "adult_help"]


def pair_noun(hero: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and partner.type == "boy":
            return "two brothers"
        if hero.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    shortcut = f["shortcut"]
    hazard = f["hazard"]
    goal = f["goal"]
    theme = f["theme"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "elite" and "hay". '
        f'Use sound effects, inner monologue, and a clear lesson learned.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle barn superhero story where {hero.id} wants to try an elite {shortcut.label}, "
            f"but {partner.id} warns about {hazard.label} and stops the stunt before anyone falls.",
            f"Write a story set in {theme.scene} where the children choose a safe plan to reach the {goal.label} and learn that showing off is not what makes a hero."
        ]
    if outcome == "tumbled":
        return [
            base,
            f"Tell a cautionary superhero story where {hero.id} ignores a warning about {hazard.label}, tries an elite {shortcut.label}, tumbles into hay, and then learns the safer way.",
            f"Write a farm-barn hero story that uses WHOOSH and THUMP, includes a worried inner thought, and ends with the lesson that careful heroes are better than flashy ones."
        ]
    return [
        base,
        f"Tell a superhero-style barn story where {hero.id} tries an elite {shortcut.label}, trouble starts because of {hazard.label}, and a grown-up uses a calm safe plan to help.",
        f"Write a story where children playing heroes need the {goal.label}, but they learn that the smartest rescue is the one that keeps everyone safe."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    parent = f["parent"]
    shortcut = f["shortcut"]
    hazard = f["hazard"]
    goal = f["goal"]
    response = f["response"]
    outcome = f["outcome"]
    pair = pair_noun(hero, partner, f["relation"])
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {partner.id}, who were pretending to be superheroes in a barn full of hay. "
            f"Their {pw} also helped when the mission became too risky."
        ),
        (
            "What did the children need to reach?",
            f"They wanted to reach the {goal.label}. It was up near {goal.place}, which is why the idea of a shortcut felt tempting."
        ),
        (
            f"Why did {partner.id} warn {hero.id}?",
            f"{partner.id} warned {hero.id} because of {hazard.label}. {hazard.warning} That meant the elite stunt could turn into a slip instead of a rescue."
        ),
        (
            f"What was {hero.id} thinking before the trouble started?",
            f"{hero.id} was imagining looking like a very elite hero. The inner thought made the risky shortcut sound exciting, even though it was not the safest choice."
        ),
    ]

    if outcome == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{hero.id} stopped before trying the stunt and went for a safer plan instead. That choice kept the hay stack quiet and let the mission end happily."
        ))
    elif outcome == "assisted":
        qa.append((
            f"How did {hero.id}'s {pw} help?",
            f"{pw.capitalize()} {response.qa_text}. That calm help ended the danger and let them reach the {goal.label} without another risky jump."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that real heroes do not need to show off. The best hero plan is the one that keeps everyone safe and still solves the problem."
        ))
    else:
        qa.append((
            f"What happened when {hero.id} tried the stunt?",
            f"{hero.id} slipped and tumbled into the hay with a big THUMP. The fall was soft, but it showed that a flashy plan can still go wrong very quickly."
        ))
        qa.append((
            "What lesson did the story teach?",
            f"The story taught that looking elite is not the same as being wise. A careful hero asks for help and chooses the safer move first."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"superhero", "hay"} | set(f["hazard"].tags) | set(f["response"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="thunder_team",
        shortcut="wagon_jump",
        hazard="muddy_boots",
        goal="bell",
        response="ladder",
        hero_name="Nova",
        hero_gender="girl",
        partner_name="Jax",
        partner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        hero_age=6,
        partner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="comet_club",
        shortcut="rope_swing",
        hazard="frayed_rope",
        goal="banner",
        response="hook_pole",
        hero_name="Leo",
        hero_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        hero_age=5,
        partner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="sun_shield",
        shortcut="bale_climb",
        hazard="rolling_bale",
        goal="mask",
        response="hold_wagon",
        hero_name="Skye",
        hero_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        parent="mother",
        trait="steady",
        delay=1,
        hero_age=6,
        partner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="thunder_team",
        shortcut="bale_climb",
        hazard="loose_hay",
        goal="mask",
        response="hook_pole",
        hero_name="Eli",
        hero_gender="boy",
        partner_name="Nora",
        partner_gender="girl",
        parent="father",
        trait="sensible",
        delay=0,
        hero_age=4,
        partner_age=7,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(shortcut: Shortcut, hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.label} does not make a believable danger for the shortcut "
        f"'{shortcut.label}'. Pick a hazard that really fits the move.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of these safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.partner_age, params.trait):
        return "averted"
    shortcut = SHORTCUTS[params.shortcut]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    return "assisted" if is_controlled(response, shortcut, hazard, params.delay) else "tumbled"


ASP_RULES = r"""
hazard(S, H) :- shortcut(S), hazard_cfg(H), applies(S, H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, S, H, G) :- theme(T), goal(G), hazard(S, H).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

partner_older :- relation(siblings), hero_age(HA), partner_age(PA), PA > HA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), bravery_init(BR), A > BR.

severity(B + HB + D) :- chosen_shortcut(S), base_risk(S, B), chosen_hazard(H), bonus_risk(H, HB), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
assisted :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(assisted) :- not averted, assisted.
outcome(tumbled) :- not averted, not assisted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("base_risk", sid, shortcut.base_risk))
        for hid in sorted(shortcut.applicable_hazards):
            lines.append(asp.fact("applies", sid, hid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard_cfg", hid))
        lines.append(asp.fact("bonus_risk", hid, hazard.bonus))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_shortcut", params.shortcut),
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome results differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero game in the hay barn, a risky stunt, and a safer lesson."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the risky move gets before help settles in")
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shortcut and args.hazard:
        shortcut = SHORTCUTS[args.shortcut]
        hazard = HAZARDS[args.hazard]
        if not hazard_at_risk(shortcut, hazard):
            raise StoryError(explain_rejection(shortcut, hazard))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.shortcut is None or c[1] == args.shortcut)
        and (args.hazard is None or c[2] == args.hazard)
        and (args.goal is None or c[3] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, shortcut, hazard, goal = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    hero_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme,
        shortcut=shortcut,
        hazard=hazard,
        goal=goal,
        response=response,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        shortcut = SHORTCUTS[params.shortcut]
        hazard = HAZARDS[params.hazard]
        goal = GOALS[params.goal]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not hazard_at_risk(shortcut, hazard):
        raise StoryError(explain_rejection(shortcut, hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=theme,
        shortcut=shortcut,
        hazard=hazard,
        goal=goal,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        partner_age=params.partner_age,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, shortcut, hazard, goal) combos:\n")
        for theme, shortcut, hazard, goal in combos:
            print(f"  {theme:12} {shortcut:11} {hazard:12} {goal}")
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
            header = (
                f"### {p.hero_name} & {p.partner_name}: {p.shortcut} with {p.hazard} "
                f"({p.theme}, {p.goal}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
