#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py
====================================================================

A standalone storyworld about a child who turns lunch into a superhero mission.
The world models a risky lunch leap, a grounded warning, a spill, and a repair
or loss depending on how big the mess becomes and how good the grown-up response
is.

The style stays close to a child-facing superhero story, with gentle rhyme woven
through the prose:
- premise: a heroic lunch game begins
- tension: a child wants to leap with lunch from a perch
- turn: the lunch spills
- resolution: a grown-up helps, and the child learns that careful heroes walk

Run it
------
    python storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py
    python storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py --lunch soup --perch bench
    python storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py --perch floor_dot
    python storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py --response superhero_spin
    python storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/lunch_rhyme_cautionary_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    squad: str
    opening: str
    title: str
    mission: str
    boast: str
    ending: str
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
class LunchItem:
    id: str
    label: str
    phrase: str
    spill: int
    splash_word: str
    loss_line: str
    save_line: str
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
class Perch:
    id: str
    label: str
    phrase: str
    height: int
    landing: str
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


def _r_spill_effects(world: World) -> list[str]:
    out: list[str] = []
    lunch = world.get("lunch")
    if lunch.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill_effects",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    buddy = world.get("buddy")
    floor = world.get("floor")
    grownup = world.get("grownup")
    floor.meters["slippery"] += 1
    floor.meters["mess"] += 1
    hero.meters["hungry"] += 1
    lunch.meters["lost"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["worry"] += 1
    buddy.memes["worry"] += 1
    grownup.meters["workload"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill_effects", tag="physical", apply=_r_spill_effects),
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


THEMES = {
    "sky_squad": Theme(
        id="sky_squad",
        squad="Sky Squad",
        opening="the long lunch tables looked like rooftops above a busy city",
        title="Captain Comet",
        mission="to deliver lunch to the corner seat before the bell could chime",
        boast='"To the rescue in a whooshing streak!"',
        ending="kept the Sky Squad brave and bright",
        tags={"superhero"},
    ),
    "moon_guard": Theme(
        id="moon_guard",
        squad="Moon Guard",
        opening="the lunchroom tiles looked like silver streets on the moon",
        title="Meteor Mask",
        mission="to carry lunch across the room like a hero on patrol",
        boast='"Moon Guard zooms with fearless feet!"',
        ending="made the Moon Guard steady and right",
        tags={"superhero"},
    ),
    "city_shield": Theme(
        id="city_shield",
        squad="City Shield",
        opening="the benches felt like towers over Hero City at noon",
        title="Thunder Cape",
        mission="to bring lunch to a waiting friend like a hero on a shining route",
        boast='"City Shield is faster than a flash!"',
        ending="showed that real heroes think before they dash",
        tags={"superhero"},
    ),
}

LUNCHES = {
    "soup": LunchItem(
        id="soup",
        label="soup",
        phrase="a warm cup of tomato soup and crackers",
        spill=3,
        splash_word="splish-soup swoop",
        loss_line="The red soup ran away in a slippery loop.",
        save_line="Most of the crackers stayed dry, and a fresh cup soon came by.",
        tags={"soup", "hot_food", "lunch"},
    ),
    "milk": LunchItem(
        id="milk",
        label="milk",
        phrase="a carton of milk and a cheese sandwich",
        spill=2,
        splash_word="slosh-slosh plop",
        loss_line="The milk spread shiny and white across the tile.",
        save_line="The sandwich stayed safe, and lunch was back in place after a little while.",
        tags={"milk", "lunch"},
    ),
    "noodles": LunchItem(
        id="noodles",
        label="noodles",
        phrase="a bowl of butter noodles and peas",
        spill=2,
        splash_word="twirl-whirl flop",
        loss_line="The noodles slid down in a buttery heap.",
        save_line="A few peas rolled free, but most of lunch was still theirs to keep.",
        tags={"noodles", "lunch"},
    ),
    "apple": LunchItem(
        id="apple",
        label="apple",
        phrase="an apple, a muffin, and a folded napkin",
        spill=0,
        splash_word="tap-tap bop",
        loss_line="Nothing much spilled at all.",
        save_line="Nothing much needed saving at all.",
        tags={"apple", "lunch"},
    ),
}

PERCHES = {
    "bench": Perch(
        id="bench",
        label="bench",
        phrase="the blue lunch bench",
        height=2,
        landing="the shiny floor below",
        tags={"bench"},
    ),
    "steps": Perch(
        id="steps",
        label="steps",
        phrase="the little stage steps by the wall",
        height=1,
        landing="the floor by the reading corner",
        tags={"steps"},
    ),
    "low_wall": Perch(
        id="low_wall",
        label="low wall",
        phrase="the low brick wall near the garden door",
        height=2,
        landing="the hard path beside the door",
        tags={"wall"},
    ),
    "floor_dot": Perch(
        id="floor_dot",
        label="floor dot",
        phrase="a painted dot on the floor",
        height=0,
        landing="the same floor",
        tags={"floor"},
    ),
}

RESPONSES = {
    "spare_tray": Response(
        id="spare_tray",
        sense=3,
        power=4,
        text="slid in with a spare tray, caught what could be saved, and wiped the slick floor before anyone slipped",
        fail="hurried over with a spare tray, but the lunch had already splashed too far to save",
        qa_text="used a spare tray and quick wiping to save the situation",
        tags={"tray", "cleanup"},
    ),
    "steady_hands": Response(
        id="steady_hands",
        sense=3,
        power=3,
        text="took the tray with steady hands, set it down safely, and dabbed up the spill with fast paper towels",
        fail="reached with steady hands, but the spill was already racing over the floor",
        qa_text="used steady hands and paper towels to stop the mess",
        tags={"paper_towels", "cleanup"},
    ),
    "towels_only": Response(
        id="towels_only",
        sense=2,
        power=2,
        text="covered the puddle with paper towels and kept other children back until the floor was dry again",
        fail="threw down paper towels, but too much lunch had already splashed away",
        qa_text="used paper towels to clean the floor and keep everyone safe",
        tags={"paper_towels", "cleanup"},
    ),
    "superhero_spin": Response(
        id="superhero_spin",
        sense=1,
        power=1,
        text="spun around with superhero arms and tried to fan the mess into one corner",
        fail="spun around with superhero arms, which did not help the spill at all",
        qa_text="tried a superhero spin",
        tags={"cleanup"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ruby", "Ella", "June"]
BOY_NAMES = ["Max", "Leo", "Sam", "Eli", "Noah", "Finn", "Theo", "Jack"]
TRAITS = ["careful", "bold", "bouncy", "kind", "curious", "swift"]


def risky_combo(lunch: LunchItem, perch: Perch) -> bool:
    return lunch.spill > 0 and perch.height > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(lunch: LunchItem, perch: Perch, delay: int) -> int:
    return lunch.spill + perch.height + delay


def is_contained(response: Response, lunch: LunchItem, perch: Perch, delay: int) -> bool:
    return response.power >= spill_severity(lunch, perch, delay)


def predict_spill(world: World, lunch: LunchItem, perch: Perch) -> dict:
    sim = world.copy()
    _do_leap(sim, lunch=lunch, perch=perch, narrate=False)
    return {
        "spills": sim.get("lunch").meters["spilled"] >= THRESHOLD,
        "slippery": sim.get("floor").meters["slippery"] >= THRESHOLD,
        "hungry": sim.get("hero").meters["hungry"] >= THRESHOLD,
    }


def _do_leap(world: World, lunch: LunchItem, perch: Perch, narrate: bool = True) -> None:
    hero = world.get("hero")
    tray = world.get("lunch")
    hero.meters["jumped"] += 1
    tray.meters["spilled"] += 1
    tray.meters["severity"] = float(spill_severity(lunch, perch, int(world.facts.get("delay", 0))))
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, buddy: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f"At lunch, {theme.opening}. {hero.id} knotted a napkin like a cape and called "
        f"{hero.pronoun('object')}self {theme.title}, while {buddy.id} marched beside "
        f"{hero.pronoun('object')} in the {theme.squad}."
    )
    world.say(
        f"They whispered that today's mission was {theme.mission}. It was a game at noon, "
        f"all gleam and swoon, a tiny heroic tune."
    )


def show_lunch(world: World, hero: Entity, lunch: LunchItem) -> None:
    world.say(
        f"{hero.id} carried {lunch.phrase} for lunch. The tray smelled good, and the warm food "
        f"made the whole room feel cozy and bright."
    )


def tempt(world: World, hero: Entity, perch: Perch, theme: Theme) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f"Then {hero.id} climbed onto {perch.phrase} and pointed at {perch.landing}. "
        f"{theme.boast} {hero.id} cried. 'I'll leap from here and land by the seat in one neat beat!'"
    )


def warn(world: World, buddy: Entity, hero: Entity, lunch: LunchItem, perch: Perch, grownup: Entity) -> None:
    pred = predict_spill(world, lunch=lunch, perch=perch)
    world.facts["predicted_spill"] = pred["spills"]
    buddy.memes["caution"] += 1
    cause = f"from {perch.phrase} with {lunch.label} in {hero.pronoun('possessive')} hands"
    world.say(
        f"{buddy.id} tugged the cape and shook {buddy.pronoun('possessive')} head. "
        f"'{hero.id}, do not leap {cause}. If you jump, your lunch may tip and slide, "
        f"and the floor may turn slick and wide.'"
    )
    world.say(
        f"{grownup.label_word.capitalize()} was helping nearby, and even without hearing every word, "
        f"{buddy.id} knew the warning was wise."
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the game felt grand, and the cape felt fast. {hero.id} bent {hero.pronoun('possessive')} knees, "
        f"took one proud breath, and jumped at last."
    )


def spill(world: World, hero: Entity, lunch: LunchItem, perch: Perch) -> None:
    _do_leap(world, lunch=lunch, perch=perch, narrate=False)
    world.say(
        f"Down came the tray in a {lunch.splash_word}. One foot hit {perch.landing}, then the cup tipped over. "
        f"{lunch.loss_line}"
    )
    world.say(
        f"{hero.id}'s cape drooped low. {hero.pronoun().capitalize()} was not flying now; "
        f"{hero.pronoun()} was staring at the slippery mess below."
    )


def alarm(world: World, buddy: Entity, grownup: Entity) -> None:
    world.say(
        f"'{grownup.label_word.capitalize()}!' called {buddy.id}. 'Please help! The floor is slippery and the lunch is down!'"
    )


def rescue(world: World, grownup: Entity, response: Response, lunch: LunchItem, hero: Entity, buddy: Entity) -> None:
    floor = world.get("floor")
    tray = world.get("lunch")
    floor.meters["slippery"] = 0.0
    floor.meters["mess"] = 0.0
    hero.meters["hungry"] = 0.0
    tray.meters["saved"] += 1
    tray.meters["lost"] = 0.0
    hero.memes["relief"] += 1
    buddy.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} came quickly and {response.text}. {lunch.save_line}"
    )
    world.say(
        f"Then {grownup.label_word} knelt by {hero.id} and spoke in a calm voice. "
        f"'A real hero protects people first. At lunch, brave feet walk, not leap.'"
    )


def rescue_fail(world: World, grownup: Entity, response: Response, hero: Entity, buddy: Entity) -> None:
    hero.memes["sadness"] += 1
    buddy.memes["sadness"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} hurried over and {response.fail}. The floor had to be blocked off "
        f"until it was safe again."
    )
    world.say(
        f"{hero.id}'s lunch was gone, and the superhero game was done. The room grew quiet after the rush."
    )


def lesson(world: World, grownup: Entity, hero: Entity, buddy: Entity) -> None:
    world.say(
        f"{grownup.label_word.capitalize()} gave {hero.id} a gentle hug with one arm and thanked {buddy.id} for calling right away. "
        f"'Fast help keeps small troubles small,' {grownup.pronoun()} said."
    )


def ending_happy(world: World, hero: Entity, buddy: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f"After that, {hero.id} carried lunch with two steady hands and walked beside {buddy.id}. "
        f"They still played heroes, but now the hero rule was clear and bright: careful steps {theme.ending}."
    )
    world.say(
        f"And when the lunch bell rang the next day, {hero.id} smiled at the bench, chose the floor, and said, "
        f"'Strong and kind is how I fly. I do not leap with lunch sky-high.'"
    )


def ending_sad(world: World, hero: Entity, buddy: Entity, theme: Theme) -> None:
    world.say(
        f"Later, when the floor was dry and the room was calm, {hero.id} sat with a plain backup snack and thought about the jump. "
        f"{buddy.id} stayed close, and the cape rested folded in {hero.pronoun('possessive')} lap."
    )
    world.say(
        f"From then on, the {theme.squad} had a new rule at lunch: no soaring with soup, no dashing with drink, "
        f"because real heroes stop and think."
    )


def tell(
    theme: Theme,
    lunch: LunchItem,
    perch: Perch,
    response: Response,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    buddy_name: str = "Max",
    buddy_gender: str = "boy",
    grownup_type: str = "teacher",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    buddy = world.add(Entity(id="buddy", kind="character", type=buddy_gender, label=buddy_name, role="buddy", traits=["careful"]))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label=grownup_type, role="grownup"))
    world.add(Entity(id="floor", kind="thing", type="floor", label="the floor"))
    lunch_ent = world.add(Entity(id="lunch", kind="thing", type="lunch", label=lunch.label))
    lunch_ent.meters["amount"] = 1.0

    world.facts["delay"] = delay

    intro(world, hero=hero, buddy=buddy, theme=theme)
    show_lunch(world, hero=hero, lunch=lunch)

    world.para()
    tempt(world, hero=hero, perch=perch, theme=theme)
    warn(world, buddy=buddy, hero=hero, lunch=lunch, perch=perch, grownup=grownup)
    defy(world, hero=hero)

    world.para()
    spill(world, hero=hero, lunch=lunch, perch=perch)
    alarm(world, buddy=buddy, grownup=grownup)

    contained = is_contained(response=response, lunch=lunch, perch=perch, delay=delay)

    world.para()
    if contained:
        rescue(world, grownup=grownup, response=response, lunch=lunch, hero=hero, buddy=buddy)
        lesson(world, grownup=grownup, hero=hero, buddy=buddy)
        world.para()
        ending_happy(world, hero=hero, buddy=buddy, theme=theme)
    else:
        rescue_fail(world, grownup=grownup, response=response, hero=hero, buddy=buddy)
        lesson(world, grownup=grownup, hero=hero, buddy=buddy)
        world.para()
        ending_sad(world, hero=hero, buddy=buddy, theme=theme)

    world.facts.update(
        hero=hero,
        buddy=buddy,
        grownup=grownup,
        theme=theme,
        lunch_cfg=lunch,
        perch=perch,
        response=response,
        contained=contained,
        outcome="contained" if contained else "ruined",
        severity=spill_severity(lunch=lunch, perch=perch, delay=delay),
        jumped=hero.meters["jumped"] >= THRESHOLD,
        spill=lunch_ent.meters["spilled"] >= THRESHOLD,
        lunch_saved=lunch_ent.meters["saved"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for lunch_id, lunch in LUNCHES.items():
            for perch_id, perch in PERCHES.items():
                if risky_combo(lunch=lunch, perch=perch):
                    combos.append((theme_id, lunch_id, perch_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    lunch: str
    perch: str
    response: str
    hero_name: str
    hero_gender: str
    buddy_name: str
    buddy_gender: str
    grownup: str
    trait: str
    delay: int = 0
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
    "superhero": [
        (
            "What makes someone a real hero?",
            "A real hero keeps people safe and makes thoughtful choices. Being careful can be braver than showing off."
        )
    ],
    "lunch": [
        (
            "Why should we carry lunch carefully?",
            "Lunch can spill if it tips or bumps into something. Careful hands keep food on the tray and the floor safe to walk on."
        )
    ],
    "soup": [
        (
            "Why is soup easy to spill?",
            "Soup is liquid, so it moves and sloshes when a cup tilts. That is why walking slowly matters."
        )
    ],
    "milk": [
        (
            "Why can milk make the floor slippery?",
            "Milk spreads quickly over a smooth floor. If nobody wipes it up, someone could slip."
        )
    ],
    "noodles": [
        (
            "Why are noodles messy when they fall?",
            "Noodles slide and scatter when a bowl tips over. That can leave a slippery, squishy mess."
        )
    ],
    "tray": [
        (
            "What is a lunch tray for?",
            "A lunch tray helps carry food in one flat place. It makes it easier to keep lunch balanced."
        )
    ],
    "paper_towels": [
        (
            "Why do people use paper towels for spills?",
            "Paper towels soak up liquid and help dry the floor. Cleaning a spill fast keeps people safe."
        )
    ],
    "cleanup": [
        (
            "What should you do if lunch spills?",
            "Stop moving, call a grown-up, and keep other people away from the slippery spot. Quick help can stop a small mess from becoming a bigger one."
        )
    ],
}
KNOWLEDGE_ORDER = ["superhero", "lunch", "soup", "milk", "noodles", "tray", "paper_towels", "cleanup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    lunch = f["lunch_cfg"]
    perch = f["perch"]
    theme = f["theme"]
    if f["contained"]:
        return [
            f'Write a rhyming superhero lunch story for a 3-to-5-year-old that includes the word "lunch".',
            f"Tell a cautionary story where {hero.label} pretends to be a superhero, leaps from {perch.phrase} with {lunch.label}, spills it, and then learns the safer way.",
            f"Write a child-facing superhero tale in which {buddy.label} warns {hero.label} and a grown-up helps turn a lunch accident into a lesson."
        ]
    return [
        f'Write a rhyming cautionary superhero story for a 3-to-5-year-old that includes the word "lunch".',
        f"Tell a story where {hero.label} makes a show-off superhero jump from {perch.phrase} with {lunch.label}, and the lunch is lost.",
        f"Write a gentle but cautionary lunch story in superhero style, with a warning from {buddy.label} and an ending where the hero learns to stop and think."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    grownup = f["grownup"]
    lunch = f["lunch_cfg"]
    perch = f["perch"]
    response = f["response"]
    theme = f["theme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who played superhero at lunch, and {buddy.label}, who tried to warn {hero.pronoun('object')}. "
            f"The {theme.squad} game made the jump feel exciting."
        ),
        (
            f"Why did {buddy.label} warn {hero.label} not to jump?",
            f"{buddy.label} knew that leaping from {perch.phrase} with {lunch.label} could tip the tray and spill lunch. "
            f"A spill would also make the floor slippery, so the warning was about safety as well as food."
        ),
        (
            f"What happened when {hero.label} jumped?",
            f"The tray tipped and the {lunch.label} spilled onto the floor. "
            f"That turned the heroic game into a real lunch problem because the mess was slippery and the food was in danger."
        ),
    ]
    if f["contained"]:
        qa.append(
            (
                f"How did the {grownup.label_word} help?",
                f"The {grownup.label_word} {response.qa_text}. "
                f"That quick help kept the floor safe and let {hero.label} keep having lunch instead of losing it all."
            )
        )
        qa.append(
            (
                f"What did {hero.label} learn by the end?",
                f"{hero.label} learned that real heroes do not leap with lunch. "
                f"By the end, {hero.pronoun()} showed the lesson by walking carefully with two steady hands."
            )
        )
    else:
        qa.append(
            (
                f"Could the {grownup.label_word} save the lunch?",
                f"No. By the time help arrived, too much had already spilled away. "
                f"The cleanup kept everyone safe, but the superhero jump still cost {hero.label} the lunch."
            )
        )
        qa.append(
            (
                f"What did {hero.label} learn by the end?",
                f"{hero.label} learned that showing off can spoil lunch and make trouble for other people too. "
                f"The new hero rule was to stop, think, and walk carefully."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["theme"].tags) | set(f["lunch_cfg"].tags) | set(f["response"].tags) | {"cleanup"}
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="sky_squad",
        lunch="soup",
        perch="bench",
        response="spare_tray",
        hero_name="Mia",
        hero_gender="girl",
        buddy_name="Max",
        buddy_gender="boy",
        grownup="teacher",
        trait="bouncy",
        delay=0,
    ),
    StoryParams(
        theme="moon_guard",
        lunch="milk",
        perch="steps",
        response="steady_hands",
        hero_name="Leo",
        hero_gender="boy",
        buddy_name="Ava",
        buddy_gender="girl",
        grownup="teacher",
        trait="bold",
        delay=0,
    ),
    StoryParams(
        theme="city_shield",
        lunch="soup",
        perch="low_wall",
        response="towels_only",
        hero_name="Ruby",
        hero_gender="girl",
        buddy_name="Finn",
        buddy_gender="boy",
        grownup="teacher",
        trait="swift",
        delay=1,
    ),
    StoryParams(
        theme="sky_squad",
        lunch="noodles",
        perch="bench",
        response="steady_hands",
        hero_name="Theo",
        hero_gender="boy",
        buddy_name="June",
        buddy_gender="girl",
        grownup="teacher",
        trait="curious",
        delay=0,
    ),
]


def explain_rejection(lunch: LunchItem, perch: Perch) -> str:
    if perch.height <= 0:
        return (
            f"(No story: {perch.phrase} is not really a perch to leap from. "
            f"Without height, there is no meaningful lunch-jump danger.)"
        )
    if lunch.spill <= 0:
        return (
            f"(No story: {lunch.phrase} is too steady for this cautionary lunch spill tale. "
            f"Pick a spillable lunch like soup, milk, or noodles.)"
        )
    return "(No story: this lunch leap has no real spill risk.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a more sensible response: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(RESPONSES[params.response], LUNCHES[params.lunch], PERCHES[params.perch], params.delay) else "ruined"


ASP_RULES = r"""
risky(L,P) :- lunch(L), spill(L,S), S > 0, perch(P), height(P,H), H > 0.
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,L,P) :- theme(T), risky(L,P).

severity(V) :- chosen_lunch(L), chosen_perch(P), chosen_delay(D),
               spill(L,S), height(P,H), V = S + H + D.
contained :- chosen_response(R), power(R,P), severity(V), P >= V.
outcome(contained) :- contained.
outcome(ruined) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for lid, lunch in LUNCHES.items():
        lines.append(asp.fact("lunch", lid))
        lines.append(asp.fact("spill", lid, lunch.spill))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("height", pid, perch.height))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_lunch", params.lunch),
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


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

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(80):
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
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming superhero lunch leap. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--lunch", choices=LUNCHES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["teacher", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the spill gets before help arrives")
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and args.lunch:
        lunch = LUNCHES[args.lunch]
        perch = PERCHES[args.perch]
        if not risky_combo(lunch=lunch, perch=perch):
            raise StoryError(explain_rejection(lunch=lunch, perch=perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.lunch is None or combo[1] == args.lunch)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, lunch, perch = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_name(rng)
    buddy_name, buddy_gender = _pick_name(rng, avoid=hero_name)
    grownup = args.grownup or "teacher"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        theme=theme,
        lunch=lunch,
        perch=perch,
        response=response,
        hero_name=hero_name,
        hero_gender=hero_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.lunch not in LUNCHES:
        raise StoryError(f"(Unknown lunch: {params.lunch})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    lunch = LUNCHES[params.lunch]
    perch = PERCHES[params.perch]
    response = RESPONSES[params.response]

    if not risky_combo(lunch=lunch, perch=perch):
        raise StoryError(explain_rejection(lunch=lunch, perch=perch))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        lunch=lunch,
        perch=perch,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        grownup_type=params.grownup,
        trait=params.trait,
        delay=params.delay,
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
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, lunch, perch) combos:\n")
        for theme, lunch, perch in combos:
            print(f"  {theme:10} {lunch:8} {perch}")
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
            header = f"### {p.hero_name}: {p.lunch} from {p.perch} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
