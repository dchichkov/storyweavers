#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py
=========================================================================

A standalone story world for a child-facing tall tale about **friendship,
curiosity, and a quest for an enormous onion**.

This world models a small quest domain:

- two friends hear or notice a clue about a giant onion,
- curiosity sends them searching across a larger-than-life landscape,
- they find the onion but cannot pull it free at first,
- a sensible tool matched to the ground lets them solve the problem together,
- they bring the onion home and the ending image proves what changed.

The simulation uses simple typed entities with physical ``meters`` and emotional
``memes``. State drives prose; the children do not merely swap into a template.

Run it
------
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py --asp
    python storyworlds/worlds/gpt-5.4/onion_friendship_curiosity_quest_tall_tale.py --verify
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
class Place:
    id: str
    label: str
    opener: str
    path: str
    onion_site: str
    horizon: str
    affords: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    hook: str
    follow: str
    prove: str
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
class Ground:
    id: str
    label: str
    fail: str
    loosen_text: str
    ground_word: str
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
class Tool:
    id: str
    label: str
    phrase: str
    sense: int
    works_on: set[str] = field(default_factory=set)
    use_text: str = ""
    carry_text: str = ""
    qa_text: str = ""
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
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


def _r_onion_tears(world: World) -> list[str]:
    out: list[str] = []
    onion = world.get("onion")
    if onion.meters["sniffed"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("tears", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["tears"] += 1
        kid.memes["wonder"] += 1
        out.append("__tears__")
    return out


def _r_failed_pull(world: World) -> list[str]:
    onion = world.get("onion")
    if onion.meters["pulled"] < THRESHOLD or onion.meters["loosened"] >= THRESHOLD:
        return []
    sig = ("failed_pull", "onion")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    onion.meters["stuck"] += 1
    for kid in world.kids():
        kid.memes["strain"] += 1
    return ["__stuck__"]


def _r_free_onion(world: World) -> list[str]:
    onion = world.get("onion")
    if onion.meters["loosened"] < THRESHOLD or onion.meters["team_pull"] < THRESHOLD:
        return []
    sig = ("free", "onion")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    onion.meters["stuck"] = 0.0
    onion.meters["free"] += 1
    onion.meters["travel"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["friendship"] += 1
    return ["__free__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="onion_tears", tag="physical", apply=_r_onion_tears),
    Rule(name="failed_pull", tag="physical", apply=_r_failed_pull),
    Rule(name="free_onion", tag="physical", apply=_r_free_onion),
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


def clue_fits(place: Place, clue: Clue) -> bool:
    return clue.id in place.affords


def tool_works(tool: Tool, ground: Ground) -> bool:
    return ground.id in tool.works_on


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for clue_id, clue in CLUES.items():
            if not clue_fits(place, clue):
                continue
            for ground_id, ground in GROUNDS.items():
                for tool_id, tool in TOOLS.items():
                    if tool.sense >= SENSE_MIN and tool_works(tool, ground):
                        combos.append((place_id, clue_id, ground_id, tool_id))
    return combos


def explain_clue(place: Place, clue: Clue) -> str:
    return (
        f"(No story: {clue.id.replace('_', ' ')} is not a good clue for {place.label}. "
        f"That place does not support that kind of sign in this world.)"
    )


def explain_tool(tool: Tool, ground: Ground) -> str:
    options = ", ".join(sorted(t.id for t in sensible_tools() if tool_works(t, ground)))
    if tool.sense < SENSE_MIN:
        return (
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}). Try a sturdier quest tool.)"
        )
    return (
        f"(No story: {tool.label} does not make sense for {ground.label}. "
        f"Try one of: {options}.)"
    )


def predict_success(world: World, tool: Tool) -> dict:
    sim = world.copy()
    onion = sim.get("onion")
    onion.meters["pulled"] += 1
    propagate(sim, narrate=False)
    onion.meters["loosened"] += 1
    onion.attrs["used_tool"] = tool.id
    sim.get("hero").attrs["helping"] = True
    sim.get("friend").attrs["helping"] = True
    onion.meters["team_pull"] += 1
    propagate(sim, narrate=False)
    return {
        "free": sim.get("onion").meters["free"] >= THRESHOLD,
        "tears": sum(k.meters["tears"] for k in sim.kids()),
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{place.opener} {hero.id} and {friend.id} were the kind of friends who "
        f"could not pass a mystery without following it to the end."
    )
    world.say(
        f"In their town, people said curiosity was a spark, but in those two it was "
        f"more like a brass band marching straight into the morning."
    )


def hear_clue(world: World, hero: Entity, friend: Entity, place: Place, clue: Clue) -> None:
    world.say(clue.hook.format(hero=hero.id, friend=friend.id, place=place.label))
    world.say(
        f'That was enough for both of them. "Let us go see," {friend.id} said, '
        f'and {hero.id} grinned as if a quest had just knocked on the door.'
    )


def set_out(world: World, hero: Entity, friend: Entity, place: Place, clue: Clue) -> None:
    hero.meters["steps"] += 1
    friend.meters["steps"] += 1
    world.say(
        f"They set out at once, following {clue.follow} along {place.path}. "
        f"{place.horizon}"
    )


def discover(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    onion = world.get("onion")
    onion.meters["sniffed"] += 1
    propagate(world, narrate=False)
    hero_t = "both blinked and laughed" if hero.type != friend.type else "blinked together and laughed"
    world.say(
        f"At last they reached {place.onion_site}, and there stood the onion. "
        f"It was so round it looked as if the moon had buried one cheek in the earth. "
        f"When the sharp onion smell brushed their noses, they {hero_t}, because tears "
        f"sprang up before either one could even say, \"There it is!\""
    )


def first_pull(world: World, hero: Entity, friend: Entity, ground: Ground) -> None:
    onion = world.get("onion")
    onion.meters["pulled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} grabbed the onion leaves, {friend.id} hugged the thick neck, "
        f"and together they heaved so hard their heels wrote little commas in the dirt. "
        f"But {ground.fail}"
    )


def choose_tool(world: World, hero: Entity, friend: Entity, tool: Tool, ground: Ground) -> None:
    pred = predict_success(world, tool)
    world.facts["predicted_free"] = pred["free"]
    world.facts["predicted_tears"] = pred["tears"]
    hero.attrs["tool"] = tool.id
    friend.attrs["tool"] = tool.id
    world.say(
        f'"Then we stop yanking and start thinking," {friend.id} said. '
        f'That was friendship talking plain and useful.'
    )
    world.say(
        f"{hero.id} fetched {tool.phrase}, and together they {tool.use_text.format(ground=ground.ground_word)}. "
        f"{ground.loosen_text}"
    )


def free_onion(world: World, hero: Entity, friend: Entity) -> None:
    onion = world.get("onion")
    onion.meters["loosened"] += 1
    onion.meters["team_pull"] += 1
    hero.attrs["helping"] = True
    friend.attrs["helping"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then the two friends counted to three and pulled again. Up came the onion "
        f"with a long earth-sigh, so suddenly that both children sat down in the grass "
        f"with the great bulb rocking in their laps like a pale gold boulder."
    )


def bring_home(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    world.say(
        f"They {tool.carry_text}, all the way home. People leaned out of windows, "
        f"dogs forgot to bark, and one old rooster crowed twice because he thought "
        f"another sunrise had rolled past."
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"That evening the town kettle simmered with sweet onion soup enough for every bowl. "
        f"But {hero.id} and {friend.id} kept the best treasure for last: a paper packet of seeds "
        f"saved from the giant onion and tied with one bit of string for both of them."
    )
    world.say(
        f"From then on, whenever a new mystery fluttered by, they did not race to be first. "
        f"They went shoulder to shoulder, curious together, because they had learned that a quest "
        f"grown with friendship can feed more than two children."
    )


def tell(
    place: Place,
    clue: Clue,
    ground: Ground,
    tool: Tool,
    *,
    hero_name: str = "Mara",
    hero_gender: str = "girl",
    friend_name: str = "Joss",
    friend_gender: str = "boy",
    parent_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type, role="elder", label="the elder"))
    onion = world.add(Entity(id="onion", kind="thing", type="onion", label="giant onion"))
    onion.meters["stuck"] = 1.0
    onion.meters["sniffed"] = 0.0
    onion.meters["pulled"] = 0.0
    onion.meters["loosened"] = 0.0
    onion.meters["team_pull"] = 0.0
    onion.meters["free"] = 0.0
    hero.attrs["helping"] = False
    friend.attrs["helping"] = False
    hero.attrs["tool"] = ""
    friend.attrs["tool"] = ""

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["elder"] = elder
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["ground"] = ground
    world.facts["tool"] = tool

    introduce(world, hero, friend, place)
    hear_clue(world, hero, friend, place, clue)
    world.para()
    set_out(world, hero, friend, place, clue)
    discover(world, hero, friend, place)
    world.para()
    first_pull(world, hero, friend, ground)
    choose_tool(world, hero, friend, tool, ground)
    free_onion(world, hero, friend)
    world.para()
    bring_home(world, hero, friend, tool)
    ending(world, hero, friend)

    world.facts["tears_happened"] = any(k.meters["tears"] >= THRESHOLD for k in world.kids())
    world.facts["onion_free"] = onion.meters["free"] >= THRESHOLD
    world.facts["friendship_helped"] = hero.attrs["helping"] and friend.attrs["helping"]
    return world


PLACES = {
    "windmill_hill": Place(
        id="windmill_hill",
        label="Windmill Hill",
        opener="On the far side of Windmill Hill, where fence posts leaned like sleepy giants,",
        path="a lane that bent between thistles and sun-warmed stones",
        onion_site="a patch beside the old windmill",
        horizon="The hill puffed out such bragging breezes that a hat could travel half a field by itself.",
        affords={"goose_gossip", "moon_map"},
        tags={"hill"},
    ),
    "creek_meadow": Place(
        id="creek_meadow",
        label="Creek Meadow",
        opener="Beyond Creek Meadow, where the grass grew high enough to hide a calf,",
        path="the silvering edge of the creek",
        onion_site="a bend where the meadow dipped and held the morning cool",
        horizon="Dragonflies stitched blue sparks over the water, and every reed looked ready to whisper a secret.",
        affords={"bee_parade", "moon_map"},
        tags={"meadow", "creek"},
    ),
    "kitchen_garden": Place(
        id="kitchen_garden",
        label="the Old Kitchen Garden",
        opener="Behind the old kitchen garden wall, where pumpkins were said to stretch in their sleep,",
        path="a brick path striped with dill shadows",
        onion_site="the back row near a broken gate",
        horizon="The garden smelled of warm leaves and supper promises, as if every bed were quietly planning a feast.",
        affords={"onion_smell", "bee_parade", "moon_map"},
        tags={"garden"},
    ),
}

CLUES = {
    "onion_smell": Clue(
        id="onion_smell",
        hook='A mighty onion smell came drifting through breakfast, sharp enough to make {hero} laugh and {friend} blink. "No ordinary onion is making that fuss," said {hero}.',
        follow="the smell the way hounds might follow a pie",
        prove="the onion smell",
        tags={"onion", "smell"},
    ),
    "bee_parade": Clue(
        id="bee_parade",
        hook='A line of bees flew over the lane as straight as marching trumpets, and {friend} said, "They look like they know where something sweet or strange is growing."',
        follow="the bee parade",
        prove="the marching bees",
        tags={"bee"},
    ),
    "moon_map": Clue(
        id="moon_map",
        hook='At dawn, {hero} found a dew-damp map on the fence rail, with a round sketch marked bigger than a cartwheel. "That looks like an onion if ever ink told the truth," said {friend}.',
        follow="the little map and the marks it made",
        prove="the map",
        tags={"map"},
    ),
}

GROUNDS = {
    "hard_clay": Ground(
        id="hard_clay",
        label="hard clay",
        fail="the onion did not budge a whisker, because its roots were stitched deep into hard clay",
        loosen_text="The clay cracked in a neat circle, the way pie crust breaks when the steam finally wins.",
        ground_word="the hard clay",
        tags={"clay"},
    ),
    "silty_bed": Ground(
        id="silty_bed",
        label="a silty creek bed",
        fail="the onion only slurped and settled deeper, because its roots were tucked inside a silty creek bed",
        loosen_text="The silty earth softened and slid apart, no longer gripping the roots like a jealous fist.",
        ground_word="the silty earth",
        tags={"silt", "creek"},
    ),
    "weedy_patch": Ground(
        id="weedy_patch",
        label="a weedy patch",
        fail="the leaves shook, but a nest of tough weeds held the bulb in place as if the patch had tied knots around it",
        loosen_text="The weeds came away in long green ropes, and the ground let go with much better manners.",
        ground_word="the weedy patch",
        tags={"weeds"},
    ),
}

TOOLS = {
    "spade": Tool(
        id="spade",
        label="spade",
        phrase="a stout little spade",
        sense=3,
        works_on={"hard_clay", "weedy_patch"},
        use_text="worked the spade around {ground}",
        carry_text="rolled the onion on the spade and nudged it home between them",
        qa_text="They used a stout spade to loosen the ground around the onion",
        tags={"spade"},
    ),
    "watering_can": Tool(
        id="watering_can",
        label="watering can",
        phrase="a broad-bellied watering can",
        sense=3,
        works_on={"hard_clay", "silty_bed"},
        use_text="poured water slowly around {ground}",
        carry_text="settled the onion in the watering can and took turns carrying the handle",
        qa_text="They poured water around the roots with a watering can to soften the soil",
        tags={"watering_can", "water"},
    ),
    "garden_fork": Tool(
        id="garden_fork",
        label="garden fork",
        phrase="an old garden fork",
        sense=3,
        works_on={"silty_bed", "weedy_patch"},
        use_text="slid the fork under {ground} and lifted carefully",
        carry_text="balanced the onion on the fork and walked home in tiny solemn steps",
        qa_text="They slid a garden fork under the roots and lifted carefully",
        tags={"fork"},
    ),
    "teacup": Tool(
        id="teacup",
        label="teacup",
        phrase="a cracked teacup",
        sense=1,
        works_on=set(),
        use_text="scraped at {ground} with the edge of the cup",
        carry_text="tried to wobble the onion along in the teacup",
        qa_text="They poked at the ground with a teacup",
        tags={"teacup"},
    ),
}

GIRL_NAMES = ["Mara", "Nell", "Tessa", "Ivy", "Ruth", "Clara", "June", "Bess"]
BOY_NAMES = ["Joss", "Eli", "Ned", "Owen", "Toby", "Finn", "Hugh", "Cal"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    clue: str
    ground: str
    tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    elder: str = "mother"
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
    "onion": [
        (
            "What is an onion?",
            "An onion is a round vegetable that grows partly under the ground in layers. When you cut or smell it closely, it can make your eyes water.",
        )
    ],
    "smell": [
        (
            "Why can an onion make your eyes water?",
            "Onions let out strong tiny chemicals into the air when they are cut or disturbed. Those chemicals bother your eyes, so your body makes tears to wash them away.",
        )
    ],
    "bee": [
        (
            "Why might bees fly in a line toward a garden?",
            "Bees look for flowers and good plant places. If many bees head the same way, it can mean something useful is growing there.",
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map helps you find where things are and which way to go. It turns a big place into clues you can follow.",
        )
    ],
    "spade": [
        (
            "What is a spade for?",
            "A spade is a digging tool with a flat blade. People use it to cut into soil and lift dirt when something is stuck in the ground.",
        )
    ],
    "watering_can": [
        (
            "Why would water help loosen hard soil?",
            "Water can soften dry ground so it does not grip roots so tightly. That makes it easier to dig or pull a plant out gently.",
        )
    ],
    "fork": [
        (
            "What does a garden fork do?",
            "A garden fork has strong tines that can lift and loosen earth. It helps pry roots free without chopping them apart.",
        )
    ],
    "friendship": [
        (
            "How can friendship help on a quest?",
            "A good friend can think with you when strength alone is not enough. Working together often solves a hard problem faster and more safely.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to ask, look, and learn more. It can start an adventure when you follow a strange clue.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "onion",
    "smell",
    "bee",
    "map",
    "spade",
    "watering_can",
    "fork",
    "friendship",
    "curiosity",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    clue = f["clue"]
    place = f["place"]
    return [
        'Write a tall-tale story for a 3-to-5-year-old that includes the word "onion" and centers on friendship, curiosity, and a quest.',
        f"Tell a warm exaggerated story where {hero.id} and {friend.id} follow {clue.prove} to {place.label} and discover an onion bigger than anyone expected.",
        "Write a simple quest story in a tall-tale style where two friends solve a giant garden problem by thinking together instead of giving up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    clue = f["clue"]
    ground = f["ground"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.id} and {friend.id}. They are curious children who decide to go on a quest together.",
        ),
        (
            "What started their quest?",
            f"They noticed {clue.prove}, and it felt too strange to ignore. Their curiosity made them follow the clue to {place.label}.",
        ),
        (
            "What did they find?",
            f"They found a giant onion growing in {place.onion_site}. The onion was so big that the story describes it like something from a tall tale.",
        ),
        (
            "Why did they cry a little when they found the onion?",
            f"The onion smell reached their noses and made their eyes water. That happened because onions can be sharp and stingy to the eyes.",
        ),
        (
            "Why could they not pull the onion out at first?",
            f"They tugged hard, but the onion was stuck in {ground.label}. The roots held fast, so strength alone was not enough.",
        ),
        (
            "How did friendship help them solve the problem?",
            f"{friend.id} helped turn the moment from wild pulling into careful thinking, and {hero.id} helped carry out the plan. They succeeded because both children worked together instead of quitting.",
        ),
        (
            "How did they get the onion free?",
            f"{tool.qa_text}. After the ground loosened, they pulled together and the onion finally came out.",
        ),
        (
            "How did the story end?",
            f"They brought the onion home and the town shared onion soup. At the end, the two friends save seeds together, showing that the quest changed into a shared promise for later.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"onion", "friendship", "curiosity"}
    tags |= set(world.facts["clue"].tags)
    tags |= set(world.facts["tool"].tags)
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen_garden",
        clue="onion_smell",
        ground="hard_clay",
        tool="watering_can",
        hero="Mara",
        hero_gender="girl",
        friend="Joss",
        friend_gender="boy",
        elder="mother",
    ),
    StoryParams(
        place="creek_meadow",
        clue="bee_parade",
        ground="silty_bed",
        tool="garden_fork",
        hero="Nell",
        hero_gender="girl",
        friend="Eli",
        friend_gender="boy",
        elder="father",
    ),
    StoryParams(
        place="windmill_hill",
        clue="moon_map",
        ground="weedy_patch",
        tool="spade",
        hero="Toby",
        hero_gender="boy",
        friend="June",
        friend_gender="girl",
        elder="mother",
    ),
    StoryParams(
        place="kitchen_garden",
        clue="moon_map",
        ground="weedy_patch",
        tool="garden_fork",
        hero="Clara",
        hero_gender="girl",
        friend="Finn",
        friend_gender="boy",
        elder="father",
    ),
    StoryParams(
        place="creek_meadow",
        clue="moon_map",
        ground="hard_clay",
        tool="watering_can",
        hero="Hugh",
        hero_gender="boy",
        friend="Bess",
        friend_gender="girl",
        elder="mother",
    ),
]


ASP_RULES = r"""
fits(Place, Clue) :- place(Place), clue(Clue), affords(Place, Clue).
usable(Tool, Ground) :- tool(Tool), ground(Ground), works_on(Tool, Ground).
sensible(Tool) :- tool(Tool), sense(Tool, S), sense_min(M), S >= M.
valid(Place, Clue, Ground, Tool) :- fits(Place, Clue), usable(Tool, Ground), sensible(Tool).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for clue_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, clue_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for ground_id in GROUNDS:
        lines.append(asp.fact("ground", ground_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for ground_id in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, ground_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(tool for (tool,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    ctools = set(asp_sensible())
    ptools = {tool.id for tool in sensible_tools()}
    if ctools == ptools:
        print(f"OK: sensible tools match ({sorted(ctools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(ctools)} python={sorted(ptools)}")

    try:
        smoke_params = CURATED[0]
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale quest storyworld: two friends follow a clue to a giant onion."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--ground", choices=GROUNDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--elder", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue:
        place = PLACES[args.place]
        clue = CLUES[args.clue]
        if not clue_fits(place, clue):
            raise StoryError(explain_clue(place, clue))
    if args.tool and args.ground:
        tool = TOOLS[args.tool]
        ground = GROUNDS[args.ground]
        if not tool_works(tool, ground) or tool.sense < SENSE_MIN:
            raise StoryError(explain_tool(tool, ground))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        tool = TOOLS[args.tool]
        raise StoryError(
            f"(Refusing tool '{tool.id}': it scores too low on common sense "
            f"(sense={tool.sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.ground is None or combo[2] == args.ground)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clue_id, ground_id, tool_id = rng.choice(sorted(combos))
    hero, hero_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=hero)
    elder = args.elder or rng.choice(PARENT_TYPES)
    return StoryParams(
        place=place_id,
        clue=clue_id,
        ground=ground_id,
        tool=tool_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        clue = CLUES[params.clue]
        ground = GROUNDS[params.ground]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if not clue_fits(place, clue):
        raise StoryError(explain_clue(place, clue))
    if not tool_works(tool, ground) or tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(tool, ground))

    world = tell(
        place=place,
        clue=clue,
        ground=ground,
        tool=tool,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.elder,
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
        print(asp_program(show="#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        tools = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible tools: {', '.join(tools)}\n")
        print(f"{len(combos)} compatible (place, clue, ground, tool) combos:\n")
        for place, clue, ground, tool in combos:
            print(f"  {place:15} {clue:12} {ground:11} {tool}")
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
            header = f"### {p.hero} & {p.friend}: {p.clue} at {p.place} ({p.ground}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
