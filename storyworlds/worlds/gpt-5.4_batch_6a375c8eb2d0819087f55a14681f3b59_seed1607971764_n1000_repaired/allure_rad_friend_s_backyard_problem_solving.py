#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py
===========================================================================

A standalone storyworld about two children in a friend's backyard who lose an
important plaything, disagree about a flashy idea, hit a twist when that idea
fails, and solve the problem with a better tool.

The domain is intentionally small and constraint-checked:

* A needed item is lost in a backyard spot.
* One child is pulled toward a shiny, "rad" tool because of its allure.
* That flashy tool must be a plausible temptation but a poor fit here.
* A calmer fix must actually match the item and the spot.
* The story ends by proving that careful problem solving beat the flashy guess.

Run it
------
    python storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py
    python storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py --item plane --spot pond
    python storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py --flashy bare_hands
    python storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/allure_rad_friend_s_backyard_problem_solving.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    game_need: str
    material: str
    flat: bool = False
    looped: bool = False
    soggy: bool = False
    bulky: bool = False
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
class SpotCfg:
    id: str
    label: str
    phrase: str
    reach: int
    watery: bool = False
    thorny: bool = False
    narrow: bool = False
    move_text: str = ""
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    magnet: bool = False
    hook: bool = False
    grab: bool = False
    scoop: bool = False
    water_ok: bool = False
    narrow_ok: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def flashy(self) -> bool:
        return self.id == "magnet_wand"
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
        return [e for e in self.entities.values() if e.role in {"impulsive", "careful"}]

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


def _r_wet_item(world: World) -> list[str]:
    item = world.get("item")
    spot = world.get("spot")
    if item.meters["lost"] < THRESHOLD:
        return []
    if not spot.attrs.get("watery") or not item.attrs.get("soggy"):
        return []
    sig = ("wet_item", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["wet"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__wet__"]


def _r_conflict(world: World) -> list[str]:
    a = world.get("a")
    b = world.get("b")
    if a.memes["pushes_idea"] < THRESHOLD or b.memes["objects"] < THRESHOLD:
        return []
    sig = ("conflict", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__conflict__"]


def _r_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wet_item", tag="physical", apply=_r_wet_item),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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


ITEMS = {
    "robot": ItemCfg(
        id="robot",
        label="robot",
        phrase="a little metal robot",
        game_need="their checkpoint guard for a backyard treasure game",
        material="metal",
        tags={"magnet", "robot", "metal"},
    ),
    "ring": ItemCfg(
        id="ring",
        label="ring toss ring",
        phrase="a bright plastic ring toss ring",
        game_need="the last ring for their game",
        material="plastic",
        looped=True,
        tags={"ring", "plastic"},
    ),
    "plane": ItemCfg(
        id="plane",
        label="paper airplane",
        phrase="a paper airplane with blue stripes",
        game_need="the plane they had been aiming at the chalk runway",
        material="paper",
        flat=True,
        soggy=True,
        tags={"paper_airplane", "paper"},
    ),
}

SPOTS = {
    "pond": SpotCfg(
        id="pond",
        label="pond",
        phrase="the little pond by the fence",
        reach=2,
        watery=True,
        move_text="slid onto the dark water and drifted against the reeds",
        tags={"pond", "water"},
    ),
    "rose_bush": SpotCfg(
        id="rose_bush",
        label="rose bush",
        phrase="the rose bush beside the shed",
        reach=1,
        thorny=True,
        move_text="skipped once and tucked itself under the thorny branches",
        tags={"rose_bush", "thorns"},
    ),
    "under_deck": SpotCfg(
        id="under_deck",
        label="deck",
        phrase="the space under the back deck",
        reach=2,
        narrow=True,
        move_text="bounced twice and disappeared between the narrow deck slats",
        tags={"deck", "narrow_space"},
    ),
}

TOOLS = {
    "magnet_wand": ToolCfg(
        id="magnet_wand",
        label="magnet wand",
        phrase="a shiny magnet wand from the toy box",
        sense=2,
        reach=2,
        magnet=True,
        water_ok=True,
        narrow_ok=True,
        tags={"magnet", "tool"},
    ),
    "grabber_claw": ToolCfg(
        id="grabber_claw",
        label="grabber claw",
        phrase="a long grabber claw from the garage shelf",
        sense=3,
        reach=2,
        grab=True,
        water_ok=True,
        narrow_ok=True,
        tags={"grabber", "tool"},
    ),
    "garden_rake": ToolCfg(
        id="garden_rake",
        label="garden rake",
        phrase="a little garden rake",
        sense=3,
        reach=2,
        hook=True,
        water_ok=False,
        narrow_ok=False,
        tags={"rake", "tool"},
    ),
    "pool_net": ToolCfg(
        id="pool_net",
        label="pool net",
        phrase="a pool net with a long handle",
        sense=3,
        reach=2,
        scoop=True,
        water_ok=True,
        narrow_ok=False,
        tags={"pool_net", "tool"},
    ),
    "bare_hands": ToolCfg(
        id="bare_hands",
        label="bare hands",
        phrase="their bare hands",
        sense=1,
        reach=1,
        grab=True,
        water_ok=True,
        narrow_ok=False,
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "calm", "observant"]


def tool_reason(tool: ToolCfg, item: ItemCfg, spot: SpotCfg) -> str:
    if tool.reach < spot.reach:
        return "it was not long enough to reach"
    if spot.narrow and not tool.narrow_ok:
        return "the opening was too narrow for it"
    if spot.watery and not tool.water_ok:
        return "it was not meant to work in water"
    if tool.id == "bare_hands" and spot.thorny:
        return "reaching in there would mean grabbing past thorns"
    if tool.magnet:
        return f"{item.label} was not made of metal"
    if tool.scoop and not spot.watery:
        return "there was nothing to scoop from the water"
    if tool.hook and not (item.looped or item.flat):
        return f"{item.label} had nothing easy for the rake to catch"
    if tool.grab and spot.watery and item.flat:
        return f"{item.label} was too flat and slippery to pinch"
    return "it was the wrong shape for the job"


def tool_works(tool: ToolCfg, item: ItemCfg, spot: SpotCfg) -> bool:
    if tool.reach < spot.reach:
        return False
    if spot.narrow and not tool.narrow_ok:
        return False
    if spot.watery and not tool.water_ok:
        return False
    if tool.id == "bare_hands" and spot.thorny:
        return False
    if tool.magnet:
        return item.material == "metal"
    if tool.scoop:
        return spot.watery
    if tool.hook:
        return item.looped or item.flat
    if tool.grab:
        return not (spot.watery and item.flat)
    return False


def sensible_tools() -> list[ToolCfg]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for spot_id, spot in SPOTS.items():
            for flashy_id, flashy in TOOLS.items():
                if flashy_id == "bare_hands":
                    continue
                if tool_works(flashy, item, spot):
                    continue
                for fix_id, fix in TOOLS.items():
                    if fix.sense < SENSE_MIN:
                        continue
                    if fix_id == flashy_id:
                        continue
                    if tool_works(fix, item, spot):
                        combos.append((item_id, spot_id, flashy_id, fix_id))
    return sorted(set(combos))


def best_fix(item: ItemCfg, spot: SpotCfg) -> ToolCfg:
    working = [tool for tool in sensible_tools() if tool_works(tool, item, spot)]
    if not working:
        raise StoryError("(No reasonable fix exists for this backyard problem.)")
    return sorted(working, key=lambda t: (-t.sense, t.id))[0]


def predict_with_tool(world: World, tool_id: str) -> dict:
    sim = world.copy()
    item = ITEMS[sim.facts["item_cfg"].id]
    spot = SPOTS[sim.facts["spot_cfg"].id]
    tool = TOOLS[tool_id]
    success = tool_works(tool, item, spot)
    if success:
        sim.get("item").meters["retrieved"] += 1
        sim.get("item").meters["lost"] = 0.0
    else:
        sim.get("item").meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "success": success,
        "wet": sim.get("item").meters["wet"] >= THRESHOLD,
        "reason": tool_reason(tool, item, spot) if not success else "",
    }


def setup_scene(world: World, a: Entity, b: Entity, friend: Entity, item: ItemCfg) -> None:
    for kid in (a, b, friend):
        kid.memes["play"] += 1
    world.say(
        f"After school, {a.id} was in {friend.id}'s backyard with {b.id}, and the three of them had turned the grass into a tiny game. "
        f"They needed {item.phrase}, {item.game_need}, to finish the last part."
    )
    world.say(
        f"The yard felt easy and ordinary in the nicest way: warm boards on the deck, a hose curled by the fence, and chalk marks fading on the patio."
    )


def lose_item(world: World, a: Entity, b: Entity, item: ItemCfg, spot: SpotCfg) -> None:
    ent = world.get("item")
    ent.meters["lost"] += 1
    ent.attrs["spot"] = spot.id
    propagate(world, narrate=False)
    world.say(
        f"Then {a.id} gave the game one more try, {b.id} laughed, and {item.label} {spot.move_text}."
    )
    if ent.meters["wet"] >= THRESHOLD:
        world.say(
            f"{b.id} made a small worried sound. If they left it there, the water would make it soft and heavy."
        )


def flashy_plan(world: World, a: Entity, b: Entity, flashy: ToolCfg, item: ItemCfg, spot: SpotCfg) -> None:
    a.memes["pushes_idea"] += 1
    b.memes["objects"] += 1
    propagate(world, narrate=False)
    allure_text = (
        f'The {flashy.label} had a real allure. Its bright end caught the sun, and {a.id} said, '
        f'"That looks so rad. Let\'s use it."'
    )
    world.say(allure_text)
    if b.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{b.id} shook {b.pronoun("possessive")} head. "{flashy.label.capitalize()} looks fun," {b.pronoun()} said, '
            f'"but {tool_reason(flashy, item, spot)}."'
        )


def failed_try(world: World, a: Entity, flashy: ToolCfg, item: ItemCfg, spot: SpotCfg) -> None:
    item_ent = world.get("item")
    a.memes["hope"] += 1
    item_ent.meters["stuck"] += 1
    pred = predict_with_tool(world, flashy.id)
    world.facts["flashy_fail_reason"] = pred["reason"]
    world.say(
        f"{a.id} stretched out with {flashy.phrase}. For a second it looked promising, but it did not work because {pred['reason']}."
    )
    if spot.watery and item.soggy:
        item_ent.meters["wet"] += 1
        world.say(
            f"The little {item.label} bobbed once, took on more water, and looked even harder to save."
        )
    elif spot.narrow:
        world.say(
            f"It only bumped the deck edge and pushed {item.label} a finger-width farther from their hands."
        )
    else:
        world.say(
            f"The branches shook, but {item.label} stayed exactly where it was."
        )


def pause_and_plan(world: World, b: Entity, friend: Entity, fix: ToolCfg, item: ItemCfg, spot: SpotCfg) -> None:
    b.memes["problem_solving"] += 1
    friend.memes["helpful"] += 1
    world.say(
        f"Nobody shouted after that. {b.id} crouched down, looked at {spot.phrase}, and thought about what the job really needed."
    )
    reason = ""
    if fix.scoop:
        reason = "something that could scoop from the water without tearing it"
    elif fix.grab:
        reason = "something skinny enough to reach in and pinch it gently"
    elif fix.hook:
        reason = "something that could catch an edge and pull it closer"
    else:
        reason = "a better-shaped tool"
    world.say(
        f'"Not the shiniest thing," {b.id} said at last. "The right thing." {friend.id} nodded and brought {fix.phrase}, '
        f"which was {reason}."
    )


def retrieve(world: World, b: Entity, fix: ToolCfg, item: ItemCfg, spot: SpotCfg) -> None:
    item_ent = world.get("item")
    item_ent.meters["retrieved"] += 1
    item_ent.meters["lost"] = 0.0
    propagate(world, narrate=False)
    line = ""
    if fix.scoop:
        line = f"{b.id} slid the net under {item.label} and lifted slowly until it rested safe in the mesh"
    elif fix.grab:
        line = f"{b.id} guided the claw in carefully, closed it with a soft click, and drew {item.label} back out"
    elif fix.hook:
        line = f"{b.id} reached in with the rake, caught the edge, and pulled {item.label} close enough to grab"
    else:
        line = f"{b.id} used {fix.label} and brought {item.label} back"
    world.say(f"{line}.")
    if item_ent.meters["relief"] >= THRESHOLD or b.memes["relief"] >= THRESHOLD:
        world.say(
            f"The tight feeling in the yard melted. Even {a_or_b(world)} could laugh again."
        )
    if spot.watery and item.soggy:
        world.say(
            f"They laid it in the sun for a minute on the warm patio stone so it could dry."
        )


def a_or_b(world: World) -> str:
    a = world.get("a")
    b = world.get("b")
    if a.memes["conflict"] >= THRESHOLD and b.memes["problem_solving"] >= THRESHOLD:
        return a.id
    return b.id


def ending(world: World, a: Entity, b: Entity, friend: Entity, item: ItemCfg) -> None:
    a.memes["learned"] += 1
    b.memes["learned"] += 1
    world.say(
        f'"Next time," {a.id} said, brushing grass from {a.pronoun("possessive")} knees, "we try the right tool before the flashy one."'
    )
    world.say(
        f"{b.id} smiled, {friend.id} reset the chalk mark, and soon the game was moving again with {item.label} back where it belonged."
    )
    world.say(
        "The backyard looked the same as before, but the children did not: now they paused, looked closely, and solved things together."
    )


def tell(
    item_cfg: ItemCfg,
    spot_cfg: SpotCfg,
    flashy_cfg: ToolCfg,
    fix_cfg: ToolCfg,
    impulsive_name: str = "Ben",
    impulsive_gender: str = "boy",
    careful_name: str = "Mia",
    careful_gender: str = "girl",
    friend_name: str = "Ava",
    friend_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    a = world.add(Entity(id="a", kind="character", type=impulsive_gender, label=impulsive_name, role="impulsive"))
    b = world.add(Entity(id="b", kind="character", type=careful_gender, label=careful_name, role="careful", attrs={"trait": trait}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="adult"))
    item = world.add(
        Entity(
            id="item",
            type="item",
            label=item_cfg.label,
            attrs={"material": item_cfg.material, "soggy": item_cfg.soggy, "looped": item_cfg.looped, "flat": item_cfg.flat},
            tags=set(item_cfg.tags),
        )
    )
    spot = world.add(
        Entity(
            id="spot",
            type="spot",
            label=spot_cfg.label,
            attrs={"watery": spot_cfg.watery, "thorny": spot_cfg.thorny, "narrow": spot_cfg.narrow, "reach": spot_cfg.reach},
            tags=set(spot_cfg.tags),
        )
    )

    world.facts.update(
        item_cfg=item_cfg,
        spot_cfg=spot_cfg,
        flashy_cfg=flashy_cfg,
        fix_cfg=fix_cfg,
        impulsive_name=impulsive_name,
        careful_name=careful_name,
        friend_name=friend_name,
        parent_type=parent_type,
        trait=trait,
    )

    setup_scene(world, Entity(id=impulsive_name, type=impulsive_gender), Entity(id=careful_name, type=careful_gender), Entity(id=friend_name, type=friend_gender), item_cfg)
    lose_item(world, Entity(id=impulsive_name, type=impulsive_gender), Entity(id=careful_name, type=careful_gender), item_cfg, spot_cfg)

    world.para()
    flashy_plan(world, Entity(id=impulsive_name, type=impulsive_gender), Entity(id=careful_name, type=careful_gender), flashy_cfg, item_cfg, spot_cfg)
    failed_try(world, Entity(id=impulsive_name, type=impulsive_gender), flashy_cfg, item_cfg, spot_cfg)

    world.para()
    pause_and_plan(world, Entity(id=careful_name, type=careful_gender), Entity(id=friend_name, type=friend_gender), fix_cfg, item_cfg, spot_cfg)
    retrieve(world, Entity(id=careful_name, type=careful_gender), fix_cfg, item_cfg, spot_cfg)
    ending(world, Entity(id=impulsive_name, type=impulsive_gender), Entity(id=careful_name, type=careful_gender), Entity(id=friend_name, type=friend_gender), item_cfg)

    world.facts.update(
        outcome="resolved",
        wet=world.get("item").meters["wet"] >= THRESHOLD,
        retrieved=world.get("item").meters["retrieved"] >= THRESHOLD,
        failed_tool_reason=world.facts.get("flashy_fail_reason", ""),
    )
    return world


def pair_noun(g1: str, g2: str) -> str:
    if g1 == "boy" and g2 == "boy":
        return "two boys"
    if g1 == "girl" and g2 == "girl":
        return "two girls"
    return "a boy and a girl"


KNOWLEDGE = {
    "magnet": [(
        "What does a magnet do?",
        "A magnet pulls on some kinds of metal. It does not pull paper or most plastic things."
    )],
    "grabber": [(
        "What is a grabber claw?",
        "A grabber claw is a long tool that can pinch and hold something from far away. It helps you reach into places your hand cannot safely go."
    )],
    "rake": [(
        "What can a rake help with?",
        "A rake can pull light things closer when its tines catch an edge or a loop. It works better for dragging than for pinching."
    )],
    "pool_net": [(
        "Why is a net useful in water?",
        "A net can slide under something floating and lift it up. That is gentler than poking at it with a hard tool."
    )],
    "pond": [(
        "Why can paper be hard to save from water?",
        "Paper gets soft and heavy when it is wet. That makes it easier to tear or sink if you keep poking at it."
    )],
    "rose_bush": [(
        "Why should children be careful around thorny bushes?",
        "Thorns can scratch skin very quickly. It is safer to stop and choose a tool than to reach in with bare hands."
    )],
    "deck": [(
        "Why can narrow spaces be tricky?",
        "A narrow space can block wide tools and hands. Sometimes the best tool is the skinniest one that still reaches."
    )],
    "paper_airplane": [(
        "What is a paper airplane?",
        "A paper airplane is a folded paper toy that glides through the air. It is light, so wind and water can move it easily."
    )],
    "ring": [(
        "Why is a ring-shaped toy easy to hook?",
        "A ring has an open middle, so a hook or rake can catch it. That shape gives the tool something to pull."
    )],
    "robot": [(
        "Why would a magnet work on a metal toy?",
        "Some metals are pulled by magnets. If a toy is made of that kind of metal, a magnet can help lift or drag it."
    )],
}
KNOWLEDGE_ORDER = [
    "magnet", "grabber", "rake", "pool_net", "pond", "rose_bush", "deck",
    "paper_airplane", "ring", "robot",
]


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item_cfg"]
    spot = world.facts["spot_cfg"]
    flashy = world.facts["flashy_cfg"]
    fix = world.facts["fix_cfg"]
    a = world.facts["impulsive_name"]
    b = world.facts["careful_name"]
    friend = world.facts["friend_name"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old set in a friend\'s backyard. Include the words "allure" and "rad", and build the plot around a small problem, a disagreement, and a clever fix.',
        f"Tell a gentle story where {a} and {b} lose a {item.label} in {spot.phrase}, argue over using {flashy.label}, and then solve the problem with {fix.label}.",
        f"Write a short backyard story where the twist is that the shiny idea is not the right one, so {friend} and the children stop, think, and choose a better tool."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    item = world.facts["item_cfg"]
    spot = world.facts["spot_cfg"]
    flashy = world.facts["flashy_cfg"]
    fix = world.facts["fix_cfg"]
    a = world.facts["impulsive_name"]
    b = world.facts["careful_name"]
    friend = world.facts["friend_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun('boy' if a in BOY_NAMES else 'girl', 'boy' if b in BOY_NAMES else 'girl')} playing in {friend}'s backyard. They were trying to finish a game together when their {item.label} got lost."
        ),
        (
            f"What problem did the children have?",
            f"They needed the {item.label} for their game, but it ended up in {spot.phrase}. That stopped the game and made them figure out how to get it back."
        ),
        (
            f"Why did {a} want to use the {flashy.label}?",
            f"{a} liked the shiny {flashy.label} because it looked exciting and rad. Its allure made it feel like the fastest answer, even though it did not match the job."
        ),
        (
            f"What was the twist when they tried the {flashy.label}?",
            f"The twist was that the exciting idea was the wrong one. It failed because {world.facts['failed_tool_reason']}, so the children had to stop guessing and really think."
        ),
        (
            "How did they solve the problem?",
            f"They studied the spot and picked {fix.phrase}. That worked because it fit both the place and the kind of thing they were trying to rescue."
        ),
        (
            "What changed by the end of the story?",
            f"At first they argued over the flashy idea, but by the end they solved the problem together. The ending shows them returning to play after choosing the right tool instead of the most exciting-looking one."
        ),
    ]
    if world.facts.get("wet"):
        qa.append((
            f"Why did they need to hurry with the {item.label}?",
            f"They worried because the {item.label} was in water and could get ruined. That gave the problem a little more pressure and made their careful choice matter even more."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["item_cfg"].tags) | set(world.facts["spot_cfg"].tags)
    tags |= set(world.facts["flashy_cfg"].tags) | set(world.facts["fix_cfg"].tags)
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


@dataclass
class StoryParams:
    item: str
    spot: str
    flashy: str
    fix: str
    impulsive_name: str
    impulsive_gender: str
    careful_name: str
    careful_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
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


CURATED = [
    StoryParams(
        item="plane",
        spot="pond",
        flashy="magnet_wand",
        fix="pool_net",
        impulsive_name="Ben",
        impulsive_gender="boy",
        careful_name="Mia",
        careful_gender="girl",
        friend_name="Ava",
        friend_gender="girl",
        parent="mother",
        trait="patient",
    ),
    StoryParams(
        item="ring",
        spot="rose_bush",
        flashy="magnet_wand",
        fix="garden_rake",
        impulsive_name="Leo",
        impulsive_gender="boy",
        careful_name="Nora",
        careful_gender="girl",
        friend_name="Zoe",
        friend_gender="girl",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        item="robot",
        spot="under_deck",
        flashy="garden_rake",
        fix="grabber_claw",
        impulsive_name="Sam",
        impulsive_gender="boy",
        careful_name="Ella",
        careful_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        item="plane",
        spot="under_deck",
        flashy="magnet_wand",
        fix="grabber_claw",
        impulsive_name="Maya",
        impulsive_gender="girl",
        careful_name="Theo",
        careful_gender="boy",
        friend_name="Lucy",
        friend_gender="girl",
        parent="father",
        trait="observant",
    ),
    StoryParams(
        item="ring",
        spot="pond",
        flashy="magnet_wand",
        fix="pool_net",
        impulsive_name="Noah",
        impulsive_gender="boy",
        careful_name="Ava",
        careful_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        parent="mother",
        trait="calm",
    ),
]


def explain_rejection(item: ItemCfg, spot: SpotCfg, flashy: Optional[ToolCfg] = None, fix: Optional[ToolCfg] = None) -> str:
    if flashy and flashy.sense < SENSE_MIN:
        return (
            f"(No story: '{flashy.id}' is known to the world, but it scores too low on common sense "
            f"for this domain. The children may be tempted by a flashy idea, but the generated story "
            f"should not select an openly unsafe main tool.)"
        )
    if flashy and tool_works(flashy, item, spot):
        return (
            f"(No story: {flashy.label} would actually work on the {item.label} in {spot.phrase}, "
            f"so it cannot serve as the mistaken flashy idea with a twist.)"
        )
    if fix and not tool_works(fix, item, spot):
        return (
            f"(No story: {fix.label} does not really solve getting the {item.label} from {spot.phrase}. "
            f"Pick a fix that truly matches the object and the place.)"
        )
    return "(No story: no valid combination matches the given options.)"


ASP_RULES = r"""
% flashily tempting tools are those at or above the minimum sense but still wrong.
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.

fails(T, I, S) :- tool(T), item(I), spot(S), not works(T, I, S).
valid(I, S, F, X) :- item(I), spot(S), tool(F), tool(X),
                     sensible_tool(F), sensible_tool(X),
                     fails(F, I, S), works(X, I, S), F != X.

outcome(I, S, F, X, resolved) :- valid(I, S, F, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        if tool.magnet:
            lines.append(asp.fact("magnet", tool_id))
        if tool.hook:
            lines.append(asp.fact("hook", tool_id))
        if tool.grab:
            lines.append(asp.fact("grab", tool_id))
        if tool.scoop:
            lines.append(asp.fact("scoop", tool_id))
        if tool.water_ok:
            lines.append(asp.fact("water_ok", tool_id))
        if tool.narrow_ok:
            lines.append(asp.fact("narrow_ok", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("material", item_id, item.material))
        if item.flat:
            lines.append(asp.fact("flat", item_id))
        if item.looped:
            lines.append(asp.fact("looped", item_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot_reach", spot_id, spot.reach))
        if spot.watery:
            lines.append(asp.fact("watery", spot_id))
        if spot.narrow:
            lines.append(asp.fact("narrow", spot_id))
        if spot.thorny:
            lines.append(asp.fact("thorny", spot_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(
        r"blocked(T,I,S) :- reach(T,TR), spot_reach(S,SR), TR < SR."
    )
    lines.append(
        r"blocked(T,I,S) :- narrow(S), not narrow_ok(T)."
    )
    lines.append(
        r"blocked(T,I,S) :- watery(S), not water_ok(T)."
    )
    lines.append(
        r'blocked(bare_hands,I,S) :- thorny(S).'
    )
    lines.append(
        r"works(T,I,S) :- magnet(T), material(I,metal), not blocked(T,I,S)."
    )
    lines.append(
        r"works(T,I,S) :- scoop(T), watery(S), not blocked(T,I,S)."
    )
    lines.append(
        r"works(T,I,S) :- hook(T), looped(I), not blocked(T,I,S)."
    )
    lines.append(
        r"works(T,I,S) :- hook(T), flat(I), not blocked(T,I,S)."
    )
    lines.append(
        r"works(T,I,S) :- grab(T), not flat(I), not blocked(T,I,S)."
    )
    lines.append(
        r"works(T,I,S) :- grab(T), flat(I), not watery(S), not blocked(T,I,S)."
    )
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
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_flashy", params.flashy),
        asp.fact("chosen_fix", params.fix),
        "picked_valid :- valid(I,S,F,X), chosen_item(I), chosen_spot(S), chosen_flashy(F), chosen_fix(X).",
        "picked_outcome(resolved) :- picked_valid.",
    ])
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    if (params.item, params.spot, params.flashy, params.fix) in set(valid_combos()):
        return "resolved"
    return "invalid"


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a small backyard problem, a flashy wrong guess, and a careful fix."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--flashy", choices=TOOLS)
    ap.add_argument("--fix", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.flashy:
        flashy = TOOLS[args.flashy]
        if flashy.sense < SENSE_MIN:
            raise StoryError(explain_rejection(ITEMS[args.item] if args.item else next(iter(ITEMS.values())), SPOTS[args.spot] if args.spot else next(iter(SPOTS.values())), flashy=flashy))
    if args.item and args.spot and args.flashy:
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        flashy = TOOLS[args.flashy]
        if tool_works(flashy, item, spot):
            raise StoryError(explain_rejection(item, spot, flashy=flashy))
    if args.item and args.spot and args.fix:
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        fix = TOOLS[args.fix]
        if not tool_works(fix, item, spot):
            raise StoryError(explain_rejection(item, spot, fix=fix))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.spot is None or combo[1] == args.spot)
        and (args.flashy is None or combo[2] == args.flashy)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, spot_id, flashy_id, fix_id = rng.choice(combos)
    impulsive_gender = rng.choice(["girl", "boy"])
    careful_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    impulsive_name = _pick_name(rng, impulsive_gender, set())
    careful_name = _pick_name(rng, careful_gender, {impulsive_name})
    friend_name = _pick_name(rng, friend_gender, {impulsive_name, careful_name})
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        spot=spot_id,
        flashy=flashy_id,
        fix=fix_id,
        impulsive_name=impulsive_name,
        impulsive_gender=impulsive_gender,
        careful_name=careful_name,
        careful_gender=careful_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS or params.spot not in SPOTS or params.flashy not in TOOLS or params.fix not in TOOLS:
        raise StoryError("(Invalid params: unknown registry key.)")
    item = ITEMS[params.item]
    spot = SPOTS[params.spot]
    flashy = TOOLS[params.flashy]
    fix = TOOLS[params.fix]
    if flashy.sense < SENSE_MIN:
        raise StoryError(explain_rejection(item, spot, flashy=flashy))
    if tool_works(flashy, item, spot):
        raise StoryError(explain_rejection(item, spot, flashy=flashy))
    if not tool_works(fix, item, spot):
        raise StoryError(explain_rejection(item, spot, fix=fix))

    world = tell(
        item_cfg=item,
        spot_cfg=spot,
        flashy_cfg=flashy,
        fix_cfg=fix,
        impulsive_name=params.impulsive_name,
        impulsive_gender=params.impulsive_gender,
        careful_name=params.careful_name,
        careful_gender=params.careful_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid combos match ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        if "allure" not in sample.story.lower() or "rad" not in sample.story.lower():
            raise StoryError("required seed words missing from story text")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not buf.getvalue().strip():
            raise StoryError("emit produced no output")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, spot, flashy, fix) combos:\n")
        for item, spot, flashy, fix in combos:
            print(f"  {item:6} {spot:10} {flashy:12} {fix}")
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
            header = f"### {p.item} at {p.spot} (flashy: {p.flashy}, fix: {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
