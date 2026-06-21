#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py
===============================================================================

A standalone story world about a child at a busy street crossing who imagines
the curb as the edge of a space mission. A distraction tugs hard, but a crossing
drill in rhyme returns inside the child's thoughts just in time.

The domain is intentionally small and constraint-checked:

- A crossing has physical features: guard, button, lane complexity.
- A lost item can drift only so far or fast.
- A helper method is only valid when it genuinely fits the crossing and the item.
- The turn is state-driven: sometimes the child stops themself after the rhyme
  echoes in an inner monologue; otherwise the grown-up or crossing guard steps in
  and stops the unsafe move.
- Every ending proves what changed: the child does not just hear the drill, but
  uses it at the crossing.

Run it
------
    python storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py --crossing school_gate --item ball --helper guard_whistle
    python storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py --crossing downtown_lights --helper guard_whistle
    python storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/drill_busy_street_crossing_rhyme_inner_monologue.py --verify
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
MEMORY_BONUS = 2
SENSE_MIN = 2
DISCIPLINE_POINTS = {
    "careful": 3,
    "patient": 3,
    "thoughtful": 3,
    "curious": 2,
    "brave": 2,
    "dreamy": 1,
}
CAUTIOUS_TRAITS = {"careful", "patient", "thoughtful"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Crossing:
    id: str
    label: str
    scene: str
    lanes: int
    has_guard: bool
    has_button: bool
    countdown: bool
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
class LostItem:
    id: str
    label: str
    phrase: str
    motion: str
    drift: int
    sound: str
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
    label: str
    sense: int
    control: int
    need_guard: bool = False
    need_button: bool = False
    max_drift: int = 99
    action_text: str = ""
    qa_text: str = ""
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    street = world.get("street")
    helper = world.get("adult")
    if child.meters["off_curb"] < THRESHOLD or street.meters["traffic"] < THRESHOLD:
        return out
    sig = ("danger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    helper.memes["alarm"] += 1
    street.meters["danger"] += 1
    out.append("__danger__")
    return out


def _r_freeze(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["reciting"] < THRESHOLD or child.meters["off_curb"] >= THRESHOLD:
        return out
    sig = ("freeze",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["frozen_feet"] += 1
    child.memes["caution"] += 1
    out.append("__freeze__")
    return out


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="freeze", tag="self_control", apply=_r_freeze),
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


def helper_available(crossing: Crossing, helper: Helper) -> bool:
    if helper.need_guard and not crossing.has_guard:
        return False
    if helper.need_button and not crossing.has_button:
        return False
    return True


def helper_effective(crossing: Crossing, item: LostItem, helper: Helper) -> bool:
    return helper.control >= crossing.lanes and item.drift <= helper.max_drift


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crossing_id, crossing in CROSSINGS.items():
        for item_id, item in ITEMS.items():
            for helper_id, helper in HELPERS.items():
                if helper.sense < SENSE_MIN:
                    continue
                if helper_available(crossing, helper) and helper_effective(crossing, item, helper):
                    combos.append((crossing_id, item_id, helper_id))
    return combos


def explain_rejection(crossing: Crossing, item: LostItem, helper: Helper) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: helper '{helper.id}' scores below the common-sense floor "
            f"for this world. Pick a calmer, safer method.)"
        )
    if helper.need_guard and not crossing.has_guard:
        return (
            f"(No story: {crossing.label} has no crossing guard, so {helper.label} "
            f"is not available there.)"
        )
    if helper.need_button and not crossing.has_button:
        return (
            f"(No story: {crossing.label} has no walk button, so {helper.label} "
            f"does not fit this crossing.)"
        )
    if helper.control < crossing.lanes:
        return (
            f"(No story: {helper.label} is too weak for {crossing.label}. This "
            f"crossing is too busy for that plan to feel believable.)"
        )
    if item.drift > helper.max_drift:
        return (
            f"(No story: {item.phrase} skitters too far for {helper.label}. Choose "
            f"a stronger helper or a gentler distraction.)"
        )
    return "(No story: this combination is not reasonable.)"


def would_self_stop(crossing: Crossing, item: LostItem, trait: str) -> bool:
    discipline = DISCIPLINE_POINTS[trait]
    return discipline + MEMORY_BONUS >= crossing.lanes + item.drift


def outcome_of(params: "StoryParams") -> str:
    crossing = CROSSINGS[params.crossing]
    item = ITEMS[params.item]
    helper = HELPERS[params.helper]
    if not (helper_available(crossing, helper) and helper_effective(crossing, item, helper) and helper.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(crossing, item, helper))
    return "self_stop" if would_self_stop(crossing, item, params.trait) else "helper_stop"


def predict_step(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["off_curb"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("street").meters["danger"],
        "fear": sim.get("child").memes["fear"],
    }


def mission_intro(world: World, child: Entity, adult: Entity, crossing: Crossing) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} walked with {adult.label_word} toward {crossing.scene}. "
        f"To {child.pronoun('object')}, the painted stripes looked like a silver "
        f"space bridge laid across a river of wheels."
    )
    detail = "A crossing guard stood nearby with a bright stop sign." if crossing.has_guard else \
        "The signal clicked above them while cars brushed the air with a busy hush."
    world.say(detail)


def teach_drill(world: World, child: Entity, adult: Entity, crossing: Crossing) -> None:
    child.memes["memory"] += MEMORY_BONUS
    world.facts["drill_lines"] = [
        "Boots stay here, near not far,",
        "Eyes count every rushing car,",
        "Ears hear brakes from near and far,",
        "Walk on white, my little star.",
    ]
    line1, line2, line3, line4 = world.facts["drill_lines"]
    who = adult.label_word.capitalize()
    world.say(
        f'At the curb, {who} whispered their crossing drill in a sing-song rhyme: '
        f'"{line1} {line2} {line3} {line4}"'
    )
    if crossing.countdown:
        world.say("The red hand glowed, so the mission was still waiting for launch.")


def tempt(world: World, child: Entity, item: LostItem) -> None:
    child.memes["urge"] += 1
    world.say(
        f"Just then, {item.phrase} {item.motion}. {item.sound} It looked as if a tiny "
        f"runaway probe had escaped the mission."
    )


def inner_monologue(world: World, child: Entity, item: LostItem) -> None:
    pred = predict_step(world)
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["thinking"] += 1
    world.say(
        f'Inside, {child.id} heard a fast little thought: "I can grab it in one zip."'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(
            f'Then another thought answered back: "No, that street is full of roaring '
            f'rockets. The drill is for right now."'
        )


def recite_and_freeze(world: World, child: Entity) -> None:
    child.memes["reciting"] += 1
    propagate(world, narrate=False)
    lines = world.facts["drill_lines"]
    world.say(
        f'{child.id} pressed {child.pronoun("possessive")} toes to the curb and sang '
        f'very softly inside {child.pronoun("possessive")} own head: "{lines[0]} '
        f'{lines[1]}"'
    )
    world.say(
        f'The rest of the rhyme followed like a helper star: "{lines[2]} {lines[3]}"'
    )


def lunge(world: World, child: Entity, item: LostItem) -> None:
    child.meters["off_curb"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id}'s body leaned after {item.label}, and one sneaker slipped off the "
        f"safe line at the curb."
    )


def helper_intervenes(world: World, child: Entity, adult: Entity, helper: Helper) -> None:
    child.meters["off_curb"] = 0.0
    child.memes["reciting"] += 1
    child.memes["fear"] += 1
    child.memes["relief"] += 1
    adult.memes["care"] += 1
    world.say(
        f"{adult.label_word.capitalize()} moved in a flash and {helper.action_text}."
    )
    world.say(
        f'"Freeze, space boots," {adult.pronoun()} said gently. "The drill comes before '
        f'the dash."'
    )


def safe_retrieval(world: World, child: Entity, adult: Entity, crossing: Crossing,
                   item: LostItem, helper: Helper, outcome: str) -> None:
    signal = "the white walking person blinked on" if crossing.countdown else "the traffic finally held still"
    world.get("street").meters["traffic"] = 0.0
    world.get("street").meters["safe_window"] += 1
    child.memes["trust"] += 1
    child.memes["pride"] += 1
    child.memes["fear"] = 0.0
    world.facts["item_recovered"] = True
    if outcome == "self_stop":
        who = "the crossing guard" if helper.need_guard else adult.label_word
        extra = "raised the sign and " if helper.need_guard else ""
        world.say(
            f"When {signal}, {who} {extra}reached safely for {item.label} instead."
        )
    else:
        world.say(
            f"A moment later, when {signal}, {adult.label_word} kept one calm hand on "
            f"{child.id} and made sure {item.label} came back the safe way."
        )


def cross_and_end(world: World, child: Entity, adult: Entity, crossing: Crossing,
                  item: LostItem, outcome: str) -> None:
    child.meters["crossed"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"Then they crossed together, stripe by stripe, while engines waited like big "
        f"metal beasts at their red light."
    )
    end_line = (
        f'{child.id} looked down at the bright crosswalk and thought, "A real space hero '
        f'does the drill before the thrill."'
    )
    world.say(end_line)
    if outcome == "self_stop":
        world.say(
            f"On the far curb, {child.id} tucked {item.label} close and smiled. The busy "
            f"street no longer felt like something to race, but something to read carefully."
        )
    else:
        world.say(
            f"On the far curb, {child.id} squeezed {adult.label_word}'s hand, took a brave "
            f"breath, and repeated the rhyme out loud. This time the mission ended with safe "
            f"feet, not fast feet."
        )


def tell(crossing: Crossing, item: LostItem, helper: Helper, *,
         name: str = "Nova", gender: str = "girl", parent: str = "mother",
         trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=gender,
        label=name,
        role="child",
        traits=[trait],
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=parent,
        label="the adult",
        role="adult",
    ))
    street = world.add(Entity(
        id="street",
        type="street",
        label="the street",
    ))
    thing = world.add(Entity(
        id="item",
        type="object",
        label=item.label,
    ))

    child.meters["off_curb"] = 0.0
    child.meters["frozen_feet"] = 0.0
    child.meters["crossed"] = 0.0
    child.memes["urge"] = 0.0
    child.memes["reciting"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["confidence"] = 0.0
    adult.memes["alarm"] = 0.0
    adult.memes["care"] = 0.0
    street.meters["traffic"] = 1.0
    street.meters["danger"] = 0.0
    street.meters["safe_window"] = 0.0

    world.facts.update(
        child=child,
        adult=adult,
        street=street,
        item_cfg=item,
        crossing=crossing,
        helper=helper,
        trait=trait,
        item_recovered=False,
    )

    mission_intro(world, child, adult, crossing)
    teach_drill(world, child, adult, crossing)

    world.para()
    tempt(world, child, item)
    inner_monologue(world, child, item)

    outcome = "self_stop" if would_self_stop(crossing, item, trait) else "helper_stop"
    world.facts["outcome"] = outcome

    if outcome == "self_stop":
        recite_and_freeze(world, child)
        world.say(
            f"{child.label} kept both feet planted on the launchpad curb even while "
            f"{item.label} tugged at {child.pronoun('possessive')} eyes."
        )
    else:
        lunge(world, child, item)
        helper_intervenes(world, child, adult, helper)

    world.para()
    safe_retrieval(world, child, adult, crossing, item, helper, outcome)
    cross_and_end(world, child, adult, crossing, item, outcome)

    world.facts["child_name"] = name
    world.facts["adult_word"] = adult.label_word
    world.facts["danger_seen"] = world.facts.get("predicted_danger", 0) >= THRESHOLD
    world.facts["used_drill"] = child.memes["reciting"] >= THRESHOLD
    world.facts["crossed_safely"] = child.meters["crossed"] >= THRESHOLD
    world.facts["helper_step"] = outcome == "helper_stop"
    world.facts["self_step"] = outcome == "self_stop"
    world.facts["drill_word_present"] = True
    return world


CROSSINGS = {
    "school_gate": Crossing(
        id="school_gate",
        label="the school crossing",
        scene="the busy street crossing by the school gate",
        lanes=2,
        has_guard=True,
        has_button=False,
        countdown=False,
        tags={"crosswalk", "guard", "traffic"},
    ),
    "downtown_lights": Crossing(
        id="downtown_lights",
        label="the downtown crossing",
        scene="a bright downtown crossing with a beeping signal",
        lanes=3,
        has_guard=False,
        has_button=True,
        countdown=True,
        tags={"crosswalk", "signal", "traffic"},
    ),
    "market_corner": Crossing(
        id="market_corner",
        label="the market corner crossing",
        scene="the noisy crossing by the market corner",
        lanes=2,
        has_guard=False,
        has_button=True,
        countdown=True,
        tags={"crosswalk", "signal", "traffic"},
    ),
}

ITEMS = {
    "paper_glider": LostItem(
        id="paper_glider",
        label="the paper glider",
        phrase="a folded paper glider",
        motion="fluttered from Nova's hand and skipped to the edge of the stripes",
        drift=1,
        sound="Flit-flit",
        tags={"paper", "wind"},
    ),
    "toy_rocket": LostItem(
        id="toy_rocket",
        label="the toy rocket",
        phrase="a tiny toy rocket",
        motion="skittered from the curb toward the first lane",
        drift=2,
        sound="Tik-tik",
        tags={"toy", "wheels"},
    ),
    "ball": LostItem(
        id="ball",
        label="the red ball",
        phrase="a red ball",
        motion="bounced away and rolled deep toward the busy lane",
        drift=3,
        sound="Bop-bop",
        tags={"ball", "rolling"},
    ),
}

HELPERS = {
    "hand_hold": Helper(
        id="hand_hold",
        label="a steady hand-hold plan",
        sense=3,
        control=3,
        need_guard=False,
        need_button=False,
        max_drift=3,
        action_text="caught the back of the coat and held that eager hand at the curb",
        qa_text="held the child back at the curb and waited for a safe moment",
        tags={"adult_help", "wait"},
    ),
    "guard_whistle": Helper(
        id="guard_whistle",
        label="the crossing guard's whistle",
        sense=3,
        control=3,
        need_guard=True,
        need_button=False,
        max_drift=3,
        action_text="lifted the bright sign while the crossing guard gave one sharp whistle",
        qa_text="used the crossing guard's stop sign and whistle to stop the child and the traffic",
        tags={"guard", "wait"},
    ),
    "button_wait": Helper(
        id="button_wait",
        label="the walk-button wait",
        sense=2,
        control=2,
        need_guard=False,
        need_button=True,
        max_drift=2,
        action_text="pointed to the walk button and kept the mission parked at the curb",
        qa_text="pressed the walk button and made the child wait instead of dashing",
        tags={"signal", "wait"},
    ),
    "call_from_curb": Helper(
        id="call_from_curb",
        label="calling from the curb",
        sense=1,
        control=1,
        need_guard=False,
        need_button=False,
        max_drift=1,
        action_text="called to the item from the curb",
        qa_text="called from the curb",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Tess", "Zuri", "Ayla", "Ivy", "Nina"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Orion", "Jude", "Eli", "Noah", "Theo"]
TRAITS = ["careful", "patient", "thoughtful", "curious", "brave", "dreamy"]


@dataclass
class StoryParams:
    crossing: str
    item: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "crosswalk": [
        (
            "What is a crosswalk?",
            "A crosswalk is a marked place where people walk across a street. The paint and signals help drivers know to stop."
        )
    ],
    "traffic": [
        (
            "Why is a busy street dangerous?",
            "A busy street has many moving cars, bikes, or buses, and they need time to stop. That is why people should wait at the curb and cross carefully."
        )
    ],
    "signal": [
        (
            "What does the walk signal mean?",
            "The walk signal shows when it is a safe time to start crossing. You still look and listen, because safe crossing uses both the signal and your attention."
        )
    ],
    "guard": [
        (
            "What does a crossing guard do?",
            "A crossing guard helps people cross safely by watching traffic and telling cars when to stop. They help children wait for the right moment."
        )
    ],
    "wait": [
        (
            "Why is waiting important before crossing a street?",
            "Waiting gives your eyes and ears time to check what the traffic is doing. A fast choice can be unsafe, but a calm choice can keep everyone safe."
        )
    ],
    "ball": [
        (
            "Why should you not chase a ball into the street?",
            "A ball can roll into traffic much faster than you can think. If you chase it, a driver may not have enough time to stop."
        )
    ],
    "paper": [
        (
            "Why can wind be tricky near a street?",
            "Wind can push light things like paper where you did not expect. That is why you should keep your feet safe even if something blows away."
        )
    ],
    "toy": [
        (
            "Why is it safer to ask for help if a toy rolls away?",
            "A grown-up can help decide when it is safe to get it or whether to leave it alone. Toys can be replaced, but people cannot."
        )
    ],
}
KNOWLEDGE_ORDER = ["crosswalk", "traffic", "signal", "guard", "wait", "ball", "paper", "toy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    crossing = f["crossing"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    if outcome == "self_stop":
        return [
            f'Write a short story for a 3-to-5-year-old set at {crossing.label} that includes the word "drill" and uses rhyme plus inner monologue.',
            f"Tell a space-adventure style story where {child.label} wants to chase {item.label}, but a crossing rhyme plays inside {child.pronoun('possessive')} thoughts and helps {child.pronoun('object')} stop.",
            f"Write a gentle story in which a child treats a busy crosswalk like a space mission and proves the safety drill worked before crossing."
        ]
    return [
        f'Write a short story for a 3-to-5-year-old set at {crossing.label} that includes the word "drill" and uses rhyme plus inner monologue.',
        f"Tell a space-adventure style story where {child.label} almost darts after {item.label}, but a grown-up steps in and reminds {child.pronoun('object')} of the crossing drill.",
        f"Write a simple traffic-safety story with a rhyming curb drill, a tense moment at a busy crossing, and a safe ending that shows what the child learned."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    crossing = f["crossing"]
    item = f["item_cfg"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who was walking with {adult.label_word} at {crossing.label}. The child imagined the crosswalk like a space bridge."
        ),
        (
            "What was the crossing drill?",
            f'The drill was a rhyming rule about keeping feet at the curb, watching cars, listening, and walking only at the safe moment. The rhyme helped the child remember what to do under pressure.'
        ),
        (
            f"Why was {item.label} a problem?",
            f"{item.label.capitalize()} moved toward the street and made {child.label} want to chase it. That tug was dangerous because the crossing was still busy."
        ),
    ]
    if outcome == "self_stop":
        qa.append(
            (
                f"How did {child.label} stop {child.pronoun('object')}self from running after {item.label}?",
                f"{child.label} heard the rhyme inside {child.pronoun('possessive')} own thoughts and pressed both feet to the curb. The inner monologue turned the safety drill into action before any step went into the street."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They waited for a safe moment, got {item.label} back the right way, and crossed together. The ending shows that {child.label} did not just hear the drill before, but used it at the busy street."
            )
        )
    else:
        qa.append(
            (
                f"What did {adult.label_word} do when {child.label} started to move?",
                f"{adult.label_word.capitalize()} {helper.qa_text}. That quick help stopped an unsafe step before traffic could become a real danger."
            )
        )
        qa.append(
            (
                f"Did {child.label} still learn the drill?",
                f"Yes. After the grown-up stopped the dash, {child.label} crossed safely and repeated the rhyme again. The lesson became stronger because it was tied to the scary moment at the curb."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["crossing"].tags) | set(f["helper"].tags)
    item = f["item_cfg"]
    if "ball" in item.tags:
        tags.add("ball")
    if "paper" in item.tags or "wind" in item.tags:
        tags.add("paper")
    if "toy" in item.tags or "wheels" in item.tags:
        tags.add("toy")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts.outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crossing="school_gate",
        item="ball",
        helper="guard_whistle",
        name="Nova",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        crossing="downtown_lights",
        item="toy_rocket",
        helper="hand_hold",
        name="Orion",
        gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        crossing="market_corner",
        item="paper_glider",
        helper="button_wait",
        name="Luna",
        gender="girl",
        parent="mother",
        trait="patient",
    ),
    StoryParams(
        crossing="market_corner",
        item="toy_rocket",
        helper="hand_hold",
        name="Milo",
        gender="boy",
        parent="father",
        trait="dreamy",
    ),
    StoryParams(
        crossing="school_gate",
        item="paper_glider",
        helper="guard_whistle",
        name="Tess",
        gender="girl",
        parent="mother",
        trait="thoughtful",
    ),
]


ASP_RULES = r"""
% --- validity --------------------------------------------------------------
available(H, C) :- helper(H), crossing(C), not need_guard(H), not need_button(H).
available(H, C) :- helper(H), crossing(C), need_guard(H), has_guard(C).
available(H, C) :- helper(H), crossing(C), need_button(H), has_button(C), not need_guard(H).
available(H, C) :- helper(H), crossing(C), need_guard(H), has_guard(C), need_button(H), has_button(C).

effective(H, C, I) :- helper(H), crossing(C), item(I),
                      control(H, HC), lanes(C, CL), HC >= CL,
                      max_drift(H, MD), drift(I, ID), ID =< MD.

valid(C, I, H) :- crossing(C), item(I), helper(H), sense(H, S), sense_min(M), S >= M,
                  available(H, C), effective(H, C, I).

% --- outcome ---------------------------------------------------------------
discipline_now(P) :- chosen_trait(T), trait_points(T, P).
threshold(V) :- chosen_crossing(C), chosen_item(I), lanes(C, CL), drift(I, ID), V = CL + ID.
self_stop :- discipline_now(P), memory_bonus(MB), threshold(V), P + MB >= V.
outcome(self_stop) :- self_stop.
outcome(helper_stop) :- not self_stop.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, crossing in CROSSINGS.items():
        lines.append(asp.fact("crossing", cid))
        lines.append(asp.fact("lanes", cid, crossing.lanes))
        if crossing.has_guard:
            lines.append(asp.fact("has_guard", cid))
        if crossing.has_button:
            lines.append(asp.fact("has_button", cid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("drift", iid, item.drift))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("control", hid, helper.control))
        lines.append(asp.fact("max_drift", hid, helper.max_drift))
        if helper.need_guard:
            lines.append(asp.fact("need_guard", hid))
        if helper.need_button:
            lines.append(asp.fact("need_button", hid))
    for trait, pts in DISCIPLINE_POINTS.items():
        lines.append(asp.fact("trait_points", trait, pts))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("memory_bonus", MEMORY_BONUS))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_crossing", params.crossing),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid_combos parity holds ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
        except StoryError:
            bad += 1
            continue
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} clingo={cl}")
    if bad == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke, trace=False, qa=True, header="### smoke")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    else:
        print("OK: smoke test generate/emit passed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child at a busy street crossing uses a rhyming drill like a space mission checklist."
    )
    ap.add_argument("--crossing", choices=sorted(CROSSINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(
            f"(No story: helper '{args.helper}' is intentionally below the common-sense floor for this world.)"
        )

    if args.crossing and args.item and args.helper:
        crossing = CROSSINGS[args.crossing]
        item = ITEMS[args.item]
        helper = HELPERS[args.helper]
        if not (helper_available(crossing, helper) and helper_effective(crossing, item, helper) and helper.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(crossing, item, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.crossing is None or combo[0] == args.crossing)
        and (args.item is None or combo[1] == args.item)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crossing_id, item_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        crossing=crossing_id,
        item=item_id,
        helper=helper_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crossing not in CROSSINGS:
        raise StoryError(f"(Unknown crossing: {params.crossing})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")
    if params.trait not in DISCIPLINE_POINTS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    crossing = CROSSINGS[params.crossing]
    item = ITEMS[params.item]
    helper = HELPERS[params.helper]
    if not (helper_available(crossing, helper) and helper_effective(crossing, item, helper) and helper.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(crossing, item, helper))

    world = tell(
        crossing=crossing,
        item=item,
        helper=helper,
        name=params.name,
        gender=params.gender,
        parent=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (crossing, item, helper) combos:\n")
        for crossing, item, helper in combos:
            print(f"  {crossing:16} {item:12} {helper}")
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
            header = f"### {p.name}: {p.item} at {p.crossing} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
