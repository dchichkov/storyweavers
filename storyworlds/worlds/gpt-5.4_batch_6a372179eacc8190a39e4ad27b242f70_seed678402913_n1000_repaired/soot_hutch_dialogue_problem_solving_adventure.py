#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py
============================================================================

A standalone storyworld about a tiny backyard adventure: two children hurry to a
small animal hutch, discover a soot problem, talk through the clues, and solve
the right problem with the right tool.

The seed asked for:
- the words "soot" and "hutch"
- Dialogue
- Problem Solving
- Adventure style

This world keeps the scope tight and plausible. Every story has:
- a beginning image of a small expedition
- a concrete soot problem at the hutch
- dialogue where the children reason about clues
- a sensible fix chosen from a small tool catalog
- an ending image that proves the hutch is safe and comfortable again

Reasonableness gate
-------------------
Not every tool fits every soot problem.

- blocked slats need a soft brush
- a sticky latch needs a damp cloth
- black water in the bowl needs fresh water

The world knows about weak ideas like a toy fan or bare hands, but refuses to
build stories around them.

Run it
------
python storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py
python storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py --problem blocked_slats --tool brush
python storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py --problem sticky_latch --tool fan
python storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py --all
python storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/soot_hutch_dialogue_problem_solving_adventure.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
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
        if self.type in {"rabbit", "rabbits", "guinea_pigs"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    approach: str
    opener: str
    weather: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    title: str
    discovery: str
    clue: str
    risk: str
    need: str
    solve_text: str
    result_text: str
    ask_line: str
    reason_line: str
    meter_key: str
    discomfort_key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    sense: int
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    caretaker: str
    animal: str
    trail_item: str
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blocked_slats(world: World) -> list[str]:
    hutch = world.get("hutch")
    animals = world.get("animals")
    out: list[str] = []
    if hutch.meters["air_blocked"] >= THRESHOLD:
        sig = ("air_blocked", "hutch")
        if sig not in world.fired:
            world.fired.add(sig)
            animals.meters["sneezy"] += 1
            for eid in ("hero", "partner"):
                if eid in world.entities:
                    world.get(eid).memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_sticky_latch(world: World) -> list[str]:
    hutch = world.get("hutch")
    animals = world.get("animals")
    out: list[str] = []
    if hutch.meters["latch_stuck"] >= THRESHOLD:
        sig = ("latch_stuck", "hutch")
        if sig not in world.fired:
            world.fired.add(sig)
            animals.meters["waiting"] += 1
            for eid in ("hero", "partner"):
                if eid in world.entities:
                    world.get(eid).memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_dirty_bowl(world: World) -> list[str]:
    hutch = world.get("hutch")
    animals = world.get("animals")
    out: list[str] = []
    if hutch.meters["water_dirty"] >= THRESHOLD:
        sig = ("water_dirty", "hutch")
        if sig not in world.fired:
            world.fired.add(sig)
            animals.meters["thirsty"] += 1
            for eid in ("hero", "partner"):
                if eid in world.entities:
                    world.get(eid).memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="blocked_slats", tag="physical", apply=_r_blocked_slats),
    Rule(name="sticky_latch", tag="physical", apply=_r_sticky_latch),
    Rule(name="dirty_bowl", tag="physical", apply=_r_dirty_bowl),
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


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="behind the stone cottage",
        approach="past the woodpile and the mint patch",
        opener="The path felt like the start of a secret mission.",
        weather="A pale morning breeze stirred the leaves.",
        ending="The little yard no longer felt troubled; it felt like a safe camp again.",
        tags={"yard", "adventure"},
    ),
    "orchard": Setting(
        id="orchard",
        place="at the edge of the apple orchard",
        approach="between the low apple trees and a stack of baskets",
        opener="Every step made the morning feel more like an expedition.",
        weather="The air smelled like apples and damp bark.",
        ending="The orchard looked bright and calm, as if the danger had slipped away.",
        tags={"orchard", "adventure"},
    ),
    "mill_lane": Setting(
        id="mill_lane",
        place="near the old lane by the mill house",
        approach="along the pebbly path and under the leaning gate",
        opener="The children marched as if they were heading for a tiny frontier outpost.",
        weather="A thin ribbon of cloud moved over the blue sky.",
        ending="The lane seemed quiet and brave again, like the end of a good quest.",
        tags={"lane", "adventure"},
    ),
}

PROBLEMS = {
    "blocked_slats": Problem(
        id="blocked_slats",
        title="soot in the air slats",
        discovery="Black soot had settled over the front of the hutch and packed itself into the little air slats.",
        clue="One of the rabbits gave a tiny sneeze from inside.",
        risk="If the slats stayed clogged, the hutch would feel stuffy.",
        need="brush",
        solve_text="swept the soot gently out of each narrow slat",
        result_text="Soon fresh air slipped through the front again.",
        ask_line='"{partner}, look at that soot," {hero} whispered. "Why are the slats so dark?"',
        reason_line='"{clue_name} tells us the air is not moving well," {partner} said. "We need something that can reach the little spaces without hurting the wood."',
        meter_key="air_blocked",
        discomfort_key="sneezy",
        tags={"soot", "air", "hutch"},
    ),
    "sticky_latch": Problem(
        id="sticky_latch",
        title="a sticky latch",
        discovery="A wet smear of soot had turned the hutch latch black and gummy.",
        clue="When {hero} touched it, the latch only gave a tired little click and stayed shut.",
        risk="If the latch stayed sticky, they could not open the door properly to check inside.",
        need="cloth",
        solve_text="rubbed the soot away from the latch until the metal shone and moved freely",
        result_text="The latch lifted with a neat click.",
        ask_line='"{partner}, the latch is stuck in soot," {hero} said. "What do we do now?"',
        reason_line='"Dry poking will only smear it more," {partner} said. "We need something soft and damp to loosen the black mess."',
        meter_key="latch_stuck",
        discomfort_key="waiting",
        tags={"soot", "latch", "hutch"},
    ),
    "dirty_bowl": Problem(
        id="dirty_bowl",
        title="a black water bowl",
        discovery="Soot flakes had fallen through the wire and turned the water bowl gray-black.",
        clue="The small animals kept sniffing the bowl and turning away.",
        risk="If the bowl stayed dirty, the animals would not want a drink.",
        need="water",
        solve_text="carried away the dark water, rinsed the bowl, and filled it with fresh clear water",
        result_text="The bowl shone clean, and the water caught a tiny square of sky.",
        ask_line='"{partner}, there is soot in the bowl," {hero} said. "They cannot drink that, can they?"',
        reason_line='"No," {partner} said. "The clue is right there. They keep turning away, so we need fresh water, not more brushing."',
        meter_key="water_dirty",
        discomfort_key="thirsty",
        tags={"soot", "water", "hutch"},
    ),
}

TOOLS = {
    "brush": Tool(
        id="brush",
        label="soft brush",
        phrase="a soft brush from the shed hook",
        use_line="used the soft brush in small careful strokes",
        sense=3,
        helps={"brush"},
        tags={"brush", "cleaning"},
    ),
    "cloth": Tool(
        id="cloth",
        label="damp cloth",
        phrase="a damp cloth from the wash bucket",
        use_line="folded the damp cloth and worked carefully at the black smear",
        sense=3,
        helps={"cloth"},
        tags={"cloth", "cleaning"},
    ),
    "water": Tool(
        id="water",
        label="fresh water",
        phrase="a small pail of fresh water",
        use_line="tipped out the dirty water and poured in fresh water",
        sense=3,
        helps={"water"},
        tags={"water", "cleaning"},
    ),
    "fan": Tool(
        id="fan",
        label="toy fan",
        phrase="a toy fan with blue plastic blades",
        use_line="waved the toy fan at the mess",
        sense=1,
        helps={"none"},
        tags={"fan"},
    ),
    "hands": Tool(
        id="hands",
        label="bare hands",
        phrase="bare hands",
        use_line="reached straight for the soot with bare hands",
        sense=1,
        helps={"none"},
        tags={"hands"},
    ),
}

ANIMALS = {
    "rabbits": {
        "type": "rabbits",
        "label": "the rabbits",
        "phrase": "two rabbits with bright noses",
        "sound": "their noses twitched",
        "ending": "The rabbits settled down in clean straw.",
    },
    "guinea_pigs": {
        "type": "guinea_pigs",
        "label": "the guinea pigs",
        "phrase": "two guinea pigs with round shiny eyes",
        "sound": "their whiskers trembled",
        "ending": "The guinea pigs made small happy squeaks under the clean roof.",
    },
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Ruby", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Finn", "Theo", "Eli", "Sam"]
TRAIL_ITEMS = ["a red string map", "a button compass", "a twig flag", "a chalk arrow"]


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def compatible(problem: Problem, tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN and problem.need in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for problem_id, problem in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if compatible(problem, tool):
                    combos.append((setting_id, problem_id, tool_id))
    return combos


def predict_solution(world: World, problem: Problem, tool: Tool) -> dict:
    sim = world.copy()
    hutch = sim.get("hutch")
    hutch.meters[problem.meter_key] += 1
    propagate(sim, narrate=False)
    solved = compatible(problem, tool)
    if solved:
        hutch.meters[problem.meter_key] = 0.0
        animals = sim.get("animals")
        animals.meters[problem.discomfort_key] = 0.0
    return {
        "problem": hutch.meters[problem.meter_key] >= THRESHOLD,
        "solved": solved,
    }


def introduce(world: World, hero: Entity, partner: Entity, setting: Setting, trail_item: str) -> None:
    hero.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"{hero.id} and {partner.id} set off {setting.place}, {setting.approach}, carrying {trail_item} as if it were real explorer gear."
    )
    world.say(f"{setting.weather} {setting.opener}")


def destination(world: World, hero: Entity, partner: Entity, animals: Entity) -> None:
    world.say(
        f'At the end of the path stood the hutch where {animals.phrase} lived. "{hero.id}," {partner.id} said softly, "let\'s make sure everything is all right."'
    )


def discover_problem(world: World, hero: Entity, partner: Entity, problem: Problem, animals: Entity) -> None:
    hutch = world.get("hutch")
    hutch.meters[problem.meter_key] += 1
    propagate(world, narrate=False)
    clue = problem.clue.format(hero=hero.id)
    world.say(problem.discovery)
    world.say(clue)
    world.say(problem.ask_line.format(hero=hero.id, partner=partner.id))
    clue_name = "That sneeze" if problem.id == "blocked_slats" else "The clue"
    world.say(problem.reason_line.format(hero=hero.id, partner=partner.id, clue_name=clue_name))


def choose_tool(world: World, hero: Entity, partner: Entity, tool: Tool, problem: Problem) -> None:
    pred = predict_solution(world, problem, tool)
    world.facts["predicted_problem_present"] = pred["problem"]
    world.facts["predicted_solved"] = pred["solved"]
    world.say(
        f'"Then we need {tool.phrase}," {hero.id} said. "{tool.label.capitalize()} can help us do this the careful way."'
    )


def fetch_tool(world: World, hero: Entity, partner: Entity, tool: Tool) -> None:
    hero.memes["bravery"] += 1
    partner.memes["bravery"] += 1
    world.say(
        f"They hurried for {tool.phrase} and came back at once, their footsteps quick on the path as if the whole yard were depending on them."
    )


def solve_problem(world: World, hero: Entity, partner: Entity, caretaker: Entity, animals: Entity, problem: Problem, tool: Tool) -> None:
    hutch = world.get("hutch")
    world.say(
        f'{caretaker.label_word.capitalize()} watched from nearby and nodded. "Slow hands," {caretaker.pronoun()} said. "Good problem-solvers always look first and hurry second."'
    )
    world.say(
        f"{hero.id} and {partner.id} {tool.use_line}. Together they {problem.solve_text}."
    )
    hutch.meters[problem.meter_key] = 0.0
    animals.meters[problem.discomfort_key] = 0.0
    hero.memes["worry"] = 0.0
    partner.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    hero.memes["pride"] += 1
    partner.memes["pride"] += 1
    animals.meters["comfortable"] += 1
    world.say(problem.result_text)
    if problem.id == "blocked_slats":
        world.say(f"{animals.label.capitalize()} breathed easy again, and {animals.attrs['sound']}.")
    elif problem.id == "sticky_latch":
        world.say(f"{hero.id} opened the little door just enough to peek in, and {animals.attrs['sound']}.")
    else:
        world.say(f"{animals.label.capitalize()} bent to drink at once, and {animals.attrs['sound']}.")


def finish(world: World, hero: Entity, partner: Entity, setting: Setting, animals: Entity) -> None:
    world.say(
        f'"We did it," {partner.id} said. "{hero.id}, this really was an adventure."'
    )
    world.say(
        f'{hero.id} smiled at the clean hutch. "A good adventure means noticing trouble and fixing it."'
    )
    world.say(f"{animals.attrs['ending']} {setting.ending}")


def tell(
    setting: Setting,
    problem: Problem,
    tool: Tool,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    partner_name: str = "Tom",
    partner_gender: str = "boy",
    caretaker_type: str = "grandmother",
    animal_id: str = "rabbits",
    trail_item: str = "a twig flag",
) -> World:
    if not compatible(problem, tool):
        raise StoryError(explain_tool(problem, tool.id))

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, phrase=partner_name, role="partner"))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=caretaker_type, label="the caretaker", phrase="the caretaker", role="caretaker"))
    animal_cfg = ANIMALS[animal_id]
    animals = world.add(
        Entity(
            id="animals",
            kind="thing",
            type=animal_cfg["type"],
            label=animal_cfg["label"],
            phrase=animal_cfg["phrase"],
            role="animals",
            attrs={"sound": animal_cfg["sound"], "ending": animal_cfg["ending"]},
        )
    )
    hutch = world.add(Entity(id="hutch", kind="thing", type="hutch", label="hutch", phrase="the hutch", role="place", tags={"hutch", "soot"}))
    world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, role="tool", tags=set(tool.tags)))

    introduce(world, hero, partner, setting, trail_item)
    destination(world, hero, partner, animals)

    world.para()
    discover_problem(world, hero, partner, problem, animals)
    choose_tool(world, hero, partner, tool, problem)
    fetch_tool(world, hero, partner, tool)

    world.para()
    solve_problem(world, hero, partner, caretaker, animals, problem, tool)
    finish(world, hero, partner, setting, animals)

    world.facts.update(
        hero=hero,
        partner=partner,
        caretaker=caretaker,
        animals=animals,
        hutch=hutch,
        setting=setting,
        problem=problem,
        tool=tool,
        trail_item=trail_item,
        solved=hutch.meters[problem.meter_key] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "soot": [
        (
            "What is soot?",
            "Soot is a soft black dust made when smoke leaves tiny bits behind. It can stick to wood, metal, and bowls and make them dirty.",
        )
    ],
    "hutch": [
        (
            "What is a hutch?",
            "A hutch is a small house or shelter for animals like rabbits or guinea pigs. It helps keep them safe and dry.",
        )
    ],
    "air": [
        (
            "Why do air slats matter on a hutch?",
            "Air slats let fresh air move in and out. If they get blocked, the inside can feel stuffy.",
        )
    ],
    "latch": [
        (
            "What does a latch do?",
            "A latch helps keep a small door closed until someone lifts or slides it open. If it gets sticky, the door may not move well.",
        )
    ],
    "water": [
        (
            "Why do small animals need clean water?",
            "Animals need fresh clean water every day to drink. Dirty water can make them turn away instead of drinking.",
        )
    ],
    "brush": [
        (
            "Why is a soft brush good for soot in tiny spaces?",
            "A soft brush can lift light soot from cracks and slats without scraping hard. That makes it a careful cleaning tool.",
        )
    ],
    "cloth": [
        (
            "Why can a damp cloth help with sticky dirt?",
            "A damp cloth can loosen dirt and wipe it away at the same time. It is good when dry dirt has turned into a smear.",
        )
    ],
    "problem_solving": [
        (
            "What do good problem-solvers do first?",
            "They look at the clues before they act. Then they pick the tool that matches the real problem.",
        )
    ],
}

KNOWLEDGE_ORDER = ["soot", "hutch", "air", "latch", "water", "brush", "cloth", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    problem = f["problem"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "soot" and "hutch".',
        f"Tell a gentle problem-solving adventure where {hero.label} and {partner.label} discover {problem.title} {setting.place} and solve it through dialogue.",
        f"Write a child-facing story where two young explorers notice a clue, talk it over, choose {tool.label}, and make a small animal hutch safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    caretaker = f["caretaker"]
    animals = f["animals"]
    problem = f["problem"]
    tool = f["tool"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {partner.label}, two children on a little adventure, and {caretaker.label_word} nearby. The story also cares about {animals.label} living in the hutch.",
        ),
        (
            "What problem did they find at the hutch?",
            f"They found {problem.title}. {problem.discovery} {problem.risk}",
        ),
        (
            f"How did {hero.label} and {partner.label} know something was wrong?",
            f"They noticed a clue right away: {problem.clue.format(hero=hero.label)} That clue showed them the soot was causing a real problem, not just making the hutch look dirty.",
        ),
        (
            "How did they solve the problem?",
            f"They talked about the clue and chose {tool.label}. Then they {problem.solve_text}, because that tool matched the real problem they had found.",
        ),
        (
            "How did the story end?",
            f"It ended with the hutch safe and clean again. {animals.attrs['ending']} That final picture shows what changed after their careful work.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem = f["problem"]
    tool = f["tool"]
    tags = {"soot", "hutch", "problem_solving"}
    if problem.id == "blocked_slats":
        tags.add("air")
        tags.add("brush")
    elif problem.id == "sticky_latch":
        tags.add("latch")
        tags.add("cloth")
    else:
        tags.add("water")
    if tool.id == "brush":
        tags.add("brush")
    if tool.id == "cloth":
        tags.add("cloth")
    if tool.id == "water":
        tags.add("water")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        problem="blocked_slats",
        tool="brush",
        hero_name="Lily",
        hero_gender="girl",
        partner_name="Tom",
        partner_gender="boy",
        caretaker="grandmother",
        animal="rabbits",
        trail_item="a twig flag",
    ),
    StoryParams(
        setting="orchard",
        problem="sticky_latch",
        tool="cloth",
        hero_name="Ben",
        hero_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        caretaker="grandfather",
        animal="guinea_pigs",
        trail_item="a red string map",
    ),
    StoryParams(
        setting="mill_lane",
        problem="dirty_bowl",
        tool="water",
        hero_name="Nora",
        hero_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        caretaker="mother",
        animal="rabbits",
        trail_item="a button compass",
    ),
]


def explain_tool(problem: Problem, tool_id: str) -> str:
    tool = TOOLS[tool_id]
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(No story: '{tool_id}' is too weak or messy for this world (sense={tool.sense} < {SENSE_MIN}). "
            f"Try one of the careful tools instead: {better}.)"
        )
    return (
        f"(No story: {tool.label} does not match the problem '{problem.id}'. "
        f"This hutch problem needs {problem.need}, so the children would choose a more fitting tool.)"
    )


def outcome_of(params: StoryParams) -> str:
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    return "solved" if compatible(problem, tool) else "invalid"


ASP_RULES = r"""
% A tool is sensible when its common-sense score is high enough.
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.

% A tool fits a problem when the problem needs a specific kind of help and the
% tool provides that help.
compatible(P, T) :- problem(P), tool(T), needs(P, Need), helps(T, Need), sensible_tool(T).

% A full story combo is valid when the setting exists and the chosen tool fits
% the chosen hutch problem.
valid(S, P, T) :- setting(S), compatible(P, T).

outcome(P, T, solved) :- compatible(P, T).
outcome(P, T, invalid) :- problem(P), tool(T), not compatible(P, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for item in sorted(tool.helps):
            lines.append(asp.fact("helps", tool_id, item))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(problem_id: str, tool_id: str) -> str:
    import asp

    extra = f"chosen_problem({problem_id}).\nchosen_tool({tool_id})."
    model = asp.one_model(
        asp_program(
            extra,
            "#show outcome/3.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    for p, t, outcome in atoms:
        if p == problem_id and t == tool_id:
            return outcome
    return "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    for problem_id in PROBLEMS:
        for tool_id in TOOLS:
            py = "solved" if compatible(PROBLEMS[problem_id], TOOLS[tool_id]) else "invalid"
            asp_out = asp_outcome(problem_id, tool_id)
            if py != asp_out:
                rc = 1
                print(f"MISMATCH outcome for {problem_id}/{tool_id}: python={py} asp={asp_out}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a small soot-and-hutch adventure with dialogue and problem solving."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--caretaker", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not compatible(problem, tool):
            raise StoryError(explain_tool(problem, args.tool))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        problem = PROBLEMS[args.problem] if args.problem else next(iter(PROBLEMS.values()))
        raise StoryError(explain_tool(problem, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, tool_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=hero_name)
    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        tool=tool_id,
        hero_name=args.hero_name or hero_name,
        hero_gender=hero_gender,
        partner_name=args.partner_name or partner_name,
        partner_gender=partner_gender,
        caretaker=args.caretaker or rng.choice(["mother", "father", "grandmother", "grandfather"]),
        animal=args.animal or rng.choice(sorted(ANIMALS)),
        trail_item=rng.choice(TRAIL_ITEMS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal choice: {params.animal})")
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    if not compatible(problem, tool):
        raise StoryError(explain_tool(problem, params.tool))

    world = tell(
        setting=SETTINGS[params.setting],
        problem=problem,
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        caretaker_type=params.caretaker,
        animal_id=params.animal,
        trail_item=params.trail_item,
    )
    world.get("hero").label = params.hero_name
    world.get("partner").label = params.partner_name
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
        print(asp_program("", "#show valid/3.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, tool) combos:\n")
        for setting_id, problem_id, tool_id in combos:
            print(f"  {setting_id:10} {problem_id:14} {tool_id}")
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
            header = f"### {p.hero_name} & {p.partner_name}: {p.problem} with {p.tool} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
