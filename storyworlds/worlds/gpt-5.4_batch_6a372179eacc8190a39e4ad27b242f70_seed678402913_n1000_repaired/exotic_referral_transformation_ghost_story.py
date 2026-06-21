#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py
=========================================================================

A standalone story world for a child-friendly ghost story with a clear
transformation turn.

Premise
-------
A child visits an old place at dusk, hears a small ghost, and learns that the
ghost cannot reach the room holding its keepsake without the right referral.
With help from a kindly caretaker and a soft light, the child carries the
matching keepsake into the room. When the ghost touches what it has been
missing, it transforms out of its gray, shivery shape into its true self and
leaves the place peaceful.

Coverage rule
-------------
Not every ghost/keepsake/referral combination makes sense. Each ghost has one
matching keepsake; each keepsake belongs in one special room; each venue only
has certain rooms; and each referral only opens one room. The world refuses
combinations that do not line up.

Run it
------
    python storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py
    python storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py --venue greenhouse --ghost cat --keepsake collar --referral gardener_pass
    python storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py --ghost child --keepsake collar
    python storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/exotic_referral_transformation_ghost_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    label: str
    entry: str
    hush: str
    special_room: str
    room_label: str
    exotic_detail: str
    eerie: int
    available_rooms: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostConfig:
    id: str
    label: str
    opening: str
    whisper: str
    true_form: str
    transform_line: str
    needs_keepsake: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    room: str
    match_ghost: str
    memory: str
    transformed_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Referral:
    id: str
    label: str
    phrase: str
    opens_room: str
    giver: str
    comfort: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    brave_bonus: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.meters["manifest"] < THRESHOLD:
        return out
    sig = ("spook", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += float(world.venue.eerie)
    out.append("__spook__")
    return out


def _r_referral(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").meters["has_referral"] < THRESHOLD:
        return out
    sig = ("referral", "door")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("door").meters["open"] += 1
    out.append("__door__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    keepsake = world.get("keepsake")
    door = world.get("door")
    if ghost.meters["near_keepsake"] < THRESHOLD:
        return out
    if keepsake.meters["returned"] < THRESHOLD:
        return out
    if door.meters["open"] < THRESHOLD:
        return out
    sig = ("transform", ghost.id, keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["transformed"] += 1
    ghost.meters["manifest"] = 0.0
    ghost.memes["peace"] += 1
    world.get("child").memes["wonder"] += 1
    world.get("caretaker").memes["relief"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="referral", tag="social", apply=_r_referral),
    Rule(name="transform", tag="magical", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(result)
    if narrate:
        for text in produced:
            if not text.startswith("__"):
                world.say(text)
    return produced


VENUES = {
    "greenhouse": Venue(
        id="greenhouse",
        label="the old greenhouse",
        entry="At the edge of town stood the old greenhouse, all silver glass and long shadows.",
        hush="Rain tapped softly on the panes, and every leaf seemed to be listening.",
        special_room="orchid_house",
        room_label="the orchid house",
        exotic_detail="Behind one locked door waited a warm room full of exotic orchids that opened only at night.",
        eerie=2,
        available_rooms={"orchid_house"},
        tags={"greenhouse", "orchid", "exotic"},
    ),
    "museum": Venue(
        id="museum",
        label="the little museum",
        entry="On a windy evening, the little museum looked as if it were holding its breath.",
        hush="The hall lamps glowed low, and the glass cases gave back pale, wobbly reflections.",
        special_room="shell_gallery",
        room_label="the shell gallery",
        exotic_detail="Past the front hall was a locked gallery lined with exotic shells from faraway shores.",
        eerie=3,
        available_rooms={"shell_gallery"},
        tags={"museum", "shell", "exotic"},
    ),
    "library": Venue(
        id="library",
        label="the old library",
        entry="At dusk, the old library made every footstep sound important.",
        hush="Dusty lamps shone like tiny moons between the shelves.",
        special_room="map_room",
        room_label="the map room",
        exotic_detail="Upstairs was a locked room where an exotic atlas rested under blue velvet.",
        eerie=2,
        available_rooms={"map_room"},
        tags={"library", "map", "exotic"},
    ),
}

GHOSTS = {
    "cat": GhostConfig(
        id="cat",
        label="a thin gray cat-ghost",
        opening="Under a fern bench sat a thin gray cat-ghost with moon-bright whiskers.",
        whisper='"I keep padding to the wrong door," it whispered. "My bell is waiting where I cannot go."',
        true_form="a soft white cat",
        transform_line="Its smoky fur folded inward like mist, and in its place stood a soft white cat with a bright little bell.",
        needs_keepsake="collar",
        tags={"cat", "ghost"},
    ),
    "child": GhostConfig(
        id="child",
        label="a small child-ghost",
        opening="Near the stair rail hovered a small child-ghost, no taller than the lowest shelf.",
        whisper='"I remember a song and a ribbon, but not my own face," the ghost murmured.',
        true_form="a smiling child made of warm light",
        transform_line="The ragged gray shape smoothed into a smiling child made of warm light, clear at last from hair ribbon to shining shoes.",
        needs_keepsake="ribbon",
        tags={"child", "ghost"},
    ),
    "bird": GhostConfig(
        id="bird",
        label="a trembling bird-ghost",
        opening="On a cracked statue perched a trembling bird-ghost, all feathers of mist.",
        whisper='"My sky was small and my feather pin was lost," it peeped. "I have fluttered here ever since."',
        true_form="a bright green bird",
        transform_line="The blur of wings tightened, brightened, and became a bright green bird with steady eyes and living feathers.",
        needs_keepsake="feather_pin",
        tags={"bird", "ghost"},
    ),
}

KEEPSAKES = {
    "collar": Keepsake(
        id="collar",
        label="bell collar",
        phrase="a tiny bell collar",
        room="orchid_house",
        match_ghost="cat",
        memory="The little bell had once chimed whenever paws hurried through the wet paths.",
        transformed_image="It rubbed against the child's ankle before trotting toward the moonlit leaves.",
        tags={"collar", "bell"},
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon in a glass tray",
        room="map_room",
        match_ghost="child",
        memory="The ribbon still held the careful bow of someone who liked things neat and brave.",
        transformed_image="It smiled, waved once, and grew lighter and lighter until the room itself seemed to remember the song.",
        tags={"ribbon", "memory"},
    ),
    "feather_pin": Keepsake(
        id="feather_pin",
        label="feather pin",
        phrase="a little feather pin on black velvet",
        room="shell_gallery",
        match_ghost="bird",
        memory="The pin caught the dim light and flashed like a tiny green wing.",
        transformed_image="It beat its wings once, circled the ceiling, and left behind one bright note of birdsong.",
        tags={"pin", "feather"},
    ),
}

REFERRALS = {
    "gardener_pass": Referral(
        id="gardener_pass",
        label="garden referral",
        phrase="a neat green referral card from the night gardener",
        opens_room="orchid_house",
        giver="night gardener",
        comfort=2,
        tags={"referral", "garden"},
    ),
    "curator_note": Referral(
        id="curator_note",
        label="curator referral",
        phrase="a cream referral note from the museum curator",
        opens_room="shell_gallery",
        giver="museum curator",
        comfort=1,
        tags={"referral", "museum"},
    ),
    "librarian_slip": Referral(
        id="librarian_slip",
        label="librarian referral",
        phrase="a quiet referral slip from the librarian",
        opens_room="map_room",
        giver="librarian",
        comfort=2,
        tags={"referral", "library"},
    ),
}

LIGHTS = {
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a round brass lantern",
        glow="glowed honey-yellow and steady",
        brave_bonus=2,
        tags={"lantern", "light"},
    ),
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        glow="cut a clean white path through the dimness",
        brave_bonus=1,
        tags={"flashlight", "light"},
    ),
    "moon_jar": Light(
        id="moon_jar",
        label="moon jar",
        phrase="a glass moon jar full of soft silver light",
        glow="shone as if a bit of bedtime moon had been tucked inside",
        brave_bonus=2,
        tags={"moonlight", "light"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Elsie", "June", "Wren", "Clara", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Jasper", "Evan", "Hugo", "Rowan", "Finn"]
TRAITS = {
    "steady": 3,
    "curious": 2,
    "timid": 1,
    "kind": 2,
    "careful": 2,
}
COMPANIONS = ["mother", "father"]


def ghost_matches(ghost_id: str, keepsake_id: str) -> bool:
    ghost = GHOSTS[ghost_id]
    keepsake = KEEPSAKES[keepsake_id]
    return ghost.needs_keepsake == keepsake.id and keepsake.match_ghost == ghost.id


def venue_allows(venue_id: str, keepsake_id: str, referral_id: str) -> bool:
    venue = VENUES[venue_id]
    keepsake = KEEPSAKES[keepsake_id]
    referral = REFERRALS[referral_id]
    return keepsake.room in venue.available_rooms and referral.opens_room == keepsake.room


def valid_combo(venue_id: str, ghost_id: str, keepsake_id: str, referral_id: str) -> bool:
    return ghost_matches(ghost_id, keepsake_id) and venue_allows(venue_id, keepsake_id, referral_id)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for venue_id in VENUES:
        for ghost_id in GHOSTS:
            for keepsake_id in KEEPSAKES:
                for referral_id in REFERRALS:
                    if valid_combo(venue_id, ghost_id, keepsake_id, referral_id):
                        out.append((venue_id, ghost_id, keepsake_id, referral_id))
    return out


def courage_score(trait: str, light_id: str, referral_id: str) -> int:
    return TRAITS[trait] + LIGHTS[light_id].brave_bonus + REFERRALS[referral_id].comfort


def outcome_of(venue_id: str, trait: str, light_id: str, referral_id: str) -> str:
    return "witnessed" if courage_score(trait, light_id, referral_id) >= VENUES[venue_id].eerie + 3 else "blinked"


def explain_invalid(venue_id: str, ghost_id: str, keepsake_id: str, referral_id: str) -> str:
    ghost = GHOSTS[ghost_id]
    keepsake = KEEPSAKES[keepsake_id]
    referral = REFERRALS[referral_id]
    venue = VENUES[venue_id]
    if not ghost_matches(ghost_id, keepsake_id):
        return (
            f"(No story: {ghost.label} is not tied to the {keepsake.label}. "
            f"This ghost needs {ghost.needs_keepsake.replace('_', ' ')} to remember itself.)"
        )
    if keepsake.room not in venue.available_rooms:
        return (
            f"(No story: {venue.label} does not contain {venue.room_label if venue.available_rooms else 'that special room'}, "
            f"so the {keepsake.label} would not reasonably be there.)"
        )
    if referral.opens_room != keepsake.room:
        return (
            f"(No story: the {referral.label} opens {referral.opens_room.replace('_', ' ')}, "
            f"but the {keepsake.label} belongs in {keepsake.room.replace('_', ' ')}.)"
        )
    return "(No story: these choices do not form a sensible haunting.)"


def predicted_calm(world: World, trait: str, light: Light, referral: Referral) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["has_referral"] += 1
    propagate(sim, narrate=False)
    score = courage_score(trait, light.id, referral.id)
    return {
        "courage": score,
        "eerie": sim.venue.eerie,
        "outcome": "witnessed" if score >= sim.venue.eerie + 3 else "blinked",
    }


def arrive(world: World, child: Entity, caretaker: Entity, venue: Venue) -> None:
    world.say(venue.entry)
    world.say(
        f"{child.id} came with {child.pronoun('possessive')} {caretaker.label_word} to return a library book and peek around before going home."
    )
    world.say(venue.hush)
    world.say(venue.exotic_detail)


def first_manifest(world: World, ghost_cfg: GhostConfig) -> None:
    ghost = world.get("ghost")
    ghost.meters["manifest"] += 1
    propagate(world, narrate=False)
    world.say(ghost_cfg.opening)
    world.say(ghost_cfg.whisper)


def child_listens(world: World, child: Entity, trait: str, venue: Venue) -> None:
    child.memes["kindness"] += 1
    if trait == "timid":
        world.say(
            f"{child.id}'s fingers went cold, but {child.pronoun()} did not run. {child.pronoun().capitalize()} listened anyway, even while the shadows of {venue.label} seemed to lean closer."
        )
    elif trait == "steady":
        world.say(
            f"{child.id} swallowed once and stood very still, the way a steady child does when something strange needs hearing."
        )
    else:
        world.say(
            f"{child.id}'s fear and curiosity bumped together inside {child.pronoun('object')}, and curiosity won."
        )


def ask_for_help(world: World, child: Entity, caretaker: Entity, referral: Referral) -> None:
    caretaker.memes["care"] += 1
    world.say(
        f'"{caretaker.label_word.capitalize()}," {child.id} whispered, "the ghost says it needs a referral."'
    )
    world.say(
        f"{caretaker.label_word.capitalize()} did not laugh. {caretaker.pronoun().capitalize()} knelt, listened to the thin little story, and took out {referral.phrase}."
    )


def take_referral(world: World, child: Entity, referral: Referral, venue: Venue) -> None:
    child.meters["has_referral"] += 1
    child.attrs["referral"] = referral.id
    propagate(world, narrate=False)
    world.say(
        f'The paper felt important in {child.id}\'s hand. It was a real referral, written for {venue.room_label}, and the locked latch clicked as soon as the card touched it.'
    )


def enter_room(world: World, child: Entity, caretaker: Entity, venue: Venue, light: Light, keepsake: Keepsake) -> None:
    world.say(
        f"Inside {venue.room_label}, {light.phrase} {light.glow}. On a small stand rested {keepsake.phrase}."
    )
    world.say(keepsake.memory)
    child.memes["resolve"] += 1
    caretaker.memes["trust"] += 1


def return_keepsake(world: World, child: Entity, ghost_cfg: GhostConfig, keepsake: Keepsake) -> None:
    world.get("ghost").meters["near_keepsake"] += 1
    world.get("keepsake").meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} lifted the {keepsake.label} with both hands and held it out to {ghost_cfg.label}."
    )


def transform_witnessed(world: World, child: Entity, ghost_cfg: GhostConfig, keepsake: Keepsake, venue: Venue) -> None:
    child.memes["fear"] = 0.0
    child.memes["bravery"] += 1
    world.say(ghost_cfg.transform_line)
    world.say(keepsake.transformed_image)
    world.say(
        f'Then a soft voice said, "Thank you for helping me find my right shape." After that, {venue.label} no longer felt cold at all.'
    )


def transform_blinked(world: World, child: Entity, caretaker: Entity, ghost_cfg: GhostConfig, keepsake: Keepsake, venue: Venue) -> None:
    child.memes["fear"] += 1
    world.say(
        f"The room gave one sudden shiver of light. {child.id} hid against {child.pronoun('possessive')} {caretaker.label_word}'s coat for a moment and almost missed the change."
    )
    world.say(ghost_cfg.transform_line)
    world.say(keepsake.transformed_image)
    world.say(
        f"When {child.id} peeked again, the frightened feeling had gone out of {venue.label}, as if someone had opened a window and let the old sadness drift away."
    )


def ending(world: World, child: Entity, caretaker: Entity, light: Light, outcome: str) -> None:
    if outcome == "witnessed":
        world.say(
            f"On the way home, {child.id} carried the {light.label} a little higher. The dark still looked dark, but it no longer looked lonely."
        )
    else:
        world.say(
            f"On the way home, {caretaker.label_word} kept one warm hand on {child.id}'s shoulder while the {light.label} bobbed beside them. The dark still held secrets, but now it felt gentle."
        )


def tell(
    venue: Venue,
    ghost_cfg: GhostConfig,
    keepsake_cfg: Keepsake,
    referral_cfg: Referral,
    light_cfg: Light,
    child_name: str,
    child_gender: str,
    caretaker_type: str,
    trait: str,
) -> World:
    world = World(venue=venue)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            label=child_name,
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=caretaker_type,
            role="caretaker",
            label="the caretaker",
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            type="ghost",
            role="ghost",
            label=ghost_cfg.label,
            attrs={"true_form": ghost_cfg.true_form},
            tags=set(ghost_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake_cfg.label,
            phrase=keepsake_cfg.phrase,
            tags=set(keepsake_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="door",
            type="door",
            label=venue.room_label,
            attrs={"room": venue.special_room},
        )
    )

    arrive(world, child, caretaker, venue)
    world.para()
    first_manifest(world, ghost_cfg)
    child_listens(world, child, trait, venue)
    ask_for_help(world, child, caretaker, referral_cfg)

    world.para()
    prediction = predicted_calm(world, trait, light_cfg, referral_cfg)
    world.facts["predicted_courage"] = prediction["courage"]
    world.facts["predicted_eerie"] = prediction["eerie"]
    take_referral(world, child, referral_cfg, venue)
    enter_room(world, child, caretaker, venue, light_cfg, keepsake_cfg)
    return_keepsake(world, child, ghost_cfg, keepsake_cfg)

    outcome = prediction["outcome"]
    world.para()
    if outcome == "witnessed":
        transform_witnessed(world, child, ghost_cfg, keepsake_cfg, venue)
    else:
        transform_blinked(world, child, caretaker, ghost_cfg, keepsake_cfg, venue)
    ending(world, child, caretaker, light_cfg, outcome)

    world.facts.update(
        venue=venue,
        ghost_cfg=ghost_cfg,
        keepsake_cfg=keepsake_cfg,
        referral_cfg=referral_cfg,
        light_cfg=light_cfg,
        child=child,
        caretaker=caretaker,
        outcome=outcome,
        transformed=world.get("ghost").meters["transformed"] >= THRESHOLD,
        true_form=ghost_cfg.true_form,
    )
    return world


@dataclass
class StoryParams:
    venue: str
    ghost: str
    keepsake: str
    referral: str
    light: str
    child_name: str
    child_gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost in a story?",
            "A ghost in a story is a spirit or shadowy person or animal that lingers after its old life. In gentle stories, ghosts are often sad or lost rather than mean.",
        )
    ],
    "referral": [
        (
            "What is a referral?",
            "A referral is a note or card that says someone is allowed to go somewhere or get help from a certain person. It is like a careful grown-up's permission.",
        )
    ],
    "orchid": [
        (
            "What is an orchid?",
            "An orchid is a kind of flower. Some orchids look very unusual, which is why people may call them exotic flowers.",
        )
    ],
    "shell": [
        (
            "What is a shell gallery?",
            "A shell gallery is a room where shells are displayed so people can look at their shapes and colors. Museums use cases to keep delicate things safe.",
        )
    ],
    "atlas": [
        (
            "What is an atlas?",
            "An atlas is a book of maps. It helps people see places from all around the world.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives steady light so people can see in dark places. A soft light can make a spooky room feel calmer.",
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a small light you can carry in your hand. It helps you see where you are going.",
        )
    ],
    "moonlight": [
        (
            "Why does moonlight look silvery?",
            "Moonlight is sunlight bouncing off the moon. It often looks silvery because it is much dimmer and cooler than daylight.",
        )
    ],
    "memory": [
        (
            "Why can a keepsake matter so much?",
            "A keepsake is a small object that helps someone remember a person, place, or feeling. In stories, finding the right keepsake can help a sad character feel whole again.",
        )
    ],
}

KNOWLEDGE_ORDER = ["ghost", "referral", "orchid", "shell", "atlas", "lantern", "flashlight", "moonlight", "memory"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue = f["venue"]
    ghost_cfg = f["ghost_cfg"]
    keepsake = f["keepsake_cfg"]
    referral = f["referral_cfg"]
    child = f["child"]
    light = f["light_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "exotic" and "referral".',
        f"Tell a story where a {child.type} named {child.id} meets {ghost_cfg.label} in {venue.label}, gets {referral.phrase}, and helps return {keepsake.phrase}.",
        f"Write a transformation ghost story set in {venue.label} where a child carries {light.phrase} into a locked room and a lost spirit changes into its true form.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    venue = f["venue"]
    ghost_cfg = f["ghost_cfg"]
    keepsake = f["keepsake_cfg"]
    referral = f["referral_cfg"]
    light = f["light_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {caretaker.label_word}, and {ghost_cfg.label} in {venue.label}. The child is the one who listens and helps.",
        ),
        (
            f"Why did the ghost need a referral?",
            f"The keepsake that belonged to the ghost was locked in {venue.room_label}, so the child needed {referral.phrase} to open the way. Without that referral, the ghost could not reach the thing that helped it remember its true self.",
        ),
        (
            f"What was waiting in {venue.room_label}?",
            f"{keepsake.phrase.capitalize()} was waiting there. It mattered because it matched the ghost's old life and stirred its memory.",
        ),
        (
            "What caused the transformation?",
            f"The transformation happened when {child.id} carried the {keepsake.label} into the right room and offered it to the ghost. The open door, the correct keepsake, and the ghost being near it all came together at once.",
        ),
    ]
    if outcome == "witnessed":
        qa.append(
            (
                f"How did {child.id} act when the ghost changed?",
                f"{child.id} stayed close enough to see the whole change. The story says {child.pronoun()} was brave enough to keep looking, so the transformation felt wondrous instead of only scary.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} see the whole transformation?",
                f"Not quite. {child.id} hid for a moment against {child.pronoun('possessive')} {caretaker.label_word}, then peeked back just after the change, because the room gave one sudden shiver of light.",
            )
        )
    qa.append(
        (
            "How did the place feel at the end?",
            f"At the end, {venue.label} no longer felt so cold or lonely. The ghost's sadness had lifted, which changed the whole place.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "referral", "memory"}
    venue = f["venue"]
    light = f["light_cfg"]
    if venue.id == "greenhouse":
        tags.add("orchid")
    elif venue.id == "museum":
        tags.add("shell")
    elif venue.id == "library":
        tags.add("atlas")
    if light.id == "lantern":
        tags.add("lantern")
    elif light.id == "flashlight":
        tags.add("flashlight")
    elif light.id == "moon_jar":
        tags.add("moonlight")
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="greenhouse",
        ghost="cat",
        keepsake="collar",
        referral="gardener_pass",
        light="moon_jar",
        child_name="Ivy",
        child_gender="girl",
        caretaker="mother",
        trait="kind",
    ),
    StoryParams(
        venue="library",
        ghost="child",
        keepsake="ribbon",
        referral="librarian_slip",
        light="lantern",
        child_name="Theo",
        child_gender="boy",
        caretaker="father",
        trait="steady",
    ),
    StoryParams(
        venue="museum",
        ghost="bird",
        keepsake="feather_pin",
        referral="curator_note",
        light="flashlight",
        child_name="Mina",
        child_gender="girl",
        caretaker="mother",
        trait="timid",
    ),
]


ASP_RULES = r"""
ghost_matches(G, K) :- ghost_needs(G, K), keepsake_for(K, G).
venue_allows(V, K, R) :- venue_has(V, Room), kept_in(K, Room), opens(R, Room).
valid(V, G, K, R) :- venue(V), ghost(G), keepsake(K), referral(R),
                     ghost_matches(G, K), venue_allows(V, K, R).

witness_score(Total) :- chosen_trait(T), trait_score(T, Ts),
                        chosen_light(L), light_bonus(L, Lb),
                        chosen_referral(R), comfort(R, C),
                        Total = Ts + Lb + C.
witnessed :- chosen_venue(V), eerie(V, E), witness_score(S), S >= E + 3.
outcome(witnessed) :- witnessed.
outcome(blinked) :- not witnessed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        lines.append(asp.fact("eerie", venue_id, venue.eerie))
        for room in sorted(venue.available_rooms):
            lines.append(asp.fact("venue_has", venue_id, room))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("ghost_needs", ghost_id, ghost.needs_keepsake))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("kept_in", keepsake_id, keepsake.room))
        lines.append(asp.fact("keepsake_for", keepsake_id, keepsake.match_ghost))
    for referral_id, referral in REFERRALS.items():
        lines.append(asp.fact("referral", referral_id))
        lines.append(asp.fact("opens", referral_id, referral.opens_room))
        lines.append(asp.fact("comfort", referral_id, referral.comfort))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("light_bonus", light_id, light.brave_bonus))
    for trait, score in TRAITS.items():
        lines.append(asp.fact("trait_score", trait, score))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_venue", params.venue),
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_light", params.light),
            asp.fact("chosen_referral", params.referral),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params.venue, params.trait, params.light, params.referral):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke generation passed.")
    except Exception as err:  # pragma: no cover - defensive verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a ghost, a referral, and a transformation."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--referral", choices=REFERRALS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=COMPANIONS)
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, gender: Optional[str]) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    return rng.choice(pool), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.venue and args.ghost and args.keepsake and args.referral:
        if not valid_combo(args.venue, args.ghost, args.keepsake, args.referral):
            raise StoryError(explain_invalid(args.venue, args.ghost, args.keepsake, args.referral))
    elif args.ghost and args.keepsake:
        ghost = GHOSTS[args.ghost]
        keepsake = KEEPSAKES[args.keepsake]
        if not ghost_matches(args.ghost, args.keepsake):
            raise StoryError(
                f"(No story: {ghost.label} does not belong with the {keepsake.label}. "
                f"That keepsake would not complete this haunting.)"
            )
    elif args.venue and args.keepsake and args.referral:
        if not venue_allows(args.venue, args.keepsake, args.referral):
            venue = VENUES[args.venue]
            keepsake = KEEPSAKES[args.keepsake]
            referral = REFERRALS[args.referral]
            raise StoryError(explain_invalid(venue.id, keepsake.match_ghost, keepsake.id, referral.id))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.referral is None or combo[3] == args.referral)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, ghost_id, keepsake_id, referral_id = rng.choice(sorted(combos))
    light_id = args.light or rng.choice(sorted(LIGHTS))
    child_name, child_gender = _pick_child(rng, args.child_gender)
    if args.child_name:
        child_name = args.child_name
    caretaker = args.caretaker or rng.choice(COMPANIONS)
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        venue=venue_id,
        ghost=ghost_id,
        keepsake=keepsake_id,
        referral=referral_id,
        light=light_id,
        child_name=child_name,
        child_gender=child_gender,
        caretaker=caretaker,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        ghost_cfg = GHOSTS[params.ghost]
        keepsake = KEEPSAKES[params.keepsake]
        referral = REFERRALS[params.referral]
        light = LIGHTS[params.light]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid child gender: {params.child_gender})")
    if params.caretaker not in COMPANIONS:
        raise StoryError(f"(Invalid caretaker: {params.caretaker})")
    if not valid_combo(params.venue, params.ghost, params.keepsake, params.referral):
        raise StoryError(explain_invalid(params.venue, params.ghost, params.keepsake, params.referral))

    world = tell(
        venue=venue,
        ghost_cfg=ghost_cfg,
        keepsake_cfg=keepsake,
        referral_cfg=referral,
        light_cfg=light,
        child_name=params.child_name,
        child_gender=params.child_gender,
        caretaker_type=params.caretaker,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, ghost, keepsake, referral) combos:\n")
        for venue_id, ghost_id, keepsake_id, referral_id in combos:
            print(f"  {venue_id:10} {ghost_id:6} {keepsake_id:11} {referral_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.ghost} in {p.venue} ({outcome_of(p.venue, p.trait, p.light, p.referral)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
