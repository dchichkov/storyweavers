#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py
==========================================================

A gentle ghost-story world: a child hears a strange voice in an old place,
jumps in fright, bumps a buttock on the rug or floor, and learns that the ghost
is not hunting for people at all. The ghost only wants one small thing set
right. A calm helper listens, the child joins in, and the room changes from
eerie to peaceful.

The world is state-driven:
- an omen raises fear and eerie pressure;
- finding the ghost's keepsake changes what can happen next;
- the chosen helping action either settles the ghost or leaves it lingering;
- settled ghosts lower fear and raise relief, which the ending proves.

Run it
------
    python storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py --place nursery --ghost child
    python storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py --ghost sailor --action polish_lantern
    python storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py --action slam_door
    python storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/buttock_dialogue_ghost_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    mood_line: str
    spot: str
    closing_image: str
    ghosts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostKind:
    id: str
    label: str
    phrase: str
    voice_line: str
    item_label: str
    item_phrase: str
    item_material: str
    need_tag: str
    search_line: str
    thanks_line: str
    fade_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    label: str
    sense: int
    solves: set[str] = field(default_factory=set)
    lead_in: str = ""
    success_line: str = ""
    fail_line: str = ""
    qa_text: str = ""
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


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    room = world.get("room")
    if ghost.meters["manifest"] >= THRESHOLD:
        sig = ("haunt", "room")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["eerie"] += 1
            for eid in ("child", "helper"):
                if eid in world.entities:
                    world.get(eid).memes["fear"] += 1
            out.append("__eerie__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    item = world.get("item")
    if item.meters["found"] >= THRESHOLD and ghost.meters["helped"] >= THRESHOLD:
        sig = ("settle", "ghost")
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["settled"] += 1
            world.get("room").meters["eerie"] = 0.0
            for eid in ("child", "helper"):
                if eid in world.entities:
                    actor = world.get(eid)
                    actor.memes["fear"] = 0.0
                    actor.memes["relief"] += 1
            out.append("__settled__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="haunt", tag="emotion", apply=_r_haunt),
    Rule(name="settle", tag="emotion", apply=_r_settle),
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


PLACES = {
    "nursery": Place(
        id="nursery",
        label="nursery",
        phrase="the old nursery at the end of the hall",
        mood_line="Moonlight lay in pale bars across the little bed and the rocking horse.",
        spot="under the crooked toy chest",
        closing_image="The rocking horse stood still, and the moon made the room look gentle instead of spooky.",
        ghosts={"child"},
        tags={"nursery", "moonlight"},
    ),
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the narrow attic under the sloping roof",
        mood_line="Dust floated like tiny silver fish around the trunks and hanging coats.",
        spot="inside a cedar sewing basket",
        closing_image="The rafters stopped creaking, and the attic felt as calm as a folded blanket.",
        ghosts={"seamstress"},
        tags={"attic", "dust"},
    ),
    "lighthouse": Place(
        id="lighthouse",
        label="lighthouse room",
        phrase="the lamp room at the top of the old lighthouse",
        mood_line="The round windows showed black sea on every side, and the glass made the wind sound lonely.",
        spot="behind the brass oil can",
        closing_image="Far below, the sea kept rolling, but the lamp room no longer sounded lonely at all.",
        ghosts={"sailor"},
        tags={"sea", "lighthouse"},
    ),
}

GHOSTS = {
    "child": GhostKind(
        id="child",
        label="child ghost",
        phrase="a small ghost in a nightgown",
        voice_line='"Please do not run," whispered the ghost. "My doll is lost, and I cannot sleep without it."',
        item_label="doll",
        item_phrase="a rag doll with one blue button eye",
        item_material="cloth",
        need_tag="lullaby",
        search_line="The tiny ghost pointed with a trembling hand toward the toy chest.",
        thanks_line='"You remembered my bedtime song," the ghost said, and the room sounded softer at once.',
        fade_line="The small ghost hugged the doll, yawned a cloudy yawn, and melted into the moonlight.",
        tags={"ghost", "doll", "lullaby"},
    ),
    "seamstress": GhostKind(
        id="seamstress",
        label="seamstress ghost",
        phrase="a pale ghost with a tape measure around her neck",
        voice_line='"My silver button is missing," sighed the ghost. "My coat can never be finished until it is back."',
        item_label="button",
        item_phrase="a round silver button as bright as a raindrop",
        item_material="silver",
        need_tag="mend",
        search_line="The ghost lifted one misty finger toward a sewing basket that smelled faintly of cedar.",
        thanks_line='"Now the coat can rest too," said the ghost, smoothing the air where cloth should have been.',
        fade_line="She pressed the button to her faded coat, and her outline stitched itself into the dark and was gone.",
        tags={"ghost", "button", "sewing"},
    ),
    "sailor": GhostKind(
        id="sailor",
        label="sailor ghost",
        phrase="a tall ghost with wet cuffs and kind eyes",
        voice_line='"The lantern went dark on my watch," murmured the ghost. "Its little key is gone, and the light has never forgiven me."',
        item_label="lantern key",
        item_phrase="a brass lantern key no bigger than a thumb",
        item_material="brass",
        need_tag="light",
        search_line="The ghost turned his face toward the lamp table and the clutter around the oil can.",
        thanks_line='"There now," the ghost said. "A light should never be left lonely."',
        fade_line="When the lantern shone again, the sailor ghost tipped his cap and thinned into the warm gold glow.",
        tags={"ghost", "lantern", "sea"},
    ),
}

ACTIONS = {
    "sing_lullaby": Action(
        id="sing_lullaby",
        label="sing a lullaby",
        sense=3,
        solves={"lullaby"},
        lead_in='Grandma squeezed the child\'s hand. "Let us be kind first," she whispered.',
        success_line='Together they sang a soft bedtime song while the child laid the lost item in the ghost\'s hands.',
        fail_line='They sang softly, but this was not the promise the ghost needed kept, so the room stayed uneasy.',
        qa_text="sang a soft lullaby and returned the lost item",
        tags={"song", "kindness"},
    ),
    "sew_button": Action(
        id="sew_button",
        label="sew the button back",
        sense=3,
        solves={"mend"},
        lead_in='"A thing that was meant to be mended should be mended," the helper said.',
        success_line='The helper threaded a needle, and the child held the button very still while they fixed what had been left unfinished.',
        fail_line='They tried to mend the feeling with busy hands, but this ghost needed a different comfort, so the chill did not lift.',
        qa_text="sewed the missing button back where it belonged",
        tags={"mend", "needle"},
    ),
    "polish_lantern": Action(
        id="polish_lantern",
        label="polish and light the lantern",
        sense=3,
        solves={"light"},
        lead_in='"If the light was the promise, then the light is what we must set right," the helper said.',
        success_line='They fitted the little key, polished the cloudy glass, and lit the lantern until a warm ring of gold filled the room.',
        fail_line='They worked carefully, but this ghost was waiting for another kind of comfort, so the shadows kept listening.',
        qa_text="fitted the key and lit the lantern again",
        tags={"light", "lantern"},
    ),
    "slam_door": Action(
        id="slam_door",
        label="slam the door and shout",
        sense=1,
        solves=set(),
        lead_in='"Go away!" the child blurted, but the sound only bounced around the room.',
        success_line="",
        fail_line='The bang made the walls jump, but it did not help a lonely ghost at all.',
        qa_text="slammed the door and shouted",
        tags={"fear"},
    ),
}

CHILD_NAMES = ["Nora", "Eli", "Mina", "Theo", "Luca", "Ivy", "June", "Ben"]
HELPER_NAMES = {
    "grandmother": ["Grandma May", "Grandma Rose", "Grandma June"],
    "grandfather": ["Grandpa Joe", "Grandpa Finn", "Grandpa Abe"],
    "aunt": ["Aunt Clara", "Aunt Wren", "Aunt Lucy"],
    "uncle": ["Uncle Sam", "Uncle Ned", "Uncle Max"],
}
TRAITS = ["curious", "careful", "soft-spoken", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    ghost: str
    action: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    child_trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="nursery",
        ghost="child",
        action="sing_lullaby",
        child_name="Nora",
        child_gender="girl",
        helper_name="Grandma Rose",
        helper_type="grandmother",
        child_trait="curious",
        delay=0,
    ),
    StoryParams(
        place="attic",
        ghost="seamstress",
        action="sew_button",
        child_name="Eli",
        child_gender="boy",
        helper_name="Aunt Clara",
        helper_type="aunt",
        child_trait="careful",
        delay=0,
    ),
    StoryParams(
        place="lighthouse",
        ghost="sailor",
        action="polish_lantern",
        child_name="Mina",
        child_gender="girl",
        helper_name="Grandpa Finn",
        helper_type="grandfather",
        child_trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        place="nursery",
        ghost="child",
        action="sew_button",
        child_name="Theo",
        child_gender="boy",
        helper_name="Uncle Max",
        helper_type="uncle",
        child_trait="brave",
        delay=1,
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for ghost_id in GHOSTS:
            if ghost_id in place.ghosts:
                combos.append((place_id, ghost_id))
    return combos


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    ghost = GHOSTS[params.ghost]
    action = ACTIONS[params.action]
    if ghost.id not in place.ghosts:
        raise StoryError(explain_place_ghost(place, ghost))
    if action.sense < SENSE_MIN:
        raise StoryError(explain_action(action.id))
    if params.delay > 1:
        return "lingering"
    return "peaceful" if ghost.need_tag in action.solves else "lingering"


def explain_place_ghost(place: Place, ghost: GhostKind) -> str:
    allowed = ", ".join(sorted(place.ghosts))
    return (
        f"(No story: {ghost.label} does not belong in {place.phrase}. "
        f"That place only fits ghosts like: {allowed}.)"
    )


def explain_action(action_id: str) -> str:
    action = ACTIONS[action_id]
    better = ", ".join(sorted(a.id for a in sensible_actions()))
    return (
        f"(Refusing action '{action.id}': it scores too low on common sense "
        f"(sense={action.sense} < {SENSE_MIN}). Try a kinder action: {better}.)"
    )


def omen_line(place: Place, ghost: GhostKind) -> str:
    if ghost.id == "child":
        return "From the dark came a tiny rocking creak and a whisper like paper slipping over paper."
    if ghost.id == "seamstress":
        return "Somewhere in the dark came the click-click of unseen needles and one long sigh."
    return "Wind worried the glass, and under it came a faint tap-tap, as if a patient finger knocked from nowhere."


def bump_line(child: Entity, place: Place) -> str:
    if place.id == "lighthouse":
        return (
            f"{child.id} gave such a start that {child.pronoun()} slipped from the stool "
            f"and bumped one buttock on the cold floorboards."
        )
    return (
        f"{child.id} jumped so fast that {child.pronoun()} sat down hard and bumped "
        f"one buttock on the rug."
    )


def search_item(world: World, place: Place, ghost: GhostKind) -> None:
    item = world.get("item")
    item.meters["found"] += 1
    world.facts["found_spot"] = place.spot
    world.say(ghost.search_line)
    world.say(
        f'The helper lifted the edge of things near {place.spot}, and there it was: '
        f"{ghost.item_phrase}."
    )


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"One windy night, {child.id} stayed awake with {helper.id} in {place.phrase}."
    )
    world.say(place.mood_line)
    world.say(
        f"{child.id} was a {child.attrs.get('trait', 'curious')} little {child.type} "
        f"who wanted to be brave, even when the dark had corners in it."
    )


def omen(world: World, child: Entity, place: Place, ghost: GhostKind) -> None:
    world.get("ghost").meters["manifest"] += 1
    propagate(world, narrate=False)
    world.say(omen_line(place, ghost))
    world.say(bump_line(child, place))
    world.say(f'"Did you hear that?" {child.id} whispered.')


def helper_arrives(world: World, helper: Entity) -> None:
    world.say(
        f'"I heard it," {helper.id} said. "{helper.pronoun("subject").capitalize()} will not laugh. '
        f'Let us listen before we frighten ourselves more."'
    )


def ghost_speaks(world: World, ghost_cfg: GhostKind) -> None:
    ghost = world.get("ghost")
    ghost.memes["lonely"] += 1
    world.say(
        f"Out of the shadow drifted {ghost_cfg.phrase}, thin as window mist."
    )
    world.say(ghost_cfg.voice_line)


def investigation(world: World, child: Entity, helper: Entity, place: Place, ghost_cfg: GhostKind) -> None:
    child.memes["courage"] += 1
    helper.memes["courage"] += 1
    world.say(
        f'"Then we will help," {helper.id} said. "{child.id}, stay close to me."'
    )
    world.say(
        f"{child.id} swallowed, nodded, and took one small step after another through {place.phrase}."
    )
    search_item(world, place, ghost_cfg)


def resolve_peacefully(world: World, child: Entity, helper: Entity, ghost_cfg: GhostKind, action: Action) -> None:
    ghost = world.get("ghost")
    ghost.meters["helped"] += 1
    propagate(world, narrate=False)
    world.say(action.lead_in)
    world.say(action.success_line)
    world.say(ghost_cfg.thanks_line)
    world.say(ghost_cfg.fade_line)
    world.say(
        f'{child.id} let out the breath {child.pronoun()} had been holding. '
        f'"It was never trying to scare us," {child.pronoun()} said.'
    )
    world.say(
        f'"No," {helper.id} answered. "It only needed kindness and a listening ear."'
    )


def linger(world: World, child: Entity, helper: Entity, place: Place, ghost_cfg: GhostKind, action: Action, delay: int) -> None:
    world.get("ghost").memees = getattr(world.get("ghost"), "memees", None)
    if delay > 1:
        world.say(
            f"They waited too long, and the room seemed to grow older and sadder with every slow minute."
        )
    world.say(action.lead_in)
    world.say(action.fail_line)
    world.say(
        f'The ghost drew back and whispered, "That is not what I came for."'
    )
    world.say(
        f"The strange chill stayed in {place.phrase}, and even {helper.id} spoke more softly after that."
    )
    world.say(
        f'{child.id} pressed close to {helper.id}. "We should come back when we know how to help for real," '
        f'{child.pronoun()} said.'
    )


def closing(world: World, place: Place, outcome: str) -> None:
    if outcome == "peaceful":
        world.say(place.closing_image)
    else:
        world.say(
            f"The place was quieter than before, but not peaceful yet; the mystery still waited in the dark."
        )


def tell(
    place: Place,
    ghost_cfg: GhostKind,
    action: Action,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_type: str,
    child_trait: str,
    delay: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"trait": child_trait},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label=place.label,
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            label=ghost_cfg.label,
            phrase=ghost_cfg.phrase,
            tags=set(ghost_cfg.tags),
        )
    )
    item = world.add(
        Entity(
            id="item",
            type="keepsake",
            label=ghost_cfg.item_label,
            phrase=ghost_cfg.item_phrase,
            tags={ghost_cfg.item_label, ghost_cfg.item_material},
        )
    )

    introduce(world, child, helper, place)
    world.para()
    omen(world, child, place, ghost_cfg)
    helper_arrives(world, helper)
    ghost_speaks(world, ghost_cfg)
    world.para()
    investigation(world, child, helper, place, ghost_cfg)

    outcome = "peaceful" if delay <= 1 and ghost_cfg.need_tag in action.solves else "lingering"

    world.para()
    if outcome == "peaceful":
        resolve_peacefully(world, child, helper, ghost_cfg, action)
    else:
        linger(world, child, helper, place, ghost_cfg, action, delay)

    world.para()
    closing(world, place, outcome)

    world.facts.update(
        place=place,
        ghost_cfg=ghost_cfg,
        action=action,
        child=child,
        helper=helper,
        room=room,
        ghost=ghost,
        item=item,
        delay=delay,
        outcome=outcome,
        found=item.meters["found"] >= THRESHOLD,
        settled=ghost.meters["settled"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a tale about something strange and spooky, often with whispers, shadows, or spirits. In gentle ghost stories, the mystery feels eerie but does not end in cruelty.",
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft song sung to help someone feel calm and sleepy. Quiet music can make a room feel safer and gentler.",
        )
    ],
    "button": [
        (
            "What does a button do?",
            "A button helps keep a piece of clothing closed or neat. If a button falls off, the clothing can look unfinished until someone sews it back.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp with a cover around the light. People use lanterns to carry light safely into dark places.",
        )
    ],
    "moonlight": [
        (
            "What is moonlight?",
            "Moonlight is the light that comes from the moon shining at night. It can make ordinary rooms look strange and silver.",
        )
    ],
    "sea": [
        (
            "Why can the sea sound spooky at night?",
            "At night, waves and wind can echo and boom in dark places. Those sounds can make a place feel lonely or mysterious.",
        )
    ],
    "sewing": [
        (
            "What does sewing mean?",
            "Sewing means joining cloth with thread, often using a needle. People sew to mend tears or attach buttons.",
        )
    ],
    "kindness": [
        (
            "Why can kindness help when someone is frightened?",
            "Kindness can slow a scared heart and make a person feel less alone. Listening and speaking gently often help more than shouting.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "moonlight", "lullaby", "button", "sewing", "lantern", "sea", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "buttock" and uses dialogue.',
        f"Tell a spooky-but-safe story where {child.id} and {helper.id} hear a voice in {place.phrase}, meet {ghost_cfg.phrase}, and learn the ghost needs help rather than fear.",
        f'Write a story in a ghost-story style with whispered dialogue, a child who gets startled and bumps a buttock, and an ending that turns a haunted room peaceful.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    action = f["action"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {helper.id}, who stayed together in {place.phrase}. It is also about a lonely ghost that wanted one small thing put right.",
        ),
        (
            f"Why did {child.id} get frightened at first?",
            f"{child.id} heard a strange sound in the dark and saw a ghost drift out of the shadows. The room felt eerie before anyone understood what the ghost really wanted.",
        ),
        (
            f"What happened to {child.id}'s body when the ghostly sound came?",
            f"{child.id} jumped in surprise and bumped one buttock on the rug or floor. That little thump shows how suddenly the fear hit.",
        ),
        (
            "What did the ghost want?",
            f"The ghost wanted its lost {ghost_cfg.item_label} and the right kind of help for it. The ghost spoke in dialogue and explained the problem instead of attacking anyone.",
        ),
    ]
    if f["outcome"] == "peaceful":
        qa.append(
            (
                f"How did {child.id} and {helper.id} help the ghost?",
                f"They found the lost {ghost_cfg.item_label} at {f.get('found_spot', 'the hidden spot')} and then {action.qa_text}. That matched what the ghost needed, so the room stopped feeling haunted.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully. The ghost thanked them, faded away, and {place.closing_image[0].lower() + place.closing_image[1:]}",
            )
        )
    else:
        qa.append(
            (
                f"Why did the ghost stay unsettled?",
                f"{child.id} and {helper.id} found the lost {ghost_cfg.item_label}, but they did not use the kind of help this ghost needed, or they waited too long. Because of that, the chill in the room never fully lifted.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a mystery still hanging in the air. The place grew quieter, but it was not peaceful yet, which shows the ghost's problem was not truly solved.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost", "kindness"} | set(world.facts["place"].tags) | set(world.facts["ghost_cfg"].tags) | set(world.facts["action"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G) :- place(P), ghost(G), haunts(P, G).
sensible(A) :- action(A), sense(A, S), sense_min(M), S >= M.

need_match(G, A) :- chosen_ghost(G), chosen_action(A), needs(G, N), solves(A, N).
delayed_too_long :- delay(D), D > 1.

outcome(peaceful) :- chosen_place(P), chosen_ghost(G), haunts(P, G), sensible(A),
                     chosen_action(A), need_match(G, A), not delayed_too_long.
outcome(lingering) :- chosen_place(P), chosen_ghost(G), haunts(P, G), sensible(A),
                      chosen_action(A), not need_match(G, A).
outcome(lingering) :- chosen_place(P), chosen_ghost(G), haunts(P, G), sensible(A),
                      chosen_action(A), delayed_too_long.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for ghost_id in sorted(place.ghosts):
            lines.append(asp.fact("haunts", place_id, ghost_id))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("needs", ghost_id, ghost.need_tag))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("sense", action_id, action.sense))
        for tag in sorted(action.solves):
            lines.append(asp.fact("solves", action_id, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_actions() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_ghost", params.ghost),
            asp.fact("chosen_action", params.action),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sensible = set(asp_sensible_actions())
    p_sensible = {a.id for a in sensible_actions()}
    if c_sensible == p_sensible:
        print(f"OK: sensible actions match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible actions: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world with dialogue. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--helper", choices=sorted(HELPER_NAMES))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long they hesitate before helping")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible place/ghost pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    return rng.choice(CHILD_NAMES), gender


def _pick_helper(rng: random.Random, helper_type: Optional[str] = None) -> tuple[str, str]:
    helper_type = helper_type or rng.choice(sorted(HELPER_NAMES))
    return rng.choice(HELPER_NAMES[helper_type]), helper_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.ghost:
        place = PLACES[args.place]
        ghost = GHOSTS[args.ghost]
        if ghost.id not in place.ghosts:
            raise StoryError(explain_place_ghost(place, ghost))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_action(args.action))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ghost_id = rng.choice(sorted(combos))
    action_id = args.action or rng.choice(sorted(a.id for a in sensible_actions()))
    child_name, child_gender = _pick_child(rng)
    helper_name, helper_type = _pick_helper(rng, args.helper)
    child_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 1, 2])
    return StoryParams(
        place=place_id,
        ghost=ghost_id,
        action=action_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        child_trait=child_trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")

    place = PLACES[params.place]
    ghost_cfg = GHOSTS[params.ghost]
    action = ACTIONS[params.action]

    if ghost_cfg.id not in place.ghosts:
        raise StoryError(explain_place_ghost(place, ghost_cfg))
    if action.sense < SENSE_MIN:
        raise StoryError(explain_action(action.id))

    world = tell(
        place=place,
        ghost_cfg=ghost_cfg,
        action=action,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
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
        print(f"sensible actions: {', '.join(asp_sensible_actions())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ghost) combos:\n")
        for place, ghost in combos:
            print(f"  {place:10} {ghost}")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name}: {p.ghost} in {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
