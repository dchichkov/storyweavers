#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py
===========================================================================

A standalone story world about a child at a zoo who wants a better look at a
rhinoceros and is tempted to take an unsafe shortcut. The world prefers a small,
plausible set of slice-of-life safety stories: an ordinary outing, a suspenseful
near mistake, a grounded warning, and a safer way to keep looking.

Run it
------
    python storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py --setting yard --shortcut duck_under
    python storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py --setting barn --shortcut duck_under
    python storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rhinoceros_suspense_cautionary_slice_of_life.py --verify
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
CALM_TRAITS = {"careful", "patient", "thoughtful"}


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
    barrier: str
    need: str
    risk: str
    opener: str
    sight_problem: str
    rhino_name: str
    rhino_detail: str
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
    action: str
    past: str
    barriers: set[str]
    helps: set[str]
    risk_text: str
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
class SafeFix:
    id: str
    label: str
    phrase: str
    barriers: set[str]
    helps: set[str]
    use_text: str
    ending_text: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "risk": setting.risk,
            "rhino_notice": False,
            "danger_seen": False,
            "stumble_seen": False,
        }

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


def _r_rhino_notice(world: World) -> list[str]:
    child = world.get("child")
    rhino = world.get("rhino")
    if child.meters["beyond_barrier"] < THRESHOLD:
        return []
    sig = ("notice", world.setting.risk)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rhino.meters["attention"] += 1
    child.memes["fear"] += 1
    world.facts["rhino_notice"] = True
    return ["__rhino_notice__"]


def _r_edge_danger(world: World) -> list[str]:
    child = world.get("child")
    place = world.get("place")
    if child.meters["beyond_barrier"] < THRESHOLD:
        return []
    if world.setting.risk not in {"mud_edge", "keeper_path", "pinch_gap"}:
        return []
    sig = ("danger", world.setting.risk)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    place.meters["danger"] += 1
    child.memes["fear"] += 1
    world.facts["danger_seen"] = True
    return ["__danger__"]


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    place = world.get("place")
    rhino = world.get("rhino")
    if child.meters["on_top"] < THRESHOLD:
        return []
    if rhino.meters["attention"] < THRESHOLD:
        return []
    sig = ("wobble", world.setting.barrier)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["wobble"] += 1
    place.meters["danger"] += 1
    child.memes["fear"] += 1
    world.facts["stumble_seen"] = True
    return ["__wobble__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="rhino_notice", tag="social", apply=_r_rhino_notice),
    Rule(name="danger", tag="physical", apply=_r_edge_danger),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
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
    "yard": Setting(
        id="yard",
        place="the city zoo's rhinoceros yard",
        barrier="rope",
        need="closer",
        risk="mud_edge",
        opener="After the grocery bags were put away, the afternoon still felt open, so they stopped at the zoo.",
        sight_problem="A knot of taller people stood at the front, and the rhinoceros looked far away beyond the dusty yard.",
        rhino_name="Mara",
        rhino_detail="The big gray rhinoceros stood by the mud pool with little birds stepping near her feet.",
        tags={"zoo", "rope", "rhinoceros"},
    ),
    "barn": Setting(
        id="barn",
        place="the warm rhinoceros barn",
        barrier="rail",
        need="higher",
        risk="wobble",
        opener="On a drizzly afternoon, they chose the indoor animal houses where everything smelled like hay and rain.",
        sight_problem="The rail was tall for a small child, and only the rhinoceros's ears showed above the heads in front.",
        rhino_name="Biko",
        rhino_detail="Inside the barn, the rhinoceros shifted his heavy feet on the straw and let out a deep, sleepy puff.",
        tags={"zoo", "rail", "rhinoceros"},
    ),
    "gate": Setting(
        id="gate",
        place="the side window near the rhinoceros keeper gate",
        barrier="slats",
        need="clearer",
        risk="pinch_gap",
        opener="They had gone to the zoo on an ordinary Saturday, the kind that began with errands and ended with one small treat.",
        sight_problem="Children crowded the best opening, and the sign by the gate made the viewing corner feel narrow and busy.",
        rhino_name="Nia",
        rhino_detail="The rhinoceros was close enough there to show the folds in her skin and the shine of damp mud on her horn.",
        tags={"zoo", "gate", "rhinoceros"},
    ),
}

SHORTCUTS = {
    "duck_under": Shortcut(
        id="duck_under",
        action="duck under the rope for just one closer peek",
        past="ducked under the rope",
        barriers={"rope"},
        helps={"closer"},
        risk_text="The rope marked the safe line because the ground near the moat edge was soft and slippery.",
        tags={"barrier", "zoo_safety"},
    ),
    "climb_rail": Shortcut(
        id="climb_rail",
        action="climb onto the rail to look over everyone",
        past="climbed onto the rail",
        barriers={"rail"},
        helps={"higher"},
        risk_text="The rail was for leaning, not standing, and a wobble that high could send small shoes skidding.",
        tags={"rail", "zoo_safety"},
    ),
    "reach_through": Shortcut(
        id="reach_through",
        action="slide fingers through the slats to point at the horn",
        past="slid fingers through the slats",
        barriers={"slats"},
        helps={"clearer"},
        risk_text="The slats left a small gap, but signs were there because curious fingers do not belong inside animal spaces.",
        tags={"gate", "zoo_safety"},
    ),
}

SAFE_FIXES = {
    "bench_mark": SafeFix(
        id="bench_mark",
        label="painted footprint spot",
        phrase="a painted footprint spot on the path",
        barriers={"rope"},
        helps={"closer"},
        use_text="showed the child a painted footprint spot where families could wait for the rhinoceros to wander nearer",
        ending_text="Soon the rhinoceros ambled over on her own, and they could see her wrinkled nose perfectly well from the safe line.",
        tags={"waiting", "patience"},
    ),
    "step_block": SafeFix(
        id="step_block",
        label="viewing block",
        phrase="a wooden viewing block",
        barriers={"rail"},
        helps={"higher"},
        use_text="pulled over a sturdy wooden viewing block kept beside the rail for small visitors",
        ending_text="Standing on the block, the child could see the whole rhinoceros at once, from the twitching ears to the round, muddy back.",
        tags={"step", "zoo_tools"},
    ),
    "quiet_window": SafeFix(
        id="quiet_window",
        label="quiet window",
        phrase="a quiet side window",
        barriers={"slats"},
        helps={"clearer"},
        use_text="led the child to a quiet side window where the glass was clean and no one had to squeeze near the gate",
        ending_text="From that window, the rhinoceros filled the whole pane like a moving gray hill, close and clear and safe to watch.",
        tags={"window", "space"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["careful", "patient", "thoughtful", "curious", "bouncy", "impulsive"]


def shortcut_works(setting: Setting, shortcut: Shortcut) -> bool:
    return setting.barrier in shortcut.barriers and setting.need in shortcut.helps


def select_fix(setting: Setting, fix_id: str) -> Optional[SafeFix]:
    fix = SAFE_FIXES.get(fix_id)
    if fix is None:
        return None
    if setting.barrier in fix.barriers and setting.need in fix.helps:
        return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for shortcut_id, shortcut in SHORTCUTS.items():
            if not shortcut_works(setting, shortcut):
                continue
            for fix_id in SAFE_FIXES:
                if select_fix(setting, fix_id):
                    combos.append((setting_id, shortcut_id, fix_id))
    return combos


def would_avoid(trait: str, adult_type: str) -> bool:
    bonus = 1 if adult_type in {"grandmother", "grandfather"} else 0
    return (3 if trait in CALM_TRAITS else 1) + bonus >= 3


def predict_risk(world: World, shortcut: Shortcut) -> dict:
    sim = world.copy()
    child = sim.get("child")
    if shortcut.id == "duck_under":
        child.meters["beyond_barrier"] += 1
    elif shortcut.id == "climb_rail":
        child.meters["on_top"] += 1
        child.meters["beyond_barrier"] += 1
    elif shortcut.id == "reach_through":
        child.meters["beyond_barrier"] += 1
    propagate(sim, narrate=False)
    return {
        "rhino_notice": sim.facts["rhino_notice"],
        "danger": sim.get("place").meters["danger"],
        "wobble": sim.get("child").meters["wobble"],
    }


def introduce(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"{setting.opener} {child.id} went with {child.pronoun('possessive')} {adult.label_word} to {setting.place}."
    )
    world.say(
        f"{setting.rhino_detail} {setting.sight_problem}"
    )


def wanting(world: World, child: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    need_line = {
        "closer": "wanted to be just a little closer",
        "higher": "wanted to see over the rail",
        "clearer": "wanted a clear look at the horn",
    }[setting.need]
    world.say(
        f"{child.id} stared and {need_line}. The rhinoceros looked calm and huge, the kind of huge that made the moment feel exciting and a little serious."
    )


def temptation(world: World, child: Entity, shortcut: Shortcut) -> None:
    child.memes["impulse"] += 1
    world.say(
        f'"I can {shortcut.action}," {child.id} whispered.'
    )


def warning(world: World, adult: Entity, child: Entity, shortcut: Shortcut, setting: Setting) -> None:
    pred = predict_risk(world, shortcut)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_rhino_notice"] = pred["rhino_notice"]
    world.facts["predicted_wobble"] = pred["wobble"]
    second = ""
    if pred["wobble"] >= THRESHOLD:
        second = " And if you wobble when he looks up, that could scare both of you."
    elif pred["danger"] >= THRESHOLD:
        second = " That line is there to keep muddy edges and animal space away from little feet and hands."
    elif pred["rhino_notice"]:
        second = " Big animals notice quick movements, even when they seem sleepy."
    world.say(
        f'{adult.label_word.capitalize()} shook {adult.pronoun("possessive")} head. "{shortcut.risk_text}{second} Stay with me."'
    )


def back_down(world: World, child: Entity, adult: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} looked at the line again, then at the rhinoceros, and stepped back beside {adult.label_word}. The exciting feeling was still there, but now it came with a small shiver of relief."
    )


def defy(world: World, child: Entity, shortcut: Shortcut) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But wanting a better look tugged harder. Before the thought could cool down, {child.id} {shortcut.past}."
    )


def do_shortcut(world: World, child: Entity, shortcut: Shortcut, setting: Setting) -> None:
    if shortcut.id == "duck_under":
        child.meters["beyond_barrier"] += 1
    elif shortcut.id == "climb_rail":
        child.meters["on_top"] += 1
        child.meters["beyond_barrier"] += 1
    elif shortcut.id == "reach_through":
        child.meters["beyond_barrier"] += 1
    propagate(world, narrate=False)

    if world.facts["rhino_notice"]:
        rhino = world.get("rhino")
        rhino.meters["near"] += 1
        world.say(
            f"The rhinoceros lifted {rhino.pronoun('possessive')} heavy head and turned toward the movement. For one long second, even the busy zoo sounds seemed to go quiet."
        )
    if world.facts["stumble_seen"]:
        world.say(
            f"{child.id}'s shoes scraped, and the rail gave a tiny, ugly shake."
        )
    elif world.facts["danger_seen"]:
        if setting.risk == "mud_edge":
            world.say(
                f"The dirt past the rope looked firmer than it was. One foot slid at the edge, and dark mud sucked softly under the sole."
            )
        elif setting.risk == "pinch_gap":
            world.say(
                f"The slats felt colder and closer than they had looked from back on the path, and the space suddenly seemed far too small for fingers."
            )
        else:
            world.say(
                f"All at once the place felt smaller and more dangerous than it had from the safe side."
            )


def rescue(world: World, adult: Entity, child: Entity, setting: Setting) -> None:
    child.meters["beyond_barrier"] = 0.0
    child.meters["on_top"] = 0.0
    world.get("place").meters["danger"] = 0.0
    child.meters["wobble"] = 0.0
    child.memes["fear"] += 1
    adult.memes["care"] += 1
    if setting.risk == "mud_edge":
        world.say(
            f'{adult.label_word.capitalize()} reached {adult.pronoun("object")} arm out fast and steady, guided {child.id} back over the line, and held onto {child.pronoun("possessive")} shoulder until both of them were still again.'
        )
    elif setting.risk == "wobble":
        world.say(
            f'{adult.label_word.capitalize()} caught {child.id} gently around the middle and lifted {child.pronoun("object")} down before the wobble could turn into a fall.'
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} folded {child.pronoun("possessive")} small hand back into {child.pronoun("possessive")} own and stepped with {child.pronoun("object")} away from the gate.'
        )


def lesson(world: World, adult: Entity, child: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f'"You were trying to see better, not be naughty," {adult.label_word} said once {child.id} was safe. "But zoo lines matter, especially near a rhinoceros. When a place is marked for safety, we listen to it."'
    )
    world.say(
        f"{child.id} nodded and pressed close for a moment, feeling the thump of a heart that was finally slowing down."
    )


def safe_view(world: World, adult: Entity, child: Entity, fix: SafeFix, setting: Setting) -> None:
    child.memes["wonder"] += 1
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    world.say(
        f"Then {adult.label_word} {fix.use_text}."
    )
    world.say(
        fix.ending_text
    )
    world.say(
        f"This time, {child.id} stayed where it was safe and watched the rhinoceros with both eyes wide open."
    )


def tell(setting: Setting, shortcut: Shortcut, fix: SafeFix,
         child_name: str = "Lily", child_gender: str = "girl",
         adult_type: str = "mother", trait: str = "careful") -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"name": child_name},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label=f"the {adult_type}",
        role="adult",
        attrs={},
    ))
    rhino = world.add(Entity(
        id="rhino",
        kind="thing",
        type="animal",
        label="rhinoceros",
        role="animal",
        attrs={"name": setting.rhino_name},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=setting.place,
        role="place",
        attrs={},
    ))

    child.memes["trust"] = 1.0 if trait in CALM_TRAITS else 0.0
    child.memes["fear"] = 0.0
    child.meters["beyond_barrier"] = 0.0
    child.meters["on_top"] = 0.0
    child.meters["wobble"] = 0.0
    rhino.meters["attention"] = 0.0
    rhino.meters["near"] = 0.0
    place.meters["danger"] = 0.0

    introduce(world, child, adult, setting)
    wanting(world, child, setting)

    world.para()
    temptation(world, child, shortcut)
    warning(world, adult, child, shortcut, setting)

    averted = would_avoid(trait, adult_type)
    if averted:
        back_down(world, child, adult)
        world.para()
        safe_view(world, adult, child, fix, setting)
        outcome = "averted"
    else:
        defy(world, child, shortcut)
        world.para()
        do_shortcut(world, child, shortcut, setting)
        rescue(world, adult, child, setting)
        lesson(world, adult, child)
        world.para()
        safe_view(world, adult, child, fix, setting)
        outcome = "near_miss"

    world.facts.update(
        child=child,
        adult=adult,
        rhino=rhino,
        place=place,
        setting_cfg=setting,
        shortcut_cfg=shortcut,
        fix_cfg=fix,
        outcome=outcome,
        child_name=child_name,
    )
    return world


KNOWLEDGE = {
    "rhinoceros": [(
        "What is a rhinoceros?",
        "A rhinoceros is a very large animal with thick skin and one or two horns on its nose. Even when it seems calm, it is powerful and needs lots of safe space."
    )],
    "zoo_safety": [(
        "Why do zoos have ropes, rails, and signs?",
        "Zoos use ropes, rails, and signs to keep people and animals safe from each other. The lines help everyone watch without getting too close."
    )],
    "patience": [(
        "Why is waiting sometimes the safest choice?",
        "Waiting can be the safest choice because it gives animals time to move on their own and lets grown-ups find a better plan. A safe view is still a good view."
    )],
    "step": [(
        "Why is a sturdy step better than climbing a rail?",
        "A sturdy step is made for standing still, but a rail is not. Using the right thing for the job helps your feet stay steady."
    )],
    "window": [(
        "Why is a window safer than reaching through a gate?",
        "A window lets you look closely without putting hands into an animal space. That keeps curious fingers safe."
    )],
    "rope": [(
        "Why should you stay behind a zoo rope?",
        "A zoo rope marks the safe side for visitors. The ground or animal space beyond it may be slippery, uneven, or too close to a big animal."
    )],
    "rail": [(
        "Why should children not stand on a rail?",
        "Rails help people lean and watch, but they are not little ladders. Standing on them can make you wobble and fall."
    )],
    "gate": [(
        "Why should you keep fingers out of gates and slats?",
        "Gaps near gates can pinch fingers, and they are part of the animal's space. Looking is fine, but reaching through is not."
    )],
}
KNOWLEDGE_ORDER = ["rhinoceros", "zoo_safety", "patience", "step", "window", "rope", "rail", "gate"]


@dataclass
class StoryParams:
    setting: str
    shortcut: str
    fix: str
    child_name: str
    child_gender: str
    adult: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    setting = f["setting_cfg"]
    shortcut = f["shortcut_cfg"]
    fix = f["fix_cfg"]
    if f["outcome"] == "averted":
        return [
            f'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "rhinoceros" and a moment of suspense at the zoo.',
            f"Tell a gentle cautionary story where {child.attrs['name']} wants to {shortcut.action}, but listens to {adult.label_word} and stays safe.",
            f"Write a story set at {setting.place} where a child feels tempted to break a safety rule, then uses {fix.label} instead.",
        ]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "rhinoceros" and a suspenseful near mistake at the zoo.',
        f"Tell a cautionary story where {child.attrs['name']} tries to {shortcut.action}, a grown-up helps in time, and the child learns why the rule matters.",
        f"Write a story set at {setting.place} where the ending image shows the child watching safely after using {fix.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    setting = f["setting_cfg"]
    shortcut = f["shortcut_cfg"]
    fix = f["fix_cfg"]
    name = child.attrs["name"]
    pw = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, {name}'s {pw}, and a rhinoceros at the zoo. The story follows an ordinary outing that turns tense for a moment."
        ),
        (
            "Why did the child want to break the rule?",
            f"{name} wanted a better look at the rhinoceros because {setting.sight_problem.lower()} The wish to see more clearly made the unsafe shortcut feel tempting."
        ),
        (
            f"What unsafe thing did {name} want to do?",
            f"{name} wanted to {shortcut.action}. {pw.capitalize()} warned that {shortcut.risk_text.lower()}"
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How did {name} stay safe?",
            f"{name} listened to {pw} and stepped back instead of taking the shortcut. Then they used {fix.phrase}, which solved the same problem without crossing the safety line."
        ))
        qa.append((
            "How did the story end?",
            f"It ended calmly, with {name} watching the rhinoceros from a safe spot. The ending proves that patience and safe choices still led to a close, exciting look."
        ))
    else:
        if f.get("rhino_notice"):
            qa.append((
                f"What made the moment feel scary?",
                f"The rhinoceros noticed the quick movement and turned its heavy head toward {name}. That sudden attention made the quiet feel sharp and showed why the rule was there."
            ))
        qa.append((
            f"How did {pw} help?",
            f"{pw.capitalize()} moved quickly and brought {name} back to the safe side before the danger could grow. After that, {pw} explained that zoo lines matter especially near a rhinoceros."
        ))
        qa.append((
            "What changed by the end?",
            f"At first {name} wanted a risky shortcut, but by the end {name} used {fix.phrase} and watched safely. The last image shows a child who learned to trade a fast choice for a careful one."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rhinoceros", "zoo_safety"}
    tags |= set(world.facts["setting_cfg"].tags)
    tags |= set(world.facts["shortcut_cfg"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="yard",
        shortcut="duck_under",
        fix="bench_mark",
        child_name="Lily",
        child_gender="girl",
        adult="mother",
        trait="careful",
    ),
    StoryParams(
        setting="barn",
        shortcut="climb_rail",
        fix="step_block",
        child_name="Leo",
        child_gender="boy",
        adult="father",
        trait="impulsive",
    ),
    StoryParams(
        setting="gate",
        shortcut="reach_through",
        fix="quiet_window",
        child_name="Maya",
        child_gender="girl",
        adult="grandfather",
        trait="patient",
    ),
    StoryParams(
        setting="yard",
        shortcut="duck_under",
        fix="bench_mark",
        child_name="Finn",
        child_gender="boy",
        adult="grandmother",
        trait="bouncy",
    ),
]


def explain_rejection(setting: Setting, shortcut: Shortcut, fix_id: Optional[str] = None) -> str:
    if not shortcut_works(setting, shortcut):
        return (
            f"(No story: {shortcut.action} does not fit {setting.place}. "
            f"This setting uses a {setting.barrier} barrier and a different kind of temptation.)"
        )
    if fix_id is not None and select_fix(setting, fix_id) is None:
        return (
            f"(No story: {SAFE_FIXES[fix_id].label} does not solve the viewing problem at {setting.place}. "
            f"The safe fix must help with {setting.need} while respecting the {setting.barrier} barrier.)"
        )
    return "(No story: the requested combination is unreasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avoid(params.trait, params.adult) else "near_miss"


ASP_RULES = r"""
% --- valid combinations ----------------------------------------------------
shortcut_works(S, C) :- setting(S), shortcut(C), barrier_of(S, B), uses_barrier(C, B),
                        need_of(S, N), helps(C, N).
fix_works(S, F)      :- setting(S), fix(F), barrier_of(S, B), safe_for(F, B),
                        need_of(S, N), helps_fix(F, N).
valid(S, C, F)       :- shortcut_works(S, C), fix_works(S, F).

% --- outcome model ---------------------------------------------------------
calm(T)              :- trait(T), calm_trait(T).
adult_bonus(1)       :- adult_type(A), grand_adult(A).
adult_bonus(0)       :- adult_type(A), not grand_adult(A).
trait_points(3)      :- trait(T), calm(T).
trait_points(1)      :- trait(T), not calm(T).
avoid_score(P + B)   :- trait_points(P), adult_bonus(B).
outcome(averted)     :- avoid_score(S), S >= 3.
outcome(near_miss)   :- avoid_score(S), S < 3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("barrier_of", setting_id, setting.barrier))
        lines.append(asp.fact("need_of", setting_id, setting.need))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        for barrier in sorted(shortcut.barriers):
            lines.append(asp.fact("uses_barrier", shortcut_id, barrier))
        for need in sorted(shortcut.helps):
            lines.append(asp.fact("helps", shortcut_id, need))
    for fix_id, fix in SAFE_FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for barrier in sorted(fix.barriers):
            lines.append(asp.fact("safe_for", fix_id, barrier))
        for need in sorted(fix.helps):
            lines.append(asp.fact("helps_fix", fix_id, need))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    for adult_type in ["mother", "father", "grandmother", "grandfather"]:
        lines.append(asp.fact("adult_kind", adult_type))
    for adult_type in ["grandmother", "grandfather"]:
        lines.append(asp.fact("grand_adult", adult_type))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("adult_type", params.adult),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a zoo visit, a rhinoceros, an unsafe shortcut, and a safer way to keep looking."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--fix", choices=SAFE_FIXES)
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.shortcut:
        setting = SETTINGS[args.setting]
        shortcut = SHORTCUTS[args.shortcut]
        if not shortcut_works(setting, shortcut):
            raise StoryError(explain_rejection(setting, shortcut))
    if args.setting and args.fix:
        if select_fix(SETTINGS[args.setting], args.fix) is None:
            shortcut = SHORTCUTS[args.shortcut] if args.shortcut else next(iter(SHORTCUTS.values()))
            raise StoryError(explain_rejection(SETTINGS[args.setting], shortcut, args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shortcut_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        shortcut=shortcut_id,
        fix=fix_id,
        child_name=name,
        child_gender=gender,
        adult=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Invalid shortcut: {params.shortcut})")
    if params.fix not in SAFE_FIXES:
        raise StoryError(f"(Invalid fix: {params.fix})")
    setting = SETTINGS[params.setting]
    shortcut = SHORTCUTS[params.shortcut]
    fix = select_fix(setting, params.fix)
    if not shortcut_works(setting, shortcut):
        raise StoryError(explain_rejection(setting, shortcut))
    if fix is None:
        raise StoryError(explain_rejection(setting, shortcut, params.fix))

    world = tell(
        setting=setting,
        shortcut=shortcut,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult,
        trait=params.trait,
    )
    story = world.render().replace("child", params.child_name)
    story = story.replace("adult", world.get("adult").label_word)
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combos match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, shortcut, fix) combos:\n")
        for setting_id, shortcut_id, fix_id in combos:
            print(f"  {setting_id:6} {shortcut_id:13} {fix_id}")
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
            header = f"### {p.child_name}: {p.setting}, {p.shortcut}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
