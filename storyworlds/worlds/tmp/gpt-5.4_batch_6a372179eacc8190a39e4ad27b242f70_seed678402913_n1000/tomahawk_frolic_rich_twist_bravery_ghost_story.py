#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py
==============================================================================

A gentle ghost-story storyworld built from the seed words "tomahawk", "frolic",
and "rich", with the features Twist and Bravery.

This world models a child in a grand old house or theater who hears a spooky
sound during play. The frightening twist is that the ghost is not trying to
hurt anyone; it is only trying to get back a missing carved toy tomahawk from a
high or hidden place. The child must be brave enough to help, either alone or
with a trusted grown-up or cousin.

The reasonableness gate is small and explicit:
- each hiding place requires a particular helper tool
- only matching (hiding, aid) pairs are valid
- the ending depends on courage + company: a bold child can help alone; a timid
  child needs company, but still helps in the end

Run it
------
    python storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py
    python storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py --place manor --hiding trunk --aid brass_key
    python storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py --hiding rafters --aid brass_key
    python storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tomahawk_frolic_rich_twist_bravery_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we need to add the
# package dir storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BOLD_TRAITS = {"brave", "steady", "curious"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    rich_detail: str
    play_detail: str
    ghost_room: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    place_phrase: str
    sound: str
    need: str
    retrieve_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    use_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    type: str
    role_text: str
    brave_boost: int
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


def _r_cold_fear(world: World) -> list[str]:
    ghost = world.get("ghost")
    hero = world.get("hero")
    room = world.get("room")
    if ghost.memes["calling"] < THRESHOLD:
        return []
    sig = ("cold_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    hero.memes["fear"] += 1
    return []


def _r_return_peace(world: World) -> list[str]:
    ghost = world.get("ghost")
    hero = world.get("hero")
    room = world.get("room")
    item = world.get("item")
    if item.attrs.get("with_ghost") is not True:
        return []
    sig = ("return_peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["peace"] += 1
    ghost.memes["sadness"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["bravery"] += 1
    room.meters["cold"] = 0.0
    room.meters["warm"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="cold_fear", tag="emotion", apply=_r_cold_fear),
    Rule(name="return_peace", tag="emotion", apply=_r_return_peace),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "manor": Place(
        id="manor",
        label="a rich old manor",
        rich_detail="Its stairs curved like ribbons, and the walls wore gold frames that glimmered in the lamplight.",
        play_detail="The long rug was perfect for a frolic of chasing feet.",
        ghost_room="the portrait hall",
        ending_image="By bedtime, the portrait hall felt still and kind, and the house listened without shivering.",
        tags={"rich", "house"},
    ),
    "hotel": Place(
        id="hotel",
        label="a rich old hotel",
        rich_detail="Crystal lamps hung over red carpet, and every mirror made the hallway seem twice as grand.",
        play_detail="The empty corridor turned their frolic into soft echoing footsteps.",
        ghost_room="the music room",
        ending_image="By bedtime, the music room gave back only a sleepy hush, and the mirrors held calm light.",
        tags={"rich", "hotel"},
    ),
    "theater": Place(
        id="theater",
        label="a rich old theater",
        rich_detail="Velvet seats, painted ceilings, and brass rails made the whole place look rich enough for a king.",
        play_detail="The backstage lane gave their frolic room to dart and spin.",
        ghost_room="the costume loft",
        ending_image="By bedtime, the costume loft stopped creaking, and the velvet curtains rested in quiet folds.",
        tags={"rich", "theater"},
    ),
}

HIDING_SPOTS = {
    "trunk": HidingSpot(
        id="trunk",
        label="a locked cedar trunk",
        place_phrase="inside a locked cedar trunk under the window",
        sound="a soft thump from the old trunk",
        need="brass_key",
        retrieve_text="opened the trunk with a small click and found the painted wooden tomahawk tucked under a folded sash",
        tags={"trunk"},
    ),
    "rafters": HidingSpot(
        id="rafters",
        label="the high rafters",
        place_phrase="up in the high rafters above the room",
        sound="a tiny tapping from the beams over the child's head",
        need="long_hook",
        retrieve_text="reached up with the hook and eased the painted wooden tomahawk down from the dusty beam",
        tags={"rafters"},
    ),
    "portrait": HidingSpot(
        id="portrait",
        label="behind a crooked portrait",
        place_phrase="behind a crooked portrait beside the fireplace",
        sound="a thin scrape from the portrait frame",
        need="step_stool",
        retrieve_text="climbed the stool and slipped the painted wooden tomahawk out from behind the portrait frame",
        tags={"portrait"},
    ),
}

AIDS = {
    "brass_key": Aid(
        id="brass_key",
        label="brass key",
        phrase="a little brass key",
        use_text="used the brass key with careful fingers",
        qa_text="used a brass key to unlock the trunk",
        tags={"key"},
    ),
    "long_hook": Aid(
        id="long_hook",
        label="long hook",
        phrase="a long dressmaker's hook",
        use_text="lifted the long hook with both hands",
        qa_text="used a long hook to bring the toy down safely",
        tags={"hook"},
    ),
    "step_stool": Aid(
        id="step_stool",
        label="step stool",
        phrase="a painted step stool",
        use_text="set the step stool in place and climbed it slowly",
        qa_text="used a step stool to reach behind the portrait",
        tags={"stool"},
    ),
}

COMPANIONS = {
    "alone": Companion(
        id="alone",
        label="alone",
        type="none",
        role_text="No one walked beside the child, so every creak sounded bigger.",
        brave_boost=0,
        tags=set(),
    ),
    "cousin": Companion(
        id="cousin",
        label="cousin",
        type="girl",
        role_text="A cousin came too, close enough to squeeze a hand when the room turned cold.",
        brave_boost=1,
        tags={"family"},
    ),
    "aunt": Companion(
        id="aunt",
        label="aunt",
        type="aunt",
        role_text="A kind aunt came along with a lamp and a calm voice.",
        brave_boost=2,
        tags={"adult"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ruby", "Tessa", "Wren", "Elsie", "Clara"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Jasper", "Evan", "Felix", "Rowan", "Hugo"]
TRAITS = ["brave", "steady", "curious", "timid", "gentle", "quiet"]


def required_aid(hiding_id: str) -> str:
    return HIDING_SPOTS[hiding_id].need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for hiding_id, hiding in HIDING_SPOTS.items():
            for aid_id in AIDS:
                if required_aid(hiding_id) == aid_id:
                    combos.append((place_id, hiding_id, aid_id))
    return combos


def courage_score(trait: str, companion_id: str) -> int:
    base = 2 if trait in BOLD_TRAITS else 1
    return base + COMPANIONS[companion_id].brave_boost


def outcome_of(params: "StoryParams") -> str:
    return "solo_help" if courage_score(params.trait, params.companion) >= 2 and params.companion == "alone" else "guided_help"


def explain_rejection(hiding: HidingSpot, aid: Aid) -> str:
    need = AIDS[hiding.need]
    return (
        f"(No story: {hiding.label} reasonably needs {need.phrase}, not {aid.phrase}. "
        f"Pick the helper that can actually reach or open the hiding place.)"
    )


def predicted_need(hiding: HidingSpot) -> str:
    return {
        "trunk": "something small that could turn a lock",
        "rafters": "something long enough to reach the beam",
        "portrait": "something steady to stand on",
    }[hiding.id]


def predict_solution(world: World, hiding: HidingSpot, aid: Aid) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.attrs["found"] = required_aid(hiding.id) == aid.id
    return {
        "can_retrieve": bool(item.attrs["found"]),
        "need": predicted_need(hiding),
    }


def opening(world: World, hero: Entity, companion_ent: Optional[Entity], place: Place) -> None:
    world.say(
        f"{hero.id} was spending the evening in {place.label}. {place.rich_detail}"
    )
    if companion_ent is not None and companion_ent.role == "companion":
        world.say(
            f"{hero.id} and {companion_ent.id} began to frolic through the wide hallway. {place.play_detail}"
        )
    else:
        world.say(
            f"Before supper, {hero.id} had a little frolic through the wide hallway. {place.play_detail}"
        )


def stir_ghost(world: World, hero: Entity, hiding: HidingSpot, place: Place) -> None:
    ghost = world.get("ghost")
    ghost.memes["calling"] += 1
    ghost.memes["sadness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the warm lamps dimmed for a blink, and a chilly breath seemed to slip out of {place.ghost_room}."
    )
    world.say(
        f"{hero.id} stopped. From {hiding.place_phrase} came {hiding.sound}."
    )


def warning(world: World, hero: Entity, hiding: HidingSpot, aid: Aid) -> None:
    pred = predict_solution(world, hiding, aid)
    world.facts["predicted_need"] = pred["need"]
    if pred["can_retrieve"]:
        world.say(
            f"{hero.id} swallowed hard and looked at {aid.phrase}. It was exactly the sort of thing that could help with {pred['need']}."
        )
    else:
        world.say(
            f"{hero.id} peered into the gloom, but {aid.phrase} did not seem right. The hiding place needed {pred['need']}."
        )


def decide(world: World, hero: Entity, companion: Companion, companion_ent: Optional[Entity]) -> None:
    score = courage_score(hero.attrs["trait"], companion.id)
    hero.memes["resolve"] = float(score)
    if companion.id == "alone" and score >= 2:
        world.say(
            f'"I am scared," {hero.id} whispered, "but I can still be brave."'
        )
    elif companion.id == "alone":
        world.say(
            f'{hero.id} took one step toward the dark doorway, then another. Even with a shaky breath, {hero.pronoun()} kept going.'
        )
    else:
        assert companion_ent is not None
        world.say(companion.role_text)
        world.say(
            f"{hero.id} felt braver with {companion_ent.id} nearby and followed the sound into {world.place.ghost_room}."
        )


def reveal_ghost(world: World, hero: Entity, companion_ent: Optional[Entity]) -> None:
    ghost = world.get("ghost")
    hero.memes["fear"] += 1
    world.say(
        "A pale child-shape shimmered beside the cold wall, not with angry eyes, but with tears bright as raindrops."
    )
    if companion_ent is not None:
        world.say(
            f'{companion_ent.id} gasped, but the ghost only pointed at the hiding place and said, "My toy. I only want my toy."'
        )
    else:
        world.say(
            'The ghost lifted one transparent hand and said, "My toy. I only want my toy."'
        )
    ghost.memes["trust"] += 1
    world.say(
        f"That was the twist: the haunting was not a hunt at all. The ghost had lost a painted wooden tomahawk and had been crying for help."
    )


def retrieve(world: World, hero: Entity, hiding: HidingSpot, aid: Aid) -> None:
    item = world.get("item")
    hero.meters["reaching"] += 1
    world.say(
        f"{hero.id} {aid.use_text}, then {hiding.retrieve_text}."
    )
    item.attrs["found"] = True
    item.attrs["with_ghost"] = True
    propagate(world, narrate=False)


def comfort(world: World, hero: Entity, companion_ent: Optional[Entity]) -> None:
    ghost = world.get("ghost")
    if companion_ent is not None:
        world.say(
            f'{hero.id} held the toy out. "{ghost.label.capitalize()}, here," {hero.pronoun()} said, and {companion_ent.id} nodded beside {hero.pronoun("object")}.'
        )
    else:
        world.say(
            f'{hero.id} held the toy out with steady hands. "{ghost.label.capitalize()}, here," {hero.pronoun()} said.'
        )
    world.say(
        "The little spirit hugged the toy tomahawk to its chest. At once, the room lost its bitter chill."
    )


def ending(world: World, hero: Entity, companion_ent: Optional[Entity], place: Place) -> None:
    hero.memes["wonder"] += 1
    if companion_ent is not None:
        world.say(
            f"The ghost gave {hero.id} and {companion_ent.id} a grateful bow, then thinned into silver light and disappeared."
        )
    else:
        world.say(
            f"The ghost gave {hero.id} one grateful bow, then thinned into silver light and disappeared."
        )
    world.say(
        f"{place.ending_image} Later, when the lamps glowed warm again, {hero.id} could frolic there without fear."
    )


def tell(
    place: Place,
    hiding: HidingSpot,
    aid: Aid,
    companion: Companion,
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    trait: str = "brave",
    guardian_type: str = "aunt",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            traits=[trait],
            attrs={"trait": trait, "name": hero_name},
        )
    )
    world.add(
        Entity(
            id="ghost",
            kind="character",
            type="child",
            label="little ghost",
            phrase="a little ghost",
            role="ghost",
            tags={"ghost"},
        )
    )
    world.add(
        Entity(
            id="item",
            kind="thing",
            type="toy",
            label="painted wooden tomahawk",
            phrase="a painted wooden tomahawk",
            role="item",
            tags={"tomahawk"},
            attrs={"found": False, "with_ghost": False},
        )
    )
    world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=place.ghost_room,
            phrase=place.ghost_room,
            role="room",
        )
    )
    guardian = world.add(
        Entity(
            id="guardian",
            kind="character",
            type=guardian_type,
            label=f"the {guardian_type}",
            phrase=f"the {guardian_type}",
            role="guardian",
        )
    )

    companion_ent: Optional[Entity] = None
    if companion.id == "cousin":
        companion_ent = world.add(
            Entity(
                id="companion",
                kind="character",
                type="girl",
                label="Cora",
                phrase="Cora",
                role="companion",
                attrs={"name": "Cora"},
            )
        )
    elif companion.id == "aunt":
        companion_ent = guardian
        companion_ent.role = "companion"

    opening(world, hero, companion_ent if companion.id != "aunt" else None, place)
    world.para()
    stir_ghost(world, hero, hiding, place)
    warning(world, hero, hiding, aid)
    decide(world, hero, companion, companion_ent if companion.id != "aunt" else guardian)
    world.para()
    reveal_ghost(world, hero, companion_ent if companion.id != "aunt" else guardian)
    retrieve(world, hero, hiding, aid)
    comfort(world, hero, companion_ent if companion.id != "aunt" else guardian)
    world.para()
    ending(world, hero, companion_ent if companion.id != "aunt" else guardian, place)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        companion=companion,
        companion_ent=companion_ent if companion.id != "aunt" else guardian,
        place=place,
        hiding=hiding,
        aid=aid,
        item=world.get("item"),
        ghost=world.get("ghost"),
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                hiding=hiding.id,
                aid=aid.id,
                companion=companion.id,
                name=hero_name,
                gender=hero_gender,
                guardian=guardian_type,
                trait=trait,
                seed=None,
            )
        ),
        brave_score=courage_score(trait, companion.id),
    )
    return world


@dataclass
class StoryParams:
    place: str
    hiding: str
    aid: str
    companion: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="manor",
        hiding="trunk",
        aid="brass_key",
        companion="alone",
        name="Lila",
        gender="girl",
        guardian="aunt",
        trait="brave",
        seed=None,
    ),
    StoryParams(
        place="hotel",
        hiding="rafters",
        aid="long_hook",
        companion="cousin",
        name="Theo",
        gender="boy",
        guardian="uncle",
        trait="gentle",
        seed=None,
    ),
    StoryParams(
        place="theater",
        hiding="portrait",
        aid="step_stool",
        companion="aunt",
        name="Ruby",
        gender="girl",
        guardian="aunt",
        trait="timid",
        seed=None,
    ),
    StoryParams(
        place="manor",
        hiding="portrait",
        aid="step_stool",
        companion="alone",
        name="Milo",
        gender="boy",
        guardian="father",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        place="theater",
        hiding="trunk",
        aid="brass_key",
        companion="cousin",
        name="Clara",
        gender="girl",
        guardian="mother",
        trait="steady",
        seed=None,
    ),
]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale with something spooky in it, like whispers, shadows, or a spirit. In a gentle ghost story, the scary thing may turn out not to be mean at all.",
        )
    ],
    "tomahawk": [
        (
            "What is a tomahawk in this story?",
            "Here it is a small carved toy tomahawk, not a real weapon. It is an old plaything the ghost loved and wanted back.",
        )
    ],
    "rich": [
        (
            "What does rich mean when a house looks rich?",
            "It means the place looks grand and fancy, with things like velvet, brass, gold frames, or shining lamps. It does not mean the house itself is a person with money.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared. A brave person can have a shaky heart and still take a careful step forward.",
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key turns a lock so something closed can be opened. People use the right key for the right lock.",
        )
    ],
    "hook": [
        (
            "What can a long hook help with?",
            "A long hook can reach something that is too high to grab by hand. It helps pull an object down carefully.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps a small person stand a little higher. It can help someone reach a shelf or picture safely.",
        )
    ],
    "adult": [
        (
            "Why can asking a grown-up for help be brave?",
            "Because it means telling the truth about being scared and choosing a safe helper. Brave choices are not always lonely choices.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "tomahawk", "rich", "bravery", "key", "hook", "stool", "adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    hiding = f["hiding"]
    companion = f["companion"]
    if companion.id == "alone":
        return [
            'Write a gentle ghost story for a 3-to-5-year-old that includes the words "tomahawk", "frolic", and "rich".',
            f"Tell a spooky-but-kind story where a {hero.type} named {hero.attrs['name']} explores {place.label} alone and learns the ghost only wants a missing toy back.",
            f"Write a story with a twist: the sound from {hiding.label} seems scary at first, but bravery reveals a lonely ghost asking for help.",
        ]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "tomahawk", "frolic", and "rich".',
        f"Tell a child-friendly haunted-house story where {hero.attrs['name']} follows a spooky sound through {place.label} with help from {companion.label}.",
        "Write a story with bravery and a kind twist: the ghost is sad, not mean, and peace returns when the lost toy is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    companion = f["companion"]
    companion_ent = f["companion_ent"]
    place = f["place"]
    hiding = f["hiding"]
    aid = f["aid"]
    outcome = f["outcome"]
    comp_phrase = "alone"
    if companion.id != "alone" and companion_ent is not None:
        comp_phrase = f"with {companion_ent.label if companion_ent.id == 'guardian' else companion_ent.attrs.get('name', companion_ent.label)}"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']}, a child in {place.label}, and a little ghost who needed help. {guardian.label_word.capitalize()} was part of the safe world around the child too.",
        ),
        (
            "What made the place feel spooky?",
            f"The lamps dimmed, the room turned cold, and a strange sound came from {hiding.place_phrase}. Those clues made the child think something ghostly was near.",
        ),
        (
            "What was the twist in the story?",
            "The ghost was not chasing anyone or trying to be cruel. It was only sad because it had lost its painted toy tomahawk and did not know how to get it back.",
        ),
        (
            f"How did {hero.attrs['name']} show bravery?",
            f"{hero.attrs['name']} went into the spooky room {comp_phrase} even while feeling scared. Bravery mattered because the ghost needed someone kind enough to stay and help.",
        ),
        (
            "How did the child get the tomahawk?",
            f"The child {aid.qa_text}. That worked because the toy was hidden at {hiding.place_phrase}, and this helper fit that exact problem.",
        ),
    ]
    if outcome == "solo_help":
        qa.append(
            (
                "Did the child need help from anyone else?",
                f"No one had to stand right beside {hero.attrs['name']} in the ghost room. The child was frightened, but still solved the problem alone with careful hands.",
            )
        )
    else:
        helper_name = "a helper"
        if companion_ent is not None:
            helper_name = companion_ent.label_word if companion_ent.id == "guardian" else companion_ent.attrs.get("name", companion_ent.label)
        qa.append(
            (
                "Why was having company important?",
                f"Having {helper_name} nearby made the child feel steadier. The company did not change what the ghost wanted, but it gave the child enough courage to keep going.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"Once the ghost got the toy tomahawk back, the room lost its chill and the haunting stopped. The ending image shows change because {hero.attrs['name']} could frolic there again without fear.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "tomahawk", "rich", "bravery"}
    aid = f["aid"]
    tags |= set(aid.tags)
    if f["companion"].id == "aunt":
        tags.add("adult")
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
    for e in world.entities.values():
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
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, H, A) :- place(P), hiding(H), aid(A), needs(H, A).

bold_trait(T) :- trait_name(T), is_bold(T).
base_courage(2) :- chosen_trait(T), bold_trait(T).
base_courage(1) :- chosen_trait(T), not bold_trait(T).
total_courage(C + B) :- base_courage(C), chosen_companion(Co), boost(Co, B).

outcome(solo_help) :- chosen_companion(alone), total_courage(V), V >= 2.
outcome(guided_help) :- not outcome(solo_help).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for hiding_id, hiding in HIDING_SPOTS.items():
        lines.append(asp.fact("hiding", hiding_id))
        lines.append(asp.fact("needs", hiding_id, hiding.need))
    for aid_id in AIDS:
        lines.append(asp.fact("aid", aid_id))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(BOLD_TRAITS):
        lines.append(asp.fact("is_bold", trait))
    for companion_id, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", companion_id))
        lines.append(asp.fact("boost", companion_id, companion.brave_boost))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_companion", params.companion),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated empty story.)")
    with io.StringIO() as buf, redirect_stdout(buf):
        emit(sample, trace=True, qa=True, header="### smoke")
        output = buf.getvalue()
    if "tomahawk" not in sample.story or "frolic" not in sample.story or "rich" not in sample.story:
        raise StoryError("(Smoke test failed: seed words missing from story.)")
    if "### smoke" not in output:
        raise StoryError("(Smoke test failed: emit() did not print header.)")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a brave child helps a lonely ghost recover a lost toy tomahawk."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hiding", choices=HIDING_SPOTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hiding and args.aid:
        hiding = HIDING_SPOTS[args.hiding]
        aid = AIDS[args.aid]
        if required_aid(args.hiding) != args.aid:
            raise StoryError(explain_rejection(hiding, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hiding is None or combo[1] == args.hiding)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, hiding, aid = rng.choice(sorted(combos))
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        hiding=hiding,
        aid=aid,
        companion=companion,
        name=name,
        gender=gender,
        guardian=guardian,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hiding not in HIDING_SPOTS:
        raise StoryError(f"(Unknown hiding place: {params.hiding})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")
    if params.guardian not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown guardian: {params.guardian})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if required_aid(params.hiding) != params.aid:
        raise StoryError(explain_rejection(HIDING_SPOTS[params.hiding], AIDS[params.aid]))

    world = tell(
        place=PLACES[params.place],
        hiding=HIDING_SPOTS[params.hiding],
        aid=AIDS[params.aid],
        companion=COMPANIONS[params.companion],
        hero_name=params.name,
        hero_gender=params.gender,
        trait=params.trait,
        guardian_type=params.guardian,
    )
    # Replace internal id with display name in prose and QA-friendly facts.
    story = world.render().replace("hero", params.name)
    world.facts["hero"].attrs["name"] = params.name
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hiding, aid) combos:\n")
        for place, hiding, aid in combos:
            print(f"  {place:8} {hiding:9} {aid}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place}, {p.hiding}, {p.aid}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
