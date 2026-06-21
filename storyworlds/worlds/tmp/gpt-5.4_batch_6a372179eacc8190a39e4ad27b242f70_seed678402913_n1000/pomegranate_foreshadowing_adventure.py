#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pomegranate_foreshadowing_adventure.py
=================================================================

A small storyworld about a child going on a little adventure with a
pomegranate in a satchel. The fruit creates an early warning image that
foreshadows the real obstacle ahead, and the child succeeds by remembering the
clue and using the right tool.

The world prefers tight, reasoned combinations:
- the place must actually contain the chosen obstacle,
- the pomegranate omen must genuinely foreshadow that obstacle,
- the chosen tool must really help with that obstacle.

Run it
------
    python storyworlds/worlds/gpt-5.4/pomegranate_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/pomegranate_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/pomegranate_foreshadowing_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/pomegranate_foreshadowing_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/pomegranate_foreshadowing_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    goals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    severity: int
    threat: str
    solved_by: str
    memory_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    label: str
    phrase: str
    foreshadows: str
    image: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    handles: str
    safety: int
    use_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_danger_stirs_fear(world: World) -> list[str]:
    hero = world.entities.get("hero")
    trail = world.entities.get("trail")
    if hero is None or trail is None:
        return []
    if trail.meters["danger"] < THRESHOLD:
        return []
    sig = ("fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return []


def _r_progress_brings_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    trail = world.entities.get("trail")
    if hero is None or trail is None:
        return []
    if trail.meters["open"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["confidence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="danger_stirs_fear", tag="emotion", apply=_r_danger_stirs_fear),
    Rule(name="progress_brings_relief", tag="emotion", apply=_r_progress_brings_relief),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def omen_matches_hazard(omen: Omen, hazard: Hazard) -> bool:
    return omen.foreshadows == hazard.id


def tool_fits_hazard(tool: Tool, hazard: Hazard) -> bool:
    return tool.handles == hazard.id


def place_supports(place: Place, hazard: Hazard, goal: Goal) -> bool:
    return hazard.id in place.affords and goal.id in place.goals


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for hazard_id, hazard in HAZARDS.items():
            for omen_id, omen in OMENS.items():
                for tool_id, tool in TOOLS.items():
                    for goal_id, goal in GOALS.items():
                        if (
                            place_supports(place, hazard, goal)
                            and omen_matches_hazard(omen, hazard)
                            and tool_fits_hazard(tool, hazard)
                        ):
                            combos.append((place_id, hazard_id, omen_id, tool_id, goal_id))
    return combos


def haste_bonus(pace: str) -> int:
    return {"careful": 0, "eager": 1}[pace]


def outcome_of(params: "StoryParams") -> str:
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    risk = hazard.severity + haste_bonus(params.pace)
    return "smooth" if tool.safety >= risk else "close_call"


def predict_obstacle(world: World, hazard: Hazard, tool: Tool, pace: str) -> dict:
    sim = world.copy()
    trail = sim.get("trail")
    trail.meters["danger"] += hazard.severity
    propagate(sim)
    risk = hazard.severity + haste_bonus(pace)
    return {
        "danger": trail.meters["danger"],
        "fear": sim.get("hero").memes["fear"],
        "safe": tool.safety >= risk,
    }


def introduce(world: World, hero: Entity, elder: Entity, place: Place, goal: Goal) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"At the edge of {place.phrase}, {hero.id} felt as if the whole morning were asking for an adventure."
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled and pointed toward {goal.phrase}. "
        f'"If you can reach it before the sun climbs too high," {elder.pronoun()} said, '
        f'"bring back its story for me."'
    )


def equip(world: World, hero: Entity, tool: Tool) -> None:
    hero.meters["prepared"] += 1
    world.say(
        f"{hero.id} tucked a pomegranate into a satchel, slipped {tool.phrase} into one hand, "
        f"and set off along the winding path."
    )


def show_omen(world: World, hero: Entity, omen: Omen) -> None:
    hero.memes["caution"] += 1
    world.say(omen.image)
    world.say(
        f"{hero.id} paused. {omen.warning} It felt like a small warning laid quietly at the start of the trail."
    )


def approach(world: World, hero: Entity, place: Place, pace: str) -> None:
    hero.memes["bravery"] += 1
    if pace == "eager":
        world.say(
            f"{hero.id} hurried through {place.label}, boots tapping fast, because adventures always seemed brighter when taken at a run."
        )
    else:
        world.say(
            f"{hero.id} moved carefully through {place.label}, watching the bends in the path the way explorers do in good stories."
        )


def encounter(world: World, hero: Entity, hazard: Hazard) -> None:
    trail = world.get("trail")
    trail.meters["danger"] += hazard.severity
    trail.meters["blocked"] += 1
    propagate(world)
    world.say(
        f"A little farther on, the path stopped being easy. {hazard.phrase} waited ahead, and {hazard.threat}."
    )


def remember(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["insight"] += 1
    world.say(
        f"Then {hero.id} remembered the pomegranate: {hazard.memory_line}"
    )


def use_tool(world: World, hero: Entity, tool: Tool, hazard: Hazard, close_call: bool) -> None:
    trail = world.get("trail")
    if close_call:
        hero.meters["scrape"] += 1
        hero.memes["fear"] += 1
        world.say(
            f"{hero.id} took one quick step too boldly and felt the danger jump close. "
            f"For a second, the adventure seemed much bigger than one child."
        )
    world.say(tool.use_line)
    trail.meters["danger"] = 0.0
    trail.meters["blocked"] = 0.0
    trail.meters["open"] += 1
    hero.meters["progress"] += 1
    propagate(world)


def reach_goal(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Soon the way opened, and {hero.id} reached {goal.phrase}. {goal.ending}"
    )


def ending(world: World, hero: Entity, elder: Entity, outcome: str) -> None:
    if outcome == "close_call":
        world.say(
            f"When {hero.id} came back, {elder.label_word} noticed the shaky breath first and the grin second."
        )
        world.say(
            f'Together they opened the pomegranate, and the ruby seeds looked less like a warning now and more like brave little lanterns. '
            f'{hero.id} told the whole story, including the moment of fright, and knew why clues matter on an adventure.'
        )
    else:
        world.say(
            f"When {hero.id} came back, {elder.label_word} split open the pomegranate for a trail feast."
        )
        world.say(
            f"The ruby seeds shone in their palms like tiny treasure beads, and {hero.id} knew the adventure had gone well because the ending felt calm, bright, and earned."
        )


def tell(
    place: Place,
    hazard: Hazard,
    omen: Omen,
    tool: Tool,
    goal: Goal,
    *,
    hero_name: str,
    hero_gender: str,
    elder_type: str,
    pace: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    fruit = world.add(Entity(id="fruit", type="fruit", label="pomegranate", phrase="a heavy pomegranate", tags={"pomegranate"}))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    trail = world.add(Entity(id="trail", type="trail", label="path", phrase="the path"))

    world.facts["hero_name"] = hero_name

    introduce(world, hero, elder, place, goal)
    equip(world, hero, tool)
    world.para()
    show_omen(world, hero, omen)
    approach(world, hero, place, pace)
    pred = predict_obstacle(world, hazard, tool, pace)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_safe"] = pred["safe"]
    world.para()
    encounter(world, hero, hazard)
    remember(world, hero, hazard)
    out = outcome_of(
        StoryParams(
            place=place.id,
            hazard=hazard.id,
            omen=omen.id,
            tool=tool.id,
            goal=goal.id,
            name=hero_name,
            gender=hero_gender,
            elder=elder_type,
            pace=pace,
            seed=None,
        )
    )
    use_tool(world, hero, tool, hazard, close_call=(out == "close_call"))
    world.para()
    reach_goal(world, hero, goal)
    ending(world, hero, elder, out)

    world.facts.update(
        place=place,
        hazard=hazard,
        omen=omen,
        tool_cfg=tool,
        goal=goal,
        hero=hero,
        elder=elder,
        fruit=fruit,
        tool=tool_ent,
        outcome=out,
        close_call=(out == "close_call"),
        smooth=(out == "smooth"),
        pomegranate_used=True,
        remembered=hero.memes["insight"] >= THRESHOLD,
    )
    return world


PLACES = {
    "orchard": Place(
        id="orchard",
        label="the old orchard",
        phrase="the old orchard behind the stone wall",
        affords={"loose_stones", "thorn_gate"},
        goals={"bell", "lookout"},
        tags={"orchard"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the ruined courtyard",
        phrase="the ruined courtyard where ivy climbed the arches",
        affords={"dark_tunnel", "thorn_gate"},
        goals={"fountain", "bell"},
        tags={"ruins"},
    ),
    "hillside": Place(
        id="hillside",
        label="the sunny hillside path",
        phrase="the sunny hillside path above the village",
        affords={"loose_stones", "dark_tunnel"},
        goals={"lookout"},
        tags={"hill"},
    ),
}

HAZARDS = {
    "loose_stones": Hazard(
        id="loose_stones",
        label="loose stones",
        phrase="a ribbon of loose stones slanting down the path",
        severity=1,
        threat="one careless step could send small rocks skittering underfoot",
        solved_by="walking_stick",
        memory_line="the rolling seeds had looked just like these restless stones, eager to slide away from a hasty foot.",
        tags={"stones", "path"},
    ),
    "thorn_gate": Hazard(
        id="thorn_gate",
        label="thorn gate",
        phrase="a thorny arch where wild branches had knitted themselves across the trail",
        severity=1,
        threat="the hooked stems tugged at sleeves and waited to scratch bare hands",
        solved_by="gloves",
        memory_line="the fruit's little crown had caught on a twig earlier, and now the whole path seemed to repeat that warning in a larger voice.",
        tags={"thorns", "path"},
    ),
    "dark_tunnel": Hazard(
        id="dark_tunnel",
        label="dark tunnel",
        phrase="a low tunnel under fallen stone where the daylight thinned into shadow",
        severity=2,
        threat="the floor vanished into dimness, and hidden dips could twist an ankle",
        solved_by="lantern",
        memory_line="the hollow heart of the pomegranate had seemed darker than the sunny skin around it, just like this passage with its secret middle.",
        tags={"dark", "tunnel"},
    ),
}

OMENS = {
    "rolling_seeds": Omen(
        id="rolling_seeds",
        label="rolling seeds",
        phrase="rolling seeds",
        foreshadows="loose_stones",
        image="At the first bend, the satchel tipped, and a few ruby pomegranate seeds spilled from a crack in the skin and rolled over the flat ground like tiny red marbles.",
        warning="They moved faster than they looked, slipping wherever the earth tilted",
        tags={"pomegranate", "foreshadowing", "stones"},
    ),
    "snagged_crown": Omen(
        id="snagged_crown",
        label="snagged crown",
        phrase="snagged crown",
        foreshadows="thorn_gate",
        image="Near a hedge, the little crown at the top of the pomegranate snagged on a dry twig, and the satchel gave a sharp, scratchy tug.",
        warning="Anything with hooks, even a small thing, could hold tight when you were not paying attention",
        tags={"pomegranate", "foreshadowing", "thorns"},
    ),
    "shadow_cup": Omen(
        id="shadow_cup",
        label="shadow cup",
        phrase="shadow cup",
        foreshadows="dark_tunnel",
        image="When sunlight touched the cracked top of the pomegranate, the dark cup inside looked deeper than the fruit itself, like a tiny cave hiding in a round red shell.",
        warning="A bright outside can still hide a shadowed middle",
        tags={"pomegranate", "foreshadowing", "dark"},
    ),
}

TOOLS = {
    "walking_stick": Tool(
        id="walking_stick",
        label="walking stick",
        phrase="a smooth walking stick",
        handles="loose_stones",
        safety=2,
        use_line="Planting the walking stick before each step, the child tested the shifting ground and crossed without letting the stones race away.",
        qa_line="used the walking stick to test each step on the sliding stones",
        tags={"walking_stick", "balance"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of garden gloves",
        handles="thorn_gate",
        safety=2,
        use_line="With the garden gloves on, the child parted the thorny branches slowly and found the narrow, safe opening hidden inside them.",
        qa_line="pulled on the gloves and opened a safe gap through the thorns",
        tags={"gloves", "thorns"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        handles="dark_tunnel",
        safety=3,
        use_line="The brass lantern lit the floor ahead step by step, turning the dark tunnel from a guess into a path the child could truly see.",
        qa_line="lit the lantern so the hidden dips and stones could be seen",
        tags={"lantern", "light"},
    ),
}

GOALS = {
    "bell": Goal(
        id="bell",
        label="bell",
        phrase="the little copper bell hanging from the cedar arch",
        ending="It gave one clear ring that skipped across the garden like a silver bird.",
        tags={"bell"},
    ),
    "fountain": Goal(
        id="fountain",
        label="fountain",
        phrase="the sleeping fountain in the middle court",
        ending="A thin thread of water still sang there, as if the place had been waiting all morning to be found.",
        tags={"fountain"},
    ),
    "lookout": Goal(
        id="lookout",
        label="lookout",
        phrase="the round lookout stone above the last rise",
        ending="From there the whole valley opened like a map, and the roofs below looked small enough to fit in a pocket.",
        tags={"lookout"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Asha", "Pia", "Zoe"]
BOY_NAMES = ["Arlo", "Milo", "Finn", "Leo", "Tobin", "Nico", "Eli"]
PACES = ["careful", "eager"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    omen: str
    tool: str
    goal: str
    name: str
    gender: str
    elder: str
    pace: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="orchard",
        hazard="thorn_gate",
        omen="snagged_crown",
        tool="gloves",
        goal="bell",
        name="Lina",
        gender="girl",
        elder="grandmother",
        pace="careful",
        seed=None,
    ),
    StoryParams(
        place="hillside",
        hazard="loose_stones",
        omen="rolling_seeds",
        tool="walking_stick",
        goal="lookout",
        name="Arlo",
        gender="boy",
        elder="grandfather",
        pace="eager",
        seed=None,
    ),
    StoryParams(
        place="courtyard",
        hazard="dark_tunnel",
        omen="shadow_cup",
        tool="lantern",
        goal="fountain",
        name="Mira",
        gender="girl",
        elder="grandmother",
        pace="careful",
        seed=None,
    ),
    StoryParams(
        place="courtyard",
        hazard="thorn_gate",
        omen="snagged_crown",
        tool="gloves",
        goal="bell",
        name="Finn",
        gender="boy",
        elder="grandfather",
        pace="eager",
        seed=None,
    ),
]


KNOWLEDGE = {
    "pomegranate": [
        (
            "What is a pomegranate?",
            "A pomegranate is a round fruit with a thick skin and many juicy red seeds inside. People break it open to eat the seeds."
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small early clue that hints at something important later. It helps the ending feel surprising and sensible at the same time."
        )
    ],
    "thorns": [
        (
            "Why can thorns be a problem on a path?",
            "Thorns are sharp points on some plants, so they can scratch skin and catch on clothes. That is why people move slowly around them or wear protection."
        )
    ],
    "stones": [
        (
            "Why are loose stones tricky to walk on?",
            "Loose stones can roll under your feet, so you may slip if you step too fast. Careful steps and good balance make them safer."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern makes light, so you can see where you are going in a dark place. Seeing the ground clearly helps you avoid hidden holes and bumps."
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorny plants?",
            "Gloves cover your hands, so sharp thorns are less likely to scratch you. They let you hold rough branches more safely."
        )
    ],
    "walking_stick": [
        (
            "Why might a walking stick help on a rough trail?",
            "A walking stick can test the ground before you put your full weight down. It also helps you keep your balance."
        )
    ],
}
KNOWLEDGE_ORDER = ["pomegranate", "foreshadowing", "thorns", "stones", "lantern", "gloves", "walking_stick"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    goal = f["goal"]
    hazard = f["hazard"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "pomegranate" and uses foreshadowing.',
        f"Tell a gentle adventure about a {hero.type} named {f['hero_name']} crossing {place.label} to reach {goal.label}, where an early pomegranate clue hints at {hazard.label}.",
        "Write a story where a child notices a small warning early, remembers it later, and finishes the adventure in a calm, satisfying way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    hazard = f["hazard"]
    omen = f["omen"]
    tool = f["tool_cfg"]
    goal = f["goal"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child on a little adventure, and {elder.label_word} who sends {hero.pronoun('object')} to bring back a story. The trip feels special because it is both a quest and a lesson in paying attention."
        ),
        (
            "What clue came early in the story?",
            f"The early clue was the pomegranate omen: {omen.warning.lower()}. That moment mattered because it quietly hinted at the trouble waiting farther along the path."
        ),
        (
            f"What obstacle did {hero.label} meet?",
            f"{hero.label} came to {hazard.phrase}. It was dangerous because {hazard.threat}."
        ),
        (
            f"How did {hero.label} get past it?",
            f"{hero.label} {tool.qa_line}. The child could do that because the pomegranate clue helped {hero.pronoun('object')} understand what kind of danger was ahead."
        ),
    ]
    if f["close_call"]:
        qa.append(
            (
                f"Was the adventure easy the whole time?",
                f"No. {hero.label} rushed a little, and the danger came close before the tool solved the problem. That close call made the foreshadowing feel important instead of decorative."
            )
        )
    else:
        qa.append(
            (
                f"Why did the adventure go smoothly?",
                f"It went smoothly because {hero.label} noticed the early warning and moved with care. Remembering the clue turned the obstacle from a surprise into a problem {hero.pronoun()} was ready for."
            )
        )
    qa.append(
        (
            f"What happened at the end?",
            f"{hero.label} reached {goal.phrase} and then returned to {elder.label_word}. The pomegranate became a happy ending image instead of a warning because the adventure had been completed safely."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pomegranate", "foreshadowing"}
    hazard = world.facts["hazard"]
    tool = world.facts["tool_cfg"]
    if hazard.id == "thorn_gate":
        tags.add("thorns")
    if hazard.id == "loose_stones":
        tags.add("stones")
    if tool.id in KNOWLEDGE:
        tags.add(tool.id)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Optional[Place], hazard: Hazard, omen: Omen, tool: Tool, goal: Optional[Goal]) -> str:
    if place is not None and hazard.id not in place.affords:
        return (
            f"(No story: {place.label} does not contain {hazard.label}, so the child would have no honest obstacle to face there.)"
        )
    if goal is not None and place is not None and goal.id not in place.goals:
        return (
            f"(No story: {goal.label} does not belong in {place.label}, so the quest would not fit the place.)"
        )
    if not omen_matches_hazard(omen, hazard):
        return (
            f"(No story: the omen '{omen.label}' does not foreshadow {hazard.label}. Foreshadowing must point toward the later obstacle.)"
        )
    if not tool_fits_hazard(tool, hazard):
        return (
            f"(No story: {tool.label} does not solve {hazard.label}. The adventure needs a sensible method, not a decorative prop.)"
        )
    return "(No story: the chosen combination is unreasonable.)"


ASP_RULES = r"""
matches_omen(H, O) :- hazard(H), omen(O), foreshadows(O, H).
fits_tool(H, T)    :- hazard(H), tool(T), handles(T, H).
supports(P, H, G)  :- place(P), affords(P, H), hosts_goal(P, G).
valid(P, H, O, T, G) :- supports(P, H, G), matches_omen(H, O), fits_tool(H, T).

haste(0) :- chosen_pace(careful).
haste(1) :- chosen_pace(eager).
risk(V + B) :- chosen_hazard(H), severity(H, V), haste(B).
smooth :- chosen_tool(T), safety(T, S), risk(R), S >= R.
outcome(smooth) :- smooth.
outcome(close_call) :- not smooth.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, hazard_id))
        for goal_id in sorted(place.goals):
            lines.append(asp.fact("hosts_goal", place_id, goal_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("severity", hazard_id, hazard.severity))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("foreshadows", omen_id, omen.foreshadows))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("handles", tool_id, tool.handles))
        lines.append(asp.fact("safety", tool_id, tool.safety))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_pace", params.pace),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pomegranate omen foreshadows a small adventure obstacle."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--pace", choices=PACES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    hazard = HAZARDS.get(args.hazard) if args.hazard else None
    omen = OMENS.get(args.omen) if args.omen else None
    tool = TOOLS.get(args.tool) if args.tool else None
    goal = GOALS.get(args.goal) if args.goal else None

    if hazard and omen and not omen_matches_hazard(omen, hazard):
        raise StoryError(explain_rejection(place, hazard, omen, tool or next(iter(TOOLS.values())), goal))
    if hazard and tool and not tool_fits_hazard(tool, hazard):
        raise StoryError(explain_rejection(place, hazard, omen or next(iter(OMENS.values())), tool, goal))
    if place and hazard and hazard.id not in place.affords:
        raise StoryError(explain_rejection(place, hazard, omen or next(iter(OMENS.values())), tool or next(iter(TOOLS.values())), goal))
    if place and goal and goal.id not in place.goals:
        raise StoryError(explain_rejection(place, hazard or next(iter(HAZARDS.values())), omen or next(iter(OMENS.values())), tool or next(iter(TOOLS.values())), goal))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.omen is None or combo[2] == args.omen)
        and (args.tool is None or combo[3] == args.tool)
        and (args.goal is None or combo[4] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hazard_id, omen_id, tool_id, goal_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    pace = args.pace or rng.choice(PACES)
    return StoryParams(
        place=place_id,
        hazard=hazard_id,
        omen=omen_id,
        tool=tool_id,
        goal=goal_id,
        name=name,
        gender=gender,
        elder=elder,
        pace=pace,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        hazard = HAZARDS[params.hazard]
        omen = OMENS[params.omen]
        tool = TOOLS[params.tool]
        goal = GOALS[params.goal]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]!r})") from None

    if not place_supports(place, hazard, goal) or not omen_matches_hazard(omen, hazard) or not tool_fits_hazard(tool, hazard):
        raise StoryError(explain_rejection(place, hazard, omen, tool, goal))

    world = tell(
        place=place,
        hazard=hazard,
        omen=omen,
        tool=tool,
        goal=goal,
        hero_name=params.name,
        hero_gender=params.gender,
        elder_type=params.elder,
        pace=params.pace,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hazard, omen, tool, goal) combos:\n")
        for place, hazard, omen, tool, goal in combos:
            print(f"  {place:10} {hazard:13} {omen:14} {tool:13} {goal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.name}: {p.place}, {p.hazard}, {p.omen}, {p.tool}, {p.goal} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
