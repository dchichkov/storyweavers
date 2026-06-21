#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slump_foreshadowing_misunderstanding_kindness_rhyming_story.py

A standalone story world about a child who sees another child in a slump,
misunderstands the reason, and then uses kindness to help.

The model keeps a small live world with physical meters and emotional memes.
A visible slump is caused by an underlying need such as hunger, cold, or
tiredness. Another child first misreads the slump, then asks gently, and a
matching kind act helps. The prose is rendered from state, not from slot-filling,
and keeps a soft rhyming-story feel.

Run it
------
    python storyworlds/worlds/gpt-5.4/slump_foreshadowing_misunderstanding_kindness_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/slump_foreshadowing_misunderstanding_kindness_rhyming_story.py --qa
    python storyworlds/worlds/gpt-5.4/slump_foreshadowing_misunderstanding_kindness_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/slump_foreshadowing_misunderstanding_kindness_rhyming_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    meter: str
    clue: str
    early_image: str
    truth_line: str
    fix_need: str
    base_severity: int
    help_noun: str
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
class Misread:
    id: str
    guess: str
    thought: str
    question: str
    plausible_for: set[str] = field(default_factory=set)
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
class Kindness:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    helps: set[str] = field(default_factory=set)
    warm_line: str = ""
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
        self.facts: dict = {
            "clarified": False,
            "kindness_offered": False,
            "kindness_matched": False,
            "outcome": "",
            "initial_guess": "",
            "adult_called": False,
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


def _r_slump(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    need_total = friend.meters["hunger"] + friend.meters["chill"] + friend.meters["fatigue"]
    if need_total >= THRESHOLD:
        sig = ("slump", friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.meters["slump"] += 1
            friend.memes["gloom"] += 1
            out.append("__slump__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    observer = world.get("observer")
    friend = world.get("friend")
    if friend.meters["slump"] >= THRESHOLD and observer.attrs.get("misread") and not world.facts["clarified"]:
        sig = ("worry", observer.id, observer.attrs["misread"])
        if sig not in world.fired:
            world.fired.add(sig)
            observer.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slump", tag="physical", apply=_r_slump),
    Rule(name="worry", tag="emotional", apply=_r_worry),
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


def place_supports(place: Place, cause: Cause) -> bool:
    return cause.id in place.affords


def plausible_misread(cause: Cause, misread: Misread) -> bool:
    return cause.id in misread.plausible_for


def kindness_matches(cause: Cause, kindness: Kindness) -> bool:
    return cause.id in kindness.helps


def severity_of(cause: Cause, delay: int) -> int:
    return cause.base_severity + delay


def outcome_of(params: "StoryParams") -> str:
    cause = CAUSES[params.cause]
    kindness = KINDNESSES[params.kindness]
    sev = severity_of(cause, params.delay)
    return "bright" if kindness.power >= sev else "gentle"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for cause_id, cause in CAUSES.items():
            if not place_supports(place, cause):
                continue
            for misread_id, misread in MISREADS.items():
                if not plausible_misread(cause, misread):
                    continue
                for kindness_id, kindness in KINDNESSES.items():
                    if kindness_matches(cause, kindness):
                        combos.append((place_id, cause_id, misread_id, kindness_id))
    return combos


def explain_place(place: Place, cause: Cause) -> str:
    return (
        f"(No story: {cause.id} does not fit {place.label} here, so the slump would "
        f"not feel grounded. Try a place that honestly affords that need.)"
    )


def explain_misread(cause: Cause, misread: Misread) -> str:
    return (
        f"(No story: reading the slump as {misread.guess} does not make sense for a "
        f"{cause.id} clue in this little world. Pick a misunderstanding the visible "
        f"clue could honestly invite.)"
    )


def explain_kindness(cause: Cause, kindness: Kindness) -> str:
    return (
        f"(No story: {kindness.label} is kind, but it does not directly help with "
        f"{cause.id} here. Pick a kind act that matches the real need.)"
    )


def foreshadow(world: World, observer: Entity, friend: Entity, cause: Cause) -> None:
    observer.memes["care"] += 1
    world.say(
        f"In {world.place.label}, the light was thin and slow, and {cause.early_image}."
    )
    world.say(
        f"{observer.id} came skipping with a hum and a hop, but then {observer.pronoun()} saw "
        f"{friend.id} on the bench in a little slump-stop."
    )


def introduce_slump(world: World, friend: Entity, cause: Cause) -> None:
    friend.attrs["true_cause"] = cause.id
    friend.meters[cause.meter] += float(cause.base_severity)
    propagate(world, narrate=False)
    world.say(
        f"{friend.id}'s shoulders had folded, small as a clump, "
        f"and {friend.pronoun('possessive')} smile had slipped to a slump."
    )
    world.say(cause.clue)


def misunderstand(world: World, observer: Entity, friend: Entity, misread: Misread) -> None:
    observer.attrs["misread"] = misread.id
    world.facts["initial_guess"] = misread.guess
    propagate(world, narrate=False)
    observer.memes["distance"] += 1
    world.say(
        f"{observer.id} paused by the daisies and gave one tiny blink. "
        f'{misread.thought}'
    )


def ask_gently(world: World, observer: Entity, friend: Entity, misread: Misread) -> None:
    observer.memes["kindness"] += 1
    world.say(
        f"But kindness tapped softly and changed {observer.pronoun('possessive')} plan. "
        f'{misread.question}'
    )


def clarify(world: World, observer: Entity, friend: Entity, cause: Cause) -> None:
    world.facts["clarified"] = True
    friend.memes["trust"] += 1
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head. "
        f'"No," {friend.pronoun()} said, "{cause.truth_line}"'
    )
    world.say(
        f"At once the wrong worry drifted out of the air, "
        f"for the slump was from {cause.fix_need}, not from a quarrel to share."
    )


def offer_kindness(world: World, observer: Entity, friend: Entity, kindness: Kindness, cause: Cause) -> None:
    world.facts["kindness_offered"] = True
    matched = kindness_matches(cause, kindness)
    world.facts["kindness_matched"] = matched
    observer.memes["generosity"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"Then {observer.id} came closer and spoke warm and light: "
        f'"Here is {kindness.phrase}. {kindness.warm_line}"'
    )
    if matched:
        friend.meters[cause.meter] = max(0.0, friend.meters[cause.meter] - kindness.power)
        if friend.meters[cause.meter] < THRESHOLD:
            friend.meters["slump"] = 0.0
            friend.memes["gloom"] = 0.0
        friend.memes["relief"] += 1
        friend.memes["friendship"] += 1
        observer.memes["friendship"] += 1
    else:
        friend.memes["comforted"] += 1


def adult_help(world: World, adult: Entity, friend: Entity, cause: Cause) -> None:
    world.facts["adult_called"] = True
    friend.meters[cause.meter] = 0.0
    friend.meters["slump"] = 0.0
    friend.memes["gloom"] = 0.0
    friend.memes["relief"] += 1
    adult.memes["care"] += 1
    world.say(
        f"Soon {adult.label_word} came over with a careful hand and helped with the last little bit, just as kindly as planned."
    )


def bright_ending(world: World, observer: Entity, friend: Entity, kindness: Kindness, cause: Cause) -> None:
    world.facts["outcome"] = "bright"
    world.say(
        f"{friend.id} took {kindness.help_noun if hasattr(kindness, 'help_noun') else kindness.label}, "
        f"and little by little the ache grew slight."
    )
    world.say(
        f"The slump uncurled, the bench felt bright, and two small friends went on their way with a lighter step and kinder sight."
    )


def gentle_ending(world: World, observer: Entity, friend: Entity, adult: Entity, kindness: Kindness, cause: Cause) -> None:
    world.facts["outcome"] = "gentle"
    world.say(
        f"{friend.id} smiled a little, though not quite tall. "
        f"The kind act helped first, but it could not fix all."
    )
    adult_help(world, adult, friend, cause)
    world.say(
        f"Then {friend.id}'s eyes shone brighter than before, "
        f"and {observer.id} learned what kind questions are for."
    )


def tell(
    place: Place,
    cause: Cause,
    misread: Misread,
    kindness: Kindness,
    *,
    observer_name: str = "Mia",
    observer_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    adult_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(place=place)
    observer = world.add(Entity(id=observer_name, kind="character", type=observer_gender, role="observer"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))

    observer.attrs["misread"] = ""
    friend.attrs["true_cause"] = cause.id
    friend.meters["hunger"] = 0.0
    friend.meters["chill"] = 0.0
    friend.meters["fatigue"] = 0.0
    friend.meters["slump"] = 0.0
    friend.memes["gloom"] = 0.0
    friend.memes["trust"] = 0.0
    friend.memes["hope"] = 0.0
    friend.memes["relief"] = 0.0
    observer.memes["care"] = 0.0
    observer.memes["worry"] = 0.0
    observer.memes["kindness"] = 0.0

    foreshadow(world, observer, friend, cause)
    introduce_slump(world, friend, cause)

    if delay > 0:
        friend.meters[cause.meter] += float(delay)
        if friend.meters[cause.meter] >= THRESHOLD:
            friend.meters["slump"] = 1.0
        world.say(
            f"Each minute that fluttered by made the trouble bump, "
            f"and deeper still sank that quiet little slump."
        )

    world.para()
    misunderstand(world, observer, friend, misread)
    ask_gently(world, observer, friend, misread)
    clarify(world, observer, friend, cause)

    world.para()
    offer_kindness(world, observer, friend, kindness, cause)
    if kindness.power >= severity_of(cause, delay):
        friend.meters[cause.meter] = 0.0
        friend.meters["slump"] = 0.0
        bright_ending(world, observer, friend, kindness, cause)
    else:
        gentle_ending(world, observer, friend, adult, kindness, cause)

    world.facts.update(
        place=place,
        cause=cause,
        misread=misread,
        kindness=kindness,
        observer=observer,
        friend=friend,
        adult=adult,
        delay=delay,
        severity=severity_of(cause, delay),
    )
    return world


PLACES = {
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        scene="a bench near the hopscotch squares",
        affords={"hungry", "tired"},
        tags={"schoolyard"},
    ),
    "park": Place(
        id="park",
        label="the park",
        scene="a bench near the duck pond",
        affords={"hungry", "cold", "tired"},
        tags={"park"},
    ),
    "bus_stop": Place(
        id="bus_stop",
        label="the bus stop",
        scene="a bench beside a windy sign",
        affords={"cold", "tired"},
        tags={"bus_stop"},
    ),
}

CAUSES = {
    "hungry": Cause(
        id="hungry",
        meter="hunger",
        clue="Beside one shoe sat an untouched bun, and the noon bell song had already been sung.",
        early_image="a lunch napkin skittered like a pale little kite",
        truth_line="I am not cross. I just missed my snack, and my tummy feels hollow and whack.",
        fix_need="a hungry belly",
        base_severity=1,
        help_noun="the shared snack",
        tags={"hungry", "food"},
    ),
    "cold": Cause(
        id="cold",
        meter="chill",
        clue="A breeze kept tugging at the ends of a sleeve, and the bench felt colder than anyone would believe.",
        early_image="the wind kept worrying the leaves in the trees",
        truth_line="I am not upset. I am cold clear through, and my hands feel stiff as dew.",
        fix_need="the cold",
        base_severity=1,
        help_noun="the warm scarf",
        tags={"cold", "warmth"},
    ),
    "tired": Cause(
        id="tired",
        meter="fatigue",
        clue="A yawn slipped out like a boat on a stream, and heavy eyes blinked at the edge of a dream.",
        early_image="the clouds moved slowly, as if ready for a nap",
        truth_line="I am not angry. I am only worn out, and my feet lost their bounce on the route.",
        fix_need="plain tiredness",
        base_severity=2,
        help_noun="the quiet rest",
        tags={"tired", "rest"},
    ),
}

MISREADS = {
    "mad": Misread(
        id="mad",
        guess="angry",
        thought='"Oh dear," thought {observer}, "perhaps {friend} is mad, and maybe I did something silly or bad."',
        question='"Did I hurt your feelings?" {observer} asked with care. "If I did, I am sorry. I can listen right here."',
        plausible_for={"hungry", "tired"},
        tags={"feelings"},
    ),
    "shy": Misread(
        id="shy",
        guess="shy",
        thought='"Maybe {friend} feels shy today," thought {observer}, "and words are hiding away."',
        question='"Would you like quiet company?" {observer} asked in a tone small and mild. "I can sit beside you a while."',
        plausible_for={"cold", "tired"},
        tags={"feelings"},
    ),
    "bored": Misread(
        id="bored",
        guess="bored",
        thought='"Maybe this bench and this breeze feel dull," thought {observer}, "and the whole afternoon feels wool."',
        question='"Are you tired of the game?" {observer} asked with a tilt of the head. "We can try something gentle instead."',
        plausible_for={"cold", "hungry"},
        tags={"feelings"},
    ),
}

KINDNESSES = {
    "share_snack": Kindness(
        id="share_snack",
        label="shared snack",
        phrase="half my pear and a cracker to nibble",
        action="shared a snack",
        power=2,
        helps={"hungry"},
        warm_line="Let us crunch a small lunch and make the world less wibbly.",
        tags={"food"},
    ),
    "wrap_scarf": Kindness(
        id="wrap_scarf",
        label="warm scarf",
        phrase="my soft scarf for your chilly neck",
        action="wrapped a scarf around those chilly shoulders",
        power=2,
        helps={"cold"},
        warm_line="A warm little wrap can chase off the shiver.",
        tags={"warmth"},
    ),
    "sit_and_rest": Kindness(
        id="sit_and_rest",
        label="quiet rest",
        phrase="a quiet minute with me on the bench",
        action="sat close and gave quiet rest",
        power=2,
        helps={"tired"},
        warm_line="We do not have to dash. We can rest for a bit.",
        tags={"rest"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella", "Zoe", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Finn", "Theo", "Eli", "Noah"]


@dataclass
class StoryParams:
    place: str
    cause: str
    misread: str
    kindness: str
    observer: str
    observer_gender: str
    friend: str
    friend_gender: str
    adult: str
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


CURATED = [
    StoryParams(
        place="park",
        cause="hungry",
        misread="bored",
        kindness="share_snack",
        observer="Mia",
        observer_gender="girl",
        friend="Ben",
        friend_gender="boy",
        adult="mother",
        delay=0,
    ),
    StoryParams(
        place="bus_stop",
        cause="cold",
        misread="shy",
        kindness="wrap_scarf",
        observer="Leo",
        observer_gender="boy",
        friend="Nora",
        friend_gender="girl",
        adult="father",
        delay=1,
    ),
    StoryParams(
        place="schoolyard",
        cause="tired",
        misread="mad",
        kindness="sit_and_rest",
        observer="Ella",
        observer_gender="girl",
        friend="Sam",
        friend_gender="boy",
        adult="mother",
        delay=0,
    ),
    StoryParams(
        place="park",
        cause="tired",
        misread="shy",
        kindness="sit_and_rest",
        observer="Theo",
        observer_gender="boy",
        friend="Ruby",
        friend_gender="girl",
        adult="father",
        delay=1,
    ),
    StoryParams(
        place="park",
        cause="tired",
        misread="mad",
        kindness="sit_and_rest",
        observer="Anna",
        observer_gender="girl",
        friend="Finn",
        friend_gender="boy",
        adult="mother",
        delay=2,
    ),
]


KNOWLEDGE = {
    "hungry": [
        (
            "What can happen when someone misses a snack?",
            "Their belly can feel empty and wobbly, and they may seem droopy or quiet. Hunger changes how a body feels, even when no one is upset."
        )
    ],
    "cold": [
        (
            "Why can cold weather make someone hunch or slump?",
            "When a person feels cold, they often curl in and hold themselves tight to keep warm. That can make them look smaller and quieter."
        )
    ],
    "tired": [
        (
            "What does being tired do to your body?",
            "Being tired can make your eyes heavy, your legs slow, and your shoulders droop. Rest helps your body get its bounce back."
        )
    ],
    "food": [
        (
            "Why can sharing food be a kind thing?",
            "If someone is hungry and it is safe to share, a small snack can help their body feel steadier. It also shows you noticed their need."
        )
    ],
    "warmth": [
        (
            "How does a scarf help when someone is cold?",
            "A scarf helps hold warmth close to the neck and chest, so chilly air does not bite as much. Warmth can help a cold body relax."
        )
    ],
    "rest": [
        (
            "Why is resting kind when someone is tired?",
            "A tired body does not always need more noise or speed. A quiet rest gives it time to settle and feel stronger again."
        )
    ],
    "feelings": [
        (
            "Why is it good to ask before guessing how someone feels?",
            "Faces and posture can be hard to read. Asking gently helps you learn what is really wrong instead of guessing the wrong thing."
        )
    ],
}
KNOWLEDGE_ORDER = ["feelings", "hungry", "cold", "tired", "food", "warmth", "rest"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    observer = f["observer"]
    friend = f["friend"]
    cause = f["cause"]
    misread = f["misread"]
    kindness = f["kindness"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "slump" and shows a misunderstanding turning into kindness.',
        f"Tell a gentle story in rhyme where {observer.id} sees {friend.id} in a slump, guesses {misread.guess}, and then learns the real problem is {cause.id}.",
        f"Write a child-facing poem-story where a small kind act like {kindness.label} helps after someone asks a caring question instead of making a harsh guess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    observer = f["observer"]
    friend = f["friend"]
    cause = f["cause"]
    misread = f["misread"]
    kindness = f["kindness"]
    adult = f["adult"]
    outcome = f["outcome"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {observer.id} and {friend.id} in {place.label}. {observer.id} notices {friend.id}'s slump and tries to understand it."
        ),
        (
            f"Why did {friend.id} look slumped at first?",
            f"{friend.id} was not slumped because of a quarrel. {friend.pronoun().capitalize()} was dealing with {cause.fix_need}, and that physical need made {friend.pronoun('possessive')} shoulders droop."
        ),
        (
            f"What did {observer.id} misunderstand?",
            f"{observer.id} first thought {friend.id} might be {misread.guess}. The slump looked like a feeling problem, but it was really caused by {cause.id}."
        ),
        (
            f"How did {observer.id} show kindness?",
            f"{observer.id} asked gently instead of stomping away, and then offered {kindness.label}. That was kind because it matched what {friend.id} truly needed."
        ),
    ]
    if outcome == "bright":
        qa.append(
            (
                "How did the problem get solved?",
                f"The kind act was strong enough to help right away, so the slump lifted and the day felt brighter again. {friend.id}'s body felt better, and the misunderstanding disappeared too."
            )
        )
    else:
        qa.append(
            (
                "Did the first kind act fix everything at once?",
                f"Not quite. The first kindness helped and made {friend.id} feel less alone, and then {adult.label_word} helped with the rest because the need had grown bigger."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["cause"].tags) | set(f["misread"].tags) | set(f["kindness"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(parts)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def render_thought(template: str, observer: Entity, friend: Entity) -> str:
    return template.format(observer=observer.id, friend=friend.id)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a visible slump, a misunderstanding, and kindness in a rhyming style."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--misread", choices=sorted(MISREADS))
    ap.add_argument("--kindness", choices=sorted(KINDNESSES))
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the need grows before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not place_supports(place, cause):
            raise StoryError(explain_place(place, cause))
    if args.cause and args.misread:
        cause = CAUSES[args.cause]
        misread = MISREADS[args.misread]
        if not plausible_misread(cause, misread):
            raise StoryError(explain_misread(cause, misread))
    if args.cause and args.kindness:
        cause = CAUSES[args.cause]
        kindness = KINDNESSES[args.kindness]
        if not kindness_matches(cause, kindness):
            raise StoryError(explain_kindness(cause, kindness))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
        and (args.misread is None or combo[2] == args.misread)
        and (args.kindness is None or combo[3] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause, misread, kindness = rng.choice(sorted(combos))
    observer, observer_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=observer)
    adult = args.adult or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        cause=cause,
        misread=misread,
        kindness=kindness,
        observer=observer,
        observer_gender=observer_gender,
        friend=friend,
        friend_gender=friend_gender,
        adult=adult,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        cause = CAUSES[params.cause]
        misread = MISREADS[params.misread]
        kindness = KINDNESSES[params.kindness]
    except KeyError as exc:
        raise StoryError(f"(No story: invalid parameter value: {exc.args[0]})") from None

    if not place_supports(place, cause):
        raise StoryError(explain_place(place, cause))
    if not plausible_misread(cause, misread):
        raise StoryError(explain_misread(cause, misread))
    if not kindness_matches(cause, kindness):
        raise StoryError(explain_kindness(cause, kindness))

    world = tell(
        place=place,
        cause=cause,
        misread=misread,
        kindness=kindness,
        observer_name=params.observer,
        observer_gender=params.observer_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        delay=params.delay,
    )

    observer = world.facts["observer"]
    friend = world.facts["friend"]
    misread_obj = world.facts["misread"]
    # Late formatting uses live names from the generated world.
    story = world.render().replace(
        MISREADS[misread_obj.id].thought,
        render_thought(MISREADS[misread_obj.id].thought, observer, friend),
    ).replace(
        MISREADS[misread_obj.id].question,
        render_thought(MISREADS[misread_obj.id].question, observer, friend),
    )

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


ASP_RULES = r"""
place_supports(P,C) :- affords(P,C).
plausible(C,M) :- misread(M), cause(C), invites(M,C).
helps(K,C) :- kindness(K), kind_for(K,C).

valid(P,C,M,K) :- place(P), cause(C), misread(M), kindness(K),
                  place_supports(P,C), plausible(C,M), helps(K,C).

severity(S) :- chosen_cause(C), base_severity(C,B), delay(D), S = B + D.
bright :- chosen_kindness(K), power(K,P), severity(S), P >= S.
gentle :- chosen_kindness(K), power(K,P), severity(S), P < S.

outcome(bright) :- bright.
outcome(gentle) :- gentle.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cause_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("base_severity", cause_id, cause.base_severity))
    for misread_id, misread in MISREADS.items():
        lines.append(asp.fact("misread", misread_id))
        for cause_id in sorted(misread.plausible_for):
            lines.append(asp.fact("invites", misread_id, cause_id))
    for kindness_id, kindness in KINDNESSES.items():
        lines.append(asp.fact("kindness", kindness_id))
        lines.append(asp.fact("power", kindness_id, kindness.power))
        for cause_id in sorted(kindness.helps):
            lines.append(asp.fact("kind_for", kindness_id, cause_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_kindness", params.kindness),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected random resolution failure at seed {s}.")
            break
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke_sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke generation and emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause, misread, kindness) combos:\n")
        for place, cause, misread, kindness in combos:
            print(f"  {place:10} {cause:7} {misread:6} {kindness}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.observer} sees {p.friend} in a slump ({p.place}, {p.cause}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
