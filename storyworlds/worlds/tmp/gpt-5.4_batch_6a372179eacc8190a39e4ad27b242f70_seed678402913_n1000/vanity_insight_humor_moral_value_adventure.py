#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py
=======================================================================

A standalone story world about a child whose vanity makes an adventure harder,
and a companion whose insight helps turn a silly setback into a wiser ending.

The domain is deliberately small and classical:

- two children go on a treasure-style adventure
- one child insists on wearing/showing off something flashy
- the flashy thing causes a comic problem at an obstacle
- a practical tool solves the obstacle, if it is actually the right tool
- the ending proves the moral: clever, useful choices matter more than show

Run it
------
python storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py
python storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py --all
python storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py --qa
python storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py --asp
python storyworlds/worlds/gpt-5.4/vanity_insight_humor_moral_value_adventure.py --verify
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
VANITY_INIT = 5.0
INSIGHTFUL_TRAITS = {"observant", "calm", "wise", "patient"}


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


@dataclass
class Adventure:
    id: str
    scene: str
    launch: str
    treasure: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    locale: str
    need: str
    severity: int
    danger_line: str
    solved_line: str
    missed_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FlashyItem:
    id: str
    phrase: str
    short: str
    snag: str
    comedy: str
    burden: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    phrase: str
    solves: set[str]
    sense: int
    power: int
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    adventure: str
    obstacle: str
    flashy_item: str
    tool: str
    hero_name: str
    hero_gender: str
    guide_name: str
    guide_gender: str
    guide_trait: str
    parent: str
    delay: int = 0
    relation: str = "friends"
    hero_age: int = 6
    guide_age: int = 6
    seed: Optional[int] = None


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


def _r_flashy_trouble(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("flashy")
    obstacle = world.facts.get("obstacle_cfg")
    if hero.meters["attempt"] < THRESHOLD or item.meters["worn"] < THRESHOLD:
        return []
    sig = ("flashy_trouble", obstacle.id if obstacle else "", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["delay"] += float(item.attrs.get("burden", 1))
    hero.meters["stuck"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["vanity"] = max(0.0, hero.memes["vanity"] - 1.0)
    if "guide" in world.entities:
        world.get("guide").memes["insight"] += 1
    return ["__comic__"]


def _r_day_gets_late(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["delay"] < THRESHOLD:
        return []
    sig = ("late", int(hero.meters["delay"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("day").meters["late"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="flashy_trouble", tag="physical", apply=_r_flashy_trouble),
    Rule(name="late_day", tag="physical", apply=_r_day_gets_late),
]


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
        for sent in produced:
            world.say(sent)
    return produced


ADVENTURES = {
    "jungle": Adventure(
        id="jungle",
        scene="a tangle of bright green jungle paths",
        launch="At the edge of the jungle trail, the leaves flicked rainwater onto their sleeves.",
        treasure="the Moonfruit Marker",
        path="a map with a dotted line through fern tunnels",
        tags={"jungle", "map", "adventure"},
    ),
    "canyon": Adventure(
        id="canyon",
        scene="a red canyon full of windy ledges",
        launch="At the canyon gate, warm wind whistled through the rocks like a tiny flute.",
        treasure="the Sunstone Badge",
        path="a map with zigzags drawn up the cliff path",
        tags={"canyon", "adventure"},
    ),
    "ruins": Adventure(
        id="ruins",
        scene="old stone ruins with vine-wrapped doors",
        launch="Near the ruined archway, pigeons fluttered out and made the dust dance.",
        treasure="the Whispering Key",
        path="a map with curled arrows around cracked pillars",
        tags={"ruins", "adventure"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="stream",
        locale="a cold stream that skipped over round stones",
        need="cross",
        severity=2,
        danger_line="The stream looked playful, but the stones were slick and the water pushed at little ankles.",
        solved_line="They crossed the stream and reached the treasure mark on the other bank.",
        missed_line="By the time they sorted themselves out, the treasure mark on the other bank had to wait for another day.",
        tags={"stream", "water", "cross"},
    ),
    "cliff": Obstacle(
        id="cliff",
        label="cliff",
        locale="a short cliff with handholds like crooked smiles",
        need="climb",
        severity=3,
        danger_line="The cliff was not huge, but loose pebbles kept slipping down the face.",
        solved_line="They climbed the cliff and spotted the treasure mark shining from the ledge above.",
        missed_line="The cliff stayed above them while the afternoon light thinned into gold.",
        tags={"cliff", "climb"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="tunnel",
        locale="a tunnel mouth dark as a closed eye",
        need="light",
        severity=2,
        danger_line="The tunnel breathed cool air, and the floor disappeared into blackness after two steps.",
        solved_line="They lit the way properly and padded through the tunnel to the treasure mark inside.",
        missed_line="Without a good plan, the tunnel remained only a dark guess, and the treasure had to stay hidden.",
        tags={"tunnel", "dark", "light"},
    ),
}

FLASHY_ITEMS = {
    "cape": FlashyItem(
        id="cape",
        phrase="a satin captain's cape with a silver edge",
        short="cape",
        snag="caught on a branch",
        comedy="The cape tried to be grand and mostly succeeded at being in the way.",
        burden=1,
        tags={"cape", "vanity"},
    ),
    "feather_hat": FlashyItem(
        id="feather_hat",
        phrase="a giant feather hat that bobbed like a goose on parade",
        short="hat",
        snag="flopped over one eye",
        comedy="Every proud step made the feather bounce as if it were applauding itself.",
        burden=2,
        tags={"hat", "vanity", "humor"},
    ),
    "medal_belt": FlashyItem(
        id="medal_belt",
        phrase="a belt of shiny medals that jingled with every wiggle",
        short="medal belt",
        snag="clanked against the rocks",
        comedy="The medals made such an important noise that even the lizards seemed to stare.",
        burden=1,
        tags={"medals", "vanity", "humor"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        phrase="a coil of rope",
        solves={"cross", "climb"},
        sense=3,
        power=3,
        use_line="looped the rope to steady the crossing and give careful feet a line to hold",
        tags={"rope", "adventure", "tool"},
    ),
    "lantern": Tool(
        id="lantern",
        phrase="a bright lantern",
        solves={"light"},
        sense=3,
        power=3,
        use_line="clicked on the lantern and washed the dark path with safe yellow light",
        tags={"lantern", "light", "tool"},
    ),
    "walking_stick": Tool(
        id="walking_stick",
        phrase="a sturdy walking stick",
        solves={"cross"},
        sense=2,
        power=2,
        use_line="tested each stone with the walking stick before anyone stepped down",
        tags={"stick", "water", "tool"},
    ),
    "grappling_hook": Tool(
        id="grappling_hook",
        phrase="a small grappling hook",
        solves={"climb"},
        sense=2,
        power=2,
        use_line="set the grappling hook onto a firm root and made a safe little hand line",
        tags={"hook", "climb", "tool"},
    ),
    "pearl_comb": Tool(
        id="pearl_comb",
        phrase="a pearl comb",
        solves=set(),
        sense=1,
        power=0,
        use_line="combed the air very beautifully",
        tags={"comb", "vanity"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Ava", "Nora", "Poppy", "June", "Ivy"]
BOY_NAMES = ["Owen", "Max", "Finn", "Leo", "Eli", "Sam", "Theo", "Ben"]
GUIDE_TRAITS = ["observant", "calm", "wise", "patient", "cheerful", "clever"]


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return obstacle.need in tool.solves


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for adv_id in ADVENTURES:
        for obs_id, obstacle in OBSTACLES.items():
            for flashy_id in FLASHY_ITEMS:
                for tool_id, tool in TOOLS.items():
                    if tool_fits(tool, obstacle) and tool.sense >= SENSE_MIN:
                        combos.append((adv_id, obs_id, flashy_id, tool_id))
    return combos


def guide_can_prevent(relation: str, hero_age: int, guide_age: int, guide_trait: str) -> bool:
    insightful = guide_trait in INSIGHTFUL_TRAITS
    older = relation == "siblings" and guide_age > hero_age
    return insightful and older


def challenge_value(obstacle: Obstacle, flashy: FlashyItem, delay: int) -> int:
    return obstacle.severity + flashy.burden + delay


def succeeds(tool: Tool, obstacle: Obstacle, flashy: FlashyItem, delay: int) -> bool:
    return tool.power >= challenge_value(obstacle, flashy, delay)


def outcome_of(params: StoryParams) -> str:
    if guide_can_prevent(
        relation=params.relation,
        hero_age=params.hero_age,
        guide_age=params.guide_age,
        guide_trait=params.guide_trait,
    ):
        return "averted"
    tool = TOOLS[params.tool]
    obstacle = OBSTACLES[params.obstacle]
    flashy = FLASHY_ITEMS[params.flashy_item]
    return "crossed" if succeeds(tool, obstacle, flashy, params.delay) else "missed"


def explain_tool(tool_id: str, obstacle_id: str) -> str:
    tool = TOOLS[tool_id]
    obstacle = OBSTACLES[obstacle_id]
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools() if tool_fits(t, obstacle)))
        return (
            f"(Refusing tool '{tool_id}': it is too silly for this world "
            f"(sense={tool.sense} < {SENSE_MIN}). Try a practical tool such as {better}.)"
        )
    return (
        f"(No story: {tool.phrase} does not solve the {obstacle.label}. "
        f"Pick a tool that can handle {obstacle.need}.)"
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def predict_problem(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "delay": int(hero.meters["delay"]),
        "embarrassment": hero.memes["embarrassment"] >= THRESHOLD,
        "late": sim.get("day").meters["late"] >= THRESHOLD,
    }


def opening(world: World, adventure: Adventure, hero: Entity, guide: Entity) -> None:
    hero.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"{adventure.launch} {hero.id} and {guide.id} had come to explore {adventure.scene}."
    )
    world.say(
        f"In {hero.id}'s pocket was {adventure.path}, and at the end of it waited {adventure.treasure}."
    )


def show_off(world: World, hero: Entity, flashy: FlashyItem) -> None:
    hero.memes["vanity"] = VANITY_INIT
    world.get("flashy").meters["worn"] += 1
    world.say(
        f"But before they began, {hero.id} pulled on {flashy.phrase}. "
        f"{flashy.comedy}"
    )
    world.say(
        f'"If treasure sees me first," {hero.id} said, "it will know I am the grandest explorer here."'
    )


def guide_warning(world: World, guide: Entity, hero: Entity, obstacle: Obstacle, flashy: FlashyItem) -> None:
    pred = predict_problem(world)
    world.facts["predicted_delay"] = pred["delay"]
    extra = " It might slow us down." if pred["delay"] else ""
    world.say(
        f'{guide.id} squinted at the path. "Your {flashy.short} looks splendid," '
        f'{guide.pronoun()} said, "but {obstacle.locale} is ahead, and splendid is not the same as useful.{extra}"'
    )


def near_miss_choice(world: World, guide: Entity, hero: Entity, tool: Tool) -> None:
    guide.memes["insight"] += 1
    hero.memes["respect"] += 1
    hero.memes["vanity"] = max(0.0, hero.memes["vanity"] - 3.0)
    world.say(
        f"{hero.id} looked at the path, then at {guide.id}, and then at the practical answer: {tool.phrase}."
    )
    world.say(
        f'"You had the right insight," {hero.id} admitted. {hero.pronoun().capitalize()} folded the fancy thing away and reached for the tool instead.'
    )


def reach_obstacle(world: World, obstacle: Obstacle) -> None:
    world.say(f"Soon they reached {obstacle.locale}.")
    world.say(obstacle.danger_line)


def attempt_with_vanity(world: World, hero: Entity, flashy: FlashyItem) -> None:
    hero.meters["attempt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried first while still showing off, and the {flashy.short} {flashy.snag}."
    )
    world.say(
        f"For one ridiculous moment, the great explorer looked less grand than tangled."
    )


def wise_fix(world: World, guide: Entity, tool: Tool, obstacle: Obstacle) -> None:
    guide.memes["insight"] += 1
    world.say(
        f'{guide.id} did not laugh for long. "{tool.phrase.capitalize()} first," '
        f'{guide.pronoun()} said, and then {guide.pronoun()} {tool.use_line}.'
    )
    world.say(obstacle.solved_line)


def missed_fix(world: World, guide: Entity, tool: Tool, obstacle: Obstacle) -> None:
    guide.memes["insight"] += 1
    world.say(
        f'{guide.id} tried to help with {tool.phrase}, and {guide.pronoun()} {tool.use_line}.'
    )
    world.say(
        f"It was a good idea, just not enough after all the fuss and delay. {obstacle.missed_line}"
    )


def moral_ending_crossed(
    world: World,
    hero: Entity,
    guide: Entity,
    parent: Entity,
    adventure: Adventure,
    flashy: FlashyItem,
    tool: Tool,
) -> None:
    hero.memes["insight"] += 1
    hero.memes["relief"] += 1
    guide.memes["relief"] += 1
    world.say(
        f"At the treasure mark, they found not a chest of jewels but a little tin box with a note from {parent.label_word.capitalize()}."
    )
    world.say(
        f'"Best explorers carry what helps," the note said. {hero.id} laughed, touched the {flashy.short}, and then lifted {tool.phrase}.'
    )
    world.say(
        f'"Vanity made me noisy," {hero.id} said, "but insight got us to {adventure.treasure}." '
        f'They went home dusty, proud, and much wiser.'
    )


def moral_ending_missed(
    world: World,
    hero: Entity,
    guide: Entity,
    parent: Entity,
    flashy: FlashyItem,
    tool: Tool,
) -> None:
    hero.memes["insight"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"When they finally turned back, {parent.label_word} was waiting by the trail sign with sandwiches and a kindly raised eyebrow."
    )
    world.say(
        f'{hero.id} sighed. "I packed too much show and not enough sense." {guide.id} patted {tool.phrase} and nodded.'
    )
    world.say(
        f'They did not bring home the treasure that day, but they did bring home insight, and that was worth more than applause from a {flashy.short}.'
    )


def tell(
    adventure: Adventure,
    obstacle: Obstacle,
    flashy: FlashyItem,
    tool: Tool,
    hero_name: str,
    hero_gender: str,
    guide_name: str,
    guide_gender: str,
    guide_trait: str,
    parent_type: str,
    delay: int,
    relation: str,
    hero_age: int,
    guide_age: int,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            attrs={"name": hero_name, "age": hero_age, "relation": relation},
            traits=["bold"],
        )
    )
    guide = world.add(
        Entity(
            id="guide",
            kind="character",
            type=guide_gender,
            label=guide_name,
            phrase=guide_name,
            role="guide",
            attrs={"name": guide_name, "age": guide_age, "relation": relation},
            traits=[guide_trait],
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
        )
    )
    flashy_ent = world.add(
        Entity(
            id="flashy",
            type="item",
            label=flashy.short,
            phrase=flashy.phrase,
            attrs={"burden": flashy.burden},
            tags=set(flashy.tags),
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.id,
            phrase=tool.phrase,
            attrs={"sense": tool.sense, "power": tool.power},
            tags=set(tool.tags),
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.locale,
            attrs={"need": obstacle.need, "severity": obstacle.severity},
            tags=set(obstacle.tags),
        )
    )
    day = world.add(Entity(id="day", type="day", label="day"))

    hero.meters["delay"] = float(delay)

    opening(world, adventure, hero, guide)
    show_off(world, hero, flashy)

    world.para()
    reach_obstacle(world, obstacle)
    guide_warning(world, guide, hero, obstacle, flashy)

    prevented = guide_can_prevent(
        relation=relation,
        hero_age=hero_age,
        guide_age=guide_age,
        guide_trait=guide_trait,
    )

    if prevented:
        near_miss_choice(world, guide, hero, tool)
        world.para()
        wise_fix(world, guide, tool, obstacle)
        world.para()
        moral_ending_crossed(world, hero, guide, parent, adventure, flashy, tool)
        outcome = "averted"
    else:
        world.say(f'"I can be both splendid and swift," {hero_name} declared.')
        world.para()
        attempt_with_vanity(world, hero, flashy)
        total_delay = int(hero.meters["delay"])
        success = succeeds(tool, obstacle, flashy, delay=total_delay)
        world.para()
        if success:
            wise_fix(world, guide, tool, obstacle)
            world.para()
            moral_ending_crossed(world, hero, guide, parent, adventure, flashy, tool)
            outcome = "crossed"
        else:
            missed_fix(world, guide, tool, obstacle)
            world.para()
            moral_ending_missed(world, hero, guide, parent, flashy, tool)
            outcome = "missed"

    world.facts.update(
        adventure=adventure,
        obstacle_cfg=obstacle,
        flashy_cfg=flashy,
        tool_cfg=tool,
        hero=hero,
        guide=guide,
        parent=parent,
        flashy=flashy_ent,
        tool=tool_ent,
        obstacle=obstacle_ent,
        day=day,
        outcome=outcome,
        relation=relation,
        hero_name=hero_name,
        guide_name=guide_name,
        total_delay=int(hero.meters["delay"]),
        prevented=prevented,
        success=outcome in {"averted", "crossed"},
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    obstacle = f["obstacle_cfg"]
    flashy = f["flashy_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    if outcome == "missed":
        return [
            'Write an adventure story for a 3-to-5-year-old that uses the words "vanity" and "insight".',
            f"Tell a humorous treasure-trail story where {hero.label} shows off in {flashy.phrase}, gets delayed at a {obstacle.label}, and learns that practical thinking matters more than looking grand.",
            f"Write a child-facing adventure with a gentle moral: {guide.label}'s insight is useful, even when the treasure must wait for another day.",
        ]
    return [
        'Write an adventure story for a 3-to-5-year-old that uses the words "vanity" and "insight".',
        f"Tell a humorous adventure where {hero.label} wants to look splendid in {flashy.phrase}, but {guide.label} helps with {tool.phrase} at a {obstacle.label}.",
        f"Write a simple treasure-hunt story with a moral about vanity, insight, and choosing tools that really help.",
    ]


KNOWLEDGE = {
    "rope": [
        (
            "What is a rope useful for on an adventure?",
            "A rope can help people hold on, climb, or cross carefully. It is useful because it gives steady support where the path feels tricky.",
        )
    ],
    "lantern": [
        (
            "Why is a lantern helpful in a dark place?",
            "A lantern makes light so you can see where to step. Seeing clearly helps people stay safe and calm.",
        )
    ],
    "climb": [
        (
            "Why should climbers use steady help on a cliff?",
            "Cliffs can have loose rocks and slippery spots. Steady help, like a rope or a safe handhold, makes climbing safer.",
        )
    ],
    "water": [
        (
            "Why can crossing a stream be hard?",
            "Stream stones can be slippery, and moving water can push at your feet. That is why careful crossing matters.",
        )
    ],
    "dark": [
        (
            "Why is it hard to walk in a dark tunnel?",
            "It is hard because you cannot see the floor or walls clearly. Good light helps you know where to put your feet.",
        )
    ],
    "vanity": [
        (
            "What does vanity mean?",
            "Vanity means caring too much about looking grand or impressive. It can distract you from what really matters.",
        )
    ],
    "insight": [
        (
            "What is insight?",
            "Insight is understanding what is really going on and what will help. It is like seeing the smart answer before trouble grows.",
        )
    ],
    "tool": [
        (
            "Why are useful tools better than flashy things on a hard path?",
            "Useful tools solve the real problem in front of you. Flashy things may look exciting, but they do not always help you move safely.",
        )
    ],
}
KNOWLEDGE_ORDER = ["vanity", "insight", "water", "climb", "dark", "rope", "lantern", "tool"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    parent = f["parent"]
    obstacle = f["obstacle_cfg"]
    flashy = f["flashy_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {guide.label}, two young explorers on a treasure hunt. They are trying to reach {f['adventure'].treasure}.",
        ),
        (
            "What made the adventure harder at first?",
            f"{hero.label} cared too much about looking grand in {flashy.phrase}. That vanity slowed the adventure because the flashy thing got in the way at the {obstacle.label}.",
        ),
        (
            f"What helpful idea did {guide.label} have?",
            f"{guide.label} showed real insight by thinking about what the path needed instead of what looked impressive. {guide.pronoun().capitalize()} used {tool.phrase} because it could really handle the {obstacle.label}.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"Did {hero.label} listen before a big problem happened?",
                f"Yes. {hero.label} listened when {guide.label} pointed out the real problem, so the silly trouble became only a near miss. That choice let them solve the obstacle without wasting the day.",
            )
        )
    elif outcome == "crossed":
        qa.append(
            (
                f"What happened when {hero.label} tried to show off?",
                f"The flashy {flashy.short} caused a comic snag and made {hero.label} look tangled instead of grand. After that, {guide.label}'s practical plan with {tool.phrase} got them across safely.",
            )
        )
    else:
        qa.append(
            (
                "Did they get the treasure that day?",
                f"No. They had a good tool in the end, but the earlier showing off cost them too much time. They came home with insight instead of treasure, because the delay made the adventure run out of afternoon.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The story teaches that vanity can make a problem bigger, while insight helps people choose what is truly useful. Looking impressive matters less than acting wisely and kindly on a hard path.",
        )
    )
    qa.append(
        (
            f"Why was the ending still good, even with {parent.label_word} waiting at the trail?",
            f"The ending was good because {hero.label} learned something real and admitted the mistake honestly. That new understanding will help on the next adventure even more than shiny treasure would.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"vanity", "insight", "tool"} | set(world.facts["tool_cfg"].tags) | set(world.facts["obstacle_cfg"].tags)
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


CURATED = [
    StoryParams(
        adventure="jungle",
        obstacle="stream",
        flashy_item="feather_hat",
        tool="walking_stick",
        hero_name="Max",
        hero_gender="boy",
        guide_name="Nora",
        guide_gender="girl",
        guide_trait="observant",
        parent="mother",
        delay=0,
        relation="friends",
        hero_age=6,
        guide_age=6,
    ),
    StoryParams(
        adventure="canyon",
        obstacle="cliff",
        flashy_item="cape",
        tool="rope",
        hero_name="Lila",
        hero_gender="girl",
        guide_name="Ben",
        guide_gender="boy",
        guide_trait="wise",
        parent="father",
        delay=1,
        relation="siblings",
        hero_age=5,
        guide_age=7,
    ),
    StoryParams(
        adventure="ruins",
        obstacle="tunnel",
        flashy_item="medal_belt",
        tool="lantern",
        hero_name="Finn",
        hero_gender="boy",
        guide_name="Ivy",
        guide_gender="girl",
        guide_trait="patient",
        parent="mother",
        delay=2,
        relation="friends",
        hero_age=6,
        guide_age=6,
    ),
    StoryParams(
        adventure="canyon",
        obstacle="cliff",
        flashy_item="feather_hat",
        tool="grappling_hook",
        hero_name="Poppy",
        hero_gender="girl",
        guide_name="Theo",
        guide_gender="boy",
        guide_trait="clever",
        parent="father",
        delay=0,
        relation="friends",
        hero_age=7,
        guide_age=6,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(A, O, F, T) :- adventure(A), obstacle(O), flashy(F), tool(T),
                     solves(T, Need), needs(O, Need),
                     sense(T, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
older_guide :- relation(siblings), guide_age(GA), hero_age(HA), GA > HA.
insightful_guide :- guide_trait(T), insightful_trait(T).
prevented :- older_guide, insightful_guide.

challenge(V) :- chosen_obstacle(O), severity(O, S),
                chosen_flashy(F), burden(F, B),
                delay(D), V = S + B + D.

can_succeed :- chosen_tool(T), power(T, P), challenge(V), P >= V.

outcome(averted) :- prevented.
outcome(crossed) :- not prevented, can_succeed.
outcome(missed)  :- not prevented, not can_succeed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for adv_id in ADVENTURES:
        lines.append(asp.fact("adventure", adv_id))
    for obs_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obs_id))
        lines.append(asp.fact("needs", obs_id, obstacle.need))
        lines.append(asp.fact("severity", obs_id, obstacle.severity))
    for flashy_id, flashy in FLASHY_ITEMS.items():
        lines.append(asp.fact("flashy", flashy_id))
        lines.append(asp.fact("burden", flashy_id, flashy.burden))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        for need in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(INSIGHTFUL_TRAITS):
        lines.append(asp.fact("insightful_trait", trait))
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
            asp.fact("chosen_flashy", params.flashy_item),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("guide_age", params.guide_age),
            asp.fact("guide_trait", params.guide_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    if "vanity" not in sample.story.lower() and "insight" not in sample.story.lower():
        raise StoryError("Smoke test failed: expected key themes missing from prose.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=True, header="SMOKE")
    _ = sample.to_json()


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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
        smoke_test()
        print("OK: smoke generate/emit/json test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: vanity causes comic trouble, insight solves the real problem."
    )
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--flashy-item", dest="flashy_item", choices=FLASHY_ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start lost to fuss and showing off")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check inline ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, obstacle) or tool.sense < SENSE_MIN:
            raise StoryError(explain_tool(args.tool, args.obstacle))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN and not args.obstacle:
        raise StoryError(
            f"(Refusing tool '{args.tool}': it is too silly for this world "
            f"(sense={TOOLS[args.tool].sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.adventure is None or combo[0] == args.adventure)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.flashy_item is None or combo[2] == args.flashy_item)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    adventure, obstacle, flashy_item, tool = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    guide_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    guide_name = _pick_name(rng, guide_gender, avoid=hero_name)
    guide_trait = rng.choice(GUIDE_TRAITS)
    relation = rng.choice(["friends", "siblings"])
    ages = rng.sample([4, 5, 6, 7], 2)
    hero_age, guide_age = ages[0], ages[1]
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        adventure=adventure,
        obstacle=obstacle,
        flashy_item=flashy_item,
        tool=tool,
        hero_name=hero_name,
        hero_gender=hero_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
        guide_trait=guide_trait,
        parent=parent,
        delay=delay,
        relation=relation,
        hero_age=hero_age,
        guide_age=guide_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.adventure not in ADVENTURES:
        raise StoryError(f"(Unknown adventure '{params.adventure}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.flashy_item not in FLASHY_ITEMS:
        raise StoryError(f"(Unknown flashy item '{params.flashy_item}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool '{params.tool}'.)")

    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    if not tool_fits(tool, obstacle) or tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool, params.obstacle))

    world = tell(
        adventure=ADVENTURES[params.adventure],
        obstacle=obstacle,
        flashy=FLASHY_ITEMS[params.flashy_item],
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
        guide_trait=params.guide_trait,
        parent_type=params.parent,
        delay=params.delay,
        relation=params.relation,
        hero_age=params.hero_age,
        guide_age=params.guide_age,
    )

    story = world.render().replace("hero", params.hero_name).replace("guide", params.guide_name)
    story = story.replace("parent", world.facts["parent"].label_word)

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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (adventure, obstacle, flashy_item, tool) combos:\n")
        for adventure, obstacle, flashy_item, tool in combos:
            print(f"  {adventure:8} {obstacle:7} {flashy_item:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = (
                f"### {p.hero_name} and {p.guide_name}: {p.flashy_item} at the "
                f"{p.obstacle} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
