#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py
=================================================================================

A standalone story world for a tiny "space adventure mystery" domain.

A child space cadet is ready for a small launch, but an important object is
missing. A clue on the floor or wall turns the loss into a mystery. The hero
pauses, listens to an inner monologue, remembers an earlier moment in a brief
flashback, and solves the puzzle by following the right helper robot's habit to
the right hiding place. The ending image proves what changed: the missing object
is back, the launch can begin, and the adventure starts with wiser eyes.

Run it
------
    python storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py
    python storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py --place moonport --cause tucked_map --clue moon_dust --helper dromedary
    python storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py --cause polished_badge --helper cargo_drone
    python storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py --all
    python storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dromedary_instance_mystery_to_solve_flashback_inner.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain_woman"}
        male = {"boy", "father", "man", "captain_man"}
        robot = {"robot", "rover", "drone", "bot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in robot:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "captain_woman": "captain",
            "captain_man": "captain",
            "mother": "mom",
            "father": "dad",
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
    intro: str
    sky: str
    craft: str
    spots: set[str] = field(default_factory=set)
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


@dataclass
class Cause:
    id: str
    item_label: str
    item_phrase: str
    hiding_place: str
    residue: str
    reason: str
    mission_need: str
    discovery: str
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
class Clue:
    id: str
    residue: str
    description: str
    flashback: str
    deduction: str
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
    style: str
    access: set[str] = field(default_factory=set)
    habit: str = ""
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "case_open": False,
            "clue_seen": False,
            "flashback": False,
            "deduced": False,
            "found": False,
            "launch_ready": False,
        }

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


def _r_missing_delays(world: World) -> list[str]:
    mission = world.get("mission")
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["missing"] >= THRESHOLD and mission.meters["delay"] < THRESHOLD:
        mission.meters["delay"] += 1
        hero.memes["worry"] += 1
        world.facts["case_open"] = True
        return ["__delay__"]
    return []


def _r_found_clears(world: World) -> list[str]:
    mission = world.get("mission")
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["found"] >= THRESHOLD:
        sig = ("found", item.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        mission.meters["delay"] = 0.0
        hero.memes["worry"] = 0.0
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        world.facts["found"] = True
        world.facts["launch_ready"] = True
        return ["__found__"]
    return []


CAUSAL_RULES = [
    Rule(name="missing_delays", tag="physical", apply=_r_missing_delays),
    Rule(name="found_clears", tag="physical", apply=_r_found_clears),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


PLACES = {
    "moonport": Place(
        id="moonport",
        label="the Moonport Glass Dock",
        intro="A silver dock curved above the moon like a bright smile.",
        sky="Beyond the windows, stars sat still and sharp in the dark.",
        craft="the little comet skiff",
        spots={"tool_locker", "warming_shelf"},
    ),
    "ring_station": Place(
        id="ring_station",
        label="the Blue Ring Station",
        intro="The station hummed softly as it turned over the planet below.",
        sky="Far outside, a blue world rolled under a thin ring of light.",
        craft="the training shuttle",
        spots={"warming_shelf", "cleaning_nook"},
    ),
    "crater_camp": Place(
        id="crater_camp",
        label="the Crater Camp Launch Yard",
        intro="Small domes glowed at the edge of a wide red crater.",
        sky="Above them, the sky was dark velvet pricked with patient stars.",
        craft="the scout hopper",
        spots={"tool_locker", "cleaning_nook"},
    ),
}

CAUSES = {
    "tucked_map": Cause(
        id="tucked_map",
        item_label="star map",
        item_phrase="the folded star map",
        hiding_place="tool_locker",
        residue="moon_dust",
        reason="the helper had tucked the map away to keep it from blowing out through the hatch",
        mission_need="without it, the route to the crystal canyon could not be checked",
        discovery="Inside the tool locker, the folded star map was tucked beside a coil of bright rope.",
        tags={"map", "tool_locker"},
    ),
    "warmed_lantern": Cause(
        id="warmed_lantern",
        item_label="signal lantern",
        item_phrase="the little signal lantern",
        hiding_place="warming_shelf",
        residue="silver_frost",
        reason="the helper had set the lantern on the warm shelf because its battery had gone cold",
        mission_need="without it, the landing lights would not blink their safe hello",
        discovery="On the warm shelf, the little signal lantern glowed again, ready and golden.",
        tags={"lantern", "warming_shelf"},
    ),
    "polished_badge": Cause(
        id="polished_badge",
        item_label="comet badge",
        item_phrase="the shiny comet badge",
        hiding_place="cleaning_nook",
        residue="soap_bubbles",
        reason="the helper had carried the badge to the cleaning nook after juice made it sticky",
        mission_need="without it, the launch suit could not clip closed in the front",
        discovery="In the cleaning nook, the shiny comet badge rested on a towel, sparkling clean.",
        tags={"badge", "cleaning_nook"},
    ),
}

CLUES = {
    "moon_dust": Clue(
        id="moon_dust",
        residue="moon_dust",
        description="a neat crescent of pale moon dust on the floor",
        flashback="Earlier, the hero had seen the helper nose open the locker with a soft click after a windy hatch alarm.",
        deduction="Dust meant the locker wheels had rolled that way from the hatch.",
        tags={"dust", "locker"},
    ),
    "silver_frost": Clue(
        id="silver_frost",
        residue="silver_frost",
        description="a tiny silver frost print beside the wall heater",
        flashback="Earlier, the hero had heard the helper beep sadly at the lantern's sleepy battery and trundle toward the warm shelf.",
        deduction="The frost print meant something cold had been carried toward warmth.",
        tags={"frost", "warming"},
    ),
    "soap_bubbles": Clue(
        id="soap_bubbles",
        residue="soap_bubbles",
        description="three soap bubbles wobbling near the wash sink",
        flashback="Earlier, the hero had laughed when the helper sprayed a cleaning mist at a sticky splash on the badge.",
        deduction="Bubbles meant the cleaner had been busy in the wash nook.",
        tags={"bubbles", "cleaning"},
    ),
}

HELPERS = {
    "dromedary": Helper(
        id="dromedary",
        label="Dromedary",
        type="rover",
        style="a friendly dromedary rover with one tall battery hump and soft sand tires",
        access={"tool_locker", "warming_shelf"},
        habit="It always carried small things to the safest nearby shelf or locker.",
        tags={"dromedary", "robot"},
    ),
    "cargo_drone": Helper(
        id="cargo_drone",
        label="Comet Cart",
        type="drone",
        style="a round cargo drone with blue lights and careful little claws",
        access={"warming_shelf"},
        habit="It liked to rescue cold gadgets and set them where they could warm up.",
        tags={"drone", "robot"},
    ),
    "mop_bot": Helper(
        id="mop_bot",
        label="Spritz",
        type="bot",
        style="a tidy mop-bot with a spinning brush and a humming soap tank",
        access={"cleaning_nook", "tool_locker"},
        habit="It tucked messy or sticky things away until they were clean.",
        tags={"cleaning", "robot"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Tali", "Lina", "Etta", "Iris", "Pia", "Zuri"]
BOY_NAMES = ["Orion", "Milo", "Kian", "Tao", "Remy", "Jules", "Nico", "Arlo"]
TRAITS = ["careful", "curious", "steady", "bright", "thoughtful", "brave"]


def valid_combo(place_id: str, cause_id: str, clue_id: str, helper_id: str) -> bool:
    if place_id not in PLACES or cause_id not in CAUSES or clue_id not in CLUES or helper_id not in HELPERS:
        return False
    place = PLACES[place_id]
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    helper = HELPERS[helper_id]
    return (
        clue.residue == cause.residue
        and cause.hiding_place in place.spots
        and cause.hiding_place in helper.access
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for cause_id in CAUSES:
            for clue_id in CLUES:
                for helper_id in HELPERS:
                    if valid_combo(place_id, cause_id, clue_id, helper_id):
                        combos.append((place_id, cause_id, clue_id, helper_id))
    return combos


def explain_rejection(place_id: str, cause_id: str, clue_id: str, helper_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if cause_id not in CAUSES:
        return f"(No story: unknown cause '{cause_id}'.)"
    if clue_id not in CLUES:
        return f"(No story: unknown clue '{clue_id}'.)"
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    place = PLACES[place_id]
    cause = CAUSES[cause_id]
    clue = CLUES[clue_id]
    helper = HELPERS[helper_id]
    if clue.residue != cause.residue:
        return (
            f"(No story: the clue '{clue_id}' leaves {clue.residue.replace('_', ' ')}, "
            f"but the cause '{cause_id}' would leave {cause.residue.replace('_', ' ')}. "
            f"The mystery would not be solvable honestly.)"
        )
    if cause.hiding_place not in place.spots:
        return (
            f"(No story: {place.label} has no {cause.hiding_place.replace('_', ' ')}, "
            f"so that hiding place cannot appear there.)"
        )
    if cause.hiding_place not in helper.access:
        return (
            f"(No story: {helper.label} cannot reach the {cause.hiding_place.replace('_', ' ')}, "
            f"so it could not have moved the item there.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_delay(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "delayed": sim.get("mission").meters["delay"] >= THRESHOLD,
        "worry": sim.get("hero").memes["worry"],
    }


def setup_scene(world: World, hero: Entity, captain: Entity, helper: Helper, cause: Cause) -> None:
    item = world.get("item")
    item.meters["missing"] = 1.0
    world.say(
        f"{world.place.intro} {world.place.sky} {hero.id}, a little cadet with a shiny helmet stripe, "
        f"was supposed to ride {world.place.craft} with Captain Sol before breakfast stars faded."
    )
    world.say(
        f"Nearby rolled {HELPERS[world.facts['helper_cfg'].id].label}, {helper.style}. "
        f"{HELPERS[world.facts['helper_cfg'].id].habit}"
    )
    world.say(
        f"But when {hero.id} reached for {cause.item_phrase}, it was gone. "
        f"Without it, {cause.mission_need}."
    )
    pred = predict_delay(world)
    world.facts["predicted_delay"] = pred["delayed"]
    propagate(world, narrate=False)
    if pred["delayed"]:
        world.say(
            f"Captain Sol checked the clock and sighed. The tiny launch would have to wait."
        )


def open_mystery(world: World, hero: Entity, captain: Entity, cause: Cause) -> None:
    hero.memes["curious"] += 1
    world.say(
        f'"This is a mystery," {hero.id} whispered. {hero.pronoun().capitalize()} looked under the seat net, '
        f"inside the snack bin, and even behind the moon boots."
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head, a small brave thought spoke up: '
        f'"In this instance, rushing will only make the mystery bigger. Look for what changed."'
    )


def notice_clue(world: World, hero: Entity, clue: Clue) -> None:
    world.facts["clue_seen"] = True
    hero.memes["focus"] += 1
    world.say(
        f"Then {hero.id} saw {clue.description}. It did not belong there, and that made {hero.pronoun('object')} stop and stare."
    )


def flashback(world: World, hero: Entity, clue: Clue, helper: Helper) -> None:
    world.facts["flashback"] = True
    hero.memes["memory"] += 1
    world.say(
        f"A flashback blinked across {hero.pronoun('possessive')} mind like a little movie. "
        f"{clue.flashback} {helper.label} had looked busy, not naughty."
    )


def deduce(world: World, hero: Entity, cause: Cause, clue: Clue) -> None:
    world.facts["deduced"] = True
    hero.memes["confidence"] += 1
    world.say(
        f'"Wait," {hero.id} murmured. "{clue.deduction} Maybe nobody stole anything. '
        f'Maybe the helper moved it for a reason."'
    )
    world.say(
        f"That idea fit the whole puzzle at once, and the scary feeling in {hero.pronoun('possessive')} chest began to loosen."
    )


def search(world: World, hero: Entity, captain: Entity, cause: Cause, helper: Helper) -> None:
    hero.attrs["target_place"] = cause.hiding_place
    place_words = cause.hiding_place.replace("_", " ")
    world.say(
        f'{hero.id} took Captain Sol by the hand and pointed. "Let\'s check the {place_words}," '
        f'{hero.pronoun()} said. {helper.label} gave a happy little beep and rolled ahead.'
    )


def find_item(world: World, hero: Entity, captain: Entity, cause: Cause) -> None:
    item = world.get("item")
    item.meters["missing"] = 0.0
    item.meters["found"] = 1.0
    propagate(world, narrate=False)
    world.say(cause.discovery)
    world.say(
        f'Captain Sol smiled wide. "So that was it. It was not lost at all. It was being kept safe."'
    )


def explain_solution(world: World, hero: Entity, captain: Entity, cause: Cause) -> None:
    world.say(
        f"{hero.id} remembered the earlier moment and understood it now: {cause.reason}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} clipped the item into place, and the whole dock seemed to breathe again."
    )


def launch(world: World, hero: Entity, captain: Entity, cause: Cause) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Soon {world.place.craft} lifted with a silver hum. {hero.id} looked out at the stars and felt bigger inside."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had solved a space mystery by thinking slowly, trusting a memory, and following one true clue."
    )


def tell(
    place: Place,
    cause: Cause,
    clue: Clue,
    helper_cfg: Helper,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    captain_type: str = "captain_woman",
    trait: str = "curious",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["little", trait],
        attrs={"target_place": ""},
    ))
    captain = world.add(Entity(
        id="Captain Sol",
        kind="character",
        type=captain_type,
        role="captain",
        label="the captain",
        attrs={},
    ))
    helper_ent = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        attrs={"access": sorted(helper_cfg.access)},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="gear",
        label=cause.item_label,
        attrs={"hiding_place": cause.hiding_place},
    ))
    mission = world.add(Entity(
        id="mission",
        kind="thing",
        type="mission",
        label="the launch",
        attrs={},
    ))
    world.facts.update(
        hero=hero,
        captain=captain,
        helper=helper_ent,
        helper_cfg=helper_cfg,
        cause=cause,
        clue=clue,
        place=place,
        item=item,
        mission=mission,
    )

    setup_scene(world, hero, captain, helper_cfg, cause)
    world.para()
    open_mystery(world, hero, captain, cause)
    notice_clue(world, hero, clue)
    flashback(world, hero, clue, helper_cfg)
    deduce(world, hero, cause, clue)
    world.para()
    search(world, hero, captain, cause, helper_cfg)
    find_item(world, hero, captain, cause)
    explain_solution(world, hero, captain, cause)
    world.para()
    launch(world, hero, captain, cause)
    return world


@dataclass
class StoryParams:
    place: str
    cause: str
    clue: str
    helper: str
    hero: str
    gender: str
    captain: str
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


KNOWLEDGE = {
    "dromedary": [
        (
            "What is a dromedary?",
            "A dromedary is a one-humped camel. In this story world, the rover is called a dromedary rover because its tall battery hump looks like that camel's back.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back at something that happened earlier. It helps the reader understand the mystery by bringing back an important memory.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that points toward an answer. Good clues help someone solve a mystery without guessing wildly.",
        )
    ],
    "robot": [
        (
            "Why might a helper robot move something?",
            "A helper robot may move an object to keep it safe, clean, or warm. That can look confusing at first, even when the robot is trying to help.",
        )
    ],
    "space": [
        (
            "Why do space crews keep tools in special places?",
            "They keep tools and gear in special places so nothing floats away, gets cold, or gets dirty. Careful storage helps everyone stay safe and ready.",
        )
    ],
    "warming": [
        (
            "Why would a battery light need warmth?",
            "Cold can make some batteries weak. A warm shelf can help a small light work properly again.",
        )
    ],
    "cleaning": [
        (
            "Why clean sticky things before using them?",
            "Sticky dirt can make clips and buttons harder to use. Cleaning helps the object work the way it should.",
        )
    ],
    "locker": [
        (
            "What is a locker for?",
            "A locker is a safe place to store important things. Putting an item in a locker can protect it from getting lost or blown away.",
        )
    ],
}
KNOWLEDGE_ORDER = ["dromedary", "flashback", "clue", "robot", "space", "warming", "cleaning", "locker"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    cause = world.facts["cause"]
    place = world.facts["place"]
    helper = world.facts["helper_cfg"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old where a cadet solves a missing-item mystery. Include the words "dromedary" and "instance".',
        f"Tell a gentle mystery story set at {place.label} where {hero.id} notices one clue, has a flashback, and realizes that {helper.label} moved {cause.item_phrase} for a good reason.",
        f"Write a child-facing story with inner monologue, one honest clue, and a happy launch at the end after the hero solves the puzzle by remembering something important.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    cause = world.facts["cause"]
    clue = world.facts["clue"]
    helper_cfg = world.facts["helper_cfg"]
    place = world.facts["place"]
    craft = place.craft
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little space cadet, Captain Sol, and {helper_cfg.label}. They are getting ready for a launch when an important item seems to be missing.",
        ),
        (
            f"What was the mystery at {place.label}?",
            f"The mystery was that {cause.item_phrase} was gone just when the crew needed it. That mattered because {cause.mission_need}.",
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {clue.description}. That clue mattered because it matched where the missing item had really been taken.",
        ),
        (
            f"How did the flashback help {hero.id} solve the mystery?",
            f"The flashback brought back an earlier moment with {helper_cfg.label}. It helped {hero.id} understand that the item had been moved to help, not to cause trouble.",
        ),
        (
            f"Why did {hero.id} stop rushing?",
            f"{hero.id} listened to an inner thought and chose to think carefully instead of panicking. That calm choice made it easier to connect the clue to the memory.",
        ),
        (
            f"Where was {cause.item_phrase}, and why was it there?",
            f"It was in the {cause.hiding_place.replace('_', ' ')}. It was there because {cause.reason}.",
        ),
        (
            f"How did the story end?",
            f"The crew found the missing item and the delay ended, so {craft} could finally lift off. The ending shows that careful thinking turned a scary mystery into the start of an adventure.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    cause = world.facts["cause"]
    helper = world.facts["helper_cfg"]
    tags = {"flashback", "clue", "space", "robot"}
    if helper.id == "dromedary":
        tags.add("dromedary")
    if cause.hiding_place == "warming_shelf":
        tags.add("warming")
    if cause.hiding_place == "cleaning_nook":
        tags.add("cleaning")
    if cause.hiding_place == "tool_locker":
        tags.add("locker")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", [], {}, None)}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if isinstance(v, (bool, int, float, str))} }")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moonport",
        cause="tucked_map",
        clue="moon_dust",
        helper="dromedary",
        hero="Nova",
        gender="girl",
        captain="captain_woman",
        trait="thoughtful",
    ),
    StoryParams(
        place="ring_station",
        cause="warmed_lantern",
        clue="silver_frost",
        helper="cargo_drone",
        hero="Orion",
        gender="boy",
        captain="captain_man",
        trait="steady",
    ),
    StoryParams(
        place="crater_camp",
        cause="polished_badge",
        clue="soap_bubbles",
        helper="mop_bot",
        hero="Mira",
        gender="girl",
        captain="captain_woman",
        trait="curious",
    ),
    StoryParams(
        place="moonport",
        cause="warmed_lantern",
        clue="silver_frost",
        helper="dromedary",
        hero="Kian",
        gender="boy",
        captain="captain_man",
        trait="bright",
    ),
]


ASP_RULES = r"""
matches(Cause, Clue) :- cause(Cause), clue(Clue), cause_residue(Cause, R), clue_residue(Clue, R).
place_has(Place, Spot) :- place(Place), spot(Spot), has_spot(Place, Spot).
helper_can(Helper, Spot) :- helper(Helper), spot(Spot), can_access(Helper, Spot).

valid(Place, Cause, Clue, Helper) :-
    place(Place), cause(Cause), clue(Clue), helper(Helper),
    cause_hiding_place(Cause, Spot),
    matches(Cause, Clue),
    place_has(Place, Spot),
    helper_can(Helper, Spot).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spot in sorted(place.spots):
            lines.append(asp.fact("spot", spot))
            lines.append(asp.fact("has_spot", place_id, spot))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_residue", cause_id, cause.residue))
        lines.append(asp.fact("cause_hiding_place", cause_id, cause.hiding_place))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_residue", clue_id, clue.residue))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for spot in sorted(helper.access):
            lines.append(asp.fact("can_access", helper_id, spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child space mystery with a clue, a flashback, and an inner monologue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain_woman", "captain_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run generation smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = (
        args.place is not None
        and args.cause is not None
        and args.clue is not None
        and args.helper is not None
    )
    if explicit and not valid_combo(args.place, args.cause, args.clue, args.helper):
        raise StoryError(explain_rejection(args.place, args.cause, args.clue, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        place_id = args.place or next(iter(PLACES))
        cause_id = args.cause or next(iter(CAUSES))
        clue_id = args.clue or next(iter(CLUES))
        helper_id = args.helper or next(iter(HELPERS))
        raise StoryError(explain_rejection(place_id, cause_id, clue_id, helper_id))

    place_id, cause_id, clue_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(pool)
    captain = args.captain or rng.choice(["captain_woman", "captain_man"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        cause=cause_id,
        clue=clue_id,
        helper=helper_id,
        hero=hero,
        gender=gender,
        captain=captain,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.place, params.cause, params.clue, params.helper):
        raise StoryError(explain_rejection(params.place, params.cause, params.clue, params.helper))

    world = tell(
        place=PLACES[params.place],
        cause=CAUSES[params.cause],
        clue=CLUES[params.clue],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero,
        hero_gender=params.gender,
        captain_type=params.captain,
        trait=params.trait,
    )
    story = world.render()
    if "dromedary" not in story.lower():
        raise StoryError("(Story quality check failed: story text must include 'dromedary'.)")
    if "instance" not in story.lower():
        raise StoryError("(Story quality check failed: story text must include 'instance'.)")
    return StorySample(
        params=params,
        story=story,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print("SMOKE resolve failed:", err)

    for params in smoke_cases:
        try:
            sample = generate(params)
            buf = io.StringIO()
            with redirect_stdout(buf):
                emit(sample, trace=False, qa=False)
            if not sample.story.strip():
                raise StoryError("empty story")
            if "dromedary" not in sample.story.lower() or "instance" not in sample.story.lower():
                raise StoryError("required seed words missing from story")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")
    if rc == 0:
        print(f"OK: generation/emit smoke tests passed on {len(smoke_cases)} scenarios.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause, clue, helper) combos:\n")
        for place_id, cause_id, clue_id, helper_id in combos:
            print(f"  {place_id:12} {cause_id:15} {clue_id:12} {helper_id}")
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
            header = f"### {p.hero}: {p.cause} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
