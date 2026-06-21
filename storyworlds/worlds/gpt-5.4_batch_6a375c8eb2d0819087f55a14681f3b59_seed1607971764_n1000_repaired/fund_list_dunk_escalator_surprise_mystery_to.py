#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py
===========================================================================

A standalone story world about two children on an escalator adventure with a
small community fund, a missing item, a mystery to solve, and a lesson about
sharing and asking for help.

The seed called for these words and features:
- words: "fund", "list", "dunk"
- setting: escalator
- features: Surprise, Mystery to Solve, Sharing
- style: Pirate Tale

This world rebuilds that premise as a simulation rather than a frozen template:
two children are on a pretend quest around an escalator, carrying a small fund
envelope and a list. A shiny donation coin seems to go missing. One child is
tempted to solve the mystery by reaching into a dangerous moving place. A calm
grown-up uses the right method instead, the mystery is solved from world state,
and the ending image proves what changed: the children share what they have and
finish the mission safely.

Run it
------
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py --theme pirates --missing coin --risky reach_gap
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py --missing ribbon
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py --risky jump_back
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fund_list_dunk_escalator_surprise_mystery_to.py --verify
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
CAREFUL_TRAITS = {"careful", "cautious", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    small: bool = False
    # physical + emotional
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
        return {"mother": "mom", "father": "dad", "clerk": "clerk", "guard": "guard"}.get(
            self.type, self.type
        )
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    mission: str
    stair_word: str
    send_off: str
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
class MissingThing:
    id: str
    label: str
    phrase: str
    shiny: str
    can_fall: bool = True
    can_hide_on_list: bool = False
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
class RiskyMove:
    id: str
    sense: int
    danger: int
    text: str
    warning: str
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
class SafeResponse:
    id: str
    sense: int
    power: int
    text: str
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


def _r_escalator_danger(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("attempted_risk") != "yes":
        return out
    if world.facts.get("escalator_running") != "yes":
        return out
    sig = ("danger", world.facts.get("risky_id", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    if "escalator" in world.entities:
        world.get("escalator").meters["danger"] += 1
    out.append("__danger__")
    return out


def _r_found_where(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") != "yes":
        return out
    place = world.facts.get("found_place")
    if not place:
        return out
    sig = ("found", place)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    found = world.get("missing")
    found.meters["found"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="escalator_danger", tag="physical", apply=_r_escalator_danger),
    Rule(name="found_where", tag="mystery", apply=_r_found_where),
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


def hazard_possible(missing: MissingThing, risky: RiskyMove) -> bool:
    return missing.can_fall and risky.danger > 0


def sensible_responses() -> list[SafeResponse]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> SafeResponse:
    return max(RESPONSES.values(), key=lambda r: (r.sense, r.power))


def mystery_place(missing: MissingThing, risky: RiskyMove) -> str:
    if missing.can_hide_on_list and risky.id == "dunk_hand":
        return "list_back"
    if risky.id == "reach_gap":
        return "comb_plate"
    if risky.id == "jump_back":
        return "step_groove"
    return "pocket_fold"


def is_contained(response: SafeResponse, risky: RiskyMove) -> bool:
    return response.power >= risky.danger


def would_listen(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    strong = trait in CAREFUL_TRAITS
    older = relation == "siblings" and cautioner_age > instigator_age
    return older and strong


def predict_trouble(world: World, missing_id: str, risky_id: str) -> dict:
    sim = world.copy()
    sim.facts["attempted_risk"] = "yes"
    sim.facts["risky_id"] = risky_id
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("escalator").meters["danger"],
        "found_place": mystery_place(MISSING[missing_id], RISKY[risky_id]),
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the mall escalator into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{t1} {a.id} and {t2} {b.id}!" {a.id} shouted. "Let\'s finish {theme.mission}!"'
    )


def mission_setup(world: World, a: Entity, b: Entity, missing: MissingThing) -> None:
    for kid in (a, b):
        kid.meters["carrying"] += 1
    world.say(
        f"They carried a paper fund envelope for the animal shelter and a crinkly list of little jobs. "
        f"At the top of the list, one line said to add {missing.phrase} before they reached the upstairs table."
    )
    world.say(
        f"{b.id} patted the envelope, then counted again. {missing.shiny.capitalize()} was gone."
    )


def wonder(world: World, b: Entity, missing: MissingThing) -> None:
    b.memes["curiosity"] += 1
    world.say(
        f'"Wait," {b.id} said. "Where did {missing.phrase} go?"'
    )
    world.say(
        "For one puzzled second, the moving steps hummed beneath them like a machine with a secret."
    )


def tempt(world: World, a: Entity, risky: RiskyMove, missing: MissingThing) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} leaned forward. "{risky.text} Maybe {missing.phrase} slipped down there."'
    )


def warn(world: World, b: Entity, a: Entity, risky: RiskyMove, helper: Entity,
         missing: MissingThing) -> None:
    pred = predict_trouble(world, missing.id, risky.id)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_place"] = pred["found_place"]
    extra = ""
    if b.memes["caution"] >= 4:
        extra = f" {b.pronoun().capitalize()} gripped the rail and looked sure."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{risky.warning} We should ask the {helper.label_word} to help instead."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, risky: RiskyMove) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"It will be fast," {a.id} said, and because {a.id} was {b.pronoun("possessive")} {rel}, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"It will be fast," {a.id} said, and moved before {b.id} could stop {a.pronoun("object")}.')


def back_down(world: World, a: Entity, b: Entity, helper: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravado"] = 0.0
    world.say(
        f'{a.id} looked at the moving teeth at the end of the step, swallowed, and stepped back. '
        f'"You\'re right," {a.pronoun()} said. "Let\'s ask the {helper.label_word}."'
    )


def attempt_risk(world: World, risky: RiskyMove) -> None:
    world.facts["attempted_risk"] = "yes"
    world.facts["risky_id"] = risky.id
    propagate(world, narrate=False)


def alarm(world: World, b: Entity, helper: Entity) -> None:
    world.say(f'"Please help!" {b.id} called. "Something tiny fell near the escalator!"')
    world.say(f'The {helper.label_word} heard at once and hurried over.')


def solve(world: World, helper: Entity, response: SafeResponse,
          risky: RiskyMove, missing: MissingThing) -> None:
    place = mystery_place(missing, risky)
    world.facts["solved"] = "yes"
    world.facts["found_place"] = place
    world.facts["escalator_running"] = "no"
    if "escalator" in world.entities:
        world.get("escalator").meters["running"] = 0.0
        world.get("escalator").meters["danger"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"The {helper.label_word} {response.text}"
    )
    if place == "comb_plate":
        world.say(
            f"Then {helper.pronoun()} pointed to a bright dot by the comb plate. {missing.shiny.capitalize()} had been waiting there the whole time."
        )
    elif place == "step_groove":
        world.say(
            f"Then {helper.pronoun()} lifted {helper.pronoun('possessive')} chin and showed them a little groove in one step. {missing.shiny.capitalize()} was tucked there."
        )
    elif place == "list_back":
        world.say(
            f"Then {helper.pronoun()} turned over the paper list. {missing.shiny.capitalize()} was stuck to the back by a stripe of old tape."
        )
    else:
        world.say(
            f"Then {helper.pronoun()} opened the folded side of the envelope. {missing.shiny.capitalize()} had slid into the pocket fold."
        )


def lesson(world: World, helper: Entity, a: Entity, b: Entity, risky: RiskyMove) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f'Then the {helper.label_word} knelt beside them. "I am glad you called me," {helper.pronoun()} said softly. '
        f'"Escalators are for riding, not for hands and games. {risky.warning}"'
    )


def surprise_and_share(world: World, helper: Entity, a: Entity, b: Entity,
                       missing: MissingThing, treat: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["sharing"] += 1
    world.say(
        f"Upstairs, they slipped {missing.phrase} into the shelter fund and checked the list again, this time together."
    )
    world.say(
        f"At the bottom of the page, a line they had missed made them blink: Surprise reward — one {treat} to share after the last job."
    )
    world.say(
        f"The {helper.label_word} smiled and bought one. {a.id} broke it neatly in half, gave the bigger piece to {b.id}, and {b.id} laughed."
    )
    world.say(
        f"Then the two brave riders stepped onto the escalator side by side, held the rail the proper way, and {a.id} said, "
        f'"Best mates share the treasure."'
    )


def tell(theme: Theme, missing: MissingThing, risky: RiskyMove, response: SafeResponse,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         trait: str = "careful", helper_type: str = "clerk",
         relation: str = "siblings", instigator_age: int = 6, cautioner_age: int = 5,
         treat: str = "blueberry muffin") -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label=helper_type,
        )
    )
    escalator = world.add(
        Entity(
            id="escalator",
            type="escalator",
            label="the escalator",
        )
    )
    missing_ent = world.add(
        Entity(
            id="missing",
            type="thing",
            label=missing.label,
            movable=True,
            small=True,
        )
    )
    list_ent = world.add(
        Entity(
            id="list",
            type="list",
            label="list",
            movable=True,
        )
    )
    fund_ent = world.add(
        Entity(
            id="fund",
            type="envelope",
            label="fund envelope",
            movable=True,
        )
    )

    escalator.meters["running"] = 1.0
    a.memes["bravery"] = 5.0
    b.memes["caution"] = 3.0 if trait in CAREFUL_TRAITS else 2.0
    world.facts.update(
        theme=theme,
        missing_cfg=missing,
        risky=risky,
        response=response,
        instigator=a,
        cautioner=b,
        helper=helper,
        treat=treat,
        relation=relation,
        attempted_risk="no",
        solved="no",
        found_place="",
        risky_id=risky.id,
        escalator_running="yes",
    )

    play_setup(world, a, b, theme)
    mission_setup(world, a, b, missing)
    world.para()
    wonder(world, b, missing)
    tempt(world, a, risky, missing)
    warn(world, b, a, risky, helper, missing)

    averted = would_listen(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, helper)
        world.para()
        solve(world, helper, response, risky, missing)
        lesson(world, helper, a, b, risky)
        world.para()
        surprise_and_share(world, helper, a, b, missing, treat)
        outcome = "averted"
    else:
        defy(world, a, b, risky)
        world.para()
        attempt_risk(world, risky)
        alarm(world, b, helper)
        contained = is_contained(response, risky)
        if not contained:
            raise StoryError("(No story: the chosen response is too weak for this escalator danger.)")
        world.para()
        solve(world, helper, response, risky, missing)
        lesson(world, helper, a, b, risky)
        world.para()
        surprise_and_share(world, helper, a, b, missing, treat)
        outcome = "contained"

    world.facts.update(
        outcome=outcome,
        averted=averted,
        found=world.get("missing").meters["found"] >= THRESHOLD,
        shared=True,
        used_word_dunk=("dunk_hand" == risky.id),
        list_entity=list_ent,
        fund_entity=fund_ent,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a silver ship that climbed the air",
        rig="The rubber rail was a rope, the shining side panels were sea walls, and each step rose like a deck carrying them toward the treasure table.",
        titles=("Captain", "Scout"),
        mission="the shelter rescue mission",
        stair_word="ship stair",
        send_off="rode up again like true little pirates",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a mountain trail made of moving stairs",
        rig="The rubber rail was a guide rope, the bright lights were cave stars, and each step lifted them toward the map table above.",
        titles=("Leader", "Scout"),
        mission="the upstairs helper mission",
        stair_word="moving stair",
        send_off="rode up again like steady explorers",
    ),
}

MISSING = {
    "coin": MissingThing(
        id="coin",
        label="coin",
        phrase="one shiny coin",
        shiny="The coin",
        can_fall=True,
        can_hide_on_list=False,
        tags={"coin", "fund"},
    ),
    "star_token": MissingThing(
        id="star_token",
        label="star token",
        phrase="one star-shaped token",
        shiny="The little token",
        can_fall=True,
        can_hide_on_list=False,
        tags={"token", "fund"},
    ),
    "ribbon": MissingThing(
        id="ribbon",
        label="ribbon sticker",
        phrase="the gold ribbon sticker",
        shiny="The ribbon sticker",
        can_fall=False,
        can_hide_on_list=True,
        tags={"list", "sticker"},
    ),
}

RISKY = {
    "reach_gap": RiskyMove(
        id="reach_gap",
        sense=0,
        danger=3,
        text="I can reach into the little gap",
        warning="Do not put your fingers near the moving teeth",
        qa_text="tried to reach into the gap beside the moving escalator step",
        tags={"escalator", "gap", "ask_adult"},
    ),
    "jump_back": RiskyMove(
        id="jump_back",
        sense=0,
        danger=2,
        text="I can hop back down one step and grab it",
        warning="Do not run or jump the wrong way on the escalator",
        qa_text="tried to jump backward on the escalator to grab the missing thing",
        tags={"escalator", "jump", "ask_adult"},
    ),
    "dunk_hand": RiskyMove(
        id="dunk_hand",
        sense=0,
        danger=2,
        text="I can dunk my hand under the flappy side skirt and feel around",
        warning="Never dunk your hand into any moving machine",
        qa_text="wanted to dunk a hand into a moving part of the escalator",
        tags={"escalator", "dunk", "ask_adult"},
    ),
}

RESPONSES = {
    "stop_button": SafeResponse(
        id="stop_button",
        sense=3,
        power=3,
        text="pressed the red stop button, waited for the steps to go still, and used a long grabber to check safely.",
        qa_text="pressed the stop button and used a long grabber to retrieve it safely",
        tags={"stop_button", "grabber", "escalator"},
    ),
    "block_and_check": SafeResponse(
        id="block_and_check",
        sense=2,
        power=2,
        text="stood the children back behind the yellow line, called for the escalator to be stopped, and checked each step carefully with a grabber.",
        qa_text="moved the children back, had the escalator stopped, and checked with a grabber",
        tags={"stop_button", "grabber", "escalator"},
    ),
    "look_only": SafeResponse(
        id="look_only",
        sense=1,
        power=1,
        text="bent down to peek while the escalator kept moving.",
        qa_text="only looked while the escalator was still moving",
        tags={"escalator"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "steady", "curious", "bold"]
TREATS = ["blueberry muffin", "small cookie", "apple bun", "jam tart"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for mid, missing in MISSING.items():
            for rid, risky in RISKY.items():
                if not hazard_possible(missing, risky):
                    continue
                if mystery_place(missing, risky) == "list_back" and not missing.can_hide_on_list:
                    continue
                combos.append((theme, mid, rid))
    return combos


@dataclass
class StoryParams:
    theme: str
    missing: str
    risky: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 5
    treat: str = "blueberry muffin"
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
    "fund": [
        (
            "What is a fund?",
            "A fund is money collected for a special purpose. People can put coins or bills into it to help others."
        )
    ],
    "list": [
        (
            "What is a list?",
            "A list is a set of things written down one after another. It helps you remember jobs or items in order."
        )
    ],
    "dunk": [
        (
            "What does dunk mean?",
            "Dunk means to push something quickly down into something else. It is fine with a cookie in milk, but not with a hand near a moving machine."
        )
    ],
    "escalator": [
        (
            "What is an escalator?",
            "An escalator is a moving stair that carries people up or down. You stand still, hold the rail, and keep fingers away from the edges."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps a grown-up reach something without putting hands into a dangerous place. It is useful when an object is small or hard to reach."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it lets more than one person enjoy something. It shows you are thinking about someone else's happiness too."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle about something you do not know yet. You solve it by looking carefully for clues."
        )
    ],
    "stop_button": [
        (
            "Why would a grown-up stop an escalator?",
            "A grown-up stops an escalator when something unsafe happens near the moving steps. It is safer to make the machine still before checking closely."
        )
    ],
}
KNOWLEDGE_ORDER = ["fund", "list", "dunk", "escalator", "grabber", "sharing", "mystery", "stop_button"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    missing = f["missing_cfg"]
    risky = f["risky"]
    return [
        f'Write a short story for a 3-to-5-year-old set on an escalator that includes the words "fund", "list", and "dunk".',
        f"Tell a gentle mystery story where {a.id} and {b.id} are carrying a small fund and a list, then {missing.phrase} seems to disappear and a grown-up helps them solve it safely.",
        f"Write a pirate-flavored adventure on an escalator where one child thinks about a risky move, the {helper.label_word} helps solve the mystery, and the ending shows sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    missing = f["missing_cfg"]
    risky = f["risky"]
    treat = f["treat"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and a {helper.label_word} who helped them. They were on an escalator mission with a fund envelope and a list."
        ),
        (
            "What was the mystery?",
            f"The mystery was that {missing.phrase} seemed to be missing while the children were riding the escalator. They had to figure out where it had gone before they finished their helper mission."
        ),
        (
            f"What risky thing did {a.id} want to do?",
            f"{a.id} {risky.qa_text}. {b.id} knew that was dangerous because moving escalator parts can pinch or trap small hands."
        ),
    ]
    place = f.get("found_place", "")
    if place == "comb_plate":
        answer = f"The {helper.label_word} stopped the escalator and found it by the comb plate at the end of the step. It had fallen near the edge, so the children could not safely get it themselves."
    elif place == "step_groove":
        answer = f"The {helper.label_word} found it tucked in a little groove in one step. That solved the mystery because the shiny thing had not vanished at all; it had just ridden along where only a careful grown-up should check."
    elif place == "list_back":
        answer = f"The {helper.label_word} turned over the list and found it stuck to the back with old tape. The surprise was that the missing thing had been with them the whole time, hiding in plain sight."
    else:
        answer = f"The {helper.label_word} found it tucked into the folded side of the fund envelope. It looked missing only because it had slipped into a hidden pocket."
    qa.append(("Where was the missing thing really?", answer))
    qa.append(
        (
            "How did the story end?",
            f"The children put the missing thing into the fund, finished the list together, and shared one {treat}. The final image shows they had learned both safety and sharing."
        )
    )
    qa.append(
        (
            "Why was sharing important at the end?",
            f"Sharing turned the surprise reward into a kind ending instead of a grabby one. After a worried moment on the escalator, the children showed they could think about each other as well as themselves."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"fund", "list", "sharing", "mystery", "escalator"}
    if f.get("used_word_dunk"):
        tags.add("dunk")
    for tag in f["response"].tags:
        if tag == "grabber":
            tags.add("grabber")
        if tag == "stop_button":
            tags.add("stop_button")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} found_place={world.facts.get('found_place')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        missing="coin",
        risky="reach_gap",
        response="stop_button",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="clerk",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=5,
        treat="blueberry muffin",
    ),
    StoryParams(
        theme="explorers",
        missing="star_token",
        risky="jump_back",
        response="block_and_check",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="guard",
        trait="thoughtful",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
        treat="small cookie",
    ),
    StoryParams(
        theme="pirates",
        missing="ribbon",
        risky="dunk_hand",
        response="stop_button",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        helper="clerk",
        trait="steady",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        treat="jam tart",
    ),
]


def explain_rejection(missing: MissingThing, risky: RiskyMove) -> str:
    if risky.danger <= 0:
        return f"(No story: {risky.id} is not a real escalator danger here.)"
    if risky.id == "dunk_hand" and not missing.can_hide_on_list:
        return (
            f"(No story: the 'dunk' version works only when the mystery can honestly end with the object stuck to the back of the list. "
            f"{missing.phrase.capitalize()} would not fit that mystery.)"
        )
    if not missing.can_fall and risky.id != "dunk_hand":
        return (
            f"(No story: {missing.phrase} does not fall into the escalator path in this world. "
            f"Pick the 'dunk_hand' mystery, where it hides on the list instead.)"
        )
    return "(No story: this combination has no grounded mystery or danger.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). "
        f"Try one of the safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_listen(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], RISKY[params.risky]) else "invalid"


ASP_RULES = r"""
% --- gate ------------------------------------------------------------------
hazard(M, R) :- can_fall(M), danger(R, D), D > 0.
hazard(M, dunk_hand) :- hide_on_list(M), danger(dunk_hand, D), D > 0.
valid(T, M, R) :- theme(T), missing(M), risky(R), hazard(M, R), not bad_pair(M, R).
bad_pair(M, dunk_hand) :- not hide_on_list(M).
bad_pair(M, R) :- not can_fall(M), risky(R), R != dunk_hand.

sensible(Resp) :- response(Resp), sense(Resp, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
careful_trait(T) :- trait(T), is_careful(T).
older_sib :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
averted :- older_sib, careful_trait(_).

contained :- chosen_response(Resp), chosen_risky(R), power(Resp, P), danger(R, D), P >= D.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(invalid) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for mid, m in MISSING.items():
        lines.append(asp.fact("missing", mid))
        if m.can_fall:
            lines.append(asp.fact("can_fall", mid))
        if m.can_hide_on_list:
            lines.append(asp.fact("hide_on_list", mid))
    for rid, r in RISKY.items():
        lines.append(asp.fact("risky", rid))
        lines.append(asp.fact("danger", rid, r.danger))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for tr in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_response", params.response),
            asp.fact("chosen_risky", params.risky),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing fund item, an escalator mystery, and a sharing ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--risky", choices=RISKY)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["clerk", "guard"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.missing and args.risky:
        m = MISSING[args.missing]
        r = RISKY[args.risky]
        if (args.risky == "dunk_hand" and not m.can_hide_on_list) or (not m.can_fall and args.risky != "dunk_hand"):
            raise StoryError(explain_rejection(m, r))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.missing is None or c[1] == args.missing)
        and (args.risky is None or c[2] == args.risky)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, missing, risky = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    name1, g1 = _pick_kid(rng)
    name2, g2 = _pick_kid(rng, avoid=name1)
    helper = args.helper or rng.choice(["clerk", "guard"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    treat = rng.choice(TREATS)
    return StoryParams(
        theme=theme,
        missing=missing,
        risky=risky,
        response=response,
        instigator=name1,
        instigator_gender=g1,
        cautioner=name2,
        cautioner_gender=g2,
        helper=helper,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        treat=treat,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing item: {params.missing})")
    if params.risky not in RISKY:
        raise StoryError(f"(Unknown risky move: {params.risky})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    missing = MISSING[params.missing]
    risky = RISKY[params.risky]
    if (params.risky == "dunk_hand" and not missing.can_hide_on_list) or (not missing.can_fall and params.risky != "dunk_hand"):
        raise StoryError(explain_rejection(missing, risky))

    world = tell(
        theme=THEMES[params.theme],
        missing=missing,
        risky=risky,
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        helper_type=params.helper,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        treat=params.treat,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, missing, risky) combos:\n")
        for theme, missing, risky in combos:
            print(f"  {theme:10} {missing:10} {risky}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.missing} on escalator ({p.theme}, {p.risky}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
