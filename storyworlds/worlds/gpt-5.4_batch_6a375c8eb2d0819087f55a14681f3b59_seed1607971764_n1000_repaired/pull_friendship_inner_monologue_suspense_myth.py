#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py
===========================================================================

A standalone storyworld about two friends in a myth-colored landscape: something
precious is caught above a sacred place, one child is tempted to pull it free,
the other feels the danger before speaking, and friendship turns suspense into a
choice.

The world model is small but classical:
- typed entities with physical meters and emotional memes
- a short causal rule engine
- a reasonableness gate for compatible helpers
- an inline ASP twin for the gate and outcome model
- state-driven prose, not slot-swapped text

Run it
------
    python storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py
    python storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py --place moon_well --snag garland
    python storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py --helper ladder
    python storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py --all
    python storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/pull_friendship_inner_monologue_suspense_myth.py --verify
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
IMPULSE_INIT = 6.0
STEADY_TRAITS = {"steady", "patient", "wise", "careful"}


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
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "keeper"}
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
class Place:
    id: str
    label: str
    phrase: str
    image: str
    water: str
    snag_spot: str
    allowed_helpers: set[str] = field(default_factory=set)
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
class Snag:
    id: str
    label: str
    phrase: str
    attached_to: str
    risk_text: str
    ending_image: str
    weight: int
    height: int
    fragile: bool = False
    sacred: bool = True
    over_water: bool = True
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
    phrase: str
    sense: int
    reach: int
    lift: int
    gentle: bool
    method: str
    success_text: str
    fail_text: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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
        clone.facts = dict(self.facts)
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


def _r_tremble(world: World) -> list[str]:
    out: list[str] = []
    rope = world.get("rope")
    if rope.meters["jerked"] < THRESHOLD:
        return out
    sig = ("tremble", "rope")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("object").meters["slipping"] += 1
    world.get("place").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__tremble__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("object")
    place = world.get("place")
    if obj.meters["slipping"] < THRESHOLD or place.meters["danger"] < THRESHOLD:
        return out
    sig = ("fall", "object")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["lost"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tremble", tag="physical", apply=_r_tremble),
    Rule(name="fall", tag="physical", apply=_r_fall),
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


def helper_fits(place: Place, snag: Snag, helper: Helper) -> bool:
    if helper.id not in place.allowed_helpers:
        return False
    if helper.sense < SENSE_MIN:
        return False
    if helper.reach < snag.height:
        return False
    if helper.lift < snag.weight:
        return False
    if snag.fragile and not helper.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for snag_id, snag in SNAGS.items():
            for helper_id, helper in HELPERS.items():
                if helper_fits(place, snag, helper):
                    combos.append((place_id, snag_id, helper_id))
    return combos


def pull_severity(snag: Snag, gust: int) -> int:
    return snag.weight + gust


def helper_succeeds(helper: Helper, snag: Snag, gust: int) -> bool:
    return helper.lift >= pull_severity(snag, gust) and helper.reach >= snag.height


def steady_value(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_avert(friend_age: int, trust: int, trait: str) -> bool:
    authority = steady_value(trait) + 1.0 + (1.0 if friend_age >= 6 else 0.0) + (1.0 if trust >= 7 else 0.0)
    return authority > IMPULSE_INIT


def predict_pull(world: World) -> dict:
    sim = world.copy()
    do_pull(sim, narrate=False)
    return {
        "danger": sim.get("place").meters["danger"],
        "slipping": sim.get("object").meters["slipping"],
        "lost": sim.get("object").meters["lost"],
    }


def introduce(world: World, instigator: Entity, friend: Entity, place: Place, snag: Snag) -> None:
    for kid in (instigator, friend):
        kid.memes["wonder"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"In the old days, when springs were said to remember songs, {instigator.id} "
        f"and {friend.id} walked together to {place.phrase}. {place.image}"
    )
    world.say(
        f"There they found {snag.phrase}, caught in {snag.attached_to} above {place.snag_spot}."
    )


def longing(world: World, instigator: Entity, snag: Snag) -> None:
    instigator.memes["desire"] += 1
    world.say(
        f'"It is so close," {instigator.id} whispered. Inside, {instigator.pronoun()} thought, '
        f'"If I just pull once, perhaps {snag.label} will come free before the water notices."'
    )


def warning(world: World, friend: Entity, instigator: Entity, snag: Snag) -> None:
    pred = predict_pull(world)
    friend.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = " The thought made the back of " + friend.pronoun("possessive") + " neck feel cold."
    world.say(
        f"{friend.id} watched the line of root and the dark water below. "
        f'Inside, {friend.pronoun()} thought, "If {instigator.id} pulls, {snag.risk_text}."{extra}'
    )
    world.say(
        f'"Do not pull it yet," {friend.id} said softly. "Let us be clever before we are brave."'
    )


def back_down(world: World, instigator: Entity, friend: Entity) -> None:
    instigator.memes["impulse"] = 0.0
    instigator.memes["trust"] += 1
    instigator.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{instigator.id} held still. The wanting was strong, but {instigator.pronoun()} looked at "
        f"{friend.id} and trusted {friend.pronoun('object')} more than the quick idea in "
        f"{instigator.pronoun('possessive')} own head."
    )


def do_pull(world: World, narrate: bool = True) -> None:
    world.get("rope").meters["jerked"] += 1
    propagate(world, narrate=narrate)


def defy(world: World, instigator: Entity, friend: Entity) -> None:
    instigator.memes["impulse"] += 1
    instigator.memes["defiance"] += 1
    world.say(
        f'"Only one little pull," {instigator.id} said, though {instigator.pronoun()} did not sound sure. '
        f'Before {friend.id} could stop {instigator.pronoun("object")}, {instigator.pronoun()} reached up.'
    )


def suspense(world: World, instigator: Entity, snag: Snag, place: Place) -> None:
    do_pull(world, narrate=False)
    world.say(
        f"The root tightened. The leaves shivered. For one heartbeat, nothing happened at all."
    )
    world.say(
        f"Then {place.water} gave a low round sound, and {snag.label} swayed over the dark."
    )


def recover(world: World, friend: Entity, helper: Helper, snag: Snag, place: Place) -> None:
    obj = world.get("object")
    obj.meters["safe"] += 1
    obj.meters["slipping"] = 0.0
    obj.meters["lost"] = 0.0
    world.get("place").meters["danger"] = 0.0
    world.say(
        f"{friend.id} moved first, because friendship can be quicker than fear. "
        f"{helper.success_text}"
    )
    world.say(
        f"Soon {snag.label} rested safe in both their hands, and even {place.water} sounded quiet again."
    )


def lose(world: World, instigator: Entity, friend: Entity, helper: Helper, snag: Snag, place: Place) -> None:
    world.get("object").meters["lost"] = 1.0
    world.say(helper.fail_text)
    world.say(
        f"They both lunged, but {snag.label} slipped from the root and vanished into {place.water}. "
        f"For a long breath, neither friend spoke."
    )
    instigator.memes["sorrow"] += 1
    friend.memes["sorrow"] += 1


def lesson(world: World, instigator: Entity, friend: Entity, snag: Snag, helper: Helper, place: Place, happy: bool) -> None:
    for kid in (instigator, friend):
        kid.memes["friendship"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    if happy:
        world.say(
            f'"Next time," {instigator.id} said, smiling a little, "I will listen before I pull."'
        )
        world.say(
            f'"And next time," {friend.id} answered, "we will solve it together from the start."'
        )
        world.say(
            f"They walked home shoulder to shoulder, carrying {snag.label} between them like a small piece of moonlight."
        )
    else:
        world.say(
            f'"I only wanted to be fast," {instigator.id} said at last. {instigator.pronoun().capitalize()} felt the words scrape on the way out.'
        )
        world.say(
            f'{friend.id} took {instigator.pronoun("possessive")} hand. "Better to be together than fast," '
            f'{friend.pronoun()} said. The loss hurt, but the friendship held.'
        )
        world.say(
            f"When they turned back once more, {place.water} was still, as if keeping the tale for itself."
        )


def safe_plan(world: World, friend: Entity, helper: Helper, snag: Snag) -> None:
    friend.memes["resolve"] += 1
    world.say(
        f'{friend.id} pointed to {helper.phrase}. "We can use that instead," {friend.pronoun()} said. '
        f'"{helper.method}"'
    )
    world.say(
        f"The plan was slower than a quick pull, which was exactly why it felt wise."
    )


def tell(
    place: Place,
    snag: Snag,
    helper: Helper,
    *,
    instigator_name: str = "Niko",
    instigator_type: str = "boy",
    friend_name: str = "Iria",
    friend_type: str = "girl",
    trait: str = "steady",
    gust: int = 0,
    instigator_age: int = 6,
    friend_age: int = 6,
    trust: int = 7,
) -> World:
    world = World(place)
    instigator = world.add(Entity(
        id=instigator_name,
        kind="character",
        type=instigator_type,
        role="instigator",
        age=instigator_age,
        traits=["quick", "bold"],
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        role="friend",
        age=friend_age,
        traits=[trait],
        attrs={},
    ))
    world.add(Entity(id="place", type="place", label=place.label, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="rope", type="root", label="hanging root", attrs={}, meters=defaultdict(float), memes=defaultdict(float)))
    world.add(Entity(id="object", type="offering", label=snag.label, attrs={}, meters=defaultdict(float), memes=defaultdict(float)))

    instigator.memes["impulse"] = IMPULSE_INIT
    instigator.memes["trust"] = float(trust)
    friend.memes["caution"] = steady_value(trait)
    world.facts["predicted_danger"] = 0.0

    introduce(world, instigator, friend, place, snag)
    world.para()
    longing(world, instigator, snag)
    warning(world, friend, instigator, snag)

    averted = would_avert(friend_age, trust, trait)
    if averted:
        back_down(world, instigator, friend)
        world.para()
        safe_plan(world, friend, helper, snag)
        recover(world, friend, helper, snag, place)
        outcome = "averted"
    else:
        world.para()
        defy(world, instigator, friend)
        suspense(world, instigator, snag, place)
        world.para()
        safe_plan(world, friend, helper, snag)
        if helper_succeeds(helper, snag, gust):
            recover(world, friend, helper, snag, place)
            outcome = "recovered"
        else:
            lose(world, instigator, friend, helper, snag, place)
            outcome = "lost"

    world.para()
    lesson(world, instigator, friend, snag, helper, place, happy=outcome != "lost")
    world.facts.update(
        instigator=instigator,
        friend=friend,
        place_cfg=place,
        snag_cfg=snag,
        helper=helper,
        outcome=outcome,
        gust=gust,
        trust=trust,
        attempted_pull=not averted,
        object_lost=world.get("object").meters["lost"] >= THRESHOLD,
        object_safe=world.get("object").meters["safe"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "spring": [
        (
            "What is a spring?",
            "A spring is a place where water comes up from the ground. People have long told stories about springs because they feel ancient and alive.",
        )
    ],
    "garland": [
        (
            "What is a garland?",
            "A garland is a ring or chain of leaves or flowers. People hang garlands for beauty, festivals, or offerings.",
        )
    ],
    "lamp": [
        (
            "What is a bronze lamp?",
            "A bronze lamp is a heavy little lamp made of metal. In old stories, a lamp often stands for memory, prayer, or light in the dark.",
        )
    ],
    "flute": [
        (
            "What is a reed flute?",
            "A reed flute is a small instrument you blow into to make music. It is light, but it can crack if handled roughly.",
        )
    ],
    "crook": [
        (
            "What is a shepherd's crook?",
            "A shepherd's crook is a staff with a curved top. The curve lets a person catch or lift something gently from a little distance away.",
        )
    ],
    "ladder": [
        (
            "Why can a ladder help someone reach safely?",
            "A ladder lets you climb up little by little instead of jumping or yanking. It is useful when something is high and needs steady hands.",
        )
    ],
    "pole": [
        (
            "What is a ferry pole?",
            "A ferry pole is a long pole used to push or guide a boat. In a story, it can also help nudge something that is hanging over water.",
        )
    ],
    "friendship": [
        (
            "How can friendship help in a scary moment?",
            "A good friend can notice danger, speak up, and stay beside you when your heart starts racing. Friendship makes courage steadier, not louder.",
        )
    ],
    "patience": [
        (
            "Why is patience useful when something feels urgent?",
            "Patience gives you time to notice what a fast feeling might miss. Going slowly can be the safest way to save something precious.",
        )
    ],
}
KNOWLEDGE_ORDER = ["spring", "garland", "lamp", "flute", "crook", "ladder", "pole", "friendship", "patience"]


PLACES = {
    "moon_well": Place(
        id="moon_well",
        label="Moon Well",
        phrase="the Moon Well",
        image="White stones circled the water, and ivy made little shadows like sleeping snakes.",
        water="the well-water",
        snag_spot="the black mirror of the well",
        allowed_helpers={"crook", "ladder"},
        tags={"spring", "friendship"},
    ),
    "laurel_spring": Place(
        id="laurel_spring",
        label="Laurel Spring",
        phrase="Laurel Spring",
        image="Laurel leaves flashed silver-green, and the water whispered under a low arch of roots.",
        water="the spring",
        snag_spot="the running water",
        allowed_helpers={"crook", "pole"},
        tags={"spring", "friendship"},
    ),
    "reed_ford": Place(
        id="reed_ford",
        label="Reed Ford",
        phrase="Reed Ford",
        image="Tall reeds leaned over the shallows, and the river carried a hush that sounded almost like breathing.",
        water="the ford",
        snag_spot="the slow dark current",
        allowed_helpers={"pole", "ladder"},
        tags={"spring", "friendship"},
    ),
}

SNAGS = {
    "garland": Snag(
        id="garland",
        label="the laurel garland",
        phrase="a laurel garland meant for the village feast",
        attached_to="a pale hanging root",
        risk_text="the root will shake and the garland may fall into the water",
        ending_image="green leaves shining in safe hands",
        weight=1,
        height=1,
        fragile=True,
        tags={"garland", "patience"},
    ),
    "lamp": Snag(
        id="lamp",
        label="the bronze lamp",
        phrase="a bronze lamp left from an old shrine",
        attached_to="a fork of roots and stone",
        risk_text="the heavy lamp will swing loose and drag everything after it",
        ending_image="a warm bronze glow under the evening sky",
        weight=3,
        height=2,
        fragile=False,
        tags={"lamp", "patience"},
    ),
    "flute": Snag(
        id="flute",
        label="the reed flute",
        phrase="a reed flute tied with faded blue thread",
        attached_to="a curling vine",
        risk_text="the thread may snap and the flute may vanish below",
        ending_image="a thin note rising over the water",
        weight=1,
        height=2,
        fragile=True,
        tags={"flute", "patience"},
    ),
}

HELPERS = {
    "crook": Helper(
        id="crook",
        label="shepherd's crook",
        phrase="the shepherd's crook resting beside a shrine wall",
        sense=3,
        reach=2,
        lift=2,
        gentle=True,
        method="We can catch the root and lift the prize instead of jerking it.",
        success_text="Using the crook's curved end, the two friends raised the snagged thing a finger-width at a time until the root let go.",
        fail_text="They tried to guide it with the crook, but the pull from below was too heavy, and the hook slid away at the worst moment.",
        qa_text="They used a shepherd's crook to lift it gently free.",
        tags={"crook", "friendship", "patience"},
    ),
    "ladder": Helper(
        id="ladder",
        label="ladder",
        phrase="an old fig-wood ladder left for shrine keepers",
        sense=2,
        reach=3,
        lift=3,
        gentle=True,
        method="One of us can steady the ladder while the other frees it carefully.",
        success_text="They set the ladder with care, one friend holding the feet while the other climbed just high enough to loosen the snag by hand.",
        fail_text="They set the ladder in a hurry, but the wind worried the branches, and before the climber could reach it, the prize slipped away.",
        qa_text="They used a ladder so one friend could reach it while the other steadied below.",
        tags={"ladder", "friendship", "patience"},
    ),
    "pole": Helper(
        id="pole",
        label="ferry pole",
        phrase="the long ferry pole tied near the bank",
        sense=2,
        reach=3,
        lift=2,
        gentle=False,
        method="We can nudge the vine from below and guide it toward shore.",
        success_text="Together they pushed with the pole in tiny careful touches, guiding the hanging thing away from the water until it came within reach.",
        fail_text="The pole could reach, but it was too rough for the shaking moment, and one hard nudge sent the prize spinning into the water.",
        qa_text="They used a long pole to guide it toward shore.",
        tags={"pole", "friendship"},
    ),
    "jump": Helper(
        id="jump",
        label="jumping for it",
        phrase="their own quick legs",
        sense=1,
        reach=1,
        lift=1,
        gentle=False,
        method="If we leap fast enough, maybe speed will be enough.",
        success_text="They leaped and somehow caught it.",
        fail_text="They jumped, but speed only made the danger worse.",
        qa_text="They tried to jump for it.",
        tags={"patience"},
    ),
}

GIRL_NAMES = ["Iria", "Thalea", "Mira", "Daphne", "Nysa", "Eleni", "Rhea", "Lysa"]
BOY_NAMES = ["Niko", "Damon", "Ivo", "Leandros", "Theo", "Panos", "Ari", "Milos"]
TRAITS = ["steady", "patient", "wise", "careful", "curious", "bright"]


@dataclass
class StoryParams:
    place: str
    snag: str
    helper: str
    instigator_name: str
    instigator_type: str
    friend_name: str
    friend_type: str
    trait: str
    gust: int = 0
    instigator_age: int = 6
    friend_age: int = 6
    trust: int = 7
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
        place="moon_well",
        snag="garland",
        helper="crook",
        instigator_name="Niko",
        instigator_type="boy",
        friend_name="Iria",
        friend_type="girl",
        trait="steady",
        gust=0,
        instigator_age=6,
        friend_age=7,
        trust=8,
    ),
    StoryParams(
        place="laurel_spring",
        snag="flute",
        helper="crook",
        instigator_name="Mira",
        instigator_type="girl",
        friend_name="Theo",
        friend_type="boy",
        trait="patient",
        gust=0,
        instigator_age=7,
        friend_age=6,
        trust=5,
    ),
    StoryParams(
        place="reed_ford",
        snag="lamp",
        helper="ladder",
        instigator_name="Ari",
        instigator_type="boy",
        friend_name="Rhea",
        friend_type="girl",
        trait="wise",
        gust=0,
        instigator_age=6,
        friend_age=6,
        trust=6,
    ),
    StoryParams(
        place="reed_ford",
        snag="lamp",
        helper="pole",
        instigator_name="Daphne",
        instigator_type="girl",
        friend_name="Milos",
        friend_type="boy",
        trait="careful",
        gust=1,
        instigator_age=6,
        friend_age=5,
        trust=4,
    ),
    StoryParams(
        place="moon_well",
        snag="flute",
        helper="ladder",
        instigator_name="Thalea",
        instigator_type="girl",
        friend_name="Ivo",
        friend_type="boy",
        trait="bright",
        gust=0,
        instigator_age=7,
        friend_age=7,
        trust=3,
    ),
]


def pair_word(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    instigator = f["instigator"]
    friend = f["friend"]
    snag = f["snag_cfg"]
    place = f["place_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth-like story for a 3-to-5-year-old about friendship and suspense. '
        f'Include the word "pull" and set it at {place.phrase}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a myth-colored story where {instigator.id} wants to pull {snag.label} free, but {friend.id} warns {instigator.pronoun('object')} in time and the two friends solve it together.",
            f"Write a gentle suspense story with inner monologue where a child almost makes a quick choice, trusts a friend instead, and ends with both friends carrying something precious home.",
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a sad but child-safe myth story where {instigator.id} gives in to the urge to pull, the precious object is lost to the water, and friendship matters more than the lost thing.",
            f"Write a suspenseful story with inner thoughts, a dangerous quick choice, and an ending where the friends stay kind to each other after a mistake.",
        ]
    return [
        base,
        f"Tell a myth-like story where {instigator.id} is tempted to pull {snag.label} free above dark water, and {friend.id} helps save it with a wiser plan.",
        f"Write a suspenseful friendship story with inner monologue and a bright ending image that proves the friends learned to move slowly together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    instigator = f["instigator"]
    friend = f["friend"]
    place = f["place_cfg"]
    snag = f["snag_cfg"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(instigator, friend)}, {instigator.id} and {friend.id}, at {place.phrase}. They face a tense moment together and stay friends through it.",
        ),
        (
            f"What was caught above the water?",
            f"It was {snag.phrase}. It hung above {place.snag_spot}, which is why the moment felt risky right away.",
        ),
        (
            f"Why did {friend.id} tell {instigator.id} not to pull it?",
            f"{friend.id} could see that a hard pull might make everything shake and send {snag.label} into the water. The warning came from noticing the root, the height, and the dark water below.",
        ),
    ]
    if f["attempted_pull"]:
        qa.append(
            (
                f"What happened when {instigator.id} tried to pull?",
                f"The place seemed to hold its breath, and then the water gave a low sound while {snag.label} swayed. That moment showed the friend was right to worry, because the pull made the danger real.",
            )
        )
    else:
        qa.append(
            (
                f"What did {instigator.id} do after hearing the warning?",
                f"{instigator.id} stopped and trusted {friend.id} instead of the quick idea in {instigator.pronoun('possessive')} head. That choice changed the whole story from a dangerous moment into a shared plan.",
            )
        )
    if outcome in {"averted", "recovered"}:
        qa.append(
            (
                f"How did the friends save {snag.label}?",
                f"{friend.id} suggested a wiser plan, and together they used {helper.phrase if helper.phrase.startswith('the ') else helper.label}. {helper.qa_text} Because they worked slowly together, the precious thing ended up safe instead of lost.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the friends still side by side and {snag.ending_image}. The ending proves they learned that friendship and patience are stronger than one quick pull.",
            )
        )
    else:
        qa.append(
            (
                f"Did the friends keep {snag.label}?",
                f"No. It slipped into {place.water} and was lost. Even so, the friends stayed together, and that became more important than the lost object.",
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that being fast is not the same as being wise. They also learned that a good friend tells the truth in a scary moment and stays beside you afterward.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["place_cfg"].tags) | set(f["snag_cfg"].tags) | set(f["helper"].tags) | {"friendship"}
    if f["helper"].id in {"crook", "ladder"} or f["snag_cfg"].id in {"garland", "lamp", "flute"}:
        tags.add("patience")
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
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, snag: Snag, helper: Helper) -> str:
    if helper.id not in place.allowed_helpers:
        allowed = ", ".join(sorted(place.allowed_helpers))
        return (
            f"(No story: {helper.label} does not belong at {place.phrase}. "
            f"Pick a helper the place could honestly offer, such as {allowed}.)"
        )
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: '{helper.id}' is known to the world but refused because it is too rash "
            f"for a child-facing story. Choose a steadier helper.)"
        )
    if helper.reach < snag.height:
        return (
            f"(No story: {helper.label} cannot reach {snag.label}. "
            f"The rescue must actually reach the snagged object.)"
        )
    if helper.lift < snag.weight:
        return (
            f"(No story: {helper.label} is too weak for {snag.label}. "
            f"The safer plan must be strong enough to work.)"
        )
    if snag.fragile and not helper.gentle:
        return (
            f"(No story: {snag.label} is fragile, and {helper.label} is too rough for it. "
            f"Use a gentler method.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
valid(P,S,H) :- place(P), snag(S), helper(H),
                offered(P,H), sensible(H), reaches(H,S), lifts(H,S), gentle_enough(H,S).

sensible(H) :- helper(H), sense(H,V), sense_min(M), V >= M.
reaches(H,S) :- helper(H), snag(S), reach(H,R), height(S,Ht), R >= Ht.
lifts(H,S) :- helper(H), snag(S), lift(H,L), weight(S,W), L >= W.
gentle_enough(H,S) :- helper(H), snag(S), not fragile(S).
gentle_enough(H,S) :- helper(H), snag(S), fragile(S), gentle(H).

authority(C + 1 + A + T) :- init_caution(C), age_bonus(A), trust_bonus(T).
init_caution(5) :- chosen_trait(T), steady_trait(T).
init_caution(3) :- chosen_trait(T), not steady_trait(T).
age_bonus(1) :- friend_age(A), A >= 6.
age_bonus(0) :- friend_age(A), A < 6.
trust_bonus(1) :- trust(V), V >= 7.
trust_bonus(0) :- trust(V), V < 7.
averted :- authority(A), impulse_init(I), A > I.

severity(W + G) :- chosen_snag(S), weight(S,W), gust(G).
contained :- chosen_helper(H), chosen_snag(S), lift(H,L), reach(H,R), weight(S,W), height(S,Ht), severity(V), L >= V, R >= Ht.

outcome(averted) :- averted.
outcome(recovered) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for helper_id in sorted(place.allowed_helpers):
            lines.append(asp.fact("offered", place_id, helper_id))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("weight", snag_id, snag.weight))
        lines.append(asp.fact("height", snag_id, snag.height))
        if snag.fragile:
            lines.append(asp.fact("fragile", snag_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        lines.append(asp.fact("reach", helper_id, helper.reach))
        lines.append(asp.fact("lift", helper_id, helper.lift))
        if helper.gentle:
            lines.append(asp.fact("gentle", helper_id))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_snag", params.snag),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_trait", params.trait),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trust", params.trust),
            asp.fact("gust", params.gust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.friend_age, params.trust, params.trait):
        return "averted"
    helper = HELPERS[params.helper]
    snag = SNAGS[params.snag]
    return "recovered" if helper_succeeds(helper, snag, params.gust) else "lost"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome comparisons failed.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like storyworld: two friends, a dangerous pull, and a wiser shared plan."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gust", type=int, choices=[0, 1, 2], help="extra difficulty from wind or shaking")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.snag and args.helper:
        place = PLACES[args.place]
        snag = SNAGS[args.snag]
        helper = HELPERS[args.helper]
        if not helper_fits(place, snag, helper):
            raise StoryError(explain_rejection(place, snag, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.snag is None or combo[1] == args.snag)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, snag_id, helper_id = rng.choice(sorted(combos))
    instigator_name, instigator_type = _pick_child(rng)
    friend_name, friend_type = _pick_child(rng, avoid=instigator_name)
    trait = rng.choice(TRAITS)
    gust = args.gust if args.gust is not None else rng.randint(0, 2)
    instigator_age = rng.randint(5, 7)
    friend_age = rng.randint(5, 7)
    trust = rng.randint(3, 9)
    return StoryParams(
        place=place_id,
        snag=snag_id,
        helper=helper_id,
        instigator_name=instigator_name,
        instigator_type=instigator_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
        gust=gust,
        instigator_age=instigator_age,
        friend_age=friend_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    place = PLACES[params.place]
    snag = SNAGS[params.snag]
    helper = HELPERS[params.helper]
    if not helper_fits(place, snag, helper):
        raise StoryError(explain_rejection(place, snag, helper))

    world = tell(
        place=place,
        snag=snag,
        helper=helper,
        instigator_name=params.instigator_name,
        instigator_type=params.instigator_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        trait=params.trait,
        gust=params.gust,
        instigator_age=params.instigator_age,
        friend_age=params.friend_age,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, snag, helper) combos:\n")
        for place_id, snag_id, helper_id in combos:
            print(f"  {place_id:13} {snag_id:8} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator_name} and {p.friend_name}: {p.snag} at {p.place} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
