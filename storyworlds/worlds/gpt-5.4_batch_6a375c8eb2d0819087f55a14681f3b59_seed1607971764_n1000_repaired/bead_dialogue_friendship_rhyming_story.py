#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bead_dialogue_friendship_rhyming_story.py
====================================================================

A small story world about two friends making matching bead keepsakes, a snapped
string, and the way kind dialogue turns a little craft disaster into a stronger
friendship.

The world models:
- typed entities with physical meters and emotional memes
- a simple forward-chaining causal layer
- a reasonableness gate for craft-material compatibility
- an inline ASP twin for the same compatibility rules and the ending model
- child-facing prose in a gentle rhyming style with dialogue

Run it
------
    python storyworlds/worlds/gpt-5.4/bead_dialogue_friendship_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/bead_dialogue_friendship_rhyming_story.py --asp
    python storyworlds/worlds/gpt-5.4/bead_dialogue_friendship_rhyming_story.py --verify
    python storyworlds/worlds/gpt-5.4/bead_dialogue_friendship_rhyming_story.py -n 5 --seed 7 --qa
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
class Spot:
    id: str
    place: str
    seat: str
    surface: str
    stop: int
    description: str
    ending_image: str
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
class Project:
    id: str
    label: str
    plural: str
    wear_line: str
    need_strength: int
    scatter: int
    gift_line: str
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
class BeadKind:
    id: str
    label: str
    phrase: str
    hole: int
    weight: int
    roll: int
    shine: str
    color: str
    backup: str
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
class Cord:
    id: str
    label: str
    phrase: str
    thickness: int
    strength: int
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
    def __init__(self, spot: Spot) -> None:
        self.spot = spot
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
        return [e for e in self.entities.values() if e.role in {"maker", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.spot)
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


def _r_snap_scatter(world: World) -> list[str]:
    out: list[str] = []
    cord = world.get("cord")
    beads = world.get("beads")
    if cord.meters["snapped"] < THRESHOLD:
        return out
    sig = ("scatter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beads.meters["loose"] += 1
    beads.meters["scattered"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__scatter__")
    return out


def _r_roll_loss(world: World) -> list[str]:
    out: list[str] = []
    beads = world.get("beads")
    centerpiece = world.get("centerpiece")
    if beads.meters["loose"] < THRESHOLD:
        return out
    severity = world.facts.get("severity", 0)
    if severity < 3:
        return out
    sig = ("lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    centerpiece.meters["lost"] += 1
    beads.meters["missing"] += 1
    out.append("__lost__")
    return out


CAUSAL_RULES = [
    Rule(name="snap_scatter", tag="physical", apply=_r_snap_scatter),
    Rule(name="roll_loss", tag="physical", apply=_r_roll_loss),
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


def compatible(project: Project, bead: BeadKind, cord: Cord) -> bool:
    return cord.thickness <= bead.hole and cord.strength >= project.need_strength


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(spot: Spot, project: Project, bead: BeadKind) -> int:
    return bead.roll + project.scatter + (2 - spot.stop)


def recovered(response: Response, spot: Spot, project: Project, bead: BeadKind) -> bool:
    return response.power >= spill_severity(spot, project, bead)


def predict_loss(world: World) -> dict:
    sim = world.copy()
    _do_snap(sim, narrate=False)
    return {
        "lost": sim.get("centerpiece").meters["lost"] >= THRESHOLD,
        "severity": sim.facts.get("severity", 0),
    }


def _do_snap(world: World, narrate: bool = True) -> None:
    cord = world.get("cord")
    cord.meters["snapped"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, spot: Spot, project: Project,
              bead: BeadKind, cord: Cord) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright little day at {spot.place}, {a.id} and {b.id} sat on {spot.seat}. "
        f"{spot.description}"
    )
    world.say(
        f"Between them lay {cord.phrase} and a tiny cup of {bead.phrase}. "
        f'Today they would make two {project.plural}, and each one would hold {bead.label} '
        f"that {bead.shine}."
    )
    world.say(
        f'"Let\'s make them match," said {a.id}. "A friend-song stitch, a click-clack catch."'
    )
    world.say(
        f'"Yes," said {b.id} with a grin so wide, "one for you and one for me to wear with pride."'
    )


def stringing(world: World, a: Entity, b: Entity, project: Project, bead: BeadKind) -> None:
    world.say(
        f"They slid each bead in a patient line, saying little rhymes to keep the pattern fine."
    )
    world.say(
        f'"Red, then gold, then {bead.color} bright," said {b.id}. '
        f'"Slow and steady makes it right," said {a.id}.'
    )
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.get("beads").meters["threaded"] += 1
    world.get("project").meters["half_done"] += 1


def hurry_and_warning(world: World, a: Entity, b: Entity) -> None:
    pred = predict_loss(world)
    world.facts["predicted_lost"] = pred["lost"]
    world.facts["predicted_severity"] = pred["severity"]
    a.memes["haste"] += 1
    b.memes["care"] += 1
    if pred["lost"]:
        world.say(
            f'{a.id} lifted the first half-made string and laughed, "Look how it swings!" '
            f'{b.id} reached out fast and said, "Wait, please wait. The knot is loose, and beads roll great."'
        )
    else:
        world.say(
            f'{a.id} lifted the first half-made string and laughed, "Look how it swings!" '
            f'{b.id} said, "Hold it low and soft and slow. A little tug can make beads go."'
        )


def snap_scene(world: World, a: Entity, bead: BeadKind) -> None:
    _do_snap(world, narrate=True)
    world.say(
        f"But {a.id} gave one happy twirl too soon. Ping! The string let go with a tiny tune."
    )
    world.say(
        f"{bead.label.capitalize()} after bead skipped out of line, flashing on the floor in a bright small shine."
    )
    if world.get("centerpiece").meters["lost"] >= THRESHOLD:
        world.say(
            f"One special bead zipped from sight and hid where little shadows met the light."
        )
    else:
        world.say(
            f"The special bead rolled only a little way and winked nearby as if to say, stay."
        )


def response_scene(world: World, a: Entity, b: Entity, response: Response, spot: Spot) -> None:
    a.memes["regret"] += 1
    b.memes["care"] += 1
    if response.id == "bowl_search":
        world.say(
            f'"Oh no," said {a.id}. "{bead_word(world)}!" '
            f'"Don\'t cry, we\'ll try," said {b.id}. "Use the bowl. We\'ll tap and listen till it comes out whole."'
        )
    elif response.id == "hands_and_hum":
        world.say(
            f'"Oh no," said {a.id}. "{bead_word(world)}!" '
            f'"Side by side," said {b.id}, "we\'ll look and hum. Kind hands are small, and small hands help things come."'
        )
    else:
        world.say(
            f'"Oh no," said {a.id}. "{bead_word(world)}!" '
            f'"Let\'s keep calm," said {b.id}. "We\'ll search together and bring it to our palm."'
        )

    if recovered(response, spot, PROJECTS[world.facts["project_cfg"].id], BEADS[world.facts["bead_cfg"].id]):
        world.say(response.text)
    else:
        world.say(response.fail)


def repair_scene(world: World, a: Entity, b: Entity, project: Project, bead: BeadKind,
                 outcome: str) -> None:
    if outcome == "found":
        world.get("centerpiece").meters["found_again"] += 1
        world.get("project").meters["finished"] += 1
        world.get("cord").meters["retied"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        a.memes["trust"] += 1
        b.memes["trust"] += 1
        world.say(
            f'Soon {b.id} held up the runaway bead. "{bead.label.capitalize()}!" {b.pronoun().capitalize()} cheered. '
            f'"We found the one we need."'
        )
        world.say(
            f'This time they tied the knot together. "{a.id}," said {b.id}, "slow hands make strong things better."'
        )
        world.say(
            f'"And friends who stop to help and see," said {a.id}, "make sturdier things than string can be."'
        )
        world.say(
            f"When the two {project.plural} were done at last, they sat {project.wear_line} as the sunny minutes passed."
        )
    else:
        world.get("project").meters["finished"] += 1
        world.get("cord").meters["retied"] += 1
        a.memes["relief"] += 1
        b.memes["relief"] += 1
        a.memes["gratitude"] += 1
        b.memes["generosity"] += 1
        world.say(
            f"They could not find the runaway bead, but {b.id} opened a small side cup. "
            f'"Here is a plain {bead.backup} bead," {b.pronoun()} said. "It is not the same, but kind is enough."'
        )
        world.say(
            f'{a.id} blinked, then smiled. "The brightest part is not the shine. The brightest part is that you are mine to trust, dear friend, and I am thine."'
        )
        world.say(
            f"They finished the two {project.plural} anyway, one extra plain and one extra bright. "
            f"Side by side, they looked just right."
        )


def ending(world: World, a: Entity, b: Entity, spot: Spot, project: Project, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    if outcome == "found":
        world.say(
            f'Then {a.id} tapped {b.id}\'s shoulder and said, "Next time I will listen before I race ahead."'
        )
        world.say(
            f'"And next time I will help, not scold," said {b.id}. "That is a friendship worth more than gold."'
        )
    else:
        world.say(
            f'"Next time," said {a.id}, "I will tie first and twirl last." '
            f'"Next time," said {b.id}, "I will stay by your side through the slow part and the fast."'
        )
    world.say(
        f"At {spot.ending_image}, the friends held up their {project.plural}. "
        f"{project.gift_line} The day ended soft, and their laughter stayed light."
    )


def bead_word(world: World) -> str:
    return BEADS[world.facts["bead_cfg"].id].label


def tell(spot: Spot, project: Project, bead: BeadKind, cord: Cord, response: Response,
         maker_name: str = "Nia", maker_gender: str = "girl",
         friend_name: str = "Omar", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(spot)
    a = world.add(Entity(id=maker_name, kind="character", type=maker_gender, role="maker"))
    b = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="adult", label="the parent"))
    world.add(Entity(id="project", type=project.id, label=project.label))
    world.add(Entity(id="cord", type="cord", label=cord.label))
    world.add(Entity(id="beads", type="beads", label=bead.label))
    world.add(Entity(id="centerpiece", type="bead", label=bead.label))
    world.facts.update(
        maker=a,
        friend=b,
        parent=parent,
        spot_cfg=spot,
        project_cfg=project,
        bead_cfg=bead,
        cord_cfg=cord,
        response=response,
        severity=spill_severity(spot, project, bead),
    )

    introduce(world, a, b, spot, project, bead, cord)
    stringing(world, a, b, project, bead)

    world.para()
    hurry_and_warning(world, a, b)
    snap_scene(world, a, bead)

    world.para()
    response_scene(world, a, b, response, spot)
    outcome = "found" if recovered(response, spot, project, bead) else "substitute"
    repair_scene(world, a, b, project, bead, outcome)

    world.para()
    ending(world, a, b, spot, project, outcome)

    world.facts.update(
        outcome=outcome,
        snapped=world.get("cord").meters["snapped"] >= THRESHOLD,
        bead_lost=world.get("centerpiece").meters["lost"] >= THRESHOLD,
        finished=world.get("project").meters["finished"] >= THRESHOLD,
    )
    return world


SPOTS = {
    "rug": Spot(
        id="rug",
        place="the playroom",
        seat="a round striped rug",
        surface="rug",
        stop=2,
        description="A striped basket sat nearby, and the floor was soft and snug.",
        ending_image="the edge of the striped rug",
        tags={"indoor", "rug"},
    ),
    "porch": Spot(
        id="porch",
        place="the front porch",
        seat="the warm porch step",
        surface="wood",
        stop=1,
        description="The boards were smooth, and sunbeams made small ladders on the floor.",
        ending_image="the sunny porch rail",
        tags={"porch", "outdoor"},
    ),
    "bench": Spot(
        id="bench",
        place="the garden bench",
        seat="the wooden bench by the peas",
        surface="stone",
        stop=0,
        description="A little path of pebbles ran below, where round things liked to roll.",
        ending_image="the garden gate",
        tags={"garden", "outdoor"},
    ),
}

PROJECTS = {
    "bracelet": Project(
        id="bracelet",
        label="bracelet",
        plural="bracelets",
        wear_line="around their wrists",
        need_strength=1,
        scatter=1,
        gift_line="One clicked against the other like a tiny rhyme in sight.",
        tags={"bracelet", "friendship"},
    ),
    "necklace": Project(
        id="necklace",
        label="necklace",
        plural="necklaces",
        wear_line="against their shirts",
        need_strength=2,
        scatter=1,
        gift_line="The two strings shone against their shirts, close to their friendly hearts.",
        tags={"necklace", "friendship"},
    ),
    "bag_charm": Project(
        id="bag_charm",
        label="bag charm",
        plural="bag charms",
        wear_line="from their school bags",
        need_strength=2,
        scatter=2,
        gift_line="The little charms swung side by side, like best-friend starts and restarts.",
        tags={"charm", "friendship"},
    ),
}

BEADS = {
    "heart": BeadKind(
        id="heart",
        label="heart bead",
        phrase="heart beads",
        hole=2,
        weight=1,
        roll=1,
        shine="glowed like a cherry drop in the sun",
        color="red",
        backup="cream",
        tags={"bead", "heart"},
    ),
    "star": BeadKind(
        id="star",
        label="star bead",
        phrase="star beads",
        hole=2,
        weight=1,
        roll=2,
        shine="winked like little stars at noon",
        color="yellow",
        backup="blue",
        tags={"bead", "star"},
    ),
    "glass": BeadKind(
        id="glass",
        label="glass bead",
        phrase="glass beads",
        hole=1,
        weight=2,
        roll=2,
        shine="caught the light with a moon-bright gleam",
        color="silver",
        backup="white",
        tags={"bead", "glass"},
    ),
}

CORDS = {
    "elastic": Cord(
        id="elastic",
        label="elastic cord",
        phrase="a coil of soft elastic cord",
        thickness=1,
        strength=2,
        tags={"elastic"},
    ),
    "thread": Cord(
        id="thread",
        label="craft thread",
        phrase="a spool of craft thread",
        thickness=1,
        strength=1,
        tags={"thread"},
    ),
    "ribbon": Cord(
        id="ribbon",
        label="narrow ribbon",
        phrase="a roll of narrow ribbon",
        thickness=2,
        strength=2,
        tags={"ribbon"},
    ),
}

RESPONSES = {
    "bowl_search": Response(
        id="bowl_search",
        sense=3,
        power=3,
        text="They turned a bowl on its side, tapped under the edge, and soon the runaway bead clicked softly into sight.",
        fail="They tapped and listened and looked with care, but the bead had slipped too far to answer there.",
        qa_text="They used a bowl and patient tapping to find the runaway bead",
        tags={"search", "bowl"},
    ),
    "hands_and_hum": Response(
        id="hands_and_hum",
        sense=3,
        power=2,
        text="Knee to knee, they searched with calm small hands, humming until the bead peeped out near the wall.",
        fail="They searched with calm small hands and hummed together, but the bead had rolled beyond their first look.",
        qa_text="They searched with their hands together and kept calm",
        tags={"search", "hands"},
    ),
    "sweep_away": Response(
        id="sweep_away",
        sense=1,
        power=0,
        text="They pushed the beads into a dusty pile with a broom.",
        fail="They pushed the beads around with a broom, which only sent the tiny bead farther away.",
        qa_text="They swept at the beads with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Nia", "Mila", "Ivy", "Lena", "Tia", "Zuri", "Asha", "Pia"]
BOY_NAMES = ["Omar", "Noah", "Eli", "Milo", "Toby", "Jai", "Ben", "Leo"]


@dataclass
class StoryParams:
    spot: str = "rug"
    project: str = "bracelet"
    bead: str = "heart"
    cord: str = "elastic"
    response: str = "bowl_search"
    maker: str = "Nia"
    maker_gender: str = "girl"
    friend: str = "Omar"
    friend_gender: str = "boy"
    parent: str = "mother"
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
    "bead": [
        (
            "What is a bead?",
            "A bead is a small piece with a hole through the middle so you can thread it onto string. People use beads to make jewelry and little decorations.",
        )
    ],
    "bracelet": [
        (
            "What is a bracelet?",
            "A bracelet is something you wear around your wrist. It can be made from string, beads, or other small pretty things.",
        )
    ],
    "necklace": [
        (
            "What is a necklace?",
            "A necklace is something you wear around your neck. It hangs on a string or chain.",
        )
    ],
    "charm": [
        (
            "What is a bag charm?",
            "A bag charm is a small decoration that hangs from a bag or zipper. It swings when the bag moves.",
        )
    ],
    "elastic": [
        (
            "Why is elastic cord useful for beads?",
            "Elastic cord stretches a little, so it is handy for bracelets and other small bead projects. It can bend without snapping as easily as some thin strings.",
        )
    ],
    "thread": [
        (
            "What is craft thread?",
            "Craft thread is a thin string people use for sewing or making things by hand. Thin thread fits small holes, but it can be weaker than thicker cord.",
        )
    ],
    "ribbon": [
        (
            "What is ribbon?",
            "Ribbon is a flat strip of fabric. Some ribbon is pretty for tying, but wide ribbon does not fit through every bead hole.",
        )
    ],
    "search": [
        (
            "What should you do when a tiny craft piece rolls away?",
            "Stop moving fast and look calmly so you do not kick it farther. Searching together and checking under nearby things works better than rushing.",
        )
    ],
    "friendship": [
        (
            "How can friends fix a small mistake together?",
            "They can talk kindly, listen to each other, and help with the problem. Working together often matters more than the small thing that went wrong.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bead", "bracelet", "necklace", "charm", "elastic", "thread", "ribbon", "search", "friendship"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for spot_id in SPOTS:
        for project_id, project in PROJECTS.items():
            for bead_id, bead in BEADS.items():
                for cord_id, cord in CORDS.items():
                    if compatible(project, bead, cord):
                        combos.append((spot_id, project_id, bead_id, cord_id))
    return combos


def explain_rejection(project: Project, bead: BeadKind, cord: Cord) -> str:
    if cord.thickness > bead.hole:
        return (
            f"(No story: {cord.label} is too thick to pass through a {bead.label}. "
            f"Pick a thinner cord or a bead with a bigger hole.)"
        )
    if cord.strength < project.need_strength:
        return (
            f"(No story: {cord.label} is too weak for a {project.label}. "
            f"Pick a stronger cord so the craft setup makes sense.)"
        )
    return "(No story: those craft materials do not fit together.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer search like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    spot = SPOTS[params.spot]
    project = PROJECTS[params.project]
    bead = BEADS[params.bead]
    return "found" if recovered(response, spot, project, bead) else "substitute"


def generation_prompts(world: World) -> list[str]:
    maker = world.facts["maker"]
    friend = world.facts["friend"]
    project = world.facts["project_cfg"]
    bead = world.facts["bead_cfg"]
    outcome = world.facts["outcome"]
    base = (
        f'Write a short rhyming story for a 3-to-5-year-old about friendship and a {bead.label}. '
        f'Include dialogue and end with two friends finishing matching {project.plural}.'
    )
    if outcome == "found":
        return [
            base,
            f"Tell a gentle rhyming story where {maker.id} and {friend.id} are making {project.plural}, the string snaps, and kind teamwork helps them find the missing bead.",
            f'Write a dialogue-rich rhyme where one child says "wait" before the string breaks, and the friends solve the bead problem together.',
        ]
    return [
        base,
        f"Tell a rhyming friendship story where a special bead rolls away, but the friends still finish their {project.plural} by being kind and flexible.",
        f'Write a simple story in rhyme where the lesson is that friendship can shine even when one bead is gone.',
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    maker = world.facts["maker"]
    friend = world.facts["friend"]
    project = world.facts["project_cfg"]
    bead = world.facts["bead_cfg"]
    cord = world.facts["cord_cfg"]
    response = world.facts["response"]
    spot = world.facts["spot_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(maker, friend)}, {maker.id} and {friend.id}, making matching {project.plural} together. Their friendship is the heart of the story, not just the craft.",
        ),
        (
            f"What were {maker.id} and {friend.id} making?",
            f"They were making two matching {project.plural} with {cord.label} and {bead.phrase}. They wanted the finished gifts to look like a pair.",
        ),
        (
            "What went wrong in the middle of the story?",
            f"The string snapped when {maker.id} lifted the half-made project too soon, and the beads scattered. Because they were working at {spot.place} on a {spot.surface} surface, the little pieces could roll away.",
        ),
        (
            f"Why did {friend.id} tell {maker.id} to wait?",
            f"{friend.id} could already imagine the loose knot giving way. The warning came from noticing that fast hands and small round beads can make a messy tumble.",
        ),
    ]
    if outcome == "found":
        qa.append(
            (
                "How did they solve the problem?",
                f"They stayed calm and {response.qa_text.lower()}. Then they tied the knot together more carefully, which let them finish the matching craft.",
            )
        )
        qa.append(
            (
                f"What changed between the beginning and the ending?",
                f"At first, {maker.id} was hurrying and {friend.id} was warning. By the end, both friends were working slowly together, and the finished {project.plural} showed that their teamwork had grown stronger.",
            )
        )
    else:
        qa.append(
            (
                "Did they still finish the gifts?",
                f"Yes. They could not find the runaway bead, but {friend.id} kindly offered a plain backup bead so the project could go on. The ending shows that friendship mattered more than one missing shiny piece.",
            )
        )
        qa.append(
            (
                f"What did {maker.id} learn?",
                f"{maker.id} learned to tie first and twirl later. {maker.pronoun('subject').capitalize()} also learned that a good friend helps when plans change, which is why the ending still feels warm.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    project = world.facts["project_cfg"]
    cord = world.facts["cord_cfg"]
    bead = world.facts["bead_cfg"]
    tags = {"bead", "search", "friendship"}
    tags |= set(project.tags)
    tags |= set(cord.tags)
    tags |= set(bead.tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  severity: {world.facts.get('severity', 0)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,B,C) :- project(P), bead(B), cord(C),
                     need_strength(P,N), strength(C,S), S >= N,
                     hole(B,H), thickness(C,T), T =< H.

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.

severity(Sp + Sc + (2 - St)) :- chosen_spot(Spot), stop(Spot,St),
                                chosen_project(P), scatter(P,Sc),
                                chosen_bead(B), roll(B,Sp).

found :- chosen_response(R), power(R,P), severity(V), P >= V.
outcome(found) :- found.
outcome(substitute) :- not found.

valid(Spot,P,B,C) :- spot(Spot), compatible(P,B,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("stop", spot_id, spot.stop))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("need_strength", project_id, project.need_strength))
        lines.append(asp.fact("scatter", project_id, project.scatter))
    for bead_id, bead in BEADS.items():
        lines.append(asp.fact("bead", bead_id))
        lines.append(asp.fact("hole", bead_id, bead.hole))
        lines.append(asp.fact("roll", bead_id, bead.roll))
    for cord_id, cord in CORDS.items():
        lines.append(asp.fact("cord", cord_id))
        lines.append(asp.fact("thickness", cord_id, cord.thickness))
        lines.append(asp.fact("strength", cord_id, cord.strength))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_bead", params.bead),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        spot="rug",
        project="bracelet",
        bead="heart",
        cord="elastic",
        response="hands_and_hum",
        maker="Nia",
        maker_gender="girl",
        friend="Omar",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        spot="porch",
        project="necklace",
        bead="star",
        cord="elastic",
        response="bowl_search",
        maker="Mila",
        maker_gender="girl",
        friend="Leo",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        spot="bench",
        project="bag_charm",
        bead="glass",
        cord="elastic",
        response="hands_and_hum",
        maker="Ivy",
        maker_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        spot="bench",
        project="bracelet",
        bead="star",
        cord="thread",
        response="bowl_search",
        maker="Tia",
        maker_gender="girl",
        friend="Noah",
        friend_gender="boy",
        parent="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: friends, a bead craft, a snap, and a kind repair."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--bead", choices=BEADS)
    ap.add_argument("--cord", choices=CORDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.bead and args.cord:
        project = PROJECTS[args.project]
        bead = BEADS[args.bead]
        cord = CORDS[args.cord]
        if not compatible(project, bead, cord):
            raise StoryError(explain_rejection(project, bead, cord))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.project is None or combo[1] == args.project)
        and (args.bead is None or combo[2] == args.bead)
        and (args.cord is None or combo[3] == args.cord)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, project_id, bead_id, cord_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    maker, maker_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=maker)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        spot=spot_id,
        project=project_id,
        bead=bead_id,
        cord=cord_id,
        response=response_id,
        maker=maker,
        maker_gender=maker_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.bead not in BEADS:
        raise StoryError(f"(Unknown bead: {params.bead})")
    if params.cord not in CORDS:
        raise StoryError(f"(Unknown cord: {params.cord})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    project = PROJECTS[params.project]
    bead = BEADS[params.bead]
    cord = CORDS[params.cord]
    response = RESPONSES[params.response]

    if not compatible(project, bead, cord):
        raise StoryError(explain_rejection(project, bead, cord))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        spot=SPOTS[params.spot],
        project=project,
        bead=bead,
        cord=cord,
        response=response,
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sensible = {r.id for r in sensible_responses()}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(cl_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            break

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0] if cases else CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (spot, project, bead, cord) combos:\n")
        for spot_id, project_id, bead_id, cord_id in combos:
            print(f"  {spot_id:8} {project_id:10} {bead_id:8} {cord_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.maker} & {p.friend}: {p.project} with {p.bead} on {p.cord} "
                f"at {p.spot} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
