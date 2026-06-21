#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/delta_quill_sound_effects_whodunit.py
================================================================

A standalone story world for a tiny child-facing whodunit: during a rainy
afternoon at a nature house near a river delta, a careful child's feather quill
goes missing just before picture-sign time. A series of concrete sounds
(*tap-tap*, *swish*, *clack!*, *drip drip*) help the children trace what
happened. The truth is never mean or criminal: a helper animal carried the quill
off for nest-building, and the children solve the mystery by following the sound
trail and making a gentle repair.

The world model tracks:
- typed entities with physical meters and emotional memes
- a short causal chain from gust -> window rattle -> quill falls -> helper carries it
- a clue system grounded in sound effects
- a reasonableness gate so only plausible helper/place/tool combinations generate
- an inline ASP twin for parity with the Python gate and outcome model

Run it
------
python storyworlds/worlds/gpt-5.4/delta_quill_sound_effects_whodunit.py
python storyworlds/worlds/gpt-5.4/delta_quill_sound_effects_whodunit.py --place delta_house --helper magpie --tool listening_cone --seed 7 --qa
python storyworlds/worlds/gpt-5.4/delta_quill_sound_effects_whodunit.py --place pond_hide --helper otter
python storyworlds/worlds/gpt-5.4/delta_quill_sound_effects_whodunit.py --all
python storyworlds/worlds/gpt-5.4/delta_quill_sound_effects_whodunit.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    nest_builder: bool = False
    sound_maker: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"magpie", "otter", "heron", "duck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    scene: str
    inside: str
    outside: str
    weather_sound: str
    clue_sound: str
    has_open_window: bool = True
    carries: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    type: str
    move_sound: str
    nest_spot: str
    reason: str
    can_carry_quill: bool = True
    likes_shiny: bool = False
    likes_soft: bool = False
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
    use_line: str
    finds: set[str] = field(default_factory=set)
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
class Prize:
    id: str
    label: str
    phrase: str
    use_for: str
    ending_image: str
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


def _r_gust_knocks(world: World) -> list[str]:
    quill = world.get("quill")
    room = world.get("room")
    window = world.get("window")
    if room.meters["gust"] < THRESHOLD or not world.facts.get("window_open", False):
        return []
    if ("gust_knocks",) in world.fired:
        return []
    world.fired.add(("gust_knocks",))
    window.meters["rattle"] += 1
    quill.meters["fallen"] += 1
    world.facts["heard_sounds"].append(world.facts["place"].weather_sound)
    world.facts["heard_sounds"].append("clatter-clack!")
    return ["__fall__"]


def _r_helper_takes(world: World) -> list[str]:
    quill = world.get("quill")
    helper = world.get("helper")
    if quill.meters["fallen"] < THRESHOLD or helper.meters["near"] < THRESHOLD:
        return []
    if ("helper_takes",) in world.fired:
        return []
    world.fired.add(("helper_takes",))
    quill.meters["missing"] += 1
    quill.attrs["location"] = "nest"
    helper.meters["carrying"] += 1
    world.facts["heard_sounds"].append(world.facts["helper_cfg"].move_sound)
    world.facts["heard_sounds"].append(world.facts["place"].clue_sound)
    return ["__taken__"]


def _r_missing_worry(world: World) -> list[str]:
    quill = world.get("quill")
    child = world.get("child")
    friend = world.get("friend")
    if quill.meters["missing"] < THRESHOLD:
        return []
    if ("missing_worry",) in world.fired:
        return []
    world.fired.add(("missing_worry",))
    child.memes["worry"] += 1
    friend.memes["curiosity"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="gust_knocks", tag="physical", apply=_r_gust_knocks),
    Rule(name="helper_takes", tag="physical", apply=_r_helper_takes),
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def helper_possible(place: Place, helper: Helper) -> bool:
    return helper.id in place.carries and helper.can_carry_quill


def tool_useful(tool: Tool, helper: Helper, place: Place) -> bool:
    return helper.id in tool.finds or place.id in tool.finds or "any" in tool.finds


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for helper_id, helper in HELPERS.items():
            if not helper_possible(place, helper):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_useful(tool, helper, place):
                    combos.append((place_id, helper_id, tool_id))
    return combos


def explain_rejection(place: Place, helper: Helper, tool: Optional[Tool] = None) -> str:
    if not helper_possible(place, helper):
        return (
            f"(No story: {helper.label} does not belong as the quill-carrying helper at "
            f"{place.label}. Pick a helper that plausibly lives or visits there.)"
        )
    if tool is not None and not tool_useful(tool, helper, place):
        return (
            f"(No story: {tool.label} would not help children follow the sound trail "
            f"to {helper.label} at {place.label}. Pick a tool that can honestly help.)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: "StoryParams") -> str:
    return "returned" if params.share_after else "kept"


def predict_disappearance(place: Place, helper: Helper) -> dict:
    world = World()
    world.facts["place"] = place
    world.facts["helper_cfg"] = helper
    world.facts["window_open"] = place.has_open_window
    world.facts["heard_sounds"] = []
    world.add(Entity(id="room", type="room", label=place.inside))
    world.add(Entity(id="window", type="window", label="window"))
    world.add(Entity(id="quill", type="quill", label="quill", movable=True, attrs={"location": "table"}))
    h = world.add(Entity(id="helper", type=helper.type, label=helper.label, nest_builder=True))
    h.meters["near"] = 1.0
    world.get("room").meters["gust"] = 1.0
    propagate(world, narrate=False)
    return {
        "missing": world.get("quill").meters["missing"] >= THRESHOLD,
        "sounds": list(world.facts["heard_sounds"]),
    }


def introduce(world: World, child: Entity, friend: Entity, teacher: Entity,
              place: Place, prize: Prize) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After lunch at {place.label}, {child.id} and {friend.id} sat by {place.inside}. "
        f"Beyond the glass, {place.outside} stretched toward the delta."
    )
    world.say(
        f"On the table lay {prize.phrase}: a smooth jar of blue ink and {child.id}'s special quill. "
        f"They were getting ready {prize.use_for}."
    )
    world.say(
        f'{teacher.label_word.capitalize()} smiled. "When the page is ready, we will make quiet marsh signs," '
        f"{teacher.pronoun()} said."
    )


def weather_beat(world: World, place: Place) -> None:
    room = world.get("room")
    room.meters["gust"] += 1
    world.say(
        f"Outside, the reeds bent and the weather whispered {place.weather_sound}. "
        f"The loose window gave a tiny shaky rattle."
    )


def discovery(world: World, child: Entity, prize: Prize) -> None:
    world.say(
        f"When {child.id} reached for the quill, {child.pronoun()} stopped. "
        f'"My quill is gone," {child.pronoun()} whispered.'
    )
    child.memes["worry"] += 1


def suspicion(world: World, friend: Entity, child: Entity) -> None:
    friend.memes["curiosity"] += 1
    world.say(
        f'"This is a mystery," said {friend.id}. "Let us be sound detectives." '
        f"{friend.pronoun().capitalize()} put one finger in the air as if listening to invisible footsteps."
    )
    world.say(
        f"{child.id} listened too. The room did not feel mean or spooky, only puzzling."
    )


def investigate(world: World, child: Entity, friend: Entity, teacher: Entity,
                helper: Helper, tool: Tool, place: Place) -> None:
    child.memes["hope"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"{teacher.label_word.capitalize()} handed them {tool.label}. {tool.use_line}"
    )
    sounds = world.facts["heard_sounds"]
    if sounds:
        joined = ", then ".join(sounds[:4])
        world.say(
            f"They stood still and remembered the sounds they had heard: {joined}. "
            f"That trail pointed away from the ink table and toward the open side door."
        )
    clue = helper.move_sound
    world.say(
        f"Near the door they heard {clue} again, softer this time. "
        f'"There!" said {friend.id}.'
    )
    world.say(
        f"They followed the sound past {place.outside} until they reached {helper.nest_spot}."
    )


def solve(world: World, child: Entity, friend: Entity, helper_ent: Entity,
          helper: Helper, prize: Prize, teacher: Entity) -> None:
    quill = world.get("quill")
    helper_ent.meters["found"] += 1
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"There, tucked beside bits of grass, was the missing quill. "
        f"A {helper.label} was nudging it into place."
    )
    world.say(
        f'"So that is the answer," {child.id} said. "It was not a thief at all." '
        f"The little helper had taken the quill because {helper.reason}."
    )
    world.say(
        f"{teacher.label_word.capitalize()} knelt beside them. "
        f'"We can be kind and still solve the mystery," {teacher.pronoun()} said.'
    )
    if world.facts["share_after"]:
        quill.attrs["location"] = "table"
        quill.meters["missing"] = 0.0
        helper_ent.meters["sharing"] += 1
        world.say(
            f"They left a soft reed for the nest and gently carried the quill back. "
            f"Soon {child.id} was using it again {prize.use_for}."
        )
    else:
        quill.attrs["location"] = "nest"
        helper_ent.meters["sharing"] += 1
        child.memes["generous"] += 1
        world.say(
            f"They left the quill where it was and brought out a spare reed pen instead. "
            f"{child.id} decided the nest needed the quill more that day."
        )


def ending(world: World, child: Entity, friend: Entity, prize: Prize, place: Place) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    shared = "returned to the table" if world.facts["share_after"] else "resting safely in the nest"
    world.say(
        f"By the end of the afternoon, the mystery was finished, the quill was {shared}, "
        f"and the children knew how the clues had fit together."
    )
    world.say(
        f"{prize.ending_image} Outside, {place.weather_sound} had softened to a sleepy hush."
    )


def tell(place: Place, helper: Helper, tool: Tool, prize: Prize,
         child_name: str = "Nora", child_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         teacher_type: str = "mother", share_after: bool = True) -> World:
    world = World()
    world.facts["place"] = place
    world.facts["helper_cfg"] = helper
    world.facts["tool_cfg"] = tool
    world.facts["prize_cfg"] = prize
    world.facts["window_open"] = place.has_open_window
    world.facts["heard_sounds"] = []
    world.facts["share_after"] = share_after

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["careful"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["curious"],
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        label="the teacher",
        role="teacher",
        traits=["calm"],
    ))
    room = world.add(Entity(id="room", type="room", label=place.inside))
    world.add(Entity(id="window", type="window", label="the window"))
    world.add(Entity(
        id="quill",
        type="quill",
        label="quill",
        movable=True,
        attrs={"location": "table"},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        type=helper.type,
        label=helper.label,
        nest_builder=True,
        sound_maker=True,
        attrs={"spot": helper.nest_spot},
    ))
    helper_ent.meters["near"] = 1.0
    room.meters["gust"] = 0.0

    introduce(world, child, friend, teacher, place, prize)
    world.para()
    weather_beat(world, place)
    propagate(world, narrate=False)
    discovery(world, child, prize)
    suspicion(world, friend, child)
    world.para()
    investigate(world, child, friend, teacher, helper, tool, place)
    world.para()
    solve(world, child, friend, helper_ent, helper, prize, teacher)
    ending(world, child, friend, prize, place)

    world.facts.update(
        child=child,
        friend=friend,
        teacher=teacher,
        helper=helper_ent,
        quill=world.get("quill"),
        outcome="returned" if share_after else "kept",
        solved=True,
        place_id=place.id,
        helper_id=helper.id,
        tool_id=tool.id,
    )
    return world


PLACES = {
    "delta_house": Place(
        id="delta_house",
        label="the delta nature house",
        scene="a marsh learning room",
        inside="the wide window seat",
        outside="silver reeds and muddy channels",
        weather_sound="drip drip ... swish",
        clue_sound="tap-tap on the boardwalk",
        has_open_window=True,
        carries={"magpie", "duck"},
        tags={"delta", "marsh"},
    ),
    "reed_shed": Place(
        id="reed_shed",
        label="the reed shed by the water",
        scene="a warm little workroom",
        inside="the wooden bench",
        outside="bundles of reeds and a narrow dock",
        weather_sound="patter-patter ... creak",
        clue_sound="scritch-scritch by the reeds",
        has_open_window=True,
        carries={"magpie", "heron"},
        tags={"delta", "reeds"},
    ),
    "pond_hide": Place(
        id="pond_hide",
        label="the pond hide",
        scene="a quiet bird-watching nook",
        inside="the peep window shelf",
        outside="lily pads and a low muddy bank",
        weather_sound="plink plink ... rustle",
        clue_sound="splish-swish near the bank",
        has_open_window=True,
        carries={"otter", "duck"},
        tags={"pond", "water"},
    ),
}

HELPERS = {
    "magpie": Helper(
        id="magpie",
        label="magpie",
        type="magpie",
        move_sound="clack-clack on the roof",
        nest_spot="a twiggy nest above the eaves",
        reason="it liked the quill's shiny nib and neat feather",
        can_carry_quill=True,
        likes_shiny=True,
        tags={"bird", "shiny"},
    ),
    "duck": Helper(
        id="duck",
        label="duck",
        type="duck",
        move_sound="waddle-wap by the puddles",
        nest_spot="a grassy tuck under the porch",
        reason="the feather felt soft for lining a nest",
        can_carry_quill=True,
        likes_soft=True,
        tags={"bird", "soft"},
    ),
    "heron": Helper(
        id="heron",
        label="young heron",
        type="heron",
        move_sound="flap-flap by the dock",
        nest_spot="a messy stick pile near the reeds",
        reason="the long feather looked useful among the reeds",
        can_carry_quill=True,
        likes_soft=True,
        tags={"bird", "reeds"},
    ),
    "otter": Helper(
        id="otter",
        label="otter pup",
        type="otter",
        move_sound="splish-swish by the bank",
        nest_spot="a snug den in the bank grass",
        reason="it had tugged the feathery end while playing",
        can_carry_quill=True,
        likes_soft=False,
        tags={"water", "play"},
    ),
}

TOOLS = {
    "listening_cone": Tool(
        id="listening_cone",
        label="a paper listening cone",
        use_line="\"Hold it by your ear and let the little sounds grow bigger,\" the teacher said.",
        finds={"any"},
        tags={"listen"},
    ),
    "mud_map": Tool(
        id="mud_map",
        label="a muddy footprint map",
        use_line="\"We can mark where each sound came from and see where the trail bends,\" the teacher said.",
        finds={"otter", "duck", "pond_hide"},
        tags={"map"},
    ),
    "reed_scope": Tool(
        id="reed_scope",
        label="a reed scope",
        use_line="\"Look through the tube after you listen, and the reeds will not hide the last clue,\" the teacher said.",
        finds={"magpie", "heron", "reed_shed", "delta_house"},
        tags={"look"},
    ),
}

PRIZES = {
    "signing": Prize(
        id="signing",
        label="quill",
        phrase="their sign-making set",
        use_for="to draw tiny bird tracks on paper",
        ending_image="Blue curls of ink and neat little marsh birds soon marched across the page.",
        tags={"writing", "quill"},
    ),
    "mapmaking": Prize(
        id="mapmaking",
        label="quill",
        phrase="their delta map kit",
        use_for="to trace winding water paths",
        ending_image="Soon a bright paper map showed every bend of water and every patch of reeds.",
        tags={"map", "quill", "delta"},
    ),
}


@dataclass
class StoryParams:
    place: str
    helper: str
    tool: str
    prize: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    teacher: str
    share_after: bool = True
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
    "delta": [
        (
            "What is a delta?",
            "A delta is a place where a river spreads into smaller streams before meeting a bigger body of water. It often has reeds, mud, birds, and shallow channels."
        )
    ],
    "quill": [
        (
            "What is a quill?",
            "A quill is a feather used for writing or drawing. Long ago people dipped quills in ink to make marks on paper."
        )
    ],
    "listen": [
        (
            "Why can listening help solve a mystery?",
            "Listening helps because sounds tell you where something is moving, rattling, or hiding. A careful ear can notice clues your eyes miss at first."
        )
    ],
    "bird": [
        (
            "Why might a bird take a feather or soft thing?",
            "A bird may carry soft or light things to help build or line a nest. Animals do that for shelter, not to be naughty."
        )
    ],
    "water": [
        (
            "What sound can water make?",
            "Water can plink, drip, swish, or splash, depending on how it moves. Those sounds can tell you whether it is raining, flowing, or being stepped in."
        )
    ],
    "map": [
        (
            "What is a map?",
            "A map is a picture that helps show where things are. It can help people remember paths and clues."
        )
    ],
}
KNOWLEDGE_ORDER = ["delta", "quill", "listen", "bird", "water", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    place = f["place"]
    helper = f["helper_cfg"]
    tool = f["tool_cfg"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    ending = "returns the quill after understanding what happened" if outcome == "returned" else "leaves the quill kindly for the nest and uses another pen"
    return [
        f'Write a short whodunit for a 3-to-5-year-old set at {place.label} that includes the words "delta" and "quill" and uses sound effects as clues.',
        f"Tell a gentle mystery where {child.id} notices a missing quill, {friend.id} helps investigate, and a {helper.label} turns out to be the answer instead of a villain.",
        f"Write a child-friendly sound-effects mystery using {tool.label} and ending with a kind solution where the children {ending}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    teacher = f["teacher"]
    helper_cfg = f["helper_cfg"]
    tool_cfg = f["tool_cfg"]
    place = f["place"]
    prize = f["prize_cfg"]
    outcome = f["outcome"]
    sounds = f["heard_sounds"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id} at {place.label}. They are helped by {teacher.label_word} while they solve the mystery of the missing quill."
        ),
        (
            "What was missing?",
            f"{child.id}'s quill was missing from the table. They needed it {prize.use_for}."
        ),
    ]
    if sounds:
        heard = ", ".join(sounds[:4])
        qa.append((
            "What clues helped solve the mystery?",
            f"The children remembered sounds like {heard}. Those noises showed that something had rattled, fallen, and then moved away from the table."
        ))
    qa.append((
        f"Why did {child.id} think the mystery was not scary in the end?",
        f"It turned out that a {helper_cfg.label} had taken the quill, not a mean thief. The answer was about nest-building or play, so the children could solve the problem kindly."
    ))
    qa.append((
        f"How did {tool_cfg.label} help them?",
        f"{tool_cfg.label.capitalize()} helped them pay close attention to the sound trail. By listening carefully, they could follow the clues toward {helper_cfg.nest_spot}."
    ))
    if outcome == "returned":
        qa.append((
            "How did the story end?",
            f"The children traded a soft reed for the nest and brought the quill back. Then {child.id} used it again, which showed the mystery was solved and everyone stayed kind."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"The children chose to leave the quill for the nest and used a spare reed pen instead. That ending showed they understood the mystery and cared about the little helper too."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["place"].tags)
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    tags |= set(f["prize_cfg"].tags)
    tags.add("listen")
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (
            ("movable", ent.movable),
            ("nest_builder", ent.nest_builder),
            ("sound_maker", ent.sound_maker),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  heard_sounds: {world.facts.get('heard_sounds', [])}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="delta_house",
        helper="magpie",
        tool="reed_scope",
        prize="mapmaking",
        child_name="Nora",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        teacher="mother",
        share_after=True,
    ),
    StoryParams(
        place="pond_hide",
        helper="otter",
        tool="mud_map",
        prize="signing",
        child_name="Lily",
        child_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        teacher="father",
        share_after=True,
    ),
    StoryParams(
        place="reed_shed",
        helper="heron",
        tool="reed_scope",
        prize="mapmaking",
        child_name="Maya",
        child_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        teacher="mother",
        share_after=False,
    ),
    StoryParams(
        place="delta_house",
        helper="duck",
        tool="listening_cone",
        prize="signing",
        child_name="Ava",
        child_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        teacher="father",
        share_after=True,
    ),
]


ASP_RULES = r"""
helper_possible(P,H) :- place(P), helper(H), carries(P,H), can_carry_quill(H).
tool_useful(T,H,P) :- tool(T), helper(H), finds(T,H).
tool_useful(T,H,P) :- tool(T), place(P), finds(T,P).
tool_useful(T,H,P) :- tool(T), finds(T,any).
valid(P,H,T) :- helper_possible(P,H), tool_useful(T,H,P).

outcome(returned) :- share_after.
outcome(kept) :- not share_after.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.has_open_window:
            lines.append(asp.fact("open_window", place_id))
        for helper_id in sorted(place.carries):
            lines.append(asp.fact("carries", place_id, helper_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        if helper.can_carry_quill:
            lines.append(asp.fact("can_carry_quill", helper_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for item in sorted(tool.finds):
            lines.append(asp.fact("finds", tool_id, item))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("share_after") if params.share_after else ""
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle sound-effects whodunit about a missing quill near a delta."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["mother", "father"])
    ap.add_argument("--share-after", choices=["yes", "no"])
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


GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Zoe", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Tom", "Eli", "Finn", "Max", "Leo", "Sam"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.helper:
        place = PLACES[args.place]
        helper = HELPERS[args.helper]
        if not helper_possible(place, helper):
            raise StoryError(explain_rejection(place, helper))
    if args.place and args.helper and args.tool:
        place = PLACES[args.place]
        helper = HELPERS[args.helper]
        tool = TOOLS[args.tool]
        if not tool_useful(tool, helper, place):
            raise StoryError(explain_rejection(place, helper, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.helper is None or combo[1] == args.helper)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, helper_id, tool_id = rng.choice(sorted(combos))
    prize_id = args.prize or rng.choice(sorted(PRIZES.keys()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != child_name]
    friend_name = args.friend_name or rng.choice(friend_pool)
    teacher = args.teacher or rng.choice(["mother", "father"])
    if args.share_after is None:
        share_after = rng.choice([True, True, False])
    else:
        share_after = args.share_after == "yes"
    return StoryParams(
        place=place_id,
        helper=helper_id,
        tool=tool_id,
        prize=prize_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher=teacher,
        share_after=share_after,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        helper = HELPERS[params.helper]
        tool = TOOLS[params.tool]
        prize = PRIZES[params.prize]
    except KeyError as exc:
        raise StoryError(f"(Invalid option: {exc.args[0]})") from exc
    if not helper_possible(place, helper):
        raise StoryError(explain_rejection(place, helper))
    if not tool_useful(tool, helper, place):
        raise StoryError(explain_rejection(place, helper, tool))

    world = tell(
        place=place,
        helper=helper,
        tool=tool,
        prize=prize,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_type=params.teacher,
        share_after=params.share_after,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    outcomes_bad = 0
    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            outcomes_bad += 1
    if outcomes_bad == 0:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {outcomes_bad}/{len(CURATED)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        smoke_sample = generate(smoke_params)
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
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
        print(f"{len(combos)} compatible (place, helper, tool) combos:\n")
        for place, helper, tool in combos:
            print(f"  {place:12} {helper:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name} & {p.friend_name}: {p.helper} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
