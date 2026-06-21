#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/arctic_champ_vanquish_flashback_rhyme_dialogue_pirate.py
===================================================================================

A standalone story world for a tiny pirate-flavored arctic tale.

Premise
-------
Two children turn a cold seaside day into an arctic pirate adventure. They want
to reach a prize on the far side of a small inlet and talk about how they will
"vanquish" the cold and become the champ of the cove. One child is tempted to
use an unsafe shortcut over weak ice or an unstable floe. The other child warns
them, helped by a flashback to a grown-up's earlier safety lesson. If the
warning fails, the child falls into danger and a grown-up must rescue them.

This world aims for:
- child-facing pirate-tale energy,
- clear beginning / turn / ending,
- world-driven prose,
- dialogue in every story,
- a brief flashback beat,
- a simple rhyme used by the children.

Run it
------
    python storyworlds/worlds/gpt-5.4/arctic_champ_vanquish_flashback_rhyme_dialogue_pirate.py
    python storyworlds/worlds/gpt-5.4/arctic_champ_vanquish_flashback_rhyme_dialogue_pirate.py --route thin_ice --rescue rope
    python storyworlds/worlds/gpt-5.4/arctic_champ_vanquish_flashback_rhyme_dialogue_pirate.py --route snowbank
    python storyworlds/worlds/gpt-5.4/arctic_champ_vanquish_flashback_rhyme_dialogue_pirate.py --all --qa
    python storyworlds/worlds/gpt-5.4/arctic_champ_vanquish_flashback_rhyme_dialogue_pirate.py --verify
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
BOLD_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "watchful"}


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
    cold_safe: bool = False
    floats: bool = False
    stable: bool = False
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
    rig: str
    rank1: str
    rank2: str
    goal: str
    water_word: str
    send_off: str
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
class Route:
    id: str
    label: str
    phrase: str
    where: str
    chant: str
    danger: str
    weak: bool = True
    cold_risk: bool = True
    drift_risk: bool = False
    spread: int = 2
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
    perch: str
    victory: str
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
class Rescue:
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


@dataclass
class SafeWay:
    id: str
    label: str
    phrase: str
    use_text: str
    glow_text: str
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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_cold_water(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    inlet = world.get("inlet")
    if hero.meters["in_water"] < THRESHOLD:
        return out
    sig = ("cold_water", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["cold"] += 1
    hero.meters["needs_help"] += 1
    inlet.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__splash__")
    return out


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    route_cfg = world.facts.get("route_cfg")
    if route_cfg is None or not route_cfg.drift_risk:
        return out
    if hero.meters["adrift"] < THRESHOLD:
        return out
    sig = ("drift", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["farther_out"] += 1
    hero.meters["needs_help"] += 1
    world.get("inlet").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__drift__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="cold_water", tag="physical", apply=_r_cold_water),
    Rule(name="drift", tag="physical", apply=_r_drift),
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


def hazard_at_risk(route: Route, prize: Prize) -> bool:
    return route.weak and route.cold_risk and prize.id in {"bell", "flag", "chest"}


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def severity(route: Route, delay: int) -> int:
    return route.spread + delay


def is_contained(rescue: Rescue, route: Route, delay: int) -> bool:
    return rescue.power >= severity(route, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, mate_age: int, trait: str) -> bool:
    mate_older = relation == "siblings" and mate_age > hero_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if mate_older else 0.0)
    return mate_older and authority > BOLD_INIT


def _do_accident(world: World, route_cfg: Route, narrate: bool = True) -> None:
    hero = world.get("hero")
    route = world.get("route")
    if route_cfg.id == "thin_ice":
        route.meters["cracked"] += 1
        hero.meters["in_water"] += 1
    elif route_cfg.id == "ice_floe":
        route.meters["shifted"] += 1
        hero.meters["adrift"] += 1
    elif route_cfg.id == "rotting_plank":
        route.meters["broken"] += 1
        hero.meters["in_water"] += 1
    propagate(world, narrate=narrate)


def predict_danger(world: World, route_cfg: Route) -> dict:
    sim = world.copy()
    _do_accident(sim, route_cfg, narrate=False)
    hero = sim.get("hero")
    return {
        "needs_help": hero.meters["needs_help"] >= THRESHOLD,
        "cold": hero.meters["cold"] >= THRESHOLD,
        "danger": sim.get("inlet").meters["danger"],
    }


def play_setup(world: World, hero: Entity, mate: Entity, theme: Theme, prize: Prize) -> None:
    for kid in (hero, mate):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright, biting afternoon, {hero.id} and {mate.id} turned the cove into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.rank1} {hero.id} and {theme.rank2} {mate.id}!" {hero.id} cried. '
        f'"Today we vanquish the wind and win {prize.phrase}!"'
    )


def sight_goal(world: World, mate: Entity, route: Route, prize: Prize) -> None:
    world.say(
        f"Across {route.where}, {prize.perch} waited like treasure at the end of a map."
    )
    world.say(
        f'{mate.id} pointed and whispered, "There it is. The one who reaches it will be the champ of the cove."'
    )


def chant(world: World, hero: Entity, route: Route) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} stamped a boot and sang, "{route.chant}"'
    )


def flashback_warn(world: World, mate: Entity, hero: Entity, route: Route, parent: Entity) -> None:
    pred = predict_danger(world, route)
    mate.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_cold"] = pred["cold"]
    world.say(
        f'{mate.id} caught {hero.pronoun("possessive")} sleeve. "No. {route.label.capitalize()} is tricksy," '
        f'{mate.pronoun()} said.'
    )
    world.say(
        f"Then a quick flashback stirred in {mate.pronoun('possessive')} mind: yesterday at the pier, "
        f"{parent.label_word} had tapped the rail and said, "
        f'"When water wears an ice hat, do not trust it. Thin ice lies, and a drifting floe does not stay still."'
    )
    extra = ""
    if pred["cold"]:
        extra = " If it gives way, the arctic water will bite like teeth."
    world.say(
        f'"Remember?" {mate.id} said. "We can still be brave without stepping there.{extra}"'
    )


def defy(world: World, hero: Entity, mate: Entity, route: Route) -> None:
    hero.memes["defiance"] += 1
    older = hero.attrs.get("relation") == "siblings" and hero.age > mate.age
    if older:
        world.say(
            f'"I can do it," {hero.id} said. "I will vanquish it in one dash." '
            f'Because {hero.id} was {mate.pronoun("possessive")} older sibling, {mate.id} could not stop '
            f'{hero.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"I can do it," {hero.id} said. "I will vanquish it in one dash." Then {hero.pronoun()} sprang toward {route.label}.'
        )


def back_down(world: World, hero: Entity, mate: Entity, route: Route, parent: Entity) -> None:
    hero.memes["bold"] = 0.0
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    rel = "brother" if mate.type == "boy" else "sister"
    world.say(
        f'{hero.id} looked at {route.label}, then at {mate.id}. "All right," {hero.pronoun()} muttered. '
        f'"You are my big {rel}, and you are right."'
    )
    world.say(
        f"They went to tell {parent.label_word} that the pirate path was not safe after all."
    )


def accident(world: World, hero: Entity, route_cfg: Route) -> None:
    _do_accident(world, route_cfg)
    if route_cfg.id == "thin_ice":
        world.say(
            f"The first step went skritch. The second went crack. On the third, the ice opened like a trapdoor, "
            f"and {hero.id} splashed down with a startled yelp."
        )
    elif route_cfg.id == "ice_floe":
        world.say(
            f"The little floe bobbed once, twice, then spun away from shore. "
            f"{hero.id} windmilled both arms as the white raft drifted out into the inlet."
        )
    else:
        world.say(
            f"The old plank gave a groan, then snapped in the middle. "
            f"{hero.id} tumbled through the spray and grabbed for the air."
        )


def alarm(world: World, mate: Entity, hero: Entity, parent: Entity) -> None:
    world.say(f'"{hero.id}!" {mate.id} shouted. "{parent.label_word.capitalize()}! Help!"')


def rescue_success(world: World, parent: Entity, rescue: Rescue, route_cfg: Route, theme: Theme) -> None:
    hero = world.get("hero")
    hero.meters["in_water"] = 0.0
    hero.meters["adrift"] = 0.0
    hero.meters["needs_help"] = 0.0
    world.get("inlet").meters["danger"] = 0.0
    body = rescue.text.replace("{route}", route_cfg.label)
    world.say(
        f"{parent.label_word.capitalize()} came running from the pier and {body}."
    )
    world.say(
        f"Soon {hero.id} was back on shore, shivering hard but safe, while the wind worried at the water all by itself."
    )
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["lesson"] += 1


def rescue_fail(world: World, parent: Entity, rescue: Rescue, route_cfg: Route) -> None:
    hero = world.get("hero")
    world.get("inlet").meters["danger"] += 1
    hero.meters["cold"] += 1
    body = rescue.fail.replace("{route}", route_cfg.label)
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {body}."
    )
    world.say(
        "For one long, frightening moment, the cold current kept pulling and the whole cove seemed louder than a storm."
    )


def second_help(world: World, parent: Entity, theme: Theme) -> None:
    hero = world.get("hero")
    mate = world.get("mate")
    hero.meters["in_water"] = 0.0
    hero.meters["adrift"] = 0.0
    hero.meters["needs_help"] = 0.0
    world.get("inlet").meters["danger"] = 0.0
    world.say(
        f"Then {parent.label_word} threw all caution into one fast, clever plan, braced low, and dragged {hero.id} close enough for {mate.id} to catch {hero.pronoun('possessive')} sleeve."
    )
    world.say(
        f"Together they hauled {hero.pronoun('object')} onto the snowy stones. No treasure mattered now except warm hands and safe feet."
    )
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["lesson"] += 1


def lesson(world: World, parent: Entity, route_cfg: Route) -> None:
    hero = world.get("hero")
    mate = world.get("mate")
    world.say("For a little while, nobody tried to sound like pirates at all.")
    world.say(
        f'Then {parent.label_word} wrapped a blanket around {hero.id} and knelt by them both. '
        f'"Brave is not the same as rash," {parent.pronoun()} said softly. '
        f'"Cold water steals your strength fast, and {route_cfg.label} is not a path. '
        f'When something feels tricksy, you call a grown-up and choose the safe way."'
    )
    world.say(f'"We will," whispered {mate.id}. "{hero.id} too," {hero.id} added.')


def safe_gift(world: World, parent: Entity, hero: Entity, mate: Entity, prize: Prize, safe_way: SafeWay, theme: Theme) -> None:
    for kid in (hero, mate):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word} had a better pirate plan. {parent.pronoun().capitalize()} showed them {safe_way.phrase}."
    )
    world.say(
        f'"Real captains use the way that gets the crew home," {parent.pronoun()} said. "{safe_way.use_text}"'
    )
    world.say(
        f"They crossed together, {safe_way.glow_text}, and reached {prize.phrase} at last."
    )
    world.say(
        f'{hero.id} laughed. "{mate.id} can be the champ of caution," {hero.pronoun()} said. '
        f'"And we both win."'
    )
    world.say(
        f"By the end, the two little pirates {theme.send_off}, not by vanquishing the water, but by respecting it."
    )


def tell(
    theme: Theme,
    route_cfg: Route,
    prize: Prize,
    safe_way: SafeWay,
    rescue: Rescue,
    hero_name: str = "Tom",
    hero_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    hero_age: int = 6,
    mate_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="captain",
        traits=["bold"],
        age=hero_age,
        attrs={"relation": relation},
    ))
    mate = world.add(Entity(
        id=mate_name,
        kind="character",
        type=mate_gender,
        role="mate",
        traits=[trait],
        age=mate_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    inlet = world.add(Entity(id="inlet", type="water", label="the inlet"))
    route = world.add(Entity(id="route", type="route", label=route_cfg.label))
    goal = world.add(Entity(id="goal", type="prize", label=prize.label))
    aid = world.add(Entity(id="safe_way", type="safe_way", label=safe_way.label, stable=True))
    _ = goal, aid

    hero.memes["bold"] = BOLD_INIT
    mate.memes["caution"] = initial_caution(trait)
    world.facts.update(
        theme=theme,
        route_cfg=route_cfg,
        prize=prize,
        safe_way=safe_way,
        rescue=rescue,
        hero=hero,
        mate=mate,
        parent=parent,
        relation=relation,
        delay=delay,
    )

    play_setup(world, hero, mate, theme, prize)
    sight_goal(world, mate, route_cfg, prize)

    world.para()
    chant(world, hero, route_cfg)
    flashback_warn(world, mate, hero, route_cfg, parent)

    averted = would_avert(relation, hero_age, mate_age, trait)
    if averted:
        back_down(world, hero, mate, route_cfg, parent)
        world.para()
        safe_gift(world, parent, hero, mate, prize, safe_way, theme)
        ending = "averted"
    else:
        defy(world, hero, mate, route_cfg)
        world.para()
        accident(world, hero, route_cfg)
        alarm(world, mate, hero, parent)
        world.para()
        if is_contained(rescue, route_cfg, delay):
            rescue_success(world, parent, rescue, route_cfg, theme)
            lesson(world, parent, route_cfg)
            world.para()
            safe_gift(world, parent, hero, mate, prize, safe_way, theme)
            ending = "rescued"
        else:
            rescue_fail(world, parent, rescue, route_cfg)
            second_help(world, parent, theme)
            lesson(world, parent, route_cfg)
            world.para()
            safe_gift(world, parent, hero, mate, prize, safe_way, theme)
            ending = "hard_rescue"

    world.facts.update(
        outcome=ending,
        danger=world.get("inlet").meters["danger"],
        severity=severity(route_cfg, delay) if not averted else 0,
        promised=hero.memes["lesson"] >= THRESHOLD or mate.memes["lesson"] >= THRESHOLD,
        accident_happened=ending != "averted",
    )
    return world


THEMES = {
    "arctic_pirates": Theme(
        id="arctic_pirates",
        scene="an arctic sea full of secret channels",
        rig="A laundry basket was their boat, a mop was their mast, and a blue scarf spread over the stones became a freezing map of the cove.",
        rank1="Captain",
        rank2="Lookout",
        goal="the prize across the inlet",
        water_word="inlet",
        send_off="marched home chanting a softer pirate song",
    ),
    "frost_raiders": Theme(
        id="frost_raiders",
        scene="a white raider sea at the edge of the world",
        rig="A wooden crate was their ship, two sticks were their oars, and a striped towel flapped like a captain's banner in the wind.",
        rank1="Captain",
        rank2="Scout",
        goal="the prize across the channel",
        water_word="channel",
        send_off="tramped back over the snow with careful boots and happy grins",
    ),
}

ROUTES = {
    "thin_ice": Route(
        id="thin_ice",
        label="thin ice",
        phrase="a skin of thin ice near the pier",
        where="the narrow water by the pier",
        chant='Ice so white, step so light, be our bridge before the night!',
        danger="The ice may crack and drop someone into freezing water.",
        weak=True,
        cold_risk=True,
        drift_risk=False,
        spread=3,
        tags={"ice", "cold_water"},
    ),
    "ice_floe": Route(
        id="ice_floe",
        label="a loose ice floe",
        phrase="a loose ice floe rocking near shore",
        where="the choppy inlet",
        chant='Floe, don\'t go! Floe, move slow! Carry our ship where champs should go!',
        danger="A floe can drift away and leave someone stranded over cold water.",
        weak=True,
        cold_risk=True,
        drift_risk=True,
        spread=2,
        tags={"ice", "cold_water", "drift"},
    ),
    "rotting_plank": Route(
        id="rotting_plank",
        label="the rotting plank",
        phrase="an old rotting plank over black water",
        where="the darkest part of the cove",
        chant='Plank, don\'t sink! Plank, don\'t blink! Hold us up before we think!',
        danger="The plank can snap and throw someone into the freezing inlet.",
        weak=True,
        cold_risk=True,
        drift_risk=False,
        spread=2,
        tags={"plank", "cold_water"},
    ),
    "snowbank": Route(
        id="snowbank",
        label="the snowbank",
        phrase="a soft snowbank beside the path",
        where="the safe edge of the shore",
        chant='Snow so bright, snow so white, pile up high and hold us tight!',
        danger="A snowbank is slippery, but it is not a crossing over the water.",
        weak=False,
        cold_risk=False,
        drift_risk=False,
        spread=0,
        tags={"snow"},
    ),
}

PRIZES = {
    "bell": Prize(
        id="bell",
        label="bell",
        phrase="the brass champ bell",
        perch="the brass champ bell on a post of driftwood",
        victory='whoever rang it could shout, "Champ of the cove!"',
        tags={"bell", "champ"},
    ),
    "flag": Prize(
        id="flag",
        label="flag",
        phrase="the blue champion flag",
        perch="the blue champion flag tucked into a snow barrel",
        victory='whoever reached it could wave it and cry, "Champ!"',
        tags={"flag", "champ"},
    ),
    "chest": Prize(
        id="chest",
        label="chest",
        phrase="the little treasure chest",
        perch="the little treasure chest perched on a crate",
        victory='whoever touched it could declare the cold vanquished',
        tags={"chest", "champ"},
    ),
}

SAFE_WAYS = {
    "rope_walk": SafeWay(
        id="rope_walk",
        label="rope walk",
        phrase="a rope walk with rail ropes tied between sturdy posts",
        use_text="Hold the side rope and take one careful step after another.",
        glow_text="their mittens brushing the rope",
        tags={"rope_walk", "safe_path"},
    ),
    "harbor_bridge": SafeWay(
        id="harbor_bridge",
        label="little harbor bridge",
        phrase="the little harbor bridge that looped around the inlet",
        use_text="The long way is the right way when the short way lies.",
        glow_text="their boots thumping the planks in a neat row",
        tags={"bridge", "safe_path"},
    ),
    "sled_ferry": SafeWay(
        id="sled_ferry",
        label="sled ferry",
        phrase="a wide sled pulled along the shore path",
        use_text="We ride the sled to the far side, then step onto dry ground together.",
        glow_text="the runners whispering over the packed snow",
        tags={"sled", "safe_path"},
    ),
}

RESCUES = {
    "rope": Rescue(
        id="rope",
        sense=3,
        power=4,
        text="snatched up the rescue rope, threw it true, and hauled the little pirate back",
        fail="threw the rescue rope, but the current and the panic made the first pull miss",
        qa_text="threw a rescue rope and pulled the child back to shore",
        tags={"rope", "rescue"},
    ),
    "ladder": Rescue(
        id="ladder",
        sense=3,
        power=3,
        text="shoved a harbor ladder flat across the edge and slid forward until the child could grab it",
        fail="pushed the harbor ladder out, but it skidded and did not reach far enough at first",
        qa_text="slid a harbor ladder out so the child could grab it",
        tags={"ladder", "rescue"},
    ),
    "boat_hook": Rescue(
        id="boat_hook",
        sense=2,
        power=2,
        text="lay flat, reached with the long boat hook, and caught the child's coat to drag them in",
        fail="reached with the boat hook, but the child drifted just beyond the first careful grab",
        qa_text="used a boat hook to pull the child closer",
        tags={"boat_hook", "rescue"},
    ),
    "run_and_grab": Rescue(
        id="run_and_grab",
        sense=1,
        power=1,
        text="ran straight onto the weak edge and somehow yanked the child back",
        fail="ran onto the weak edge too, which only made the ice break wider",
        qa_text="ran onto the ice and grabbed the child",
        tags={"bad_rescue"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "steady", "thoughtful", "watchful", "curious", "clever"]


@dataclass
class StoryParams:
    theme: str
    route: str
    prize: str
    safe_way: str
    rescue: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    mate_age: int = 4
    relation: str = "siblings"
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for route_id, route in ROUTES.items():
            for prize_id, prize in PRIZES.items():
                if hazard_at_risk(route, prize):
                    combos.append((theme_id, route_id, prize_id))
    return combos


KNOWLEDGE = {
    "ice": [
        (
            "Why can thin ice be dangerous?",
            "Thin ice can crack under your weight and drop you into freezing water. It may look bright and solid, but looks can fool you."
        )
    ],
    "cold_water": [
        (
            "Why is arctic water dangerous?",
            "Arctic water is so cold that it can make your body weak and shaky very quickly. That is why grown-ups hurry to get people out fast."
        )
    ],
    "drift": [
        (
            "Why is a loose ice floe unsafe?",
            "A loose ice floe can move away from shore with the water underneath it. Then a person can end up farther from help instead of closer."
        )
    ],
    "plank": [
        (
            "Why can an old plank be unsafe?",
            "Old wood can crack or snap when someone steps on it. If it is over water, a broken plank can make a bad fall much worse."
        )
    ],
    "rope": [
        (
            "What is a rescue rope for?",
            "A rescue rope lets a grown-up reach someone without stepping into the same danger. It helps pull the person back to shore."
        )
    ],
    "ladder": [
        (
            "Why can a ladder help in a rescue?",
            "A ladder spreads weight and gives a person something long and sturdy to grab. That can make it safer than crawling onto weak ice."
        )
    ],
    "boat_hook": [
        (
            "What is a boat hook?",
            "A boat hook is a long pole used near boats and docks. A grown-up can use it to reach something without leaning too far over the water."
        )
    ],
    "bridge": [
        (
            "Why is a bridge safer than thin ice?",
            "A real bridge is built to hold people up, while thin ice can break without warning. A safe path is better than a daring shortcut."
        )
    ],
    "sled": [
        (
            "What is a sled good for in snow?",
            "A sled can carry people or things over packed snow without stepping into unsafe places. It is useful when the ground is cold and slippery."
        )
    ],
    "bell": [
        (
            "What is a bell for in a game?",
            "A bell can be the goal of a game because everyone hears it ring. It makes the ending feel exciting and easy to share."
        )
    ],
    "flag": [
        (
            "Why do pirates like flags in stories?",
            "Flags are bright and easy to spot from far away. In pirate stories, a flag often shows who has reached the goal."
        )
    ],
    "chest": [
        (
            "Why is a treasure chest exciting in a pretend game?",
            "A treasure chest feels like a promise of something special inside. Even a little box can turn a game into an adventure."
        )
    ],
    "champ": [
        (
            "What does champ mean?",
            "Champ is a short way to say champion. It means the winner or the person everyone cheers for."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ice",
    "cold_water",
    "drift",
    "plank",
    "rope",
    "ladder",
    "boat_hook",
    "bridge",
    "sled",
    "bell",
    "flag",
    "chest",
    "champ",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    route = f["route_cfg"]
    prize = f["prize"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-style arctic story for a 3-to-5-year-old where two children want to reach {prize.phrase}, but one remembers a safety warning in a flashback and stops the risky plan.',
            f'Include the words "arctic", "champ", and "vanquish", along with dialogue and a little rhyme, in a story where {hero.id} backs down from crossing {route.label}.',
            f"Tell a gentle pirate tale where {mate.id} uses a remembered grown-up lesson to stop {hero.id} before the danger begins."
        ]
    return [
        f'Write a pirate-style arctic story for a 3-to-5-year-old where two children race to be the champ of the cove and one takes a risky shortcut over {route.label}.',
        f'Include the words "arctic", "champ", and "vanquish", with dialogue, a rhyme, and a quick flashback warning, in a rescue story for young children.',
        f"Tell a snowy pirate adventure where {hero.id} ignores {mate.id}'s warning, trouble happens by the water, and a grown-up shows the safer way the next day."
    ]


def pair_noun(hero: Entity, mate: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and mate.type == "boy":
            return "two brothers"
        if hero.type == "girl" and mate.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    parent = f["parent"]
    route = f["route_cfg"]
    prize = f["prize"]
    safe_way = f["safe_way"]
    rescue = f["rescue"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(hero, mate, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {mate.id}, playing pirates by an arctic cove. Their {parent.label_word} is the grown-up who helps them."
        ),
        (
            "What did they want to do?",
            f"They wanted to reach {prize.phrase} across the water and become the champ of the cove. Their pirate game made the goal feel bold and exciting."
        ),
        (
            f"Why did {mate.id} warn {hero.id}?",
            f"{mate.id} knew that {route.label} was unsafe and remembered a grown-up's warning in a flashback. {mate.pronoun().capitalize()} understood that the cold water could make a small mistake turn dangerous very fast."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What happened after the warning?",
                f"{hero.id} listened and gave up the risky shortcut, so nobody fell into danger. The choice changed the whole ending because the adventure could continue the safe way."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} tried to cross {route.label}?",
                f"The shortcut failed and {hero.id} ended up in trouble by the freezing water. It happened because {hero.pronoun()} trusted a weak path instead of the safer way."
            )
        )
        if outcome == "rescued":
            qa.append(
                (
                    f"How did {parent.label_word} help?",
                    f"{parent.label_word.capitalize()} {rescue.qa_text}. The rescue worked quickly enough to stop the danger before it grew worse."
                )
            )
        else:
            qa.append(
                (
                    f"Was the first rescue attempt easy?",
                    f"No. The first try did not solve everything right away, so the moment stayed scary for longer. After that, the family worked together to pull {hero.id} back to safety."
                )
            )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children using {safe_way.label} instead of the risky shortcut. The last image proves what changed: they still had their pirate game, but now they chose courage with care."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["route_cfg"].tags) | set(f["prize"].tags)
    outcome = f["outcome"]
    if f["safe_way"].id == "harbor_bridge":
        tags.add("bridge")
    if f["safe_way"].id == "sled_ferry":
        tags.add("sled")
    if outcome != "averted":
        tags |= set(f["rescue"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
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
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(R, P) :- weak(R), cold_risk(R), prize(P).
sensible(Res) :- rescue(Res), sense(Res, S), sense_min(M), S >= M.
valid(T, R, P) :- theme(T), route(R), prize(P), hazard(R, P).

cautious_now(Trait) :- trait(Trait), is_cautious(Trait).
init_caution(5) :- trait(Trait), cautious_now(Trait).
init_caution(3) :- trait(Trait), not cautious_now(Trait).

mate_older :- relation(siblings), hero_age(H), mate_age(M), M > H.
bonus(4) :- mate_older.
bonus(0) :- not mate_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- mate_older, authority(A), bold_init(B), A > B.

sev(S + D) :- chosen_route(R), spread(R, S), delay(D).
rescue_power(P) :- chosen_rescue(R), power(R, P).
contained :- rescue_power(P), sev(V), P >= V.

outcome(averted) :- averted.
outcome(rescued) :- not averted, contained.
outcome(hard_rescue) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if route.weak:
            lines.append(asp.fact("weak", rid))
        if route.cold_risk:
            lines.append(asp.fact("cold_risk", rid))
        lines.append(asp.fact("spread", rid, route.spread))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for sid in SAFE_WAYS:
        lines.append(asp.fact("safe_way", sid))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, rescue.sense))
        lines.append(asp.fact("power", rid, rescue.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
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
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("mate_age", params.mate_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.mate_age, params.trait):
        return "averted"
    return "rescued" if is_contained(RESCUES[params.rescue], ROUTES[params.route], params.delay) else "hard_rescue"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_rescues()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible rescues match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        theme="arctic_pirates",
        route="thin_ice",
        prize="bell",
        safe_way="harbor_bridge",
        rescue="rope",
        hero="Tom",
        hero_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        hero_age=6,
        mate_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="frost_raiders",
        route="ice_floe",
        prize="flag",
        safe_way="sled_ferry",
        rescue="ladder",
        hero="Mia",
        hero_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        trait="watchful",
        delay=1,
        hero_age=6,
        mate_age=5,
        relation="friends",
    ),
    StoryParams(
        theme="arctic_pirates",
        route="rotting_plank",
        prize="chest",
        safe_way="rope_walk",
        rescue="boat_hook",
        hero="Sam",
        hero_gender="boy",
        mate="Nora",
        mate_gender="girl",
        parent="mother",
        trait="steady",
        delay=2,
        hero_age=7,
        mate_age=5,
        relation="siblings",
    ),
    StoryParams(
        theme="frost_raiders",
        route="thin_ice",
        prize="bell",
        safe_way="harbor_bridge",
        rescue="rope",
        hero="Leo",
        hero_gender="boy",
        mate="Theo",
        mate_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        hero_age=5,
        mate_age=7,
        relation="siblings",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: arctic pirate children, a risky shortcut, and a safer way."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--safe-way", dest="safe_way", choices=SAFE_WAYS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the danger gets before the rescue fully works")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def explain_rejection(route: Route, prize: Prize) -> str:
    if not route.cold_risk or not route.weak:
        return (
            f"(No story: {route.label} is not a real crossing danger over freezing water, "
            f"so there is no honest rescue story to tell. Pick thin ice, a loose ice floe, or the rotting plank.)"
        )
    return (
        f"(No story: {route.label} does not make a sensible danger for reaching {prize.phrase} here.)"
    )


def explain_rescue(rid: str) -> str:
    rescue = RESCUES[rid]
    better = ", ".join(sorted(r.id for r in sensible_rescues()))
    return (
        f"(Refusing rescue '{rid}': it scores too low on common sense "
        f"(sense={rescue.sense} < {SENSE_MIN}). Try one of the safer rescues: {better}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.prize:
        route = ROUTES[args.route]
        prize = PRIZES[args.prize]
        if not hazard_at_risk(route, prize):
            raise StoryError(explain_rejection(route, prize))
    if args.route and not ROUTES[args.route].cold_risk:
        route = ROUTES[args.route]
        prize = PRIZES[args.prize] if args.prize else PRIZES[next(iter(PRIZES))]
        raise StoryError(explain_rejection(route, prize))
    if args.rescue and RESCUES[args.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(args.rescue))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.route is None or combo[1] == args.route)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, route, prize = rng.choice(sorted(combos))
    safe_way = args.safe_way or rng.choice(sorted(SAFE_WAYS))
    rescue = args.rescue or rng.choice(sorted(r.id for r in sensible_rescues()))
    hero, hero_gender = _pick_kid(rng)
    mate, mate_gender = _pick_kid(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, mate_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme,
        route=route,
        prize=prize,
        safe_way=safe_way,
        rescue=rescue,
        hero=hero,
        hero_gender=hero_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        mate_age=mate_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.safe_way not in SAFE_WAYS:
        raise StoryError(f"(Unknown safe way: {params.safe_way})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if not hazard_at_risk(ROUTES[params.route], PRIZES[params.prize]):
        raise StoryError(explain_rejection(ROUTES[params.route], PRIZES[params.prize]))
    if RESCUES[params.rescue].sense < SENSE_MIN:
        raise StoryError(explain_rescue(params.rescue))

    world = tell(
        theme=THEMES[params.theme],
        route_cfg=ROUTES[params.route],
        prize=PRIZES[params.prize],
        safe_way=SAFE_WAYS[params.safe_way],
        rescue=RESCUES[params.rescue],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        hero_age=params.hero_age,
        mate_age=params.mate_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible rescues: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, route, prize) combos:\n")
        for theme, route, prize in combos:
            print(f"  {theme:15} {route:12} {prize}")
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
            header = f"### {p.hero} & {p.mate}: {p.route} for {p.prize} ({p.theme}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
