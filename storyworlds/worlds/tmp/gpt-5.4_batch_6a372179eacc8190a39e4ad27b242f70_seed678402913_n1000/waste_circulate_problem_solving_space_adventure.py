#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py
==============================================================================

A standalone storyworld for a small space-adventure problem-solving tale.

Premise:
    Two children are visiting or helping on a small spaceship or moon base.
    Their pretend mission is interrupted when loose waste clogs a fan or air
    tube, so fresh air cannot circulate well. They must notice the problem,
    choose a sensible tool, clean up the right kind of waste, and restore the
    air flow. The story ends by showing a tidier, safer system and a calmer
    crew.

The world model keeps both physical meters (blocked air, mess, fixed flow) and
emotional memes (worry, pride, teamwork). Prose comes from the simulated state,
not from a frozen template with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py
    python storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py --place ship --waste wrappers --blockage vent
    python storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py --waste juice_box --tool grabber
    python storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/waste_circulate_problem_solving_space_adventure.py --qa --json
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman", "captain_female"}
        male = {"boy", "father", "man", "captain_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "captain_female": "captain",
            "captain_male": "captain",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    scene: str
    route: str
    window: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    pretend: str
    goal: str
    exclaim: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Waste:
    id: str
    label: str
    phrase: str
    plural: bool
    container: str
    material: str
    flexible: bool
    compostable: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Blockage:
    id: str
    label: str
    phrase: str
    opening: str
    airflow_phrase: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
    sense: int
    handles_flexible: bool
    handles_rigid: bool
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SortBin:
    id: str
    label: str
    phrase: str
    accepts: set[str]
    lesson: str
    tags: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_low_air(world: World) -> list[str]:
    out: list[str] = []
    air = world.get("air")
    clog = world.get("clog")
    if clog.meters["stuck"] >= THRESHOLD and air.meters["circulating"] <= 0:
        sig = ("low_air",)
        if sig not in world.fired:
            world.fired.add(sig)
            for ch in world.characters():
                ch.memes["worry"] += 1
            out.append("__low_air__")
    return out


def _r_restore_air(world: World) -> list[str]:
    out: list[str] = []
    air = world.get("air")
    clog = world.get("clog")
    if clog.meters["stuck"] <= 0 and air.meters["circulating"] >= THRESHOLD:
        sig = ("restored_air",)
        if sig not in world.fired:
            world.fired.add(sig)
            for ch in world.characters():
                ch.memes["relief"] += 1
                ch.memes["pride"] += 1
            out.append("__restored_air__")
    return out


CAUSAL_RULES = [
    Rule(name="low_air", tag="physical", apply=_r_low_air),
    Rule(name="restore_air", tag="physical", apply=_r_restore_air),
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
        for s in produced:
            world.say(s)
    return produced


def tool_can_handle(tool: Tool, waste: Waste) -> bool:
    if waste.flexible:
        return tool.handles_flexible
    return tool.handles_rigid


def choose_bin_for(waste: Waste) -> Optional[SortBin]:
    for bin_cfg in BINS.values():
        if waste.material in bin_cfg.accepts:
            return bin_cfg
    return None


def valid_combo(place_id: str, waste_id: str, blockage_id: str, tool_id: str) -> bool:
    waste = WASTES[waste_id]
    blockage = BLOCKAGES[blockage_id]
    tool = TOOLS[tool_id]
    return tool.sense >= SENSE_MIN and tool.safe and tool_can_handle(tool, waste) and blockage.severity >= 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for waste_id in WASTES:
            for blockage_id in BLOCKAGES:
                for tool_id in TOOLS:
                    if valid_combo(place_id, waste_id, blockage_id, tool_id):
                        combos.append((place_id, waste_id, blockage_id, tool_id))
    return combos


def explain_tool_rejection(tool: Tool, waste: Waste) -> str:
    if tool.sense < SENSE_MIN or not tool.safe:
        return (
            f"(No story: {tool.phrase} is not a sensible, safe repair tool here. "
            f"Pick a careful tool like the soft grabber, the small net, or the magnetic picker.)"
        )
    if waste.flexible and not tool.handles_flexible:
        return (
            f"(No story: {tool.label} would not catch {waste.label} well enough to pull it free. "
            f"Pick a tool that can lift soft, floppy waste.)"
        )
    if (not waste.flexible) and not tool.handles_rigid:
        return (
            f"(No story: {tool.label} is poor at lifting a rigid piece like {waste.label}. "
            f"Pick a tool that can grip or attract a firm object.)"
        )
    return "(No story: this tool does not fit the repair.)"


def predict_fix(world: World, waste: Waste, tool: Tool) -> dict:
    sim = world.copy()
    _do_repair(sim, waste, tool, narrate=False)
    return {
        "cleared": sim.get("clog").meters["stuck"] <= 0,
        "circulating": sim.get("air").meters["circulating"] >= THRESHOLD,
    }


def _do_repair(world: World, waste: Waste, tool: Tool, narrate: bool = True) -> None:
    clog = world.get("clog")
    air = world.get("air")
    if not tool_can_handle(tool, waste):
        return
    clog.meters["stuck"] = 0.0
    clog.meters["removed"] += 1
    air.meters["circulating"] = 1.0
    world.get("bay").meters["tidy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, kid1: Entity, kid2: Entity, captain: Entity, place: Place, mission: Mission) -> None:
    for kid in (kid1, kid2):
        kid.memes["joy"] += 1
    world.say(
        f"{kid1.id} and {kid2.id} were helping {captain.label_word} on {place.scene}. "
        f"Outside {place.window}, stars looked like cold silver sprinkles."
    )
    world.say(
        f"They pretended they were {mission.pretend}. "
        f'"{mission.exclaim}" {kid1.id} said. "Let\'s {mission.goal}."'
    )
    world.say(place.route)


def problem_appears(world: World, kid2: Entity, waste: Waste, blockage: Blockage) -> None:
    clog = world.get("clog")
    air = world.get("air")
    clog.meters["stuck"] = 1.0
    clog.meters["severity"] = float(blockage.severity)
    air.meters["circulating"] = 0.0
    air.meters["stale"] += 1
    world.get("bay").meters["mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {kid2.id} heard a funny sputter. Near {blockage.opening}, "
        f"{waste.phrase} had slipped where it did not belong."
    )
    world.say(
        f"The little air system could not circulate properly anymore, and {blockage.airflow_phrase}."
    )


def inspect(world: World, kid1: Entity, kid2: Entity, captain: Entity, waste: Waste, blockage: Blockage, tool: Tool) -> None:
    pred = predict_fix(world, waste, tool)
    world.facts["predicted_clear"] = pred["cleared"]
    world.facts["predicted_circulating"] = pred["circulating"]
    kid1.memes["focus"] += 1
    kid2.memes["focus"] += 1
    world.say(
        f'{captain.label_word.capitalize()} knelt beside them. "{blockage.phrase} is blocked," '
        f'{captain.pronoun()} said. "We need to think, not panic."'
    )
    world.say(
        f"{kid1.id} pointed at the waste and {kid2.id} fetched {tool.phrase}. "
        f"They studied the gap, the shape of the {waste.label}, and how to pull it out without pushing it deeper."
    )


def repair(world: World, kid1: Entity, kid2: Entity, waste: Waste, blockage: Blockage, tool: Tool) -> None:
    _do_repair(world, waste, tool, narrate=False)
    for kid in (kid1, kid2):
        kid.memes["teamwork"] += 1
    world.say(
        f"{kid1.id} held the light steady while {kid2.id} used {tool.phrase}. "
        f"{tool.use_text} around the {waste.label}, and together they eased it out of {blockage.phrase}."
    )
    world.say(
        f"At once the fan gave a smooth hum, and clean air began to circulate through the little cabin again."
    )


def sort_and_learn(world: World, captain: Entity, kid1: Entity, kid2: Entity, waste: Waste, bin_cfg: SortBin) -> None:
    world.get("clog").meters["sorted"] += 1
    world.get("bay").meters["sorted"] += 1
    for kid in (kid1, kid2):
        kid.memes["lesson"] += 1
    world.say(
        f'{captain.label_word.capitalize()} opened {bin_cfg.phrase}. "{bin_cfg.lesson}" {captain.pronoun()} said.'
    )
    world.say(
        f"They dropped {waste.it()} into the {bin_cfg.label} so loose waste would not float back and cause trouble again."
    )


def ending(world: World, kid1: Entity, kid2: Entity, mission: Mission, place: Place) -> None:
    for kid in (kid1, kid2):
        kid.memes["joy"] += 1
    world.say(
        f"The room felt cooler and easier to breathe in. Nothing rattled now except a happy, steady purr from the vents."
    )
    world.say(
        f"{kid2.id} grinned at {kid1.id}. {mission.ending} On {place.scene}, even a small clean-up felt like a brave space victory."
    )


def tell(
    place: Place,
    mission: Mission,
    waste: Waste,
    blockage: Blockage,
    tool: Tool,
    kid1_name: str,
    kid1_gender: str,
    kid2_name: str,
    kid2_gender: str,
    captain_type: str,
) -> World:
    world = World()
    kid1 = world.add(Entity(id=kid1_name, kind="character", type=kid1_gender, role="solver"))
    kid2 = world.add(Entity(id=kid2_name, kind="character", type=kid2_gender, role="helper"))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, role="captain", label="the captain"))
    world.add(Entity(id="air", type="system", label="air loop"))
    world.add(Entity(id="clog", type="blockage", label=blockage.label))
    world.add(Entity(id="bay", type="room", label="cabin"))
    world.facts["captain"] = captain

    introduce(world, kid1, kid2, captain, place, mission)
    world.para()
    problem_appears(world, kid2, waste, blockage)
    inspect(world, kid1, kid2, captain, waste, blockage, tool)
    world.para()
    repair(world, kid1, kid2, waste, blockage, tool)
    bin_cfg = choose_bin_for(waste)
    if bin_cfg is not None:
        sort_and_learn(world, captain, kid1, kid2, waste, bin_cfg)
    world.para()
    ending(world, kid1, kid2, mission, place)

    world.facts.update(
        place=place,
        mission=mission,
        waste=waste,
        blockage=blockage,
        tool=tool,
        kid1=kid1,
        kid2=kid2,
        bin=bin_cfg,
        solved=world.get("air").meters["circulating"] >= THRESHOLD,
        sorted=world.get("clog").meters["sorted"] >= THRESHOLD,
    )
    return world


PLACES = {
    "ship": Place(
        id="ship",
        scene="a tiny training ship",
        route="The narrow hall curved past blinking panels and a round sleeping nook.",
        window="the ship's glass dome",
        tags={"space", "ship"},
    ),
    "station": Place(
        id="station",
        scene="a small moon station",
        route="A silver walkway led past plant trays, tool hooks, and one humming wall fan.",
        window="the moon window",
        tags={"space", "station"},
    ),
    "base": Place(
        id="base",
        scene="a bright crater base",
        route="The corridor had soft floor lights and a map of tunnels painted on one wall.",
        window="the thick lookout window",
        tags={"space", "base"},
    ),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        pretend="junior space rescuers",
        goal="check every air passage",
        exclaim="Space rescue team, ready",
        ending='"Air rescue complete," she said, and they gave each other a tiny moon-hop cheer.',
        tags={"problem_solving", "space"},
    ),
    "explorers": Mission(
        id="explorers",
        pretend="planet explorers on a grand survey",
        goal="inspect the humming ship",
        exclaim="Explorers to the control deck",
        ending='"Mission fixed," he said, and they marched down the hall like proud explorers.',
        tags={"problem_solving", "space"},
    ),
    "engineers": Mission(
        id="engineers",
        pretend="young star engineers",
        goal="keep the base running smoothly",
        exclaim="Star engineers on duty",
        ending='"Systems smiling again," she whispered, and both children laughed.',
        tags={"problem_solving", "space"},
    ),
}

WASTES = {
    "wrappers": Waste(
        id="wrappers",
        label="snack wrappers",
        phrase="two shiny snack wrappers",
        plural=True,
        container="recycling drawer",
        material="plastic",
        flexible=True,
        tags={"waste", "recycling", "plastic"},
    ),
    "peel": Waste(
        id="peel",
        label="banana peel",
        phrase="a curly banana peel",
        plural=False,
        container="compost cup",
        material="food",
        flexible=True,
        compostable=True,
        tags={"waste", "compost", "food"},
    ),
    "juice_box": Waste(
        id="juice_box",
        label="juice box",
        phrase="a squished juice box",
        plural=False,
        container="recycling drawer",
        material="carton",
        flexible=False,
        tags={"waste", "recycling", "carton"},
    ),
    "bolt_cap": Waste(
        id="bolt_cap",
        label="metal bolt cap",
        phrase="a little metal bolt cap",
        plural=False,
        container="metal bin",
        material="metal",
        flexible=False,
        tags={"waste", "metal"},
    ),
}

BLOCKAGES = {
    "vent": Blockage(
        id="vent",
        label="vent",
        phrase="the vent grille",
        opening="the vent grille",
        airflow_phrase="the breeze by their cheeks faded to almost nothing",
        severity=1,
        tags={"air", "vent"},
    ),
    "fan": Blockage(
        id="fan",
        label="fan",
        phrase="the wall fan housing",
        opening="the wall fan housing",
        airflow_phrase="the fan only coughed and spun in slow little jerks",
        severity=2,
        tags={"air", "fan"},
    ),
    "tube": Blockage(
        id="tube",
        label="air tube",
        phrase="the clear air tube",
        opening="the clear air tube",
        airflow_phrase="the whoosh in the tube turned thin and whispery",
        severity=2,
        tags={"air", "tube"},
    ),
}

TOOLS = {
    "grabber": Tool(
        id="grabber",
        label="soft grabber",
        phrase="the soft grabber",
        use_text="The padded tips closed gently",
        sense=3,
        handles_flexible=True,
        handles_rigid=True,
        safe=True,
        tags={"tool", "grabber"},
    ),
    "net": Tool(
        id="net",
        label="small net",
        phrase="the small net",
        use_text="The fine net slipped neatly",
        sense=2,
        handles_flexible=True,
        handles_rigid=False,
        safe=True,
        tags={"tool", "net"},
    ),
    "magnet": Tool(
        id="magnet",
        label="magnetic picker",
        phrase="the magnetic picker",
        use_text="The magnetic tip clicked into place",
        sense=2,
        handles_flexible=False,
        handles_rigid=True,
        safe=True,
        tags={"tool", "magnet", "metal"},
    ),
    "poke_stick": Tool(
        id="poke_stick",
        label="poking stick",
        phrase="the poking stick",
        use_text="They tried to nudge it",
        sense=1,
        handles_flexible=False,
        handles_rigid=False,
        safe=False,
        tags={"tool"},
    ),
}

BINS = {
    "recycling": SortBin(
        id="recycling",
        label="recycling drawer",
        phrase="the blue recycling drawer",
        accepts={"plastic", "carton", "metal"},
        lesson="Clean things can be recycled, so they become useful again",
        tags={"recycling"},
    ),
    "compost": SortBin(
        id="compost",
        label="compost cup",
        phrase="the green compost cup",
        accepts={"food"},
        lesson="Food scraps can go in compost, where they break down the right way",
        tags={"compost"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nora", "Ivy", "Ruby", "Tess"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Sam", "Noah", "Jude"]


@dataclass
class StoryParams:
    place: str
    mission: str
    waste: str
    blockage: str
    tool: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    captain: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "waste": [
        (
            "What does waste mean?",
            "Waste is stuff left over after you are done using it. It should be put in the right place so it does not make a mess or cause a problem.",
        )
    ],
    "circulate": [
        (
            "What does it mean when air can circulate?",
            "It means air can move around from place to place. Moving air helps a room feel fresh and comfortable.",
        )
    ],
    "recycling": [
        (
            "What is recycling?",
            "Recycling is when used things like some cans, cartons, or plastic are collected and made into new things. It helps keep useful material out of the trash.",
        )
    ],
    "compost": [
        (
            "What is compost?",
            "Compost is made from food scraps and plant bits that break down over time. People can use it to help soil grow plants.",
        )
    ],
    "vent": [
        (
            "What does a vent do?",
            "A vent is an opening that lets air move in or out. If it gets blocked, air cannot circulate as well.",
        )
    ],
    "fan": [
        (
            "What does a fan do?",
            "A fan moves air around. That helps a room feel cooler and fresher.",
        )
    ],
    "tube": [
        (
            "What is an air tube?",
            "An air tube carries air from one place to another. If something gets stuck inside, the air flow can slow down.",
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking carefully, and trying a good fix. It is not just guessing fast.",
        )
    ],
    "space": [
        (
            "Why do space stations and ships need clean air systems?",
            "People in space live inside closed rooms, so the air system has to keep moving air around. A blocked system can make the air feel stale and stuffy.",
        )
    ],
    "metal": [
        (
            "Why does a magnet pick up some metal things?",
            "Some kinds of metal are pulled by magnets. That can make a magnetic tool useful for lifting a small metal piece.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "waste",
    "circulate",
    "problem_solving",
    "space",
    "recycling",
    "compost",
    "vent",
    "fan",
    "tube",
    "metal",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    place = f["place"]
    waste = f["waste"]
    blockage = f["blockage"]
    return [
        (
            f'Write a short space adventure for a 3-to-5-year-old that includes the words '
            f'"waste" and "circulate" and ends with a tidy fix.'
        ),
        (
            f"Tell a gentle problem-solving story where {kid1.id} and {kid2.id} discover that "
            f"{waste.label} is blocking {blockage.phrase} on {place.scene}."
        ),
        (
            f"Write a child-facing story about a small air-flow problem in space, where careful thinking "
            f"and clean-up save the day instead of rushing."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    captain = f["captain"]
    waste = f["waste"]
    blockage = f["blockage"]
    tool = f["tool"]
    bin_cfg = f.get("bin")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid1.id} and {kid2.id}, two children on a small space adventure, and the captain who helped them think carefully.",
        ),
        (
            "What problem did they find?",
            f"They found that {waste.phrase} was blocking {blockage.phrase}, so the air could not circulate well. That made the room feel wrong and gave them a real problem to solve.",
        ),
        (
            "Why did they stop and think before acting?",
            f"They needed to pull the waste out without pushing it deeper into the air system. Thinking first helped them choose a tool that fit the shape of the stuck piece.",
        ),
        (
            f"How did {kid1.id} and {kid2.id} fix the problem?",
            f"They worked together with {tool.phrase} and carefully pulled the {waste.label} free. Once the blockage was gone, clean air began to circulate through the cabin again.",
        ),
    ]
    if bin_cfg is not None:
        qa.append(
            (
                "What did they do with the waste after they removed it?",
                f"They put it into the {bin_cfg.label} instead of leaving it loose. That mattered because loose waste could float back and block the air system again.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the room feeling fresh again and the children feeling proud. The smooth hum of the vents showed that their careful fix had really worked.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"waste", "circulate", "problem_solving", "space"}
    tags |= set(f["waste"].tags)
    tags |= set(f["blockage"].tags)
    tags |= set(f["mission"].tags)
    tags |= set(f["tool"].tags)
    if f.get("bin") is not None:
        tags |= set(f["bin"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="ship",
        mission="rescue",
        waste="wrappers",
        blockage="vent",
        tool="grabber",
        kid1="Luna",
        kid1_gender="girl",
        kid2="Max",
        kid2_gender="boy",
        captain="captain_female",
    ),
    StoryParams(
        place="station",
        mission="engineers",
        waste="juice_box",
        blockage="fan",
        tool="grabber",
        kid1="Theo",
        kid1_gender="boy",
        kid2="Mia",
        kid2_gender="girl",
        captain="captain_male",
    ),
    StoryParams(
        place="base",
        mission="explorers",
        waste="bolt_cap",
        blockage="tube",
        tool="magnet",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Finn",
        kid2_gender="boy",
        captain="captain_female",
    ),
    StoryParams(
        place="station",
        mission="rescue",
        waste="peel",
        blockage="vent",
        tool="net",
        kid1="Ava",
        kid1_gender="girl",
        kid2="Leo",
        kid2_gender="boy",
        captain="captain_male",
    ),
]


ASP_RULES = r"""
valid_combo(P,W,B,T) :- place(P), waste(W), blockage(B), tool(T),
                        sensible(T), safe(T), fits(T,W), severe(B).

fits(T,W) :- flexible(W), handles_flexible(T).
fits(T,W) :- rigid(W), handles_rigid(T).
severe(B) :- blockage(B), severity(B,S), S >= 1.

% Pick sorting destination from the waste material.
sorted_into(W,recycling) :- material(W,plastic).
sorted_into(W,recycling) :- material(W,carton).
sorted_into(W,recycling) :- material(W,metal).
sorted_into(W,compost)   :- material(W,food).

#show valid_combo/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for wid, waste in WASTES.items():
        lines.append(asp.fact("waste", wid))
        lines.append(asp.fact("material", wid, waste.material))
        if waste.flexible:
            lines.append(asp.fact("flexible", wid))
        else:
            lines.append(asp.fact("rigid", wid))
    for bid, blockage in BLOCKAGES.items():
        lines.append(asp.fact("blockage", bid))
        lines.append(asp.fact("severity", bid, blockage.severity))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sense", tid, tool.sense))
        if tool.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", tid))
        if tool.safe:
            lines.append(asp.fact("safe", tid))
        if tool.handles_flexible:
            lines.append(asp.fact("handles_flexible", tid))
        if tool.handles_rigid:
            lines.append(asp.fact("handles_rigid", tid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_combo/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: children solve an air-circulation waste problem on a small space adventure."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--waste", choices=WASTES)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--captain", choices=["captain_female", "captain_male"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [name for name in names if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.waste:
        tool = TOOLS[args.tool]
        waste = WASTES[args.waste]
        if not valid_combo(
            place_id=args.place or next(iter(PLACES)),
            waste_id=args.waste,
            blockage_id=args.blockage or next(iter(BLOCKAGES)),
            tool_id=args.tool,
        ):
            raise StoryError(explain_tool_rejection(tool, waste))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.waste is None or combo[1] == args.waste)
        and (args.blockage is None or combo[2] == args.blockage)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, waste, blockage, tool = rng.choice(sorted(combos))
    mission = args.mission or rng.choice(sorted(MISSIONS))
    captain = args.captain or rng.choice(["captain_female", "captain_male"])
    kid1, kid1_gender = _pick_kid(rng)
    kid2, kid2_gender = _pick_kid(rng, avoid=kid1)
    return StoryParams(
        place=place,
        mission=mission,
        waste=waste,
        blockage=blockage,
        tool=tool,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        captain=captain,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.waste not in WASTES:
        raise StoryError(f"(Unknown waste: {params.waste})")
    if params.blockage not in BLOCKAGES:
        raise StoryError(f"(Unknown blockage: {params.blockage})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.captain not in {"captain_female", "captain_male"}:
        raise StoryError(f"(Unknown captain type: {params.captain})")
    if not valid_combo(params.place, params.waste, params.blockage, params.tool):
        raise StoryError(explain_tool_rejection(TOOLS[params.tool], WASTES[params.waste]))

    world = tell(
        place=PLACES[params.place],
        mission=MISSIONS[params.mission],
        waste=WASTES[params.waste],
        blockage=BLOCKAGES[params.blockage],
        tool=TOOLS[params.tool],
        kid1_name=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2_name=params.kid2,
        kid2_gender=params.kid2_gender,
        captain_type=params.captain,
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
        print(asp_program("#show valid_combo/4.\n#show sorted_into/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, waste, blockage, tool) combos:\n")
        for place, waste, blockage, tool in combos:
            print(f"  {place:8} {waste:10} {blockage:8} {tool}")
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
            header = f"### {p.kid1} & {p.kid2}: {p.waste} in {p.blockage} at {p.place} ({p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
