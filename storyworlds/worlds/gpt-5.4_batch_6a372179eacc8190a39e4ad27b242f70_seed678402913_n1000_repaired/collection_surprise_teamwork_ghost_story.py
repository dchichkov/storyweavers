#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/collection_surprise_teamwork_ghost_story.py
======================================================================

A standalone story world for a child-facing ghost-story-flavored tale about a
missing collection, a spooky misunderstanding, teamwork, and a surprise reveal.

Premise
-------
Two children have a little collection they care about. In a dim, creaky place,
a spooky sound and a fluttering shape make them think a ghost has taken it.
Instead of running apart or blaming each other, they work together in a sensible
way. Their teamwork solves the problem, and the "ghost" turns out to be
something ordinary and harmless.

Coverage constraint
-------------------
Not every spooky source fits every place, and not every teamwork plan is a
reasonable fix. This world enforces two small common-sense constraints:

* A ghost-source must be physically supported by the chosen place
  (for example, a loose shutter only makes sense where there is a window).
* A teamwork method must match the problem's height:
  low places can be reached with a careful pair method; high places need a
  stool-and-spotter plan.

The world model drives the prose:
* wind + source -> spooky sound / flutter
* spooky signs + dark place -> fear rises
* a slide/fall event can move the collection out of reach
* teamwork method lowers risk and raises confidence
* the ending image depends on what actually changed in the world

Run it
------
    python storyworlds/worlds/gpt-5.4/collection_surprise_teamwork_ghost_story.py
    python storyworlds/worlds/gpt-5.4/collection_surprise_teamwork_ghost_story.py --place attic --collection buttons
    python storyworlds/worlds/gpt-5.4/collection_surprise_teamwork_ghost_story.py --source shutter
    python storyworlds/worlds/gpt-5.4/collection_surprise_teamwork_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/collection_surprise_teamwork_ghost_story.py --qa --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    spooky_detail: str
    has_window: bool = False
    has_sheet: bool = False
    height: str = "low"
    tags: set[str] = field(default_factory=set)


@dataclass
class CollectionKind:
    id: str
    noun: str
    phrase: str
    container: str
    shine: str
    plural: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound: str
    flutter: str
    needs_window: bool = False
    needs_sheet: bool = False
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    reaches: set[str] = field(default_factory=set)
    setup: str = ""
    action: str = ""
    proof: str = ""
    tags: set[str] = field(default_factory=set)


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
        return [e for e in self.entities.values() if e.role in {"finder", "helper"}]

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


def _r_spook(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    out: list[str] = []
    if room.meters["gust"] >= THRESHOLD and source.meters["ready"] >= THRESHOLD:
        sig = ("spook",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["spooky"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__spook__")
    return out


def _r_slide(world: World) -> list[str]:
    room = world.get("room")
    collection = world.get("collection")
    if room.meters["spooky"] >= THRESHOLD and collection.meters["safe"] >= THRESHOLD:
        sig = ("slide",)
        if sig not in world.fired:
            world.fired.add(sig)
            collection.meters["safe"] = 0.0
            collection.meters["misplaced"] += 1
            collection.attrs["location"] = "high_ledge" if world.place.height == "high" else "behind_trunk"
            return ["__slide__"]
    return []


def _r_teamwork(world: World) -> list[str]:
    if world.get("plan").meters["active"] < THRESHOLD:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["confidence"] += 1
        kid.memes["fear"] = max(0.0, kid.memes["fear"] - 1.0)
        kid.memes["trust"] += 1
    return ["__teamwork__"]


CAUSAL_RULES = [
    Rule(name="spook", tag="emotion", apply=_r_spook),
    Rule(name="slide", tag="physical", apply=_r_slide),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the old attic above the hall",
        spooky_detail="The rafters creaked, and the slanting roof made every corner look deeper than it was.",
        has_window=True,
        has_sheet=True,
        height="high",
        tags={"attic", "dark_place"},
    ),
    "shed": Place(
        id="shed",
        label="garden shed",
        phrase="the garden shed by the fence",
        spooky_detail="Rakes leaned against the wall, and every tiny knock sounded bigger in the dim light.",
        has_window=False,
        has_sheet=True,
        height="low",
        tags={"shed", "dark_place"},
    ),
    "barn_loft": Place(
        id="barn_loft",
        label="barn loft",
        phrase="the little loft in Grandpa's barn",
        spooky_detail="Dust floated in thin bars of light, and the boards gave long, whispery groans.",
        has_window=True,
        has_sheet=False,
        height="high",
        tags={"barn", "dark_place"},
    ),
}

COLLECTIONS = {
    "shells": CollectionKind(
        id="shells",
        noun="shells",
        phrase="a small collection of smooth shells",
        container="a blue tin",
        shine="their pale edges looked like moonlight",
        plural=True,
        tags={"shells", "collection"},
    ),
    "buttons": CollectionKind(
        id="buttons",
        noun="buttons",
        phrase="a neat collection of bright buttons",
        container="a round cookie tin",
        shine="the shiny ones blinked like tiny eyes when light touched them",
        plural=True,
        tags={"buttons", "collection"},
    ),
    "feathers": CollectionKind(
        id="feathers",
        noun="feathers",
        phrase="a soft collection of striped feathers",
        container="a long picture box",
        shine="their bands of brown and cream made them look special even in the gloom",
        plural=True,
        tags={"feathers", "collection"},
    ),
}

SOURCES = {
    "shutter": Source(
        id="shutter",
        label="loose shutter",
        sound="tap-tap-tap against the frame",
        flutter="the shadow jumped on the wall",
        needs_window=True,
        needs_sheet=False,
        reveal="a loose shutter outside the window, knocking in the wind",
        tags={"wind", "window"},
    ),
    "sheet": Source(
        id="sheet",
        label="old dust sheet",
        sound="hushed brushing sounds",
        flutter="a white shape lifted and sank again",
        needs_window=False,
        needs_sheet=True,
        reveal="an old dust sheet puffing up whenever air slipped under it",
        tags={"sheet", "wind"},
    ),
    "owl": Source(
        id="owl",
        label="barn owl",
        sound="a soft hoo and a scritch of claws",
        flutter="two round eyes blinked from a beam",
        needs_window=False,
        needs_sheet=False,
        reveal="a sleepy little owl perched up high, blinking at them",
        tags={"owl", "animal"},
    ),
}

METHODS = {
    "pair_reach": Method(
        id="pair_reach",
        label="careful pair reach",
        reaches={"low"},
        setup="One child held the lantern steady while the other knelt and reached where both could still see.",
        action="Together they moved the trunk slowly and reached behind it without tipping anything over",
        proof="the missing box scraped forward into the light",
        tags={"teamwork", "careful"},
    ),
    "stool_spotter": Method(
        id="stool_spotter",
        label="stool and spotter",
        reaches={"low", "high"},
        setup="They fetched a small stool; one climbed carefully while the other braced the legs and watched every step.",
        action="Working as one, they stretched just far enough to hook the box and guide it down safely",
        proof="the box settled into waiting hands instead of falling",
        tags={"teamwork", "stool"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["brave", "careful", "curious", "quiet", "thoughtful", "steady"]


def source_fits(place: Place, source: Source) -> bool:
    if source.needs_window and not place.has_window:
        return False
    if source.needs_sheet and not place.has_sheet:
        return False
    return True


def method_fits(place: Place, method: Method) -> bool:
    return place.height in method.reaches


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for coll_id in COLLECTIONS:
            for source_id, source in SOURCES.items():
                if not source_fits(place, source):
                    continue
                for method_id, method in METHODS.items():
                    if method_fits(place, method):
                        combos.append((place_id, coll_id, source_id, method_id))
    return combos


@dataclass
class StoryParams:
    place: str
    collection: str
    source: str
    method: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


def introduce(world: World, a: Entity, b: Entity, collection_cfg: CollectionKind, place: Place) -> None:
    for kid in (a, b):
        kid.memes["care"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} loved keeping {collection_cfg.phrase} together."
    )
    world.say(
        f"They kept it in {collection_cfg.container}, and {collection_cfg.shine}."
    )
    world.say(
        f"That afternoon they carried the tin to {place.phrase}, because they wanted a secret place to sort and admire their collection."
    )
    world.say(place.spooky_detail)


def darken(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    room = world.get("room")
    room.meters["dim"] += 1
    world.say(
        f'"Stay where the light can still find you," called their {parent.label_word} from downstairs.'
    )
    world.say(
        f'But in the quiet dimness, even that kind voice sounded far away, and {a.id} and {b.id} huddled closer over the box.'
    )


def gust_and_spook(world: World, source_cfg: Source) -> None:
    room = world.get("room")
    source = world.get("source")
    room.meters["gust"] += 1
    source.meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a gust slipped through, and there came {source_cfg.sound}. At the same moment, {source_cfg.flutter}."
    )
    if room.meters["spooky"] >= THRESHOLD:
        world.say(
            'Both children went still. For one breath, it truly seemed as if a ghost had stirred in the dark.'
        )


def lose_collection(world: World, collection_cfg: CollectionKind) -> None:
    collection = world.get("collection")
    propagate(world, narrate=False)
    loc = collection.attrs.get("location", "somewhere out of sight")
    if loc == "high_ledge":
        place_phrase = "up on a narrow ledge under the rafters"
    else:
        place_phrase = "behind an old trunk near the wall"
    world.say(
        f"The children jerked in surprise, and {collection_cfg.container} slid away from them and vanished {place_phrase}."
    )
    world.say(
        f'"Our collection!" one whispered. Now the dark place felt emptier and much more frightening.'
    )


def decide_together(world: World, a: Entity, b: Entity, method_cfg: Method) -> None:
    plan = world.get("plan")
    plan.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} took a shaky breath. "{b.id}, do not let go of me," {a.pronoun()} said.'
    )
    world.say(
        f'"I won\'t," said {b.id}. "We can do this together." {method_cfg.setup}'
    )


def recover(world: World, method_cfg: Method, collection_cfg: CollectionKind) -> None:
    collection = world.get("collection")
    collection.meters["misplaced"] = 0.0
    collection.meters["found"] += 1
    collection.attrs["location"] = "hands"
    world.say(
        f"{method_cfg.action}, and {method_cfg.proof}."
    )
    world.say(
        f"When they opened {collection_cfg.container}, every part of their collection was still inside."
    )


def reveal(world: World, source_cfg: Source, a: Entity, b: Entity) -> None:
    source = world.get("source")
    source.meters["understood"] += 1
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f"Then the truth showed itself at last: it had only been {source_cfg.reveal}."
    )
    world.say(
        f"{a.id} and {b.id} looked at each other, and the scary idea melted into a surprised laugh."
    )


def ending(world: World, a: Entity, b: Entity, collection_cfg: CollectionKind, parent: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"They carried {collection_cfg.container} back down together and showed it to their {parent.label_word}."
    )
    world.say(
        f'"No ghost stole our collection," {b.id} said. "We just needed two pairs of hands and a brave look."'
    )
    world.say(
        f"That night the collection sat safe on the table, and the children no longer thought of the place as haunted. They remembered it as the spot where teamwork made the dark seem small."
    )


def tell(
    place: Place,
    collection_cfg: CollectionKind,
    source_cfg: Source,
    method_cfg: Method,
    child1: str = "Lily",
    child1_gender: str = "girl",
    child2: str = "Tom",
    child2_gender: str = "boy",
    parent_type: str = "mother",
    trait1: str = "careful",
    trait2: str = "steady",
) -> World:
    world = World(place)
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="finder", traits=[trait1]))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="helper", traits=[trait2]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="place", label=place.label, attrs={"height": place.height}))
    collection = world.add(
        Entity(
            id="collection",
            type="collection",
            label=collection_cfg.noun,
            phrase=collection_cfg.phrase,
            owner=f"{a.id}&{b.id}",
            attrs={"container": collection_cfg.container, "location": "lap"},
            tags=set(collection_cfg.tags),
        )
    )
    collection.meters["safe"] = 1.0
    source = world.add(Entity(id="source", type="source", label=source_cfg.label, tags=set(source_cfg.tags)))
    plan = world.add(Entity(id="plan", type="plan", label=method_cfg.label, tags=set(method_cfg.tags)))

    introduce(world, a, b, collection_cfg, place)
    world.para()
    darken(world, a, b, parent)
    gust_and_spook(world, source_cfg)
    lose_collection(world, collection_cfg)
    world.para()
    decide_together(world, a, b, method_cfg)
    recover(world, method_cfg, collection_cfg)
    reveal(world, source_cfg, a, b)
    world.para()
    ending(world, a, b, collection_cfg, parent)

    world.facts.update(
        child1=a,
        child2=b,
        parent=parent,
        place=place,
        collection_cfg=collection_cfg,
        source_cfg=source_cfg,
        method_cfg=method_cfg,
        collection=collection,
        source=source,
        spooky=room.meters["spooky"] >= THRESHOLD,
        misplaced=collection.meters["found"] < THRESHOLD,
        found=collection.meters["found"] >= THRESHOLD,
        teamwork=plan.meters["active"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "collection": [
        (
            "What is a collection?",
            "A collection is a group of special things someone gathers and keeps together because they like them. People often sort them in a box, tin, or album."
        )
    ],
    "wind": [
        (
            "Why can wind sound spooky in an old place?",
            "Wind can push loose things and make tapping, rustling, or creaking sounds. In a quiet old place, those sounds can seem bigger and stranger than they really are."
        )
    ],
    "window": [
        (
            "What can a loose shutter do?",
            "A loose shutter can bang or tap against a window frame when the wind blows. That can make a sudden, surprising sound."
        )
    ],
    "sheet": [
        (
            "Why can a sheet look like a ghost?",
            "A sheet can puff up, droop, or flutter when air moves under it. In dim light, that can look like a white floating shape."
        )
    ],
    "owl": [
        (
            "Why might an owl seem scary in the dark?",
            "An owl can make a soft hooting sound, and its eyes can shine in dim light. If you do not know what made the sound, it can feel spooky at first."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help one another and do different parts of a job together. It can make a hard problem safer and easier to solve."
        )
    ],
    "stool": [
        (
            "Why should one child spot another on a stool?",
            "A spotter keeps the stool steady and watches carefully, which helps prevent a wobble or fall. Working together makes reaching something higher safer."
        )
    ],
    "careful": [
        (
            "What does it mean to do something carefully?",
            "Doing something carefully means moving slowly, paying attention, and trying not to make a mistake. Care helps keep people and things safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["collection", "wind", "window", "sheet", "owl", "teamwork", "stool", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    place = f["place"]
    collection_cfg = f["collection_cfg"]
    source_cfg = f["source_cfg"]
    return [
        f'Write a short ghost-story-style story for a 3-to-5-year-old that includes the word "collection".',
        f"Tell a gentle spooky story where {a.id} and {b.id} think a ghost is in {place.phrase}, but the scary sign comes from {source_cfg.label} and the children solve the problem with teamwork.",
        f"Write a child-facing story about a missing {collection_cfg.noun} collection, a surprise reveal, and two children helping each other instead of running away.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    parent = f["parent"]
    place = f["place"]
    collection_cfg = f["collection_cfg"]
    source_cfg = f["source_cfg"]
    method_cfg = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}. They were taking care of {collection_cfg.phrase} together."
        ),
        (
            "Where did the story happen?",
            f"It happened in {place.phrase}. The place felt spooky because it was dim and full of creaks and shadows."
        ),
        (
            "What went missing?",
            f"{collection_cfg.container} holding their collection slid out of sight. That is why the children suddenly felt scared."
        ),
        (
            "Why did the children think there might be a ghost?",
            f"They heard {source_cfg.sound} and saw that {source_cfg.flutter}. In the dark, those signs felt ghostly before they knew the real cause."
        ),
        (
            "How did the children solve the problem?",
            f"They used teamwork instead of panicking. {method_cfg.setup} Then {method_cfg.action}, so they got the box back safely."
        ),
        (
            "What was the surprise at the end?",
            f"The surprise was that there was no ghost at all. It had only been {source_cfg.reveal}, which explained both the sound and the spooky-looking movement."
        ),
        (
            f"What changed by the end of the story?",
            f"At first {a.id} and {b.id} felt frightened and unsure in the dark place. By the end they felt relieved and proud, because working together helped them rescue their collection and understand what had really happened."
        ),
        (
            f"What did they tell their {parent.label_word}?",
            f"They said no ghost had stolen their collection. They understood that two calm helpers had solved the mystery."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"collection", "teamwork", "careful"}
    tags |= set(f["source_cfg"].tags)
    if f["method_cfg"].id == "stool_spotter":
        tags.add("stool")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        collection="shells",
        source="sheet",
        method="stool_spotter",
        child1="Lily",
        child1_gender="girl",
        child2="Tom",
        child2_gender="boy",
        parent="mother",
        trait1="careful",
        trait2="steady",
    ),
    StoryParams(
        place="shed",
        collection="buttons",
        source="sheet",
        method="pair_reach",
        child1="Ben",
        child1_gender="boy",
        child2="Mia",
        child2_gender="girl",
        parent="father",
        trait1="curious",
        trait2="quiet",
    ),
    StoryParams(
        place="barn_loft",
        collection="feathers",
        source="owl",
        method="stool_spotter",
        child1="Zoe",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
        parent="mother",
        trait1="thoughtful",
        trait2="brave",
    ),
    StoryParams(
        place="attic",
        collection="buttons",
        source="shutter",
        method="stool_spotter",
        child1="Ava",
        child1_gender="girl",
        child2="Ella",
        child2_gender="girl",
        parent="father",
        trait1="quiet",
        trait2="steady",
    ),
]


def explain_source(place: Place, source: Source) -> str:
    if source.needs_window and not place.has_window:
        return f"(No story: {source.label} needs a place with a window, but {place.phrase} does not have one.)"
    if source.needs_sheet and not place.has_sheet:
        return f"(No story: {source.label} needs a hanging sheet or cover, but {place.phrase} has none.)"
    return "(No story: that spooky source does not fit this place.)"


def explain_method(place: Place, method: Method) -> str:
    return (
        f"(No story: {method.label} cannot safely reach a {place.height} hiding spot in {place.phrase}. "
        f"Pick a method that reaches {place.height} places.)"
    )


ASP_RULES = r"""
fits_source(P, S) :- place(P), source(S), not needs_window(S), not needs_sheet(S).
fits_source(P, S) :- place(P), source(S), needs_window(S), has_window(P), not needs_sheet(S).
fits_source(P, S) :- place(P), source(S), needs_sheet(S), has_sheet(P), not needs_window(S).
fits_source(P, S) :- place(P), source(S), needs_window(S), has_window(P), needs_sheet(S), has_sheet(P).

fits_method(P, M) :- place(P), method(M), height(P, H), reaches(M, H).

valid(P, C, S, M) :- place(P), collection(C), source(S), method(M), fits_source(P, S), fits_method(P, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("height", pid, place.height))
        if place.has_window:
            lines.append(asp.fact("has_window", pid))
        if place.has_sheet:
            lines.append(asp.fact("has_sheet", pid))
    for cid in COLLECTIONS:
        lines.append(asp.fact("collection", cid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if source.needs_window:
            lines.append(asp.fact("needs_window", sid))
        if source.needs_sheet:
            lines.append(asp.fact("needs_sheet", sid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for h in sorted(method.reaches):
            lines.append(asp.fact("reaches", mid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test story generation passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(5):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a spooky missing collection solved by teamwork and a surprise reveal."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--collection", choices=COLLECTIONS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in names if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        if not source_fits(place, source):
            raise StoryError(explain_source(place, source))
    if args.place and args.method:
        place = PLACES[args.place]
        method = METHODS[args.method]
        if not method_fits(place, method):
            raise StoryError(explain_method(place, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.collection is None or combo[1] == args.collection)
        and (args.source is None or combo[2] == args.source)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, collection_id, source_id, method_id = rng.choice(sorted(combos))
    child1, g1 = _pick_child(rng)
    child2, g2 = _pick_child(rng, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    return StoryParams(
        place=place_id,
        collection=collection_id,
        source=source_id,
        method=method_id,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        parent=parent,
        trait1=trait1,
        trait2=trait2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.collection not in COLLECTIONS:
        raise StoryError(f"(Invalid collection: {params.collection})")
    if params.source not in SOURCES:
        raise StoryError(f"(Invalid source: {params.source})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")

    place = PLACES[params.place]
    source = SOURCES[params.source]
    method = METHODS[params.method]
    if not source_fits(place, source):
        raise StoryError(explain_source(place, source))
    if not method_fits(place, method):
        raise StoryError(explain_method(place, method))

    world = tell(
        place=place,
        collection_cfg=COLLECTIONS[params.collection],
        source_cfg=source,
        method_cfg=method,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
        trait1=params.trait1,
        trait2=params.trait2,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, collection, source, method) combos:\n")
        for place, collection, source, method in combos:
            print(f"  {place:10} {collection:10} {source:8} {method}")
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
            header = f"### {p.child1} & {p.child2}: {p.collection} in {p.place} ({p.source}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
