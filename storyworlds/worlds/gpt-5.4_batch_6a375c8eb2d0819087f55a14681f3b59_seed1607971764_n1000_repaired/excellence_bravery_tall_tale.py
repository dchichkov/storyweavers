#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py
==========================================================

A standalone story world for a child-sized tall tale about bravery, preparation,
and excellence on the wide old frontier.

Premise
-------
A brave child in an exaggerated prairie world must climb to a lookout bell
before a storm rolls in, so ranch hands and animals know to come home. The path
holds one outsized obstacle. The child is given fitting gear and a sturdy animal
helper, and the story's turn comes from whether that pairing is merely good
enough for a hard climb or whether the child must also blow a whistle and bring
the whole ranch together.

This world prefers *reasonable* combinations:
- the chosen obstacle must belong to the chosen setting
- the tool must actually counter that obstacle
- the animal helper must be suited to that obstacle too

The model then decides whether the child:
- reaches the bell alone in a big tall-tale triumph, or
- makes a brave start and wisely calls for help, turning the ending into a
  teamwork story instead of a foolish solo stunt

Run it
------
    python storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py
    python storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py --trace
    python storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py --asp
    python storyworlds/worlds/gpt-5.4/excellence_bravery_tall_tale.py --verify
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
from io import StringIO
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    bell_place: str
    horizon: str
    town_name: str
    afford_obstacles: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    phrase: str
    hurdle: str
    scene: str
    severity: int
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
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    power: int
    guards: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    phrase: str
    move_line: str
    bonus: int
    fits: set[str] = field(default_factory=set)
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


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    path = world.get("path")
    bell = world.get("bell")
    if hero.meters["push"] < THRESHOLD:
        return out
    if hero.meters["stuck"] >= THRESHOLD:
        return out
    if hero.meters["progress"] >= THRESHOLD:
        return out
    sig = ("progress",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["progress"] += 1
    path.meters["crossed"] += 1
    bell.meters["reachable"] += 1
    out.append("__progress__")
    return out


def _r_ring(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    bell = world.get("bell")
    town = world.get("town")
    if bell.meters["reachable"] < THRESHOLD or hero.meters["ring_attempt"] < THRESHOLD:
        return out
    if bell.meters["rung"] >= THRESHOLD:
        return out
    sig = ("ring",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bell.meters["rung"] += 1
    town.meters["gathering"] += 1
    hero.memes["pride"] += 1
    out.append("__bell__")
    return out


def _r_gather(world: World) -> list[str]:
    out: list[str] = []
    bell = world.get("bell")
    town = world.get("town")
    if bell.meters["rung"] < THRESHOLD or town.meters["home"] >= THRESHOLD:
        return out
    sig = ("gather",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    town.meters["home"] += 1
    town.memes["relief"] += 1
    out.append("__home__")
    return out


CAUSAL_RULES = [
    Rule(name="progress", tag="physical", apply=_r_progress),
    Rule(name="ring", tag="physical", apply=_r_ring),
    Rule(name="gather", tag="social", apply=_r_gather),
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


SETTINGS = {
    "prairie_ranch": Setting(
        id="prairie_ranch",
        place="the wide prairie ranch",
        bell_place="a lookout hill with a supper bell on top",
        horizon="The grass rolled away so far it looked as if the earth had put on a green blanket and forgotten where to tuck it in.",
        town_name="Brushy Creek",
        afford_obstacles={"mud_slope", "wind_gap"},
        tags={"prairie", "ranch"},
    ),
    "mesa_farm": Setting(
        id="mesa_farm",
        place="the red-dirt mesa farm",
        bell_place="a stony rise with a brass bell on top",
        horizon="The mesas stood so tall they seemed to be propping up the sky with their flat red shoulders.",
        town_name="Juniper Flat",
        afford_obstacles={"wind_gap", "cactus_wash"},
        tags={"mesa", "farm"},
    ),
    "canyon_station": Setting(
        id="canyon_station",
        place="the canyon way-station",
        bell_place="a cliffside bell post above the trail",
        horizon="The canyon walls leaned in so close and so high that even an echo had to climb to catch its breath.",
        town_name="Copper Bend",
        afford_obstacles={"cactus_wash", "mud_slope"},
        tags={"canyon", "station"},
    ),
}

OBSTACLES = {
    "mud_slope": Obstacle(
        id="mud_slope",
        label="mud slope",
        phrase="a mud slope slick as fresh pudding",
        hurdle="the hill had turned slippery after a hard splash of rain",
        scene="Every step wanted to slide backward as if the whole hill were trying to creep home on its own.",
        severity=4,
        tags={"mud", "storm"},
    ),
    "wind_gap": Obstacle(
        id="wind_gap",
        label="wind gap",
        phrase="a wind gap that whooped and shoved",
        hurdle="a narrow pass where the wind liked to practice wrestling",
        scene="The gusts came barreling through so fiercely they could have blown the freckles off a scarecrow.",
        severity=5,
        tags={"wind", "storm"},
    ),
    "cactus_wash": Obstacle(
        id="cactus_wash",
        label="cactus wash",
        phrase="a cactus wash bristling with thorns",
        hurdle="a dry wash lined with poky pear and jumpy burrs",
        scene="The prickles stood so thick they looked like the wash had grown a hundred green porcupines overnight.",
        severity=3,
        tags={"cactus", "thorn"},
    ),
}

TOOLS = {
    "cleat_boots": Tool(
        id="cleat_boots",
        label="cleat boots",
        phrase="a pair of cleat boots with teeth on the soles",
        use_line="drove those boot teeth into the ground and held fast",
        power=2,
        guards={"mud_slope"},
        tags={"boots", "gear"},
    ),
    "sail_cloak": Tool(
        id="sail_cloak",
        label="sail cloak",
        phrase="a sail cloak with little lead beads sewn in the hem",
        use_line="wrapped the cloak close and let the weighted hem keep the wind from bossing the day around",
        power=2,
        guards={"wind_gap"},
        tags={"cloak", "wind"},
    ),
    "cowhide_chaps": Tool(
        id="cowhide_chaps",
        label="cowhide chaps",
        phrase="thick cowhide chaps shiny from good oil",
        use_line="let the thorns scrape the leather instead of skin",
        power=2,
        guards={"cactus_wash"},
        tags={"chaps", "leather"},
    ),
    "spiral_spurs": Tool(
        id="spiral_spurs",
        label="spiral spurs",
        phrase="spiral spurs that bit the earth in neat little stars",
        use_line="clicked the spurs against the slope and found a grip where there should not have been any",
        power=1,
        guards={"mud_slope", "cactus_wash"},
        tags={"spurs", "gear"},
    ),
    "storm_goggles": Tool(
        id="storm_goggles",
        label="storm goggles",
        phrase="storm goggles clear as creek ice",
        use_line="kept eyes open wide even while the air tried to slap them shut",
        power=1,
        guards={"wind_gap"},
        tags={"goggles", "wind"},
    ),
}

HELPERS = {
    "mule": Helper(
        id="mule",
        label="mule",
        phrase="Old Blue the mule, steady as a fence post",
        move_line="Old Blue planted each hoof as if he were signing his name on the land.",
        bonus=1,
        fits={"mud_slope", "cactus_wash"},
        tags={"mule", "animal"},
    ),
    "goat": Helper(
        id="goat",
        label="goat",
        phrase="Pepper the goat, nimble as a skipped stone",
        move_line="Pepper danced from stone to stone like the path had been built just for goat feet.",
        bonus=1,
        fits={"wind_gap", "cactus_wash"},
        tags={"goat", "animal"},
    ),
    "pony": Helper(
        id="pony",
        label="pony",
        phrase="Comet the pony, quick and surehearted",
        move_line="Comet leaned into the hard places and kept going with his ears tipped forward like little brave flags.",
        bonus=1,
        fits={"mud_slope", "wind_gap"},
        tags={"pony", "animal"},
    ),
    "donkey": Helper(
        id="donkey",
        label="donkey",
        phrase="Dusty the donkey, patient as Sunday",
        move_line="Dusty took the rough way one calm step at a time and never bothered to argue with the ground.",
        bonus=0,
        fits={"mud_slope", "cactus_wash", "wind_gap"},
        tags={"donkey", "animal"},
    ),
}

GIRL_NAMES = ["Mabel", "Ada", "Tess", "Millie", "Nell", "Ruby", "Lula", "Dora"]
BOY_NAMES = ["Bo", "Eli", "Ned", "Jesse", "Cal", "Wes", "Tom", "Hank"]
TRAITS = ["brave", "steady", "quick", "cheerful", "stouthearted", "gritty"]


def obstacle_in_setting(setting_id: str, obstacle_id: str) -> bool:
    return obstacle_id in SETTINGS[setting_id].afford_obstacles


def tool_fits(obstacle_id: str, tool_id: str) -> bool:
    return obstacle_id in TOOLS[tool_id].guards


def helper_fits(obstacle_id: str, helper_id: str) -> bool:
    return obstacle_id in HELPERS[helper_id].fits


def sensible_combo(setting_id: str, obstacle_id: str, tool_id: str, helper_id: str) -> bool:
    return (
        obstacle_in_setting(setting_id, obstacle_id)
        and tool_fits(obstacle_id, tool_id)
        and helper_fits(obstacle_id, helper_id)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for obstacle_id in sorted(SETTINGS[setting_id].afford_obstacles):
            for tool_id in TOOLS:
                for helper_id in HELPERS:
                    if sensible_combo(setting_id, obstacle_id, tool_id, helper_id):
                        combos.append((setting_id, obstacle_id, tool_id, helper_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    tool: str
    helper: str
    hero: str
    gender: str
    mentor: str
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


def ability_score(params: StoryParams) -> int:
    return int(BRAVERY_INIT) + TOOLS[params.tool].power + HELPERS[params.helper].bonus


def challenge_score(params: StoryParams) -> int:
    return OBSTACLES[params.obstacle].severity + params.delay


def outcome_of(params: StoryParams) -> str:
    return "solo" if ability_score(params) >= challenge_score(params) else "team"


def predict_attempt(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    bell = sim.get("bell")
    hero.meters["push"] += 1
    if ability_score(params) < challenge_score(params):
        hero.meters["stuck"] += 1
        hero.memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "reaches_bell": bell.meters["reachable"] >= THRESHOLD,
        "needs_help": hero.meters["stuck"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, mentor: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.town_name}, folks said the country around {setting.place} was so big "
        f"that a shout needed two lunches and a nap to cross it."
    )
    world.say(setting.horizon)
    world.say(
        f"Among those long miles lived {hero.id}, a {hero.traits[0]} little {hero.type}, "
        f"and {hero.pronoun('possessive')} {mentor.label_word}, who believed a child could do a hard thing kindly and well."
    )


def bell_problem(world: World, hero: Entity, mentor: Entity, setting: Setting) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"Each evening the ranch hands listened for the bell on {setting.bell_place}. "
        f"When it rang, wagons turned home, chickens fluffed onto their roosts, and even the cattle stopped acting as if the prairie belonged only to them."
    )
    world.say(
        f"That afternoon a storm shouldered up on the horizon, dark and puffed as a stack of traveling mountains. "
        f'"Somebody must ring the bell before the rain gallops in," said {mentor.label_word.capitalize()}.'
    )


def volunteer(world: World, hero: Entity, mentor: Entity) -> None:
    hero.memes["bravery"] += BRAVERY_INIT
    world.say(
        f'"I will," said {hero.id}, standing so straight {hero.pronoun()} looked like a fence post that had learned manners. '
        f'{mentor.label_word.capitalize()} smiled and said, "Bravery is finest when it walks hand in hand with excellence."'
    )


def equip(world: World, hero: Entity, mentor: Entity, obstacle: Obstacle, tool: Tool, helper: Helper) -> None:
    world.facts["task"] = "ring the lookout bell before the storm"
    world.say(
        f"But the way to the bell crossed {obstacle.phrase}. {obstacle.hurdle.capitalize()}, and {obstacle.scene}"
    )
    world.say(
        f'So {mentor.label_word} gave {hero.id} {tool.phrase} and pointed to {helper.phrase}. '
        f'"Take what fits the trouble," {mentor.pronoun()} said. "That is part of excellence too."'
    )


def set_off(world: World, hero: Entity, helper_ent: Entity) -> None:
    hero.memes["resolve"] += 1
    helper_ent.memes["loyalty"] += 1
    world.say(
        f"{hero.id} swung up beside {helper_ent.label}, and off they went. "
        f"{helper_ent.attrs['move_line']}"
    )


def climb(world: World, hero: Entity, obstacle: Obstacle, tool: Tool, helper_ent: Entity, params: StoryParams) -> None:
    pred = predict_attempt(world, params)
    world.facts["predicted_reach"] = pred["reaches_bell"]
    world.facts["predicted_help"] = pred["needs_help"]
    world.say(
        f"At the hard part, {hero.id} remembered the gift in {hero.pronoun('possessive')} hands. "
        f"{hero.pronoun().capitalize()} {tool.use_line}."
    )
    hero.meters["push"] += 1
    if outcome_of(params) == "team":
        hero.meters["stuck"] += 1
        hero.memes["fear"] += 1
        hero.meters["scraped"] += 1
        world.say(
            f"For a breath or two, even that was not enough. The trail bucked and fussed, and {hero.id} felt small in all that bigness."
        )
    propagate(world, narrate=False)


def whistle_for_help(world: World, hero: Entity, mentor: Entity, helper_ent: Entity) -> None:
    hero.memes["wisdom"] += 1
    world.say(
        f"Then {hero.id} did another brave thing. {hero.pronoun().capitalize()} pulled out the ranch whistle and blew one sharp note."
    )
    world.say(
        f"The sound skipped over the land, and soon {mentor.label_word}, two ranch hands, and a wagon team came rolling up below. "
        f'"Hold steady!" called {mentor.label_word}.'
    )
    helper_ent.memes["relief"] += 1
    hero.meters["stuck"] = 0.0
    hero.meters["push"] += 1
    world.get("path").meters["help_chain"] += 1
    propagate(world, narrate=False)


def ring_bell(world: World, hero: Entity, bell: Entity) -> None:
    hero.meters["ring_attempt"] += 1
    propagate(world, narrate=False)
    if bell.meters["rung"] >= THRESHOLD:
        world.say(
            f"At the top, {hero.id} seized the rope and gave it a pull. The bell boomed so loud it might have knocked dust off the moon."
        )


def homecoming(world: World, hero: Entity, mentor: Entity, setting: Setting, outcome: str) -> None:
    town = world.get("town")
    if town.meters["home"] >= THRESHOLD:
        if outcome == "solo":
            world.say(
                f"Down below, wagons swung toward {setting.town_name}, hats waved, and the whole place seemed to breathe in at once and breathe out safe."
            )
            world.say(
                f"When {hero.id} came back down, {mentor.label_word} hugged {hero.pronoun('object')} and said, "
                f'"That was bravery, and that was excellence too: you matched yourself to the job and carried it through."'
            )
        else:
            world.say(
                f"Down below, the ranch stirred like one great creature turning home together. Wagons rolled in, lanterns blinked alive, and everybody reached {setting.town_name} before the sky opened."
            )
            world.say(
                f"When {hero.id} came down at last, {mentor.label_word} squeezed {hero.pronoun('possessive')} shoulder and said, "
                f'"You started bravely and called wisely. Excellence is not showing off; it is doing the work the right way."'
            )
    world.say(
        f"That night the bell shone over the darkening land, and {hero.id} felt taller than the lookout itself."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    tool: Tool,
    helper: Helper,
    hero_name: str = "Mabel",
    gender: str = "girl",
    mentor_type: str = "mother",
    trait: str = "brave",
    delay: int = 0,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"display": hero_name},
        )
    )
    mentor = world.add(
        Entity(
            id="mentor",
            kind="character",
            type=mentor_type,
            label="the grown-up",
            role="mentor",
            attrs={"display": mentor_type},
        )
    )
    bell = world.add(
        Entity(
            id="bell",
            type="bell",
            label="the lookout bell",
            phrase="the lookout bell",
            role="goal",
        )
    )
    town = world.add(
        Entity(
            id="town",
            type="town",
            label=setting.town_name,
            phrase=setting.town_name,
            role="town",
        )
    )
    path = world.add(
        Entity(
            id="path",
            type="path",
            label=obstacle.label,
            phrase=obstacle.phrase,
            role="path",
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            type="animal",
            label=helper.label,
            phrase=helper.phrase,
            role="helper",
            attrs={"move_line": helper.move_line},
            tags=set(helper.tags),
        )
    )

    world.facts["setting"] = setting
    world.facts["obstacle"] = obstacle
    world.facts["tool"] = tool
    world.facts["helper_cfg"] = helper
    world.facts["delay"] = delay

    introduce(world, hero, mentor, setting)
    bell_problem(world, hero, mentor, setting)

    world.para()
    volunteer(world, hero, mentor)
    equip(world, hero, mentor, obstacle, tool, helper)
    set_off(world, hero, helper_ent)

    world.para()
    params = StoryParams(
        setting=setting.id,
        obstacle=obstacle.id,
        tool=tool.id,
        helper=helper.id,
        hero=hero_name,
        gender=gender,
        mentor=mentor_type,
        trait=trait,
        delay=delay,
    )
    climb(world, hero, obstacle, tool, helper_ent, params)

    if outcome_of(params) == "team":
        whistle_for_help(world, hero, mentor, helper_ent)

    ring_bell(world, hero, bell)

    world.para()
    homecoming(world, hero, mentor, setting, outcome_of(params))

    world.facts.update(
        hero=hero,
        mentor=mentor,
        bell=bell,
        town=town,
        path=path,
        helper=helper_ent,
        hero_name=hero_name,
        outcome=outcome_of(params),
        reached=bell.meters["reachable"] >= THRESHOLD,
        rang=bell.meters["rung"] >= THRESHOLD,
        town_safe=town.meters["home"] >= THRESHOLD,
        scraped=hero.meters["scraped"] >= THRESHOLD,
        called_help=path.meters["help_chain"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "prairie": [
        (
            "What is a prairie?",
            "A prairie is a wide stretch of open grassland with very few trees. Because it is so open, you can often see weather and people from far away.",
        )
    ],
    "mesa": [
        (
            "What is a mesa?",
            "A mesa is a high hill or landform with a broad, flat top and steep sides. It can look a little like a giant table made of rock.",
        )
    ],
    "canyon": [
        (
            "What is a canyon?",
            "A canyon is a deep gap in the land with steep rocky walls. Water and time can carve it little by little.",
        )
    ],
    "storm": [
        (
            "Why do people hurry before a storm?",
            "Storms can bring hard rain, strong wind, and dark skies very quickly. Getting home early helps people and animals stay safe.",
        )
    ],
    "bell": [
        (
            "Why would a bell help people far away?",
            "A big bell makes a loud sound that can travel across a long distance. People can hear it and know it is time to come home or gather together.",
        )
    ],
    "boots": [
        (
            "What do cleat boots do?",
            "Cleat boots have grippy bottoms that help feet hold onto slippery ground. They make it easier not to slide.",
        )
    ],
    "cloak": [
        (
            "What can a heavy cloak do in strong wind?",
            "A heavy cloak can flap less and stay close to your body. That helps the wind shove you around less.",
        )
    ],
    "chaps": [
        (
            "What are chaps for?",
            "Chaps are tough outer leg covers, often made of leather. They help protect legs from scratches, brush, or thorns.",
        )
    ],
    "mule": [
        (
            "Why are mules known for being steady?",
            "Mules are often careful about where they place their feet. That steadiness can help on rough or slippery ground.",
        )
    ],
    "goat": [
        (
            "Why are goats good at climbing?",
            "Goats are nimble and balanced, and they can place their feet very carefully. That helps them move on rocky or narrow places.",
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small horse. Ponies can be strong, quick, and good company for work or travel.",
        )
    ],
    "donkey": [
        (
            "Why do people call donkeys patient?",
            "Donkeys are known for taking careful steps and not rushing. That can make them useful on a hard path.",
        )
    ],
    "excellence": [
        (
            "What does excellence mean?",
            "Excellence means doing something very well, with care and effort. It is not just being bold; it is trying to do the right job the right way.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "prairie",
    "mesa",
    "canyon",
    "storm",
    "bell",
    "boots",
    "cloak",
    "chaps",
    "mule",
    "goat",
    "pony",
    "donkey",
    "excellence",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    if outcome == "solo":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the word "excellence" and features bravery on {setting.place}.',
            f"Tell a frontier-style story where a brave child uses {tool.label} and {helper.label} to cross {obstacle.phrase} and ring a bell before a storm.",
            f"Write a gentle tall tale where {hero.attrs['display']} proves that bravery and excellence can live together in one big heroic deed.",
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "excellence" and shows that bravery can include asking for help.',
        f"Tell a frontier-style story where a child starts across {obstacle.phrase}, uses {tool.label}, and then wisely calls for help to ring the bell before a storm.",
        f"Write a warm tall tale in which teamwork turns a brave attempt into a safe and excellent ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    helper_ent = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['display']}, a brave little {hero.type}, and {hero.pronoun('possessive')} {mentor.label_word} on {setting.place}. They were trying to ring the lookout bell before a storm.",
        ),
        (
            "Why did the bell need to be rung?",
            f"The bell told wagons, ranch hands, and animals it was time to come home before the storm arrived. Ringing it mattered because the sky was already darkening and everybody needed warning.",
        ),
        (
            f"What trouble stood in {hero.attrs['display']}'s way?",
            f"The path crossed {obstacle.phrase}. That was dangerous because {obstacle.hurdle} and the hard place could slow or stop the climb.",
        ),
        (
            f"How did the grown-up help {hero.attrs['display']} get ready?",
            f"{mentor.label_word.capitalize()} gave {hero.attrs['display']} {tool.phrase} and sent {helper_ent.label} along too. That showed excellence, because they matched the gear and helper to the trouble instead of hoping for luck.",
        ),
    ]
    if f["outcome"] == "solo":
        qa.append(
            (
                f"How did {hero.attrs['display']} reach the bell?",
                f"{hero.attrs['display']} used the {tool.label} and trusted {helper_ent.label} on the hard path. Because the gear fit the problem, the climb worked and the bell could be reached.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The bell rang across {setting.town_name}, and everyone turned safely home before the storm. At the end, the grown-up said the deed showed both bravery and excellence.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.attrs['display']} call for help?",
                f"The path was still too hard even after a brave start, and {hero.attrs['display']} began to get stuck. Blowing the whistle was brave too, because it let the right people come help finish the job safely.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The bell still rang in time, but it happened with help from the ranch instead of by one child alone. That ending proves bravery can work together with wisdom and excellence.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["obstacle"].tags) | set(f["tool"].tags) | set(f["helper_cfg"].tags) | {"bell", "excellence"}
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="prairie_ranch",
        obstacle="mud_slope",
        tool="cleat_boots",
        helper="pony",
        hero="Mabel",
        gender="girl",
        mentor="mother",
        trait="brave",
        delay=0,
    ),
    StoryParams(
        setting="mesa_farm",
        obstacle="wind_gap",
        tool="sail_cloak",
        helper="goat",
        hero="Bo",
        gender="boy",
        mentor="father",
        trait="steady",
        delay=1,
    ),
    StoryParams(
        setting="canyon_station",
        obstacle="cactus_wash",
        tool="cowhide_chaps",
        helper="mule",
        hero="Ruby",
        gender="girl",
        mentor="father",
        trait="gritty",
        delay=0,
    ),
    StoryParams(
        setting="prairie_ranch",
        obstacle="wind_gap",
        tool="storm_goggles",
        helper="donkey",
        hero="Cal",
        gender="boy",
        mentor="mother",
        trait="quick",
        delay=2,
    ),
    StoryParams(
        setting="mesa_farm",
        obstacle="cactus_wash",
        tool="spiral_spurs",
        helper="goat",
        hero="Ada",
        gender="girl",
        mentor="father",
        trait="stouthearted",
        delay=1,
    ),
]


def explain_rejection(setting_id: str, obstacle_id: str, tool_id: str, helper_id: str) -> str:
    pieces: list[str] = []
    if obstacle_id and setting_id and not obstacle_in_setting(setting_id, obstacle_id):
        pieces.append(
            f"{OBSTACLES[obstacle_id].label} does not belong in {SETTINGS[setting_id].place}"
        )
    if obstacle_id and tool_id and not tool_fits(obstacle_id, tool_id):
        pieces.append(
            f"{TOOLS[tool_id].label} does not honestly solve {OBSTACLES[obstacle_id].label}"
        )
    if obstacle_id and helper_id and not helper_fits(obstacle_id, helper_id):
        pieces.append(
            f"{HELPERS[helper_id].label} is not a good match for {OBSTACLES[obstacle_id].label}"
        )
    if not pieces:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(pieces) + ".)"


ASP_RULES = r"""
% --- base reasonableness gate -----------------------------------------------
valid(S,O,T,H) :- setting(S), obstacle(O), tool(T), helper(H),
                  affords(S,O), guards(T,O), fits(H,O).

% --- ability vs challenge outcome -------------------------------------------
ability(B + TP + HB) :- bravery_init(B), chosen_tool(T), tool_power(T,TP),
                        chosen_helper(H), helper_bonus(H,HB).
challenge(OS + D)    :- chosen_obstacle(O), obstacle_severity(O,OS), delay(D).

outcome(solo) :- ability(A), challenge(C), A >= C.
outcome(team) :- ability(A), challenge(C), A < C.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for obstacle_id in sorted(setting.afford_obstacles):
            lines.append(asp.fact("affords", setting_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_severity", obstacle_id, obstacle.severity))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_power", tool_id, tool.power))
        for obstacle_id in sorted(tool.guards):
            lines.append(asp.fact("guards", tool_id, obstacle_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_bonus", helper_id, helper.bonus))
        for obstacle_id in sorted(helper.fits):
            lines.append(asp.fact("fits", helper_id, obstacle_id))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_helper", params.helper),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a brave child rings the lookout bell with excellence."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra strain from the coming storm")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render a curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and not obstacle_in_setting(args.setting, args.obstacle):
        raise StoryError(explain_rejection(args.setting, args.obstacle, args.tool or "", args.helper or ""))
    if args.obstacle and args.tool and not tool_fits(args.obstacle, args.tool):
        raise StoryError(explain_rejection(args.setting or next(iter(SETTINGS)), args.obstacle, args.tool, args.helper or ""))
    if args.obstacle and args.helper and not helper_fits(args.obstacle, args.helper):
        raise StoryError(explain_rejection(args.setting or next(iter(SETTINGS)), args.obstacle, args.tool or "", args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, tool_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        tool=tool_id,
        helper=helper_id,
        hero=hero,
        gender=gender,
        mentor=mentor,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not sensible_combo(params.setting, params.obstacle, params.tool, params.helper):
        raise StoryError(explain_rejection(params.setting, params.obstacle, params.tool, params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        helper=HELPERS[params.helper],
        hero_name=params.hero,
        gender=params.gender,
        mentor_type=params.mentor,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos parity holds ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos parity:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(60):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        buf = StringIO()
        stdout = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = stdout
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, obstacle, tool, helper) combos:\n")
        for setting_id, obstacle_id, tool_id, helper_id in combos:
            print(f"  {setting_id:15} {obstacle_id:12} {tool_id:14} {helper_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.obstacle} at {p.setting} ({p.tool}, {p.helper}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
