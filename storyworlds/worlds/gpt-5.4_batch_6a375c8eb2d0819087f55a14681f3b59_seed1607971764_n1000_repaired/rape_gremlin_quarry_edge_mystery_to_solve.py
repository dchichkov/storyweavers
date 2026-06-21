#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py
=======================================================================

A standalone story world for a tiny detective story set at the quarry edge.
Two children notice that something has gone missing near a path lined with wild
yellow rape flowers. A mischievous gremlin has taken the object, and the
children must solve the mystery by following an honest clue, choosing a lure
that would really tempt the creature, and keeping safely back from the quarry
edge.

The domain is deliberately small and constraint-checked: not every clue fits
every hiding place, not every missing object would tempt a gremlin, and not
every recovery plan is safe. The simulated state drives the prose, the turn,
and the ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py --item whistle --clue pebbles
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py --hide ledge_nest
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py --trace
    python storyworlds/worlds/gpt-5.4/rape_gremlin_quarry_edge_mystery_to_solve.py --verify
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
SAFE_DISTANCE = 2


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
        female = {"girl", "mother", "woman", "ranger_woman"}
        male = {"boy", "father", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
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
class Item:
    id: str
    label: str
    phrase: str
    shine: int
    jingle: int
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
class Clue:
    id: str
    label: str
    sentence: str
    points_to: set[str]
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
class Hideout:
    id: str
    label: str
    phrase: str
    near_edge: bool
    distance: int
    reachable_by_child: bool
    texture: str
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
class Lure:
    id: str
    label: str
    phrase: str
    needs: set[str]
    rhyme: str
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


@dataclass
class HelperPlan:
    id: str
    label: str
    phrase: str
    safe_for_edge: bool
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
        return [e for e in self.entities.values() if e.role in {"detective", "partner"}]

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


def _r_edge_worry(world: World) -> list[str]:
    out: list[str] = []
    for child in world.kids():
        if child.meters["at_edge"] < THRESHOLD:
            continue
        sig = ("edge_worry", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["fear"] += 1
        if "ranger" in world.entities:
            world.get("ranger").memes["alert"] += 1
        out.append("__edge__")
    return out


def _r_found_clue(world: World) -> list[str]:
    if world.facts.get("clue_found") and not world.facts.get("suspect_named"):
        sig = ("suspect", "gremlin")
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["curiosity"] += 1
            world.facts["suspect_named"] = True
    return []


def _r_gremlin_comes(world: World) -> list[str]:
    if not world.facts.get("lure_set"):
        return []
    if not world.facts.get("lure_works"):
        return []
    gremlin = world.get("gremlin")
    if gremlin.meters["visible"] >= THRESHOLD:
        return []
    sig = ("gremlin_visible",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gremlin.meters["visible"] += 1
    for kid in world.kids():
        kid.memes["awe"] += 1
    return ["__gremlin__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="edge_worry", tag="safety", apply=_r_edge_worry),
    Rule(name="found_clue", tag="mystery", apply=_r_found_clue),
    Rule(name="gremlin_comes", tag="turn", apply=_r_gremlin_comes),
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
        for s in produced:
            world.say(s)
    return produced


def item_tempts_gremlin(item: Item) -> bool:
    return (item.shine + item.jingle) >= 2


def clue_fits_hide(clue: Clue, hide: Hideout) -> bool:
    return hide.id in clue.points_to


def lure_fits_item(lure: Lure, item: Item) -> bool:
    needs = set(lure.needs)
    if "shine" in needs and item.shine <= 0:
        return False
    if "jingle" in needs and item.jingle <= 0:
        return False
    return True


def plan_safe_for_hide(plan: HelperPlan, hide: Hideout) -> bool:
    return (not hide.near_edge) or plan.safe_for_edge


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        if not item_tempts_gremlin(item):
            continue
        for clue_id, clue in CLUES.items():
            for hide_id, hide in HIDES.items():
                if not clue_fits_hide(clue, hide):
                    continue
                for lure_id, lure in LURES.items():
                    if lure_fits_item(lure, item):
                        combos.append((item_id, clue_id, hide_id, lure_id))
    return combos


def safe_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for item_id, clue_id, hide_id, lure_id in valid_combos():
        hide = HIDES[hide_id]
        for plan_id, plan in PLANS.items():
            if plan_safe_for_hide(plan, hide):
                out.append((item_id, clue_id, hide_id, lure_id, plan_id))
    return out


def explain_item_rejection(item: Item) -> str:
    return (
        f"(No story: {item.phrase} is not shiny or jangly enough to tempt a gremlin, "
        f"so there is no honest mystery for this world to solve.)"
    )


def explain_clue_rejection(clue: Clue, hide: Hideout) -> str:
    return (
        f"(No story: the clue '{clue.label}' would not fairly point toward {hide.phrase}. "
        f"A detective story needs a clue that really fits the hiding place.)"
    )


def explain_lure_rejection(lure: Lure, item: Item) -> str:
    return (
        f"(No story: {lure.phrase} would not tempt a gremlin that stole {item.phrase}. "
        f"The lure must match what the creature liked about the missing object.)"
    )


def explain_plan_rejection(plan: HelperPlan, hide: Hideout) -> str:
    return (
        f"(No story: {plan.phrase} is not safe for {hide.phrase}. Near the quarry edge, "
        f"the children need a safer recovery plan.)"
    )


def predict_danger(world: World, hide: Hideout, plan: HelperPlan) -> dict:
    sim = world.copy()
    detective = sim.get("detective")
    partner = sim.get("partner")
    if hide.near_edge and not plan.safe_for_edge:
        detective.meters["at_edge"] += 1
        partner.meters["at_edge"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": detective.memes["fear"] + partner.memes["fear"],
        "safe": detective.meters["at_edge"] < THRESHOLD and partner.meters["at_edge"] < THRESHOLD,
    }


def introduce(world: World, detective: Entity, partner: Entity, ranger: Entity) -> None:
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    world.say(
        f"On a bright afternoon, {detective.id} and {partner.id} walked with Ranger "
        f"{ranger.id} along the quarry edge path. Below them, the old stone walls dropped "
        f"away, and beside the fence a patch of wild rape flowers shone yellow in the wind."
    )
    world.say(
        f'{detective.id} liked to notice small things. "{detective.id} the detective," '
        f'{partner.id} teased, and {detective.id} grinned because it was true.'
    )


def set_objective(world: World, detective: Entity, partner: Entity, item: Item) -> None:
    world.say(
        f"They had come to hang little route markers for a bird walk, and {detective.id} "
        f"was carrying {item.phrase}."
    )
    world.say(
        f'When {detective.id} reached for it again, it was gone. "{item.label.capitalize()}!" '
        f'{detective.pronoun().capitalize()} gasped. "{partner.id}, it was right here."'
    )
    world.facts["item_missing"] = True


def inspect_scene(world: World, partner: Entity, clue: Clue) -> None:
    world.say(
        f'{partner.id} crouched beside the fence. "Wait," {partner.pronoun()} whispered. '
        f'"Look at this." {clue.sentence}'
    )
    world.facts["clue_found"] = True
    world.facts["clue_id"] = clue.id
    propagate(world, narrate=False)


def name_suspect(world: World, detective: Entity, partner: Entity, clue: Clue) -> None:
    detective.memes["deduction"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'"That is no wind-trick," {detective.id} said. "That is a clue." '
        f'{partner.id} nodded slowly. "Then who took it?"'
    )
    world.say(
        f'{detective.id} looked from the clue to the fence and lowered {detective.pronoun("possessive")} '
        f'voice. "A gremlin, maybe. A quarry-edge gremlin who likes small, bright things."'
    )


def warn_about_edge(world: World, ranger: Entity, hide: Hideout, plan: HelperPlan) -> None:
    pred = predict_danger(world, hide, plan)
    world.facts["predicted_safe"] = pred["safe"]
    if hide.near_edge:
        world.say(
            f'Ranger {ranger.id} lifted a hand. "Mystery first, feet second," '
            f'{ranger.pronoun()} said. "No one goes past the white stones by the quarry edge."'
        )
    else:
        world.say(
            f'Ranger {ranger.id} smiled. "Good detectives look carefully and walk carefully too," '
            f'{ranger.pronoun()} said.'
        )


def follow_clue(world: World, detective: Entity, partner: Entity, hide: Hideout) -> None:
    detective.meters["steps_taken"] += 1
    partner.meters["steps_taken"] += 1
    world.say(
        f"The clue led them toward {hide.phrase}. The path there felt quiet, except for the "
        f"scratch of dry grass and the far-off clink of stone."
    )
    world.facts["hide_reached"] = True
    if hide.near_edge:
        world.say(
            f'{partner.id} stopped at the line of white warning stones. "I do not like how close '
            f'that looks," {partner.pronoun()} said.'
        )


def set_lure(world: World, detective: Entity, partner: Entity, lure: Lure, item: Item) -> None:
    world.facts["lure_set"] = True
    world.facts["lure_works"] = lure_fits_item(lure, item)
    world.say(
        f'"Let us ask the thief nicely," {detective.id} said. Together they set out {lure.phrase}.'
    )
    world.say(
        f'Then the two children whispered their rhyme:\n'
        f'"{lure.rhyme}"'
    )
    propagate(world, narrate=False)


def unsafe_reach(world: World, detective: Entity, partner: Entity, hide: Hideout) -> None:
    detective.meters["at_edge"] += 1
    partner.meters["at_edge"] += 1
    propagate(world, narrate=False)
    world.say(
        f'For one quick second the hiding place seemed close enough to grab. "{item_word(world)}!" '
        f'{partner.id} said. But the stones underfoot looked crumbly, and the drop beyond them looked deep.'
    )


def ranger_recovers(world: World, ranger: Entity, hide: Hideout, item: Item) -> None:
    world.get("gremlin").meters["visible"] += 1
    world.get("gremlin").meters["caught_out"] += 1
    item_ent = world.get("item")
    item_ent.meters["found"] += 1
    item_ent.meters["hidden"] = 0.0
    world.say(
        f"At once a little gremlin with pebble-gray ears popped from {hide.phrase}, hugging "
        f"{item.phrase} to its chest."
    )
    world.say(
        f'"Oh!" it squeaked. "It was so shiny. I only borrowed it."'
    )
    world.say(
        f'Ranger {ranger.id} kept everyone back, stepped forward the safe way, and took the '
        f'{item.label} back without going beyond the warning stones.'
    )


def child_recovers(world: World, detective: Entity, partner: Entity, hide: Hideout, item: Item) -> None:
    world.get("gremlin").meters["visible"] += 1
    item_ent = world.get("item")
    item_ent.meters["found"] += 1
    item_ent.meters["hidden"] = 0.0
    world.say(
        f"At once a little gremlin with pebble-gray ears peeped from {hide.phrase}, carrying "
        f"{item.phrase} as if it were treasure."
    )
    world.say(
        f'"Please put it down," {detective.id} said. "We solved your mystery, so now you must solve ours."'
    )
    world.say(
        f"The gremlin blinked, set the {item.label} on a flat stone, and scuttled back into hiding."
    )


def kind_ending(world: World, detective: Entity, partner: Entity, ranger: Entity, item: Item) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    world.say(
        f'"Case closed," {partner.id} said, and this time {detective.id} laughed out loud.'
    )
    world.say(
        f'Ranger {ranger.id} tucked the {item.label} safely into {ranger.pronoun("possessive")} pack and said, '
        f'"A good detective finds the truth and keeps everybody safe."'
    )
    world.say(
        f"As the three of them walked on, the rape flowers nodded in the breeze, and somewhere "
        f"behind the stones the gremlin sang the rhyme much more softly than before."
    )


def teach_gremlin(world: World, detective: Entity, partner: Entity, item: Item) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    world.say(
        f'"Next time, ask," {partner.id} told the little thief. The gremlin rubbed its ears and nodded.'
    )
    world.say(
        f'{detective.id} clipped the {item.label} back where it belonged, and the path looked right again.'
    )
    world.say(
        "The mystery felt smaller now, like a knot untied, and the quarry edge no longer seemed so secret."
    )


def item_word(world: World) -> str:
    item = world.facts.get("item_cfg")
    return item.label if item is not None else "it"


def tell(
    item: Item,
    clue: Clue,
    hide: Hideout,
    lure: Lure,
    plan: HelperPlan,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    ranger_name: str = "Iris",
    ranger_type: str = "ranger_woman",
) -> World:
    world = World()
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
        attrs={"name": detective_name},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        attrs={"name": partner_name},
    ))
    ranger = world.add(Entity(
        id="ranger",
        kind="character",
        type=ranger_type,
        label=ranger_name,
        role="ranger",
        attrs={"name": ranger_name},
    ))
    gremlin = world.add(Entity(
        id="gremlin",
        kind="character",
        type="gremlin",
        label="gremlin",
        role="culprit",
        attrs={"likes_shiny": item.shine > 0, "likes_jingle": item.jingle > 0},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="object",
        label=item.label,
        role="missing_item",
    ))

    item_ent.meters["hidden"] = 1.0
    detective.meters["at_edge"] = 0.0
    partner.meters["at_edge"] = 0.0
    detective.memes["fear"] = 0.0
    partner.memes["fear"] = 0.0
    world.facts["clue_found"] = False
    world.facts["suspect_named"] = False
    world.facts["lure_set"] = False
    world.facts["lure_works"] = False
    world.facts["predicted_safe"] = True

    introduce(world, detective, partner, ranger)
    set_objective(world, detective, partner, item)

    world.para()
    inspect_scene(world, partner, clue)
    name_suspect(world, detective, partner, clue)
    warn_about_edge(world, ranger, hide, plan)

    world.para()
    follow_clue(world, detective, partner, hide)
    set_lure(world, detective, partner, lure, item)

    if hide.near_edge and not plan.safe_for_hide:
        unsafe_reach(world, detective, partner, hide)
        ranger_recovers(world, ranger, hide, item)
        outcome = "ranger_rescue"
    elif hide.near_edge:
        ranger_recovers(world, ranger, hide, item)
        outcome = "ranger_safe"
    else:
        child_recovers(world, detective, partner, hide, item)
        outcome = "child_safe"

    world.para()
    if outcome == "child_safe":
        teach_gremlin(world, detective, partner, item)
    else:
        kind_ending(world, detective, partner, ranger, item)

    world.facts.update(
        detective=detective,
        partner=partner,
        ranger=ranger,
        gremlin=gremlin,
        item=item_ent,
        item_cfg=item,
        clue_cfg=clue,
        hide_cfg=hide,
        lure_cfg=lure,
        plan_cfg=plan,
        outcome=outcome,
        found=item_ent.meters["found"] >= THRESHOLD,
        near_edge=hide.near_edge,
        fright=detective.memes["fear"] + partner.memes["fear"],
    )
    return world


ITEMS = {
    "whistle": Item(
        id="whistle",
        label="whistle",
        phrase="a silver whistle on a blue cord",
        shine=2,
        jingle=1,
        tags={"whistle", "shiny"},
    ),
    "badge": Item(
        id="badge",
        label="badge",
        phrase="a brass helper badge",
        shine=2,
        jingle=0,
        tags={"badge", "metal"},
    ),
    "bell": Item(
        id="bell",
        label="bell",
        phrase="a little brass bell",
        shine=1,
        jingle=2,
        tags={"bell", "sound"},
    ),
    "sandwich": Item(
        id="sandwich",
        label="sandwich",
        phrase="a paper-wrapped sandwich",
        shine=0,
        jingle=0,
        tags={"food"},
    ),
}

CLUES = {
    "pebbles": Clue(
        id="pebbles",
        label="three stacked pebbles",
        sentence="Three pebbles were stacked in a tiny tower, too neat for the wind to make.",
        points_to={"fence_post", "ledge_nest"},
        tags={"pebbles", "stack"},
    ),
    "yellow_petals": Clue(
        id="yellow_petals",
        label="yellow petals",
        sentence="Yellow rape petals lay in a crooked trail where something small had hurried through.",
        points_to={"tool_crate", "fence_post"},
        tags={"rape_flower", "petals"},
    ),
    "scratch_marks": Clue(
        id="scratch_marks",
        label="scratch marks",
        sentence="Fine scratch marks ran over a flat board, with one bright speck caught in the wood.",
        points_to={"tool_crate", "rope_coil"},
        tags={"scratch", "wood"},
    ),
}

HIDES = {
    "tool_crate": Hideout(
        id="tool_crate",
        label="tool crate",
        phrase="an old tool crate beside the path",
        near_edge=False,
        distance=5,
        reachable_by_child=True,
        texture="splintery wood",
        tags={"crate"},
    ),
    "rope_coil": Hideout(
        id="rope_coil",
        label="rope coil",
        phrase="a big coil of rope near the signpost",
        near_edge=False,
        distance=4,
        reachable_by_child=True,
        texture="scratchy rope",
        tags={"rope"},
    ),
    "fence_post": Hideout(
        id="fence_post",
        label="fence post",
        phrase="the hollow base of a fence post",
        near_edge=True,
        distance=2,
        reachable_by_child=False,
        texture="cold stone",
        tags={"fence", "edge"},
    ),
    "ledge_nest": Hideout(
        id="ledge_nest",
        label="ledge nest",
        phrase="a narrow ledge nest just beyond the warning stones",
        near_edge=True,
        distance=1,
        reachable_by_child=False,
        texture="crumbly rock",
        tags={"ledge", "edge"},
    ),
}

LURES = {
    "spoon_chime": Lure(
        id="spoon_chime",
        label="spoon chime",
        phrase="two spoons tied with twine so they chimed together",
        needs={"jingle"},
        rhyme="Gremlin, gremlin, soft and small,\nhear the silver tapping call.",
        qa_text="They used a little chiming lure because the missing object made a sound the gremlin liked.",
        tags={"sound", "rhyme"},
    ),
    "mirror_flash": Lure(
        id="mirror_flash",
        label="mirror flash",
        phrase="a pocket mirror that flashed bright in the sun",
        needs={"shine"},
        rhyme="Gremlin, gremlin, bright and quick,\nfollow the sparkle, not the trick.",
        qa_text="They flashed a little mirror because the thief liked bright, shiny things.",
        tags={"shine", "rhyme"},
    ),
    "tin_song": Lure(
        id="tin_song",
        label="tin song",
        phrase="a shining tin lid tapped in a merry beat",
        needs={"shine", "jingle"},
        rhyme="Gremlin, gremlin, ring and gleam,\ncome and see our silver gleam.",
        qa_text="They chose a lure that both shone and rang, matching exactly what had tempted the gremlin.",
        tags={"shine", "sound", "rhyme"},
    ),
}

PLANS = {
    "call_ranger": HelperPlan(
        id="call_ranger",
        label="call the ranger",
        phrase="call the ranger to step forward while the children stay behind the stones",
        safe_for_edge=True,
        tags={"adult_help", "safe"},
    ),
    "trade_from_path": HelperPlan(
        id="trade_from_path",
        label="trade from the path",
        phrase="offer the lure from the safe side of the path and wait",
        safe_for_edge=True,
        tags={"wait", "safe"},
    ),
    "reach_over": HelperPlan(
        id="reach_over",
        label="reach over",
        phrase="lean over the stones and snatch the object quickly",
        safe_for_edge=False,
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Rose", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Noah", "Eli", "Theo", "Jack", "Owen"]
RANGER_NAMES = ["Iris", "June", "Mara", "Tess", "Rowan", "Ash"]
TRAITS = ["careful", "curious", "sharp-eyed", "thoughtful", "steady"]


@dataclass
class StoryParams:
    item: str
    clue: str
    hide: str
    lure: str
    plan: str
    detective_name: str
    detective_gender: str
    partner_name: str
    partner_gender: str
    ranger_name: str
    ranger_type: str
    detective_trait: str
    partner_trait: str
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
    "quarry": [(
        "What is a quarry?",
        "A quarry is a big place where stone has been cut from the ground. The edges can be steep, so people need to stay on the safe path."
    )],
    "gremlin": [(
        "What is a gremlin in this story world?",
        "A gremlin is a small make-believe creature that likes mischief and borrowed treasures. It is not evil, but it can still cause trouble."
    )],
    "rape_flower": [(
        "What are rape flowers?",
        "Rape flowers are small yellow flowers that grow on a tall plant. In fields or wild patches, they can make the ground look bright yellow."
    )],
    "whistle": [(
        "What does a whistle do?",
        "A whistle makes a sharp sound when you blow through it. People use one to signal, call attention, or lead a group."
    )],
    "bell": [(
        "Why would a bell attract attention?",
        "A bell makes a clear ringing sound, so people and story creatures notice it quickly. Shiny bells can be tempting because they look bright and sound bright too."
    )],
    "badge": [(
        "What is a badge?",
        "A badge is a small sign or metal piece that shows a role, job, or helper's place. It can feel special because it is worn proudly."
    )],
    "sound": [(
        "Why do jingling sounds help in a mystery like this?",
        "A jingling sound can draw someone out because it is easy to hear and follow. Detectives use what a suspect likes to make a good plan."
    )],
    "shine": [(
        "Why would something shiny be tempting?",
        "Shiny things catch the light and stand out. A curious creature might grab one just because it sparkles."
    )],
    "adult_help": [(
        "Why should children ask an adult for help near a quarry edge?",
        "An adult can judge the danger and reach things more safely. Near a steep edge, asking for help is the smart detective choice."
    )],
    "rhyme": [(
        "Why do stories use a rhyme?",
        "A rhyme is easy to remember and fun to say. In a mystery, a rhyme can become a clue, a signal, or a clever way to lure someone out."
    )],
}
KNOWLEDGE_ORDER = [
    "quarry", "gremlin", "rape_flower", "whistle", "bell", "badge",
    "shine", "sound", "adult_help", "rhyme",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    lure = f["lure_cfg"]
    hide = f["hide_cfg"]
    return [
        f'Write a short detective story for ages 3 to 5 set at a quarry edge, using the words "rape" and "gremlin". Make a {item.label} go missing and let children solve the mystery safely.',
        f"Tell a mystery-to-solve story where two children notice a missing {item.label}, follow a fair clue, speak in dialogue, and use a rhyme to lure out a gremlin.",
        f"Write a gentle detective story near a quarry edge in which the hiding place is {hide.phrase} and the children use {lure.label} to uncover the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    partner = f["partner"]
    ranger = f["ranger"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    hide = f["hide_cfg"]
    lure = f["lure_cfg"]
    plan = f["plan_cfg"]
    outcome = f["outcome"]
    dq = detective.label
    pq = partner.label
    rq = ranger.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {dq} and {pq}, two children acting like detectives at the quarry edge, and Ranger {rq} who keeps them safe."
        ),
        (
            f"What mystery did {dq} and {pq} have to solve?",
            f"They had to find out who took the missing {item.label} and where it had been hidden. The mystery began when the object vanished from the path."
        ),
        (
            "What clue helped them?",
            f"The clue was {clue.label}. It mattered because it honestly pointed them toward {hide.phrase} instead of making them guess."
        ),
        (
            "Why did they suspect a gremlin?",
            f"They saw a clue too neat and odd to be chance, so they guessed a gremlin had been sneaking about. The missing object was just the sort of bright little treasure a gremlin would borrow."
        ),
        (
            "How did the rhyme help solve the mystery?",
            f"{lure.qa_text} The rhyme gave the plan a clear signal, and that brought the gremlin out where the children could see it."
        ),
    ]
    if hide.near_edge:
        qa.append((
            "Why did they have to be careful at the quarry edge?",
            f"They were close to a steep drop, so they had to stay behind the warning stones. {plan.phrase.capitalize()} was the safe way to finish the mystery."
        ))
    if outcome == "child_safe":
        qa.append((
            "How did the story end?",
            f"The gremlin put the {item.label} down on a flat stone, and the children got it back without going too close to danger. The ending feels calm because they solved the mystery with patience, not grabbing."
        ))
    else:
        qa.append((
            "Who got the missing object back?",
            f"Ranger {rq} got the {item.label} back while the children stayed in the safe place. That mattered because the hiding place was too close to the quarry edge for children to reach."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"quarry", "gremlin", "rhyme"}
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    lure = f["lure_cfg"]
    plan = f["plan_cfg"]
    tags |= set(item.tags)
    tags |= set(clue.tags)
    tags |= set(lure.tags)
    tags |= set(plan.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="whistle",
        clue="yellow_petals",
        hide="tool_crate",
        lure="mirror_flash",
        plan="trade_from_path",
        detective_name="Nora",
        detective_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        ranger_name="Iris",
        ranger_type="ranger_woman",
        detective_trait="sharp-eyed",
        partner_trait="careful",
    ),
    StoryParams(
        item="bell",
        clue="pebbles",
        hide="fence_post",
        lure="tin_song",
        plan="call_ranger",
        detective_name="Mia",
        detective_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        ranger_name="June",
        ranger_type="ranger_woman",
        detective_trait="curious",
        partner_trait="steady",
    ),
    StoryParams(
        item="badge",
        clue="scratch_marks",
        hide="rope_coil",
        lure="mirror_flash",
        plan="trade_from_path",
        detective_name="Ella",
        detective_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        ranger_name="Rowan",
        ranger_type="ranger_man",
        detective_trait="thoughtful",
        partner_trait="sharp-eyed",
    ),
    StoryParams(
        item="whistle",
        clue="pebbles",
        hide="ledge_nest",
        lure="tin_song",
        plan="call_ranger",
        detective_name="Ava",
        detective_gender="girl",
        partner_name="Sam",
        partner_gender="boy",
        ranger_name="Ash",
        ranger_type="ranger_man",
        detective_trait="careful",
        partner_trait="curious",
    ),
]


ASP_RULES = r"""
tempting(I) :- item(I), shine(I,S), jingle(I,J), S + J >= 2.

valid(I,C,H,L) :- item(I), clue(C), hide(H), lure(L),
                  tempting(I),
                  points_to(C,H),
                  lure_ok(L,I).

lure_ok(L,I) :- lure_needs_nothing(L), item(I).
lure_ok(L,I) :- needs_shine(L), shine(I,S), S > 0, not needs_jingle(L).
lure_ok(L,I) :- needs_jingle(L), jingle(I,J), J > 0, not needs_shine(L).
lure_ok(L,I) :- needs_shine(L), needs_jingle(L), shine(I,S), S > 0, jingle(I,J), J > 0.

safe_plan(H,P) :- hide(H), plan(P), not near_edge(H).
safe_plan(H,P) :- hide(H), plan(P), near_edge(H), safe_for_edge(P).

outcome(ranger_safe)   :- chosen_hide(H), near_edge(H), chosen_plan(P), safe_for_edge(P).
outcome(ranger_rescue) :- chosen_hide(H), near_edge(H), chosen_plan(P), not safe_for_edge(P).
outcome(child_safe)    :- chosen_hide(H), not near_edge(H).

#show valid/4.
#show safe_plan/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("shine", item_id, item.shine))
        lines.append(asp.fact("jingle", item_id, item.jingle))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for hide_id in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, hide_id))
    for hide_id, hide in HIDES.items():
        lines.append(asp.fact("hide", hide_id))
        if hide.near_edge:
            lines.append(asp.fact("near_edge", hide_id))
    for lure_id, lure in LURES.items():
        lines.append(asp.fact("lure", lure_id))
        if "shine" in lure.needs:
            lines.append(asp.fact("needs_shine", lure_id))
        if "jingle" in lure.needs:
            lines.append(asp.fact("needs_jingle", lure_id))
        if not lure.needs:
            lines.append(asp.fact("lure_needs_nothing", lure_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        if plan.safe_for_edge:
            lines.append(asp.fact("safe_for_edge", plan_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_safe_plan_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "safe_plan")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_hide", params.hide),
        asp.fact("chosen_plan", params.plan),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    hide = HIDES[params.hide]
    plan = PLANS[params.plan]
    if hide.near_edge and plan.safe_for_edge:
        return "ranger_safe"
    if hide.near_edge and not plan.safe_for_edge:
        return "ranger_rescue"
    return "child_safe"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-story world: a missing object, a gremlin, a fair clue, and a safe solution at the quarry edge."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hide", choices=HIDES)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--ranger", choices=["ranger_woman", "ranger_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and not item_tempts_gremlin(ITEMS[args.item]):
        raise StoryError(explain_item_rejection(ITEMS[args.item]))

    if args.clue and args.hide and not clue_fits_hide(CLUES[args.clue], HIDES[args.hide]):
        raise StoryError(explain_clue_rejection(CLUES[args.clue], HIDES[args.hide]))

    if args.lure and args.item and not lure_fits_item(LURES[args.lure], ITEMS[args.item]):
        raise StoryError(explain_lure_rejection(LURES[args.lure], ITEMS[args.item]))

    if args.plan and args.hide and not plan_safe_for_hide(PLANS[args.plan], HIDES[args.hide]):
        raise StoryError(explain_plan_rejection(PLANS[args.plan], HIDES[args.hide]))

    combos = [c for c in valid_combos()
              if (args.item is None or c[0] == args.item)
              and (args.clue is None or c[1] == args.clue)
              and (args.hide is None or c[2] == args.hide)
              and (args.lure is None or c[3] == args.lure)]
    if not combos:
        raise StoryError("(No valid mystery combination matches the given options.)")

    item_id, clue_id, hide_id, lure_id = rng.choice(sorted(combos))
    safe_plans = [pid for pid, plan in PLANS.items() if plan_safe_for_hide(plan, HIDES[hide_id])]
    if args.plan is not None:
        if args.plan not in safe_plans:
            raise StoryError(explain_plan_rejection(PLANS[args.plan], HIDES[hide_id]))
        plan_id = args.plan
    else:
        plan_id = rng.choice(sorted(safe_plans))

    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=detective_name)
    ranger_type = args.ranger or rng.choice(["ranger_woman", "ranger_man"])
    ranger_name = rng.choice(RANGER_NAMES)
    detective_trait = rng.choice(TRAITS)
    partner_trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        clue=clue_id,
        hide=hide_id,
        lure=lure_id,
        plan=plan_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        ranger_name=ranger_name,
        ranger_type=ranger_type,
        detective_trait=detective_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hide not in HIDES:
        raise StoryError(f"(Unknown hide: {params.hide})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")

    item = ITEMS[params.item]
    clue = CLUES[params.clue]
    hide = HIDES[params.hide]
    lure = LURES[params.lure]
    plan = PLANS[params.plan]

    if not item_tempts_gremlin(item):
        raise StoryError(explain_item_rejection(item))
    if not clue_fits_hide(clue, hide):
        raise StoryError(explain_clue_rejection(clue, hide))
    if not lure_fits_item(lure, item):
        raise StoryError(explain_lure_rejection(lure, item))
    if not plan_safe_for_hide(plan, hide):
        raise StoryError(explain_plan_rejection(plan, hide))

    world = tell(
        item=item,
        clue=clue,
        hide=hide,
        lure=lure,
        plan=plan,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        ranger_name=params.ranger_name,
        ranger_type=params.ranger_type,
    )

    # Replace ids in story with chosen display names in child-facing prose.
    story = world.render()
    story = story.replace("detective", params.detective_name)
    story = story.replace("partner", params.partner_name)
    story = story.replace("ranger", params.ranger_name)

    # Better, authored text with names rather than internal ids.
    display_story = story
    for src, dst in [
        ("detective", params.detective_name),
        ("partner", params.partner_name),
        ("ranger", params.ranger_name),
    ]:
        display_story = display_story.replace(src, dst)

    # The prose itself already uses labels, but the entity ids remain internal only;
    # the stored story should be the world's rendered text with labels unchanged.
    display_story = world.render().replace("detective", params.detective_name).replace(
        "partner", params.partner_name
    ).replace("ranger", params.ranger_name)

    return StorySample(
        params=params,
        story=display_story,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid mystery combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid mystery combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_safe = {(hid, pid) for hid, hide in HIDES.items() for pid, plan in PLANS.items() if plan_safe_for_hide(plan, hide)}
    asp_safe = set(asp_safe_plan_pairs())
    if py_safe == asp_safe:
        print(f"OK: safe plan pairs match ({len(py_safe)} pairs).")
    else:
        rc = 1
        print("MISMATCH in safe plan pairs:")
        if asp_safe - py_safe:
            print("  only in clingo:", sorted(asp_safe - py_safe))
        if py_safe - asp_safe:
            print("  only in python:", sorted(py_safe - asp_safe))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (item, clue, hide, lure) combos:\n")
        for item_id, clue_id, hide_id, lure_id in combos:
            safe = sorted(pid for (hid, pid) in asp_safe_plan_pairs() if hid == hide_id)
            print(f"  {item_id:8} {clue_id:14} {hide_id:10} {lure_id:12} [{', '.join(safe)}]")
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
            header = f"### {p.detective_name} & {p.partner_name}: {p.item} -> {p.hide} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
