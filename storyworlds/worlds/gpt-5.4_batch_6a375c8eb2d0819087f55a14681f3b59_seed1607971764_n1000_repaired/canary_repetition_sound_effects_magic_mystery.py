#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/canary_repetition_sound_effects_magic_mystery.py
============================================================================

A standalone story world about a child, a canary, and a tiny mystery in a
creaky old house. The child hears the same strange sound again and again,
follows clues, and discovers that the canary has found a little bit of magic:
a star-bright chime that echoes a soft ring wherever it goes.

The world model tracks physical state (where things are, whether something is
hidden, whether a door is stuck, whether the chime is glowing) and emotional
state (worry, wonder, relief, trust). The repeated mystery beat comes from live
state: the sound happens in several places because the canary carries the
enchanted chime from room to room.

Run it
------
    python storyworlds/worlds/gpt-5.4/canary_repetition_sound_effects_magic_mystery.py
    python storyworlds/worlds/gpt-5.4/canary_repetition_sound_effects_magic_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/canary_repetition_sound_effects_magic_mystery.py --all
    python storyworlds/worlds/gpt-5.4/canary_repetition_sound_effects_magic_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/canary_repetition_sound_effects_magic_mystery.py --verify
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
HELP_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    hidden: bool = False
    # meters = physical, memes = emotional
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"canary", "bird"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Setting:
    id: str
    place: str
    hush: str
    hidden_spot: str
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
class Sound:
    id: str
    text: str
    echo_text: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    sparkle: str
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
class HidingSpot:
    id: str
    label: str
    phrase: str
    room: str
    stuck: bool = False
    open_sound: str = ""
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
class Helper:
    id: str
    type: str
    label: str
    sense: int
    method: str
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


def _r_repeat_sound(world: World) -> list[str]:
    out: list[str] = []
    canary = world.get("canary")
    charm = world.get("charm")
    if canary.attrs.get("carrying") != "charm":
        return out
    if charm.meters["glowing"] < THRESHOLD:
        return out
    loc = canary.attrs.get("place", "")
    if not loc:
        return out
    sig = ("repeat_sound", loc)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts.setdefault("heard_places", []).append(loc)
    world.get("child").memes["worry"] += 1
    world.get("child").memes["curiosity"] += 1
    out.append("__mystery_sound__")
    return out


def _r_found_relief(world: World) -> list[str]:
    child = world.get("child")
    canary = world.get("canary")
    if canary.hidden or canary.attrs.get("place") == "":
        return []
    if child.meters["found_canary"] < THRESHOLD:
        return []
    sig = ("found_relief", canary.attrs.get("place", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    child.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="repeat_sound", tag="mystery", apply=_r_repeat_sound),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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


def helper_is_sensible(helper: Helper) -> bool:
    return helper.sense >= HELP_MIN


def valid_combo(spot: HidingSpot, helper: Helper) -> bool:
    if spot.stuck and helper.id == "look_alone":
        return False
    return helper_is_sensible(helper)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for sound_id in SOUNDS:
            for magic_id in MAGIC_ITEMS:
                for spot_id, spot in HIDING_SPOTS.items():
                    for helper_id, helper in HELPERS.items():
                        if valid_combo(spot, helper):
                            combos.append((setting_id, sound_id, magic_id, spot_id, helper_id))
    return combos


def predict_search(world: World, spot_id: str, helper_id: str) -> dict:
    sim = world.copy()
    spot = HIDING_SPOTS[spot_id]
    helper = HELPERS[helper_id]
    if helper.id != "look_alone":
        _bring_helper(sim, helper, narrate=False)
    _search(sim, spot, helper, narrate=False)
    return {
        "found": sim.get("child").meters["found_canary"] >= THRESHOLD,
        "opened": sim.get("spot").meters["opened"] >= THRESHOLD,
    }


def _move_canary(world: World, place: str, narrate: bool = False) -> None:
    canary = world.get("canary")
    canary.attrs["place"] = place
    propagate(world, narrate=narrate)


def _bring_helper(world: World, helper: Helper, narrate: bool = True) -> None:
    adult = world.get("helper")
    child = world.get("child")
    adult.attrs["active"] = True
    child.memes["trust"] += 1
    if helper.id == "grandma":
        adult.type = "woman"
    elif helper.id == "caretaker":
        adult.type = "mother"
    else:
        adult.type = "father"
    if narrate:
        world.say(helper.method)


def setup_story(world: World, child: Entity, canary: Entity, setting: Setting) -> None:
    child.memes["love"] += 1
    canary.memes["trust"] += 1
    world.say(
        f"One dusky evening, {child.id} stayed in {setting.place}, where {setting.hush}."
    )
    world.say(
        f"In a sunny cage by the window lived a little canary named {canary.id}. "
        f"{child.id} liked to whisper good-night to the bird every evening."
    )


def vanishing(world: World, child: Entity, canary: Entity, magic: MagicItem) -> None:
    world.say(
        f"That night, {child.id} saw something new in the cage: {magic.phrase}. "
        f"It gave off {magic.sparkle}."
    )
    world.say(
        f'Then came a tiny sound -- "{world.facts["sound"].text}." '
        f'{canary.id} fluttered once, twice, and when {child.id} blinked, the cage door stood open and the canary was gone.'
    )
    canary.hidden = True
    canary.attrs["place"] = "window"
    world.get("charm").meters["glowing"] = 1.0
    world.get("charm").hidden = False
    world.get("charm").attrs["place"] = "window"
    canary.attrs["carrying"] = "charm"
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    world.facts["heard_places"] = []
    _move_canary(world, "window", narrate=False)


def first_clue(world: World, child: Entity, setting: Setting) -> None:
    sound = world.facts["sound"]
    world.say(
        f'{child.id} listened. From the hall came the same whispery sound again: '
        f'"{sound.echo_text}, {sound.echo_text}."'
    )
    world.say(
        f"It was as if the house itself were repeating a secret and pointing toward {setting.hidden_spot}."
    )
    _move_canary(world, "hall", narrate=False)


def second_clue(world: World, child: Entity) -> None:
    sound = world.facts["sound"]
    world.say(
        f'{child.id} padded after it. Soon the sound came once more -- '
        f'"{sound.echo_text}, {sound.echo_text}" -- now from the stairs.'
    )
    world.say("The mystery was moving, and so was the child.")
    _move_canary(world, "stairs", narrate=False)


def ask_for_help(world: World, child: Entity, helper: Helper) -> None:
    pred = predict_search(world, world.facts["spot_cfg"].id, helper.id)
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_opened"] = pred["opened"]
    if helper.id == "look_alone":
        world.say(
            f'{child.id} hugged {child.pronoun("possessive")} own elbows and whispered, '
            f'"I can be brave. I will look, and look, and look."'
        )
    else:
        world.say(
            f'{child.id} did not want the mystery to stay lonely, so {child.pronoun()} called for help.'
        )
        _bring_helper(world, helper, narrate=True)


def stuck_barrier(world: World, spot: HidingSpot, helper: Helper) -> None:
    if not spot.stuck:
        return
    world.get("spot").meters["stuck"] = 1.0
    world.say(
        f"But {spot.phrase} would not open. It gave a hard little {spot.open_sound}, then stayed shut."
    )
    if helper.id == "look_alone":
        world.say(
            f"{world.get('child').id} pulled and pulled, but the secret place would not budge."
        )


def _search(world: World, spot: HidingSpot, helper: Helper, narrate: bool = True) -> None:
    child = world.get("child")
    canary = world.get("canary")
    spot_ent = world.get("spot")
    spot_ent.attrs["place"] = spot.room

    if spot.stuck and helper.id == "look_alone":
        if narrate:
            stuck_barrier(world, spot, helper)
        return

    if spot.stuck and helper.id != "look_alone":
        spot_ent.meters["opened"] += 1
        if narrate:
            world.say(
                f'Together they tried the hidden place again. "{spot.open_sound}!" '
                f'This time it opened.'
            )
    else:
        spot_ent.meters["opened"] += 1
        if narrate:
            world.say(f"{child.id} peeped into {spot.phrase}.")

    canary.hidden = False
    canary.attrs["place"] = spot.room
    child.meters["found_canary"] += 1
    world.get("charm").attrs["place"] = spot.room
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, canary: Entity, magic: MagicItem, spot: HidingSpot) -> None:
    world.say(
        f"Inside {spot.phrase} sat {canary.id}, safe and bright-eyed, with {magic.label} tucked beneath one yellow wing."
    )
    world.say(
        f'When {child.id} held out {child.pronoun("possessive")} hands, the little charm gave a soft '
        f'"{world.facts["sound"].text}" and glowed like a star in a puddle.'
    )


def explain_magic(world: World, child: Entity, helper: Helper, magic: MagicItem) -> None:
    if helper.id == "look_alone":
        world.say(
            f"{child.id} understood it then: the magic charm had been ringing wherever the canary flew, turning one clue into another clue."
        )
    else:
        label = helper.label
        world.say(
            f'{label.capitalize()} smiled softly. "The little thing is enchanted," {world.get("helper").pronoun()} said. '
            f'"It answers movement with music, so it kept saying where the canary had gone."'
        )
    child.memes["wonder"] += 1
    world.get("charm").meters["understood"] += 1


def ending(world: World, child: Entity, canary: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    canary.memes["trust"] += 1
    world.say(
        f"{child.id} carried {canary.id} back to the window and latched the cage with a careful click."
    )
    world.say(
        f"After that, whenever the house grew still, {child.id} smiled at the memory of the mystery -- "
        f"the repeated sound, the glowing clue, and the little canary safe at home in {setting.place}."
    )


def tell(
    setting: Setting,
    sound: Sound,
    magic: MagicItem,
    spot: HidingSpot,
    helper: Helper,
    child_name: str = "Mina",
    child_gender: str = "girl",
    canary_name: str = "Goldie",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    canary = world.add(Entity(id=canary_name, kind="thing", type="canary", role="canary", movable=True))
    helper_ent = world.add(Entity(id="Helper", kind="character", type="mother", role="helper", label="the grown-up"))
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label=magic.label, movable=True))
    spot_ent = world.add(Entity(id="spot", kind="thing", type="spot", label=spot.label, movable=False))

    child.attrs["place"] = "bedroom"
    canary.attrs["place"] = "window"
    canary.attrs["carrying"] = ""
    helper_ent.attrs["active"] = False
    charm.attrs["place"] = "cage"
    spot_ent.attrs["place"] = spot.room
    charm.meters["glowing"] = 0.0
    charm.meters["understood"] = 0.0
    spot_ent.meters["opened"] = 0.0
    spot_ent.meters["stuck"] = 0.0
    child.meters["found_canary"] = 0.0

    child.memes["worry"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["safety"] = 0.0
    canary.memes["trust"] = 0.0

    world.facts["setting"] = setting
    world.facts["sound"] = sound
    world.facts["magic"] = magic
    world.facts["spot_cfg"] = spot
    world.facts["helper_cfg"] = helper
    world.facts["heard_places"] = []

    setup_story(world, child, canary, setting)
    world.para()
    vanishing(world, child, canary, magic)
    first_clue(world, child, setting)
    second_clue(world, child)

    world.para()
    ask_for_help(world, child, helper)
    if spot.stuck:
        stuck_barrier(world, spot, helper)
    _search(world, spot, helper, narrate=True)

    world.para()
    reveal(world, child, canary, magic, spot)
    explain_magic(world, child, helper, magic)
    ending(world, child, canary, setting)

    world.facts.update(
        child=child,
        canary=canary,
        helper=helper_ent,
        found=child.meters["found_canary"] >= THRESHOLD,
        spot_opened=spot_ent.meters["opened"] >= THRESHOLD,
        helper_used=helper.id != "look_alone",
        repeated_count=len(world.facts.get("heard_places", [])),
    )
    return world


SETTINGS = {
    "attic_house": Setting(
        id="attic_house",
        place="the old attic house",
        hush="the floorboards creaked and the lamp made warm circles on the walls",
        hidden_spot="the landing by the stairs",
        tags={"house", "mystery"},
    ),
    "tower_flat": Setting(
        id="tower_flat",
        place="the top-floor tower flat",
        hush="the windows hummed in the wind and shadows sat quietly in the corners",
        hidden_spot="the narrow stair turn",
        tags={"house", "mystery"},
    ),
    "grand_hall": Setting(
        id="grand_hall",
        place="the long hallway house",
        hush="every tick of the clock sounded important",
        hidden_spot="the dark end of the passage",
        tags={"house", "mystery"},
    ),
}

SOUNDS = {
    "ting": Sound(
        id="ting",
        text="ting",
        echo_text="ting... ting",
        tags={"sound", "magic"},
    ),
    "plink": Sound(
        id="plink",
        text="plink",
        echo_text="plink... plink",
        tags={"sound", "magic"},
    ),
    "chime": Sound(
        id="chime",
        text="chime",
        echo_text="chime... chime",
        tags={"sound", "magic"},
    ),
}

MAGIC_ITEMS = {
    "starbell": MagicItem(
        id="starbell",
        label="a tiny star-bell",
        phrase="a tiny star-bell no bigger than a thumb",
        sparkle="a silver-blue shimmer",
        tags={"magic", "bell"},
    ),
    "moon_charm": MagicItem(
        id="moon_charm",
        label="a moon charm",
        phrase="a moon charm shaped like a drop of light",
        sparkle="a pale golden glow",
        tags={"magic", "charm"},
    ),
    "glass_note": MagicItem(
        id="glass_note",
        label="a glass note",
        phrase="a clear glass note that looked almost like frozen song",
        sparkle="a pearly shine",
        tags={"magic", "music"},
    ),
}

HIDING_SPOTS = {
    "hat_box": HidingSpot(
        id="hat_box",
        label="hat box",
        phrase="the round hat box on the landing shelf",
        room="landing",
        stuck=False,
        open_sound="fuff",
        tags={"box"},
    ),
    "linen_chest": HidingSpot(
        id="linen_chest",
        label="linen chest",
        phrase="the old linen chest under the stairs",
        room="under_stairs",
        stuck=True,
        open_sound="creeeak",
        tags={"chest"},
    ),
    "curtain_nook": HidingSpot(
        id="curtain_nook",
        label="curtain nook",
        phrase="the velvet curtain nook by the tall clock",
        room="hall_end",
        stuck=False,
        open_sound="swish",
        tags={"curtain"},
    ),
}

HELPERS = {
    "look_alone": Helper(
        id="look_alone",
        type="solo",
        label="no grown-up",
        sense=2,
        method="",
        tags={"brave"},
    ),
    "grandma": Helper(
        id="grandma",
        type="grandma",
        label="grandma",
        sense=3,
        method="Grandma came with a candle-lamp and listened with one finger raised, as if even the air might speak.",
        tags={"family", "help"},
    ),
    "caretaker": Helper(
        id="caretaker",
        type="mother",
        label="mom",
        sense=3,
        method="Mom came softly down the hall and said they would solve the mystery together.",
        tags={"family", "help"},
    ),
    "shout_and_wait": Helper(
        id="shout_and_wait",
        type="noise",
        label="nobody useful",
        sense=1,
        method="",
        tags={"bad_help"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ivy", "Wren", "Tessa", "Lucy", "Ada"]
BOY_NAMES = ["Owen", "Leo", "Milo", "Finn", "Eli", "Theo", "Jasper", "Noah"]
CANARY_NAMES = ["Goldie", "Sunny", "Pip", "Dandy", "Saffron", "Flit"]


@dataclass
class StoryParams:
    setting: str
    sound: str
    magic_item: str
    hiding_spot: str
    helper: str
    child_name: str
    child_gender: str
    canary_name: str
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
    "canary": [
        (
            "What is a canary?",
            "A canary is a small yellow songbird. People sometimes keep canaries as gentle pets because they sing bright little songs."
        )
    ],
    "sound": [
        (
            "Why can a small sound help solve a mystery?",
            "A small sound can tell you where something is, especially in a quiet place. If it happens again and again, it can become a clue you can follow."
        )
    ],
    "magic": [
        (
            "What is a magic charm in a story?",
            "A magic charm is a tiny object with special powers. In stories, it might glow, ring, or help people notice something hidden."
        )
    ],
    "bell": [
        (
            "Why does a bell make a good clue?",
            "A bell is useful as a clue because it can be heard even when it is small. Its sound can lead someone toward the place where it is hiding."
        )
    ],
    "charm": [
        (
            "What does a charm mean in a story?",
            "A charm is a little special object that may carry luck or magic. In a mystery story, it can make ordinary things feel secret and important."
        )
    ],
    "music": [
        (
            "How can music feel mysterious?",
            "Music can feel mysterious when it is soft, far away, or keeps repeating from a place you cannot yet see. Then it sounds like a message waiting to be understood."
        )
    ],
    "help": [
        (
            "Why is it smart to ask a grown-up for help with a mystery?",
            "A grown-up can help you stay calm and notice good clues. Asking for help can solve the problem safely and faster."
        )
    ],
    "box": [
        (
            "What is a hat box?",
            "A hat box is a round box used to hold hats. In stories, it can also be a good hiding place because it is big enough to tuck small things inside."
        )
    ],
    "chest": [
        (
            "What is a chest?",
            "A chest is a big box with a lid for storing things like blankets or clothes. Old chests in stories often creak and make fine secret places."
        )
    ],
    "curtain": [
        (
            "What is a curtain nook?",
            "A curtain nook is a little space hidden by a curtain. It feels secret because cloth can cover what is behind it."
        )
    ],
}
KNOWLEDGE_ORDER = ["canary", "sound", "magic", "bell", "charm", "music", "help", "box", "chest", "curtain"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    sound = world.facts["sound"]
    magic = world.facts["magic"]
    helper_cfg = world.facts["helper_cfg"]
    base = (
        f'Write a short mystery story for a 3-to-5-year-old about a canary, a repeating sound, and a magical clue. Include the word "canary".'
    )
    if helper_cfg.id == "look_alone":
        return [
            base,
            f"Tell a gentle mystery where {child.id} hears '{sound.text}' again and again, follows the sound alone, and finds a canary carrying {magic.label}.",
            f"Write a child-friendly magical mystery in which repetition helps solve the puzzle because the same sound keeps leading the child forward.",
        ]
    return [
        base,
        f"Tell a gentle mystery where {child.id} hears '{sound.text}' again and again, asks a grown-up for help, and discovers a canary hiding with {magic.label}.",
        f"Write a magical mystery where a repeated sound becomes a clue, a helper joins the search, and the ending proves the canary is safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    canary = world.facts["canary"]
    setting = world.facts["setting"]
    sound = world.facts["sound"]
    magic = world.facts["magic"]
    spot = world.facts["spot_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    heard = list(world.facts.get("heard_places", []))
    helper_word = helper_cfg.label
    if helper_cfg.id == "look_alone":
        helper_sentence = f"{child.id} searched alone."
    else:
        helper_sentence = f"{helper_word.capitalize()} came to help, so {child.id} did not have to solve the mystery alone."
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and a pet canary named {canary.id}. The story happens in {setting.place}, where a strange little mystery begins."
        ),
        (
            "What made the mystery start?",
            f"The mystery started when the cage door stood open and the canary was gone. At the same time, a magic object made a tiny sound, which turned the disappearance into a clue."
        ),
        (
            "Why did the sound matter?",
            f'The sound mattered because it kept happening again and again in new places. That repetition told {child.id} that the clue was moving through the house.'
        ),
    ]
    if heard:
        qa.append(
            (
                "Where did the repeated sound lead?",
                f"It led from one place to another, including {', '.join(heard)}. Each new sound pulled {child.id} closer to the hiding place."
            )
        )
    if helper_cfg.id == "look_alone":
        qa.append(
            (
                f"How did {child.id} solve the mystery?",
                f"{child.id} kept following the repeated sound and searched carefully until the hiding place was found. {helper_sentence}"
            )
        )
    else:
        qa.append(
            (
                f"How did {helper_word} help solve the mystery?",
                f"{helper_word.capitalize()} came along and helped open or check the hiding place. That help mattered because the clue could be followed more calmly and safely together."
            )
        )
    qa.append(
        (
            "What was the magical clue really doing?",
            f"The magical clue was ringing wherever the canary carried it. That is why the sound kept repeating before the child finally found {spot.phrase}."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the canary safe again and the mystery understood at last. The careful ending image is the cage being latched with a click, showing that things are calm now."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"canary"}
    tags |= set(world.facts["sound"].tags)
    tags |= set(world.facts["magic"].tags)
    tags |= set(world.facts["spot_cfg"].tags)
    if world.facts.get("helper_used"):
        tags |= {"help"}
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  heard_places={world.facts.get('heard_places', [])}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic_house",
        sound="ting",
        magic_item="starbell",
        hiding_spot="hat_box",
        helper="look_alone",
        child_name="Mina",
        child_gender="girl",
        canary_name="Goldie",
        seed=101,
    ),
    StoryParams(
        setting="tower_flat",
        sound="plink",
        magic_item="moon_charm",
        hiding_spot="linen_chest",
        helper="grandma",
        child_name="Owen",
        child_gender="boy",
        canary_name="Sunny",
        seed=102,
    ),
    StoryParams(
        setting="grand_hall",
        sound="chime",
        magic_item="glass_note",
        hiding_spot="curtain_nook",
        helper="caretaker",
        child_name="Nora",
        child_gender="girl",
        canary_name="Pip",
        seed=103,
    ),
]


def explain_rejection(spot: HidingSpot, helper: Helper) -> str:
    if helper.id == "shout_and_wait":
        return (
            f"(Refusing helper '{helper.id}': it is not a sensible way to solve a gentle mystery. "
            f"Pick a calmer helper who actually helps search.)"
        )
    if spot.stuck and helper.id == "look_alone":
        return (
            f"(No story: {spot.phrase} is stuck, so a child searching alone cannot reasonably open it. "
            f"Choose a helper who can assist.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
helper_sensible(H) :- helper(H), sense(H,S), help_min(M), S >= M.
needs_help(Spot)   :- spot(Spot), spot_stuck(Spot).
valid_combo(Spot,H) :- helper_sensible(H), spot(Spot), helper(H), not blocked(Spot,H).
blocked(Spot,look_alone) :- needs_help(Spot).

valid(Se,So,Ma,Sp,H) :- setting(Se), sound(So), magic_item(Ma), spot(Sp), helper(H), valid_combo(Sp,H).

found(Sp,H) :- valid_combo(Sp,H).
opened(Sp,H) :- valid_combo(Sp,H), not blocked(Sp,H).
opened(Sp,H) :- valid_combo(Sp,H), not needs_help(Sp).

#show valid/5.
#show found/2.
#show opened/2.
#show helper_sensible/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for mid in MAGIC_ITEMS:
        lines.append(asp.fact("magic_item", mid))
    for spid, spot in HIDING_SPOTS.items():
        lines.append(asp.fact("spot", spid))
        if spot.stuck:
            lines.append(asp.fact("spot_stuck", spid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
    lines.append(asp.fact("help_min", HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_helper_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(h for (h,) in asp.atoms(model, "helper_sensible"))


def asp_predict(spot_id: str, helper_id: str) -> tuple[bool, bool]:
    import asp
    extra = ""
    model = asp.one_model(asp_program(extra))
    found_atoms = set(asp.atoms(model, "found"))
    opened_atoms = set(asp.atoms(model, "opened"))
    return ((spot_id, helper_id) in found_atoms, (spot_id, helper_id) in opened_atoms)


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_sensible = {hid for hid, helper in HELPERS.items() if helper_is_sensible(helper)}
    asp_sensible = set(asp_helper_sensible())
    if py_sensible == asp_sensible:
        print(f"OK: sensible helpers match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: python={sorted(py_sensible)} asp={sorted(asp_sensible)}")

    for spot_id, spot in HIDING_SPOTS.items():
        for helper_id, helper in HELPERS.items():
            py_pred = valid_combo(spot, helper)
            found, opened = asp_predict(spot_id, helper_id)
            asp_pred = (spot_id, helper_id) in {(sp, hp) for (_, _, _, sp, hp) in asp_valid}
            if py_pred != asp_pred:
                rc = 1
                print(f"MISMATCH predict-valid for ({spot_id}, {helper_id})")
            if asp_pred and not found:
                rc = 1
                print(f"MISMATCH found false for valid ({spot_id}, {helper_id})")
            if spot.stuck and helper_id == "look_alone" and opened:
                rc = 1
                print(f"MISMATCH opened true for blocked ({spot_id}, {helper_id})")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a canary, a repeating sound, and a magical mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--magic-item", dest="magic_item", choices=MAGIC_ITEMS)
    ap.add_argument("--hiding-spot", dest="hiding_spot", choices=HIDING_SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--canary-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hiding_spot and args.helper:
        spot = HIDING_SPOTS[args.hiding_spot]
        helper = HELPERS[args.helper]
        if not valid_combo(spot, helper):
            raise StoryError(explain_rejection(spot, helper))
    if args.helper and not helper_is_sensible(HELPERS[args.helper]):
        raise StoryError(explain_rejection(HIDING_SPOTS[args.hiding_spot] if args.hiding_spot else next(iter(HIDING_SPOTS.values())), HELPERS[args.helper]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.sound is None or c[1] == args.sound)
        and (args.magic_item is None or c[2] == args.magic_item)
        and (args.hiding_spot is None or c[3] == args.hiding_spot)
        and (args.helper is None or c[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sound_id, magic_id, spot_id, helper_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    canary_name = args.canary_name or rng.choice(CANARY_NAMES)
    return StoryParams(
        setting=setting_id,
        sound=sound_id,
        magic_item=magic_id,
        hiding_spot=spot_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        canary_name=canary_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        sound = SOUNDS[params.sound]
        magic = MAGIC_ITEMS[params.magic_item]
        spot = HIDING_SPOTS[params.hiding_spot]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_combo(spot, helper):
        raise StoryError(explain_rejection(spot, helper))

    world = tell(
        setting=setting,
        sound=sound,
        magic=magic,
        spot=spot,
        helper=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        canary_name=params.canary_name,
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
        print(f"{len(combos)} compatible (setting, sound, magic_item, hiding_spot, helper) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{x:12}" for x in row))
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
                f"### {p.child_name}: {p.sound} / {p.magic_item} / {p.hiding_spot} / {p.helper}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
