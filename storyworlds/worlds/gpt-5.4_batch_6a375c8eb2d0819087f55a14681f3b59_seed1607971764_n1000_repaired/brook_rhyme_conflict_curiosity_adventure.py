#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py
======================================================================

A standalone story world about a child-sized adventure by a brook: a rhyming
clue sparks curiosity, two children disagree about a risky shortcut, and a safe
way forward changes how the adventure ends.

The world model is built around:
- a rhyming treasure-clue quest,
- a brook with physical danger (current + slippery footing),
- a curious instigator and a cautious partner,
- a sensible grown-up response,
- a safe ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py --brook swift_brook
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py --method hopping_log
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py --response mossy_log
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py --all
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/brook_rhyme_conflict_curiosity_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "ranger_f"}
        male = {"boy", "father", "grandfather", "man", "ranger_m"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "ranger_f": "ranger",
            "ranger_m": "ranger",
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
class Quest:
    id: str
    scene: str
    clue_open: str
    clue_close: str
    prize: str
    prize_phrase: str
    find_text: str
    sendoff: str
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
class Brook:
    id: str
    label: str
    scene: str
    sound: str
    current: int
    slippery: int
    bridge: str
    bridge_place: str
    bank_detail: str
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
class Method:
    id: str
    label: str
    try_text: str
    surface: str
    balance: int
    splash: int
    sense: int
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
class EndingGift:
    id: str
    phrase: str
    use_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "partner"}]

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


def _r_brook_danger(world: World) -> list[str]:
    out: list[str] = []
    if "instigator" not in world.entities or "brook" not in world.entities:
        return out
    kid = world.get("instigator")
    brook_ent = world.get("brook")
    satchel = world.get("satchel")
    if kid.meters["in_brook"] < THRESHOLD:
        return out
    sig = ("brook_danger", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    brook_ent.meters["danger"] += 1
    satchel.meters["wet"] += 1
    satchel.meters["drifting"] += 1
    kid.memes["fear"] += 1
    for other in world.kids():
        other.memes["fear"] += 1
    out.append("__splash__")
    return out


def _r_blur_clue(world: World) -> list[str]:
    out: list[str] = []
    satchel = world.get("satchel")
    clue = world.get("clue")
    if satchel.meters["wet"] < THRESHOLD:
        return out
    sig = ("blur", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["blurred"] += 1
    out.append("__blur__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="brook_danger", tag="physical", apply=_r_brook_danger),
    Rule(name="blur_clue", tag="physical", apply=_r_blur_clue),
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


def hazard_score(brook: Brook, method: Method) -> int:
    return brook.current + brook.slippery + method.splash - method.balance


def hazard_at_risk(brook: Brook, method: Method) -> bool:
    return hazard_score(brook, method) >= 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def crossing_severity(brook: Brook, method: Method, delay: int) -> int:
    return hazard_score(brook, method) + delay


def is_recovered(response: Response, brook: Brook, method: Method, delay: int) -> bool:
    return response.power >= crossing_severity(brook, method, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if partner_older else 0.0)
    return partner_older and authority > BRAVERY_INIT


def predict_slip(world: World) -> dict:
    sim = world.copy()
    _attempt_crossing(sim, narrate=False)
    return {
        "wet_satchel": sim.get("satchel").meters["wet"] >= THRESHOLD,
        "fear": sim.get("instigator").memes["fear"],
        "blurred": sim.get("clue").meters["blurred"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, guide: Entity, quest: Quest, brook: Brook) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"On a bright morning, {a.id} and {b.id} set off with {guide.label_word} for "
        f"{quest.scene}. Ahead of them, the {brook.label} {brook.sound} through {brook.scene}."
    )
    world.say(
        f"In {guide.label_word}'s pocket was a treasure slip with a rhyme on it: "
        f'"{quest.clue_open}"'
    )
    world.say(f'"{quest.clue_close}"')
    world.say(
        f"The words made the whole path feel like a secret song, and the children hurried on, "
        f"{quest.sendoff}."
    )


def discover(world: World, a: Entity, b: Entity, brook: Brook, quest: Quest) -> None:
    world.say(
        f"Soon they reached the brook. On the far bank, just beyond {brook.bank_detail}, "
        f"{a.id} spotted {quest.prize_phrase}."
    )
    world.say(
        f'"Look!" {a.id} whispered. "The rhyme must mean that {quest.prize}."'
    )


def tempt(world: World, a: Entity, method: Method) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id}'s eyes shone with curiosity. "
        f'"I can get there first," {a.pronoun()} said. "I will {method.try_text}."'
    )


def warn(world: World, b: Entity, a: Entity, guide: Entity, brook: Brook, method: Method) -> None:
    pred = predict_slip(world)
    b.memes["caution"] += 1
    world.facts["predicted_blur"] = pred["blurred"]
    extra = ""
    if pred["wet_satchel"]:
        extra = " The clue slip could get wet and blurry too."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. '
        f'"Wait, {a.id}. The {method.surface} looks slippery, and the brook is quick today. '
        f'{guide.label_word.capitalize()} said adventures still need careful feet."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, guide: Entity, brook: Brook) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} took one more look at the bright water, then let out a slow breath. '
        f'"All right," {a.pronoun()} said. "Let\'s do it the wise way."'
    )
    world.say(
        f"They followed {guide.label_word} to {brook.bridge_place}, where {brook.bridge} waited over the water."
    )


def defy(world: World, a: Entity, b: Entity, method: Method) -> None:
    a.memes["defiance"] += 1
    instigator_older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older:
        world.say(
            f'"We will lose the trail if we wait," {a.id} said. Because {a.id} was '
            f"{b.pronoun('possessive')} older sibling, {b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"We will lose the trail if we wait," {a.id} said, and darted toward {method.surface}.'
        )


def _attempt_crossing(world: World, narrate: bool = True) -> None:
    kid = world.get("instigator")
    method = world.facts["method_cfg"]
    kid.meters["in_brook"] += 1
    kid.meters["soaked"] += float(method.splash)
    propagate(world, narrate=narrate)


def attempt(world: World, a: Entity, brook: Brook, method: Method) -> None:
    _attempt_crossing(world, narrate=True)
    world.say(
        f"{a.id} put one foot on {method.surface}. For a blink it seemed fine. "
        f"Then the moss gave a sly green slide, the water slapped high, and {a.pronoun()} splashed into the edge of the brook."
    )


def alarm(world: World, b: Entity, guide: Entity, a: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} cried.')
    world.say(f'"Hold still!" called {guide.label_word.capitalize()}.')
    if world.get("clue").meters["blurred"] >= THRESHOLD:
        world.say("The satchel bobbed once, and the treasure slip inside went dark with water.")


def rescue(world: World, guide: Entity, response: Response, brook: Brook, quest: Quest) -> None:
    kid = world.get("instigator")
    satchel = world.get("satchel")
    clue = world.get("clue")
    brook_ent = world.get("brook")
    kid.meters["in_brook"] = 0.0
    brook_ent.meters["danger"] = 0.0
    satchel.meters["drifting"] = 0.0
    satchel.meters["saved"] += 1
    clue.meters["saved"] += 1
    world.say(
        f"{guide.label_word.capitalize()} {response.text.replace('{bridge}', brook.bridge).replace('{bridge_place}', brook.bridge_place)}."
    )
    world.say(
        f"Soon {a_or_the(kid)} was back on the bank, dripping but safe, with the satchel held high above the water."
    )
    world.say(
        f'The wet slip could still be read, and {guide.label_word} tapped the rhyme with a dry finger. '
        f'"Curious is good," {guide.pronoun()} said, "but curious and careful gets you farther."'
    )
    for e in world.kids():
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
        e.memes["fear"] = 0.0
    world.facts["quest_continues"] = True
    world.facts["found_prize"] = True
    world.say(
        f"They crossed by the safe way after that, and {quest.find_text}"
    )


def rescue_fail(world: World, guide: Entity, response: Response, quest: Quest) -> None:
    kid = world.get("instigator")
    satchel = world.get("satchel")
    clue = world.get("clue")
    kid.meters["in_brook"] = 0.0
    satchel.meters["drifting"] = 1.0
    clue.meters["lost"] += 1
    world.say(
        f"{guide.label_word.capitalize()} {response.fail}."
    )
    world.say(
        f"{a_or_the(kid).capitalize()} was pulled safely back to shore, but the soaked clue slip spun away between the reeds."
    )
    for e in world.kids():
        e.memes["relief"] += 1
        e.memes["sadness"] += 1
        e.memes["lesson"] += 1
    world.facts["quest_continues"] = False
    world.facts["found_prize"] = False


def lesson_after_loss(world: World, guide: Entity, a: Entity, b: Entity, gift: EndingGift) -> None:
    world.say(
        f'{guide.label_word.capitalize()} wrapped {a.id} in a dry towel from the pack and pulled {b.id} close. '
        f'"The brook was stronger than your hurry," {guide.pronoun()} said softly.'
    )
    world.say(
        f"{a.id} blinked at the empty water and nodded. {b.id} nodded too. "
        f"They had wanted the adventure to gallop, but now they knew a good trail asks for patience."
    )
    world.say(
        f"The next day, {guide.label_word} brought {gift.phrase}. "
        f"{gift.use_text}, and the children copied a new rhyme on the first clean page."
    )


def safe_finish(world: World, guide: Entity, a: Entity, b: Entity, quest: Quest, gift: EndingGift) -> None:
    world.say(
        f"That evening, {guide.label_word} gave them {gift.phrase}. "
        f"{gift.use_text}."
    )
    world.say(
        f"Soon {a.id} and {b.id} were making up their own trail rhyme: "
        f'"Brook and book, stop and look."'
    )
    world.say(
        f"They laughed, tucked the new gear away, and watched the late light shine where the little {quest.prize} had been found."
    )


def a_or_the(ent: Entity) -> str:
    return ent.id


def tell(
    quest: Quest,
    brook: Brook,
    method: Method,
    response: Response,
    gift: EndingGift,
    *,
    instigator: str = "Nora",
    instigator_gender: str = "girl",
    partner: str = "Eli",
    partner_gender: str = "boy",
    guide_type: str = "grandfather",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 5,
    partner_age: int = 7,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["curious", "bold"],
    ))
    b = world.add(Entity(
        id=partner,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        role="guide",
        label="the guide",
    ))
    brook_ent = world.add(Entity(id="brook", type="brook", label=brook.label))
    clue = world.add(Entity(id="clue", type="paper", label="treasure slip"))
    satchel = world.add(Entity(id="satchel", type="satchel", label="satchel"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    world.facts.update(
        quest=quest,
        brook_cfg=brook,
        method_cfg=method,
        response=response,
        gift=gift,
        guide=guide,
    )

    introduce(world, a, b, guide, quest, brook)
    discover(world, a, b, brook, quest)

    world.para()
    tempt(world, a, method)
    warn(world, b, a, guide, brook, method)

    averted = would_avert(relation, instigator_age, partner_age, trait)

    if averted:
        back_down(world, a, b, guide, brook)
        world.facts["quest_continues"] = True
        world.facts["found_prize"] = True
        world.para()
        world.say(
            f"They crossed at {brook.bridge_place}, following the rhyme step by step, and {quest.find_text}"
        )
        world.say(
            f'{a.id} grinned at {b.id}. "Good thing you made me stop and look," {a.pronoun()} said.'
        )
        world.para()
        safe_finish(world, guide, a, b, quest, gift)
        severity = 0
        recovered = True
    else:
        defy(world, a, b, method)
        world.para()
        attempt(world, a, brook, method)
        alarm(world, b, guide, a)
        severity = crossing_severity(brook, method, delay)
        recovered = is_recovered(response, brook, method, delay)
        world.para()
        if recovered:
            rescue(world, guide, response, brook, quest)
            world.para()
            safe_finish(world, guide, a, b, quest, gift)
        else:
            rescue_fail(world, guide, response, quest)
            lesson_after_loss(world, guide, a, b, gift)

    outcome = "averted" if averted else ("recovered" if recovered else "lost")
    world.facts.update(
        instigator=a,
        partner=b,
        clue=clue,
        satchel=satchel,
        brook=brook_ent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        found_prize=world.facts.get("found_prize", False),
        clue_blurred=clue.meters["blurred"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "moonstone": Quest(
        id="moonstone",
        scene="a small treasure hunt along the fern path",
        clue_open="By the brook where silver ferns all look,",
        clue_close="seek the moonstone by the crook.",
        prize="moonstone",
        prize_phrase="a pale moonstone tucked beside a bent root",
        find_text="they found the moonstone shining like a drop of quiet sky.",
        sendoff="as if the path itself were singing",
        tags={"rhyme", "treasure"},
    ),
    "feather": Quest(
        id="feather",
        scene="a winding search for a kingfisher feather",
        clue_open="By the brook where bright reeds hook,",
        clue_close="find the feather near the nook.",
        prize="feather",
        prize_phrase="a blue feather gleaming near a willow root",
        find_text="they found the feather striped with river-blue and tucked it gently into the satchel.",
        sendoff="with their noses lifted for clues",
        tags={"rhyme", "feather"},
    ),
    "bell": Quest(
        id="bell",
        scene="a hidden-bell adventure under the pines",
        clue_open="By the brook where pebbles click and look,",
        clue_close="search the mossy stump beside the crook.",
        prize="bell",
        prize_phrase="a tiny brass bell peeping from the moss",
        find_text="they found the bell and its soft ring sounded like a bright drop of gold.",
        sendoff="with springy, adventurous steps",
        tags={"rhyme", "bell"},
    ),
}

BROOKS = {
    "fern_brook": Brook(
        id="fern_brook",
        label="fern brook",
        scene="ferns and round stones",
        sound="chuckled",
        current=1,
        slippery=1,
        bridge="a little wooden bridge",
        bridge_place="the bend in the trail",
        bank_detail="a tuft of bright moss",
        tags={"brook", "bridge"},
    ),
    "mossy_brook": Brook(
        id="mossy_brook",
        label="mossy brook",
        scene="mossy banks and alder roots",
        sound="ran whispering",
        current=1,
        slippery=2,
        bridge="a narrow bridge with a hand rail",
        bridge_place="the alder bend",
        bank_detail="a clump of reeds",
        tags={"brook", "bridge"},
    ),
    "swift_brook": Brook(
        id="swift_brook",
        label="swift brook",
        scene="cold stones and quick water",
        sound="rushed",
        current=2,
        slippery=2,
        bridge="a sturdy footbridge",
        bridge_place="the high bend",
        bank_detail="a fringe of long grass",
        tags={"brook", "bridge"},
    ),
}

METHODS = {
    "stepping_stones": Method(
        id="stepping_stones",
        label="stepping stones",
        try_text="skip across the stepping stones",
        surface="the stepping stones",
        balance=2,
        splash=1,
        sense=2,
        tags={"stones", "slip"},
    ),
    "hopping_log": Method(
        id="hopping_log",
        label="mossy log",
        try_text="hop across the mossy log",
        surface="the mossy log",
        balance=1,
        splash=1,
        sense=1,
        tags={"log", "slip"},
    ),
    "wading": Method(
        id="wading",
        label="shallow edge",
        try_text="wade through the shallow edge",
        surface="the shallow edge",
        balance=1,
        splash=2,
        sense=1,
        tags={"water", "wet"},
    ),
}

RESPONSES = {
    "footbridge": Response(
        id="footbridge",
        sense=3,
        power=4,
        text="caught the satchel strap with a walking stick, steadied the child, and led everyone to {bridge} at {bridge_place}",
        fail="reached with a walking stick and shouted directions, but the satchel still spun out of reach before everyone reached the bridge",
        qa_text="used a walking stick and the footbridge to get everyone safely across",
        tags={"bridge", "walking_stick"},
    ),
    "handrope": Response(
        id="handrope",
        sense=3,
        power=3,
        text="threw a hand rope from the pack, pulled the child to the bank, and then guided them over {bridge}",
        fail="threw a hand rope and pulled the child out, but the clue slip washed away before the satchel could be saved",
        qa_text="used a hand rope to pull the child in and then took the bridge",
        tags={"rope", "bridge"},
    ),
    "long_branch": Response(
        id="long_branch",
        sense=2,
        power=2,
        text="lay a long branch across the nearest gap, braced it hard, and helped the child climb back to the bank before using {bridge}",
        fail="stretched a long branch toward the child, but the water tugged the satchel free before it could be hooked",
        qa_text="used a long branch to help the child back and then chose the bridge",
        tags={"branch", "bridge"},
    ),
    "mossy_log": Response(
        id="mossy_log",
        sense=1,
        power=1,
        text="hurried everyone onto another log, wobbling beside the water",
        fail="tried another mossy log, but it only made the scramble slower and slippier",
        qa_text="tried another log crossing",
        tags={"log"},
    ),
}

GIFTS = {
    "field_book": EndingGift(
        id="field_book",
        phrase="a small field book with dry pages",
        use_text="They used it to copy clues and make new rhymes for later trails",
        tags={"book", "rhyme"},
    ),
    "waxed_map": EndingGift(
        id="waxed_map",
        phrase="a waxed map sleeve with a blue cord",
        use_text="They slid their clues inside so the next adventure could stay dry by the water",
        tags={"map", "dry"},
    ),
    "pocket_compass": EndingGift(
        id="pocket_compass",
        phrase="a little pocket compass in a tin case",
        use_text="They passed it between them and promised to stop before each risky step and look together",
        tags={"compass", "care"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Mia", "Zoe", "Anna", "Ruby", "Ella"]
BOY_NAMES = ["Eli", "Ben", "Sam", "Theo", "Max", "Noah", "Finn", "Leo"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "bright"]
GUIDES = ["mother", "father", "grandmother", "grandfather", "ranger_f", "ranger_m"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for quest_id in QUESTS:
        for brook_id, brook in BROOKS.items():
            for method_id, method in METHODS.items():
                if hazard_at_risk(brook, method):
                    combos.append((quest_id, brook_id, method_id))
    return combos


@dataclass
class StoryParams:
    quest: str
    brook: str
    method: str
    response: str
    gift: str
    instigator: str
    instigator_gender: str
    partner: str
    partner_gender: str
    guide: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    partner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
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
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of flowing water. It can look gentle, but the stones around it can still be slippery."
        )
    ],
    "bridge": [
        (
            "Why is a bridge safer than slippery stones?",
            "A bridge gives you a steady place to walk over the water. That is safer because your feet do not have to balance on wet, moving rocks."
        )
    ],
    "rope": [
        (
            "What can a rope help with near water?",
            "A rope can help a grown-up pull or steady someone from a safer place. It helps because the helper does not have to step into the slippery water too."
        )
    ],
    "walking_stick": [
        (
            "Why would a walking stick help on a trail?",
            "A walking stick can help with balance and reaching. Near a brook, a grown-up can also use it to hook or steady something without leaning too far."
        )
    ],
    "branch": [
        (
            "Why can a long branch help someone climb out of a brook?",
            "A long branch gives a handhold from the bank. It helps because the child can grab something firm while a grown-up stays out of the water."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme clue?",
            "A rhyme clue is a hint written with words that sound alike. It can make directions easier to remember and more fun to follow."
        )
    ],
    "care": [
        (
            "Can curiosity be a good thing?",
            "Yes. Curiosity helps you notice new things and ask questions, but it works best when you slow down and choose a safe way to explore."
        )
    ],
    "map": [
        (
            "Why would someone keep a map or clue in a dry sleeve?",
            "A dry sleeve keeps paper from getting wet and blurry. That matters near a brook because splashes can ruin a clue very quickly."
        )
    ],
    "book": [
        (
            "Why might children keep a field book on a walk?",
            "A field book gives them a place to copy clues, draw what they see, and remember the trail later. It turns a walk into a careful adventure."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass helps you tell direction. On an adventure, it reminds you to pause, look around, and think before you hurry."
        )
    ],
}
KNOWLEDGE_ORDER = ["brook", "rhyme", "bridge", "rope", "walking_stick", "branch", "map", "book", "compass", "care"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    quest = f["quest"]
    brook = f["brook_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write an adventure story for a 3-to-5-year-old with a rhyming clue, a brook, and two children who disagree about a shortcut.',
            f"Tell a gentle adventure where {a.id} wants to {method.try_text}, but {b.id} stops {a.pronoun('object')} and they find the {quest.prize} by taking the safe bridge instead.",
            f'Write a story that includes the word "brook", uses rhyme and curiosity, and ends with the children learning to stop and look before rushing ahead.',
        ]
    if outcome == "lost":
        return [
            f'Write a child-facing adventure about a rhyming treasure hunt beside a brook where curiosity turns into a mistake, but everyone gets safe again.',
            f"Tell a story where {a.id} ignores a warning and tries to {method.try_text}, and the clue is lost even though a grown-up rescues the child.",
            f'Write a cautionary adventure with rhyme, conflict, and curiosity, ending in a wiser new start instead of a prize.',
        ]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes a brook, a rhyming clue, a disagreement, and a safe rescue.',
        f"Tell a story where {a.id} is too curious to wait, slips while trying to {method.try_text}, and then learns the wise way to finish the treasure hunt.",
        f'Write a simple adventure with rhyme and conflict that ends with the children still finding the {quest.prize} after choosing the safer path.',
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    guide = f["guide"]
    quest = f["quest"]
    brook = f["brook_cfg"]
    method = f["method_cfg"]
    response = f["response"]
    gift = f["gift"]
    pair = pair_noun(a, b, a.attrs.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, on an adventure with {guide.label_word}. They are following a rhyme clue near a brook."
        ),
        (
            "What started the adventure?",
            f"The adventure started with a rhyme clue about the {quest.prize}. The rhyme made the trail feel like a game and pulled the children forward with curiosity."
        ),
        (
            f"Why did {a.id} want to hurry across the brook?",
            f"{a.id} saw {quest.prize_phrase} on the far bank and thought the clue pointed straight to it. Curiosity made the treasure feel very close, so waiting seemed hard."
        ),
        (
            f"Why did {b.id} say no?",
            f"{b.id} thought the {method.surface} looked slippery and the brook looked quick. {b.pronoun().capitalize()} was worried the satchel and clue slip would get wet if {a.id} rushed."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{b.id}'s warning worked, so {a.id} stopped before stepping into danger. Because they paused and chose the bridge, the adventure kept going without a fall."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They crossed safely, found the {quest.prize}, and later got {gift.phrase}. The ending shows they became more careful explorers, not less curious ones."
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"What happened when {a.id} tried to {method.try_text}?",
                f"{a.id} slipped into the edge of the brook and the satchel got wet. That mattered because the clue slip inside could have blurred and spoiled the hunt."
            )
        )
        qa.append(
            (
                f"How did {guide.label_word} help?",
                f"{guide.label_word.capitalize()} {response.qa_text}. The quick help kept {a.id} safe and saved enough of the clue for the treasure hunt to continue."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that curiosity is better with care. The brook did not end the adventure, but it taught them to stop and look before rushing."
            )
        )
    else:
        qa.append(
            (
                f"Did they still find the {quest.prize} that day?",
                f"No. {guide.label_word.capitalize()} got {a.id} back safely, but the clue slip washed away. Without the rhyme to guide them, the treasure had to wait for another day."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely but sadly: the prize was not found, and the children went home wiser. The next day they had better gear and a calmer plan for future adventures."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that hurry can spoil a good adventure. Curiosity still mattered, but not more than safety near the brook."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"brook", "rhyme", "care"}
    tags |= set(f["response"].tags)
    tags |= set(f["gift"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="moonstone",
        brook="fern_brook",
        method="stepping_stones",
        response="footbridge",
        gift="field_book",
        instigator="Nora",
        instigator_gender="girl",
        partner="Eli",
        partner_gender="boy",
        guide="grandfather",
        trait="careful",
        delay=0,
        instigator_age=5,
        partner_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        quest="feather",
        brook="mossy_brook",
        method="stepping_stones",
        response="handrope",
        gift="waxed_map",
        instigator="Ben",
        instigator_gender="boy",
        partner="Mia",
        partner_gender="girl",
        guide="mother",
        trait="steady",
        delay=0,
        instigator_age=6,
        partner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        quest="bell",
        brook="swift_brook",
        method="wading",
        response="long_branch",
        gift="pocket_compass",
        instigator="Ava",
        instigator_gender="girl",
        partner="Theo",
        partner_gender="boy",
        guide="ranger_f",
        trait="thoughtful",
        delay=1,
        instigator_age=6,
        partner_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        quest="moonstone",
        brook="swift_brook",
        method="stepping_stones",
        response="footbridge",
        gift="waxed_map",
        instigator="Leo",
        instigator_gender="boy",
        partner="Ruby",
        partner_gender="girl",
        guide="father",
        trait="cautious",
        delay=0,
        instigator_age=7,
        partner_age=5,
        relation="siblings",
        trust=5,
    ),
]


def explain_rejection(brook: Brook, method: Method) -> str:
    return (
        f"(No story: trying {method.label} at the {brook.label} is not risky enough to drive this adventure. "
        f"This world only tells versions where the shortcut really could lead to a slip and a changed ending.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.partner_age, params.trait):
        return "averted"
    brook = BROOKS[params.brook]
    method = METHODS[params.method]
    response = RESPONSES[params.response]
    return "recovered" if is_recovered(response, brook, method, params.delay) else "lost"


ASP_RULES = r"""
hazard(B, M) :- brook(B), method(M), current(B, C), slippery(B, S), splash(M, Sp), balance(M, Ba),
                H = C + S + Sp - Ba, H >= 2.
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(Q, B, M) :- quest(Q), hazard(B, M), sensible(_).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), instigator_age(IA), partner_age(PA), PA > IA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), bravery_init(BR), A > BR.

severity(H + D) :- chosen_brook(B), chosen_method(M), current(B, C), slippery(B, S),
                   splash(M, Sp), balance(M, Ba), H = C + S + Sp - Ba, delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(lost) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for bid, b in BROOKS.items():
        lines.append(asp.fact("brook", bid))
        lines.append(asp.fact("current", bid, b.current))
        lines.append(asp.fact("slippery", bid, b.slippery))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("balance", mid, m.balance))
        lines.append(asp.fact("splash", mid, m.splash))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
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

    scenario = "\n".join([
        asp.fact("chosen_brook", params.brook),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
            raise StoryError("empty story")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming brook adventure with curiosity, conflict, and a safer way forward."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--brook", choices=BROOKS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the trouble gets before help fully catches up")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.brook and args.method:
        brook = BROOKS[args.brook]
        method = METHODS[args.method]
        if not hazard_at_risk(brook, method):
            raise StoryError(explain_rejection(brook, method))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.brook is None or c[1] == args.brook)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, brook_id, method_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gift_id = rng.choice(sorted(GIFTS))
    instigator, ig = _pick_kid(rng)
    partner, pg = _pick_kid(rng, avoid=instigator)
    guide = args.guide or rng.choice(GUIDES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        quest=quest_id,
        brook=brook_id,
        method=method_id,
        response=response_id,
        gift=gift_id,
        instigator=instigator,
        instigator_gender=ig,
        partner=partner,
        partner_gender=pg,
        guide=guide,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    missing = []
    if params.quest not in QUESTS:
        missing.append(f"quest={params.quest}")
    if params.brook not in BROOKS:
        missing.append(f"brook={params.brook}")
    if params.method not in METHODS:
        missing.append(f"method={params.method}")
    if params.response not in RESPONSES:
        missing.append(f"response={params.response}")
    if params.gift not in GIFTS:
        missing.append(f"gift={params.gift}")
    if missing:
        raise StoryError(f"(Invalid params: {', '.join(missing)})")

    brook = BROOKS[params.brook]
    method = METHODS[params.method]
    response = RESPONSES[params.response]
    if not hazard_at_risk(brook, method):
        raise StoryError(explain_rejection(brook, method))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        QUESTS[params.quest],
        brook,
        method,
        response,
        GIFTS[params.gift],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        guide_type=params.guide,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        partner_age=params.partner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (quest, brook, method) combos:\n")
        for quest, brook, method in combos:
            print(f"  {quest:10} {brook:12} {method}")
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
            header = f"### {p.instigator} & {p.partner}: {p.quest} at {p.brook} via {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
