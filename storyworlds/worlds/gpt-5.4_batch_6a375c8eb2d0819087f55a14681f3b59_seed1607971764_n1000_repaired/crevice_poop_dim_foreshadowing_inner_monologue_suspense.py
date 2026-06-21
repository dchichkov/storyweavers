#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py
======================================================================================

A standalone storyworld for a tiny rhyming rescue tale:

A child and a grown-up hear a small creature trapped in a crevice.
The place is poop-dim and shadowy, the child feels suspense, thinks in
little inner-monologue beats, and the ending image proves that care and the
right rescue tool changed everything.

This world models:
- typed entities with physical meters and emotional memes
- a reasonableness gate over rescue plans
- a state-driven story with foreshadowing, inner monologue, and suspense
- a Python gate plus an inline ASP twin

Run it
------
    python storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py
    python storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py --animal chick --crevice wall_crack
    python storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py --tool broom
    python storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py --all
    python storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/crevice_poop_dim_foreshadowing_inner_monologue_suspense.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    scared_sound: str = ""
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Place:
    id: str
    label: str
    entry_line: str
    dim_line: str
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
class Animal:
    id: str
    label: str
    cry: str
    tiny_word: str
    movement: str
    fragile: bool
    likes: str
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
class CreviceCfg:
    id: str
    label: str
    width: int
    depth: int
    floor: str
    shadow_line: str
    threat_line: str
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
    reach: int
    narrowness: int
    gentleness: int
    sense: int
    action_text: str
    fail_text: str
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


def _r_animal_distress(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    crevice = world.get("crevice")
    child = world.get("child")
    if animal.meters["trapped"] < THRESHOLD:
        return out
    sig = ("distress", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.memes["fear"] += 1
    child.memes["worry"] += 1
    crevice.meters["danger"] += 1
    out.append("__distress__")
    return out


def _r_deeper_if_wrong_tool(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    crevice = world.get("crevice")
    if world.facts.get("attempted_bad_tool") != 1:
        return out
    sig = ("slip", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["depth"] += 1
    animal.memes["fear"] += 1
    crevice.meters["danger"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="animal_distress", tag="physical", apply=_r_animal_distress),
    Rule(name="deeper_if_wrong_tool", tag="physical", apply=_r_deeper_if_wrong_tool),
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


def fits(tool: Tool, crevice: CreviceCfg) -> bool:
    return tool.narrowness <= crevice.width


def reaches(tool: Tool, crevice: CreviceCfg) -> bool:
    return tool.reach >= crevice.depth


def gentle_enough(tool: Tool, animal: Animal) -> bool:
    needed = 2 if animal.fragile else 1
    return tool.gentleness >= needed


def rescue_possible(tool: Tool, crevice: CreviceCfg, animal: Animal) -> bool:
    return fits(tool, crevice) and reaches(tool, crevice) and gentle_enough(tool, animal)


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for animal_id, animal in ANIMALS.items():
            for crevice_id, crevice in CREVICES.items():
                for tool_id, tool in TOOLS.items():
                    if tool.sense >= SENSE_MIN and rescue_possible(tool, crevice, animal):
                        combos.append((place_id, animal_id, crevice_id, tool_id))
    return combos


def explain_tool_rejection(tool: Tool, crevice: CreviceCfg, animal: Animal) -> str:
    reasons: list[str] = []
    if tool.sense < SENSE_MIN:
        reasons.append(f"'{tool.label}' is not a careful rescue choice here")
    if not fits(tool, crevice):
        reasons.append(f"it is too wide for {crevice.label}")
    if not reaches(tool, crevice):
        reasons.append(f"it cannot reach far enough into {crevice.label}")
    if not gentle_enough(tool, animal):
        reasons.append(f"it is too rough for a {animal.label}")
    if not reasons:
        reasons.append("this combination is unreasonable")
    return "(No story: " + "; ".join(reasons) + ".)"


def predict_rescue(world: World, tool_id: str) -> dict:
    sim = world.copy()
    tool = TOOLS[tool_id]
    animal_cfg: Animal = sim.facts["animal_cfg"]
    crevice_cfg: CreviceCfg = sim.facts["crevice_cfg"]
    possible = rescue_possible(tool, crevice_cfg, animal_cfg)
    if possible:
        sim.get("animal").meters["trapped"] = 0.0
        sim.get("animal").meters["rescued"] += 1
        sim.get("crevice").meters["danger"] = 0.0
    else:
        sim.facts["attempted_bad_tool"] = 1
        propagate(sim, narrate=False)
    return {
        "possible": possible,
        "fear": sim.get("animal").memes["fear"],
        "danger": sim.get("crevice").meters["danger"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["curious"] += 1
    world.say(
        f"{place.entry_line} {child.id} walked with {child.pronoun('possessive')} "
        f"{helper.label_word} through the hush of {place.label}."
    )
    world.say(
        f"{place.dim_line} Even the air felt poop-dim, soft and brown and slim, "
        f"as if the day had folded in on whim."
    )


def foreshadow(world: World, crevice_cfg: CreviceCfg) -> None:
    world.say(
        f"Along the wall ran {crevice_cfg.label}, {crevice_cfg.shadow_line}. "
        f"It looked too still, too thin, too grim."
    )


def hear_cry(world: World, child: Entity, animal: Entity, animal_cfg: Animal) -> None:
    animal.meters["trapped"] += 1
    animal.meters["depth"] = float(world.facts["crevice_cfg"].depth)
    propagate(world, narrate=False)
    world.say(
        f"Then came {animal_cfg.cry} from somewhere low and dim. "
        f'"Did you hear that tiny sound?" whispered {child.id}.'
    )


def search(world: World, child: Entity, crevice_cfg: CreviceCfg, animal_cfg: Animal) -> None:
    child.memes["suspense"] += 1
    world.say(
        f"{child.id} knelt near the crevice and peered past dust and stone. "
        f"There, on {crevice_cfg.floor}, sat the {animal_cfg.tiny_word} {animal_cfg.label} alone."
    )


def inner_monologue(world: World, child: Entity, crevice_cfg: CreviceCfg) -> None:
    world.say(
        f'{child.id} thought, "Oh hush, brave heart, stay trim. '
        f'If I rush at {crevice_cfg.label}, I may scare it farther in."'
    )


def wrong_idea(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["impulse"] += 1
    world.say(
        f'"What if we use {tool.label}?" asked {child.id}. '
        f'{helper.label_word.capitalize()} looked once and did not grin.'
    )


def caution(world: World, helper: Entity, tool: Tool, animal_cfg: Animal, crevice_cfg: CreviceCfg) -> None:
    pred = predict_rescue(world, tool.id)
    world.facts["predicted_possible"] = pred["possible"]
    world.facts["predicted_danger"] = pred["danger"]
    if pred["possible"]:
        world.say(
            f'"That might just work," said {helper.label_word}, very low and very thin, '
            f'"if we move with patient hands and let the rescue begin."'
        )
    else:
        world.say(
            f'"No, not {tool.label}," said {helper.label_word}. '
            f'"{crevice_cfg.threat_line}, and a {animal_cfg.label} is small and thin."'
        )


def choose_good_tool(world: World, helper: Entity, tool: Tool) -> None:
    world.say(
        f'{helper.label_word.capitalize()} reached for {tool.label}, steady and slow, '
        f'with eyes that seemed to measure every place the little one might go.'
    )


def attempt_fail(world: World, tool: Tool, animal: Entity, crevice: Entity) -> None:
    world.facts["attempted_bad_tool"] = 1
    propagate(world, narrate=False)
    animal.meters["trapped"] += 0.5
    crevice.meters["danger"] += 0.5
    world.say(
        f"But {tool.fail_text}. The sound went smaller, sharper, thin. "
        f"For one long blink, it seemed the poor small thing might slip farther in."
    )


def rescue(world: World, tool: Tool, animal: Entity, helper: Entity, child: Entity, animal_cfg: Animal) -> None:
    animal.meters["trapped"] = 0.0
    animal.meters["rescued"] += 1
    animal.meters["depth"] = 0.0
    animal.memes["fear"] = 0.0
    animal.memes["relief"] += 1
    child.memes["relief"] += 1
    child.memes["care"] += 1
    helper.memes["care"] += 1
    world.get("crevice").meters["danger"] = 0.0
    world.say(
        f"{tool.action_text}. Up came the {animal_cfg.label}, wobbling light as a pin, "
        f"but safe at last against the day and not lost deep within."
    )


def comfort(world: World, child: Entity, animal_cfg: Animal) -> None:
    world.say(
        f'{child.id} held still and breathed out slow. "You are safe now, little {animal_cfg.label}," '
        f'{child.pronoun()} said. The frightened sound was gone; in its place came a soft small glow.'
    )


def release(world: World, child: Entity, helper: Entity, animal_cfg: Animal) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"They set the {animal_cfg.label} where the warm straw lay. "
        f"It gave one bright {animal_cfg.movement}, then tucked itself away."
    )
    world.say(
        f"And {child.id} smiled to see what patient hands had done that day: "
        f"the poop-dim place was only dim until kind care showed the way."
    )


def tell(
    place: Place,
    animal_cfg: Animal,
    crevice_cfg: CreviceCfg,
    good_tool: Tool,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
    wrong_tool: Optional[Tool] = None,
) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(
        Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper")
    )
    crevice = world.add(
        Entity(id="crevice", type="crevice", label=crevice_cfg.label, attrs={"width": crevice_cfg.width})
    )
    animal = world.add(
        Entity(
            id="animal",
            type=animal_cfg.id,
            label=animal_cfg.label,
            role="animal",
            fragile=animal_cfg.fragile,
            scared_sound=animal_cfg.cry,
        )
    )

    world.facts.update(
        place=place,
        animal_cfg=animal_cfg,
        crevice_cfg=crevice_cfg,
        tool_cfg=good_tool,
        wrong_tool=wrong_tool,
        attempted_bad_tool=0,
    )

    introduce(world, child, helper, place)
    foreshadow(world, crevice_cfg)

    world.para()
    hear_cry(world, child, animal, animal_cfg)
    search(world, child, crevice_cfg, animal_cfg)
    inner_monologue(world, child, crevice_cfg)

    world.para()
    if wrong_tool is not None:
        wrong_idea(world, child, helper, wrong_tool)
        caution(world, helper, wrong_tool, animal_cfg, crevice_cfg)
        attempt_fail(world, wrong_tool, animal, crevice)
        world.para()

    choose_good_tool(world, helper, good_tool)
    rescue(world, good_tool, animal, helper, child, animal_cfg)
    comfort(world, child, animal_cfg)

    world.para()
    release(world, child, helper, animal_cfg)

    world.facts.update(
        child=child,
        helper=helper,
        animal=animal,
        rescued=animal.meters["rescued"] >= THRESHOLD,
        danger=crevice.meters["danger"],
        suspense=child.memes["suspense"] >= THRESHOLD,
    )
    return world


PLACES = {
    "coop": Place(
        id="coop",
        label="the hen coop",
        entry_line="Past the seed bin and the latch with a rusty rim,",
        dim_line="The window wore old dust and feather-smudges",
        tags={"coop", "dim"},
    ),
    "barn": Place(
        id="barn",
        label="the barn wall",
        entry_line="By the hay bales stacked in a sleepy brim,",
        dim_line="The rafters kept the noon light low and grain-dim",
        tags={"barn", "dim"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        entry_line="Near the watering cans and the rake hung trim,",
        dim_line="The boards let in only skinny stripes of light",
        tags={"shed", "dim"},
    ),
}

ANIMALS = {
    "chick": Animal(
        id="chick",
        label="chick",
        cry="peep-peep-peep",
        tiny_word="downy",
        movement="hop",
        fragile=True,
        likes="warm straw",
        tags={"chick", "careful"},
    ),
    "mouse": Animal(
        id="mouse",
        label="mouse",
        cry="eep-eep",
        tiny_word="quivering",
        movement="scurry",
        fragile=False,
        likes="seed husks",
        tags={"mouse", "careful"},
    ),
    "toad": Animal(
        id="toad",
        label="toad",
        cry="tiny scritch-scritch",
        tiny_word="mottled",
        movement="plop",
        fragile=False,
        likes="cool dirt",
        tags={"toad", "careful"},
    ),
}

CREVICES = {
    "wall_crack": CreviceCfg(
        id="wall_crack",
        label="a wall crevice",
        width=1,
        depth=2,
        floor="cool grit",
        shadow_line="a narrow mouth under a board, black-slim and still",
        threat_line="it will only poke too hard and drive the little one deeper",
        tags={"crevice", "narrow"},
    ),
    "stone_gap": CreviceCfg(
        id="stone_gap",
        label="a stone crevice",
        width=1,
        depth=3,
        floor="cold pebbles",
        shadow_line="a pinched gray seam between two stones, dusk-thin and chill",
        threat_line="it will scrape the sides and make the scared one slip deeper",
        tags={"crevice", "stone"},
    ),
    "beam_split": CreviceCfg(
        id="beam_split",
        label="a beam crevice",
        width=2,
        depth=2,
        floor="dry splinters",
        shadow_line="a split in old wood, long as a finger and dark at the rim",
        threat_line="it may be clumsy in there and frighten the trapped one deeper",
        tags={"crevice", "wood"},
    ),
}

TOOLS = {
    "ribbon_loop": Tool(
        id="ribbon_loop",
        label="a ribbon loop on a spoon handle",
        reach=3,
        narrowness=1,
        gentleness=3,
        sense=3,
        action_text="Grandma slid the ribbon loop in softly and lifted with a tender grin",
        fail_text="the loop sagged and slid away",
        qa_text="used a soft ribbon loop on a spoon handle to lift it out gently",
        tags={"gentle_tool", "rescue"},
    ),
    "oven_mitt": Tool(
        id="oven_mitt",
        label="an oven mitt",
        reach=1,
        narrowness=3,
        gentleness=2,
        sense=2,
        action_text="Dad reached only as far as the edge, and the mitt could not go in",
        fail_text="the mitt was much too puffy for the slot",
        qa_text="tried to use an oven mitt",
        tags={"mitt"},
    ),
    "cardboard_scoop": Tool(
        id="cardboard_scoop",
        label="a thin cardboard scoop",
        reach=2,
        narrowness=1,
        gentleness=2,
        sense=3,
        action_text="Dad eased the thin scoop under the little body and slid it back out again",
        fail_text="the scoop bent and could not tuck under safely",
        qa_text="slid a thin cardboard scoop under it and drew it out gently",
        tags={"gentle_tool", "rescue"},
    ),
    "broom": Tool(
        id="broom",
        label="a broom handle",
        reach=3,
        narrowness=1,
        gentleness=0,
        sense=1,
        action_text="the broom handle nudged too roughly to be kind",
        fail_text="the broom handle tapped the stone in a harsh dry din",
        qa_text="tried a broom handle",
        tags={"rough_tool"},
    ),
    "tongs": Tool(
        id="tongs",
        label="kitchen tongs",
        reach=2,
        narrowness=1,
        gentleness=1,
        sense=2,
        action_text="Grandpa pinched the tongs around the cardboard guide and drew the little one in",
        fail_text="the tongs clicked too sharply and the trapped thing shrank farther in",
        qa_text="used kitchen tongs very carefully with a guide",
        tags={"tongs"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tess", "Ivy", "Wren", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Jude", "Eli", "Nico", "Ben"]


@dataclass
class StoryParams:
    place: str
    animal: str
    crevice: str
    tool: str
    wrong_tool: str
    child_name: str
    child_gender: str
    helper_type: str
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
        place="coop",
        animal="chick",
        crevice="wall_crack",
        tool="ribbon_loop",
        wrong_tool="broom",
        child_name="Mina",
        child_gender="girl",
        helper_type="grandmother",
        seed=None,
    ),
    StoryParams(
        place="barn",
        animal="mouse",
        crevice="beam_split",
        tool="cardboard_scoop",
        wrong_tool="oven_mitt",
        child_name="Owen",
        child_gender="boy",
        helper_type="grandfather",
        seed=None,
    ),
    StoryParams(
        place="shed",
        animal="toad",
        crevice="stone_gap",
        tool="ribbon_loop",
        wrong_tool="tongs",
        child_name="Ivy",
        child_gender="girl",
        helper_type="father",
        seed=None,
    ),
    StoryParams(
        place="barn",
        animal="chick",
        crevice="beam_split",
        tool="cardboard_scoop",
        wrong_tool="broom",
        child_name="Theo",
        child_gender="boy",
        helper_type="mother",
        seed=None,
    ),
]


KNOWLEDGE = {
    "crevice": [
        (
            "What is a crevice?",
            "A crevice is a very narrow crack or gap in stone or wood. Small things can slip into it and be hard to reach.",
        )
    ],
    "chick": [
        (
            "Why must you be gentle with a chick?",
            "A chick is tiny and delicate, so rough poking can hurt it or scare it badly. Gentle hands help it stay safe and calm.",
        )
    ],
    "mouse": [
        (
            "Why can a trapped mouse be hard to help?",
            "A trapped mouse is small and quick, and when it is frightened it may hide deeper. Slow, careful movements keep it from darting away.",
        )
    ],
    "toad": [
        (
            "Why should you move slowly around a toad?",
            "Toads can get startled and try to wriggle away when something rushes at them. Calm, slow rescue gives them a better chance to stay still.",
        )
    ],
    "gentle_tool": [
        (
            "Why is a soft or thin tool useful in a narrow gap?",
            "A soft or thin tool can fit into the gap and reach the trapped animal without scraping or pushing too hard. That makes rescue safer.",
        )
    ],
    "rough_tool": [
        (
            "Why is a rough stick or broom a bad rescue tool for a tiny animal?",
            "A rough tool may poke too hard or frighten the animal deeper into the crack. In a tight place, gentleness matters more than force.",
        )
    ],
    "suspense": [
        (
            "What is suspense in a story?",
            "Suspense is the worried feeling you get when you do not know what will happen next. It makes you lean in and hope for a good ending.",
        )
    ],
    "foreshadow": [
        (
            "What is foreshadowing?",
            "Foreshadowing is when a story gives a little early hint about trouble or a big moment that is coming later. It helps the middle feel exciting and connected.",
        )
    ],
    "inner_monologue": [
        (
            "What is inner monologue?",
            "Inner monologue is the quiet talk a character says inside their own mind. It lets readers know what the character is thinking and feeling.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "crevice",
    "chick",
    "mouse",
    "toad",
    "gentle_tool",
    "rough_tool",
    "suspense",
    "foreshadow",
    "inner_monologue",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    animal_cfg: Animal = f["animal_cfg"]
    crevice_cfg: CreviceCfg = f["crevice_cfg"]
    tool: Tool = f["tool_cfg"]
    return [
        (
            f'Write a rhyming story for a 3-to-5-year-old that includes the words '
            f'"crevice" and "poop-dim", where {child.id} hears a trapped {animal_cfg.label} '
            f'in {crevice_cfg.label} and helps rescue it.'
        ),
        (
            f"Tell a suspenseful but gentle rhyme about a child who spots a tiny {animal_cfg.label} "
            f"in {crevice_cfg.label}, thinks carefully inside {child.pronoun('possessive')} own head, "
            f"and watches a grown-up use {tool.label} to help."
        ),
        (
            "Write a short story in rhyming lines that uses foreshadowing, inner monologue, "
            "and suspense, ending with a small creature safe in the light."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    animal_cfg: Animal = f["animal_cfg"]
    crevice_cfg: CreviceCfg = f["crevice_cfg"]
    tool: Tool = f["tool_cfg"]
    wrong_tool = f.get("wrong_tool")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {helper.label_word}, and a trapped {animal_cfg.label}. They are together in a dim place where a careful rescue must happen.",
        ),
        (
            f"Where was the {animal_cfg.label}?",
            f"The little {animal_cfg.label} was stuck in {crevice_cfg.label}. It was down on {crevice_cfg.floor}, which made it hard to reach and added suspense.",
        ),
        (
            "Why did the story feel suspenseful?",
            f"It felt suspenseful because the child could hear the tiny cries before the rescue worked, and the narrow crevice made everything uncertain. The danger was small but real, so every careful choice mattered.",
        ),
        (
            "What was the child's inner monologue?",
            f"{child.id} told {child.pronoun('object')}self not to rush, because hurrying might scare the trapped animal deeper in. That private thought showed {child.pronoun('possessive')} worry and helped guide the careful rescue.",
        ),
    ]
    if wrong_tool is not None:
        qa.append(
            (
                f"Why did they not use {wrong_tool.label}?",
                f"They did not use {wrong_tool.label} because it was not a safe rescue choice for that crevice and that animal. It could have been too rough or clumsy, and that might have pushed the little {animal_cfg.label} farther in.",
            )
        )
    qa.append(
        (
            f"How did {helper.label_word} rescue the {animal_cfg.label}?",
            f"{helper.label_word.capitalize()} {tool.qa_text}. The tool fit the crevice and was gentle enough, so the rescue worked without frightening the tiny animal deeper inside.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the little {animal_cfg.label} safe again, no longer trapped in the crevice. The final image shows that the poop-dim place did not stay scary once kind, patient care brought relief.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"crevice", "suspense", "foreshadow", "inner_monologue"}
    tags |= set(f["animal_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    wrong_tool = f.get("wrong_tool")
    if wrong_tool is not None:
        tags |= set(wrong_tool.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.fragile:
            bits.append("fragile=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.

needs_gentle(A,2) :- animal(A), fragile(A).
needs_gentle(A,1) :- animal(A), not fragile(A).

fits(T,C)    :- tool(T), crevice(C), narrowness(T,N), width(C,W), N <= W.
reaches(T,C) :- tool(T), crevice(C), reach(T,R), depth(C,D), R >= D.
gentle(T,A)  :- tool(T), animal(A), gentleness(T,G), needs_gentle(A,Need), G >= Need.

rescue_possible(T,C,A) :- sensible_tool(T), fits(T,C), reaches(T,C), gentle(T,A).
valid(P,A,C,T) :- place(P), animal(A), crevice(C), rescue_possible(T,C,A).

#show sensible_tool/1.
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        if animal.fragile:
            lines.append(asp.fact("fragile", aid))
    for cid, crevice in CREVICES.items():
        lines.append(asp.fact("crevice", cid))
        lines.append(asp.fact("width", cid, crevice.width))
        lines.append(asp.fact("depth", cid, crevice.depth))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("reach", tid, tool.reach))
        lines.append(asp.fact("narrowness", tid, tool.narrowness))
        lines.append(asp.fact("gentleness", tid, tool.gentleness))
        lines.append(asp.fact("sense", tid, tool.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show_override: str = "") -> str:
    if show_override:
        return f"{asp_facts()}\n{ASP_RULES}\n{show_override}\n"
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {t.id for t in sensible_tools()}
    asp_sensible = set(asp_sensible_tools())
    if py_sensible == asp_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: python={sorted(py_sensible)} clingo={sorted(asp_sensible)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming rescue storyworld: a tiny creature in a crevice, a poop-dim place, suspense, and a careful rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--crevice", choices=CREVICES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--wrong-tool", choices=TOOLS, dest="wrong_tool")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.animal and args.crevice:
        tool = TOOLS[args.tool]
        animal = ANIMALS[args.animal]
        crevice = CREVICES[args.crevice]
        if not rescue_possible(tool, crevice, animal) or tool.sense < SENSE_MIN:
            raise StoryError(explain_tool_rejection(tool, crevice, animal))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.animal is None or c[1] == args.animal)
        and (args.crevice is None or c[2] == args.crevice)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, animal, crevice, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])

    wrong_candidates = [
        tid
        for tid, t in TOOLS.items()
        if tid != tool and (
            t.sense < SENSE_MIN or not rescue_possible(t, CREVICES[crevice], ANIMALS[animal])
        )
    ]
    if args.wrong_tool:
        chosen_wrong = args.wrong_tool
    else:
        chosen_wrong = rng.choice(sorted(wrong_candidates)) if wrong_candidates else tool

    return StoryParams(
        place=place,
        animal=animal,
        crevice=crevice,
        tool=tool,
        wrong_tool=chosen_wrong,
        child_name=name,
        child_gender=gender,
        helper_type=helper_type,
        seed=None,
    )


def _require_key(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    place = _require_key(PLACES, params.place, "place")
    animal = _require_key(ANIMALS, params.animal, "animal")
    crevice = _require_key(CREVICES, params.crevice, "crevice")
    tool = _require_key(TOOLS, params.tool, "tool")
    wrong_tool = _require_key(TOOLS, params.wrong_tool, "wrong tool")

    if tool.sense < SENSE_MIN or not rescue_possible(tool, crevice, animal):
        raise StoryError(explain_tool_rejection(tool, crevice, animal))

    world = tell(
        place=place,
        animal_cfg=animal,
        crevice_cfg=crevice,
        good_tool=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        wrong_tool=wrong_tool,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_tools()
        print(f"sensible tools: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, animal, crevice, tool) combos:\n")
        for place, animal, crevice, tool in combos:
            print(f"  {place:6} {animal:6} {crevice:10} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.animal} in {p.crevice} ({p.place}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
