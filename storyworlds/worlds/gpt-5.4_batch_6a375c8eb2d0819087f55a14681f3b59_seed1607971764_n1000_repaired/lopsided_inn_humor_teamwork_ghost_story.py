#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py
=====================================================================

A standalone story world for a funny, child-facing ghost story set in a
lopsided inn. Two children hear a spooky sound, meet a flustered ghost who is
trying to warn everyone about the real cause, and solve the problem together.

The model prefers small, plausible haunt/fix pairs:
- a loose shutter can be tied
- a clanking sign can be tightened
- a moaning pipe can be wrapped
- a rattling dumbwaiter can be wedged

The story can end in two ways:
- settled: the team fixes the problem and the inn grows quiet
- rumpus: they try, but the chosen fix is too weak or too late, so the inn stays
  noisy until morning, though everyone remains safe

Run it
------
    python storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py
    python storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py --ghost bellhop --haunt sign
    python storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py --tool spoon
    python storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lopsided_inn_humor_teamwork_ghost_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class GhostKind:
    id: str
    label: str
    intro: str
    apology: str
    gag: str
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
class Haunt:
    id: str
    source: str
    location: str
    sound: str
    fix_tag: str
    severity: int
    clue: str
    success: str
    failure: str
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
    fix_tags: set[str]
    power: int
    sense: int
    action: str
    fail_action: str
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
        return [e for e in self.entities.values() if e.role in {"child_a", "child_b"}]

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


def _r_noise(world: World) -> list[str]:
    source = world.get("source")
    inn = world.get("inn")
    ghost = world.get("ghost")
    if source.meters["rattling"] < THRESHOLD or source.meters["fixed"] >= THRESHOLD:
        return []
    sig = ("noise", source.id, int(source.meters["rattling"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    inn.meters["noise"] += 1
    ghost.memes["embarrassed"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__noise__"]


def _r_team(world: World) -> list[str]:
    a = world.get("child_a")
    b = world.get("child_b")
    ghost = world.get("ghost")
    if a.memes["teamwork"] < THRESHOLD or b.memes["teamwork"] < THRESHOLD:
        return []
    sig = ("team",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["courage"] += 1
    b.memes["courage"] += 1
    ghost.memes["hope"] += 1
    return ["__team__"]


CAUSAL_RULES = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="team", tag="social", apply=_r_team),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def can_fix(haunt: Haunt, tool: Tool) -> bool:
    return haunt.fix_tag in tool.fix_tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ghost_id in GHOSTS:
        for haunt_id, haunt in HAUNTS.items():
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and can_fix(haunt, tool):
                    combos.append((ghost_id, haunt_id, tool_id))
    return combos


def disturbance(haunt: Haunt, delay: int) -> int:
    return haunt.severity + delay


def settles(haunt: Haunt, tool: Tool, delay: int) -> bool:
    return tool.power >= disturbance(haunt, delay)


def explain_tool_rejection(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it is too silly or weak for a careful fix "
        f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_combo_rejection(haunt: Haunt, tool: Tool) -> str:
    return (
        f"(No story: {tool.phrase} would not reasonably fix {haunt.source} at "
        f"{haunt.location}. Pick a tool that can really handle that problem.)"
    )


def predict_noise(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["rattling"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("inn").meters["noise"],
        "fear": sum(kid.memes["fear"] for kid in sim.kids()),
    }


def opening(world: World, a: Entity, b: Entity, caretaker: Entity) -> None:
    inn = world.get("inn")
    world.say(
        f"On a windy evening, {a.id} and {b.id} arrived with {caretaker.label_word} "
        f"at the Mooncup, a lopsided inn that leaned just enough to make the teacups "
        f"slide in tiny circles on the table."
    )
    world.say(
        f"The hall smelled of soup and candle wax, and the old floor gave a polite "
        f"crook of a creak under every step."
    )
    inn.meters["tilt"] = 1


def first_sound(world: World, a: Entity, b: Entity, haunt: Haunt) -> None:
    source = world.get("source")
    source.meters["rattling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just as the children were deciding which bed squeaked less, a sound came "
        f"from {haunt.location}: {haunt.sound}."
    )
    world.say(
        f"{a.id} grabbed {b.id}'s sleeve. {b.id} listened hard, then whispered, "
        f'"That is either a ghost or the rudest furniture in the world."'
    )


def ghost_arrives(world: World, a: Entity, b: Entity, ghost_cfg: GhostKind, haunt: Haunt) -> None:
    ghost = world.get("ghost")
    ghost.memes["shy"] = 1
    world.say(
        f"A pale little shape drifted around the corner. It was {ghost_cfg.intro}. "
        f'"Boo," it said, then winced. "{ghost_cfg.apology}"'
    )
    world.say(
        f"Instead of rattling chains, the ghost pointed frantically toward {haunt.location}. "
        f"{ghost_cfg.gag}"
    )
    if sum(k.memes["fear"] for k in world.kids()) >= 2:
        world.say(
            f"{a.id} and {b.id} were scared, but the ghost looked more worried than wicked."
        )


def explain_problem(world: World, caretaker: Entity, haunt: Haunt) -> None:
    pred = predict_noise(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{caretaker.label_word.capitalize()} lifted the lamp and looked where the ghost was pointing. '
        f'"Oh," {caretaker.pronoun()} said. "{haunt.clue}"'
    )
    world.say(
        f"If nobody helped, the whole inn would keep waking itself up all night."
    )


def make_plan(world: World, a: Entity, b: Entity, ghost_cfg: GhostKind, tool: Tool) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.get("ghost").meme_factor = 0 if not hasattr(world.get("ghost"), "meme_factor") else world.get("ghost").meme_factor
    propagate(world, narrate=False)
    world.say(
        f'{a.id} held the lamp, {b.id} reached for {tool.phrase}, and the ghost floated beside them, '
        f'trying to look brave. "We do this together," {b.id} said.'
    )
    world.say(
        f'The ghost gave a tiny nod. "{ghost_cfg.apology} I mean... thank you," it whispered.'
    )


def fix_success(world: World, a: Entity, b: Entity, caretaker: Entity,
                ghost_cfg: GhostKind, haunt: Haunt, tool: Tool) -> None:
    source = world.get("source")
    inn = world.get("inn")
    ghost = world.get("ghost")
    source.meters["fixed"] = 1
    source.meters["rattling"] = 0
    inn.meters["noise"] = 0
    ghost.memes["gratitude"] += 1
    ghost.memes["joy"] += 1
    for kid in (a, b):
        kid.memes["fear"] = 0
        kid.memes["joy"] += 1
        kid.memes["courage"] += 1
    world.say(
        f"Together they {tool.action} {haunt.success}."
    )
    world.say(
        f"The dreadful noise stopped so suddenly that everyone could hear the inn settling "
        f"with one long, sleepy sigh."
    )
    world.say(
        f'The ghost blinked, then laughed a little see-through laugh. "{ghost_cfg.gag.split(".")[0]}," '
        f'{caretaker.label_word} said, and even {a.id} laughed.'
    )


def fix_failure(world: World, a: Entity, b: Entity, caretaker: Entity,
                haunt: Haunt, tool: Tool) -> None:
    source = world.get("source")
    inn = world.get("inn")
    source.meters["rattling"] += 1
    inn.meters["noise"] += 1
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"They tried to help, but {tool.fail_action}, and {haunt.failure}"
    )
    world.say(
        f"The whole lopsided inn answered with bangs and groans, as if it had decided to tell the joke louder."
    )
    world.say(
        f'{caretaker.label_word.capitalize()} herded everyone back from the noise and promised, '
        f'"We will fix it properly in the morning, with daylight and steadier hands."'
    )


def settled_ending(world: World, a: Entity, b: Entity, caretaker: Entity,
                   ghost_cfg: GhostKind, haunt: Haunt, tool: Tool) -> None:
    ghost = world.get("ghost")
    world.say(
        f"After that, the ghost did not have to wail anymore. It bowed to the children, "
        f"straightened its little cap, and floated to the front desk like the proudest helper in the inn."
    )
    world.say(
        f"{caretaker.label_word.capitalize()} tucked {a.id} and {b.id} into bed, and the quiet that followed "
        f"felt warm instead of spooky."
    )
    world.say(
        f"When the wind touched the windows again, {a.id} only smiled. In the Mooncup inn, the night's "
        f"ghost story ended with teamwork, one good laugh, and not a single extra clank."
    )
    world.facts["ending_image"] = (
        f"The ghost floated proudly through the quiet inn while {a.id} and {b.id} smiled in bed."
    )
    ghost.attrs["fixed_with"] = tool.label
    ghost.attrs["helped_place"] = haunt.location


def rumpus_ending(world: World, a: Entity, b: Entity, caretaker: Entity,
                  ghost_cfg: GhostKind, haunt: Haunt) -> None:
    ghost = world.get("ghost")
    ghost.memes["embarrassed"] += 1
    world.say(
        f"The ghost drooped like a wet napkin. Still, it floated beside the children while they all listened "
        f"to the racket together, and somehow that made the room feel less lonely."
    )
    world.say(
        f"{a.id} and {b.id} did not sleep much, but they stayed shoulder to shoulder and counted the bangs "
        f"in whispers until morning."
    )
    world.say(
        f"When dawn finally came, the pale ghost gave them a grateful wave. Even in a noisy inn, teamwork had "
        f"turned a frightening night into a friendly one."
    )
    world.facts["ending_image"] = (
        f"At dawn, the children and the ghost waved to one another over a still-rattling hall."
    )
    ghost.attrs["helped_place"] = haunt.location
    ghost.attrs["failed_fix"] = haunt.source


def tell(ghost_cfg: GhostKind, haunt: Haunt, tool: Tool,
         child1: str = "Nora", child1_gender: str = "girl",
         child2: str = "Theo", child2_gender: str = "boy",
         relation: str = "siblings", caretaker_type: str = "mother",
         trait1: str = "funny", trait2: str = "steady", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(
        id="child_a",
        kind="character",
        type=child1_gender,
        label=child1,
        role="child_a",
        traits=[trait1],
        attrs={"name": child1, "relation": relation},
    ))
    b = world.add(Entity(
        id="child_b",
        kind="character",
        type=child2_gender,
        label=child2,
        role="child_b",
        traits=[trait2],
        attrs={"name": child2, "relation": relation},
    ))
    caretaker = world.add(Entity(
        id="caretaker",
        kind="character",
        type=caretaker_type,
        label="the caretaker",
        role="caretaker",
        attrs={},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=ghost_cfg.label,
        role="ghost",
        attrs={"ghost_kind": ghost_cfg.id},
    ))
    inn = world.add(Entity(
        id="inn",
        kind="thing",
        type="inn",
        label="the Mooncup inn",
        role="place",
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="haunt_source",
        label=haunt.source,
        role="source",
        attrs={"location": haunt.location, "fix_tag": haunt.fix_tag},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        role="tool",
        attrs={"tool_id": tool.id},
    ))

    a.memes["humor"] = 1 if trait1 in {"funny", "playful", "cheerful"} else 0
    b.memes["humor"] = 1 if trait2 in {"funny", "playful", "cheerful"} else 0
    a.memes["courage"] = 1
    b.memes["courage"] = 1
    inn.meters["noise"] = 0
    source.meters["rattling"] = 0
    source.meters["fixed"] = 0
    world.facts["relation"] = relation
    world.facts["delay"] = delay

    opening(world, a, b, caretaker)
    first_sound(world, a, b, haunt)

    world.para()
    ghost_arrives(world, a, b, ghost_cfg, haunt)
    explain_problem(world, caretaker, haunt)

    world.para()
    make_plan(world, a, b, ghost_cfg, tool)
    world.facts["attempted_tool"] = tool.label
    world.facts["predicted_disturbance"] = disturbance(haunt, delay)

    if settles(haunt, tool, delay):
        fix_success(world, a, b, caretaker, ghost_cfg, haunt, tool)
        world.para()
        settled_ending(world, a, b, caretaker, ghost_cfg, haunt, tool)
        outcome = "settled"
    else:
        fix_failure(world, a, b, caretaker, haunt, tool)
        world.para()
        rumpus_ending(world, a, b, caretaker, ghost_cfg, haunt)
        outcome = "rumpus"

    world.facts.update(
        child_a=a,
        child_b=b,
        caretaker=caretaker,
        ghost=ghost,
        ghost_cfg=ghost_cfg,
        haunt=haunt,
        source=source,
        tool=tool,
        tool_entity=tool_ent,
        inn=inn,
        outcome=outcome,
        quiet=(outcome == "settled"),
    )
    return world


GHOSTS = {
    "bellhop": GhostKind(
        id="bellhop",
        label="a bellhop ghost",
        intro="a tiny bellhop ghost with a crooked cap and a silver luggage tag still pinned to its coat",
        apology="Sorry. I always mean to sound helpful, but it comes out as boo",
        gag="Every time it tried to whisper, its little desk bell gave a silly ding all by itself.",
        tags={"ghost", "inn", "bell"},
    ),
    "baker": GhostKind(
        id="baker",
        label="a baker ghost",
        intro="a round baker ghost dusted with flour, carrying a tray that passed straight through one transparent elbow",
        apology="Sorry. I was aiming for hush, not boo",
        gag="When it sneezed, a puff of ghost-flour swirled in the air like a tiny white cloud.",
        tags={"ghost", "baking", "inn"},
    ),
    "captain": GhostKind(
        id="captain",
        label="a captain ghost",
        intro="an old captain ghost in striped pajamas, pointing with an umbrella as if it were a sword",
        apology="Sorry. I keep trying to warn people in a dignified way",
        gag="Its umbrella saluted so hard that it turned in a slow, embarrassed circle.",
        tags={"ghost", "wind", "inn"},
    ),
}

HAUNTS = {
    "shutter": Haunt(
        id="shutter",
        source="the loose attic shutter",
        location="the attic landing",
        sound="BANG-bang... skreee",
        fix_tag="tie",
        severity=2,
        clue="the shutter cord has slipped loose again",
        success="around the shutter until it stopped smacking the wall",
        failure="the shutter banged even harder than before",
        tags={"wind", "shutter"},
    ),
    "sign": Haunt(
        id="sign",
        source="the hanging sign outside",
        location="the front porch",
        sound="CLANK... thunk... CLANK",
        fix_tag="tighten",
        severity=3,
        clue="the sign chain has shaken itself half loose",
        success="until the sign sat snug and only swayed softly",
        failure="the sign lurched sideways and clanged against the post",
        tags={"sign", "wind", "inn"},
    ),
    "pipe": Haunt(
        id="pipe",
        source="the old kitchen pipe",
        location="the kitchen wall",
        sound="OOOOooooh... honk",
        fix_tag="wrap",
        severity=1,
        clue="that pipe is singing because the cold air is slipping through a bare joint",
        success="around the pipe joint, and its ghostly song shrank to a sleepy hum",
        failure="the pipe gave an even louder moan that made the spoons tremble",
        tags={"pipe", "kitchen"},
    ),
    "dumbwaiter": Haunt(
        id="dumbwaiter",
        source="the rattling dumbwaiter",
        location="the service nook by the stairs",
        sound="clitter-clatter... bump",
        fix_tag="wedge",
        severity=2,
        clue="the little dumbwaiter box keeps wobbling in its track",
        success="under the wobbling box until it stood still",
        failure="the box rattled down and up again with a fresh series of bumps",
        tags={"stairs", "dumbwaiter", "inn"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        fix_tags={"tie"},
        power=2,
        sense=3,
        action="looped the rope carefully",
        fail_action="the rope slipped from their hands",
        tags={"rope", "fix"},
    ),
    "wrench": Tool(
        id="wrench",
        label="wrench",
        phrase="a stout wrench",
        fix_tags={"tighten"},
        power=3,
        sense=3,
        action="tightened the bolts with the wrench",
        fail_action="the wrench knocked once and skidded away",
        tags={"wrench", "fix", "metal"},
    ),
    "towel": Tool(
        id="towel",
        label="towel",
        phrase="a folded kitchen towel",
        fix_tags={"wrap"},
        power=1,
        sense=2,
        action="wrapped the towel snugly",
        fail_action="the towel sagged and slid loose",
        tags={"towel", "cloth", "kitchen"},
    ),
    "doorstop": Tool(
        id="doorstop",
        label="doorstop",
        phrase="a rubber doorstop",
        fix_tags={"wedge"},
        power=2,
        sense=3,
        action="pressed the doorstop firmly",
        fail_action="the doorstop popped free like a seed",
        tags={"doorstop", "fix"},
    ),
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a soup spoon",
        fix_tags=set(),
        power=0,
        sense=1,
        action="tapped at the trouble with a spoon",
        fail_action="the spoon only made an extra ping",
        tags={"spoon", "silly"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ada", "Zoe", "Iris", "Tessa", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Sam", "Leo", "Owen", "Finn"]
TRAITS = ["funny", "steady", "curious", "brave", "playful", "careful"]


@dataclass
class StoryParams:
    ghost: str
    haunt: str
    tool: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    relation: str
    caretaker: str
    trait1: str
    trait2: str
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
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is a spirit that people imagine can appear after someone is gone. In gentle ghost stories, the ghost is often lonely or trying to tell someone something."
        )
    ],
    "inn": [
        (
            "What is an inn?",
            "An inn is a house where travelers can sleep, eat, and rest for the night. It is like a small old hotel."
        )
    ],
    "wind": [
        (
            "Why can wind make spooky sounds?",
            "Wind pushes on shutters, signs, pipes, and other loose things. When they shake or whistle, the noises can sound spooky in the dark."
        )
    ],
    "shutter": [
        (
            "What does a shutter do?",
            "A shutter covers a window from the outside. If it gets loose, it can bang against the wall in the wind."
        )
    ],
    "sign": [
        (
            "Why would an inn have a sign?",
            "A sign helps travelers find the inn. If the chain gets loose, the sign can swing and clank."
        )
    ],
    "pipe": [
        (
            "Why can a pipe moan or whistle?",
            "Air moving through a loose place in a pipe can make a long humming sound. In the dark, that can seem ghostly even when it has an ordinary cause."
        )
    ],
    "dumbwaiter": [
        (
            "What is a dumbwaiter?",
            "A dumbwaiter is a little box lift inside a building that carries food or other things between floors. If it wobbles, it can rattle."
        )
    ],
    "rope": [
        (
            "What can a rope do?",
            "A rope can tie or hold something in place. It helps keep loose things from flapping or swinging."
        )
    ],
    "wrench": [
        (
            "What is a wrench for?",
            "A wrench helps turn nuts and bolts so something can be tightened. Grown-ups often use it for repairs."
        )
    ],
    "towel": [
        (
            "How can a towel help with a drafty pipe?",
            "A towel can be wrapped around a small chilly gap to soften a whistle for a while. It is only for a small problem, not a big repair."
        )
    ],
    "doorstop": [
        (
            "What does a doorstop do?",
            "A doorstop wedges under something so it will not slide or wobble. It can help hold a little moving thing still."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another and do different parts of the same job together. Working as a team can make a hard problem feel smaller."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "inn",
    "wind",
    "shutter",
    "sign",
    "pipe",
    "dumbwaiter",
    "rope",
    "wrench",
    "towel",
    "doorstop",
    "teamwork",
]


CURATED = [
    StoryParams(
        ghost="bellhop",
        haunt="shutter",
        tool="rope",
        child1="Nora",
        child1_gender="girl",
        child2="Theo",
        child2_gender="boy",
        relation="siblings",
        caretaker="mother",
        trait1="funny",
        trait2="steady",
        delay=0,
    ),
    StoryParams(
        ghost="baker",
        haunt="pipe",
        tool="towel",
        child1="Mina",
        child1_gender="girl",
        child2="Eli",
        child2_gender="boy",
        relation="friends",
        caretaker="father",
        trait1="careful",
        trait2="playful",
        delay=0,
    ),
    StoryParams(
        ghost="captain",
        haunt="sign",
        tool="wrench",
        child1="Ada",
        child1_gender="girl",
        child2="Max",
        child2_gender="boy",
        relation="siblings",
        caretaker="father",
        trait1="brave",
        trait2="funny",
        delay=0,
    ),
    StoryParams(
        ghost="bellhop",
        haunt="dumbwaiter",
        tool="doorstop",
        child1="Iris",
        child1_gender="girl",
        child2="Leo",
        child2_gender="boy",
        relation="friends",
        caretaker="mother",
        trait1="curious",
        trait2="steady",
        delay=1,
    ),
    StoryParams(
        ghost="captain",
        haunt="sign",
        tool="wrench",
        child1="Tessa",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
        relation="siblings",
        caretaker="mother",
        trait1="funny",
        trait2="careful",
        delay=1,
    ),
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    ghost_cfg = f["ghost_cfg"]
    haunt = f["haunt"]
    tool = f["tool"]
    outcome = f["outcome"]
    names = f'{a.label} and {b.label}'
    base = (
        f'Write a short ghost story for a 3-to-5-year-old set in a lopsided inn. '
        f'Use humor and teamwork, and include a friendly {ghost_cfg.label}.'
    )
    if outcome == "settled":
        return [
            base,
            f"Tell a gentle ghost story where {names} hear {haunt.sound} at night, discover a worried ghost, and use {tool.phrase} to help fix the real problem together.",
            f'Write a funny spooky story in which a ghost seems scary at first but is really trying to ask for help, and the ending becomes warm and quiet.'
        ]
    return [
        base,
        f"Tell a child-friendly ghost story where {names} bravely try to help a flustered ghost with {tool.phrase}, but the noisy problem is still too big to settle before morning.",
        f'Write a spooky-but-safe story with teamwork and jokes, where the children do not solve the noise right away but become friends with the ghost by dawn.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    caretaker = f["caretaker"]
    ghost_cfg = f["ghost_cfg"]
    haunt = f["haunt"]
    tool = f["tool"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, a worried {ghost_cfg.label}, and their {caretaker.label_word} at the old inn."
        ),
        (
            "Why did the noise seem like a ghost at first?",
            f"The sound came suddenly in the dark and echoed through the lopsided inn, so it felt spooky right away. The children did not yet know that the ghost was pointing to a real noisy problem."
        ),
        (
            "What was the ghost really trying to do?",
            f"The ghost was trying to warn everyone about {haunt.source} at {haunt.location}. It looked spooky, but it was really asking for help before the noise kept the whole inn awake."
        ),
        (
            "How did the children show teamwork?",
            f"They stayed together, listened to the ghost, and carried out different parts of the plan with {tool.label}. Working together made them braver than they felt when the first sound came."
        ),
    ]
    if f["outcome"] == "settled":
        qa.append(
            (
                "How did they stop the haunting sound?",
                f"They used {tool.phrase} to fix the trouble at {haunt.location}, and the sound finally stopped. Once the real cause was fixed, the inn grew quiet and the ghost no longer needed to boo for help."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a warm, peaceful picture: the inn was quiet, the ghost was proud instead of worried, and the children could smile at the dark. The ending shows that the scary mystery changed into a friendly one."
            )
        )
    else:
        qa.append(
            (
                "Did the children solve the problem that night?",
                f"No. They tried to help, but the fix was too weak or the trouble had grown too noisy by then. Even so, staying together turned the frightening night into one they could bear."
            )
        )
        qa.append(
            (
                "How did the story still change for the better?",
                f"The noise went on, but the children were no longer alone with it. By morning they had become friends with the ghost, so the inn felt less scary even before the repair was finished."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "inn", "teamwork"}
    tags |= set(f["ghost_cfg"].tags)
    tags |= set(f["haunt"].tags)
    tags |= set(f["tool"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
can_fix(H, T)    :- haunt(H), tool(T), needs(H, Need), fixes(T, Need).
valid(G, H, T)   :- ghost(G), haunt(H), sensible_tool(T), can_fix(H, T).

disturbance(V) :- chosen_haunt(H), severity(H, S), delay(D), V = S + D.
tool_power(P)  :- chosen_tool(T), power(T, P).

outcome(settled) :- disturbance(V), tool_power(P), P >= V.
outcome(rumpus)  :- disturbance(V), tool_power(P), P < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ghost_id in GHOSTS:
        lines.append(asp.fact("ghost", ghost_id))
    for haunt_id, haunt in HAUNTS.items():
        lines.append(asp.fact("haunt", haunt_id))
        lines.append(asp.fact("needs", haunt_id, haunt.fix_tag))
        lines.append(asp.fact("severity", haunt_id, haunt.severity))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        for tag in sorted(tool.fix_tags):
            lines.append(asp.fact("fixes", tool_id, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_haunt", params.haunt),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "settled" if settles(HAUNTS[params.haunt], TOOLS[params.tool], params.delay) else "rumpus"


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

    py_sensible = {tool.id for tool in sensible_tools()}
    asp_sensible = set(asp_sensible_tools())
    if py_sensible == asp_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny ghost story at a lopsided inn."
    )
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the noise goes on before the repair attempt")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid ghost/haunt/tool combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(args.tool))
    if args.haunt and args.tool:
        haunt = HAUNTS[args.haunt]
        tool = TOOLS[args.tool]
        if not can_fix(haunt, tool):
            raise StoryError(explain_combo_rejection(haunt, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.ghost is None or combo[0] == args.ghost)
        and (args.haunt is None or combo[1] == args.haunt)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ghost_id, haunt_id, tool_id = rng.choice(sorted(combos))
    child1, g1 = _pick_child(rng)
    child2, g2 = _pick_child(rng, avoid=child1)
    relation = rng.choice(["siblings", "friends"])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        ghost=ghost_id,
        haunt=haunt_id,
        tool=tool_id,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        relation=relation,
        caretaker=caretaker,
        trait1=trait1,
        trait2=trait2,
        delay=delay,
    )


def _require(mapping: dict, key: str, label: str):
    if key not in mapping:
        raise StoryError(f"(Unknown {label}: {key})")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    ghost_cfg = _require(GHOSTS, params.ghost, "ghost")
    haunt = _require(HAUNTS, params.haunt, "haunt")
    tool = _require(TOOLS, params.tool, "tool")

    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(params.tool))
    if not can_fix(haunt, tool):
        raise StoryError(explain_combo_rejection(haunt, tool))

    world = tell(
        ghost_cfg=ghost_cfg,
        haunt=haunt,
        tool=tool,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        relation=params.relation,
        caretaker_type=params.caretaker,
        trait1=params.trait1,
        trait2=params.trait2,
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible_tools()
        print(f"sensible tools: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ghost, haunt, tool) combos:\n")
        for ghost_id, haunt_id, tool_id in combos:
            print(f"  {ghost_id:8} {haunt_id:10} {tool_id}")
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
                f"### {p.child1} & {p.child2}: {p.ghost} / {p.haunt} / {p.tool} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
