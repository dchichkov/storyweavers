#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py
================================================================================

A standalone story world for a tiny ghost-story-shaped domain set in an elevator.

A child hears a spooky rumor, rides an elevator, notices eerie clues, and feels
a rush of fear. But the world has ordinary causes. A canny child or helper can
spot the real clue, call the right grown-up, and an effective fix turns the
"ghost" into an everyday problem with a safe ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py
    python storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py --source leaking_bag
    python storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py --fix air_freshener
    python storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/canny_icky_effective_elevator_bravery_ghost_story.py --verify
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
BASE_BRAVERY = 4.0


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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "superintendent": "super",
            "caretaker": "caretaker",
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
class Mood:
    id: str
    opener: str
    rumor: str
    shadow: str
    ending: str
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
class Source:
    id: str
    clue: str
    sound: str
    image: str
    smell: str
    material: str
    icky: bool
    hazard: str
    severity: int
    needs_fix: str
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    useful_for: set[str] = field(default_factory=set)
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    car = world.get("car")
    child = world.get("child")
    helper = world.get("helper")
    if source.meters["active"] >= THRESHOLD:
        sig = ("spook", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            car.meters["spooky"] += 1
            child.memes["fear"] += 1
            helper.memes["fear"] += 0.5
            out.append("__spooky__")
    return out


def _r_icky(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    if source.attrs.get("icky") and source.meters["active"] >= THRESHOLD:
        sig = ("icky", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["disgust"] += 1
            out.append("__icky__")
    return out


def _r_canny(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["bravery"] >= THRESHOLD and child.memes["curiosity"] >= THRESHOLD:
        sig = ("canny", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["canny"] += 1
            out.append("__canny__")
    return out


CAUSAL_RULES = [
    Rule(name="spook", tag="emotion", apply=_r_spook),
    Rule(name="icky", tag="emotion", apply=_r_icky),
    Rule(name="canny", tag="emotion", apply=_r_canny),
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


def valid_fix(source: Source, fix: Fix) -> bool:
    return source.needs_fix in fix.useful_for and fix.sense >= SENSE_MIN


def enough_fix(source: Source, fix: Fix) -> bool:
    return fix.power >= source.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mood_id in MOODS:
        for source_id, source in SOURCES.items():
            for fix_id, fix in FIXES.items():
                if valid_fix(source, fix):
                    combos.append((mood_id, source_id, fix_id))
    return combos


def predict_truth(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["active"] += 1
    sim.get("child").memes["curiosity"] += 1
    propagate(sim, narrate=False)
    source = sim.get("source")
    child = sim.get("child")
    return {
        "spooky": sim.get("car").meters["spooky"] >= THRESHOLD,
        "icky": bool(source.attrs.get("icky")),
        "canny": child.memes["canny"] >= THRESHOLD,
    }


def can_investigate(bravery: int, helper_style: str) -> bool:
    bonus = 1 if helper_style in {"steady", "canny"} else 0
    return bravery + bonus >= 5


def explain_rejection(source: Source, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). A storyworld should prefer a more effective repair.)"
        )
    return (
        f"(No story: {fix.id} does not actually solve the problem caused by {source.id}. "
        f"The fix must match the real cause inside the elevator.)"
    )


MOODS = {
    "whispery": Mood(
        id="whispery",
        opener="The apartment hallway was hushed enough to hear the elevator cables hum.",
        rumor='Older kids had been whispering that the elevator had a ghost who rode between floors at dusk.',
        shadow="The dim brass walls held soft shadows that slid when the car moved.",
        ending="After that, the elevator still hummed, but it sounded ordinary instead of haunted.",
        tags={"ghost", "hallway"},
    ),
    "stormy": Mood(
        id="stormy",
        opener="Rain tapped the lobby windows, and the old elevator seemed to listen.",
        rumor='Someone in the building said a ghost liked stormy evenings and sighed inside the elevator.',
        shadow="Each flicker of outside light made the mirrored panel look deeper than it really was.",
        ending="By bedtime, the storm had passed, and the elevator felt like part of the building again, not a ghost story.",
        tags={"ghost", "storm"},
    ),
    "midnightish": Mood(
        id="midnightish",
        opener="Even before supper, the hallway felt like the edge of nighttime.",
        rumor='At mailboxes, people had traded a tiny ghost story about a pale rider who never pressed a button.',
        shadow="The silver doors gave back a shivery reflection that looked stranger than the truth.",
        ending="From then on, the elevator was just an elevator again, and that was a very comforting thing.",
        tags={"ghost", "night"},
    ),
}

SOURCES = {
    "leaking_bag": Source(
        id="leaking_bag",
        clue="a dark drip sliding from a torn grocery bag near the back corner",
        sound="a soft plip... plip...",
        image="a wobbly bag bumping the wall whenever the car shook",
        smell="a sour, icky smell from old soup and peels",
        material="sticky soup and mushy peels",
        icky=True,
        hazard="the floor could get slimy and make someone slip",
        severity=2,
        needs_fix="clean_spill",
        tags={"icky", "spill", "slip"},
    ),
    "vent_string": Source(
        id="vent_string",
        clue="a silver gift ribbon caught in the ceiling vent",
        sound="a whispery skritch-skritch as the ribbon brushed the grate",
        image="the loose ribbon trembling like a tiny white finger",
        smell="no smell at all",
        material="gift ribbon",
        icky=False,
        hazard="the loose ribbon could keep scraping and startling riders",
        severity=1,
        needs_fix="remove_ribbon",
        tags={"rattle", "vent"},
    ),
    "balloon": Source(
        id="balloon",
        clue="a star balloon string snagged above the light panel",
        sound="a squeaky moan when the balloon rubbed the ceiling",
        image="the balloon bobbing in and out of the top corner like it wanted to float away",
        smell="no smell at all",
        material="foil balloon",
        icky=False,
        hazard="the string could tangle and the balloon kept making ghosty sounds",
        severity=1,
        needs_fix="lower_balloon",
        tags={"balloon", "squeak"},
    ),
    "mop_smear": Source(
        id="mop_smear",
        clue="a gray streak of old mop water shining under the light",
        sound="a sticky shff when shoes pulled free of the floor",
        image="a wet smear glimmering like a cold puddle",
        smell="an icky, sour mop smell",
        material="dirty mop water",
        icky=True,
        hazard="the sticky floor could make the elevator feel unsafe and dirty",
        severity=2,
        needs_fix="clean_spill",
        tags={"icky", "cleaning", "slip"},
    ),
}

FIXES = {
    "wipe_and_sign": Fix(
        id="wipe_and_sign",
        sense=3,
        power=2,
        text="used paper towels, soap, and a bright yellow caution sign to wipe the floor until it was clean",
        qa_text="cleaned the messy floor and put up a caution sign",
        useful_for={"clean_spill"},
        tags={"clean", "effective"},
    ),
    "remove_ribbon": Fix(
        id="remove_ribbon",
        sense=3,
        power=1,
        text="stood on the stopped car's safe threshold, gently pulled the ribbon free, and tucked it away",
        qa_text="pulled the ribbon out of the vent so it could not scrape anymore",
        useful_for={"remove_ribbon"},
        tags={"fix", "effective"},
    ),
    "lower_balloon": Fix(
        id="lower_balloon",
        sense=3,
        power=1,
        text="caught the balloon string, lowered the balloon, and tied it short so it could not rub the ceiling",
        qa_text="lowered the balloon and tied the string so it stopped squeaking",
        useful_for={"lower_balloon"},
        tags={"fix", "effective"},
    ),
    "air_freshener": Fix(
        id="air_freshener",
        sense=1,
        power=0,
        text="sprayed sweet smell into the air",
        qa_text="sprayed air freshener",
        useful_for=set(),
        tags={"smell"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Tess"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Finn", "Sam", "Eli", "Noah"]
HELPER_STYLES = ["steady", "jumpy", "canny", "kind"]


@dataclass
class StoryParams:
    mood: str
    source: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_style: str
    caretaker_type: str
    bravery: int
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


def introduce(world: World, mood: Mood, child: Entity, helper: Entity) -> None:
    world.say(mood.opener)
    world.say(
        f"{child.id} and {helper.id} stood outside the elevator with a grocery sack and a library book between them."
    )
    world.say(mood.rumor)
    world.say(
        f'{helper.id} leaned closer. "Do you think it is true?"'
    )


def approach(world: World, mood: Mood, child: Entity) -> None:
    world.say(
        f"{child.id} looked at the doors. {mood.shadow}"
    )
    if child.memes["bravery"] >= 5:
        world.say(
            f'"Maybe not," {child.id} said, trying to sound brave even while {child.pronoun("possessive")} heart beat faster.'
        )
    else:
        world.say(
            f'{child.id} swallowed hard. "I hope not," {child.pronoun()} whispered.'
        )


def enter_elevator(world: World, child: Entity, helper: Entity, source: Source) -> None:
    car = world.get("car")
    src = world.get("source")
    src.meters["active"] += 1
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The doors slid open, and they stepped into the elevator. At once they heard {source.sound}."
    )
    world.say(
        f"They also saw {source.image}."
    )
    if source.icky:
        world.say(
            f"There was {source.smell}, and the whole little car felt especially icky."
        )
    car.meters["moving"] += 1


def fright(world: World, child: Entity, helper: Entity) -> None:
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f'{helper.id} grabbed the railing. "{helper.id if helper.id.endswith("s") else helper.id}," {child.id} whispered, "something is in here."'
        )
    else:
        world.say(
            f"The sound was strange enough to make both children stand very still."
        )


def inspect(world: World, child: Entity, helper: Entity, source: Source) -> None:
    pred = predict_truth(world)
    world.facts["predicted_spooky"] = pred["spooky"]
    world.facts["predicted_icky"] = pred["icky"]
    world.facts["predicted_canny"] = pred["canny"]
    child.memes["bravery"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=False)
    if child.memes["canny"] >= THRESHOLD:
        world.say(
            f"But {child.id} took one careful breath and looked again in a canny way, not a panicky one."
        )
    else:
        world.say(
            f"But {child.id} took one careful breath and made {child.pronoun("possessive")}self look again."
        )
    world.say(
        f"Then {child.pronoun()} spotted {source.clue}."
    )
    if source.icky:
        world.say(
            f'"That is not a ghost," {child.id} said. "It is {source.material}, and {source.hazard}."'
        )
    else:
        world.say(
            f'"That is not a ghost," {child.id} said. "It is just {source.material}, and that is what is making the creepy sound."'
        )


def call_caretaker(world: World, child: Entity, helper: Entity, caretaker: Entity) -> None:
    helper.memes["trust"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} nodded and pressed the help button instead of guessing wildly."
    )
    world.say(
        f"In a moment, the building {caretaker.label_word} answered and told them to stay calm while {caretaker.pronoun()} came right over."
    )


def fix_problem(world: World, caretaker: Entity, source: Source, fix: Fix) -> None:
    world.get("source").meters["active"] = 0.0
    world.get("car").meters["spooky"] = 0.0
    world.get("car").meters["safe"] += 1
    body = fix.text
    world.say(
        f"When the doors opened on the lobby, the {caretaker.label_word} took one look and {body}."
    )
    world.say(
        f"It was such an effective fix that the spooky noise stopped at once."
    )


def lesson(world: World, child: Entity, helper: Entity, caretaker: Entity, source: Source) -> None:
    child.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'"You were brave to look carefully and ask for help," the {caretaker.label_word} said.'
    )
    if source.icky:
        world.say(
            f'"Old messes can smell awful and look strange in a small place like an elevator, but that still does not make them magic."'
        )
    else:
        world.say(
            f'"Funny sounds can feel scary in a small place like an elevator, but careful eyes usually find the real reason."'
        )


def ending(world: World, mood: Mood, child: Entity, helper: Entity) -> None:
    world.say(
        f"{child.id} and {helper.id} rode up again together, and this time the elevator only hummed and clicked like a machine should."
    )
    world.say(
        f"{mood.ending}"
    )


def tell(
    mood: Mood,
    source: Source,
    fix: Fix,
    *,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_gender: str,
    helper_style: str,
    caretaker_type: str,
    bravery: int,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["careful"],
        attrs={"helper_style": helper_style},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_style],
        attrs={},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        role="caretaker",
        label="the building grown-up",
        attrs={},
    ))
    car = world.add(Entity(
        id="car",
        kind="thing",
        type="elevator",
        label="elevator car",
        attrs={},
    ))
    src = world.add(Entity(
        id="source",
        kind="thing",
        type="cause",
        label=source.id,
        attrs={"icky": source.icky, "hazard": source.hazard},
    ))
    child.memes["bravery"] = float(bravery)
    child.memes["curiosity"] = 0.0
    child.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    helper.memes["curiosity"] = 0.0
    helper.memes["trust"] = 0.0
    car.meters["spooky"] = 0.0
    car.meters["safe"] = 0.0
    src.meters["active"] = 0.0

    introduce(world, mood, child, helper)
    approach(world, mood, child)

    world.para()
    enter_elevator(world, child, helper, source)
    fright(world, child, helper)

    world.para()
    if can_investigate(bravery, helper_style):
        inspect(world, child, helper, source)
        call_caretaker(world, child, helper, caretaker)
        world.para()
        fix_problem(world, caretaker, source, fix)
        lesson(world, child, helper, caretaker, source)
        world.para()
        ending(world, mood, child, helper)
        outcome = "solved"
    else:
        world.say(
            f"{child.id} wanted to be brave, but the creepy little noises felt too big all at once."
        )
        world.say(
            f"{helper.id} squeezed {child.pronoun('possessive')} hand, and together they hurried back out before the doors closed."
        )
        world.say(
            f"They told the {caretaker.label_word} what they had seen, and the grown-up checked the elevator right away."
        )
        world.para()
        fix_problem(world, caretaker, source, fix)
        lesson(world, child, helper, caretaker, source)
        world.para()
        world.say(
            f"Later, {child.id} was glad they had still done the brave thing by telling a grown-up, even before {child.pronoun()} understood the clue."
        )
        world.say(
            f"{mood.ending}"
        )
        outcome = "told_adult"

    world.facts.update(
        mood=mood,
        source_cfg=source,
        fix=fix,
        child=child,
        helper=helper,
        caretaker=caretaker,
        outcome=outcome,
        investigated=outcome == "solved",
        icky=source.icky,
        bravery=bravery,
        helper_style=helper_style,
    )
    return world


KNOWLEDGE = {
    "elevator": [
        (
            "What does an elevator do?",
            "An elevator carries people up and down between floors in a building. It is a small room that moves safely when it is working properly."
        )
    ],
    "spill": [
        (
            "Why can a spill on the floor be dangerous?",
            "A spill can make the floor slippery. In a small place like an elevator, that can make someone slip before they have room to steady themselves."
        )
    ],
    "ghost": [
        (
            "Why can ordinary things feel like a ghost story?",
            "Strange sounds, shadows, and smells can make your imagination race. When you look carefully, there is often a real everyday cause."
        )
    ],
    "effective": [
        (
            "What does effective mean?",
            "Effective means something works well and really solves the problem. An effective fix does more than just hide the trouble for a minute."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the wise thing even when you feel scared. Sometimes bravery means looking carefully, and sometimes it means calling a grown-up for help."
        )
    ],
    "clean": [
        (
            "Why is cleaning a dirty elevator important?",
            "Cleaning keeps the floor safer and nicer to use. It also removes bad smells and sticky messes that can scare or bother riders."
        )
    ],
    "balloon": [
        (
            "Why might a balloon make a squeaky sound?",
            "A foil balloon can rub against a wall or ceiling and squeak. In a quiet place, that sound can seem much stranger than it really is."
        )
    ],
    "vent": [
        (
            "What is a vent?",
            "A vent is an opening that lets air move in and out. If something catches in it, that thing can flutter or scrape and make a noise."
        )
    ],
}
KNOWLEDGE_ORDER = ["elevator", "ghost", "bravery", "spill", "clean", "balloon", "vent", "effective"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source_cfg"]
    return [
        'Write a short ghost-story-style tale for a 3-to-5-year-old set in an elevator that includes the words "canny", "icky", and "effective".',
        f"Tell a gentle spooky story where {child.id} hears a scary sound in an elevator, shows bravery, and learns there is an ordinary cause.",
        f"Write a story about an elevator rumor, a child who looks carefully, and a grown-up who fixes a {source.id.replace('_', ' ')} problem in an effective way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    caretaker = f["caretaker"]
    source = f["source_cfg"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id} riding an elevator and feeling spooked by a strange clue. A building {caretaker.label_word} helps them at the turning point."
        ),
        (
            "Why did the elevator seem haunted at first?",
            f"It seemed haunted because the children heard {source.sound} and saw {source.image}. In a small elevator, those clues felt bigger and stranger than they really were."
        ),
    ]
    if source.icky:
        qa.append((
            "What made the elevator feel especially icky?",
            f"The elevator smelled like {source.material} and had a messy clue inside. That gross smell and sticky-looking mess made the ghost rumor feel more real."
        ))
    if outcome == "solved":
        qa.append((
            f"How did {child.id} show bravery?",
            f"{child.id} felt scared but still looked carefully instead of only panicking. That brave pause helped {child.pronoun()} notice {source.clue} and understand the real problem."
        ))
    else:
        qa.append((
            f"How did {child.id} show bravery even before understanding everything?",
            f"{child.id} was too frightened to inspect the clue closely, but still told a grown-up right away. That was brave because asking for help was the safest choice."
        ))
    qa.append((
        "How was the problem fixed?",
        f"The building {caretaker.label_word} {fix.qa_text}. It was effective because it stopped the strange sound or mess instead of only covering it up."
    ))
    qa.append((
        "How did the story end?",
        f"In the end, the elevator felt ordinary again, and the children were calmer. The ending proves that careful bravery can turn a ghost story back into everyday life."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    source = f["source_cfg"]
    fix = f["fix"]
    tags = {"elevator", "ghost", "bravery", "effective"} | set(source.tags) | set(fix.tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mood="whispery",
        source="leaking_bag",
        fix="wipe_and_sign",
        child_name="Nora",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        helper_style="steady",
        caretaker_type="caretaker",
        bravery=5,
    ),
    StoryParams(
        mood="stormy",
        source="vent_string",
        fix="remove_ribbon",
        child_name="Tom",
        child_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        helper_style="canny",
        caretaker_type="superintendent",
        bravery=4,
    ),
    StoryParams(
        mood="midnightish",
        source="balloon",
        fix="lower_balloon",
        child_name="Ava",
        child_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        helper_style="kind",
        caretaker_type="caretaker",
        bravery=3,
    ),
    StoryParams(
        mood="whispery",
        source="mop_smear",
        fix="wipe_and_sign",
        child_name="Finn",
        child_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        helper_style="jumpy",
        caretaker_type="superintendent",
        bravery=5,
    ),
]

ASP_RULES = r"""
valid(M,S,F) :- mood(M), source(S), fix(F), needs_fix(S,N), useful_for(F,N), sense(F,Se), sense_min(Min), Se >= Min.

bonus(1) :- helper_style(steady).
bonus(1) :- helper_style(canny).
bonus(0) :- not helper_style(steady), not helper_style(canny).

investigates :- bravery(B), bonus(X), B + X >= 5.
solved_enough :- chosen_source(S), chosen_fix(F), severity(S,V), power(F,P), P >= V.

outcome(solved) :- investigates, solved_enough.
outcome(told_adult) :- not investigates, solved_enough.
:- chosen_source(S), chosen_fix(F), severity(S,V), power(F,P), P < V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("needs_fix", source_id, source.needs_fix))
        lines.append(asp.fact("severity", source_id, source.severity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
        for need in sorted(fix.useful_for):
            lines.append(asp.fact("useful_for", fix_id, need))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_fix", params.fix),
        asp.fact("bravery", params.bravery),
        asp.fact("helper_style", params.helper_style),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    if not valid_fix(SOURCES[params.source], FIXES[params.fix]):
        return "?"
    if not enough_fix(SOURCES[params.source], FIXES[params.fix]):
        return "?"
    return "solved" if can_investigate(params.bravery, params.helper_style) else "told_adult"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed for smoke seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story-style elevator world with bravery, canny observation, and an effective fix."
    )
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--caretaker", choices=["caretaker", "superintendent"])
    ap.add_argument("--bravery", type=int, choices=[3, 4, 5, 6])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.fix:
        source = SOURCES[args.source]
        fix = FIXES[args.fix]
        if not valid_fix(source, fix):
            raise StoryError(explain_rejection(source, fix))
        if not enough_fix(source, fix):
            raise StoryError(
                f"(No story: {args.fix} is not strong enough to fully solve the {args.source} problem.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.mood is None or combo[0] == args.mood)
        and (args.source is None or combo[1] == args.source)
        and (args.fix is None or combo[2] == args.fix)
        and enough_fix(SOURCES[combo[1]], FIXES[combo[2]])
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mood_id, source_id, fix_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    helper_style = rng.choice(HELPER_STYLES)
    caretaker_type = args.caretaker or rng.choice(["caretaker", "superintendent"])
    bravery = args.bravery if args.bravery is not None else rng.choice([3, 4, 5, 6])
    return StoryParams(
        mood=mood_id,
        source=source_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_style=helper_style,
        caretaker_type=caretaker_type,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    for key, registry in (("mood", MOODS), ("source", SOURCES), ("fix", FIXES)):
        value = getattr(params, key)
        if value not in registry:
            raise StoryError(f"(Invalid {key}: {value})")
    if params.caretaker_type not in {"caretaker", "superintendent"}:
        raise StoryError(f"(Invalid caretaker type: {params.caretaker_type})")
    if params.bravery not in {3, 4, 5, 6}:
        raise StoryError(f"(Invalid bravery: {params.bravery})")
    source = SOURCES[params.source]
    fix = FIXES[params.fix]
    if not valid_fix(source, fix):
        raise StoryError(explain_rejection(source, fix))
    if not enough_fix(source, fix):
        raise StoryError(f"(No story: {params.fix} is not strong enough to solve {params.source}.)")

    world = tell(
        MOODS[params.mood],
        source,
        fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_style=params.helper_style,
        caretaker_type=params.caretaker_type,
        bravery=params.bravery,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mood, source, fix) combos:\n")
        for mood_id, source_id, fix_id in combos:
            print(f"  {mood_id:11} {source_id:12} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.source} in elevator ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
