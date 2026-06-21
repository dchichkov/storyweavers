#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py
=================================================================

A standalone storyworld about Mike using gentle humor to help a friend through a
small public-rhyme mishap. The world stays tiny and concrete: a place, a silly
prop, a supportive response, and a short performance with a turn. The prose is
written in a playful rhyming style, but the story still comes from simulated
state rather than slot-swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py --place playground --prop bubble_wand
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py --place classroom --prop rubber_chicken
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py --json
    python storyworlds/worlds/gpt-5.4/mike_friendship_humor_rhyming_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    role: str = ""
    owner: str = ""
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Place:
    id: str
    label: str
    scene: str
    audience: str
    allows_bubbles: bool = False
    allows_loud: bool = False
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
class Prop:
    id: str
    label: str
    phrase: str
    mishap: str
    clumsy: int
    loud: bool = False
    bubbles: bool = False
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
    power: int
    text: str
    fail: str
    qa_text: str
    kind: str
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


def _r_stage_jitters(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    if friend.memes["shy"] >= THRESHOLD and friend.memes["on_stage"] >= THRESHOLD:
        sig = ("jitters", friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["freeze"] += 1
            out.append("__jitters__")
    return out


def _r_mishap_embarrass(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    mike = world.get("mike")
    prop = world.get("prop")
    if prop.meters["mishap"] >= THRESHOLD:
        for child in (mike, friend):
            sig = ("embarrass", child.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            child.memes["embarrassed"] += 1
        friend.memes["shy"] += 1
        world.get("crowd").memes["surprise"] += 1
        out.append("__mishap__")
    return out


def _r_support_steadies(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    mike = world.get("mike")
    if mike.memes["supporting"] >= THRESHOLD:
        sig = ("steady", friend.id)
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["shy"] = max(0.0, friend.memes["shy"] - 2.0)
            friend.memes["courage"] += 1
            friend.memes["joy"] += 1
            mike.memes["joy"] += 1
            friend.memes["trust"] += 1
            world.get("crowd").memes["kind_laughter"] += 1
            out.append("__support__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stage_jitters", tag="emotion", apply=_r_stage_jitters),
    Rule(name="mishap_embarrass", tag="emotion", apply=_r_mishap_embarrass),
    Rule(name="support_steadies", tag="social", apply=_r_support_steadies),
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


def prop_fits(place: Place, prop: Prop) -> bool:
    if prop.bubbles and not place.allows_bubbles:
        return False
    if prop.loud and not place.allows_loud:
        return False
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def stumble_severity(prop: Prop, delay: int) -> int:
    return prop.clumsy + delay


def is_recovered(response: Response, prop: Prop, delay: int) -> bool:
    return response.power >= stumble_severity(prop, delay)


def predict_stumble(world: World, delay: int) -> dict:
    sim = world.copy()
    friend = sim.get("friend")
    prop = sim.get("prop")
    friend.memes["on_stage"] += 1
    propagate(sim, narrate=False)
    prop.meters["mishap"] += 1
    propagate(sim, narrate=False)
    severity = prop.clumsy + delay
    return {
        "freeze": friend.memes["freeze"] >= THRESHOLD,
        "shy": friend.memes["shy"],
        "severity": severity,
    }


def open_day(world: World, mike: Entity, friend: Entity, place: Place, parent: Entity) -> None:
    mike.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {place.scene}, Mike and {friend.id} were best-buddy bright, "
        f"two grinny little friends in the soft morning light."
    )
    world.say(
        f"{parent.label_word.capitalize()} had helped them pack a toy mike for the show, "
        f"and Mike said, \"We'll rhyme side by side, nice and slow.\""
    )


def plan_rhyme(world: World, mike: Entity, friend: Entity, place: Place, prop: Prop) -> None:
    world.say(
        f"At {place.label}, they planned a silly rhyme with {prop.phrase}. "
        f"Their words bounced with giggles; their feet tapped in time."
    )
    world.say(
        f"Mike made a tiny bow and said, \"When we start, do not hide. "
        f"If your knees feel wibbly, I'll stay right by your side.\""
    )


def stage_call(world: World, mike: Entity, friend: Entity, place: Place) -> None:
    friend.memes["anticipation"] += 1
    world.say(
        f"Soon {place.audience} looked on, and the children stepped near. "
        f"Mike felt a flutter of fun, but {friend.id} felt a flutter of fear."
    )


def gentle_warning(world: World, mike: Entity, friend: Entity, prop: Prop, response: Response, delay: int) -> None:
    pred = predict_stumble(world, delay)
    world.facts["predicted_freeze"] = pred["freeze"]
    world.facts["predicted_severity"] = pred["severity"]
    friend.memes["shy"] += 1
    world.say(
        f'Mike whispered, "If the joke gets bumpy and your brave feels small, '
        f'I can {response.kind} so neither of us has to do it all."'
    )
    if pred["freeze"]:
        world.say(
            f"{friend.id} gave a tiny nod. Even before the rhyme began, "
            f"{friend.pronoun()} knew the kindest plan."
        )


def climb_stage(world: World, mike: Entity, friend: Entity) -> None:
    mike.memes["on_stage"] += 1
    friend.memes["on_stage"] += 1
    propagate(world, narrate=False)
    if friend.memes["freeze"] >= THRESHOLD:
        world.say(
            f"When they reached the front, {friend.id}'s words tucked in tight. "
            f"{friend.pronoun().capitalize()} held the toy mike gently, but not quite."
        )


def mishap(world: World, mike: Entity, friend: Entity, prop: Prop) -> None:
    prop.meters["mishap"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the funny fumble: {prop.mishap}. "
        f"For one blink the room went still, as still as a nap."
    )


def rescue_success(world: World, mike: Entity, friend: Entity, response: Response, place: Place) -> None:
    mike.memes["supporting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Mike {response.text}. He tipped the toy mike toward {friend.id} with a grin, "
        f"as if to say, \"Come on, my friend. Hop back in.\""
    )
    world.say(
        f"Then the rhyme rolled out in a jolly, jangly stream, "
        f"and {place.audience} laughed the kind laugh that makes cheeks beam."
    )


def rescue_fail(world: World, mike: Entity, friend: Entity, response: Response, place: Place) -> None:
    mike.memes["supporting"] += 0.5
    world.say(
        f"Mike {response.fail}. The rhyme did not break in a terrible way, "
        f"but it wobbled and wandered and scooted astray."
    )
    world.say(
        f"{place.audience.capitalize()} waited kindly, yet the moment felt long, "
        f"so the children made a small bow and ended the song."
    )


def after_success(world: World, mike: Entity, friend: Entity, place: Place, prop: Prop) -> None:
    mike.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    mike.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"After the claps, {friend.id} bumped Mike's shoulder and smiled. "
        f'"You kept it fun and friendly," {friend.pronoun()} said, still bright-eyed and wild.'
    )
    world.say(
        f"Mike laughed, \"A joke is best when two friends share the mike.\" "
        f"Together they tucked away the {prop.label} and skipped off alike."
    )


def after_fail(world: World, mike: Entity, friend: Entity, parent: Entity, prop: Prop) -> None:
    mike.memes["regret"] += 1
    friend.memes["sad"] += 1
    world.say(
        f"Behind the stage, Mike rubbed the {prop.label} and gave a soft sigh. "
        f'"I should have helped you sooner. I am sorry," he said, eye to eye.'
    )
    world.say(
        f"{parent.label_word.capitalize()} knelt nearby and said, "
        f"\"Good friends can try again after a wobble goes by.\""
    )
    mike.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"So Mike and {friend.id} practiced one small rhyme in the shade, "
        f"sharing the toy mike together till new brave was made."
    )


def tell(
    place: Place,
    prop: Prop,
    response: Response,
    mike_name: str = "Mike",
    friend_name: str = "Lila",
    friend_gender: str = "girl",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(place)
    mike = world.add(Entity(id=mike_name, kind="character", type="boy", role="helper"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    crowd = world.add(Entity(id="crowd", kind="group", type="group", label=place.audience))
    prop_ent = world.add(Entity(id="prop", kind="thing", type="prop", label=prop.label, tags=set(prop.tags)))
    mike_tool = world.add(Entity(id="toy_mike", kind="thing", type="mike", label="toy mike", owner=mike.id))

    friend.memes["shy"] = 2.0
    friend.memes["trust"] = 2.0
    mike.memes["care"] = 2.0
    mike.memes["supporting"] = 0.0
    prop_ent.meters["mishap"] = 0.0
    crowd.memes["surprise"] = 0.0
    crowd.memes["kind_laughter"] = 0.0
    world.facts.update(
        place=place,
        prop_cfg=prop,
        response=response,
        delay=delay,
        mike=mike,
        friend=friend,
        parent=parent,
        crowd=crowd,
        toy_mike=mike_tool,
    )

    open_day(world, mike, friend, place, parent)
    plan_rhyme(world, mike, friend, place, prop)
    world.para()
    stage_call(world, mike, friend, place)
    gentle_warning(world, mike, friend, prop, response, delay)
    climb_stage(world, mike, friend)
    mishap(world, mike, friend, prop)

    recovered = is_recovered(response, prop, delay)
    world.facts["severity"] = stumble_severity(prop, delay)
    world.facts["recovered"] = recovered

    world.para()
    if recovered:
        rescue_success(world, mike, friend, response, place)
        world.para()
        after_success(world, mike, friend, place, prop)
        outcome = "recovered"
    else:
        rescue_fail(world, mike, friend, response, place)
        world.para()
        after_fail(world, mike, friend, parent, prop)
        outcome = "practice_after"
    world.facts["outcome"] = outcome
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom rug",
        scene="the bright classroom",
        audience="their classmates",
        allows_bubbles=False,
        allows_loud=False,
        tags={"classroom"},
    ),
    "playground": Place(
        id="playground",
        label="the playground bench-stage",
        scene="the sunny playground",
        audience="their friends by the slide",
        allows_bubbles=True,
        allows_loud=True,
        tags={"playground"},
    ),
    "backyard": Place(
        id="backyard",
        label="the backyard stepping-stones",
        scene="the green backyard",
        audience="their family on picnic chairs",
        allows_bubbles=True,
        allows_loud=True,
        tags={"backyard"},
    ),
}

PROPS = {
    "paper_mustache": Prop(
        id="paper_mustache",
        label="paper mustache",
        phrase="a paper mustache on a stick",
        mishap="the paper mustache spun sideways and tickled Mike's nose",
        clumsy=1,
        loud=False,
        bubbles=False,
        tags={"mustache", "dress_up"},
    ),
    "sock_puppet": Prop(
        id="sock_puppet",
        label="sock puppet",
        phrase="a floppy sock puppet with button eyes",
        mishap="the sock puppet plopped over the toy mike and muffled the first line",
        clumsy=1,
        loud=False,
        bubbles=False,
        tags={"puppet"},
    ),
    "bubble_wand": Prop(
        id="bubble_wand",
        label="bubble wand",
        phrase="a bubble wand loop",
        mishap="a bubble landed right on the toy mike and popped with a tiny plink",
        clumsy=2,
        loud=False,
        bubbles=True,
        tags={"bubbles"},
    ),
    "rubber_chicken": Prop(
        id="rubber_chicken",
        label="rubber chicken",
        phrase="a rubber chicken with a squeak in its beak",
        mishap="the rubber chicken let out a sudden squeak that made both children blink",
        clumsy=2,
        loud=True,
        bubbles=False,
        tags={"rubber_chicken", "squeak"},
    ),
}

RESPONSES = {
    "share_mike": Response(
        id="share_mike",
        sense=3,
        power=3,
        text="slid close, shared the first silly line, and made room for the next one",
        fail="tried to slide close and start the rhyme alone, but he left too little room for a quick reply",
        qa_text="shared the first line and tilted the toy mike toward the friend",
        kind="share the first line",
        tags={"sharing", "encouragement"},
    ),
    "hold_hands": Response(
        id="hold_hands",
        sense=3,
        power=2,
        text="took one of {friend}'s hands, whispered the beat, and counted them in",
        fail="reached for a hand and whispered the beat, but the pause had already grown too long",
        qa_text="held a hand and counted the rhyme in softly",
        kind="hold your hand and count us in",
        tags={"friendship", "encouragement"},
    ),
    "funny_bow": Response(
        id="funny_bow",
        sense=2,
        power=1,
        text="made an extra-loopy bow and sang the next word in a squeaky voice",
        fail="made an extra-loopy bow and a squeaky joke, but the stumble was already bigger than the laugh",
        qa_text="made a silly bow to turn the wobble into a joke",
        kind="turn it into a gentle joke",
        tags={"humor"},
    ),
    "show_off": Response(
        id="show_off",
        sense=1,
        power=1,
        text="rushed ahead with the rhyme all by himself",
        fail="kept talking over the moment all by himself",
        qa_text="kept going alone",
        kind="take over the whole rhyme",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lila", "Maya", "Nora", "Zoe", "Ella", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Noah", "Max"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prop_id, prop in PROPS.items():
            if prop_fits(place, prop):
                combos.append((place_id, prop_id))
    return combos


@dataclass
class StoryParams:
    place: str
    prop: str
    response: str
    friend_name: str
    friend_gender: str
    parent: str
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


KNOWLEDGE = {
    "mike": [
        (
            "What is a mike?",
            "A mike is another word for a microphone. It helps your voice sound louder so other people can hear you.",
        )
    ],
    "bubbles": [
        (
            "Why do bubbles pop?",
            "Bubbles pop when their thin, soapy skin breaks. A touch, a dry spot, or a little bump can make them burst.",
        )
    ],
    "rubber_chicken": [
        (
            "Why do people laugh at a rubber chicken?",
            "A rubber chicken looks silly because it is a toy shaped in a funny way. Its squeak can surprise people and make the joke even goofier.",
        )
    ],
    "puppet": [
        (
            "What is a puppet?",
            "A puppet is a toy you move to pretend it can talk. People use puppets for jokes, stories, and little shows.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help a shy friend?",
            "Sharing makes a hard moment feel smaller because the friend is not alone. When someone joins in kindly, brave feelings can grow.",
        )
    ],
    "encouragement": [
        (
            "What is encouragement?",
            "Encouragement is when you help someone feel brave enough to try. Kind words or a gentle hand can help a lot.",
        )
    ],
    "humor": [
        (
            "What is humor?",
            "Humor is the playful, funny part of a joke or a silly moment. Good humor makes people laugh without being mean.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mike", "bubbles", "rubber_chicken", "puppet", "sharing", "encouragement", "humor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    prop = f["prop_cfg"]
    friend = f["friend"]
    outcome = f["outcome"]
    if outcome == "recovered":
        return [
            f'Write a short rhyming story for a 3-to-5-year-old about Mike helping a shy friend during a funny show. Include the word "mike".',
            f"Tell a gentle friendship story set at {place.label} where Mike and {friend.id} use {prop.phrase}, a small mishap happens, and Mike helps the rhyme come out happily.",
            "Write a playful story with humor and friendship where a silly joke goes wrong for one moment, but kindness turns it right.",
        ]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old about Mike and a friend whose little performance gets wobbly. Include the word "mike".',
        f"Tell a friendship story set at {place.label} where Mike and {friend.id} bring {prop.phrase}, the joke fumbles, and they practice together after the show.",
        "Write a humorous but gentle story where a shy child needs support after a silly stage mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mike = f["mike"]
    friend = f["friend"]
    place = f["place"]
    prop = f["prop_cfg"]
    response = f["response"]
    parent = f["parent"]
    delay = f["delay"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Mike and {friend.id}, two friends getting ready to do a silly rhyme together. {parent.label_word.capitalize()} helps the day feel safe and calm.",
        ),
        (
            "What were Mike and the friend planning to do?",
            f"They were planning to do a funny rhyming show at {place.label} with {prop.phrase}. The toy mike and the silly prop were meant to make the performance playful.",
        ),
        (
            f"Why did {friend.id} feel nervous?",
            f"{friend.id} felt shy because people were watching and the rhyme had to happen out loud. In the world model, that stage moment raised {friend.pronoun('possessive')} jitters before the joke even slipped.",
        ),
        (
            "What went wrong in the show?",
            f"The small problem came when {prop.mishap}. That funny fumble made the moment feel embarrassing before Mike reacted.",
        ),
    ]
    if outcome == "recovered":
        if response.id == "hold_hands":
            body = response.qa_text
        else:
            body = response.qa_text
        qa.append(
            (
                "How did Mike help?",
                f"Mike {body}. That support lowered the shy feeling and helped {friend.id} join the rhyme instead of freezing alone.",
            )
        )
        qa.append(
            (
                "Why did the audience laugh happily?",
                f"They laughed because the joke stayed gentle and both friends shared it together. The funny moment became kinder than the stumble, so the laughter felt warm instead of sharp.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with Mike and {friend.id} smiling, hearing claps, and walking off together. The ending image proves the friendship grew stronger through the wobble.",
            )
        )
    else:
        qa.append(
            (
                "Did Mike fix the problem right away?",
                f"Not quite. The stumble severity was {f['severity']}, and Mike's response came too weakly after a delay of {delay}, so the rhyme ended early. Afterward he apologized and practiced kindly with {friend.id}.",
            )
        )
        qa.append(
            (
                "What did Mike and the friend do after the show?",
                f"They practiced one small rhyme together in the shade. That second try mattered because friendship was more important than getting the show perfect.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended softly, not with a big win but with a better friendship. Mike and {friend.id} shared the toy mike while building new brave together.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mike", "humor"}
    tags |= set(f["prop_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        prop="paper_mustache",
        response="share_mike",
        friend_name="Lila",
        friend_gender="girl",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        place="playground",
        prop="bubble_wand",
        response="hold_hands",
        friend_name="Ben",
        friend_gender="boy",
        parent="father",
        delay=0,
    ),
    StoryParams(
        place="backyard",
        prop="rubber_chicken",
        response="funny_bow",
        friend_name="Maya",
        friend_gender="girl",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        place="playground",
        prop="rubber_chicken",
        response="share_mike",
        friend_name="Theo",
        friend_gender="boy",
        parent="father",
        delay=0,
    ),
]


def explain_rejection(place: Place, prop: Prop) -> str:
    if prop.bubbles and not place.allows_bubbles:
        return (
            f"(No story: {place.label} is not a good place for bubbles. "
            f"A bubble wand needs open air, or the joke becomes fussy instead of funny.)"
        )
    if prop.loud and not place.allows_loud:
        return (
            f"(No story: {prop.label} is too noisy for {place.label}. "
            f"This world rejects a joke that would drown out the rhyme.)"
        )
    return "(No story: that place and prop do not make a reasonable performance.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a kinder, more helpful move: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "recovered" if is_recovered(RESPONSES[params.response], PROPS[params.prop], params.delay) else "practice_after"


ASP_RULES = r"""
valid(P, Pr) :- place(P), prop(Pr), compatible(P, Pr).

compatible(P, Pr) :- place(P), prop(Pr), not needs_bubbles(Pr), not needs_loud(Pr).
compatible(P, Pr) :- place(P), prop(Pr), needs_bubbles(Pr), allows_bubbles(P), not needs_loud(Pr).
compatible(P, Pr) :- place(P), prop(Pr), needs_loud(Pr), allows_loud(P), not needs_bubbles(Pr).
compatible(P, Pr) :- place(P), prop(Pr), needs_bubbles(Pr), allows_bubbles(P), needs_loud(Pr), allows_loud(P).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

severity(C + D) :- chosen_prop(Pr), clumsy(Pr, C), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
outcome(recovered) :- resp_power(P), severity(S), P >= S.
outcome(practice_after) :- resp_power(P), severity(S), P < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.allows_bubbles:
            lines.append(asp.fact("allows_bubbles", pid))
        if place.allows_loud:
            lines.append(asp.fact("allows_loud", pid))
    for prid, prop in PROPS.items():
        lines.append(asp.fact("prop", prid))
        lines.append(asp.fact("clumsy", prid, prop.clumsy))
        if prop.bubbles:
            lines.append(asp.fact("needs_bubbles", prid))
        if prop.loud:
            lines.append(asp.fact("needs_loud", prid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_prop", params.prop),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    parser = build_parser()
    cases = list(CURATED)
    for s in range(50):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Mike, a funny rhyme, and a kind rescue when a joke wobbles."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the wobble lasts before Mike helps")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, prop) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.prop:
        place = PLACES[args.place]
        prop = PROPS[args.prop]
        if not prop_fits(place, prop):
            raise StoryError(explain_rejection(place, prop))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.prop is None or c[1] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prop_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    if args.friend_name:
        friend_name = args.friend_name
    else:
        pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
        friend_name = rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        prop=prop_id,
        response=response_id,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        prop = PROPS[params.prop]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not prop_fits(place, prop):
        raise StoryError(explain_rejection(place, prop))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        prop=prop,
        response=response,
        mike_name="Mike",
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, prop) combos:\n")
        for place, prop in combos:
            print(f"  {place:10} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
        for i, sample in enumerate(samples):
            sample.params.seed = base_seed + i
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
            header = f"### Mike & {p.friend_name}: {p.prop} at {p.place} ({p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
