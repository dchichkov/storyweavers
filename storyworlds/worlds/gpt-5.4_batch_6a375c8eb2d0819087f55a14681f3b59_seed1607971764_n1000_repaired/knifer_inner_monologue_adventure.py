#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py
==============================================================

A standalone storyworld for a tiny adventure tale with **inner monologue**:
two children on a treasure-style expedition find their prize caught behind a
natural obstacle, and one child is tempted to use a sharp **knifer** alone.
The world model prefers the safer adventure move: pause, think, and get the
right grown-up help.

The domain is intentionally small and constraint-checked:
- some obstacles can reasonably be cut loose; some cannot
- some grown-up responses can really solve the problem; weak ones are refused
- an older, cautious partner can sometimes talk the eager explorer out of using
  the knifer at all
- otherwise the child tries it, gets into a small scrape, and a ranger fixes the
  problem the right way

Run it
------
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py --obstacle vine
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py --obstacle stone
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py --response tape
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py --all
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/knifer_inner_monologue_adventure.py --verify
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
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    cuttable: bool = False
    sharp: bool = False
    # physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_f"}
        male = {"boy", "father", "man", "ranger_m"}
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
            "ranger_f": "ranger",
            "ranger_m": "ranger",
        }.get(self.type, self.type)
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
class Expedition:
    id: str
    place: str
    opener: str
    goal: str
    path: str
    finale: str
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
    the: str
    caught_text: str
    challenge_text: str
    cut_line: str
    spread: int
    cuttable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Prize:
    id: str
    label: str
    phrase: str
    shine: str
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
class SharpTool:
    id: str
    label: str
    phrase: str
    where: str
    action: str
    lesson: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_nick(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    leader = world.get("leader")
    if tool.meters["swinging"] < THRESHOLD:
        return out
    sig = ("nick",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.meters["nick"] += 1
    leader.memes["shock"] += 1
    leader.memes["fear"] += 1
    world.get("camp").meters["danger"] += 1
    out.append("__nick__")
    return out


def _r_snag_worse(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    tool = world.get("tool")
    if obstacle.meters["tugged"] < THRESHOLD or tool.meters["used"] < THRESHOLD:
        return out
    sig = ("snag_worse",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["tight"] += 1
    out.append("__tight__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="nick", tag="physical", apply=_r_nick),
    Rule(name="snag_worse", tag="physical", apply=_r_snag_worse),
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


def obstacle_at_risk(tool: SharpTool, obstacle: Obstacle) -> bool:
    return obstacle.cuttable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def snag_severity(obstacle: Obstacle, delay: int) -> int:
    return obstacle.spread + delay


def is_resolved(response: Response, obstacle: Obstacle, delay: int) -> bool:
    return response.power >= snag_severity(obstacle, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, leader_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > leader_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if partner_older else 0.0)
    return partner_older and authority > BOLDNESS_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    _do_knifer(sim, narrate=False)
    return {
        "nick": sim.get("leader").meters["nick"] >= THRESHOLD,
        "danger": sim.get("camp").meters["danger"],
        "tight": sim.get("obstacle").meters["tight"] >= THRESHOLD,
    }


def _do_knifer(world: World, narrate: bool = True) -> None:
    tool = world.get("tool")
    obstacle = world.get("obstacle")
    tool.meters["used"] += 1
    tool.meters["swinging"] += 1
    obstacle.meters["tugged"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, leader: Entity, partner: Entity, expedition: Expedition) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["adventure"] += 1
    world.say(
        f"{leader.id} and {partner.id} set out on {expedition.opener}. "
        f"They followed {expedition.path}, certain that {expedition.goal} was waiting ahead."
    )


def find_prize(world: World, prize: Prize, obstacle: Obstacle) -> None:
    world.say(
        f"Soon they spotted {prize.phrase}, {prize.shine}, but {obstacle.the} held it fast. "
        f"{obstacle.challenge_text}"
    )


def inner_monologue_tempt(world: World, leader: Entity, tool: SharpTool) -> None:
    leader.memes["boldness"] += 1
    world.say(
        f"In {leader.id}'s pocket was {tool.phrase}. "
        f'"I could {tool.action} myself," {leader.pronoun()} thought. '
        f'"If I am quick, I can finish the adventure before anyone says no."'
    )


def warn(world: World, partner: Entity, leader: Entity, tool: SharpTool, obstacle: Obstacle, ranger: Entity) -> None:
    pred = predict_trouble(world)
    partner.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["nick"]:
        extra = f" {partner.id} imagined the sharp edge skipping and hurting {leader.id}."
    world.say(
        f'{partner.id} touched {leader.id}\'s sleeve. "Please do not use the {tool.label} alone," '
        f'{partner.pronoun()} said. "{obstacle.The} is twisty, and {ranger.label_word} said sharp tools are for grown-up hands on jobs like this."'
        f"{extra}"
    )


def back_down(world: World, leader: Entity, partner: Entity, tool: SharpTool, ranger: Entity) -> None:
    leader.memes["boldness"] = 0.0
    leader.memes["relief"] += 1
    partner.memes["relief"] += 1
    sib = "brother" if partner.type == "boy" else "sister"
    world.say(
        f'{leader.id} took one look at {partner.id}, {leader.pronoun("possessive")} older {sib}, and let out a long breath. '
        f'"My adventure brain wanted to be first," {leader.pronoun()} thought, "but being brave can mean stopping."'
    )
    world.say(
        f"So {leader.pronoun()} folded the {tool.label} closed and called for the {ranger.label_word} instead."
    )


def defy(world: World, leader: Entity, partner: Entity, tool: SharpTool) -> None:
    leader.memes["defiance"] += 1
    world.say(
        f'"Maybe just one little cut," {leader.pronoun()} thought. '
        f'Before {partner.id} could stop {leader.pronoun("object")}, {leader.pronoun()} pulled out the {tool.label}.'
    )


def scrape(world: World, leader: Entity, obstacle: Obstacle, tool: SharpTool) -> None:
    _do_knifer(world, narrate=False)
    world.say(
        f"{tool.phrase.capitalize()} flashed once. The sharp edge slipped on {obstacle.cut_line}, "
        f"and {leader.id} gave a small gasp."
    )
    if leader.meters["nick"] >= THRESHOLD:
        world.say(
            f"The {tool.label} had only nicked {leader.pronoun('possessive')} finger, but that tiny sting made the whole trail feel less like a game."
        )
    if obstacle.meters["tight"] >= THRESHOLD:
        world.say(
            f"Worse, {obstacle.the} pulled tighter around the prize instead of letting go."
        )


def alarm(world: World, partner: Entity, leader: Entity, ranger: Entity) -> None:
    world.say(f'"{ranger.label_word.capitalize()}!" {partner.id} called. "{leader.id} tried the knifer and got hurt!"')


def rescue(world: World, ranger: Entity, response: Response, obstacle: Obstacle, prize: Prize) -> None:
    world.get("camp").meters["danger"] = 0.0
    world.get("obstacle").meters["tight"] = 0.0
    world.get("obstacle").meters["caught"] = 0.0
    world.get("leader").memes["fear"] = 0.0
    body = response.text.replace("{obstacle}", obstacle.label).replace("{prize}", prize.label)
    world.say(
        f"The {ranger.label_word} came at once and {body}."
    )
    world.say(
        f"In a moment, {prize.phrase} was free again, and the trail felt open instead of prickly and tight."
    )


def rescue_fail(world: World, ranger: Entity, response: Response, obstacle: Obstacle, prize: Prize) -> None:
    world.get("camp").meters["danger"] += 1
    body = response.fail.replace("{obstacle}", obstacle.label).replace("{prize}", prize.label)
    world.say(
        f"The {ranger.label_word} hurried over and {body}."
    )
    world.say(
        f"The knot of trouble only seemed bigger, and {prize.phrase} still trembled out of reach."
    )


def comfort_and_lesson(world: World, ranger: Entity, leader: Entity, partner: Entity, tool: SharpTool) -> None:
    for kid in (leader, partner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["trust"] += 1
    world.say(
        f'The {ranger.label_word} knelt beside them. "I am glad you called right away," {ranger.pronoun()} said. '
        f'"A knifer can solve some jobs, but only when a grown-up is in charge and everyone has space to work."'
    )
    world.say(
        f'{leader.id} looked at the closed tool in {leader.pronoun("possessive")} hand. '
        f'"Next time," {leader.pronoun()} thought, "I will stop my fast adventure idea before it runs ahead of me."'
    )
    world.say(
        f'{partner.id} nodded, and together they promised that {tool.lesson}.'
    )


def grim_lesson(world: World, ranger: Entity, leader: Entity, partner: Entity, tool: SharpTool) -> None:
    for kid in (leader, partner):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'The {ranger.label_word} wrapped {leader.id}\'s small finger and led both children back to camp. '
        f'"No lost treasure is worth a sharp mistake," {ranger.pronoun()} said.'
    )
    world.say(
        f'{leader.id} thought about the stalled adventure and the sting in {leader.pronoun("possessive")} hand. '
        f'{partner.id} stayed close, and neither of them forgot that {tool.lesson}.'
    )


def bright_ending(world: World, expedition: Expedition, prize: Prize, leader: Entity, partner: Entity) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"They held up {prize.phrase}, and {prize.shine.lower()} seemed to wink at them from the sunlight."
    )
    world.say(
        f"Then the two explorers {expedition.finale}, walking a little slower and a lot wiser than before."
    )


def partial_ending(world: World, expedition: Expedition, leader: Entity, partner: Entity) -> None:
    world.say(
        f"Even without the prize, they walked back along {expedition.path}, still side by side."
    )
    world.say(
        f"The adventure had changed shape: not a tale about being first, but a tale about getting everyone home safe."
    )


def tell(
    expedition: Expedition,
    obstacle: Obstacle,
    prize: Prize,
    tool: SharpTool,
    response: Response,
    leader_name: str = "Nia",
    leader_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    trait: str = "careful",
    ranger_type: str = "ranger_f",
    delay: int = 0,
    leader_age: int = 6,
    partner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        role="leader",
        age=leader_age,
        attrs={"name": leader_name, "relation": relation},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        age=partner_age,
        traits=[trait],
        attrs={"name": partner_name, "relation": relation},
    ))
    ranger = world.add(Entity(
        id="ranger",
        kind="character",
        type=ranger_type,
        label="the ranger",
        role="ranger",
    ))
    world.add(Entity(id="camp", type="camp", label="camp"))
    world.add(Entity(id="tool", type="tool", label=tool.label, sharp=True))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label, cuttable=obstacle.cuttable))
    world.add(Entity(id="prize", type="prize", label=prize.label))

    leader.memes["boldness"] = BOLDNESS_INIT
    partner.memes["trust"] = float(trust)
    partner.memes["caution"] = initial_caution(trait)
    world.get("obstacle").meters["caught"] = 1.0

    introduce(world, leader, partner, expedition)
    find_prize(world, prize, obstacle)

    world.para()
    inner_monologue_tempt(world, leader, tool)
    warn(world, partner, leader, tool, obstacle, ranger)

    averted = would_avert(relation, leader_age, partner_age, trait)

    if averted:
        back_down(world, leader, partner, tool, ranger)
        world.para()
        rescue(world, ranger, best_response(), obstacle, prize)
        comfort_and_lesson(world, ranger, leader, partner, tool)
        world.para()
        bright_ending(world, expedition, prize, leader, partner)
        severity = 0
        resolved = True
    else:
        defy(world, leader, partner, tool)
        world.para()
        scrape(world, leader, obstacle, tool)
        alarm(world, partner, leader, ranger)
        severity = snag_severity(obstacle, delay)
        world.get("obstacle").meters["severity"] = float(severity)
        resolved = is_resolved(response, obstacle, delay)

        world.para()
        if resolved:
            rescue(world, ranger, response, obstacle, prize)
            comfort_and_lesson(world, ranger, leader, partner, tool)
            world.para()
            bright_ending(world, expedition, prize, leader, partner)
        else:
            rescue_fail(world, ranger, response, obstacle, prize)
            grim_lesson(world, ranger, leader, partner, tool)
            world.para()
            partial_ending(world, expedition, leader, partner)

    outcome = "averted" if averted else ("resolved" if resolved else "stalled")
    world.facts.update(
        expedition=expedition,
        obstacle_cfg=obstacle,
        prize_cfg=prize,
        tool_cfg=tool,
        response=response,
        leader=leader,
        partner=partner,
        ranger=ranger,
        outcome=outcome,
        injury=leader.meters["nick"] >= THRESHOLD,
        resolved=resolved,
        severity=severity,
        delay=delay,
        relation=relation,
    )
    return world


EXPEDITIONS = {
    "trail": Expedition(
        id="trail",
        place="the forest trail",
        opener="their Saturday treasure expedition at the forest trail",
        goal="a hidden token from the old map",
        path="the mossy path under tall trees",
        finale="hurried on toward the next turn in the map",
        tags={"trail", "adventure"},
    ),
    "marsh": Expedition(
        id="marsh",
        place="the reeds by the marsh walk",
        opener="their marsh-side adventure march",
        goal="a bright finder's charm from the map",
        path="the boardwalk between whispering reeds",
        finale="stepped on toward the little lookout deck",
        tags={"marsh", "adventure"},
    ),
    "cove": Expedition(
        id="cove",
        place="the rocky cove path",
        opener="their cliff-cove adventure hunt",
        goal="a shining explorer badge from the map",
        path="the windy path above the water",
        finale="trotted toward the cave-mouth bend",
        tags={"cove", "adventure"},
    ),
}

OBSTACLES = {
    "vine": Obstacle(
        id="vine",
        label="vine curtain",
        the="the vine curtain",
        caught_text="caught in a hanging vine curtain",
        challenge_text="Long green loops twisted around it like a tiny jungle gate.",
        cut_line="the twisting vine",
        spread=2,
        cuttable=True,
        tags={"vine", "plants"},
    ),
    "bramble": Obstacle(
        id="bramble",
        label="bramble tangle",
        the="the bramble tangle",
        caught_text="caught in a bramble tangle",
        challenge_text="The thorny stems hooked together so tightly that every pull made them pinch more.",
        cut_line="the thorny bramble stem",
        spread=3,
        cuttable=True,
        tags={"bramble", "plants"},
    ),
    "net": Obstacle(
        id="net",
        label="old rope net",
        the="the old rope net",
        caught_text="caught in an old rope net",
        challenge_text="The wet cords had knotted themselves into a stubborn snare.",
        cut_line="the wet rope knot",
        spread=2,
        cuttable=True,
        tags={"rope", "knot"},
    ),
    "stone": Obstacle(
        id="stone",
        label="stone crack",
        the="the stone crack",
        caught_text="wedged in a stone crack",
        challenge_text="Hard rock pressed around it, and no careful slice could change that.",
        cut_line="the stone edge",
        spread=1,
        cuttable=False,
        tags={"stone"},
    ),
}

PRIZES = {
    "token": Prize(
        id="token",
        label="sun token",
        phrase="the little sun token",
        shine="Its gold paint shone like a brave little sunrise",
        tags={"treasure"},
    ),
    "badge": Prize(
        id="badge",
        label="compass badge",
        phrase="the round compass badge",
        shine="Its silver rim flashed like a tiny moon",
        tags={"treasure"},
    ),
    "shell": Prize(
        id="shell",
        label="glimmer shell",
        phrase="the glimmer shell",
        shine="Its pale stripes glowed like a secret pearl",
        tags={"treasure"},
    ),
}

TOOLS = {
    "knifer": SharpTool(
        id="knifer",
        label="knifer",
        phrase="a little folding knifer",
        where="in the side pocket of the pack",
        action="snip the snag free",
        lesson="children must ask a grown-up before a sharp tool comes out",
        tags={"sharp_tool", "knifer"},
    ),
}

RESPONSES = {
    "shears": Response(
        id="shears",
        sense=3,
        power=4,
        text="used long-handled shears to open a safe gap in the {obstacle} and lifted the {prize} free with a gloved hand",
        fail="tried the shears, but the mess of stems had tightened too much to clear quickly",
        qa_text="used long-handled shears and a gloved hand to free the prize",
        tags={"shears", "gloves", "grownup_help"},
    ),
    "untangle": Response(
        id="untangle",
        sense=3,
        power=3,
        text="steadied the branches, loosened each loop one by one, and untangled the {prize} without any sharp edges near the children",
        fail="worked at the loops, but they had cinched too tightly to loosen in time",
        qa_text="loosened the loops and untangled the prize by hand",
        tags={"untangle", "grownup_help"},
    ),
    "pole": Response(
        id="pole",
        sense=2,
        power=2,
        text="used a hook pole to lift the snag high, then slid the {prize} free",
        fail="lifted at the snag with a pole, but the tangle only pulled tighter",
        qa_text="used a hook pole to lift the snag and slide the prize free",
        tags={"pole", "grownup_help"},
    ),
    "tape": Response(
        id="tape",
        sense=1,
        power=1,
        text="wrapped tape around the trouble spot and tugged until the {prize} came loose",
        fail="wrapped tape around the tangle, but tape could not solve a job like that",
        qa_text="wrapped tape around the tangle",
        tags={"tape"},
    ),
}

GIRL_NAMES = ["Nia", "Mila", "Ava", "Lena", "Zoe", "Ivy", "Maya", "Lila"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Eli", "Noah", "Theo", "Max", "Kai"]
TRAITS = ["careful", "steady", "patient", "thoughtful", "curious", "brisk"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for expedition_id in EXPEDITIONS:
        for obstacle_id, obstacle in OBSTACLES.items():
            if obstacle_at_risk(TOOLS["knifer"], obstacle):
                for prize_id in PRIZES:
                    combos.append((expedition_id, obstacle_id, prize_id))
    return combos


@dataclass
class StoryParams:
    expedition: str
    obstacle: str
    prize: str
    tool: str
    response: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    ranger_type: str
    trait: str
    delay: int = 0
    leader_age: int = 6
    partner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "knifer": [(
        "What is a knifer?",
        "In this story, a knifer is a small sharp tool for cutting. Sharp tools are for careful grown-up use, not for children to handle alone."
    )],
    "sharp_tool": [(
        "Why can a sharp tool be dangerous?",
        "A sharp tool can slip and cut skin very quickly. That is why children should stop and ask a grown-up for help."
    )],
    "plants": [(
        "Why can vines and brambles be hard to untangle?",
        "Vines loop around things, and brambles hook with little thorns. Pulling too fast can make the snag tighter instead of looser."
    )],
    "rope": [(
        "Why do knots get tighter when you pull the wrong way?",
        "A knot tightens when the loops are pulled against each other. Careful loosening works better than yanking."
    )],
    "grownup_help": [(
        "Why is it smart to get a grown-up for a tricky sharp job?",
        "A grown-up can use the right tool, keep everyone back, and solve the problem safely. Asking for help is part of being brave."
    )],
    "shears": [(
        "What are long-handled shears?",
        "Long-handled shears are cutting tools with long grips. They let a grown-up cut plants while keeping hands farther from the sharp part."
    )],
    "gloves": [(
        "Why do gloves help with thorns or rough plants?",
        "Gloves protect your skin from scratches and pokes. They also help a grown-up hold rough branches more safely."
    )],
    "untangle": [(
        "What does untangle mean?",
        "Untangle means to loosen something carefully so the loops come apart. It is slower than yanking, but often safer and better."
    )],
    "pole": [(
        "What is a hook pole used for?",
        "A hook pole lets someone lift or pull something from farther away. That can help when a grown-up needs more reach."
    )],
}
KNOWLEDGE_ORDER = [
    "knifer", "sharp_tool", "plants", "rope", "grownup_help", "shears",
    "gloves", "untangle", "pole"
]


def pair_noun(leader: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and partner.type == "boy":
            return "two brothers"
        if leader.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    expedition = f["expedition"]
    obstacle = f["obstacle_cfg"]
    prize = f["prize_cfg"]
    leader = f["leader"]
    partner = f["partner"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "knifer" '
        f"and uses inner monologue. Two children find {prize.phrase} on {expedition.place}, but it is caught in {obstacle.the}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle adventure where {leader.label} wants to use a knifer but listens to {partner.label}, and a ranger helps safely instead.",
            'Write a story with inner thoughts like "Maybe I can do it myself" and "Being brave can mean stopping," ending with a wiser adventure.'
        ]
    if outcome == "stalled":
        return [
            base,
            f"Tell a cautionary adventure where {leader.label} acts on a fast inner thought, gets a small nick, and the treasure is left behind while the children learn a safety lesson.",
            'Write a story where inner monologue shows the difference between wanting to be first and choosing what keeps everyone safe.'
        ]
    return [
        base,
        f"Tell a simple adventure where {leader.label} ignores a warning, tries the knifer, and then a ranger frees the treasure the right way.",
        'Write a child-facing story with inner monologue, a risky choice, calm grown-up help, and an ending image that shows the children have changed.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    expedition = f["expedition"]
    obstacle = f["obstacle_cfg"]
    prize = f["prize_cfg"]
    tool = f["tool_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(leader, partner, relation)
    leader_name = leader.label
    partner_name = partner.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader_name} and {partner_name}, on an adventure with a ranger nearby. They were following a map and looking for {prize.phrase}."
        ),
        (
            "What problem did the children find?",
            f"They found {prize.phrase}, but it was stuck in {obstacle.the}. That snag is what made the quick knifer idea seem tempting."
        ),
        (
            f"What was {leader_name} thinking to {leader.pronoun('object')}self?",
            f"{leader_name} thought that {leader.pronoun()} might free the prize alone with the knifer and finish the adventure quickly. The inner thought shows how being eager can race ahead of safer choices."
        ),
        (
            f"Why did {partner_name} warn {leader_name}?",
            f"{partner_name} warned {leader_name} because the snag was twisty and a sharp tool could slip. {partner_name} was trying to stop a small treasure problem from turning into an injury."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Why did {leader_name} stop before using the knifer?",
            f"{leader_name} listened to {partner_name} and realized that being brave did not mean being first. That change happened inside the adventure, in {leader.pronoun('possessive')} own thoughts, before anyone got hurt."
        ))
        qa.append((
            "How was the problem solved?",
            f"The ranger solved it safely and freed the prize. The children learned that asking for the right help can keep an adventure moving without turning it dangerous."
        ))
    elif f["outcome"] == "resolved":
        body = response.qa_text.replace("{target}", obstacle.label).replace("{obstacle}", obstacle.label).replace("{prize}", prize.label)
        qa.append((
            f"What happened when {leader_name} tried the knifer?",
            f"The sharp edge slipped, and {leader_name} got a small nick on {leader.pronoun('possessive')} finger. The prize also stayed stuck, so the risky shortcut did not solve the real problem."
        ))
        qa.append((
            "How did the ranger help?",
            f"The ranger {body}. That worked because a grown-up used the right method for the kind of snag the children had found."
        ))
        qa.append((
            "What did the ending show had changed?",
            f"The children kept adventuring, but more wisely than before. The final image of them carrying the treasure carefully shows they had learned to slow down and ask for help."
        ))
    else:
        qa.append((
            f"Did the quick knifer idea work?",
            f"No. {leader_name} got a small nick, and the prize was still not free. The failed shortcut showed that a fast idea is not always a good adventure plan."
        ))
        qa.append((
            "How did the story end?",
            f"They went back safely without the prize. The ending is sadder, but it proves the lesson mattered more than winning the treasure."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool_cfg"].tags) | set(f["obstacle_cfg"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["response"].tags)
    else:
        tags |= {"grownup_help", "shears", "gloves"}
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("cuttable", e.cuttable), ("sharp", e.sharp)) if on]
        if flags:
            bits.append(f"flags={flags}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({label:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        expedition="trail",
        obstacle="vine",
        prize="token",
        tool="knifer",
        response="shears",
        leader_name="Nia",
        leader_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        ranger_type="ranger_f",
        trait="careful",
        delay=0,
        leader_age=5,
        partner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        expedition="marsh",
        obstacle="net",
        prize="badge",
        tool="knifer",
        response="untangle",
        leader_name="Leo",
        leader_gender="boy",
        partner_name="Mila",
        partner_gender="girl",
        ranger_type="ranger_m",
        trait="thoughtful",
        delay=0,
        leader_age=6,
        partner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        expedition="cove",
        obstacle="bramble",
        prize="shell",
        tool="knifer",
        response="pole",
        leader_name="Ava",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        ranger_type="ranger_f",
        trait="brisk",
        delay=1,
        leader_age=7,
        partner_age=6,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        expedition="trail",
        obstacle="bramble",
        prize="badge",
        tool="knifer",
        response="shears",
        leader_name="Kai",
        leader_gender="boy",
        partner_name="Lila",
        partner_gender="girl",
        ranger_type="ranger_m",
        trait="steady",
        delay=0,
        leader_age=7,
        partner_age=5,
        relation="friends",
        trust=6,
    ),
]


def explain_rejection(obstacle: Obstacle) -> str:
    if not obstacle.cuttable:
        return (
            f"(No story: {obstacle.the} cannot be solved by cutting, so a knifer is the wrong kind of temptation. "
            f"Pick a vine, net, or bramble snag instead.)"
        )
    return "(No story: this combination has no reasonable sharp-tool problem.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a safer grown-up method such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.leader_age, params.partner_age, params.trait):
        return "averted"
    return "resolved" if is_resolved(RESPONSES[params.response], OBSTACLES[params.obstacle], params.delay) else "stalled"


ASP_RULES = r"""
hazard(O) :- obstacle(O), cuttable(O).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(E,O,P) :- expedition(E), prize(P), hazard(O).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), leader_age(LA), partner_age(PA), PA > LA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), boldness_init(B), A > B.

severity(Sp + D) :- chosen_obstacle(O), spread(O,Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R,P).
resolved :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(resolved) :- not averted, resolved.
outcome(stalled) :- not averted, not resolved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for eid in EXPEDITIONS:
        lines.append(asp.fact("expedition", eid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        if obstacle.cuttable:
            lines.append(asp.fact("cuttable", oid))
        lines.append(asp.fact("spread", oid, obstacle.spread))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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

    scenario = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("leader_age", params.leader_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld with inner monologue and a risky knifer choice."
    )
    ap.add_argument("--expedition", choices=EXPEDITIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--ranger", choices=["ranger_f", "ranger_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the snag has to tighten before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (expedition, obstacle, prize) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a generation smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and not OBSTACLES[args.obstacle].cuttable:
        raise StoryError(explain_rejection(OBSTACLES[args.obstacle]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.expedition is None or combo[0] == args.expedition)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    expedition, obstacle, prize = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    leader_name, leader_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=leader_name)
    ranger_type = args.ranger or rng.choice(["ranger_f", "ranger_m"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    leader_age, partner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        expedition=expedition,
        obstacle=obstacle,
        prize=prize,
        tool="knifer",
        response=response,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        ranger_type=ranger_type,
        trait=trait,
        delay=delay,
        leader_age=leader_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.expedition not in EXPEDITIONS:
        raise StoryError(f"(Unknown expedition: {params.expedition})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.ranger_type not in {"ranger_f", "ranger_m"}:
        raise StoryError(f"(Unknown ranger type: {params.ranger_type})")
    if not OBSTACLES[params.obstacle].cuttable:
        raise StoryError(explain_rejection(OBSTACLES[params.obstacle]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        expedition=EXPEDITIONS[params.expedition],
        obstacle=OBSTACLES[params.obstacle],
        prize=PRIZES[params.prize],
        tool=TOOLS[params.tool],
        response=RESPONSES[params.response],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        trait=params.trait,
        ranger_type=params.ranger_type,
        delay=params.delay,
        leader_age=params.leader_age,
        partner_age=params.partner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (expedition, obstacle, prize) combos:\n")
        for expedition, obstacle, prize in combos:
            print(f"  {expedition:10} {obstacle:8} {prize}")
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
            header = (
                f"### {p.leader_name} & {p.partner_name}: {p.prize} at {p.obstacle} "
                f"({p.expedition}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
