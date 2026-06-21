#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py
==============================================================================

A gentle ghost-story storyworld about a child who thinks a house is haunted,
then discovers the ghost is lonely rather than cruel. The child shows mercy,
offers a fitting kindness, and the haunting turns into reconciliation.

The world model keeps a small typed simulation:
- a child, a grown-up, a ghost, and a keepsake
- physical meters like cold, glow, found, and settled
- emotional memes like fear, pity, trust, and relief

The turn is state-driven: a restless ghost makes a room feel colder and fills it
with a particular sign. When the child follows that sign, finds the misplaced
keepsake, and cares for it in the right way, the ghost settles. The twist is
that the "scary" ghost was only asking for help.

Run it
------
    python storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py
    python storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py --room attic --keepsake portrait --sign frame_taps --kindness hang_straight
    python storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py --room nursery --keepsake teacup
    python storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mercy_reconciliation_kindness_twist_ghost_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class RoomCfg:
    id: str
    label: str
    phrase: str
    old_item_spot: str
    safe_glow: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SignCfg:
    id: str
    label: str
    opening: str
    trail: str
    source_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class KeepsakeCfg:
    id: str
    label: str
    phrase: str
    owner_hint: str
    resting_place: str
    need_kindness: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindnessCfg:
    id: str
    label: str
    fits: set[str] = field(default_factory=set)
    action_text: str = ""
    gentle_result: str = ""
    qa_text: str = ""
    mercy_words: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room_cfg: RoomCfg) -> None:
        self.room_cfg = room_cfg
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
        clone = World(self.room_cfg)
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


def _r_restless_cold(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if ghost is None or room is None or child is None:
        return []
    if ghost.meters["restless"] < THRESHOLD:
        return []
    sig = ("cold",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    child.memes["fear"] += 1
    return []


def _r_sign_to_search(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if ghost is None or child is None:
        return []
    if ghost.meters["signaling"] < THRESHOLD:
        return []
    sig = ("search",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.meters["searching"] += 1
    return []


def _r_kindness_settles(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    keepsake = world.entities.get("keepsake")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if ghost is None or keepsake is None or room is None or child is None:
        return []
    if keepsake.meters["cared_for"] < THRESHOLD:
        return []
    sig = ("settled",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["settled"] += 1
    ghost.meters["restless"] = 0.0
    room.meters["cold"] = 0.0
    room.meters["warm_glow"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="restless_cold", tag="physical", apply=_r_restless_cold),
    Rule(name="sign_to_search", tag="social", apply=_r_sign_to_search),
    Rule(name="kindness_settles", tag="resolution", apply=_r_kindness_settles),
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


ROOMS = {
    "attic": RoomCfg(
        id="attic",
        label="attic",
        phrase="the attic under the sloping roof",
        old_item_spot="a cedar trunk near the window",
        safe_glow="the moon made a silver pool across the floorboards",
        allows={"music_box", "portrait"},
        tags={"attic", "ghost_house"},
    ),
    "parlor": RoomCfg(
        id="parlor",
        label="parlor",
        phrase="the old parlor with a sleepy fireplace",
        old_item_spot="a side table beside the fireplace",
        safe_glow="the last coal glowed red in the grate",
        allows={"music_box", "portrait", "teacup"},
        tags={"parlor", "ghost_house"},
    ),
    "nursery": RoomCfg(
        id="nursery",
        label="nursery",
        phrase="the quiet nursery at the end of the hall",
        old_item_spot="a painted shelf under the moonlit window",
        safe_glow="the wallpaper stars seemed almost awake",
        allows={"wooden_horse", "music_box"},
        tags={"nursery", "ghost_house"},
    ),
}

SIGNS = {
    "humming": SignCfg(
        id="humming",
        label="a thin humming tune",
        opening="a thin humming tune drifted through the dark",
        trail="the tune seemed to come from inside an old box",
        source_for={"music_box"},
        tags={"music_box", "sound"},
    ),
    "frame_taps": SignCfg(
        id="frame_taps",
        label="soft taps from the wall",
        opening="three soft taps came from the wall, then three more",
        trail="the taps kept drawing the eye to a dusty picture hook",
        source_for={"portrait"},
        tags={"portrait", "sound"},
    ),
    "cup_clink": SignCfg(
        id="cup_clink",
        label="a lonely clink of china",
        opening="a lonely clink of china sounded from the dark",
        trail="the tiny clink led straight to a tray with one missing cup",
        source_for={"teacup"},
        tags={"teacup", "sound"},
    ),
    "hoof_taps": SignCfg(
        id="hoof_taps",
        label="little hoof taps on the floorboards",
        opening="little hoof taps pattered across the floorboards",
        trail="the taps stopped beside a toy chest with a broken latch",
        source_for={"wooden_horse"},
        tags={"toy", "sound"},
    ),
}

KEEPSAKES = {
    "music_box": KeepsakeCfg(
        id="music_box",
        label="music box",
        phrase="a little silver music box",
        owner_hint="someone once rocked a baby to sleep with that song",
        resting_place="the small table by the bed",
        need_kindness="wind_and_place",
        reveal_line="the ghost was not hunting anyone at all; it only wanted its lullaby heard kindly again",
        tags={"music_box", "memory"},
    ),
    "portrait": KeepsakeCfg(
        id="portrait",
        label="portrait",
        phrase="a round portrait in a brass frame",
        owner_hint="someone had loved the smiling face in that picture",
        resting_place="the old picture hook above the mantel",
        need_kindness="hang_straight",
        reveal_line="the ghost had been tapping because the family picture had been taken down and forgotten",
        tags={"portrait", "memory"},
    ),
    "teacup": KeepsakeCfg(
        id="teacup",
        label="teacup",
        phrase="a blue teacup with a tiny painted rose",
        owner_hint="someone had once shared quiet evening tea in this room",
        resting_place="the tray by the fireplace",
        need_kindness="set_on_tray",
        reveal_line="the ghost had not come for revenge; it had come because one dear cup had been left alone in the dust",
        tags={"teacup", "memory"},
    ),
    "wooden_horse": KeepsakeCfg(
        id="wooden_horse",
        label="wooden horse",
        phrase="a small wooden horse with one loose ribbon",
        owner_hint="someone had once pushed that toy gently across the nursery floor",
        resting_place="the painted nursery shelf",
        need_kindness="mend_and_shelve",
        reveal_line="the ghost had only wanted the toy set back where a child had loved it",
        tags={"toy", "memory"},
    ),
}

KINDNESSES = {
    "wind_and_place": KindnessCfg(
        id="wind_and_place",
        label="wind the music box and set it carefully down",
        fits={"music_box"},
        action_text="wound the little key, listened to the tune wake up, and set the music box carefully on the small table by the bed",
        gentle_result="The tune floated through the room like a soft blanket.",
        qa_text="wound the music box and placed it where it belonged",
        mercy_words='Then {child} whispered, "If you only wanted your song, I will show mercy and help."',
        tags={"music_box", "kindness"},
    ),
    "hang_straight": KindnessCfg(
        id="hang_straight",
        label="dust the portrait and hang it straight",
        fits={"portrait"},
        action_text="wiped the glass with a sleeve, lifted the portrait with both hands, and hung it straight on the old picture hook",
        gentle_result="The brass frame caught the firelight and shone warmly instead of gloomily.",
        qa_text="dusted the portrait and hung it back on the wall",
        mercy_words='Then {child} whispered, "I thought you wanted to frighten me, but I will show mercy and put it right."',
        tags={"portrait", "kindness"},
    ),
    "set_on_tray": KindnessCfg(
        id="set_on_tray",
        label="carry the teacup back to its tray",
        fits={"teacup"},
        action_text="lifted the blue teacup from the dusty box and set it gently on the tray by the fireplace",
        gentle_result="The china gave one small happy clink, as if answering.",
        qa_text="carried the teacup back to its tray",
        mercy_words='Then {child} whispered, "You seem lonely, not mean. I will show mercy and help you."',
        tags={"teacup", "kindness"},
    ),
    "mend_and_shelve": KindnessCfg(
        id="mend_and_shelve",
        label="tie the ribbon and place the wooden horse on its shelf",
        fits={"wooden_horse"},
        action_text="tied the loose ribbon into a neat bow and placed the wooden horse on the painted nursery shelf",
        gentle_result="The little toy stood as proudly as if it had been waiting all along.",
        qa_text="fixed the ribbon and placed the wooden horse back on its shelf",
        mercy_words='Then {child} whispered, "I will not run from you. I will show mercy and be gentle."',
        tags={"toy", "kindness"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Elsie", "Clara", "Rose", "June"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Sam", "Eli", "Noah", "Theo", "Finn"]
TRAITS = ["gentle", "careful", "curious", "thoughtful", "brave", "kind"]


def sign_matches_keepsake(sign_id: str, keepsake_id: str) -> bool:
    return keepsake_id in SIGNS[sign_id].source_for


def kindness_fits_keepsake(kindness_id: str, keepsake_id: str) -> bool:
    return keepsake_id in KINDNESSES[kindness_id].fits


def room_allows_keepsake(room_id: str, keepsake_id: str) -> bool:
    return keepsake_id in ROOMS[room_id].allows


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for keepsake_id in room.allows:
            for sign_id in SIGNS:
                if not sign_matches_keepsake(sign_id, keepsake_id):
                    continue
                for kindness_id in KINDNESSES:
                    if kindness_fits_keepsake(kindness_id, keepsake_id):
                        combos.append((room_id, sign_id, keepsake_id, kindness_id))
    return sorted(combos)


def outcome_of(room_id: str, sign_id: str, keepsake_id: str, kindness_id: str) -> str:
    if (
        room_allows_keepsake(room_id, keepsake_id)
        and sign_matches_keepsake(sign_id, keepsake_id)
        and kindness_fits_keepsake(kindness_id, keepsake_id)
    ):
        return "reconciled"
    return "unsettled"


def explain_room_rejection(room_id: str, keepsake_id: str) -> str:
    room = ROOMS[room_id]
    keepsake = KEEPSAKES[keepsake_id]
    allowed = ", ".join(sorted(room.allows))
    return (
        f"(No story: {room.label} is not a good home for the {keepsake.label} in this world. "
        f"That room only supports keepsakes like {allowed}.)"
    )


def explain_sign_rejection(sign_id: str, keepsake_id: str) -> str:
    sign = SIGNS[sign_id]
    keepsake = KEEPSAKES[keepsake_id]
    return (
        f"(No story: {sign.label} does not point to the {keepsake.label}. "
        f"The haunting sign must honestly grow from the missing keepsake.)"
    )


def explain_kindness_rejection(kindness_id: str, keepsake_id: str) -> str:
    kindness = KINDNESSES[kindness_id]
    keepsake = KEEPSAKES[keepsake_id]
    return (
        f"(No story: '{kindness.label}' is not the right act of mercy for the {keepsake.label}. "
        f"The reconciliation only works when the kindness fits what was lost.)"
    )


def predict_restless(world: World) -> dict:
    sim = world.copy()
    ghost = sim.get("ghost")
    ghost.meters["restless"] += 1
    ghost.meters["signaling"] += 1
    propagate(sim, narrate=False)
    room = sim.get("room")
    child = sim.get("child")
    return {
        "cold": room.meters["cold"],
        "fear": child.memes["fear"],
        "searching": child.meters["searching"],
    }


def predict_resolution(world: World) -> dict:
    sim = world.copy()
    keepsake = sim.get("keepsake")
    keepsake.meters["cared_for"] += 1
    propagate(sim, narrate=False)
    return {
        "settled": sim.get("ghost").meters["settled"],
        "warm_glow": sim.get("room").meters["warm_glow"],
        "relief": sim.get("child").memes["relief"],
    }


def introduce(world: World, child: Entity, elder: Entity, room: RoomCfg) -> None:
    world.say(
        f"One windy evening, {child.id} stayed with {child.pronoun('possessive')} {elder.label_word} "
        f"in {room.phrase}. The house was old enough to creak in its sleep."
    )
    world.say(
        f"{child.id} was a {next((t for t in child.attrs.get('traits', []) if t), 'curious')} "
        f"{child.type} who tried to be brave, even when the shadows looked longer than they should."
    )


def settle_in(world: World, child: Entity, elder: Entity, room: RoomCfg) -> None:
    world.say(
        f"After supper, {elder.label_word.capitalize()} carried up a lantern and said the storm would pass soon."
    )
    world.say(
        f"But when the house grew quiet, {room.safe_glow}, and that somehow made the dark corners look deeper."
    )


def haunting_begins(world: World, child: Entity, sign: SignCfg) -> None:
    ghost = world.get("ghost")
    ghost.meters["restless"] += 1
    ghost.meters["signaling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {sign.opening}. {child.id} pulled the blanket to {child.pronoun('possessive')} chin and listened very hard."
    )


def fear_and_guess(world: World, child: Entity, elder: Entity) -> None:
    pred = predict_restless(world)
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["fear"] += 1
    world.say(
        f'"There is a ghost," {child.id} whispered. {elder.label_word.capitalize()} sat beside {child.pronoun("object")}, '
        f'and though {elder.pronoun()} kept a calm voice, even the room felt colder now.'
    )
    world.say(
        f'"Old houses make old sounds," {elder.label_word.capitalize()} said softly. "Still, we can look kindly before we decide to be angry."'
    )


def follow_sign(world: World, child: Entity, elder: Entity, room: RoomCfg, sign: SignCfg) -> None:
    child.memes["courage"] += 1
    world.say(
        f"So {child.id} took the lantern, and {elder.label_word} went too. They crossed {room.phrase}, "
        f"following the sound until {sign.trail}."
    )


def find_keepsake(world: World, child: Entity, keepsake: KeepsakeCfg, room: RoomCfg) -> None:
    item = world.get("keepsake")
    item.meters["found"] += 1
    world.say(
        f"Inside {room.old_item_spot} they found {keepsake.phrase}, gray with dust. At once {child.id} understood that "
        f"{keepsake.owner_hint}."
    )


def reveal_twist(world: World, child: Entity, ghost: Entity, keepsake: KeepsakeCfg) -> None:
    child.memes["pity"] += 1
    ghost.memes["hope"] += 1
    world.say(
        f"A pale figure appeared beside them, not with claws or a roar, but with sad eyes and folded hands. "
        f"{keepsake.reveal_line}."
    )
    world.say(
        f"The twist made {child.id}'s fear loosen. The ghost had not been wicked at all. It had been lonely."
    )


def show_mercy(world: World, child: Entity, kindness: KindnessCfg) -> None:
    line = kindness.mercy_words.format(child=child.id)
    world.say(line)


def perform_kindness(world: World, child: Entity, kindness: KindnessCfg) -> None:
    keepsake = world.get("keepsake")
    keepsake.meters["cared_for"] += 1
    child.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(f"So {child.id} {kindness.action_text}.")
    world.say(kindness.gentle_result)


def reconciliation(world: World, child: Entity, elder: Entity, room: RoomCfg) -> None:
    ghost = world.get("ghost")
    child.memes["reconciliation"] += 1
    ghost.memes["gratitude"] += 1
    world.say(
        f"The ghost's sharp edges thinned into a soft, pearly light. The cold left {room.phrase}, and the house breathed out as if it had been waiting."
    )
    world.say(
        f'"Thank you," sighed the ghost. {elder.label_word.capitalize()} squeezed {child.id}\'s shoulder, proud that kindness had done what fear could not.'
    )


def ending_image(world: World, child: Entity, elder: Entity, room: RoomCfg, keepsake: KeepsakeCfg) -> None:
    world.say(
        f"After that night, whenever {child.id} passed through {room.label}, it no longer felt haunted. It felt remembered."
    )
    world.say(
        f"And on the place where the {keepsake.label} now rested, a small, peaceful shine stayed behind like a smile no storm could blow away."
    )


def tell(
    room_cfg: RoomCfg,
    sign_cfg: SignCfg,
    keepsake_cfg: KeepsakeCfg,
    kindness_cfg: KindnessCfg,
    child_name: str = "Lily",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World(room_cfg)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"traits": [trait]},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost",
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label=room_cfg.label,
            phrase=room_cfg.phrase,
        )
    )
    keepsake = world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake_cfg.label,
            phrase=keepsake_cfg.phrase,
            tags=set(keepsake_cfg.tags),
        )
    )

    introduce(world, child, elder, room_cfg)
    settle_in(world, child, elder, room_cfg)

    world.para()
    haunting_begins(world, child, sign_cfg)
    fear_and_guess(world, child, elder)
    follow_sign(world, child, elder, room_cfg, sign_cfg)

    world.para()
    find_keepsake(world, child, keepsake_cfg, room_cfg)
    reveal_twist(world, child, ghost, keepsake_cfg)
    show_mercy(world, child, kindness_cfg)
    perform_kindness(world, child, kindness_cfg)

    world.para()
    reconciliation(world, child, elder, room_cfg)
    ending_image(world, child, elder, room_cfg, keepsake_cfg)

    outcome = "reconciled" if ghost.meters["settled"] >= THRESHOLD else "unsettled"
    world.facts.update(
        child=child,
        elder=elder,
        ghost=ghost,
        room_cfg=room_cfg,
        sign_cfg=sign_cfg,
        keepsake_cfg=keepsake_cfg,
        kindness_cfg=kindness_cfg,
        outcome=outcome,
        predicted_resolution=predict_resolution(world),
    )
    return world


@dataclass
class StoryParams:
    room: str
    sign: str
    keepsake: str
    kindness: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        room="attic",
        sign="frame_taps",
        keepsake="portrait",
        kindness="hang_straight",
        child_name="Clara",
        child_gender="girl",
        elder="grandmother",
        trait="careful",
    ),
    StoryParams(
        room="parlor",
        sign="cup_clink",
        keepsake="teacup",
        kindness="set_on_tray",
        child_name="Tom",
        child_gender="boy",
        elder="grandfather",
        trait="thoughtful",
    ),
    StoryParams(
        room="nursery",
        sign="hoof_taps",
        keepsake="wooden_horse",
        kindness="mend_and_shelve",
        child_name="Nora",
        child_gender="girl",
        elder="grandmother",
        trait="gentle",
    ),
    StoryParams(
        room="attic",
        sign="humming",
        keepsake="music_box",
        kindness="wind_and_place",
        child_name="Ben",
        child_gender="boy",
        elder="grandfather",
        trait="curious",
    ),
]


KNOWLEDGE = {
    "ghost_house": [
        (
            "What makes an old house sound spooky?",
            "Old houses creak because wood, pipes, and windows move a little in wind or cold. Those sounds can feel spooky when the house is quiet.",
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space just under the roof of a house. People often keep old boxes and keepsakes there.",
        )
    ],
    "parlor": [
        (
            "What is a parlor?",
            "A parlor is an old-fashioned sitting room where people talk, rest, or drink tea together.",
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a small box with a tiny tune inside. When you wind it, it plays a gentle song.",
        )
    ],
    "portrait": [
        (
            "What is a portrait?",
            "A portrait is a picture of a person. Families keep portraits to remember people they love.",
        )
    ],
    "teacup": [
        (
            "Why can a teacup feel special to someone?",
            "A teacup can hold memories of quiet talks and family time. That can make even a small cup feel precious.",
        )
    ],
    "toy": [
        (
            "Why do toys sometimes matter for a long time?",
            "A toy can remind someone of being small, loved, and safe. That memory can matter even after the toy is old.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to be gentle and helpful instead of harsh. It can make other people feel safe and understood.",
        )
    ],
    "mercy": [
        (
            "What is mercy?",
            "Mercy is choosing gentleness when you could answer with anger or fear instead. It means giving compassion to someone who needs it.",
        )
    ],
    "memory": [
        (
            "Why do people keep keepsakes?",
            "People keep keepsakes because objects can hold memories of people, places, and loving moments. A keepsake helps a memory feel close.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost_house",
    "attic",
    "parlor",
    "music_box",
    "portrait",
    "teacup",
    "toy",
    "kindness",
    "mercy",
    "memory",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    room_cfg = f["room_cfg"]
    sign_cfg = f["sign_cfg"]
    keepsake_cfg = f["keepsake_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "mercy" and ends with reconciliation.',
        f"Tell a ghost story where a child named {child.id} hears {sign_cfg.label} in {room_cfg.phrase}, thinks a ghost is scary, and then learns the ghost only wants help with a lost {keepsake_cfg.label}.",
        f"Write a kind ghost story with a twist: the haunting in the {room_cfg.label} is really a lonely memory asking for care, and the child solves it through mercy instead of anger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    room_cfg = f["room_cfg"]
    sign_cfg = f["sign_cfg"]
    keepsake_cfg = f["keepsake_cfg"]
    kindness_cfg = f["kindness_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child staying with {child.pronoun('possessive')} {elder.label_word}, and a lonely ghost in {room_cfg.phrase}. The story follows how fear turns into kindness.",
        ),
        (
            "What first made the room seem haunted?",
            f"The haunting began when {sign_cfg.opening} in the dark room. That strange sign made {child.id} think a ghost might be trying to scare everyone.",
        ),
        (
            f"Why was {child.id} afraid at first?",
            f"{child.id} felt afraid because the room turned colder and the sound came from the dark. When something is hidden and strange, it is easy to imagine danger before you know the truth.",
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the ghost was not mean at all. It was lonely and restless because the {keepsake_cfg.label} had been misplaced and forgotten.",
        ),
        (
            f"How did {child.id} show mercy?",
            f"{child.id} chose mercy by speaking gently and helping instead of running away or getting angry. Then {child.pronoun()} {kindness_cfg.qa_text}, which answered what the ghost had really needed.",
        ),
        (
            "How did the story end?",
            f"The ghost settled into a soft light, the cold left the room, and peace came back to the house. The ending shows reconciliation, because kindness repaired what fear had misunderstood.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    room_cfg = f["room_cfg"]
    keepsake_cfg = f["keepsake_cfg"]
    tags: set[str] = set(room_cfg.tags) | set(keepsake_cfg.tags) | {"kindness", "mercy"}
    if keepsake_cfg.id == "wooden_horse":
        tags.add("toy")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sign_matches(S, K) :- sign_points_to(S, K).
kindness_fits(A, K) :- kindness_for(A, K).

valid(Room, Sign, Keep, Act) :-
    room(Room), sign(Sign), keepsake(Keep), kindness(Act),
    allowed(Room, Keep),
    sign_matches(Sign, Keep),
    kindness_fits(Act, Keep).

outcome(Room, Sign, Keep, Act, reconciled) :-
    valid(Room, Sign, Keep, Act).

outcome(Room, Sign, Keep, Act, unsettled) :-
    room(Room), sign(Sign), keepsake(Keep), kindness(Act),
    not valid(Room, Sign, Keep, Act).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for keepsake_id in sorted(room.allows):
            lines.append(asp.fact("allowed", room_id, keepsake_id))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        for keepsake_id in sorted(sign.source_for):
            lines.append(asp.fact("sign_points_to", sign_id, keepsake_id))
    for keepsake_id in KEEPSAKES:
        lines.append(asp.fact("keepsake", keepsake_id))
    for kindness_id, kindness in KINDNESSES.items():
        lines.append(asp.fact("kindness", kindness_id))
        for keepsake_id in sorted(kindness.fits):
            lines.append(asp.fact("kindness_for", kindness_id, keepsake_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(room_id: str, sign_id: str, keepsake_id: str, kindness_id: str) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_room", room_id),
            asp.fact("chosen_sign", sign_id),
            asp.fact("chosen_keep", keepsake_id),
            asp.fact("chosen_act", kindness_id),
            (
                "picked_outcome(O) :- outcome(R,S,K,A,O), "
                "chosen_room(R), chosen_sign(S), chosen_keep(K), chosen_act(A)."
            ),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
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

    all_rooms = sorted(ROOMS)
    all_signs = sorted(SIGNS)
    all_keepsakes = sorted(KEEPSAKES)
    all_kindness = sorted(KINDNESSES)
    mismatches = []
    checked = 0
    for room_id in all_rooms:
        for sign_id in all_signs:
            for keepsake_id in all_keepsakes:
                for kindness_id in all_kindness:
                    checked += 1
                    py = outcome_of(room_id, sign_id, keepsake_id, kindness_id)
                    asp_out = asp_outcome(room_id, sign_id, keepsake_id, kindness_id)
                    if py != asp_out:
                        mismatches.append((room_id, sign_id, keepsake_id, kindness_id, py, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {checked} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes ({len(mismatches)} cases).")
        for row in mismatches[:10]:
            print(" ", row)

    try:
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise StoryError("Generated story was empty in smoke test.")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a child mistakes a lonely haunting for danger, then shows mercy and kindness."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.keepsake and not room_allows_keepsake(args.room, args.keepsake):
        raise StoryError(explain_room_rejection(args.room, args.keepsake))
    if args.sign and args.keepsake and not sign_matches_keepsake(args.sign, args.keepsake):
        raise StoryError(explain_sign_rejection(args.sign, args.keepsake))
    if args.kindness and args.keepsake and not kindness_fits_keepsake(args.kindness, args.keepsake):
        raise StoryError(explain_kindness_rejection(args.kindness, args.keepsake))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.sign is None or combo[1] == args.sign)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.kindness is None or combo[3] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, sign_id, keepsake_id, kindness_id = rng.choice(combos)
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        room=room_id,
        sign=sign_id,
        keepsake=keepsake_id,
        kindness=kindness_id,
        child_name=child_name,
        child_gender=child_gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.kindness not in KINDNESSES:
        raise StoryError(f"(Unknown kindness act: {params.kindness})")
    if not room_allows_keepsake(params.room, params.keepsake):
        raise StoryError(explain_room_rejection(params.room, params.keepsake))
    if not sign_matches_keepsake(params.sign, params.keepsake):
        raise StoryError(explain_sign_rejection(params.sign, params.keepsake))
    if not kindness_fits_keepsake(params.kindness, params.keepsake):
        raise StoryError(explain_kindness_rejection(params.kindness, params.keepsake))

    world = tell(
        room_cfg=ROOMS[params.room],
        sign_cfg=SIGNS[params.sign],
        keepsake_cfg=KEEPSAKES[params.keepsake],
        kindness_cfg=KINDNESSES[params.kindness],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, sign, keepsake, kindness) combos:\n")
        for room_id, sign_id, keepsake_id, kindness_id in combos:
            print(f"  {room_id:8} {sign_id:12} {keepsake_id:12} {kindness_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.child_name}: {p.keepsake} in the {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
