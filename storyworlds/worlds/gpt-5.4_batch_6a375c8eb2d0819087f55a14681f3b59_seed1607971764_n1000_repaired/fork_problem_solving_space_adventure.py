#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py
==================================================================

A standalone story world for a tiny "space adventure" problem-solving tale.

Premise
-------
Two children are playing space explorers. During the game, an important mission
part slips into an awkward place. One child blurts out a quick bad idea -- using
a fork to poke for it -- but a calmer helper steers the moment toward a safer,
smarter plan. The children solve the problem with a tool that actually matches
the object and the place, then finish their pretend mission with new confidence.

This world is built around a small common-sense constraint:
the chosen rescue tool must match both

1. the lost item's physical properties, and
2. the kind of hiding place it fell into.

A magnet wand works for a metal part. A sticky loop works for a light flat part.
A grabber works where there is room to clasp something. A fork is known to the
world as a tempting but poor idea, and stories refuse to use it as the solution.

Run it
------
    python storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py
    python storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py --place vent --item star_key
    python storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py --tool fork
    python storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/fork_problem_solving_space_adventure.py --verify
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
class Mission:
    id: str
    scene: str
    opening: str
    goal: str
    end_line: str
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
class Place:
    id: str
    label: str
    phrase: str
    problem_text: str
    warning: str
    affordances: set[str] = field(default_factory=set)
    danger_tags: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    material: str
    shape: str
    mission_use: str
    success_hold: str
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
    method: str
    sense: int
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "helper"}]

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


def _r_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["lost"] < THRESHOLD:
        return []
    sig = ("worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__worry__"]


def _r_solve(world: World) -> list[str]:
    item = world.get("item")
    tool = world.get("tool")
    if item.meters["lost"] < THRESHOLD or tool.meters["used"] < THRESHOLD:
        return []
    if not world.facts.get("tool_matches", False):
        return []
    sig = ("solve", item.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["lost"] = 0.0
    item.meters["retrieved"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["confidence"] += 1
        kid.memes["worry"] = 0.0
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="solve", tag="physical", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tool_fits(place: Place, item: LostItem, tool: Tool) -> bool:
    if tool.sense < SENSE_MIN:
        return False
    method = tool.method
    if method not in place.affordances:
        return False
    if method == "magnet":
        return item.material == "metal"
    if method == "sticky":
        return item.shape == "flat"
    if method == "grip":
        return item.shape in {"chunky", "looped"}
    return False


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for place_id, place in PLACES.items():
            for item_id, item in ITEMS.items():
                for tool_id, tool in TOOLS.items():
                    if tool_fits(place, item, tool):
                        combos.append((mission_id, place_id, item_id, tool_id))
    return combos


def explain_tool_rejection(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(Refusing tool '{tool_id}': a {tool.label} is a poor and unsafe fix here. "
            f"In this world, the fork is the hasty idea the children should stop and rethink. "
            f"Try one of: {better}.)"
        )
    return f"(Refusing tool '{tool_id}': it is not a sensible rescue tool here.)"


def explain_combo_rejection(place: Place, item: LostItem, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return explain_tool_rejection(tool.id)
    return (
        f"(No story: {tool.label} does not honestly solve getting the {item.label} out of "
        f"{place.phrase}. The rescue tool must match both the place and the item.)"
    )


def predict_solution(world: World, tool_id: str) -> dict:
    sim = world.copy()
    sim_tool = sim.get(tool_id)
    sim_tool.meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": sim.get("item").meters["retrieved"] >= THRESHOLD,
        "remaining_lost": sim.get("item").meters["lost"],
    }


def setup(world: World, captain: Entity, helper: Entity, mission: Mission) -> None:
    for kid in (captain, helper):
        kid.memes["joy"] += 1
        kid.memes["imagination"] += 1
    world.say(
        f"After supper, {captain.id} and {helper.id} turned the room into {mission.scene}. "
        f"{mission.opening}"
    )
    world.say(
        f'"Captain {captain.id}," said {helper.id}, saluting with two fingers, '
        f'"our mission is {mission.goal}."'
    )


def trouble(world: World, captain: Entity, item: LostItem, place: Place) -> None:
    world.get("item").meters["lost"] += 1
    propagate(world, narrate=False)
    captain.memes["surprise"] += 1
    world.say(
        f"Then the {item.label} slipped away and vanished into {place.phrase}. "
        f"{place.problem_text}"
    )


def bad_idea(world: World, captain: Entity, helper: Entity, place: Place) -> None:
    captain.memes["impulse"] += 1
    world.say(
        f'"I know," {captain.id} said. "I can poke for it with a fork."'
    )
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head at once. '
        f'"No. {place.warning} A fork could slip, scrape, or get stuck too."'
    )


def think(world: World, helper: Entity, tool: Tool) -> None:
    helper.memes["calm"] += 1
    pred = predict_solution(world, "tool")
    world.facts["predicted_solved"] = pred["solved"]
    world.say(
        f'{helper.id} crouched down and looked carefully. '
        f'"Let\'s stop and think like real space explorers," {helper.pronoun()} said. '
        f'"We need {tool.phrase}, because it can {tool.text}."'
    )


def use_tool(world: World, captain: Entity, helper: Entity, item: LostItem, tool: Tool) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    propagate(world, narrate=False)
    captain.memes["focus"] += 1
    helper.memes["focus"] += 1
    world.say(
        f"Together they moved slowly. {captain.id} held the light steady while "
        f"{helper.id} used {tool.phrase}. {tool.text.capitalize()}, and soon "
        f"the {item.label} slid back into sight."
    )


def celebrate(world: World, captain: Entity, helper: Entity, mission: Mission, item: LostItem) -> None:
    for kid in (captain, helper):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f'"We got it!" {captain.id} cheered, holding {item.success_hold}.'
    )
    world.say(
        f"They set the {item.label} back where it belonged and finished {item.mission_use}. "
        f"{mission.end_line}"
    )


def lesson(world: World, parent: Entity, captain: Entity, helper: Entity) -> None:
    for kid in (captain, helper):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled from the doorway. "
        f'"That was smart problem solving," {parent.pronoun()} said. '
        f'"You did not grab the first idea. You looked, thought, and picked the right tool."'
    )


def tell(
    mission: Mission,
    place: Place,
    item_cfg: LostItem,
    tool_cfg: Tool,
    captain_name: str = "Nova",
    captain_gender: str = "girl",
    helper_name: str = "Leo",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_gender,
        role="captain",
        traits=["bold"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["careful"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="mission_part",
        label=item_cfg.label,
        attrs={"material": item_cfg.material, "shape": item_cfg.shape},
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        attrs={"method": tool_cfg.method},
    ))
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))

    world.facts.update(
        mission=mission,
        place_cfg=place,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        captain=captain,
        helper=helper,
        parent=parent,
        item=item,
        tool=tool,
        tool_matches=tool_fits(place, item_cfg, tool_cfg),
    )

    setup(world, captain, helper, mission)
    world.para()
    trouble(world, captain, item_cfg, place)
    bad_idea(world, captain, helper, place)
    world.para()
    think(world, helper, tool_cfg)
    use_tool(world, captain, helper, item_cfg, tool_cfg)
    celebrate(world, captain, helper, mission, item_cfg)
    lesson(world, parent, captain, helper)

    world.facts.update(
        solved=item.meters["retrieved"] >= THRESHOLD,
        bad_idea="fork",
    )
    return world


MISSIONS = {
    "beacon": Mission(
        id="beacon",
        scene="a silver spaceship under a dark blanket sky",
        opening="A laundry basket was the cockpit, glow stickers were stars, and a pillow became the moon.",
        goal="to relight the lost moon beacon before the pretend comet storm arrived",
        end_line="Soon their cardboard ship was humming through the stars again, and the brave crew knew they could solve hard things together.",
        tags={"space", "beacon"},
    ),
    "rescue": Mission(
        id="rescue",
        scene="a rescue shuttle circling a sleepy red planet",
        opening="Two chairs were the pilot seats, a scarf was the nebula trail, and a lamp on the rug shone like a faraway sun.",
        goal="to send supplies to a tiny rover before night fell on the planet",
        end_line="The mission glowed on, and the little crew felt steadier than before, as if their ship had learned a new kind of strength.",
        tags={"space", "rover"},
    ),
    "saturn": Mission(
        id="saturn",
        scene="a ringed explorer ship headed for Saturn",
        opening="A cardboard box was the control room, crayons were star maps, and a shiny bowl on the floor was the planet with bright rings.",
        goal="to guide the ship safely through the glittering rings",
        end_line="Their ship sailed on past the shining rings, and both explorers wore the pleased look of children who had solved their own little mystery.",
        tags={"space", "planet"},
    ),
}

PLACES = {
    "vent": Place(
        id="vent",
        label="floor vent",
        phrase="the narrow floor vent by the wall",
        problem_text="The slats were too close for fingers, and the dark space beneath looked deep as a tiny engine tunnel.",
        warning="Forks do not belong near vents, and the narrow slats are the wrong place for poking",
        affordances={"magnet", "sticky"},
        danger_tags={"metalwork"},
        tags={"vent"},
    ),
    "sofa_gap": Place(
        id="sofa_gap",
        label="sofa gap",
        phrase="the deep gap behind the sofa",
        problem_text="It had slipped past the cushions into a dark crack where hands could not reach all the way down.",
        warning="A fork is a poor tool for fishing in a deep crack behind furniture",
        affordances={"magnet", "sticky", "grip"},
        danger_tags={"sharp"},
        tags={"sofa"},
    ),
    "crate_edge": Place(
        id="crate_edge",
        label="storage crate",
        phrase="the space behind the tall toy crate",
        problem_text="The crate sat close to the wall, leaving only a skinny shadow where the piece had hidden itself.",
        warning="A fork could scratch the crate and still miss the lost part",
        affordances={"sticky", "grip"},
        danger_tags={"sharp"},
        tags={"crate"},
    ),
}

ITEMS = {
    "star_key": LostItem(
        id="star_key",
        label="star key",
        phrase="a shiny star key",
        material="metal",
        shape="chunky",
        mission_use="the moon beacon",
        success_hold="the star key high in the flashlight beam",
        tags={"metal", "key"},
    ),
    "moon_map": LostItem(
        id="moon_map",
        label="moon map",
        phrase="a thin moon map card",
        material="paper",
        shape="flat",
        mission_use="the course through the comet trail",
        success_hold="the moon map card carefully between both hands",
        tags={"map", "paper"},
    ),
    "comet_chip": LostItem(
        id="comet_chip",
        label="comet chip",
        phrase="a little comet chip",
        material="plastic",
        shape="flat",
        mission_use="the signal board",
        success_hold="the comet chip on an open palm",
        tags={"chip", "plastic"},
    ),
    "ring_handle": LostItem(
        id="ring_handle",
        label="ring handle",
        phrase="a looped ring handle",
        material="plastic",
        shape="looped",
        mission_use="the rover hatch",
        success_hold="the ring handle dangling from two fingers",
        tags={"handle", "loop"},
    ),
}

TOOLS = {
    "magnet_wand": Tool(
        id="magnet_wand",
        label="magnet wand",
        phrase="the magnet wand",
        method="magnet",
        sense=3,
        text="pull the metal piece without pushing it farther away",
        qa_text="used a magnet wand to pull the metal piece back",
        tags={"magnet"},
    ),
    "tape_loop": Tool(
        id="tape_loop",
        label="tape loop on a ruler",
        phrase="a ruler with a little tape loop on the end",
        method="sticky",
        sense=3,
        text="touch the flat piece and lift it gently",
        qa_text="used a tape loop to lift the flat piece out",
        tags={"tape"},
    ),
    "grabber": Tool(
        id="grabber",
        label="grabber claw",
        phrase="the grabber claw",
        method="grip",
        sense=2,
        text="reach into the gap and clasp the piece without dropping it",
        qa_text="used a grabber claw to clasp the piece and pull it free",
        tags={"grabber"},
    ),
    "fork": Tool(
        id="fork",
        label="fork",
        phrase="a fork",
        method="poke",
        sense=1,
        text="jab at the lost piece",
        qa_text="tried to poke for it with a fork",
        tags={"fork"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zoe", "Ava", "Nora", "Skye"]
BOY_NAMES = ["Leo", "Max", "Finn", "Eli", "Theo", "Kai", "Sam"]


@dataclass
class StoryParams:
    mission: str
    place: str
    item: str
    tool: str
    captain: str
    captain_gender: str
    helper: str
    helper_gender: str
    parent: str
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
    "fork": [(
        "Why was using a fork a bad idea?",
        "A fork is for eating, not for solving a stuck-object problem. It can slip, scratch things, or push the lost object farther away."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet can pull some metal things without grabbing them with fingers. That makes it useful when a metal object is hard to reach."
    )],
    "tape": [(
        "How can a tape loop help pick something up?",
        "A small sticky loop can touch a light flat object and lift it gently. It works best when the object is not heavy."
    )],
    "grabber": [(
        "What is a grabber claw for?",
        "A grabber claw is a tool that reaches into a tight place and clasps something. It helps when hands cannot fit."
    )],
    "vent": [(
        "Why are floor vents tricky places to reach into?",
        "Floor vents have narrow slats and a dark space underneath. Small things can slip in where fingers cannot easily go."
    )],
    "problem_solving": [(
        "What does good problem solving mean?",
        "Good problem solving means you stop, look carefully, and choose a plan that fits the problem. The first idea is not always the best one."
    )],
}

KNOWLEDGE_ORDER = ["problem_solving", "fork", "vent", "magnet", "tape", "grabber"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    tool = f["tool_cfg"]
    captain = f["captain"]
    helper = f["helper"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "fork" and centers on problem solving.',
        f"Tell a gentle story where {captain.id} and {helper.id} lose a {item.label} during a pretend space mission, reject the bad fork idea, and solve the problem with {tool.phrase}.",
        f"Write a child-facing story set in a pretend spaceship where a mission part slips into {place.phrase}, and the children must think carefully to finish {mission.goal}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    helper = f["helper"]
    parent = f["parent"]
    mission = f["mission"]
    place = f["place_cfg"]
    item = f["item_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain.id} and {helper.id}, two children pretending to be space explorers. {parent.label_word.capitalize()} also appears at the end and notices how they solved the problem."
        ),
        (
            "What problem happened in the story?",
            f"The {item.label} slipped into {place.phrase} while they were playing. That mattered because they needed it to finish {mission.goal}."
        ),
        (
            "Why did the children decide not to use a fork?",
            f"They stopped the fork idea because it was the wrong tool for that tight place. A fork could slip or push the {item.label} farther away instead of helping."
        ),
        (
            f"How did {helper.id} solve the problem?",
            f"{helper.id} suggested {tool.phrase} and used it carefully while {captain.id} helped. It worked because that tool matched both the {item.label} and the place where it was stuck."
        ),
        (
            "How did the story end?",
            f"They got the {item.label} back and finished their pretend mission. The ending shows that they felt proud because careful thinking worked better than the first quick idea."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"problem_solving", "fork"}
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    if "vent" in place.tags:
        tags.add("vent")
    tags |= set(tool.tags)
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="beacon",
        place="vent",
        item="star_key",
        tool="magnet_wand",
        captain="Nova",
        captain_gender="girl",
        helper="Leo",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        mission="rescue",
        place="sofa_gap",
        item="moon_map",
        tool="tape_loop",
        captain="Max",
        captain_gender="boy",
        helper="Luna",
        helper_gender="girl",
        parent="father",
    ),
    StoryParams(
        mission="saturn",
        place="crate_edge",
        item="ring_handle",
        tool="grabber",
        captain="Mira",
        captain_gender="girl",
        helper="Finn",
        helper_gender="boy",
        parent="mother",
    ),
    StoryParams(
        mission="beacon",
        place="sofa_gap",
        item="comet_chip",
        tool="tape_loop",
        captain="Theo",
        captain_gender="boy",
        helper="Skye",
        helper_gender="girl",
        parent="father",
    ),
]


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.

supports(P, magnet) :- place(P), afford(P, magnet).
supports(P, sticky) :- place(P), afford(P, sticky).
supports(P, grip)   :- place(P), afford(P, grip).

fits(I, magnet) :- item(I), material(I, metal).
fits(I, sticky) :- item(I), shape(I, flat).
fits(I, grip)   :- item(I), shape(I, chunky).
fits(I, grip)   :- item(I), shape(I, looped).

valid(M, P, I, T) :- mission(M), place(P), item(I), tool(T),
                     sensible_tool(T), method(T, K),
                     supports(P, K), fits(I, K).

outcome(solved) :- chosen_place(P), chosen_item(I), chosen_tool(T),
                   sensible_tool(T), method(T, K), supports(P, K), fits(I, K).
outcome(stuck)  :- not outcome(solved).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for affordance in sorted(place.affordances):
            lines.append(asp.fact("afford", place_id, affordance))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("material", item_id, item.material))
        lines.append(asp.fact("shape", item_id, item.shape))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("method", tool_id, tool.method))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    return "solved" if tool_fits(place, item, tool) else "stuck"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    test_cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            test_cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in test_cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(test_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(test_cases)} outcome checks differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(777))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny space adventure about solving a stuck-object problem."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool is not None and args.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {args.tool})")
    if args.place is not None and args.place not in PLACES:
        raise StoryError(f"(Unknown place: {args.place})")
    if args.item is not None and args.item not in ITEMS:
        raise StoryError(f"(Unknown item: {args.item})")
    if args.mission is not None and args.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {args.mission})")

    if args.tool is not None and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.place is None or combo[1] == args.place)
        and (args.item is None or combo[2] == args.item)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        if args.place and args.item and args.tool:
            raise StoryError(explain_combo_rejection(PLACES[args.place], ITEMS[args.item], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, place_id, item_id, tool_id = rng.choice(sorted(combos))
    captain, captain_gender = _pick_name(rng)
    helper, helper_gender = _pick_name(rng, avoid=captain)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        mission=mission_id,
        place=place_id,
        item=item_id,
        tool=tool_id,
        captain=captain,
        captain_gender=captain_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mission = MISSIONS[params.mission]
        place = PLACES[params.place]
        item = ITEMS[params.item]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err})") from None

    if not tool_fits(place, item, tool):
        raise StoryError(explain_combo_rejection(place, item, tool))

    world = tell(
        mission=mission,
        place=place,
        item_cfg=item,
        tool_cfg=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, place, item, tool) combos:\n")
        for mission_id, place_id, item_id, tool_id in combos:
            print(f"  {mission_id:8} {place_id:10} {item_id:11} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.captain} & {p.helper}: {p.item} in {p.place} ({p.mission}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
