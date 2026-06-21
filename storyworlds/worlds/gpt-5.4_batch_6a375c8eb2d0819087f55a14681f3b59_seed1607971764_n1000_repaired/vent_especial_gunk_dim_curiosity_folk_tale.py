#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py
========================================================================

A standalone storyworld for a small folk-tale domain about curiosity, an old
vent, and the difference between poking at a mystery and solving it the careful
way.

Seed words carried into the prose:
- vent
- especial
- gunk-dim

The model rebuilds a tiny causal tale:

    A curious child hears an odd song in a high vent.
    The room feels gunk-dim because the vent is clogged.
    The child wants to poke at it.
    A careful elder warns that there is an especial way to help a vent.
    If the child waits, the elder fixes it at once.
    If the child pokes anyway, soot or leaves spill down first.
    Then either the elder mends the problem, or they must wait for stronger help.
    The ending image shows what changed: bright air, wiser curiosity, and a safer habit.

Run it
------
    python storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py
    python storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py --setting cottage --blockage soot
    python storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py --response bare_hand
    python storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/vent_especial_gunk_dim_curiosity_folk_tale.py --verify
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
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
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
class Setting:
    id: str
    place: str
    opening: str
    hearth: str
    outside: str
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
class Blockage:
    id: str
    label: str
    material: str
    song: str
    spill_text: str
    clean_text: str
    severity: int
    darkness: int
    spillable: bool = True
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
class UnsafeTool:
    id: str
    label: str
    phrase: str
    motion: str
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


@dataclass
class StoryParams:
    setting: str
    blockage: str
    tool: str
    response: str
    child_name: str
    child_gender: str
    elder_type: str
    temper: str
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


def _r_spill(world: World) -> list[str]:
    vent = world.get("vent")
    room = world.get("room")
    child = world.get("child")
    if vent.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["dirty"] += 1
    child.meters["sooty"] += 1
    child.memes["fear"] += 1
    return ["__spill__"]


def _r_cleared(world: World) -> list[str]:
    vent = world.get("vent")
    room = world.get("room")
    if vent.meters["cleared"] < THRESHOLD:
        return []
    sig = ("cleared",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["bright"] += 1
    room.meters["warm"] += 1
    return ["__clear__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="cleared", tag="physical", apply=_r_cleared),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(setting_id: str, blockage_id: str) -> bool:
    setting = SETTINGS[setting_id]
    blockage = BLOCKAGES[blockage_id]
    return blockage.spillable and "vent" in setting.tags


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for setting_id in SETTINGS:
        for blockage_id in BLOCKAGES:
            if valid_combo(setting_id, blockage_id):
                combos.append((setting_id, blockage_id))
    return combos


def severity_of(blockage: Blockage, delay: int) -> int:
    return blockage.severity + delay


def mended(response: Response, blockage: Blockage, delay: int) -> bool:
    return response.power >= severity_of(blockage, delay)


def waits_instead(temper: str) -> bool:
    return temper == "patient"


def predict_spill(world: World, blockage: Blockage) -> dict:
    sim = world.copy()
    vent = sim.get("vent")
    room = sim.get("room")
    child = sim.get("child")
    vent.meters["spilled"] += 1
    room.meters["dark"] += float(blockage.darkness)
    propagate(sim, narrate=False)
    return {
        "dirty_room": room.meters["dirty"] >= THRESHOLD,
        "sooty_child": child.meters["sooty"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, elder: Entity, blockage: Blockage) -> None:
    room = world.get("room")
    vent = world.get("vent")
    child.memes["curiosity"] = 5.0
    child.memes["trust"] = 4.0 if child.attrs["temper"] == "eager" else 6.0
    room.meters["dark"] = float(blockage.darkness)
    vent.meters["clogged"] = 1.0
    world.say(
        f"{world.setting.opening} There lived a curious {child.type} named {child.id}, "
        f"who always listened when the house tried to say something."
    )
    world.say(
        f"One chill afternoon, a high vent above {world.setting.hearth} sang {blockage.song}. "
        f"The room had gone a little gunk-dim, and that was enough to set curiosity tapping at {child.id}'s heart."
    )
    world.say(
        f"{elder.label_word.capitalize()} was sorting kindling and humming softly, while {child.id} kept glancing up at the vent."
    )


def temptation(world: World, child: Entity, tool: UnsafeTool) -> None:
    child.memes["tempted"] += 1
    world.say(
        f'"I wonder what is hiding in that vent," {child.id} whispered. '
        f'{child.pronoun().capitalize()} reached for {tool.phrase}, thinking {tool.motion}.'
    )


def warning(world: World, elder: Entity, child: Entity, blockage: Blockage, tool: UnsafeTool) -> None:
    pred = predict_spill(world, blockage)
    world.facts["predicted_dirty"] = pred["dirty_room"]
    world.facts["predicted_sooty"] = pred["sooty_child"]
    child.memes["cautioned"] += 1
    world.say(
        f'"No, little heart," said {elder.label_word} gently. "A vent is not mended by poking. '
        f'There is an especial way, or {blockage.material} will come tumbling down."'
    )
    if pred["dirty_room"] and pred["sooty_child"]:
        world.say(
            f"{elder.label_word.capitalize()} pointed at {tool.label} and added, "
            f'"That would leave the room dirty and your face smudged too."'
        )


def wait_branch(world: World, elder: Entity, child: Entity, blockage: Blockage, response: Response) -> None:
    child.memes["obedience"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} curled {child.pronoun('possessive')} fingers back and stepped away from the wall. "
        f"Curiosity still shone in {child.pronoun('possessive')} eyes, but now it stood beside patience instead of ahead of it."
    )
    world.para()
    mend(world, elder, child, blockage, response)
    lesson(world, elder, child, blockage, waiting=True)
    world.para()
    bright_ending(world, child, elder, blockage, waited=True, lingering=False)


def poke(world: World, child: Entity, blockage: Blockage, tool: UnsafeTool) -> None:
    vent = world.get("vent")
    room = world.get("room")
    child.memes["defiance"] += 1
    vent.meters["spilled"] += 1
    room.meters["dark"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity ran faster than wisdom. {child.id} lifted {tool.label} and {tool.motion}."
    )
    world.say(
        f"At once, {blockage.spill_text} A dusty breath rushed out, and the little room looked darker before it could ever look better."
    )


def alarm(world: World, elder: Entity, child: Entity) -> None:
    world.say(
        f'"Oh, my poppet!" cried {elder.label_word}. "{child.id}, stand back from the hearth."'
    )


def mend(world: World, elder: Entity, child: Entity, blockage: Blockage, response: Response) -> None:
    vent = world.get("vent")
    room = world.get("room")
    vent.meters["clogged"] = 0.0
    vent.meters["cleared"] += 1
    room.meters["dark"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder.label_word.capitalize()} {response.text.format(clean=blockage.clean_text)}."
    )
    world.say(
        f"Soon the vent breathed again. Warmth slipped back into the room, and the gunk-dim corners thinned into plain old shadow."
    )


def fail_mend(world: World, elder: Entity, child: Entity, blockage: Blockage, response: Response) -> None:
    child.memes["fear"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{elder.label_word.capitalize()} {response.fail.format(clean=blockage.clean_text)}."
    )
    world.say(
        f"The mess on the floor was swept into a pan, but the vent still sighed the wrong way, and the room stayed dim and chilly."
    )


def lesson(world: World, elder: Entity, child: Entity, blockage: Blockage, waiting: bool) -> None:
    child.memes["lesson"] += 1
    if waiting:
        world.say(
            f'"You did well to let your curiosity hold my hand," said {elder.label_word}. '
            f'"Mysteries grow kinder when we meet them the careful way."'
        )
    else:
        world.say(
            f"{elder.label_word.capitalize()} drew {child.id} close and dusted {child.pronoun('possessive')} cheek. "
            f'"Curiosity is a bright candle," {elder.pronoun()} said, "but even a bright candle needs a lantern around it."'
        )
    world.say(
        f'{child.id} nodded. {child.pronoun().capitalize()} had wanted to know the secret of the vent, '
        f"and now {child.pronoun()} knew one more thing besides: careful hands make better endings."
    )


def waiting_ending(world: World, child: Entity, elder: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"That evening, {elder.label_word} lit a lantern and set it on the table, and its round glow turned the room gentle again."
    )
    world.say(
        f"They would ask the village sweep for stronger help at first light. Until then, {child.id} sat beside the firebox with a small brush, "
        f"cleaning the fallen dust and asking questions instead of reaching upward."
    )
    world.say(
        f"So the house did not yet shine, but the child within it had already grown wiser."
    )


def bright_ending(world: World, child: Entity, elder: Entity, blockage: Blockage, waited: bool, lingering: bool) -> None:
    if lingering:
        waiting_ending(world, child, elder)
        return
    if waited:
        world.say(
            f"When the work was done, {child.id} stood beneath the vent and laughed to hear its new clear hum."
        )
    else:
        world.say(
            f"After the sweeping and brushing, {child.id} looked up again, this time with clean hands and a calmer heart."
        )
    world.say(
        f"The warm air moved lightly through the house, the fire burned steady, and even {world.setting.outside} seemed to listen."
    )
    world.say(
        f"From that day on, whenever wonder tugged at {child.id}, {child.pronoun()} still asked questions first. "
        f"And that, old tale tellers say, is how curiosity learned to walk with care."
    )


def tell(
    setting: Setting,
    blockage: Blockage,
    tool: UnsafeTool,
    response: Response,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    temper: str = "eager",
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"temper": temper},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        attrs={},
    ))
    room = world.add(Entity(id="room", type="room", label="the room", attrs={}))
    vent = world.add(Entity(id="vent", type="vent", label="the vent", attrs={}))

    # Initialize every value the rules read.
    room.meters["dirty"] = 0.0
    room.meters["bright"] = 0.0
    room.meters["warm"] = 0.0
    room.meters["dark"] = 0.0
    vent.meters["spilled"] = 0.0
    vent.meters["cleared"] = 0.0
    vent.meters["clogged"] = 0.0
    child.meters["sooty"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["tempted"] = 0.0
    child.memes["cautioned"] = 0.0
    child.memes["defiance"] = 0.0
    child.memes["obedience"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["lesson"] = 0.0
    child.memes["hope"] = 0.0

    opening(world, child, elder, blockage)
    world.para()
    temptation(world, child, tool)
    warning(world, elder, child, blockage, tool)

    if waits_instead(temper):
        world.facts["outcome"] = "averted"
        wait_branch(world, elder, child, blockage, response)
    else:
        world.say(
            f"{child.label} bit {child.pronoun('possessive')} lip. The mystery still rustled above, and wanting to know felt almost louder than the warning."
        )
        world.para()
        poke(world, child, blockage, tool)
        alarm(world, elder, child)
        world.para()
        if mended(response, blockage, delay):
            world.facts["outcome"] = "mended"
            mend(world, elder, child, blockage, response)
            lesson(world, elder, child, blockage, waiting=False)
            world.para()
            bright_ending(world, child, elder, blockage, waited=False, lingering=False)
        else:
            world.facts["outcome"] = "waiting"
            fail_mend(world, elder, child, blockage, response)
            lesson(world, elder, child, blockage, waiting=False)
            world.para()
            bright_ending(world, child, elder, blockage, waited=False, lingering=True)

    outcome = world.facts["outcome"]
    world.facts.update(
        child=child,
        elder=elder,
        room=room,
        vent=vent,
        setting_cfg=setting,
        blockage_cfg=blockage,
        tool_cfg=tool,
        response_cfg=response,
        child_name=child_name,
        tool_used=tool.label,
        spill_happened=vent.meters["spilled"] >= THRESHOLD,
        soot_happened=child.meters["sooty"] >= THRESHOLD,
        room_dirty=room.meters["dirty"] >= THRESHOLD,
        room_bright=room.meters["bright"] >= THRESHOLD,
        severity=severity_of(blockage, delay),
        delay=delay,
        outcome=outcome,
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="the crooked cottage under the hill",
        opening="Long ago, in the crooked cottage under the hill, the wind liked to nose around the eaves.",
        hearth="the old red hearthstones",
        outside="the ash tree outside the door",
        tags={"vent", "folk", "hearth"},
    ),
    "bakehouse": Setting(
        id="bakehouse",
        place="the village bakehouse",
        opening="Long ago, beside the village lane, there stood a warm bakehouse with flour in its cracks and stories in its beams.",
        hearth="the big bread oven",
        outside="the line of waiting sparrows on the sill",
        tags={"vent", "folk", "oven"},
    ),
    "tower": Setting(
        id="tower",
        place="the watch tower above the fields",
        opening="Long ago, on a windy rise above the fields, there stood a little watch tower with a hearth no wider than a barrel lid.",
        hearth="the narrow stone firebox",
        outside="the far wheat moving like water",
        tags={"vent", "folk", "stone"},
    ),
}

BLOCKAGES = {
    "soot": Blockage(
        id="soot",
        label="soot",
        material="soot",
        song="a thin, scratchy whistle",
        spill_text="a black puff of soot broke loose and came pattering down like dirty snow",
        clean_text="the soot from the throat of the vent",
        severity=3,
        darkness=2,
        spillable=True,
        tags={"soot", "dirty", "vent"},
    ),
    "leaves": Blockage(
        id="leaves",
        label="leaves",
        material="dry leaves",
        song="a papery hiss",
        spill_text="a twist of dry leaves and dust fluttered out and spun across the floor",
        clean_text="the leaves caught in the vent mouth",
        severity=2,
        darkness=1,
        spillable=True,
        tags={"leaves", "vent", "autumn"},
    ),
    "cobwebs": Blockage(
        id="cobwebs",
        label="cobwebs",
        material="old cobwebs",
        song="a whisper so soft it seemed half asleep",
        spill_text="gray cobwebs sagged free with a sprinkle of chimney dust",
        clean_text="the cobwebs snagged across the vent",
        severity=1,
        darkness=1,
        spillable=True,
        tags={"cobweb", "vent"},
    ),
    "stone": Blockage(
        id="stone",
        label="stone chip",
        material="a stone chip",
        song="a dull clink",
        spill_text="nothing sensible fell at all",
        clean_text="the stone chip jammed deep inside",
        severity=4,
        darkness=2,
        spillable=False,
        tags={"stone", "vent"},
    ),
}

TOOLS = {
    "spoon": UnsafeTool(
        id="spoon",
        label="the long wooden spoon",
        phrase="the long wooden spoon from the porridge pot",
        motion="to tap the vent grille from below",
        tags={"spoon", "poke"},
    ),
    "poker": UnsafeTool(
        id="poker",
        label="the fireplace poker",
        phrase="the fireplace poker",
        motion="to jab up through the slats",
        tags={"poker", "poke"},
    ),
    "reed": UnsafeTool(
        id="reed",
        label="the marsh reed",
        phrase="a stiff marsh reed",
        motion="to fish about inside the crack",
        tags={"reed", "poke"},
    ),
}

RESPONSES = {
    "vent_brush": Response(
        id="vent_brush",
        sense=3,
        power=3,
        text="fetched the vent brush, climbed the stool with one steady hand on the wall, and teased {clean} free a little at a time",
        fail="fetched the vent brush and worked patiently, but {clean} was packed too hard to clear before dusk",
        qa_text="used the vent brush to clear the blockage",
        tags={"brush", "vent"},
    ),
    "ladder_cloth": Response(
        id="ladder_cloth",
        sense=3,
        power=2,
        text="set a short ladder in place, covered the hearth with a cloth, and swept {clean} out with careful strokes",
        fail="set up the ladder and cloth, but {clean} was too stubborn for that light cleaning alone",
        qa_text="used a ladder and cloth to sweep the blockage out",
        tags={"ladder", "cloth", "vent"},
    ),
    "sweep_hook": Response(
        id="sweep_hook",
        sense=4,
        power=4,
        text="brought out the old sweep hook, loosened {clean}, and drew it down cleanly into a waiting pan",
        fail="brought out the old sweep hook, yet even then {clean} would not fully come free before nightfall",
        qa_text="used the sweep hook to draw the blockage out",
        tags={"sweep", "hook", "vent"},
    ),
    "bare_hand": Response(
        id="bare_hand",
        sense=1,
        power=1,
        text="reached up with bare fingers and tugged {clean} loose",
        fail="reached up with bare fingers, but only made the mess smear wider",
        qa_text="tried to pull the blockage out by hand",
        tags={"hand", "vent"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Tala", "Niva", "Elsa", "Lina"]
BOY_NAMES = ["Ivo", "Marek", "Tobin", "Jori", "Pavel", "Niko"]
TEMPERS = ["patient", "eager"]


def explain_rejection(setting_id: str, blockage_id: str) -> str:
    setting = SETTINGS[setting_id]
    blockage = BLOCKAGES[blockage_id]
    if not blockage.spillable:
        return (
            f"(No story: in {setting.place}, {blockage.label} does not make the child-facing spill-and-clean tale this world models. "
            f"Choose soot, leaves, or cobwebs for a blockage that can fall and be mended.)"
        )
    return "(No story: this combination does not fit the vent tale.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if waits_instead(params.temper):
        return "averted"
    if mended(RESPONSES[params.response], BLOCKAGES[params.blockage], params.delay):
        return "mended"
    return "waiting"


KNOWLEDGE = {
    "vent": [
        (
            "What does a vent do?",
            "A vent lets air move in or out of a room or stove. When it is clear, smoke and warm air can travel the way they should.",
        )
    ],
    "soot": [
        (
            "What is soot?",
            "Soot is soft black dust made when things burn. It can smear onto walls, hands, and clothes very easily.",
        )
    ],
    "leaves": [
        (
            "Why can leaves block a vent?",
            "Dry leaves can blow into openings and gather in a tight little pile. Then the air cannot move through as easily.",
        )
    ],
    "cobweb": [
        (
            "What are cobwebs?",
            "Cobwebs are old spider webs with dust caught in them. They are light, but enough of them can make a dirty tangle.",
        )
    ],
    "brush": [
        (
            "Why is a brush better than poking with a stick?",
            "A brush is made to sweep dirt out gently and in the right direction. Poking can shove the mess deeper or make it fall suddenly.",
        )
    ],
    "ladder": [
        (
            "Why should a grown-up use a ladder carefully?",
            "A ladder helps someone reach a high place safely when it is set firmly and used with care. That is better than stretching or climbing on something wobbly.",
        )
    ],
    "sweep": [
        (
            "What does a chimney or vent sweep do?",
            "A sweep clears soot and other clogs from places where air and smoke need to move. That helps a fire burn more safely and cleanly.",
        )
    ],
    "curiosity": [
        (
            "Is curiosity good?",
            "Yes. Curiosity helps you notice, ask, and learn. It works best when you pair it with patience and safe choices.",
        )
    ],
}
KNOWLEDGE_ORDER = ["vent", "soot", "leaves", "cobweb", "brush", "ladder", "sweep", "curiosity"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    blockage = f["blockage_cfg"]
    setting = f["setting_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a folk tale for a young child that includes the words "vent", "especial", and "gunk-dim", where a curious {child.type} waits for the careful way.',
            f"Tell a gentle old-fashioned story set in {setting.place} where a child wonders about a singing vent, resists the urge to poke at {blockage.label}, and learns that patience can guide curiosity.",
            f'Write a small folk tale in which the room grows gunk-dim, an elder speaks of an especial way to mend it, and the ending proves that asking first is wiser than grabbing a tool.',
        ]
    if outcome == "waiting":
        return [
            f'Write a folk tale for a young child that includes the words "vent", "especial", and "gunk-dim", where curiosity causes a dusty mistake and the family must wait for stronger help.',
            f"Tell an old-fashioned cautionary story set in {setting.place} where a child pokes a vent, {blockage.label} falls, and the lesson is to ask questions before touching hidden things.",
            f"Write a gentle-but-sober tale in which a curious child makes the room messier before it can be fixed, and an elder turns the mistake into a lesson about careful hands.",
        ]
    return [
        f'Write a folk tale for a young child that includes the words "vent", "especial", and "gunk-dim", where curiosity leads to trouble but a calm elder mends it.',
        f"Tell a simple old-style story set in {setting.place} where a child pokes at a mysterious vent, a dusty blockage falls, and an elder fixes the problem the right way.",
        f"Write a small folk tale about curiosity, soot or leaves in a high vent, and a bright ending that shows what changed after the careful repair.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    blockage = f["blockage_cfg"]
    response = f["response_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    child_name = f["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a curious {child.type}, and {elder.label_word}, who knows how to mend the old house. The story follows what happens when mystery and caution meet under one roof.",
        ),
        (
            "Why did the child keep looking at the vent?",
            f"The vent was singing strangely, and the room had gone gunk-dim, so {child_name} wanted to know what was hidden inside. Curiosity started the whole trouble because the mystery felt too close to ignore.",
        ),
        (
            f"What did {child_name} want to use on the vent?",
            f"{child_name} reached for {tool.label} and wanted to poke at the vent from below. {elder.label_word.capitalize()} warned that this would make the blockage fall instead of truly fixing it.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {child_name} do after the warning?",
                f"{child_name} stepped back and let patience win over impulse. Because {child.pronoun()} waited, the elder could clear the vent without any dirty spill at all.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The vent was cleared, the room grew warm and bright, and {child_name} learned to ask first. The ending shows curiosity still alive, but now walking beside care.",
            )
        )
    elif outcome == "mended":
        qa.append(
            (
                f"What happened when {child_name} poked the vent?",
                f"{blockage.spill_text[0].upper()}{blockage.spill_text[1:]}, and dust darkened the room. The mistake happened because poking shook the blockage loose before anyone was ready for it.",
            )
        )
        qa.append(
            (
                f"How did {elder.label_word} fix the problem?",
                f"{elder.label_word.capitalize()} {response.qa_text}. That careful method cleared the vent properly, so warmth and light could return instead of more mess falling down.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child_name} learned that curiosity is good, but it needs careful hands. The elder's help turned a messy moment into a wiser habit.",
            )
        )
    else:
        qa.append(
            (
                f"Could {elder.label_word} fix the vent right away?",
                f"No. {elder.label_word.capitalize()} tried, but the blockage was too stubborn for that method before nightfall. They could clean the fallen mess, yet they still needed stronger help the next day.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with a lantern on the table and a promise to fetch stronger help at first light. The vent was not fully mended yet, but {child_name} had already begun to use curiosity more wisely.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"vent", "curiosity"}
    blockage = f["blockage_cfg"]
    response = f["response_cfg"]
    tags |= set(blockage.tags)
    if f["outcome"] != "averted":
        tags |= set(response.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({e.type:12}) label={label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        blockage="soot",
        tool="poker",
        response="vent_brush",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        temper="eager",
        delay=0,
    ),
    StoryParams(
        setting="bakehouse",
        blockage="leaves",
        tool="spoon",
        response="ladder_cloth",
        child_name="Tobin",
        child_gender="boy",
        elder_type="grandfather",
        temper="patient",
        delay=0,
    ),
    StoryParams(
        setting="tower",
        blockage="soot",
        tool="reed",
        response="ladder_cloth",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        temper="eager",
        delay=1,
    ),
    StoryParams(
        setting="cottage",
        blockage="cobwebs",
        tool="spoon",
        response="vent_brush",
        child_name="Niko",
        child_gender="boy",
        elder_type="grandfather",
        temper="patient",
        delay=0,
    ),
    StoryParams(
        setting="bakehouse",
        blockage="soot",
        tool="poker",
        response="sweep_hook",
        child_name="Lina",
        child_gender="girl",
        elder_type="grandmother",
        temper="eager",
        delay=0,
    ),
]


ASP_RULES = r"""
valid(S, B)      :- setting(S), blockage(B), spillable(B), setting_has_vent(S).

sensible(R)      :- response(R), sense(R, N), sense_min(M), N >= M.

patient_waits    :- temper(patient).
mended           :- chosen_blockage(B), severity(B, SV), delay(D), chosen_response(R), power(R, P), P >= SV + D.

outcome(averted) :- patient_waits.
outcome(mended)  :- not patient_waits, mended.
outcome(waiting) :- not patient_waits, not mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if "vent" in setting.tags:
            lines.append(asp.fact("setting_has_vent", setting_id))
    for blockage_id, blockage in BLOCKAGES.items():
        lines.append(asp.fact("blockage", blockage_id))
        lines.append(asp.fact("severity", blockage_id, blockage.severity))
        if blockage.spillable:
            lines.append(asp.fact("spillable", blockage_id))
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

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_blockage", params.blockage),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("temper", params.temper),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a curious child, a singing vent, and the careful way to mend what mystery hides."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--temper", choices=TEMPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.blockage and not valid_combo(args.setting, args.blockage):
        raise StoryError(explain_rejection(args.setting, args.blockage))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.blockage is None or combo[1] == args.blockage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, blockage_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    tool_id = args.tool or rng.choice(sorted(TOOLS))
    temper = args.temper or rng.choice(TEMPERS)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        blockage=blockage_id,
        tool=tool_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_type=elder_type,
        temper=temper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.blockage not in BLOCKAGES:
        raise StoryError(f"(Unknown blockage: {params.blockage})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.temper not in TEMPERS:
        raise StoryError(f"(Unknown temper: {params.temper})")
    if not valid_combo(params.setting, params.blockage):
        raise StoryError(explain_rejection(params.setting, params.blockage))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=SETTINGS[params.setting],
        blockage=BLOCKAGES[params.blockage],
        tool=TOOLS[params.tool],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        temper=params.temper,
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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, blockage) combos:\n")
        for setting_id, blockage_id in combos:
            print(f"  {setting_id:10} {blockage_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
                f"### {p.child_name}: {p.blockage} in the vent "
                f"({p.setting}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
