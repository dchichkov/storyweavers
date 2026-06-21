#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/symbol_saver_minute_foreshadowing_fable.py
=====================================================================

A standalone storyworld for a small fable-shaped domain:

A young animal in a meadow storehouse notices a warning sign before a storm.
A painted symbol, a tiny clue, and one spare minute foreshadow danger. The hero
must choose whether to fetch the right "saver" tool in time to protect the
community's winter food.

The world model is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate over compatible problem/fix combinations
- an inline ASP twin for the same gate and for outcome parity
- state-driven prose, plus three Q&A sets grounded in world state

Run it
------
    python storyworlds/worlds/gpt-5.4/symbol_saver_minute_foreshadowing_fable.py
    python storyworlds/worlds/gpt-5.4/symbol_saver_minute_foreshadowing_fable.py --all
    python storyworlds/worlds/gpt-5.4/symbol_saver_minute_foreshadowing_fable.py --verify
    python storyworlds/worlds/gpt-5.4/symbol_saver_minute_foreshadowing_fable.py -n 5 --seed 7 --qa
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    vulnerable_to: set[str] = field(default_factory=set)
    repairs: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "goose", "ewe", "doe"}
        male = {"boy", "buck", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class HeroSpec:
    id: str
    species: str
    title: str
    trait: str
    home_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FoodSpec:
    id: str
    label: str
    phrase: str
    vulnerable_to: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class ThreatSpec:
    id: str
    label: str
    clue: str
    threat_line: str
    harms: set[str]
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolSpec:
    id: str
    label: str
    phrase: str
    saver_name: str
    repairs: set[str]
    power: int
    use_line: str
    fail_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SymbolSpec:
    id: str
    phrase: str
    meaning: str
    lesson_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    food: str
    threat: str
    tool: str
    symbol: str
    elder_name: str
    delay: int = 0
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


def _r_food_ruined(world: World) -> list[str]:
    out: list[str] = []
    food = world.get("food")
    store = world.get("store")
    if food.meters["exposed"] < THRESHOLD:
        return out
    sig = ("ruined", food.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    food.meters["spoiled"] += 1
    store.meters["loss"] += 1
    for eid in ("hero", "elder"):
        world.get(eid).memes["sorrow"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="food_ruined", tag="physical", apply=_r_food_ruined),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


HEROES = {
    "mole": HeroSpec(
        id="mole",
        species="mole",
        title="little Mole",
        trait="patient",
        home_word="burrow",
        tags={"mole"},
    ),
    "squirrel": HeroSpec(
        id="squirrel",
        species="squirrel",
        title="quick Squirrel",
        trait="nimble",
        home_word="oak hollow",
        tags={"squirrel"},
    ),
    "mouse": HeroSpec(
        id="mouse",
        species="mouse",
        title="small Mouse",
        trait="careful",
        home_word="hedge hole",
        tags={"mouse"},
    ),
}

FOODS = {
    "grain": FoodSpec(
        id="grain",
        label="grain",
        phrase="a sack of winter grain",
        vulnerable_to={"rain", "puddle"},
        tags={"grain"},
    ),
    "nuts": FoodSpec(
        id="nuts",
        label="nuts",
        phrase="a basket of dry nuts",
        vulnerable_to={"rain", "puddle"},
        tags={"nuts"},
    ),
    "berries": FoodSpec(
        id="berries",
        label="berries",
        phrase="a clay jar of dried berries",
        vulnerable_to={"rain", "lid"},
        tags={"berries"},
    ),
}

THREATS = {
    "roof_crack": ThreatSpec(
        id="roof_crack",
        label="a crack in the roof",
        clue="one cold drop slipped through the rafters and landed beside the food",
        threat_line="If the storm came hard, rain would pour through the roof crack.",
        harms={"rain"},
        severity=2,
        tags={"roof", "rain"},
    ),
    "low_shelf": ThreatSpec(
        id="low_shelf",
        label="a low shelf near the floor",
        clue="a bead of water crept under the door and touched the lowest shelf",
        threat_line="If the ditch filled, a floor puddle would creep under the door.",
        harms={"puddle"},
        severity=2,
        tags={"puddle", "shelf"},
    ),
    "loose_lid": ThreatSpec(
        id="loose_lid",
        label="a loose jar lid",
        clue="the lid gave a tiny click and sat crooked instead of tight",
        threat_line="If damp air entered, the berries would turn soft and sour.",
        harms={"lid"},
        severity=1,
        tags={"lid", "berries"},
    ),
}

TOOLS = {
    "roof_saver_patch": ToolSpec(
        id="roof_saver_patch",
        label="roof-saver patch",
        phrase="a roof-saver patch of waxed leaves",
        saver_name="roof-saver",
        repairs={"roof_crack"},
        power=3,
        use_line="pressed the waxed leaves over the crack and tied them firm with reed string",
        fail_line="pressed the patch in place, but the rain was already streaming too hard through the gap",
        qa_line="used a roof-saver patch of waxed leaves to cover the crack",
        tags={"roof_saver", "repair"},
    ),
    "shelf_saver_stone": ToolSpec(
        id="shelf_saver_stone",
        label="shelf-saver stone",
        phrase="a flat shelf-saver stone",
        saver_name="shelf-saver",
        repairs={"low_shelf"},
        power=3,
        use_line="heaved the flat stone under the food and lifted it clear of the creeping water",
        fail_line="got the stone under the food, but the puddle had already soaked the bottom",
        qa_line="slid a shelf-saver stone underneath to lift the food above the water",
        tags={"shelf_saver", "repair"},
    ),
    "jar_saver_band": ToolSpec(
        id="jar_saver_band",
        label="jar-saver band",
        phrase="a jar-saver band of braided grass",
        saver_name="jar-saver",
        repairs={"loose_lid"},
        power=2,
        use_line="wrapped the braided band around the jar and pulled the lid snug again",
        fail_line="wrapped the band on, but damp had already crept into the berries",
        qa_line="tightened the lid with a jar-saver band of braided grass",
        tags={"jar_saver", "repair"},
    ),
}

SYMBOLS = {
    "drop": SymbolSpec(
        id="drop",
        phrase="a blue drop symbol",
        meaning="water can sneak in where no one expects it",
        lesson_word="watch the leaks",
        tags={"symbol", "water"},
    ),
    "leaf": SymbolSpec(
        id="leaf",
        phrase="a green leaf symbol",
        meaning="small care keeps winter stores safe",
        lesson_word="save before you boast",
        tags={"symbol", "care"},
    ),
    "sun": SymbolSpec(
        id="sun",
        phrase="a gold sun symbol",
        meaning="dry food must be kept dry to stay sweet",
        lesson_word="a dry store feeds many mouths",
        tags={"symbol", "dry"},
    ),
}

ELDER_NAMES = ["Badger", "Tortoise", "Aunt Wren", "Old Hare"]


def hazard_at_risk(food: FoodSpec, threat: ThreatSpec) -> bool:
    return bool(food.vulnerable_to & threat.harms)


def tool_fits(tool: ToolSpec, threat: ThreatSpec) -> bool:
    return threat.id in tool.repairs


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for food_id, food in FOODS.items():
        for threat_id, threat in THREATS.items():
            if not hazard_at_risk(food, threat):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_fits(tool, threat):
                    combos.append((food_id, threat_id, tool_id))
    return sorted(combos)


def storm_severity(threat: ThreatSpec, delay: int) -> int:
    return threat.severity + delay


def is_saved(tool: ToolSpec, threat: ThreatSpec, delay: int) -> bool:
    return tool.power >= storm_severity(threat, delay)


def explain_combo(food: FoodSpec, threat: ThreatSpec, tool: Optional[ToolSpec] = None) -> str:
    if not hazard_at_risk(food, threat):
        return (
            f"(No story: {threat.label} would not spoil {food.label}, so the warning has no honest bite.)"
        )
    if tool is not None and not tool_fits(tool, threat):
        return (
            f"(No story: the {tool.label} does not fix {threat.label}. Pick a saver made for that trouble.)"
        )
    return "(No story: that combination does not belong in this little world.)"


def predict_loss(world: World, threat: ThreatSpec, tool: ToolSpec, delay: int) -> dict:
    sim = world.copy()
    food = sim.get("food")
    if not is_saved(tool, threat, delay):
        food.meters["exposed"] += 1
        propagate(sim, narrate=False)
    return {
        "spoiled": food.meters["spoiled"] >= THRESHOLD,
        "loss": sim.get("store").meters["loss"],
    }


def opening(world: World, hero: Entity, elder: Entity, food: Entity, symbol: SymbolSpec) -> None:
    world.say(
        f"In a meadow storehouse, {hero.id} the {hero.type} liked to boast that quick feet could solve any trouble."
    )
    world.say(
        f"Above the doorway hung {symbol.phrase}, painted there by {elder.id} to remind every neighbor that {symbol.meaning}."
    )
    world.say(
        f"Below it rested {food.phrase}, the kind of winter store that kept many bellies calm when the grass lay asleep."
    )


def foreshadow(world: World, hero: Entity, threat: ThreatSpec) -> None:
    hero.memes["notice"] += 1
    world.say(
        f"That afternoon the swallows flew low, the light turned pewter, and {threat.clue}."
    )
    world.say(
        f"{hero.id} paused for a minute. The little sign felt smaller than a storm, yet harder to ignore."
    )


def temptation(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"It is only a small thing," said {hero.id}. "Surely I can play one more race before I bother {elder.id}."'
    )


def elder_warning(world: World, hero: Entity, elder: Entity, threat: ThreatSpec, symbol: SymbolSpec, tool: ToolSpec, delay: int) -> None:
    pred = predict_loss(world, threat, tool, delay)
    world.facts["predicted_loss"] = pred["spoiled"]
    world.say(
        f'But {elder.id} looked from the sky to the {symbol.phrase} and said, "{threat.threat_line} Small signs are the first drums of large trouble."'
    )
    if pred["spoiled"]:
        world.say(
            f'"Use the {tool.label} now," {elder.id} added. "A saver fetched in one minute is stronger than a hundred regrets after rain."'
        )


def fetch_and_fix(world: World, hero: Entity, elder: Entity, food: Entity, threat: ThreatSpec, tool: ToolSpec, delay: int) -> None:
    hero.memes["care"] += 1
    if delay == 0:
        hurry = "at once"
    elif delay == 1:
        hurry = "after one last look at the dark clouds"
    else:
        hurry = "after wasting two nervous minutes"
    world.say(
        f"{hero.id} ran {hurry} to fetch {tool.phrase}, the little saver kept beside the reeds and twine."
    )
    if is_saved(tool, threat, delay):
        world.say(
            f"{hero.pronoun('subject').capitalize()} {tool.use_line}."
        )
        hero.memes["relief"] += 1
        elder.memes["relief"] += 1
    else:
        food.meters["exposed"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.pronoun('subject').capitalize()} {tool.fail_line}."
        )


def storm_and_ending(world: World, hero: Entity, elder: Entity, food: Entity, threat: ThreatSpec, tool: ToolSpec, symbol: SymbolSpec) -> None:
    if food.meters["spoiled"] >= THRESHOLD:
        world.say(
            "Soon the storm struck. Rain drummed, water crept, and the storehouse smelled of wet loss instead of supper."
        )
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} head. The painted symbol had warned truly, but pride had walked slower than the cloud."
        )
        world.say(
            f'{elder.id} was gentle even then. "{symbol.lesson_word.capitalize()}," {elder.pronoun("subject")} said. "A small warning is already a kind of gift."'
        )
        world.say(
            f"And from that day on, {hero.id} listened when little signs whispered, for a saver is best fetched before the flood asks for it."
        )
        world.facts["outcome"] = "spoiled"
    else:
        world.say(
            "Then the storm struck. Rain drummed on the roof, and wind worried the door, but the winter food stayed dry."
        )
        world.say(
            f"{hero.id} touched the painted symbol and understood it at last. It was not decoration. It was memory made visible."
        )
        world.say(
            f'{elder.id} smiled. "{symbol.lesson_word.capitalize()}," {elder.pronoun("subject")} said. "The wise heart hears tomorrow in today\'s small sounds."'
        )
        world.say(
            f"And so {hero.id}, once proud of quick feet alone, became known as a careful saver of stores as well as steps."
        )
        world.facts["outcome"] = "saved"


def tell(hero_spec: HeroSpec, food_spec: FoodSpec, threat_spec: ThreatSpec, tool_spec: ToolSpec,
         symbol_spec: SymbolSpec, elder_name: str, delay: int) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_spec.title.split()[-1],
        kind="character",
        type=hero_spec.species,
        label=hero_spec.title,
        role="hero",
        traits=[hero_spec.trait],
        tags=set(hero_spec.tags),
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type="animal",
        label="the elder",
        role="elder",
        traits=["wise"],
    ))
    food = world.add(Entity(
        id="food",
        kind="thing",
        type="food",
        label=food_spec.label,
        phrase=food_spec.phrase,
        vulnerable_to=set(food_spec.vulnerable_to),
        tags=set(food_spec.tags),
    ))
    store = world.add(Entity(
        id="store",
        kind="thing",
        type="storehouse",
        label="storehouse",
    ))

    opening(world, hero, elder, food, symbol_spec)
    foreshadow(world, hero, threat_spec)

    world.para()
    temptation(world, hero, elder)
    elder_warning(world, hero, elder, threat_spec, symbol_spec, tool_spec, delay)

    world.para()
    fetch_and_fix(world, hero, elder, food, threat_spec, tool_spec, delay)
    storm_and_ending(world, hero, elder, food, threat_spec, tool_spec, symbol_spec)

    world.facts.update(
        hero=hero,
        elder=elder,
        food=food,
        food_cfg=food_spec,
        threat=threat_spec,
        tool=tool_spec,
        symbol=symbol_spec,
        delay=delay,
        saved=food.meters["spoiled"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    food = f["food_cfg"]
    threat = f["threat"]
    tool = f["tool"]
    symbol = f["symbol"]
    if f["outcome"] == "saved":
        return [
            'Write a short fable for a young child that includes the words "symbol", "saver", and "minute".',
            f"Tell a foreshadowing fable about {hero.id.lower()} noticing {threat.label} near {food.phrase}, trusting a painted symbol, and using a {tool.label} just in time.",
            "Write a gentle animal fable where a tiny warning matters more than boasting, and end with a clear moral image.",
        ]
    return [
        'Write a short fable for a young child that includes the words "symbol", "saver", and "minute".',
        f"Tell a foreshadowing fable about {hero.id.lower()} seeing {threat.label} near {food.phrase} but moving too slowly, so the warning comes true.",
        "Write a sad-but-gentle animal fable where a small clue foretells a larger loss, and finish with a spoken lesson.",
    ]


KNOWLEDGE = {
    "symbol": [
        (
            "What is a symbol?",
            "A symbol is a picture or mark that stands for an idea. It can remind people of something important even when no one is speaking."
        )
    ],
    "saver": [
        (
            "What does saver mean in a story like this?",
            "A saver is something that helps protect what matters. It can be a tool, a plan, or even a quick helpful action."
        )
    ],
    "minute": [
        (
            "How long is a minute?",
            "A minute is a short piece of time made of sixty seconds. It feels small, but sometimes one minute is enough to change what happens next."
        )
    ],
    "rain": [
        (
            "Why can rain spoil stored food?",
            "Rain adds water where dry food should stay dry. Once food gets wet, it can turn soft, moldy, or rotten."
        )
    ],
    "lid": [
        (
            "Why should a jar lid fit tightly?",
            "A tight lid keeps damp air and water out. That helps the food inside stay dry and safe longer."
        )
    ],
    "repair": [
        (
            "Why do small repairs matter?",
            "Small repairs stop trouble while it is still small. Fixing a crack or a loose part early can prevent a much bigger problem later."
        )
    ],
}
KNOWLEDGE_ORDER = ["symbol", "saver", "minute", "rain", "lid", "repair"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    food_cfg = f["food_cfg"]
    threat = f["threat"]
    tool = f["tool"]
    symbol = f["symbol"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {elder.id} in a meadow storehouse. They are trying to keep {food_cfg.phrase} safe before a storm."
        ),
        (
            "What was the symbol for?",
            f"The painted {symbol.phrase} reminded the animals that {symbol.meaning}. It mattered because the warning in the picture matched the small clue {hero.id} saw."
        ),
        (
            f"What clue foreshadowed the trouble?",
            f"The story planted a small warning before the storm: {threat.clue}. That quiet sign hinted that the larger trouble named by {threat.label} was coming."
        ),
        (
            f"Why did one minute matter?",
            f"One minute mattered because the danger was still small when {hero.id} first noticed it. In this story, a quick minute could be turned into a rescue instead of a regret."
        ),
    ]
    if f["outcome"] == "saved":
        out.append(
            (
                f"How did {hero.id} save the food?",
                f"{hero.id} fetched the {tool.label} and {tool.qa_line}. That worked because the repair matched the real problem and came before the storm grew too strong."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"The storm came, but the winter food stayed dry. {hero.id} understood that the symbol was wise advice, not mere paint, and became known as a careful saver."
            )
        )
    else:
        out.append(
            (
                f"Why was the saver not enough this time?",
                f"The {tool.label} was the right kind of tool, but it came too late. The storm had already beaten the repair, so the food was spoiled before the fix could truly help."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"The storm spoiled the food, and {hero.id} learned the warning had been true. The ending is sad, but it teaches that little signs should be trusted early."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"symbol", "saver", "minute", "repair"}
    threat = world.facts["threat"]
    if "rain" in threat.harms or "puddle" in threat.harms:
        tags.add("rain")
    if threat.id == "loose_lid":
        tags.add("lid")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.vulnerable_to:
            bits.append(f"vulnerable_to={sorted(ent.vulnerable_to)}")
        if ent.repairs:
            bits.append(f"repairs={sorted(ent.repairs)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="mouse",
        food="berries",
        threat="loose_lid",
        tool="jar_saver_band",
        symbol="sun",
        elder_name="Tortoise",
        delay=0,
    ),
    StoryParams(
        hero="squirrel",
        food="nuts",
        threat="roof_crack",
        tool="roof_saver_patch",
        symbol="leaf",
        elder_name="Badger",
        delay=0,
    ),
    StoryParams(
        hero="mole",
        food="grain",
        threat="low_shelf",
        tool="shelf_saver_stone",
        symbol="drop",
        elder_name="Old Hare",
        delay=1,
    ),
    StoryParams(
        hero="mouse",
        food="grain",
        threat="roof_crack",
        tool="roof_saver_patch",
        symbol="drop",
        elder_name="Aunt Wren",
        delay=2,
    ),
]


ASP_RULES = r"""
hazard(Food, Threat) :- food(Food), threat(Threat), vulnerable(Food, Kind), harms(Threat, Kind).
fits(Tool, Threat)   :- tool(Tool), threat(Threat), repairs(Tool, Threat).
valid(Food, Threat, Tool) :- hazard(Food, Threat), fits(Tool, Threat).

severity(V) :- chosen_threat(T), base_severity(T, B), delay(D), V = B + D.
saved       :- chosen_tool(Tool), chosen_threat(Threat), tool_power(Tool, P), severity(V), P >= V.
outcome(saved)   :- saved.
outcome(spoiled) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        for kind in sorted(food.vulnerable_to):
            lines.append(asp.fact("vulnerable", food_id, kind))
    for threat_id, threat in THREATS.items():
        lines.append(asp.fact("threat", threat_id))
        lines.append(asp.fact("base_severity", threat_id, threat.severity))
        for kind in sorted(threat.harms):
            lines.append(asp.fact("harms", threat_id, kind))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_power", tool_id, tool.power))
        for rep in sorted(tool.repairs):
            lines.append(asp.fact("repairs", tool_id, rep))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_threat", params.threat),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    threat = THREATS[params.threat]
    return "saved" if is_saved(tool, threat, params.delay) else "spoiled"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches.append(params)
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small foreshadowing fable about a warning symbol, a saver tool, and one important minute."
    )
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--food", choices=sorted(FOODS))
    ap.add_argument("--threat", choices=sorted(THREATS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--symbol", choices=sorted(SYMBOLS))
    ap.add_argument("--elder-name", choices=ELDER_NAMES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how many minutes the hero waits before fetching the saver")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid food/threat/tool combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.threat:
        if not hazard_at_risk(FOODS[args.food], THREATS[args.threat]):
            raise StoryError(explain_combo(FOODS[args.food], THREATS[args.threat]))
    if args.tool and args.threat:
        if not tool_fits(TOOLS[args.tool], THREATS[args.threat]):
            food = FOODS[args.food] if args.food else next(iter(FOODS.values()))
            raise StoryError(explain_combo(food, THREATS[args.threat], TOOLS[args.tool]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.food is None or combo[0] == args.food)
        and (args.threat is None or combo[1] == args.threat)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    food_id, threat_id, tool_id = rng.choice(sorted(combos))
    hero_id = args.hero or rng.choice(sorted(HEROES))
    symbol_id = args.symbol or rng.choice(sorted(SYMBOLS))
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        hero=hero_id,
        food=food_id,
        threat=threat_id,
        tool=tool_id,
        symbol=symbol_id,
        elder_name=elder_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero: {params.hero})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.threat not in THREATS:
        raise StoryError(f"(Unknown threat: {params.threat})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.symbol not in SYMBOLS:
        raise StoryError(f"(Unknown symbol: {params.symbol})")
    if params.elder_name not in ELDER_NAMES:
        raise StoryError(f"(Unknown elder name: {params.elder_name})")

    food = FOODS[params.food]
    threat = THREATS[params.threat]
    tool = TOOLS[params.tool]
    if not hazard_at_risk(food, threat):
        raise StoryError(explain_combo(food, threat))
    if not tool_fits(tool, threat):
        raise StoryError(explain_combo(food, threat, tool))

    world = tell(
        hero_spec=HEROES[params.hero],
        food_spec=food,
        threat_spec=threat,
        tool_spec=tool,
        symbol_spec=SYMBOLS[params.symbol],
        elder_name=params.elder_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (food, threat, tool) combos:\n")
        for food_id, threat_id, tool_id in combos:
            print(f"  {food_id:8} {threat_id:10} {tool_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.food} / {p.threat} / {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
