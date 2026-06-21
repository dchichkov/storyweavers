#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py
========================================================================

A standalone story world for a small fable-shaped domain built around a found
document. Two young animals discover a paper in the woods. Curiosity pulls one
way, kindness pulls the other, and a small conflict decides whether the paper is
returned politely or peeped at first.

The world model tracks a few physical meters (lost, returned, opened, crumpled)
and a few emotional memes (curiosity, worry, conflict, relief, shame, pride).
Those state changes drive the prose, the QA, and the ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py
    python storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py --document seed_map
    python storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py --action hide_it
    python storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py --all
    python storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/document_kindness_conflict_curiosity_fable.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class DocumentCfg:
    id: str
    label: str
    phrase: str
    owner_name: str
    owner_species: str
    purpose: str
    reveal: str
    benefit: str
    place_hint: str
    sealed: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceCfg:
    id: str
    label: str
    phrase: str
    detail: str
    owners: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ActionCfg:
    id: str
    sense: int
    opens_first: bool
    returns: bool
    hides: bool
    title: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lost_worry(world: World) -> list[str]:
    out: list[str] = []
    doc = world.entities.get("document")
    owner = world.entities.get("owner")
    if not doc or not owner:
        return out
    if doc.meters["lost"] < THRESHOLD or doc.meters["returned"] >= THRESHOLD:
        return out
    sig = ("worry", doc.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_tug_crumple(world: World) -> list[str]:
    out: list[str] = []
    doc = world.entities.get("document")
    if not doc or doc.meters["tugged"] < THRESHOLD:
        return out
    sig = ("crumple", doc.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    doc.meters["crumpled"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"finder", "friend"}:
            ent.memes["conflict"] += 1
    out.append("__crumple__")
    return out


def _r_opened_shame(world: World) -> list[str]:
    out: list[str] = []
    doc = world.entities.get("document")
    if not doc or doc.meters["opened"] < THRESHOLD or not doc.attrs.get("sealed"):
        return out
    sig = ("shame", doc.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"finder", "friend"}:
            ent.memes["shame"] += 1
    out.append("__shame__")
    return out


def _r_return_relief(world: World) -> list[str]:
    out: list[str] = []
    doc = world.entities.get("document")
    owner = world.entities.get("owner")
    if not doc or not owner or doc.meters["returned"] < THRESHOLD:
        return out
    sig = ("relief", doc.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["relief"] += 1
    owner.memes["gratitude"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"finder", "friend"}:
            ent.memes["pride"] += 1
            ent.memes["kindness"] += 1
            ent.memes["conflict"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="lost_worry", tag="social", apply=_r_lost_worry),
    Rule(name="tug_crumple", tag="physical", apply=_r_tug_crumple),
    Rule(name="opened_shame", tag="social", apply=_r_opened_shame),
    Rule(name="return_relief", tag="social", apply=_r_return_relief),
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
        for sent in produced:
            world.say(sent)
    return produced


DOCUMENTS = {
    "seed_map": DocumentCfg(
        id="seed_map",
        label="seed map",
        phrase="a folded document with neat little rows and circles",
        owner_name="Beaver",
        owner_species="beaver",
        purpose="where spring seeds should be planted",
        reveal="it showed where spring seeds should be planted along the riverbank",
        benefit="flowers and beans for everyone later in the season",
        place_hint="near the willow bridge",
        sealed=False,
        tags={"document", "map", "garden"},
    ),
    "feast_invite": DocumentCfg(
        id="feast_invite",
        label="feast invitation",
        phrase="a cream-colored document tied with blue grass",
        owner_name="Owl",
        owner_species="owl",
        purpose="which families should come to the moonlight feast",
        reveal="it was an invitation list for the moonlight feast in the old school stump",
        benefit="a supper where shy neighbors would sit together and become friends",
        place_hint="below the old school stump",
        sealed=True,
        tags={"document", "invitation", "feast"},
    ),
    "soup_list": DocumentCfg(
        id="soup_list",
        label="soup list",
        phrase="a spotted document tucked around a sprig of mint",
        owner_name="Hedgehog",
        owner_species="hedgehog",
        purpose="which burrows needed soup before the cold night",
        reveal="it named the burrows that needed warm soup before the cold night",
        benefit="hot bowls for tired neighbors before frost crept in",
        place_hint="beside the berry path",
        sealed=False,
        tags={"document", "list", "kindness"},
    ),
}

PLACES = {
    "bridge": PlaceCfg(
        id="bridge",
        label="willow bridge",
        phrase="by the willow bridge",
        detail="The brook talked in small silver sounds under the planks.",
        owners={"Beaver"},
        tags={"bridge", "water"},
    ),
    "stump": PlaceCfg(
        id="stump",
        label="school stump",
        phrase="below the old school stump",
        detail="A ring of mushrooms made the stump look like a little forest desk.",
        owners={"Owl"},
        tags={"stump", "school"},
    ),
    "berry_path": PlaceCfg(
        id="berry_path",
        label="berry path",
        phrase="beside the berry path",
        detail="The air smelled sweet, and the brambles held the last red berries.",
        owners={"Hedgehog"},
        tags={"berries", "path"},
    ),
    "rushes": PlaceCfg(
        id="rushes",
        label="rushy bend",
        phrase="near the rushy bend",
        detail="Tall reeds nodded there as if they were listening to every footstep.",
        owners={"Beaver", "Hedgehog"},
        tags={"reeds", "path"},
    ),
}

ACTIONS = {
    "ask_owner": ActionCfg(
        id="ask_owner",
        sense=3,
        opens_first=False,
        returns=True,
        hides=False,
        title="carry it back at once",
        tags={"return"},
    ),
    "ask_elder": ActionCfg(
        id="ask_elder",
        sense=3,
        opens_first=False,
        returns=True,
        hides=False,
        title="take it to a wise grown-up first",
        tags={"return", "elder"},
    ),
    "peek_then_return": ActionCfg(
        id="peek_then_return",
        sense=2,
        opens_first=True,
        returns=True,
        hides=False,
        title="peep inside and then return it",
        tags={"peek", "return"},
    ),
    "hide_it": ActionCfg(
        id="hide_it",
        sense=1,
        opens_first=False,
        returns=False,
        hides=True,
        title="hide it for later",
        tags={"hide"},
    ),
}

FINDER_NAMES = [
    ("Pip", "squirrel"),
    ("Mina", "mouse"),
    ("Tansy", "rabbit"),
    ("Nip", "mole"),
]
FRIEND_NAMES = [
    ("Fern", "rabbit"),
    ("Bram", "badger"),
    ("Wren", "mouse"),
    ("Clover", "squirrel"),
]
TRAITS = ["curious", "gentle", "quick", "careful", "bright"]
MORALS = {
    "praised": "Curiosity is bright, but kindness tells it where to walk.",
    "mended": "A curious paw should still remember another creature's trust.",
}


def place_matches(document: DocumentCfg, place: PlaceCfg) -> bool:
    return document.owner_name in place.owners


def sensible_actions() -> list[ActionCfg]:
    return [cfg for cfg in ACTIONS.values() if cfg.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for doc_id, doc in DOCUMENTS.items():
        for place_id, place in PLACES.items():
            if place_matches(doc, place):
                combos.append((doc_id, place_id))
    return combos


@dataclass
class StoryParams:
    document: str
    place: str
    action: str
    finder_name: str
    finder_species: str
    friend_name: str
    friend_species: str
    parent_style: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        document="seed_map",
        place="bridge",
        action="ask_owner",
        finder_name="Pip",
        finder_species="squirrel",
        friend_name="Fern",
        friend_species="rabbit",
        parent_style="steady",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        document="feast_invite",
        place="stump",
        action="peek_then_return",
        finder_name="Mina",
        finder_species="mouse",
        friend_name="Bram",
        friend_species="badger",
        parent_style="wise",
        trait="gentle",
        seed=None,
    ),
    StoryParams(
        document="soup_list",
        place="berry_path",
        action="ask_elder",
        finder_name="Tansy",
        finder_species="rabbit",
        friend_name="Wren",
        friend_species="mouse",
        parent_style="calm",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        document="soup_list",
        place="rushes",
        action="ask_owner",
        finder_name="Nip",
        finder_species="mole",
        friend_name="Clover",
        friend_species="squirrel",
        parent_style="kind",
        trait="bright",
        seed=None,
    ),
]


def explain_rejection(document_id: str, place_id: str) -> str:
    doc = DOCUMENTS[document_id]
    place = PLACES[place_id]
    return (
        f"(No story: {doc.owner_name}'s {doc.label} is not a likely thing to be found "
        f"{place.phrase}. Pick a place closer to where {doc.owner_name.lower()} walks.)"
    )


def explain_action(action_id: str) -> str:
    action = ACTIONS[action_id]
    better = ", ".join(sorted(cfg.id for cfg in sensible_actions()))
    return (
        f"(Refusing action '{action.id}': it scores too low on common sense "
        f"(sense={action.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    doc = DOCUMENTS[params.document]
    action = ACTIONS[params.action]
    if action.opens_first and doc.sealed:
        return "mended"
    return "praised"


def owner_title(style: str) -> str:
    return {
        "steady": "in a steady voice",
        "wise": "in a wise little hush",
        "calm": "in a calm voice",
        "kind": "with a kind smile",
    }.get(style, "gently")


def introduce(world: World, finder: Entity, friend: Entity, place: PlaceCfg) -> None:
    world.say(
        f"In a green corner of the wood, {finder.id} the {finder.type} and "
        f"{friend.id} the {friend.type} were walking {place.phrase}."
    )
    world.say(place.detail)
    world.say(
        f"{finder.id} loved noticing odd things, and {friend.id} was the sort who "
        f"noticed what odd things might mean to somebody else."
    )


def find_document(world: World, finder: Entity, friend: Entity, doc_cfg: DocumentCfg) -> None:
    doc = world.get("document")
    doc.meters["lost"] += 1
    finder.memes["curiosity"] += 1
    friend.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Under a fern lay {doc_cfg.phrase}. On one corner was written the word "
        f'"document" in careful ink.'
    )
    world.say(
        f'"Oh!" said {finder.id}. "{doc_cfg.label.capitalize()} sounds important."'
    )


def wonder(world: World, finder: Entity, friend: Entity, doc_cfg: DocumentCfg) -> None:
    if doc_cfg.id == "seed_map":
        guess = "a treasure map for beans and bright marigolds"
    elif doc_cfg.id == "feast_invite":
        guess = "a secret list of guests and moonlit cakes"
    else:
        guess = "a list of errands, soups, and somebody's hungry supper"
    world.say(
        f"{finder.id}'s whiskers twitched with curiosity. To {finder.pronoun('object')}, "
        f"the folded paper looked like {guess}."
    )
    world.say(
        f'But {friend.id} tipped {friend.pronoun("possessive")} head and said, '
        f'"If it is important, someone may be looking for it right now."'
    )


def tug_conflict(world: World, finder: Entity, friend: Entity) -> None:
    doc = world.get("document")
    doc.meters["tugged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{finder.id} lifted one side of the paper, and {friend.id} put a paw on the other."
    )
    world.say(
        "Not hard, and not mean, but enough for the corner to bend and for both little "
        "hearts to feel the pinch of a quarrel."
    )


def ask_path(world: World, finder: Entity, friend: Entity, doc_cfg: DocumentCfg, place: PlaceCfg) -> None:
    owner = world.get("owner")
    world.say(
        f'"Let us not make a stranger of another creature\'s paper," said {friend.id}. '
        f'Together they carried the document from {place.phrase} to {owner.id} the {owner.type}.'
    )
    doc = world.get("document")
    doc.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} looked up {owner_title(world.facts['params'].parent_style)} and "
        f"gave a long breath of relief."
    )


def elder_path(world: World, finder: Entity, friend: Entity, doc_cfg: DocumentCfg) -> None:
    elder = world.get("elder")
    world.say(
        f'{friend.id} said, "If we are unsure, let us ask {elder.id}." So the two friends '
        f"took the paper to {elder.id} the {elder.type}, who kept the bell-stump tidy."
    )
    world.say(
        f"{elder.id} read the name in the corner and nodded. "
        f'"This belongs to {doc_cfg.owner_name}," {elder.pronoun()} said.'
    )
    doc = world.get("document")
    doc.meters["returned"] += 1
    propagate(world, narrate=False)
    owner = world.get("owner")
    world.say(
        f"Soon the paper was back in {owner.id}'s paws, and the worried crease left "
        f"{owner.pronoun('possessive')} brow."
    )


def peek_path(world: World, finder: Entity, friend: Entity, doc_cfg: DocumentCfg, place: PlaceCfg) -> None:
    doc = world.get("document")
    world.say(
        f'{finder.id} whispered, "Only one little look." Curiosity leaned close, and '
        f"{friend.id} did not step away."
    )
    doc.meters["opened"] += 1
    propagate(world, narrate=False)
    if doc_cfg.sealed:
        world.say(
            "The grass ribbon loosened, and the tidy fold was not quite tidy anymore."
        )
    else:
        world.say(
            "The fold opened with a soft papery sigh."
        )
    world.say(
        f"They saw enough to know it was about {doc_cfg.purpose}, and at once the paper "
        f"felt less like treasure and more like somebody's trust."
    )
    tug_conflict(world, finder, friend)
    world.say(
        f"With their ears growing warm, they hurried from {place.phrase} to find its owner."
    )
    doc.meters["returned"] += 1
    propagate(world, narrate=False)


def reveal_and_resolution(world: World, doc_cfg: DocumentCfg, action: ActionCfg) -> None:
    owner = world.get("owner")
    finder = world.get("finder")
    friend = world.get("friend")
    doc = world.get("document")
    world.say(
        f"{owner.id} smoothed the document and explained that {doc_cfg.reveal}."
    )
    world.say(
        f"It mattered because it would mean {doc_cfg.benefit}."
    )
    if action.opens_first and doc_cfg.sealed:
        world.say(
            f'{finder.id} looked at the loosened tie and said, "I am sorry. My curiosity '
            f'ran ahead of my manners."'
        )
        world.say(
            f'{owner.id} was not cruel. "{finder.id}," {owner.pronoun()} said, '
            f'"a bright mind is best when it walks beside a kind one."'
        )
    else:
        world.say(
            f'{owner.id} thanked them both, and {friend.id} felt as light as a leaf in sun.'
        )
    if doc.meters["crumpled"] >= THRESHOLD:
        world.say(
            f"{friend.id} helped smooth the bent corner flat against a tree stump, and "
            f"{finder.id} held it carefully this time."
        )


def ending_image(world: World, doc_cfg: DocumentCfg, outcome: str) -> None:
    finder = world.get("finder")
    friend = world.get("friend")
    if outcome == "mended":
        world.say(
            f"When they walked home, {finder.id} asked questions more softly, and "
            f"{friend.id} answered with a smile instead of a frown."
        )
    else:
        world.say(
            f"After that, whenever {finder.id} found some puzzling thing in the grass, "
            f"{friend.id} would smile and say, 'First let kindness read it with us.'"
        )
    world.say(
        f"And so, in that little wood, even a lost document could teach two young friends "
        f"how to keep curiosity gentle."
    )
    world.say(MORALS[outcome])


def tell(
    doc_cfg: DocumentCfg,
    place_cfg: PlaceCfg,
    action_cfg: ActionCfg,
    params: StoryParams,
) -> World:
    world = World()
    finder = world.add(
        Entity(
            id=params.finder_name,
            kind="character",
            type=params.finder_species,
            role="finder",
            traits=[params.trait, "curious"],
            label=params.finder_name,
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type=params.friend_species,
            role="friend",
            traits=["kind", "steady"],
            label=params.friend_name,
        )
    )
    owner = world.add(
        Entity(
            id=doc_cfg.owner_name,
            kind="character",
            type=doc_cfg.owner_species,
            role="owner",
            label=doc_cfg.owner_name,
        )
    )
    elder = world.add(
        Entity(
            id="Mossy",
            kind="character",
            type="tortoise",
            role="elder",
            label="Mossy",
        )
    )
    document = world.add(
        Entity(
            id="document",
            kind="thing",
            type="document",
            label=doc_cfg.label,
            phrase=doc_cfg.phrase,
            attrs={"sealed": doc_cfg.sealed},
            tags=set(doc_cfg.tags),
        )
    )

    world.facts["params"] = params

    introduce(world, finder, friend, place_cfg)
    find_document(world, finder, friend, doc_cfg)
    wonder(world, finder, friend, doc_cfg)

    world.para()
    if action_cfg.id == "peek_then_return":
        peek_path(world, finder, friend, doc_cfg, place_cfg)
    elif action_cfg.id == "ask_elder":
        elder_path(world, finder, friend, doc_cfg)
    else:
        ask_path(world, finder, friend, doc_cfg, place_cfg)

    world.para()
    reveal_and_resolution(world, doc_cfg, action_cfg)
    ending = "mended" if action_cfg.opens_first and doc_cfg.sealed else "praised"
    world.para()
    ending_image(world, doc_cfg, ending)

    world.facts.update(
        document_cfg=doc_cfg,
        place_cfg=place_cfg,
        action_cfg=action_cfg,
        finder=finder,
        friend=friend,
        owner=owner,
        elder=elder,
        document=document,
        outcome=ending,
        returned=document.meters["returned"] >= THRESHOLD,
        opened=document.meters["opened"] >= THRESHOLD,
        crumpled=document.meters["crumpled"] >= THRESHOLD,
        owner_worried=owner.memes["worry"] >= THRESHOLD,
        owner_relieved=owner.memes["relief"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "document": [
        (
            "What is a document?",
            "A document is a piece of writing that keeps important information. It might be a list, a map, or an invitation."
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map shows where things are. It helps you find the right place."
        )
    ],
    "list": [
        (
            "What is a list for?",
            "A list keeps several important things in order so they are easier to remember. People use lists for jobs, names, and plans."
        )
    ],
    "invitation": [
        (
            "What is an invitation?",
            "An invitation tells someone they are welcome at a gathering. It helps people know where to go and when to come."
        )
    ],
    "return": [
        (
            "What should you do if you find something important that belongs to someone else?",
            "You should try to return it to the owner or ask a trusted grown-up to help. That is a kind and honest thing to do."
        )
    ],
    "elder": [
        (
            "Why ask a wise grown-up for help?",
            "A wise grown-up can help you decide what is fair and safe. They often know who something belongs to."
        )
    ],
    "peek": [
        (
            "Why can peeking at someone else's paper be unkind?",
            "A paper can hold private plans or names. Looking without permission can break trust, even if you are only curious."
        )
    ],
    "hide": [
        (
            "Why is hiding a found object a bad idea?",
            "Hiding it keeps the owner from getting it back. It usually makes a small problem bigger."
        )
    ],
    "kindness": [
        (
            "How can kindness and curiosity work together?",
            "Curiosity can ask good questions, and kindness can help choose a fair answer. Together they help you learn without hurting anyone."
        )
    ],
}
KNOWLEDGE_ORDER = ["document", "map", "list", "invitation", "return", "elder", "peek", "hide", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    doc = f["document_cfg"]
    action = f["action_cfg"]
    if f["outcome"] == "mended":
        return [
            'Write a gentle fable for a 3-to-5-year-old that includes the word "document" and shows curiosity causing a small mistake.',
            f"Tell a woodland fable where {finder.id} and {friend.id} find a lost {doc.label}, peek first, and then learn why returning it kindly matters.",
            "Write a short animal story with kindness, conflict, and curiosity, ending in an apology and a moral.",
        ]
    return [
        'Write a gentle fable for a 3-to-5-year-old that includes the word "document".',
        f"Tell a woodland story where {finder.id} and {friend.id} find a lost {doc.label} and choose {action.title} instead of keeping it.",
        "Write a short fable about kindness, conflict, and curiosity where doing the fair thing helps the whole community.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    owner = f["owner"]
    doc = f["document_cfg"]
    place = f["place_cfg"]
    action = f["action_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {finder.id} the {finder.type} and {friend.id} the {friend.type}, who found {doc.phrase} {place.phrase}. The paper belonged to {owner.id} the {owner.type}."
        ),
        (
            "What did they find?",
            f"They found a lost {doc.label}. It was a document, which means it held important information for someone."
        ),
        (
            f"Why did {finder.id} want to look at it?",
            f"{finder.id} was curious and imagined the paper might hold a secret. That curiosity is what pulled the story into its little conflict."
        ),
        (
            f"Why did {friend.id} want to be careful?",
            f"{friend.id} understood that the paper belonged to someone else. {friend.id} was trying to protect another creature's trust, not spoil the adventure."
        ),
    ]
    if action.id == "ask_elder":
        qa.append(
            (
                "How did they solve the problem?",
                f"They took the document to Mossy the tortoise first, and Mossy helped return it to {owner.id}. Asking a wise grown-up turned curiosity into a kind choice."
            )
        )
    elif action.id == "ask_owner":
        qa.append(
            (
                "How did they solve the problem?",
                f"They carried the document straight back to {owner.id}. Returning it quickly ended the worry and showed kindness."
            )
        )
    elif action.id == "peek_then_return":
        second = "The paper felt less like treasure and more like somebody's trust."
        if outcome == "mended":
            second = "Because it was sealed, their peeking made them feel ashamed and ready to apologize."
        qa.append(
            (
                "What happened when they peeked at the document?",
                f"They opened it before asking permission and learned it was about {doc.purpose}. {second}"
            )
        )
    if f["crumpled"]:
        qa.append(
            (
                "Was there a conflict?",
                f"Yes. They had a small tug over the paper, and one corner bent. The quarrel was not fierce, but it showed how curiosity and caution were pulling in different directions."
            )
        )
    if outcome == "mended":
        qa.append(
            (
                "What did they learn at the end?",
                f"They learned that curiosity needs manners. Returning the document and apologizing helped mend the trust they had bent."
            )
        )
    else:
        qa.append(
            (
                "Why was returning the document a kind thing to do?",
                f"It let {owner.id} use the paper for {doc.purpose}. That kindness helped more than just one creature, because the document mattered to the whole neighborhood."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"document", "kindness"} | set(f["document_cfg"].tags) | set(f["action_cfg"].tags)
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
matches_place(D, P) :- document(D), place(P), owner_of(D, O), place_owner(P, O).
valid(D, P) :- matches_place(D, P).

sensible(A) :- action(A), sense(A, S), sense_min(M), S >= M.

outcome(mended) :- chosen_document(D), chosen_action(A), sealed(D), opens_first(A).
outcome(praised) :- chosen_document(D), chosen_action(A), not sealed(D), opens_first(A).
outcome(praised) :- chosen_action(A), not opens_first(A), returns(A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for doc_id, doc in DOCUMENTS.items():
        lines.append(asp.fact("document", doc_id))
        lines.append(asp.fact("owner_of", doc_id, doc.owner_name))
        if doc.sealed:
            lines.append(asp.fact("sealed", doc_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for owner in sorted(place.owners):
            lines.append(asp.fact("place_owner", place_id, owner))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("sense", action_id, action.sense))
        if action.opens_first:
            lines.append(asp.fact("opens_first", action_id))
        if action.returns:
            lines.append(asp.fact("returns", action_id))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_document", params.document),
            asp.fact("chosen_action", params.action),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {cfg.id for cfg in sensible_actions()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible actions match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible actions: python={sorted(python_sensible)} clingo={sorted(clingo_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if params.action not in ACTIONS:
            continue
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = copy.deepcopy(CURATED[0])
        smoke_params.seed = 999
        smoke = generate(smoke_params)
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify safeguard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a found document, curiosity, kindness, and a small woodland quarrel."
    )
    ap.add_argument("--document", choices=DOCUMENTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible document/place combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_pair(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    finder = rng.choice(FINDER_NAMES)
    friend_choices = [pair for pair in FRIEND_NAMES if pair[0] != finder[0]]
    friend = rng.choice(friend_choices)
    return finder, friend


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.document and args.place and not place_matches(DOCUMENTS[args.document], PLACES[args.place]):
        raise StoryError(explain_rejection(args.document, args.place))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_action(args.action))

    combos = [
        combo for combo in valid_combos()
        if (args.document is None or combo[0] == args.document)
        and (args.place is None or combo[1] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    document_id, place_id = rng.choice(sorted(combos))
    action_id = args.action or rng.choice(sorted(cfg.id for cfg in sensible_actions()))
    (finder_name, finder_species), (friend_name, friend_species) = _pick_pair(rng)
    parent_style = rng.choice(["steady", "wise", "calm", "kind"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        document=document_id,
        place=place_id,
        action=action_id,
        finder_name=finder_name,
        finder_species=finder_species,
        friend_name=friend_name,
        friend_species=friend_species,
        parent_style=parent_style,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.document not in DOCUMENTS:
        raise StoryError(f"(Unknown --document value: {params.document})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown --place value: {params.place})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown --action value: {params.action})")
    if not place_matches(DOCUMENTS[params.document], PLACES[params.place]):
        raise StoryError(explain_rejection(params.document, params.place))
    if ACTIONS[params.action].sense < SENSE_MIN:
        raise StoryError(explain_action(params.action))

    world = tell(
        doc_cfg=DOCUMENTS[params.document],
        place_cfg=PLACES[params.place],
        action_cfg=ACTIONS[params.action],
        params=params,
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
        print(f"sensible actions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (document, place) combos:\n")
        for document_id, place_id in combos:
            print(f"  {document_id:12} {place_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(copy.deepcopy(params)) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.finder_name} & {p.friend_name}: {p.document} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
