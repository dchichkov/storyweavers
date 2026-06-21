#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/snout_sound_effects_adventure.py
===========================================================

A standalone storyworld about a child and a snout-led adventure: a little
explorer follows brave, concrete clues -- snuffle sounds, rustles, splashes,
and knocks -- to help a small animal reach something it cannot get alone.
The world model enforces a simple common-sense constraint:

    obstacle -> only some tools can solve it safely and honestly

A branch can be:
- a happy recovery with the right tool
- a gentle near-miss where the helper stops and rethinks before trouble
- a sad-but-safe "too late" ending when the wrong delay lets the river take the prize

The prose is state-driven: curiosity creates pursuit, risk creates caution,
gear changes what is possible, and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/snout_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/snout_sound_effects_adventure.py --animal piglet --obstacle crack
    python storyworlds/worlds/gpt-5.4/snout_sound_effects_adventure.py --tool net
    python storyworlds/worlds/gpt-5.4/snout_sound_effects_adventure.py --verify
    python storyworlds/worlds/gpt-5.4/snout_sound_effects_adventure.py --asp
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    reachable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Setting:
    id: str
    place: str
    path: str
    landmark: str
    home: str
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
class Animal:
    id: str
    label: str
    phrase: str
    snout_phrase: str
    call: str
    step_sound: str
    snout_sound: str
    size: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    owner_text: str
    use_text: str
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
class Obstacle:
    id: str
    label: str
    place: str
    risk_text: str
    sound: str
    severity: int
    recoverable: bool = True
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
    works_for: set[str]
    sense: int
    power: int
    action_text: str
    fail_text: str
    qa_text: str
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


def _r_animal_worried(world: World) -> list[str]:
    animal = world.get("animal")
    treasure = world.get("treasure")
    if treasure.meters["stuck"] < THRESHOLD:
        return []
    sig = ("animal_worried", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["worry"] += 1
    return ["__worry__"]


def _r_hero_brave(world: World) -> list[str]:
    hero = world.get("hero")
    animal = world.get("animal")
    if hero.memes["resolve"] < THRESHOLD or animal.memes["worry"] < THRESHOLD:
        return []
    sig = ("hero_brave", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    return []


def _r_success_relief(world: World) -> list[str]:
    treasure = world.get("treasure")
    animal = world.get("animal")
    hero = world.get("hero")
    if treasure.meters["saved"] < THRESHOLD:
        return []
    sig = ("relief", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["joy"] += 1
    animal.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="animal_worried", tag="emotional", apply=_r_animal_worried),
    Rule(name="hero_brave", tag="emotional", apply=_r_hero_brave),
    Rule(name="success_relief", tag="emotional", apply=_r_success_relief),
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


def obstacle_needs_tool(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in tool.works_for


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def challenge_severity(obstacle: Obstacle, delay: int) -> int:
    return obstacle.severity + delay


def is_solved(tool: Tool, obstacle: Obstacle, delay: int) -> bool:
    return obstacle_needs_tool(obstacle, tool) and tool.power >= challenge_severity(obstacle, delay)


def explain_obstacle_rejection(obstacle: Obstacle, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not honestly solve {obstacle.label}. "
        f"The fix must match the obstacle instead of just naming random gear.)"
    )


def explain_tool_rejection(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it is too weak or clumsy for this world "
        f"(sense={tool.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def predict_trouble(world: World, obstacle_id: str, delay: int) -> dict:
    sim = world.copy()
    treasure = sim.get("treasure")
    treasure.meters["stuck"] += 1
    if obstacle_id == "river" and delay >= 2:
        treasure.meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "animal_worried": sim.get("animal").memes["worry"] >= THRESHOLD,
        "lost": treasure.meters["lost"] >= THRESHOLD,
    }


def opening(world: World, hero: Entity, animal: Animal, setting: Setting, treasure: Treasure) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"On a bright morning, {hero.id} set out along {setting.path} near {setting.place}, "
        f"pretending the day was a grand adventure map."
    )
    world.say(
        f"In {hero.pronoun('possessive')} satchel was {treasure.phrase}. {treasure.owner_text}."
    )
    world.say(
        f"Then came a small sound from behind {setting.landmark}: "
        f'"{animal.call}... {animal.step_sound}... {animal.snout_sound}."'
    )


def meet_animal(world: World, hero: Entity, animal_cfg: Animal, setting: Setting) -> None:
    animal = world.get("animal")
    animal.memes["trust"] += 1
    world.say(
        f"{hero.id} peeked around {setting.landmark} and saw {animal_cfg.phrase} "
        f"with {animal_cfg.snout_phrase}. Its little feet went {animal_cfg.step_sound} in the leaves."
    )
    world.say(
        f"The tiny creature lifted its snout, sniffed the air, and looked ready to ask for help."
    )


def problem(world: World, hero: Entity, animal_cfg: Animal, treasure_cfg: Treasure, obstacle_cfg: Obstacle, parent: Entity, delay: int) -> None:
    treasure = world.get("treasure")
    treasure.meters["stuck"] += 1
    propagate(world, narrate=False)
    pred = predict_trouble(world, obstacle_cfg.id, delay)
    world.facts["predicted_lost"] = pred["lost"]
    world.say(
        f"{animal_cfg.phrase.capitalize()} had been nudging {treasure_cfg.phrase} along the path, "
        f"but now it was trapped at {obstacle_cfg.place}. {obstacle_cfg.sound}"
    )
    world.say(
        f'{hero.id} knelt down. "{obstacle_cfg.risk_text}" {hero.pronoun()} whispered, '
        f"remembering what {hero.pronoun('possessive')} {parent.label_word} always said about stopping to think first."
    )


def pause_and_rethink(world: World, hero: Entity, animal_cfg: Animal, obstacle_cfg: Obstacle) -> None:
    hero.memes["caution"] += 1
    world.say(
        f"{hero.id} almost lunged forward with bare hands, but the {obstacle_cfg.label} made "
        f"{hero.pronoun('object')} stop. {hero.pronoun().capitalize()} listened again: "
        f'"{animal_cfg.snout_sound}... {obstacle_cfg.sound}"'
    )
    world.say(
        f"That careful pause turned the adventure from reckless to brave."
    )


def fetch_tool(world: World, hero: Entity, tool_cfg: Tool, setting: Setting) -> None:
    hero.memes["resolve"] += 1
    tool = world.get("tool")
    tool.meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} hurried to {setting.home}, found {tool_cfg.phrase}, and ran back with it held tight."
    )


def rescue(world: World, hero: Entity, animal_cfg: Animal, treasure_cfg: Treasure, obstacle_cfg: Obstacle, tool_cfg: Tool) -> None:
    treasure = world.get("treasure")
    treasure.meters["stuck"] = 0.0
    treasure.meters["saved"] += 1
    treasure.reachable = True
    propagate(world, narrate=False)
    world.say(
        f"{tool_cfg.action_text} \"{animal_cfg.call}!\" {hero.id} said. "
        f'"{obstacle_cfg.sound}... {tool_cfg.label} swish... pluck!"'
    )
    world.say(
        f"Soon {treasure_cfg.phrase} was safe again, and {animal_cfg.phrase} pressed its snout against "
        f"{hero.id}'s knee in a thankful nuzzle."
    )


def fail_loss(world: World, hero: Entity, animal_cfg: Animal, treasure_cfg: Treasure, obstacle_cfg: Obstacle, tool_cfg: Tool) -> None:
    treasure = world.get("treasure")
    treasure.meters["lost"] += 1
    treasure.meters["stuck"] = 0.0
    world.say(
        f"{tool_cfg.fail_text} Before either of them could try again, {treasure_cfg.phrase} "
        f"slipped away with a sad {obstacle_cfg.sound.lower()}."
    )
    world.say(
        f"{animal_cfg.phrase.capitalize()} gave one small \"{animal_cfg.call}\" and lowered its snout."
    )


def lesson(world: World, hero: Entity, animal_cfg: Animal, treasure_cfg: Treasure, parent: Entity, solved: bool) -> None:
    hero.memes["lesson"] += 1
    if solved:
        world.say(
            f"When {hero.id} got home, {hero.pronoun('possessive')} {parent.label_word} smiled to hear the tale. "
            f'"You were kind, and you used the right tool," {parent.pronoun()} said. '
            f'"That is how real adventurers help."'
        )
        world.say(
            f"The next afternoon, {hero.id} and {animal_cfg.phrase} explored the path again, "
            f"with the little animal's snout going {animal_cfg.snout_sound} at every interesting stump."
        )
    else:
        hero.memes["sadness"] += 1
        world.say(
            f"When {hero.id} got home, {hero.pronoun('possessive')} {parent.label_word} gave {hero.pronoun('object')} a warm hug. "
            f'"Sometimes being brave also means learning what must be done faster next time," {parent.pronoun()} said.'
        )
        world.say(
            f"The next day, {hero.id} returned with safer gear and a slower step, ready to help sooner if another small friend needed it."
        )


def celebrate(world: World, hero: Entity, animal_cfg: Animal, treasure_cfg: Treasure, setting: Setting) -> None:
    world.say(
        f"At sunset they sat beside {setting.landmark}. {animal_cfg.phrase.capitalize()} curled around "
        f"{treasure_cfg.phrase}, and {hero.id} listened to the woods go "
        f'"hush... chirp... rustle."'
    )
    world.say(
        f"It no longer felt like a place of trouble. It felt like the end of a true adventure."
    )


def tell(
    setting: Setting,
    animal_cfg: Animal,
    treasure_cfg: Treasure,
    obstacle_cfg: Obstacle,
    tool_cfg: Tool,
    *,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait, "curious"],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={},
    ))
    animal = world.add(Entity(
        id="animal",
        kind="character",
        type="animal",
        label=animal_cfg.label,
        role="animal",
        attrs={"animal_id": animal_cfg.id},
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure_cfg.label,
        role="treasure",
        portable=True,
        reachable=False,
        attrs={"treasure_id": treasure_cfg.id},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        role="tool",
        portable=True,
        attrs={"tool_id": tool_cfg.id},
    ))
    site = world.add(Entity(
        id="site",
        kind="thing",
        type="place",
        label=setting.place,
        role="setting",
        attrs={"setting_id": setting.id, "obstacle_id": obstacle_cfg.id},
    ))

    for ent in (hero, parent, animal, treasure, tool, site):
        ent.meters["seeded"] += 0.0
        ent.memes["seeded"] += 0.0

    opening(world, hero, animal_cfg, setting, treasure_cfg)
    meet_animal(world, hero, animal_cfg, setting)

    world.para()
    problem(world, hero, animal_cfg, treasure_cfg, obstacle_cfg, parent, delay)
    pause_and_rethink(world, hero, animal_cfg, obstacle_cfg)
    fetch_tool(world, hero, tool_cfg, setting)

    world.para()
    solved = is_solved(tool_cfg, obstacle_cfg, delay)
    if solved:
        rescue(world, hero, animal_cfg, treasure_cfg, obstacle_cfg, tool_cfg)
        lesson(world, hero, animal_cfg, treasure_cfg, parent, True)
        world.para()
        celebrate(world, hero, animal_cfg, treasure_cfg, setting)
        outcome = "saved"
    else:
        fail_loss(world, hero, animal_cfg, treasure_cfg, obstacle_cfg, tool_cfg)
        lesson(world, hero, animal_cfg, treasure_cfg, parent, False)
        outcome = "lost"

    world.facts.update(
        hero=hero,
        parent=parent,
        animal=animal,
        animal_cfg=animal_cfg,
        treasure=treasure,
        treasure_cfg=treasure_cfg,
        obstacle=obstacle_cfg,
        tool=tool_cfg,
        setting=setting,
        outcome=outcome,
        solved=solved,
        delay=delay,
    )
    return world


SETTINGS = {
    "woods": Setting(
        id="woods",
        place="the whispering woods",
        path="a mossy path",
        landmark="a hollow log",
        home="the little shed by the garden gate",
        tags={"woods", "adventure"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the windy meadow",
        path="a narrow dirt trail",
        landmark="an old stone",
        home="the basket porch at the edge of the field",
        tags={"meadow", "adventure"},
    ),
    "marsh": Setting(
        id="marsh",
        place="the bright marsh",
        path="a boardwalk path",
        landmark="a bent willow stump",
        home="the boathouse shelf near the dock",
        tags={"marsh", "adventure"},
    ),
}

ANIMALS = {
    "piglet": Animal(
        id="piglet",
        label="piglet",
        phrase="a striped little piglet",
        snout_phrase="a pink muddy snout",
        call="snorf",
        step_sound="pat-pat",
        snout_sound="snuffle-snuffle",
        size="small",
        tags={"piglet", "snout", "animal"},
    ),
    "mole": Animal(
        id="mole",
        label="mole",
        phrase="a round little mole",
        snout_phrase="a soft velvet snout",
        call="mmpf",
        step_sound="scritch-scritch",
        snout_sound="sniff-sniff",
        size="small",
        tags={"mole", "snout", "animal"},
    ),
    "tapir_calf": Animal(
        id="tapir_calf",
        label="tapir calf",
        phrase="a shy tapir calf",
        snout_phrase="a tiny striped snout",
        call="prru",
        step_sound="thup-thup",
        snout_sound="snuff-snuff",
        size="small",
        tags={"tapir", "snout", "animal"},
    ),
}

TREASURES = {
    "apple": Treasure(
        id="apple",
        label="apple",
        phrase="a shiny red apple",
        owner_text="It was meant for a trail snack after the exploring was done",
        use_text="a snack",
        tags={"apple", "food"},
    ),
    "bell": Treasure(
        id="bell",
        label="bell",
        phrase="a tiny brass bell",
        owner_text="It was the sort of thing that could make any game sound important",
        use_text="a ringing prize",
        tags={"bell", "bell"},
    ),
    "map_tube": Treasure(
        id="map_tube",
        label="map tube",
        phrase="a rolled-up paper map in a little tube",
        owner_text="It held a pretend map with dotted lines and an X at the end",
        use_text="a pretend map",
        tags={"map", "adventure"},
    ),
}

OBSTACLES = {
    "crack": Obstacle(
        id="crack",
        label="a narrow crack between stones",
        place="the edge of a narrow crack between stones",
        risk_text="If I poke in there the wrong way, it might slip deeper",
        sound="tik... tik...",
        severity=1,
        recoverable=True,
        tags={"crack", "stones"},
    ),
    "briar": Obstacle(
        id="briar",
        label="a briar patch",
        place="a knot of thorny briars",
        risk_text="Thorns can scratch small hands and tear things too",
        sound="scrrritch",
        severity=2,
        recoverable=True,
        tags={"briar", "thorn"},
    ),
    "river": Obstacle(
        id="river",
        label="the rushing river edge",
        place="the slippery river edge",
        risk_text="One wrong grab and it could splash away",
        sound="splash-hush",
        severity=3,
        recoverable=True,
        tags={"river", "water"},
    ),
}

TOOLS = {
    "stick": Tool(
        id="stick",
        label="stick",
        phrase="a forked walking stick",
        works_for={"crack"},
        sense=2,
        power=1,
        action_text="With the forked stick, carefully lifted the prize free.",
        fail_text="The stick tapped and nudged, but could not keep the prize from sliding farther.",
        qa_text="used a forked stick to lift it free",
        tags={"stick", "tool"},
    ),
    "blanket": Tool(
        id="blanket",
        label="blanket",
        phrase="a thick old blanket",
        works_for={"briar"},
        sense=3,
        power=2,
        action_text="Spread the blanket over the briars and tugged the prize loose without touching the thorns.",
        fail_text="The blanket snagged and bunched, and the prize stayed caught too long.",
        qa_text="spread a blanket over the briars and tugged it loose",
        tags={"blanket", "tool"},
    ),
    "hook": Tool(
        id="hook",
        label="hook",
        phrase="a long river hook",
        works_for={"river"},
        sense=3,
        power=3,
        action_text="Reached with the long hook and drew the prize back from the water.",
        fail_text="The hook splashed once, but the current pulled the prize away before it could catch.",
        qa_text="used a long hook to draw it back from the water",
        tags={"hook", "tool", "water"},
    ),
    "net": Tool(
        id="net",
        label="net",
        phrase="a butterfly net",
        works_for=set(),
        sense=1,
        power=1,
        action_text="",
        fail_text="The net fluttered uselessly and was no help at all.",
        qa_text="tried a net",
        tags={"net", "tool"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Ava", "Zoe", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Sam", "Max", "Theo", "Eli", "Jack"]
TRAITS = ["careful", "steady", "kind", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for animal_id in ANIMALS:
            for treasure_id in TREASURES:
                for obstacle_id, obstacle in OBSTACLES.items():
                    for tool_id, tool in TOOLS.items():
                        if obstacle_needs_tool(obstacle, tool) and tool.sense >= SENSE_MIN:
                            combos.append((setting_id, animal_id, treasure_id, obstacle_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    animal: str
    treasure: str
    obstacle: str
    tool: str
    hero_name: str
    hero_gender: str
    parent: str
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
    "snout": [
        (
            "What is a snout?",
            "A snout is the long front part of some animals' faces, where their nose and mouth are. Animals use it to sniff, nudge, and find things."
        )
    ],
    "piglet": [
        (
            "What is a piglet?",
            "A piglet is a baby pig. Piglets are small, curious, and often use their snouts to sniff the ground."
        )
    ],
    "mole": [
        (
            "Why do moles sniff so much?",
            "Moles use their noses and snouts to explore because they live close to the ground. Sniffing helps them find food and notice what is around them."
        )
    ],
    "tapir": [
        (
            "What is a tapir calf?",
            "A tapir calf is a baby tapir. It has a small snout that helps it smell things and pick through leaves."
        )
    ],
    "river": [
        (
            "Why is a river edge slippery?",
            "River edges can be wet and muddy, so feet or objects can slide easily. That is why people should slow down and use the right tool near water."
        )
    ],
    "thorn": [
        (
            "Why are briars tricky to touch?",
            "Briars have sharp thorns that can scratch skin and catch on cloth. Covering them first can make helping much safer."
        )
    ],
    "crack": [
        (
            "Why can things get stuck in a crack?",
            "A narrow crack can pinch an object so it will not come back out easily. Poking carelessly can push it farther in."
        )
    ],
    "hook": [
        (
            "What is a hook good for near water?",
            "A long hook can reach something without making you lean too far. It lets you pull an object back from a slippery place."
        )
    ],
    "blanket": [
        (
            "How can a blanket help with thorns?",
            "A thick blanket can cover sharp thorns for a moment. Then something can be pulled across the blanket instead of scraping through the briars."
        )
    ],
    "stick": [
        (
            "How can a stick help lift something?",
            "A stick can reach into a narrow place when fingers do not fit. If it has a fork or bend, it can gently lift an object out."
        )
    ],
}
KNOWLEDGE_ORDER = ["snout", "piglet", "mole", "tapir", "crack", "thorn", "river", "stick", "blanket", "hook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal_cfg = f["animal_cfg"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "snout" '
        f'and uses playful sound effects. A child helps {animal_cfg.phrase} at {obstacle.place}.'
    )
    if outcome == "saved":
        return [
            base,
            f"Tell a gentle adventure where {hero.id} hears {animal_cfg.snout_sound} in the wild, "
            f"stops to think, and uses a {tool.label} to help.",
            'Write a story with sound effects like "snuffle-snuffle" or "splash-hush" where the ending shows that careful bravery solves the problem.',
        ]
    return [
        base,
        f"Tell a cautionary adventure where {hero.id} tries to help {animal_cfg.phrase} but is too late, "
        f"so the child learns that brave helpers must hurry and choose the right gear.",
        'Write a sad-but-safe story with sound effects where a small loss teaches the hero to be better prepared next time.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    animal_cfg = f["animal_cfg"]
    treasure_cfg = f["treasure_cfg"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {animal_cfg.phrase}. They meet on an adventure path when the little animal needs help."
        ),
        (
            f"What clue led {hero.id} to the little animal?",
            f"{hero.id} heard the sound effects first, like {animal_cfg.call} and {animal_cfg.snout_sound}. Those sounds led {hero.pronoun('object')} to the creature behind the landmark."
        ),
        (
            f"What was the problem?",
            f"{animal_cfg.phrase.capitalize()} could not get {treasure_cfg.phrase} back because it was trapped at {obstacle.place}. The obstacle made a direct grab unsafe or unhelpful."
        ),
        (
            f"Why did {hero.id} stop to think before helping?",
            f"{hero.id} remembered that rushing can make trouble worse. The danger depended on the obstacle, so {hero.pronoun()} needed the right tool instead of just quick hands."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How did {hero.id} save the {treasure_cfg.label}?",
                f"{hero.pronoun().capitalize()} used the {tool.label} and {tool.qa_text}. That worked because the tool matched the obstacle and let {hero.pronoun('object')} help safely."
            )
        )
        qa.append(
            (
                "How did the animal feel at the end?",
                f"It felt happy and relieved, and it thanked {hero.id} with a nuzzle from its snout. The ending shows the worry is gone because the treasure is safe again."
            )
        )
    else:
        qa.append(
            (
                f"Why was the treasure lost?",
                f"The delay gave the danger time to get worse, so the rescue came too late. Even a brave helper cannot always fix a problem once the obstacle has already carried the prize away."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.pronoun().capitalize()} learned to move sooner and bring the right gear. The story ends sadly, but the lesson makes {hero.pronoun('object')} readier to help next time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"snout"} | set(f["animal_cfg"].tags) | set(f["obstacle"].tags) | set(f["tool"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="woods",
        animal="piglet",
        treasure="apple",
        obstacle="crack",
        tool="stick",
        hero_name="Nora",
        hero_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="meadow",
        animal="mole",
        treasure="bell",
        obstacle="briar",
        tool="blanket",
        hero_name="Ben",
        hero_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        setting="marsh",
        animal="tapir_calf",
        treasure="map_tube",
        obstacle="river",
        tool="hook",
        hero_name="Maya",
        hero_gender="girl",
        parent="mother",
        trait="brave",
        delay=0,
    ),
    StoryParams(
        setting="marsh",
        animal="piglet",
        treasure="apple",
        obstacle="river",
        tool="hook",
        hero_name="Leo",
        hero_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=2,
    ),
]


ASP_RULES = r"""
% reasonableness gate
solves(O,T) :- works_for(T,O).
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(S,A,Tr,O,T) :- setting(S), animal(A), treasure(Tr), obstacle(O), tool(T),
                     solves(O,T), sensible(T).

% outcome model
severity(V) :- chosen_obstacle(O), obstacle_severity(O,S), delay(D), V = S + D.
contained :- chosen_tool(T), chosen_obstacle(O), solves(O,T),
             tool_power(T,P), severity(V), P >= V.
outcome(saved) :- contained.
outcome(lost) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_severity", oid, obstacle.severity))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        lines.append(asp.fact("tool_power", tid, tool.power))
        for oid in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tid, oid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def outcome_of(params: StoryParams) -> str:
    if params.tool not in TOOLS or params.obstacle not in OBSTACLES:
        return "?"
    return "saved" if is_solved(TOOLS[params.tool], OBSTACLES[params.obstacle], params.delay) else "lost"


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
    p_sens = {t.id for t in sensible_tools()}
    if c_sens == p_sens:
        print(f"OK: sensible tools match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child follows snout sounds into a small adventure and helps with the right tool."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before the rescue works; higher makes losses likelier")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.tool in TOOLS and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(args.tool))
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not obstacle_needs_tool(obstacle, tool):
            raise StoryError(explain_obstacle_rejection(obstacle, tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.animal is None or c[1] == args.animal)
        and (args.treasure is None or c[2] == args.treasure)
        and (args.obstacle is None or c[3] == args.obstacle)
        and (args.tool is None or c[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, animal_id, treasure_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        treasure=treasure_id,
        obstacle=obstacle_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        parent=parent,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in [
        ("setting", SETTINGS),
        ("animal", ANIMALS),
        ("treasure", TREASURES),
        ("obstacle", OBSTACLES),
        ("tool", TOOLS),
    ]:
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value})")

    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(params.tool))
    if not obstacle_needs_tool(obstacle, tool):
        raise StoryError(explain_obstacle_rejection(obstacle, tool))

    world = tell(
        SETTINGS[params.setting],
        ANIMALS[params.animal],
        TREASURES[params.treasure],
        obstacle,
        tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, animal, treasure, obstacle, tool) combos:\n")
        for setting_id, animal_id, treasure_id, obstacle_id, tool_id in combos:
            print(f"  {setting_id:7} {animal_id:11} {treasure_id:9} {obstacle_id:8} {tool_id}")
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
                f"### {p.hero_name}: {p.animal} at {p.obstacle} with {p.tool} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
