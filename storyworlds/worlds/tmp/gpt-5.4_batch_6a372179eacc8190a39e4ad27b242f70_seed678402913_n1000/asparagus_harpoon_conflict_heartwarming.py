#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py
=====================================================================

A standalone story world about two children, a drifting asparagus-day problem,
and a dangerous old harpoon that must *not* become the solution.

This world models a small heartwarming conflict:
- the family is out by water during asparagus time,
- something important drifts just out of reach,
- one child wants to grab an old harpoon hanging nearby,
- another child objects,
- a calm grown-up resolves the conflict with a gentler tool.

The simulation tracks simple physical meters (floating, retrieved, urgency) and
emotional memes (worry, defiance, conflict, relief). The prose is rendered from
those state changes rather than from a single frozen template.

Run it
------
python storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py
python storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py --place farm_pond --lost basket --safe-tool net
python storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py --place barn_yard
python storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py --all
python storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py --qa
python storyworlds/worlds/gpt-5.4/asparagus_harpoon_conflict_heartwarming.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
CALM_TRAITS = {"careful", "gentle", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    sharp: bool = False
    safe_retriever: bool = False
    fragile: bool = False
    buoyant: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    water: bool = True
    shore: str = ""
    asparagus_line: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    drift_line: str
    rescue_line: str
    distance: int = 1
    fragile: bool = False
    buoyant: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    reach: int = 1
    gentle: bool = False
    action: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_floating_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["floating"] < THRESHOLD:
            continue
        sig = ("floating_worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "water" in world.entities:
            world.get("water").meters["urgency"] += 1
        for kid in world.kids():
            kid.memes["worry"] += 1
        out.append("__drift__")
    return out


def _r_conflict(world: World) -> list[str]:
    a = world.entities.get("instigator")
    b = world.entities.get("cautioner")
    if a is None or b is None:
        return []
    if a.memes["grab_harpoon"] < THRESHOLD or b.memes["object"] < THRESHOLD:
        return []
    sig = ("conflict", a.id, b.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__conflict__"]


def _r_relief(world: World) -> list[str]:
    thing = world.entities.get("lost")
    if thing is None:
        return []
    if thing.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("relief", thing.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    thing.meters["floating"] = 0.0
    if "water" in world.entities:
        world.get("water").meters["urgency"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["worry"] = 0.0
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="floating_worry", tag="physical", apply=_r_floating_worry),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="relief", tag="social", apply=_r_relief),
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


def valid_combo(place: Place, lost: LostThing, safe_tool: SafeTool) -> bool:
    if not place.water:
        return False
    if safe_tool.reach < lost.distance:
        return False
    if lost.fragile and not safe_tool.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for lost_id, lost in LOST_THINGS.items():
            for tool_id, tool in SAFE_TOOLS.items():
                if valid_combo(place, lost, tool):
                    combos.append((place_id, lost_id, tool_id))
    return combos


def older_cautioner_can_stop(relation: str, instigator_age: int, cautioner_age: int,
                             trait: str) -> bool:
    return (
        relation == "siblings"
        and cautioner_age > instigator_age
        and trait in CALM_TRAITS
    )


def outcome_of(params: "StoryParams") -> str:
    return (
        "listened"
        if older_cautioner_can_stop(
            params.relation,
            params.instigator_age,
            params.cautioner_age,
            params.trait,
        )
        else "guided"
    )


def explain_rejection(place: Place, lost: LostThing, safe_tool: Optional[SafeTool] = None) -> str:
    if not place.water:
        return (
            f"(No story: {place.label} has no open water, so {lost.label} cannot drift away. "
            "This world needs a water-side problem before anyone argues about the harpoon.)"
        )
    if safe_tool is not None and safe_tool.reach < lost.distance:
        return (
            f"(No story: {safe_tool.label} cannot reach the drifting {lost.label}. "
            "Pick a tool with a longer reach or a nearer drifting object.)"
        )
    if safe_tool is not None and lost.fragile and not safe_tool.gentle:
        return (
            f"(No story: {lost.label} is too delicate for {safe_tool.label}. "
            "This storyworld only allows a rescue tool that can bring it back gently.)"
        )
    return "(No story: that combination does not make a reasonable rescue.)"


def predict_harpoon_risk(world: World) -> dict:
    sim = world.copy()
    instigator = sim.get("instigator")
    cautioner = sim.get("cautioner")
    instigator.memes["grab_harpoon"] += 1
    cautioner.memes["object"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": instigator.memes["conflict"] >= THRESHOLD,
        "urgency": sim.get("water").meters["urgency"],
    }


def predict_rescue(world: World, safe_tool: SafeTool) -> dict:
    sim = world.copy()
    if not valid_combo(sim.place, LOST_THINGS[sim.facts["lost_cfg"].id], safe_tool):
        return {"retrieved": False}
    sim.get("lost").meters["retrieved"] += 1
    propagate(sim, narrate=False)
    return {"retrieved": sim.get("lost").meters["retrieved"] >= THRESHOLD}


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright asparagus day, {a.id} and {b.id} went with their family to {place.label}. "
        f"{place.scene}"
    )
    world.say(place.asparagus_line)


def drift(world: World, lost_ent: Entity, lost: LostThing) -> None:
    lost_ent.meters["floating"] += 1
    propagate(world, narrate=False)
    world.say(lost.drift_line)


def notice_harpoon(world: World, a: Entity) -> None:
    a.memes["idea"] += 1
    world.say(
        f"Then {a.id} spotted an old harpoon hanging on a hook by the little shed. "
        f'"I could use the harpoon," {a.pronoun()} said, already stepping toward it.'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    pred = predict_harpoon_risk(world)
    b.memes["object"] += 1
    extra = ""
    if pred["conflict"]:
        extra = " It would only make everybody upset."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "No, {a.id}. A harpoon is sharp, and '
        f'{parent.label_word} said sharp tools are for grown-ups."{extra}'
    )


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["grab_harpoon"] += 1
    a.memes["defiance"] += 1
    propagate(world, narrate=False)
    if a.memes["conflict"] >= THRESHOLD:
        world.say(
            f'"But it is long enough!" {a.id} said. {b.id} stepped in front of the hook, '
            f'and for a moment the two children stared at each other with hot cheeks and worried eyes.'
        )
    else:
        world.say(f'"But it is long enough!" {a.id} insisted.')


def back_down(world: World, a: Entity, b: Entity) -> None:
    a.memes["grab_harpoon"] = 0.0
    a.memes["defiance"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at the old harpoon, then at {b.id}'s steady face, and let out a small breath. "
        f'"Okay," {a.pronoun()} said. "I do not want to make it worse."'
    )


def intervene(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["heard_parent"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over at once, saw the old harpoon on the hook, "
        f"and gently rested a hand on it before {a.id} could touch it."
    )
    world.say(
        f'"Thank you for stopping and talking first," {parent.pronoun()} said. '
        f'"A harpoon is not a child tool. We can solve this the calm way."'
    )


def rescue(world: World, parent: Entity, safe_tool: SafeTool, lost_ent: Entity, lost: LostThing) -> None:
    pred = predict_rescue(world, safe_tool)
    if not pred["retrieved"]:
        raise StoryError(explain_rejection(world.place, lost, safe_tool))
    lost_ent.meters["retrieved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} picked up {safe_tool.phrase} and {safe_tool.action}. "
        f"{lost.rescue_line}"
    )


def comfort(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
    world.say(
        f"Then {parent.label_word} knelt between them. "
        f'"You were both trying to help," {parent.pronoun()} said softly. '
        f'"The kind thing now is to use safe hands and a calm plan."'
    )


def ending(world: World, a: Entity, b: Entity, parent: Entity, place: Place, lost: LostThing) -> None:
    if lost.id == "basket":
        saved = "The rescued basket still smelled green and sweet, and the asparagus tips peeked over the cloth."
    elif lost.id == "recipe_card":
        saved = "The little recipe card stayed dry enough for dinner, with only one corner curled from the splash."
    else:
        saved = "The hat came back with a shining drop on its brim, and everyone laughed when the breeze tried to steal it again."
    world.say(saved)
    world.say(
        f"Soon {a.id} and {b.id} were walking beside {parent.label_word} again, carrying asparagus together instead of arguing. "
        f"{place.ending_image}"
    )


def tell(place: Place, lost_cfg: LostThing, safe_tool: SafeTool,
         instigator_name: str = "Ben", instigator_gender: str = "boy",
         cautioner_name: str = "Lily", cautioner_gender: str = "girl",
         parent_type: str = "mother", trait: str = "careful",
         instigator_age: int = 6, cautioner_age: int = 7,
         relation: str = "siblings") -> World:
    world = World(place)

    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator_name,
        role="instigator",
        age=instigator_age,
        traits=["eager"],
    ))
    a.attrs["name"] = instigator_name

    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner_name,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
    ))
    b.attrs["name"] = cautioner_name

    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    water = world.add(Entity(id="water", type="water", label=place.shore))
    lost_ent = world.add(Entity(
        id="lost",
        type="lost",
        label=lost_cfg.label,
        phrase=lost_cfg.phrase,
        fragile=lost_cfg.fragile,
        buoyant=lost_cfg.buoyant,
        tags=set(lost_cfg.tags),
    ))
    lost_ent.attrs["plural"] = lost_cfg.plural
    world.add(Entity(
        id="harpoon",
        type="tool",
        label="harpoon",
        phrase="the old harpoon",
        sharp=True,
        tags={"harpoon", "sharp_tools"},
    ))

    world.facts.update(
        place=place,
        lost_cfg=lost_cfg,
        safe_tool=safe_tool,
        relation=relation,
        instigator_name=instigator_name,
        cautioner_name=cautioner_name,
        parent=parent,
    )

    introduce(world, a, b, place)
    world.para()
    drift(world, lost_ent, lost_cfg)
    notice_harpoon(world, a)
    warn(world, b, a, parent)

    outcome = "listened" if older_cautioner_can_stop(relation, instigator_age, cautioner_age, trait) else "guided"

    if outcome == "listened":
        back_down(world, a, b)
        world.para()
        intervene(world, parent, a, b)
        rescue(world, parent, safe_tool, lost_ent, lost_cfg)
        comfort(world, parent, a, b)
        ending(world, a, b, parent, place, lost_cfg)
    else:
        argue(world, a, b)
        world.para()
        intervene(world, parent, a, b)
        rescue(world, parent, safe_tool, lost_ent, lost_cfg)
        comfort(world, parent, a, b)
        ending(world, a, b, parent, place, lost_cfg)

    world.facts.update(
        instigator=a,
        cautioner=b,
        lost=lost_ent,
        outcome=outcome,
        retrieved=lost_ent.meters["retrieved"] >= THRESHOLD,
        conflict=a.memes["conflict"] >= THRESHOLD or b.memes["conflict"] >= THRESHOLD,
    )
    return world


PLACES = {
    "farm_pond": Place(
        id="farm_pond",
        label="the farm pond",
        scene="The water shone beside the long rows, and the cut asparagus lay in a wicker basket near the bank.",
        shore="the pond edge",
        asparagus_line="They liked helping pick the tall asparagus spears and laying them in neat green bundles.",
        ending_image="By the time the sun leaned low, the family was heading home with the safe tool put away and supper in mind.",
        tags={"pond", "asparagus"},
    ),
    "market_dock": Place(
        id="market_dock",
        label="the little market dock",
        scene="Crates of fresh asparagus waited under striped awnings, and the canal bumped softly against the boards.",
        shore="the canal edge",
        asparagus_line="A seller had given the children a few extra asparagus stalks to carry like tiny green flags.",
        ending_image="Soon the boards were warm under their shoes, and the whole dock smelled like bread, water, and fresh vegetables.",
        tags={"dock", "asparagus"},
    ),
    "garden_ditch": Place(
        id="garden_ditch",
        label="the kitchen garden ditch",
        scene="A narrow strip of water ran by the fence, where the asparagus patch stood feathery and tall in the afternoon light.",
        shore="the ditch edge",
        asparagus_line="The children had been choosing the straightest asparagus for soup and pretending each stalk was a green wand.",
        ending_image="A robin hopped along the fence as they walked back to the porch, and the asparagus leaves whispered in the breeze.",
        tags={"garden", "asparagus"},
    ),
    "barn_yard": Place(
        id="barn_yard",
        label="the barn yard",
        scene="The wheelbarrow was full of asparagus, but the ground was dry and dusty all the way to the gate.",
        water=False,
        shore="the dry yard",
        asparagus_line="There was no pond, canal, or ditch nearby, only straw and the sleepy barn cat.",
        ending_image="The evening still felt warm and gentle.",
        tags={"yard", "asparagus"},
    ),
}

LOST_THINGS = {
    "basket": LostThing(
        id="basket",
        label="basket",
        phrase="the asparagus basket",
        drift_line="A puff of wind tipped the asparagus basket off the bank, and it bobbed just out on the water.",
        rescue_line="In another moment the basket was back at the edge, dripping but safe.",
        distance=2,
        fragile=False,
        buoyant=True,
        tags={"basket", "asparagus"},
    ),
    "recipe_card": LostThing(
        id="recipe_card",
        label="recipe card",
        phrase="the little soup recipe card",
        drift_line="The recipe card for asparagus soup slipped from the picnic cloth and skated onto the water like a pale leaf.",
        rescue_line="The recipe card slid back into reach without tearing.",
        distance=1,
        fragile=True,
        buoyant=True,
        tags={"recipe", "asparagus"},
    ),
    "hat": LostThing(
        id="hat",
        label="hat",
        phrase="the straw hat",
        drift_line="A straw hat that had been shading the asparagus bundles tumbled from the bank and spun away in a lazy circle.",
        rescue_line="The hat came gliding back to shore, rocking once before it settled against the grass.",
        distance=2,
        fragile=True,
        buoyant=True,
        tags={"hat", "asparagus"},
    ),
}

SAFE_TOOLS = {
    "net": SafeTool(
        id="net",
        label="net",
        phrase="a long-handled net",
        reach=2,
        gentle=True,
        action="reached over the water with a long-handled net and lifted carefully",
        qa_text="used a long-handled net to lift it back gently",
        tags={"net", "safe_tools"},
    ),
    "boat_hook": SafeTool(
        id="boat_hook",
        label="boat hook",
        phrase="the smooth boat hook",
        reach=3,
        gentle=False,
        action="eased the smooth boat hook under the drifting thing and drew it in slowly",
        qa_text="used a boat hook to draw it in slowly",
        tags={"boat_hook", "safe_tools"},
    ),
    "rake": SafeTool(
        id="rake",
        label="rake",
        phrase="a small garden rake",
        reach=1,
        gentle=False,
        action="stretched out with a small garden rake and tugged the edge back",
        qa_text="used a small garden rake to tug it back",
        tags={"rake", "safe_tools"},
    ),
}


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo", "Eli", "Jack"]
TRAITS = ["careful", "gentle", "patient", "thoughtful", "curious", "brisk"]


@dataclass
class StoryParams:
    place: str
    lost: str
    safe_tool: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 7
    seed: Optional[int] = None


KNOWLEDGE = {
    "asparagus": [
        (
            "What is asparagus?",
            "Asparagus is a green spring vegetable with long tender stalks. People cook it for meals like soup or supper."
        )
    ],
    "harpoon": [
        (
            "What is a harpoon?",
            "A harpoon is a long sharp tool made for catching large animals in the water. It is dangerous and not for children to handle."
        )
    ],
    "sharp_tools": [
        (
            "Why should children leave sharp tools to grown-ups?",
            "Sharp tools can cut, poke, or slip very quickly. A grown-up has stronger control and knows the safe way to use them."
        )
    ],
    "net": [
        (
            "What is a long-handled net good for?",
            "A long-handled net can scoop up something from the water without poking it. That makes it gentle for light or delicate things."
        )
    ],
    "boat_hook": [
        (
            "What is a boat hook?",
            "A boat hook is a long pole with a curved end. Grown-ups use it to pull floating things closer from a boat or dock."
        )
    ],
    "rake": [
        (
            "What is a garden rake for?",
            "A garden rake is a tool for pulling leaves or soil into place. It is not as gentle as a net for delicate things on the water."
        )
    ],
    "pond": [
        (
            "Why can things drift away on a pond?",
            "Wind and little ripples can push light things across the surface. Even a slow drift can move them out of reach."
        )
    ],
    "dock": [
        (
            "What is a dock?",
            "A dock is a platform by the water where people can stand or tie up small boats. It lets people reach the edge more safely."
        )
    ],
    "garden": [
        (
            "What is a garden ditch?",
            "A garden ditch is a narrow strip of water or a little channel by a garden. It helps move water, but things can still slip into it."
        )
    ],
    "safe_tools": [
        (
            "What should you do if something falls into water and you cannot reach it safely?",
            "Stop and ask a grown-up for help. A safe tool and a calm plan are better than grabbing something dangerous."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "asparagus", "harpoon", "sharp_tools", "pond", "dock", "garden",
    "net", "boat_hook", "rake", "safe_tools",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    instigator = f["instigator"]
    cautioner = f["cautioner"]
    lost_cfg = f["lost_cfg"]
    place = f["place"]
    safe_tool = f["safe_tool"]
    outcome = f["outcome"]
    if outcome == "listened":
        return [
            'Write a heartwarming conflict story for a 3-to-5-year-old that includes the words "asparagus" and "harpoon".',
            f"Tell a gentle story where {instigator.attrs['name']} wants to use a harpoon to reach a drifting {lost_cfg.label} at {place.label}, but {cautioner.attrs['name']} talks {instigator.pronoun('object')} out of it and a grown-up uses {safe_tool.phrase} instead.",
            "Write a story about a small argument, a dangerous idea, and a calm family ending with asparagus carried home together.",
        ]
    return [
        'Write a heartwarming conflict story for a 3-to-5-year-old that includes the words "asparagus" and "harpoon".',
        f"Tell a gentle story where {instigator.attrs['name']} reaches toward an old harpoon after a {lost_cfg.label} drifts away, but a grown-up steps in and solves the problem with {safe_tool.phrase}.",
        "Write a story where children disagree for a moment, then learn that a safe tool and calm words are better than a sharp one.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    place = f["place"]
    lost_cfg = f["lost_cfg"]
    safe_tool = f["safe_tool"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.attrs['name']} and {b.attrs['name']}, and their {parent.label_word}. They were spending time near {place.label} during asparagus time."
        ),
        (
            "What problem started the conflict?",
            f"The {lost_cfg.label} drifted out on the water, and {a.attrs['name']} wanted to use the old harpoon to get it back. {b.attrs['name']} disagreed because the harpoon was sharp and unsafe for children."
        ),
        (
            f"Why did {b.attrs['name']} say no to the harpoon?",
            f"{b.attrs['name']} knew the harpoon was a dangerous sharp tool. The warning mattered because everybody was already worried about the drifting {lost_cfg.label}, and a sharp tool would only make the moment harder."
        ),
    ]
    if f["outcome"] == "listened":
        qa.append(
            (
                f"What did {a.attrs['name']} do after listening?",
                f"{a.attrs['name']} stepped back from the old harpoon and agreed not to touch it. That changed the scene from an argument into a calm wait for the grown-up's help."
            )
        )
    else:
        qa.append(
            (
                f"Did the children stay upset?",
                f"No. They argued for a moment, but their {parent.label_word} came over before anyone touched the harpoon. The grown-up's calm voice helped turn the conflict into a safer plan."
            )
        )
    qa.append(
        (
            f"How did their {parent.label_word} solve the problem?",
            f"Their {parent.label_word} {safe_tool.qa_text}. That worked because {safe_tool.label} could reach the drifting {lost_cfg.label} without needing the dangerous harpoon."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended warmly, with the drifting {lost_cfg.label} safe again and the family walking together with asparagus. The ending shows that the children had moved from conflict to cooperation."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"asparagus", "harpoon", "sharp_tools", "safe_tools"}
    place = world.facts["place"]
    safe_tool = world.facts["safe_tool"]
    lost_cfg = world.facts["lost_cfg"]
    tags |= set(place.tags)
    tags |= set(safe_tool.tags)
    tags |= set(lost_cfg.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.sharp:
            flags.append("sharp")
        if e.safe_retriever:
            flags.append("safe_retriever")
        if e.fragile:
            flags.append("fragile")
        if e.buoyant:
            flags.append("buoyant")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="farm_pond",
        lost="basket",
        safe_tool="net",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        place="market_dock",
        lost="recipe_card",
        safe_tool="net",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="gentle",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        place="garden_ditch",
        lost="hat",
        safe_tool="boat_hook",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
    ),
    StoryParams(
        place="farm_pond",
        lost="recipe_card",
        safe_tool="net",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Ava",
        cautioner_gender="girl",
        parent="father",
        trait="patient",
        relation="siblings",
        instigator_age=4,
        cautioner_age=8,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
fragile_need_gentle(L) :- lost(L), fragile(L).
can_reach(Tool, Lost)  :- tool(Tool), lost(Lost), reach(Tool, R), distance(Lost, D), R >= D.
gentle_enough(Tool, Lost) :- tool(Tool), lost(Lost), not fragile_need_gentle(Lost).
gentle_enough(Tool, Lost) :- tool(Tool), lost(Lost), fragile_need_gentle(Lost), gentle(Tool).
valid(Place, Lost, Tool) :- place(Place), has_water(Place), lost(Lost), tool(Tool),
                            can_reach(Tool, Lost), gentle_enough(Tool, Lost).

% --- outcome model ---------------------------------------------------------
calm_trait(T) :- trait(T), calm(T).
older_cautioner :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
listened :- older_cautioner, calm_trait(T).
guided   :- not listened.
outcome(listened) :- listened.
outcome(guided)   :- guided.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.water:
            lines.append(asp.fact("has_water", place_id))
    for lost_id, lost in LOST_THINGS.items():
        lines.append(asp.fact("lost", lost_id))
        lines.append(asp.fact("distance", lost_id, lost.distance))
        if lost.fragile:
            lines.append(asp.fact("fragile", lost_id))
    for tool_id, tool in SAFE_TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        if tool.gentle:
            lines.append(asp.fact("gentle", tool_id))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm", trait))
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
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: asparagus by the water, a dangerous harpoon, and a heartwarming calm solution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--safe-tool", choices=SAFE_TOOLS, dest="safe_tool")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and not PLACES[args.place].water:
        lost = LOST_THINGS[args.lost] if args.lost else next(iter(LOST_THINGS.values()))
        raise StoryError(explain_rejection(PLACES[args.place], lost))
    if args.place and args.lost and args.safe_tool:
        place = PLACES[args.place]
        lost = LOST_THINGS[args.lost]
        tool = SAFE_TOOLS[args.safe_tool]
        if not valid_combo(place, lost, tool):
            raise StoryError(explain_rejection(place, lost, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.lost is None or combo[1] == args.lost)
        and (args.safe_tool is None or combo[2] == args.safe_tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, lost_id, tool_id = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        place=place_id,
        lost=lost_id,
        safe_tool=tool_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.lost not in LOST_THINGS:
        raise StoryError(f"(Invalid lost thing: {params.lost})")
    if params.safe_tool not in SAFE_TOOLS:
        raise StoryError(f"(Invalid safe tool: {params.safe_tool})")

    place = PLACES[params.place]
    lost = LOST_THINGS[params.lost]
    safe_tool = SAFE_TOOLS[params.safe_tool]
    if not valid_combo(place, lost, safe_tool):
        raise StoryError(explain_rejection(place, lost, safe_tool))

    world = tell(
        place=place,
        lost_cfg=lost,
        safe_tool=safe_tool,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
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
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, lost, safe_tool) combos:\n")
        for place, lost, tool in combos:
            print(f"  {place:12} {lost:12} {tool}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.lost} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
