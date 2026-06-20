#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py
========================================================

A standalone story world for a small fable domain built from the seed words
"macho", Surprise, and Rhyme.

Premise
-------
A boastful animal wants to prove how macho and strong it is when a path to
something good is blocked. A wiser friend predicts that brute force will fail.
Then a tiny, surprising helper reveals the right trick: not more pushing, but a
matched tool used with care. The ending closes with a short rhyming moral.

This world prefers a few strong, common-sense variants over wide coverage:
different places, obstacles, and correct tools can vary, but the lesson stays
coherent: size and swagger are not the same as wisdom.

Run it
------
    python storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py
    python storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py --place spring --obstacle stone --tool lever
    python storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py --obstacle stone --tool rope
    python storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py --all
    python storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/macho_surprise_rhyme_fable.py --verify
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

# Make storyworlds/results.py importable when run directly from this nested dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    tiny: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    scene: str
    goal: str
    afford_obstacles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    the: str
    blocks: str
    weight: int
    material: str
    needs: str
    fail_text: str
    success_text: str
    reveal_text: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    works_for: set[str]
    helper: str
    helper_intro: str
    helper_line: str
    success_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    species: str
    title: str
    boast_verb: str
    move_verb: str
    traits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Temper:
    id: str
    label: str
    patience: int
    listening: int
    flavor: str
    rhyme: str
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    boaster = world.get("boaster")
    if boaster.meters["fatigue"] >= THRESHOLD:
        sig = ("tired", "boaster")
        if sig not in world.fired:
            world.fired.add(sig)
            boaster.memes["frustration"] += 1
            out.append("__tired__")
    return out


def _r_open_path(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["moved"] >= THRESHOLD:
        sig = ("open", "path")
        if sig not in world.fired:
            world.fired.add(sig)
            path = world.get("path")
            path.meters["open"] += 1
            for eid in ("boaster", "friend", "helper"):
                if eid in world.entities:
                    world.get(eid).memes["relief"] += 1
                    world.get(eid).memes["joy"] += 1
            out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule("tired", "physical", _r_tired),
    Rule("open_path", "physical", _r_open_path),
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


def valid_combo(place: Place, obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in place.afford_obstacles and obstacle.id in tool.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for oid, obstacle in OBSTACLES.items():
            for tid, tool in TOOLS.items():
                if valid_combo(place, obstacle, tool):
                    out.append((pid, oid, tid))
    return out


LISTENING_MIN = 5


def listens_before_strain(temper: Temper) -> bool:
    return temper.listening >= LISTENING_MIN


def explain_rejection(place: Place, obstacle: Obstacle, tool: Tool) -> str:
    if obstacle.id not in place.afford_obstacles:
        return (
            f"(No story: {obstacle.the} does not belong in {place.label}. "
            f"That place does not afford this blocked-path problem.)"
        )
    return (
        f"(No story: {tool.label} is not the right trick for {obstacle.the}. "
        f"This fable only tells matched problem-and-fix pairs, so the tool must "
        f"fit the obstacle.)"
    )


def predict_shove(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    boaster = sim.get("boaster")
    do_shove(sim, boaster, obstacle, narrate=False)
    return {
        "moved": sim.get("obstacle").meters["moved"] >= THRESHOLD,
        "fatigue": sim.get("boaster").meters["fatigue"],
    }


def do_shove(world: World, boaster: Entity, obstacle: Obstacle, narrate: bool = True) -> None:
    boaster.meters["effort"] += 1
    boaster.meters["fatigue"] += 1
    if boaster.meters["strength"] >= obstacle.weight + 1:
        world.get("obstacle").meters["moved"] += 1
    propagate(world, narrate=narrate)


def do_tool(world: World, tool: Tool, obstacle: Obstacle) -> None:
    helper = world.get("helper")
    helper.memes["clever"] += 1
    world.get("obstacle").meters["moved"] += 1
    world.get("obstacle").meters["loosened"] += 1
    propagate(world, narrate=False)


def introduce(world: World, boaster: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"In {place.scene}, {boaster.id} the {boaster.type} loved to walk with "
        f"{friend.id} the {friend.type}."
    )
    world.say(
        f"They were on the way to {place.goal}, and the morning smelled bright and clean."
    )


def reveal_problem(world: World, obstacle: Obstacle, place: Place) -> None:
    world.say(
        f"But {obstacle.the} lay across the way and blocked {obstacle.blocks}."
    )
    world.say(
        f"Until it moved, nobody could reach {place.goal}."
    )


def macho_boast(world: World, boaster: Entity, temper: Temper, obstacle: Obstacle) -> None:
    boaster.memes["pride"] += 1
    world.say(
        f'{boaster.id} puffed up {boaster.pronoun("possessive")} chest. '
        f'"I am too macho for little tricks," {boaster.pronoun()} said. '
        f'"{temper.rhyme}"'
    )
    world.say(
        f"With a grand snort, {boaster.pronoun()} planted {boaster.pronoun('possessive')} feet beside {obstacle.the}."
    )


def warn(world: World, friend: Entity, boaster: Entity, obstacle: Obstacle, tool: Tool) -> None:
    pred = predict_shove(world, OBSTACLES[obstacle.id])
    friend.memes["care"] += 1
    world.facts["predicted_fatigue"] = pred["fatigue"]
    world.say(
        f'{friend.id} tilted {friend.pronoun("possessive")} head. '
        f'"Big muscles are fine," {friend.pronoun()} said, '
        f'"but shoving {obstacle.the} will only make you tired. '
        f'What we need is {tool.phrase}."'
    )


def pause_and_listen(world: World, boaster: Entity, friend: Entity) -> None:
    boaster.memes["pride"] -= 0.2
    boaster.memes["trust"] += 1
    world.say(
        f"{boaster.id} frowned, then stopped before the first hard shove."
    )
    world.say(
        f"For once, {boaster.pronoun()} listened to {friend.id} instead of to the noisy drum of {boaster.pronoun('possessive')} own pride."
    )


def strain_and_fail(world: World, boaster: Entity, obstacle: Obstacle) -> None:
    do_shove(world, boaster, obstacle)
    world.say(
        obstacle.fail_text.format(name=boaster.id, pron=boaster.pronoun("subject"))
    )
    if boaster.memes["frustration"] >= THRESHOLD:
        world.say(
            f"Soon {boaster.pronoun()} was breathing hard, and the path was still closed."
        )


def surprise_helper(world: World, tool: Tool) -> None:
    helper = world.get("helper")
    helper.memes["surprise"] += 1
    world.say(tool.helper_intro.format(helper=helper.id))
    world.say(f'"{tool.helper_line}"')


def solve(world: World, boaster: Entity, friend: Entity, helper: Entity,
          obstacle: Obstacle, tool: Tool) -> None:
    do_tool(world, tool, obstacle)
    boaster.memes["gratitude"] += 1
    boaster.memes["lesson"] += 1
    friend.memes["joy"] += 1
    world.say(
        obstacle.reveal_text.format(helper=helper.id, tool=tool.label)
    )
    world.say(
        tool.success_line.format(
            boaster=boaster.id,
            friend=friend.id,
            helper=helper.id,
            obstacle=obstacle.label,
        )
    )
    world.say(obstacle.success_text)


def ending(world: World, boaster: Entity, helper: Entity, place: Place, temper: Temper,
           listened_early: bool) -> None:
    if listened_early:
        world.say(
            f"{boaster.id} bowed to {helper.id}, then to {helper.pronoun('possessive')} friend."
        )
        world.say(
            f'"A quiet thought can beat a loud snout," {boaster.pronoun()} said.'
        )
    else:
        boaster.memes["humility"] += 1
        world.say(
            f"{boaster.id} rubbed {boaster.pronoun('possessive')} sore shoulders and looked at the tiny helper with wide eyes."
        )
        world.say(
            f'"I called myself macho," {boaster.pronoun()} murmured, '
            f'"but wisdom moved what bragging could not."'
        )
    world.say(
        f"Then the three friends went on to {place.goal}, and the whole path seemed kinder than before."
    )
    world.say(
        "And this was the rhyme they remembered after that: "
        '"When pride says, \'Push!\' and wits say, \'Try,\' the smallest guide may show you why."'
    )


def tell(place: Place, obstacle: Obstacle, tool: Tool, boaster_cfg: Animal,
         friend_cfg: Animal, temper: Temper) -> World:
    world = World(place)
    boaster = world.add(Entity(
        id=boaster_cfg.id, kind="character", type=boaster_cfg.species,
        role="boaster", label=boaster_cfg.species, traits=sorted(boaster_cfg.traits),
    ))
    friend = world.add(Entity(
        id=friend_cfg.id, kind="character", type=friend_cfg.species,
        role="friend", label=friend_cfg.species, traits=sorted(friend_cfg.traits),
    ))
    helper = world.add(Entity(
        id=tool.helper, kind="character", type=tool.helper,
        role="helper", label=tool.helper, tiny=True, traits=["small", "clever"],
    ))
    world.add(Entity(id="obstacle", type="obstacle", label=obstacle.label))
    world.add(Entity(id="path", type="path", label="the path"))

    boaster.meters["strength"] = float(ANIMAL_STRENGTH.get(boaster_cfg.species, 2))
    friend.meters["steadiness"] = 1.0
    helper.meters["smallness"] = 1.0

    introduce(world, boaster, friend, place)
    reveal_problem(world, obstacle, place)

    world.para()
    macho_boast(world, boaster, temper, obstacle)
    warn(world, friend, boaster, obstacle, tool)

    listened_early = listens_before_strain(temper)
    if listened_early:
        world.para()
        pause_and_listen(world, boaster, friend)
        surprise_helper(world, tool)
        solve(world, boaster, friend, helper, obstacle, tool)
    else:
        world.para()
        strain_and_fail(world, boaster, obstacle)
        surprise_helper(world, tool)
        solve(world, boaster, friend, helper, obstacle, tool)

    world.para()
    ending(world, boaster, helper, place, temper, listened_early)

    outcome = "early" if listened_early else "humbled"
    world.facts.update(
        place=place,
        obstacle_cfg=obstacle,
        tool=tool,
        boaster=boaster,
        friend=friend,
        helper=helper,
        temper=temper,
        outcome=outcome,
        path_open=world.get("path").meters["open"] >= THRESHOLD,
        obstacle_moved=world.get("obstacle").meters["moved"] >= THRESHOLD,
        tired=boaster.meters["fatigue"] >= THRESHOLD,
    )
    return world


PLACES = {
    "spring": Place(
        "spring",
        "the spring path",
        "a green path beside a bubbling spring",
        "the cool water",
        {"stone"},
        tags={"spring", "water"},
    ),
    "bridge": Place(
        "bridge",
        "the berry bridge",
        "a little bridge above a slow stream",
        "the berry patch",
        {"log"},
        tags={"bridge", "berries"},
    ),
    "garden": Place(
        "garden",
        "the melon gate",
        "a warm garden path by a wooden gate",
        "the sweet melons",
        {"cart"},
        tags={"garden", "melons"},
    ),
}

OBSTACLES = {
    "stone": Obstacle(
        "stone",
        "round stone",
        "the round stone",
        "the narrow way to the spring",
        4,
        "stone",
        "lever",
        "{name} shoved until dust puffed around {pron} paws, but the stone only gave a sleepy wobble.",
        "The stone rolled aside, and cool water flashed in the sun.",
        "At the edge of a fern, {helper} pointed to a long stick tucked under the grass. It was just right for a {tool}.",
        tags={"stone", "heavy"},
    ),
    "log": Obstacle(
        "log",
        "fallen log",
        "the fallen log",
        "the little bridge to the berries",
        3,
        "wood",
        "roller",
        "{name} pushed and huffed, but the log only bumped back and pinned the bridge as before.",
        "The log rolled away from the bridge, and the berry patch shone red on the far side.",
        "From beneath a leaf, {helper} tapped three smooth reeds lying by the bank. They were perfect little rollers.",
        tags={"log", "bridge"},
    ),
    "cart": Obstacle(
        "cart",
        "stuck cart",
        "the stuck cart",
        "the gate to the melons",
        3,
        "wood",
        "rope",
        "{name} leaned and grunted, but the cart wheels were wedged in the ruts and would not budge.",
        "The cart slid free of the ruts, and the melon gate swung open.",
        "On a low branch, {helper} showed a strong vine hanging in a loop. It was just the right thing to use as a {tool}.",
        tags={"cart", "gate"},
    ),
}

TOOLS = {
    "lever": Tool(
        "lever",
        "lever stick",
        "a long lever stick",
        "pry",
        {"stone"},
        "Mouse",
        "Just then, out popped {helper}, no bigger than a curl of bark.",
        "Tip it, don't hit it. A smart lift is stronger than a sore shoulder.",
        "{helper} showed where to place the stick, {friend} pressed down, and {boaster} guided the stone until it rolled free.",
        tags={"lever", "tool"},
    ),
    "roller": Tool(
        "roller",
        "reed rollers",
        "three smooth reed rollers",
        "roll",
        {"log"},
        "Beetle",
        "Then, with a tiny buzz, {helper} climbed onto the log as if it were a hill.",
        "Round things like rolling. Give the log little wheels, and it will move itself.",
        "{helper} nudged the reeds into place, {friend} steadied them, and {boaster} pushed once more. This time the log rolled away.",
        tags={"roller", "tool"},
    ),
    "rope": Tool(
        "rope",
        "vine rope",
        "a loop of vine rope",
        "pull",
        {"cart"},
        "Wren",
        "All at once, {helper} fluttered down from the gatepost with bright eyes.",
        "Pull from the side, not from the pride. A good loop beats a mighty shove.",
        "{helper} showed how to loop the vine, {friend} held the gate clear, and {boaster} pulled from the side until the cart slid free.",
        tags={"rope", "tool"},
    ),
}

BOASTERS = {
    "Boar": Animal("Boar", "boar", "Mr.", "snorted", "shoved", {"bold"}, {"boar"}),
    "Goat": Animal("Goat", "goat", "Mr.", "stamped", "pushed", {"showy"}, {"goat"}),
    "Ram": Animal("Ram", "ram", "Mr.", "huffed", "butted", {"proud"}, {"ram"}),
}

FRIENDS = {
    "Mole": Animal("Mole", "mole", "the", "murmured", "guided", {"steady"}, {"mole"}),
    "Tortoise": Animal("Tortoise", "tortoise", "the", "said", "steadied", {"patient"}, {"tortoise"}),
    "Duck": Animal("Duck", "duck", "the", "quacked", "watched", {"calm"}, {"duck"}),
}

TEMPERAMENTS = {
    "stubborn": Temper(
        "stubborn", "stubborn", 2, 2,
        "all shove and no pause",
        "Macho and mighty, macho and grand! I'll move this trouble with one bold stand!",
        {"stubborn"},
    ),
    "showy": Temper(
        "showy", "showy", 3, 4,
        "more noise than thought",
        "Macho and speedy, macho and bright! I'll push this thing before lunchtime light!",
        {"showy"},
    ),
    "steady": Temper(
        "steady", "steady", 6, 6,
        "able to stop and think",
        "Macho can wait and wisdom can steer; strength is best when sense is near.",
        {"steady"},
    ),
    "thoughtful": Temper(
        "thoughtful", "thoughtful", 7, 7,
        "proud but teachable",
        "Macho is nothing if reason is small; the best strong heart can listen to all.",
        {"thoughtful"},
    ),
}

ANIMAL_STRENGTH = {
    "boar": 3,
    "goat": 3,
    "ram": 3,
    "mole": 1,
    "tortoise": 1,
    "duck": 1,
    "Mouse": 0,
    "Beetle": 0,
    "Wren": 0,
}


def outcome_of(params: "StoryParams") -> str:
    return "early" if listens_before_strain(TEMPERAMENTS[params.temper]) else "humbled"


@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    boaster: str
    friend: str
    temper: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "lever": [(
        "What does a lever do?",
        "A lever helps lift or move something heavy by using a long stick or bar. "
        "It lets a small push do a bigger job."
    )],
    "roller": [(
        "Why do rollers help move a log?",
        "Rollers let the log turn instead of scrape. Rolling takes less force than dragging."
    )],
    "rope": [(
        "Why can a rope help move a stuck cart?",
        "A rope lets you pull from a better angle and keep your feet away from the wheels. "
        "That can free the cart more safely than only shoving."
    )],
    "pride": [(
        "Why can pride cause trouble?",
        "Pride can make someone ignore good advice because they want to look strong. "
        "When that happens, they may choose showing off over solving the problem."
    )],
    "helper": [(
        "Can a small animal help with a big problem?",
        "Yes. A tiny helper may notice the right trick, tool, or place to stand. "
        "Wisdom is not measured only by size."
    )],
    "spring": [(
        "Why do animals like a spring?",
        "A spring gives fresh water, and fresh water helps animals drink and stay cool."
    )],
    "bridge": [(
        "Why is a blocked bridge a problem?",
        "A bridge is a safe way to cross. If it is blocked, getting to the other side becomes hard."
    )],
    "garden": [(
        "What grows in a garden?",
        "A garden can grow fruits and vegetables with sun, soil, and water."
    )],
}
KNOWLEDGE_ORDER = ["pride", "helper", "lever", "roller", "rope", "spring", "bridge", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool"]
    boaster = f["boaster"]
    friend = f["friend"]
    outcome = f["outcome"]
    if outcome == "early":
        return [
            f'Write a short fable for a young child that includes the word "macho", a surprise tiny helper, and a rhyming moral.',
            f"Tell a fable where {boaster.id} the {boaster.type} wants to move {obstacle.the} to reach {place.goal}, but listens in time to {friend.id} and learns that the right tool matters.",
            f"Write a gentle rhyme-tinged animal story in which bragging almost takes over, yet wisdom wins before anyone gets hurt."
        ]
    return [
        f'Write a short fable for a young child that includes the word "macho", a surprise tiny helper, and a rhyming moral.',
        f"Tell a fable where {boaster.id} the {boaster.type} boasts too loudly, strains against {obstacle.the}, and is surprised when a tiny helper shows the right way to reach {place.goal}.",
        f"Write a child-facing animal story with a small twist: the strongest-looking character fails by force, while a tiny surprise helper solves the problem with {tool.label}."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    boaster = f["boaster"]
    friend = f["friend"]
    helper = f["helper"]
    place = f["place"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {boaster.id} the {boaster.type}, {friend.id} the {friend.type}, and a tiny helper named {helper.id}. "
            f"They wanted to get past {obstacle.the} to reach {place.goal}."
        ),
        (
            f"What was blocking the way?",
            f"{obstacle.The} was blocking {obstacle.blocks}. Until it moved, the animals could not reach {place.goal}."
        ),
        (
            f"Why did {friend.id} warn {boaster.id} not to keep shoving?",
            f"{friend.id} could tell that brute force would only make {boaster.id} tired. "
            f"The obstacle needed {tool.phrase}, not just more pride."
        ),
    ]
    if outcome == "early":
        qa.append((
            f"What surprise changed the story?",
            f"A tiny helper, {helper.id}, suddenly appeared and showed them the right tool. "
            f"That surprise turned the story from bragging into teamwork before {boaster.id} wore {boaster.pronoun('object')}self out."
        ))
        qa.append((
            f"What did {boaster.id} learn?",
            f"{boaster.id} learned that listening early can be a kind of strength. "
            f"The path opened because {boaster.pronoun()} accepted a smart idea instead of trying to look macho."
        ))
    else:
        qa.append((
            f"What happened when {boaster.id} tried to move {obstacle.the} alone?",
            f"{boaster.id} strained and got tired, but the obstacle barely moved. "
            f"That failure proved that showing off was not the same as solving the problem."
        ))
        qa.append((
            f"How did the tiny helper solve the problem?",
            f"{helper.id} surprised everyone by showing them how to use {tool.phrase}. "
            f"With the right trick and a little teamwork, the obstacle moved and the path opened."
        ))
        qa.append((
            f"What did {boaster.id} learn at the end?",
            f"{boaster.id} learned that wisdom can come from a very small voice. "
            f"After bragging failed, {boaster.pronoun()} understood that pride without thought is weak."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"pride", "helper", f["tool"].id, f["place"].id}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tiny:
            bits.append("tiny=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("spring", "stone", "lever", "Boar", "Tortoise", "stubborn"),
    StoryParams("bridge", "log", "roller", "Goat", "Mole", "showy"),
    StoryParams("garden", "cart", "rope", "Ram", "Duck", "steady"),
    StoryParams("spring", "stone", "lever", "Goat", "Duck", "thoughtful"),
]


ASP_RULES = r"""
% --- problem/solution compatibility gate -----------------------------------
valid(P, O, T) :- place(P), obstacle(O), tool(T), affords(P, O), works_for(T, O).

% --- outcome model ----------------------------------------------------------
early_listen :- temper(Tm), listening(Tm, L), listen_min(M), L >= M.
outcome(early)   :- early_listen.
outcome(humbled) :- not early_listen.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for oid in sorted(place.afford_obstacles):
            lines.append(asp.fact("affords", pid, oid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for oid in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tid, oid))
    for temper_id, temper in TEMPERAMENTS.items():
        lines.append(asp.fact("temper_kind", temper_id))
        lines.append(asp.fact("listening", temper_id, temper.listening))
    lines.append(asp.fact("listen_min", LISTENING_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("temper", params.temper)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a macho boast, a surprise helper, and a rhyming fable ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--boaster", choices=BOASTERS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--temper", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.tool:
        if not valid_combo(PLACES[args.place], OBSTACLES[args.obstacle], TOOLS[args.tool]):
            raise StoryError(explain_rejection(PLACES[args.place], OBSTACLES[args.obstacle], TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, tool = rng.choice(sorted(combos))
    boaster = args.boaster or rng.choice(sorted(BOASTERS))
    friend = args.friend or rng.choice(sorted(FRIENDS))
    temper = args.temper or rng.choice(sorted(TEMPERAMENTS))
    return StoryParams(place, obstacle, tool, boaster, friend, temper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        OBSTACLES[params.obstacle],
        TOOLS[params.tool],
        BOASTERS[params.boaster],
        FRIENDS[params.friend],
        TEMPERAMENTS[params.temper],
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
        print(f"{len(combos)} compatible (place, obstacle, tool) combos:\n")
        for place, obstacle, tool in combos:
            print(f"  {place:8} {obstacle:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.boaster}: {p.obstacle} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
