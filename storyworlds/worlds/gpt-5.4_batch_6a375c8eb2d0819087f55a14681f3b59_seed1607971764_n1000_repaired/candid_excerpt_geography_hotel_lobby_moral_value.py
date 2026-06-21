#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py
================================================================================

A standalone story world for a tiny hotel-lobby tale in a playful, cautionary
style: two children turn a hotel lobby into an adventure, need a map for their
pretend quest, and face a moral choice about taking something that is not theirs.

This world is built around a simple value-centered premise:
    wanting something for play -> temptation to take or damage shared property
    -> warning from a friend/sibling -> choice
    -> candid honesty and repair, or a smaller sad consequence if honesty is delayed.

The seed words appear naturally in the story world:
- candid
- excerpt
- geography

Run it
------
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py --source atlas --response confess
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py --source sculpture
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py --json
    python storyworlds/worlds/gpt-5.4/candid_excerpt_geography_hotel_lobby_moral_value.py --verify
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
URGE_INIT = 6.0
HONEST_TRAITS = {"candid", "careful", "truthful", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    public_item: bool = False
    map_source: bool = False
    tearable: bool = False
    copyable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    age: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "clerk_woman"}
        male = {"boy", "father", "man", "clerk_man"}
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
            "clerk_woman": "clerk",
            "clerk_man": "clerk",
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
class Theme:
    id: str
    scene: str
    rig: str
    leader: str
    mate: str
    goal: str
    route: str
    role_solo: str
    role_plural: str
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
class SourceItem:
    id: str
    label: str
    phrase: str
    owner: str
    place: str
    excerpt: str
    geography_word: str
    map_source: bool = True
    public_item: bool = True
    tearable: bool = True
    copyable: bool = True
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
class DecoyItem:
    id: str
    label: str
    phrase: str
    owner: str
    place: str
    map_source: bool = False
    public_item: bool = True
    tearable: bool = False
    copyable: bool = False
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
    honest: bool
    repair: bool
    text: str
    ending: str
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
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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


def _r_damage_distress(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("source")
    if item is None or item.meters["damaged"] < THRESHOLD:
        return out
    sig = ("damage_distress", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lobby = world.get("lobby")
    lobby.meters["trouble"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__damage__")
    return out


def _r_confession_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("source")
    if item is None:
        return out
    if item.meters["damaged"] < THRESHOLD:
        return out
    teller = world.get("instigator")
    helper = world.get("clerk")
    if teller.memes["confessed"] < THRESHOLD:
        return out
    sig = ("confession_relief", teller.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    teller.memes["relief"] += 1
    helper.memes["trust"] += 1
    world.get("cautioner").memes["relief"] += 1
    out.append("__confessed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_distress", tag="physical", apply=_r_damage_distress),
    Rule(name="confession_relief", tag="social", apply=_r_confession_relief),
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


def source_is_usable(item: SourceItem | DecoyItem) -> bool:
    return item.map_source and item.public_item and item.tearable and item.copyable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_honesty(trait: str) -> float:
    return 5.0 if trait in HONEST_TRAITS else 3.0


def would_ask_first(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_honesty(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > URGE_INIT


def predict_damage(world: World) -> dict:
    sim = world.copy()
    source = sim.get("source")
    _do_tear(sim, source, narrate=False)
    return {
        "damaged": source.meters["damaged"] >= THRESHOLD,
        "trouble": sim.get("lobby").meters["trouble"],
    }


def _do_tear(world: World, source: Entity, narrate: bool = True) -> None:
    source.meters["damaged"] += 1
    source.meters["missing_page"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright travel morning, {a.id} and {b.id} turned the hotel lobby into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.leader} {a.id} and {theme.mate} {b.id}!" {a.id} cried. '
        f'"Let\'s find {theme.goal}!"'
    )


def need_map(world: World, b: Entity, theme: Theme, source_cfg: SourceItem) -> None:
    world.say(
        f"But the route to {theme.goal} needed a real map, and the table by the armchairs "
        f"held {source_cfg.phrase} with an excerpt about {source_cfg.geography_word}."
    )
    world.say(
        f'{b.id} leaned closer. "That geography page looks perfect for our quest," '
        f'{b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, source_cfg: SourceItem) -> None:
    a.memes["urge"] += 1
    glow = "eyes shone at once" if a.memes["urge"] >= 6 else "eyes shone"
    world.say(
        f'{a.id}\'s {glow}. "I know! We can tear out that little excerpt and use it as our map."'
    )
    world.say("For one excited breath, the idea felt quick and clever.")


def warn(world: World, b: Entity, a: Entity, source_cfg: SourceItem, clerk: Entity) -> None:
    pred = predict_damage(world)
    b.memes["honesty"] += 1
    world.facts["predicted_trouble"] = pred["trouble"]
    extra = ""
    if b.memes["honesty"] >= 6:
        extra = f" {b.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, that book is for '
        f'everyone in the hotel lobby. If we tear out the excerpt, we will ruin it, '
        f'and the clerk will find the missing page."{extra}'
    )
    world.say(
        f'"If we need a map, we should ask first and be candid about what we want," '
        f'{b.id} added.'
    )


def back_down(world: World, a: Entity, b: Entity, theme: Theme, clerk: Entity) -> None:
    a.memes["urge"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the shared book, then at {b.id}, and felt the brave game inside '
        f'{a.pronoun("object")} slow down. "You\'re right," {a.pronoun()} said.'
    )
    world.say(
        f"They left the book exactly where it was and went to the front desk to ask the "
        f"{clerk.label_word} for help instead."
    )


def ask_and_help(world: World, clerk: Entity, a: Entity, b: Entity, source_cfg: SourceItem,
                 theme: Theme, map_gift: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
        kid.memes["honesty"] += 1
    clerk.memes["kindness"] += 1
    world.say(
        f'The {clerk.label_word} smiled when they asked so politely. "{source_cfg.label.capitalize()} '
        f'should stay whole," {clerk.pronoun()} said, "but I can give you {map_gift.label} instead."'
    )
    world.say(
        f'Soon {a.id} held {map_gift.label}, and {b.id} traced the tiny streets with one finger. '
        f'"Now this is a proper voyage," {a.id} said.'
    )
    world.say(
        f"At last the {theme.role_plural} {theme.send_off}, and the hotel lobby felt bright, busy, "
        f"and honest."
    )


def defy(world: World, a: Entity, b: Entity, relation: str) -> None:
    a.memes["defiance"] += 1
    older = relation == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Don\'t fuss," {a.id} said. Because {a.id} was {b.pronoun("possessive")} '
            f'{rel}, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Don\'t fuss," {a.id} said, and reached for the page anyway.')


def tear_excerpt(world: World, source: Entity, source_cfg: SourceItem) -> None:
    _do_tear(world, source)
    world.say(
        f"The paper gave a soft rip. A neat little excerpt came loose, showing a coast, "
        f"a blue river, and one paragraph about {source_cfg.geography_word}."
    )
    world.say(
        f"For half a second it looked like a perfect treasure map. Then the torn edge stared back, "
        f"plain as a mistake."
    )


def notice_loss(world: World, b: Entity, clerk: Entity, source_cfg: SourceItem) -> None:
    world.say(
        f'"{source_cfg.label.capitalize()} is ripped!" {b.id} whispered. The sound of the hotel lobby '
        f"did not stop, but suddenly it felt much too loud."
    )
    world.say(
        f'The {clerk.label_word} looked over from the desk and saw the damaged page.'
    )


def candid_confession(world: World, a: Entity, clerk: Entity, source_cfg: SourceItem) -> None:
    a.memes["confessed"] += 1
    a.memes["honesty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id}'s cheeks went hot. Then {a.pronoun()} took a breath and walked to the desk."
    )
    world.say(
        f'"I did it," {a.pronoun()} said in a candid little voice. "I tore out the excerpt because '
        f"I wanted a map. I am sorry."
    )
    clerk.memes["trust"] += 1


def repair_and_lesson(world: World, clerk: Entity, a: Entity, b: Entity, response: Response,
                      source: Entity, map_gift: Entity, theme: Theme) -> None:
    source.meters["repaired"] += 1
    source.meters["damaged"] = 0.0
    world.get("lobby").meters["trouble"] = 0.0
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    clerk.memes["kindness"] += 1
    world.say(
        f'The {clerk.label_word} nodded. "{response.text}" {clerk.pronoun()} said. '
        f'"Thank you for telling the truth right away."'
    )
    world.say(
        f'Together they tucked the torn piece into an envelope for repair, and the '
        f'{clerk.label_word} handed them {map_gift.label} from the city rack.'
    )
    world.say(
        f'{b.id} smiled at {a.id}. This time the {theme.role_plural} {theme.send_off} with a real map, '
        f'and the hotel lobby felt warm again.'
    )


def hide_it(world: World, a: Entity, b: Entity, clerk: Entity, source_cfg: SourceItem,
            theme: Theme) -> None:
    a.memes["shame"] += 1
    b.memes["fear"] += 1
    clerk.memes["trust"] -= 1
    world.say(
        f"{a.id} folded the torn excerpt small and tried to hide it under {a.pronoun('possessive')} sleeve."
    )
    world.say(
        f'But the torn page in {source_cfg.label} showed the truth at once, and the {clerk.label_word} '
        f'saw what had happened without any help.'
    )
    world.say(
        f'The game ended there. The children sat quietly in the hotel lobby while the grown-up voices '
        f"turned gentle and serious around them."
    )
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f"Later, {a.id} admitted the truth at last, but the shining voyage feeling had already gone. "
        f"After that, both children remembered that a brave heart should also be honest."
    )
@dataclass
class StoryParams:
    theme: str
    source: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    clerk: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
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
    "geography": [
        (
            "What is geography?",
            "Geography is the study of places on Earth, like mountains, rivers, towns, and seas. "
            "It helps us understand where things are and how places fit together.",
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map shows where places are and how to get from one place to another. "
            "It is like a picture of roads, rivers, rooms, or land seen from above.",
        )
    ],
    "book": [
        (
            "Why should shared books stay whole?",
            "Shared books are for many people to use, so tearing pages out ruins them for everyone else. "
            "Taking care of them is one way to be fair.",
        )
    ],
    "honesty": [
        (
            "What does it mean to be candid?",
            "Being candid means telling the truth plainly instead of hiding it. "
            "A candid person says what really happened, even when it feels hard.",
        ),
        (
            "Why is honesty important after a mistake?",
            "Honesty helps other people understand what happened and fix the problem. "
            "When you tell the truth quickly, trust can begin to grow again.",
        ),
    ],
    "repair": [
        (
            "What does repair mean?",
            "Repair means trying to fix something that was torn, broken, or damaged. "
            "It does not erase the mistake, but it helps care for what was hurt.",
        )
    ],
}
KNOWLEDGE_ORDER = ["geography", "map", "book", "honesty", "repair"]


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
    theme = f["theme"]
    source_cfg = f["source_cfg"]
    outcome = f["outcome"]
    if outcome == "asked_first":
        return [
            f'Write a hotel lobby story for a 3-to-5-year-old where two children playing {theme.role_plural} '
            f'want a map from a {source_cfg.label} but choose to ask first. Include the words "candid", '
            f'"excerpt", and "geography".',
            f"Tell a gentle story where {a.id} wants to tear out an excerpt from a shared {source_cfg.label}, "
            f"but {b.id} warns that honest asking is better, and the clerk helps them.",
            f'Write a simple moral-value story in a playful pirate-like style where children in a hotel lobby '
            f'learn that being candid is braver than grabbing what is not theirs.',
        ]
    if outcome == "confessed":
        return [
            f'Write a hotel lobby story for a 3-to-5-year-old where a child damages a shared {source_cfg.label}, '
            f'then gives a candid confession and learns honesty. Include the words "candid", "excerpt", and '
            f'"geography".',
            f"Tell a pirate-like cautionary story where {a.id} tears out an excerpt for a pretend map, feels sorry, "
            f"and tells the clerk the truth.",
            f'Write a small moral-value story that shows how honesty after a mistake can lead to repair, kindness, '
            f'and a better ending.',
        ]
    return [
        f'Write a hotel lobby story for a 3-to-5-year-old where a child hides the truth after tearing an excerpt '
        f'from a shared geography book. Include the words "candid", "excerpt", and "geography".',
        f"Tell a sad but child-safe cautionary story where {a.id} tries to hide a torn page instead of speaking honestly.",
        f'Write a simple story showing that hiding a mistake makes the game smaller, while honesty would have helped.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    clerk = f["clerk"]
    theme = f["theme"]
    source_cfg = f["source_cfg"]
    source = f["source"]
    map_gift = f["map_gift"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were playing {theme.role_plural} in a hotel lobby. "
            f"It is also about the {clerk.label_word} who helped once the trouble was known.",
        ),
        (
            "Why did the children care about the book on the table?",
            f"They wanted a map for their pretend voyage, and the shared {source_cfg.label} had an excerpt about "
            f"{source_cfg.geography_word}. That made it look useful for their game.",
        ),
        (
            f"What warning did {b.id} give {a.id}?",
            f"{b.id} warned that the {source_cfg.label} belonged in the hotel lobby for everyone to use. "
            f"{b.pronoun().capitalize()} also knew that tearing out a page would damage it and cause trouble right away.",
        ),
    ]
    if f["outcome"] == "asked_first":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} listened and did not tear the page out. Instead, the children went to the desk and asked for help, "
                f"which kept the shared book whole.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The clerk gave them {map_gift.label}, and they went back to their adventure honestly. "
                f"The ending proves that asking first can protect other people's things and still keep the fun alive.",
            )
        )
    elif f["outcome"] == "confessed":
        qa.append(
            (
                f"What happened when {a.id} tore out the excerpt?",
                f"The page ripped free and left the {source_cfg.label} damaged. "
                f"For a moment it looked like a useful map, but the torn edge made the mistake plain.",
            )
        )
        qa.append(
            (
                f"How did {a.id} fix the problem as much as possible?",
                f"{a.id} was candid and told the clerk the truth right away. "
                f"Because of that honest confession, they could set the torn piece aside for repair and get help the proper way.",
            )
        )
        qa.append(
            (
                "What moral did the children learn?",
                "They learned that honesty is part of being brave. "
                "Telling the truth did not erase the mistake, but it opened the door to repair, forgiveness, and a better ending.",
            )
        )
    else:
        qa.append(
            (
                f"Why did the ending feel sadder after {a.id} hid the torn page?",
                f"Hiding the truth did not really hide the damage, because the book still showed the missing page. "
                f"The game stopped, and the children had to sit with the trouble instead of fixing it quickly.",
            )
        )
        qa.append(
            (
                "What should have happened instead?",
                f"{a.id} should have given a candid apology as soon as the page tore. "
                f"That would have helped the clerk understand what happened and start repairing the damage sooner.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["source_cfg"].tags)
    tags |= set(f["response"].tags)
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
        flags = [
            n for n, on in (
                ("public_item", e.public_item),
                ("map_source", e.map_source),
                ("tearable", e.tearable),
                ("copyable", e.copyable),
            ) if on
        ]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        source="atlas",
        response="confess",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        clerk="clerk_woman",
        trait="candid",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
    ),
    StoryParams(
        theme="explorers",
        source="guidebook",
        response="apologize",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        clerk="clerk_man",
        trait="truthful",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
    ),
    StoryParams(
        theme="pirates",
        source="magazine",
        response="confess",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Noah",
        cautioner_gender="boy",
        parent="mother",
        clerk="clerk_woman",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        theme="pirates",
        source="atlas",
        response="hide",
        instigator="Zoe",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        parent="father",
        clerk="clerk_man",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
]


def explain_rejection(source_id: str) -> str:
    if source_id in DECOYS:
        item = DECOYS[source_id]
        return (
            f"(No story: {item.phrase} in the hotel lobby does not contain any map or geography excerpt, "
            f"so the children would have no tempting page to take. Pick a shared book or magazine instead.)"
        )
    return "(No story: this source cannot honestly support the map-taking problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense and moral sense "
        f"(sense={r.sense} < {SENSE_MIN}). A storyworld should prefer candid honesty. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_ask_first(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "asked_first"
    return "confessed" if RESPONSES[params.response].honest else "hidden"


ASP_RULES = r"""
usable_source(S) :- source(S), map_source(S), public_item(S), tearable(S), copyable(S).
valid(T, S) :- theme(T), usable_source(S).

cautious_now(T) :- trait(T), honest_trait(T).
init_honesty(5) :- trait(T), cautious_now(T).
init_honesty(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(H + 1 + B) :- init_honesty(H), bonus(B).
asked_first :- cautioner_older, authority(A), urge_init(U), A > U.

confessed :- not asked_first, chosen_response(R), honest_response(R).
hidden :- not asked_first, chosen_response(R), not honest_response(R).

outcome(asked_first) :- asked_first.
outcome(confessed) :- confessed.
outcome(hidden) :- hidden.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for src_id, src in SOURCES.items():
        lines.append(asp.fact("source", src_id))
        if src.map_source:
            lines.append(asp.fact("map_source", src_id))
        if src.public_item:
            lines.append(asp.fact("public_item", src_id))
        if src.tearable:
            lines.append(asp.fact("tearable", src_id))
        if src.copyable:
            lines.append(asp.fact("copyable", src_id))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        if r.honest:
            lines.append(asp.fact("honest_response", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("urge_init", int(URGE_INIT)))
    for tr in sorted(HONEST_TRAITS):
        lines.append(asp.fact("honest_trait", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    program = asp_facts() + "\n" + r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
#show sensible/1.
"""
    model = asp.one_model(program)
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: children in a hotel lobby, a tempting shared book, and a moral choice about honesty."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--source", choices=list(SOURCES.keys()) + list(DECOYS.keys()))
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--clerk", choices=["clerk_woman", "clerk_man"])
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
    if args.source and args.source in DECOYS:
        raise StoryError(explain_rejection(args.source))
    if args.source and args.source not in SOURCES:
        raise StoryError("(No story: unknown source.)")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.source is None or c[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, source = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    clerk = args.clerk or rng.choice(["clerk_woman", "clerk_man"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme,
        source=source,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        clerk=clerk,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme '{params.theme}'.)")
    if params.source not in SOURCES:
        if params.source in DECOYS:
            raise StoryError(explain_rejection(params.source))
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if RESPONSES[params.response].sense < SENSE_MIN and not (
        params.response == "hide"
    ):
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        source_cfg=SOURCES[params.source],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        clerk_type=params.clerk,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, source) combos:\n")
        for theme, source in combos:
            print(f"  {theme:10} {source}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.source} in hotel lobby ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(theme: Theme, source_cfg: SourceItem, response: Response,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         parent_type: str = "mother", clerk_type: str = "clerk_woman",
         trait: str = "candid", relation: str = "siblings",
         instigator_age: int = 6, cautioner_age: int = 4) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age if False else 0,
    ))
    a.id = instigator
    a.attrs["relation"] = relation
    a.attrs["age"] = instigator_age
    a.memes["urge"] = URGE_INIT

    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        traits=[trait],
    ))
    b.id = cautioner
    b.attrs["relation"] = relation
    b.attrs["age"] = cautioner_age
    b.memes["honesty"] = initial_honesty(trait)

    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    clerk = world.add(Entity(
        id="clerk",
        kind="character",
        type=clerk_type,
        label="the clerk",
        role="clerk",
    ))
    world.add(Entity(id="lobby", type="room", label="the hotel lobby"))
    source = world.add(Entity(
        id="source",
        type="book",
        label=source_cfg.label,
        owner=source_cfg.owner,
        public_item=source_cfg.public_item,
        map_source=source_cfg.map_source,
        tearable=source_cfg.tearable,
        copyable=source_cfg.copyable,
    ))
    map_gift = world.add(Entity(
        id="gift_map",
        type="map",
        label="a free foldout map",
        owner="hotel",
    ))

    world.facts["instigator_name"] = instigator
    world.facts["cautioner_name"] = cautioner
    world.facts["relation"] = relation
    world.facts["map_word"] = source_cfg.geography_word
    world.facts["source_cfg"] = source_cfg
    world.facts["response"] = response
    world.facts["theme"] = theme

    play_setup(world, a, b, theme)
    need_map(world, b, theme, source_cfg)

    world.para()
    tempt(world, a, source_cfg)
    warn(world, b, a, source_cfg, clerk)

    averted = would_ask_first(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, theme, clerk)
        world.para()
        ask_and_help(world, clerk, a, b, source_cfg, theme, map_gift)
        outcome = "asked_first"
    else:
        defy(world, a, b, relation)
        world.para()
        tear_excerpt(world, source, source_cfg)
        notice_loss(world, b, clerk, source_cfg)
        world.para()
        if response.honest:
            candid_confession(world, a, clerk, source_cfg)
            repair_and_lesson(world, clerk, a, b, response, source, map_gift, theme)
            outcome = "confessed"
        else:
            hide_it(world, a, b, clerk, source_cfg, theme)
            outcome = "hidden"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        clerk=clerk,
        source=source,
        map_gift=map_gift,
        outcome=outcome,
        damaged=source.meters["missing_page"] >= THRESHOLD,
        repaired=source.meters["repaired"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a grand harbor before a voyage",
        rig="The striped rug became the sea, the brass luggage cart became their ship, "
            "the potted palm leaned like an island tree, and the soft chairs turned into cliffs.",
        leader="Captain",
        mate="Navigator",
        goal="the hidden harbor",
        route="across the sea rug",
        role_solo="a pirate",
        role_plural="pirates",
        send_off="set off across the sea rug toward the hidden harbor",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a far-off expedition camp",
        rig="The striped rug became a winding river, the brass luggage cart became their wagon, "
            "the potted palm leaned like jungle leaves, and the soft chairs turned into hills.",
        leader="Leader",
        mate="Scout",
        goal="the secret valley",
        route="past the river rug",
        role_solo="an explorer",
        role_plural="explorers",
        send_off="marched off past the river rug toward the secret valley",
    ),
}

SOURCES = {
    "atlas": SourceItem(
        id="atlas",
        label="atlas",
        phrase="a thick geography atlas",
        owner="hotel",
        place="on the low table",
        excerpt="a coast and river map",
        geography_word="the geography of the coast",
        map_source=True,
        public_item=True,
        tearable=True,
        copyable=True,
        tags={"geography", "book", "map", "honesty"},
    ),
    "guidebook": SourceItem(
        id="guidebook",
        label="guidebook",
        phrase="a city guidebook",
        owner="hotel",
        place="beside the brochures",
        excerpt="a neighborhood map excerpt",
        geography_word="the geography of the old town",
        map_source=True,
        public_item=True,
        tearable=True,
        copyable=True,
        tags={"geography", "book", "map", "honesty"},
    ),
    "magazine": SourceItem(
        id="magazine",
        label="travel magazine",
        phrase="a glossy travel magazine",
        owner="hotel",
        place="on the armchair table",
        excerpt="an excerpt with a mountain map",
        geography_word="the geography of the mountains",
        map_source=True,
        public_item=True,
        tearable=True,
        copyable=True,
        tags={"geography", "magazine", "map", "honesty"},
    ),
}

DECOYS = {
    "sculpture": DecoyItem(
        id="sculpture",
        label="lobby sculpture",
        phrase="a smooth stone sculpture",
        owner="hotel",
        place="by the fountain wall",
        map_source=False,
        public_item=True,
        tearable=False,
        copyable=False,
        tags={"lobby"},
    ),
}

RESPONSES = {
    "confess": Response(
        id="confess",
        sense=3,
        honest=True,
        repair=True,
        text="We can mend this better if you are truthful",
        ending="The truth made room for repair and kindness.",
        qa_text="told the clerk the truth right away and helped set the torn piece aside for repair",
        tags={"honesty", "repair"},
    ),
    "apologize": Response(
        id="apologize",
        sense=3,
        honest=True,
        repair=True,
        text="Thank you for being candid and saying what happened",
        ending="Honesty turned a mistake into a lesson.",
        qa_text="gave a candid apology and accepted help repairing the damaged book",
        tags={"honesty", "repair"},
    ),
    "hide": Response(
        id="hide",
        sense=1,
        honest=False,
        repair=False,
        text="",
        ending="Hiding the truth made the trouble heavier.",
        qa_text="tried to hide the torn page instead of telling the truth",
        tags={"dishonesty"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["candid", "careful", "truthful", "thoughtful", "curious", "bold"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for theme_id in THEMES:
        for src_id, src in SOURCES.items():
            if source_is_usable(src):
                combos.append((theme_id, src_id))
    return combos

if __name__ == "__main__":
    main()
