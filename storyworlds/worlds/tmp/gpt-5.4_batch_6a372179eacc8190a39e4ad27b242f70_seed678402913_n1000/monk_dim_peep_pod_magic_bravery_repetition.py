#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py
=========================================================================

A standalone story world for a gentle ghost-story domain built from the seed
words "monk-dim", "peep", and "pod", with the features Magic, Bravery, and
Repetition.

Premise
-------
A child hears a tiny "peep, peep" in a monk-dim old place at dusk. The sound
seems ghostly. Hidden nearby is a small magic pod. If the child dares to repeat
the pod's little charm enough times, the pod begins to glow, the frightened
ghost becomes gentle and visible, and the place changes from eerie to kind. If
the child is too frightened to keep repeating the charm, the ghost is left
unhelped and the child hurries away still wondering.

World-model idea
----------------
This world uses one shared Entity class for children, ghosts, places, and
objects. State evolves on two axes:

* physical meters: dark, glow, hush, open, etc.
* emotional memes: fear, bravery, trust, relief, wonder, loneliness.

A simple rule engine turns hidden-ghost + darkness into eeriness, and magic glow
into hope and calming. The prose is rendered from the resulting state rather
than from a frozen template.

Reasonableness gate
-------------------
Not every ghost belongs in every place, and not every pod can help every ghost.
A combination is valid only when:

* the place can host that ghost kind, and
* the pod's magic matches the ghost's need.

Outcome model
-------------
Even for a valid setup, the child must gather enough courage by repeating the
charm. The ending is:

* helped   -- bravery plus repetition is enough to calm and help the ghost
* fled     -- the child starts but cannot keep going, so the mystery remains

Run it
------
python storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py
python storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py --all
python storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py --qa
python storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py --trace --seed 7
python storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py --asp
python storyworlds/worlds/gpt-5.4/monk_dim_peep_pod_magic_bravery_repetition.py --verify
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

# Make the shared result containers importable when this script is run directly
# from a nested world directory:
# storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MAP = {"timid": 1, "steady": 2, "bold": 3}


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str = ""
    label: str = ""
    phrase: str = ""
    opening: str = ""
    echo: str = ""
    host_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostKind:
    id: str = ""
    label: str = ""
    phrase: str = ""
    opening: str = ""
    need: str = ""
    need_label: str = ""
    reveal: str = ""
    peace: str = ""
    peep_sound: str = "peep, peep"
    place_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    soothe_need: int = 4


@dataclass
class PodKind:
    id: str = ""
    label: str = ""
    phrase: str = ""
    magic: str = ""
    charm: str = ""
    glow: str = ""
    gift: str = ""
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


def _r_eerie(world: World) -> list[str]:
    out: list[str] = []
    place = world.entities.get("place")
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if place is None or ghost is None or child is None:
        return out
    if place.meters["dark"] >= THRESHOLD and ghost.meters["hidden"] >= THRESHOLD:
        sig = ("eerie",)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["hush"] += 1
            child.memes["fear"] += 1
            out.append("__eerie__")
    return out


def _r_glow_hope(world: World) -> list[str]:
    out: list[str] = []
    pod = world.entities.get("pod")
    place = world.entities.get("place")
    ghost = world.entities.get("ghost")
    if pod is None or place is None or ghost is None:
        return out
    level = int(pod.meters["spoken"])
    for step in range(1, level + 1):
        sig = ("glow", step)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        place.meters["glow"] += 1
        if place.meters["dark"] > 0:
            place.meters["dark"] -= 1
        ghost.memes["hope"] += 1
        ghost.memes["trust"] += 1
        out.append("__glow__")
    return out


def _r_visible(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    place = world.entities.get("place")
    if ghost is None or child is None or place is None:
        return out
    if ghost.memes["trust"] >= THRESHOLD and place.meters["glow"] >= THRESHOLD:
        sig = ("visible",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["visible"] += 1
            if child.memes["fear"] > 0:
                child.memes["fear"] -= 1
            child.memes["wonder"] += 1
            out.append("__visible__")
    return out


CAUSAL_RULES = [
    Rule(name="eerie", tag="mood", apply=_r_eerie),
    Rule(name="glow_hope", tag="magic", apply=_r_glow_hope),
    Rule(name="visible", tag="social", apply=_r_visible),
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


def combo_valid(place: Place, ghost: GhostKind, pod: PodKind) -> bool:
    return bool(place.host_tags & ghost.place_tags) and pod.magic == ghost.need


def courage_total(courage: str, repeats: int) -> int:
    return BRAVERY_MAP[courage] + repeats


def outcome_of(params: "StoryParams") -> str:
    if not combo_valid(PLACES[params.place], GHOSTS[params.ghost], PODS[params.pod]):
        raise StoryError("(No valid story: the ghost, place, and pod do not belong together.)")
    ghost = GHOSTS[params.ghost]
    total = courage_total(params.courage, params.repeats)
    return "helped" if total >= ghost.soothe_need else "fled"


def predict_outcome(world: World, courage: str, repeats: int, soothe_need: int) -> dict:
    sim = world.copy()
    child = sim.get("child")
    pod = sim.get("pod")
    child.memes["bravery"] = float(BRAVERY_MAP[courage])
    for _ in range(repeats):
        child.memes["bravery"] += 1
        pod.meters["spoken"] += 1
        propagate(sim, narrate=False)
    return {
        "glow": int(sim.get("place").meters["glow"]),
        "trust": int(sim.get("ghost").memes["trust"]),
        "helped": child.memes["bravery"] >= soothe_need,
    }


def introduce(world: World, child: Entity, place_cfg: Place) -> None:
    place = world.get("place")
    world.say(
        f"At dusk, {child.id} stepped into {place_cfg.phrase}. {place_cfg.opening}"
    )
    world.say(
        f"The stones were so monk-dim that even the corners looked folded in prayer."
    )
    place.meters["dark"] = 2


def hear_peep(world: World, child: Entity, ghost_cfg: GhostKind, place_cfg: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.pronoun()} heard it: {ghost_cfg.peep_sound}. {ghost_cfg.opening}"
    )
    world.say(place_cfg.echo)
    propagate(world, narrate=False)
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"{child.id}'s shoulders jumped, but {child.pronoun()} did not run."
        )


def find_pod(world: World, child: Entity, pod_cfg: PodKind) -> None:
    pod = world.get("pod")
    pod.meters["closed"] = 1
    world.say(
        f"Beneath a cracked stone lay {pod_cfg.phrase}. It was hardly bigger than {child.pronoun('possessive')} thumb."
    )
    world.say(
        f"When {child.id} touched it, the pod felt warm, as if a little bit of Magic had been waiting inside."
    )


def remember_charm(world: World, child: Entity, pod_cfg: PodKind, ghost_cfg: GhostKind,
                   courage: str, repeats: int) -> None:
    pred = predict_outcome(world, courage, repeats, ghost_cfg.soothe_need)
    world.facts["predicted_glow"] = pred["glow"]
    world.facts["predicted_helped"] = pred["helped"]
    world.say(
        f"{child.id} remembered an old saying: if a frightened thing makes only a peep, you must answer softly and keep answering."
    )
    world.say(
        f'The words on the pod seemed to wake under {child.pronoun("possessive")} fingers: "{pod_cfg.charm}"'
    )


def repeat_charm(world: World, child: Entity, pod_cfg: PodKind, count: int) -> None:
    pod = world.get("pod")
    place = world.get("place")
    child.memes["bravery"] += 1
    pod.meters["spoken"] += 1
    propagate(world, narrate=False)
    number_word = {1: "once", 2: "twice", 3: "three times"}[count]
    if count == 1:
        world.say(
            f'{child.id} whispered it {number_word}. {pod_cfg.glow}'
        )
    elif count == 2:
        world.say(
            f'{child.id} said it {number_word}, and the pod answered with a pale silver shine.'
        )
    else:
        world.say(
            f'{child.id} said it {number_word}, louder this time, and the light grew brave enough to touch the walls.'
        )
    if place.meters["dark"] <= 1:
        world.say("The dark no longer felt hungry. It listened instead.")


def reveal_ghost(world: World, child: Entity, ghost_cfg: GhostKind) -> None:
    ghost = world.get("ghost")
    ghost.meters["hidden"] = 0
    ghost.meters["visible"] = 1
    world.say(ghost_cfg.reveal)
    world.say(
        f"It was only a ghost because it was lost, not because it was cruel."
    )


def help_ghost(world: World, child: Entity, ghost_cfg: GhostKind, pod_cfg: PodKind) -> None:
    ghost = world.get("ghost")
    pod = world.get("pod")
    place = world.get("place")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["bravery"] += 1
    ghost.memes["peace"] += 1
    ghost.memes["loneliness"] = 0
    ghost.meters["settled"] += 1
    pod.meters["open"] = 1
    pod.meters["closed"] = 0
    place.meters["dark"] = 0
    place.meters["glow"] += 1
    world.say(
        f"{child.id} held out the pod, and {pod_cfg.gift}."
    )
    world.say(ghost_cfg.peace)
    world.say(
        f"After that, the place was still old and quiet, but it was not frightening anymore."
    )


def leave_wondering(world: World, child: Entity, ghost_cfg: GhostKind) -> None:
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} began the charm, but the little peep sounded farther away each time."
    )
    world.say(
        f"The child hugged the pod to {child.pronoun('possessive')} chest and backed toward the door before {ghost_cfg.label} could fully appear."
    )
    world.say(
        f"Outside, the night air felt bigger and easier to breathe, yet {child.id} still wondered who had needed help in the dark."
    )


def tell(place_cfg: Place, ghost_cfg: GhostKind, pod_cfg: PodKind,
         child_name: str = "Nell", child_type: str = "girl",
         courage: str = "steady", repeats: int = 2) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        tags={"child"},
    ))
    place = world.add(Entity(
        id="place",
        kind="place",
        type="place",
        label=place_cfg.label,
        phrase=place_cfg.phrase,
        role="place",
        tags=set(place_cfg.tags),
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=ghost_cfg.label,
        phrase=ghost_cfg.phrase,
        role="ghost",
        tags=set(ghost_cfg.tags),
    ))
    pod = world.add(Entity(
        id="pod",
        kind="thing",
        type="pod",
        label=pod_cfg.label,
        phrase=pod_cfg.phrase,
        role="pod",
        tags=set(pod_cfg.tags),
    ))

    ghost.meters["hidden"] = 1
    ghost.memes["loneliness"] = 1
    child.memes["bravery"] = float(BRAVERY_MAP[courage])

    introduce(world, child, place_cfg)
    hear_peep(world, child, ghost_cfg, place_cfg)

    world.para()
    find_pod(world, child, pod_cfg)
    remember_charm(world, child, pod_cfg, ghost_cfg, courage, repeats)

    world.para()
    for count in range(1, repeats + 1):
        repeat_charm(world, child, pod_cfg, count)

    helped = child.memes["bravery"] >= ghost_cfg.soothe_need
    world.para()
    if helped:
        reveal_ghost(world, child, ghost_cfg)
        help_ghost(world, child, ghost_cfg, pod_cfg)
    else:
        leave_wondering(world, child, ghost_cfg)

    world.facts.update(
        child=child,
        place_cfg=place_cfg,
        ghost_cfg=ghost_cfg,
        pod_cfg=pod_cfg,
        place=place,
        ghost=ghost,
        pod=pod,
        outcome="helped" if helped else "fled",
        repeats=repeats,
        courage=courage,
        helped=helped,
    )
    return world


PLACES = {
    "abbey_hall": Place(
        id="abbey_hall",
        label="abbey hall",
        phrase="the old abbey hall",
        opening="Long candle hooks hung empty there, and a thin evening light leaned through the windows.",
        echo='Every small sound came back a breath later, as if the hall itself wished to peep back, "peep, peep."',
        host_tags={"stone", "echo"},
        tags={"ghost", "old_place", "hall"},
    ),
    "bell_tower": Place(
        id="bell_tower",
        label="bell tower",
        phrase="the winding bell tower",
        opening="The stairs curled upward through shadow, and the ropes of the bells slept without moving.",
        echo='From above came the tiniest "peep, peep," so faint it sounded like a lost note from a far bell.',
        host_tags={"high", "echo"},
        tags={"ghost", "tower", "bells"},
    ),
    "cloister_garden": Place(
        id="cloister_garden",
        label="cloister garden",
        phrase="the cloister garden behind the old wall",
        opening="Moonlight lay in the paths, but the hedges made little monk-dim rooms of shadow between the herbs.",
        echo='Near the rosemary, a nervous "peep, peep" slipped out from the leaves and hid again.',
        host_tags={"garden", "moon"},
        tags={"ghost", "garden", "moon"},
    ),
}

GHOSTS = {
    "lost_novice": GhostKind(
        id="lost_novice",
        label="a lantern-thin little ghost",
        phrase="a lantern-thin little ghost in a torn white robe",
        opening="It did not sound like a rat or a bird. It sounded like someone trying to be brave and failing.",
        need="light",
        need_label="a path of light",
        reveal="Out of the dimness came a small white figure, no taller than the child, with a face as pale as milk and eyes full of asking.",
        peace='When the silver light spread along the floor, the ghost smiled. It bowed, followed the shining path to the far door, and faded like mist at morning.',
        peep_sound="peep, peep",
        place_tags={"stone", "echo", "high"},
        tags={"ghost", "light"},
        soothe_need=4,
    ),
    "weeping_choir": GhostKind(
        id="weeping_choir",
        label="a humming choir ghost",
        phrase="a humming choir ghost with a soft torn collar",
        opening="The peeping sound had a tune folded inside it, like the first note of a song that had forgotten the rest.",
        need="song",
        need_label="a remembered song",
        reveal="A narrow child-ghost drifted from the shadows with both hands pressed to its throat, as if it had been searching for one lost note all night.",
        peace='The pod answered with a cradle-soft tune. The ghost found the missing note, sang one clear line, and then melted into the dark beams above like a kind breath.',
        peep_sound="peep, peep",
        place_tags={"echo", "high"},
        tags={"ghost", "song", "bells"},
        soothe_need=5,
    ),
    "dew_sleeper": GhostKind(
        id="dew_sleeper",
        label="a garden sleeper ghost",
        phrase="a garden sleeper ghost with leaves in its hair",
        opening="This peep sounded damp and tired, the way a dream might sound if it had fallen into the grass.",
        need="dew",
        need_label="a drink of moon-dew",
        reveal="Between the herbs stood a pale small ghost with wet curls and sleepy eyes, as if it had woken in the wrong season.",
        peace='Pearly drops rose from the pod and settled on the rosemary. The ghost touched them, sighed, and folded into the moonlit garden until even its edges smelled sweet.',
        peep_sound="peep, peep",
        place_tags={"garden", "moon"},
        tags={"ghost", "garden", "dew"},
        soothe_need=4,
    ),
}

PODS = {
    "glow_pod": PodKind(
        id="glow_pod",
        label="glow pod",
        phrase="a folded glow pod",
        magic="light",
        charm="Little pod, little light, show the kind road through the night.",
        glow="At once a bead of gold woke under its shell.",
        gift="the shell opened like a lantern flower and poured a soft path of light across the floor",
        tags={"pod", "light", "magic"},
    ),
    "hush_pod": PodKind(
        id="hush_pod",
        label="hush pod",
        phrase="a ribbed hush pod",
        magic="song",
        charm="Little pod, little song, carry the lost note right along.",
        glow="A thin warm hum stirred inside it.",
        gift="the shell parted and sent out a thread of music so gentle that even the dust seemed to listen",
        tags={"pod", "song", "magic"},
    ),
    "dew_pod": PodKind(
        id="dew_pod",
        label="dew pod",
        phrase="a pearly dew pod",
        magic="dew",
        charm="Little pod, little dew, wake the silver hidden through.",
        glow="A cool pearl-light trembled inside it.",
        gift="the shell loosened and floated up bright drops, round as moonlit tears",
        tags={"pod", "dew", "magic"},
    ),
}

GIRL_NAMES = ["Nell", "Mira", "Tessa", "Lina", "May", "Ivy", "Clara", "Elsie"]
BOY_NAMES = ["Oren", "Tobin", "Miles", "Rowan", "Eli", "Jon", "Felix", "Hugo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for ghost_id, ghost in GHOSTS.items():
            for pod_id, pod in PODS.items():
                if combo_valid(place, ghost, pod):
                    combos.append((place_id, ghost_id, pod_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    ghost: str
    pod: str
    name: str
    gender: str
    courage: str
    repeats: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="abbey_hall",
        ghost="lost_novice",
        pod="glow_pod",
        name="Nell",
        gender="girl",
        courage="steady",
        repeats=2,
    ),
    StoryParams(
        place="bell_tower",
        ghost="weeping_choir",
        pod="hush_pod",
        name="Oren",
        gender="boy",
        courage="bold",
        repeats=2,
    ),
    StoryParams(
        place="cloister_garden",
        ghost="dew_sleeper",
        pod="dew_pod",
        name="Mira",
        gender="girl",
        courage="steady",
        repeats=2,
    ),
    StoryParams(
        place="bell_tower",
        ghost="lost_novice",
        pod="glow_pod",
        name="Rowan",
        gender="boy",
        courage="timid",
        repeats=1,
    ),
]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with something spooky or mysterious in it. In gentle ghost stories, the ghost is often sad or lost instead of mean."
        )
    ],
    "magic": [
        (
            "What is Magic in a story?",
            "Magic is something impossible happening in a story, like a pod glowing or a song floating through the air. It helps make the world feel wondrous."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the kind or right thing even when you feel afraid. It does not mean you never feel scared."
        )
    ],
    "repetition": [
        (
            "Why do stories sometimes repeat words?",
            "Repeating words can make a story feel musical and memorable. It can also show a character trying again and again."
        )
    ],
    "pod": [
        (
            "What is a pod?",
            "A pod is a small shell or case that can hold seeds or something precious inside. In this story world, a pod can hold a little bit of magic too."
        )
    ],
    "light": [
        (
            "Why does light feel less scary than darkness?",
            "Light helps you see what is really there, so your mind has fewer shadows to worry about. It can make a place feel safer and calmer."
        )
    ],
    "song": [
        (
            "How can a song help someone feel calm?",
            "A soft song can make breathing slow down and hearts feel steadier. It can also help someone remember they are not alone."
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is water that gathers in tiny drops on grass and leaves, especially in the cool morning or evening."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "magic", "bravery", "repetition", "pod", "light", "song", "dew"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place_cfg = f["place_cfg"]
    ghost_cfg = f["ghost_cfg"]
    pod_cfg = f["pod_cfg"]
    outcome = f["outcome"]
    prompts = [
        (
            f'Write a gentle Ghost Story for a 3-to-5-year-old that includes the exact words '
            f'"monk-dim", "peep", and "pod", and uses Magic, Bravery, and Repetition.'
        ),
        (
            f"Tell a spooky-but-kind story where a {child.type} named {child.id} hears "
            f'"{ghost_cfg.peep_sound}" in {place_cfg.phrase}, finds {pod_cfg.phrase}, and must repeat a charm.'
        ),
    ]
    if outcome == "helped":
        prompts.append(
            f"Write a story where repetition helps a frightened child become brave enough to help a lost ghost, ending with {ghost_cfg.need_label}."
        )
    else:
        prompts.append(
            f"Write a mysterious story where the child begins bravely but cannot finish helping the ghost, and leaves still wondering about the peep in the dark."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    place_cfg = f["place_cfg"]
    ghost_cfg = f["ghost_cfg"]
    pod_cfg = f["pod_cfg"]
    repeats = f["repeats"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who hears a tiny ghostly peep in {place_cfg.phrase}. The story also follows the hidden ghost and the magic {pod_cfg.label}."
        ),
        (
            "What made the place feel spooky at first?",
            f"The place was monk-dim, quiet, and full of echoes, and a hidden voice kept saying {ghost_cfg.peep_sound}. Because the child could not see who was making the sound, the darkness felt more frightening."
        ),
        (
            f"What did {child.id} find?",
            f"{child.id} found {pod_cfg.phrase} tucked in the dark. The pod felt warm and seemed to hold a little Magic inside."
        ),
        (
            f"Why did {child.id} repeat the charm?",
            f"{child.id} repeated the charm to wake the pod's magic and answer the frightened peep kindly. Each repetition made the child a little braver and the dark a little less strong."
        ),
    ]
    if outcome == "helped":
        qa.append(
            (
                "How was the ghost helped?",
                f"The pod's magic gave the ghost {ghost_cfg.need_label}, which was exactly what it had been missing. Once the child kept going bravely, the ghost could stop hiding and finally rest."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully. The ghost was no longer lost, and the old place felt quiet in a friendly way instead of a frightening one."
            )
        )
    else:
        qa.append(
            (
                "Did the child solve the mystery?",
                f"Not completely. {child.id} began the charm and tried to be brave, but fear won before the ghost could be fully helped."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with wonder instead of peace. The child got safely outside, but still kept thinking about the tiny peep left in the dark."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "magic", "bravery", "repetition", "pod"}
    tags |= set(f["pod_cfg"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, ghost: GhostKind, pod: PodKind) -> str:
    if not (place.host_tags & ghost.place_tags):
        return (
            f"(No story: {ghost.label} does not belong naturally in {place.phrase}. "
            f"The place and ghost need to share the same kind of haunting.)"
        )
    if pod.magic != ghost.need:
        return (
            f"(No story: {pod.label} offers {pod.magic}, but {ghost.label} needs "
            f"{ghost.need_label}. The magic fix must match the ghost's problem.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
% Reasonableness gate.
valid(P, G, Pd) :- place(P), ghost(G), pod(Pd),
                   hosts(P, T), haunts(G, T),
                   needs(G, M), gives(Pd, M).

% Outcome model.
bravery_total(B + R) :- courage_value(B), repeats(R).
helped :- bravery_total(T), chosen_ghost(G), soothe_need(G, N), T >= N.
outcome(helped) :- helped.
outcome(fled) :- not helped.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for tag in sorted(place.host_tags):
            lines.append(asp.fact("hosts", place_id, tag))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("needs", ghost_id, ghost.need))
        lines.append(asp.fact("soothe_need", ghost_id, ghost.soothe_need))
        for tag in sorted(ghost.place_tags):
            lines.append(asp.fact("haunts", ghost_id, tag))
    for pod_id, pod in PODS.items():
        lines.append(asp.fact("pod", pod_id))
        lines.append(asp.fact("gives", pod_id, pod.magic))
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
            asp.fact("chosen_ghost", params.ghost),
            asp.fact("repeats", params.repeats),
            asp.fact("courage_value", BRAVERY_MAP[params.courage]),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a monk-dim place, a peep in the dark, and a magic pod."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--pod", choices=PODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--courage", choices=sorted(BRAVERY_MAP))
    ap.add_argument("--repeats", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.ghost and args.pod:
        if not combo_valid(PLACES[args.place], GHOSTS[args.ghost], PODS[args.pod]):
            raise StoryError(explain_rejection(PLACES[args.place], GHOSTS[args.ghost], PODS[args.pod]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.pod is None or combo[2] == args.pod)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ghost_id, pod_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    courage = args.courage or rng.choice(["timid", "steady", "bold"])
    repeats = args.repeats if args.repeats is not None else rng.choice([1, 2, 2, 3])
    return StoryParams(
        place=place_id,
        ghost=ghost_id,
        pod=pod_id,
        name=name,
        gender=gender,
        courage=courage,
        repeats=repeats,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.pod not in PODS:
        raise StoryError(f"(Unknown pod: {params.pod})")
    if params.courage not in BRAVERY_MAP:
        raise StoryError(f"(Unknown courage level: {params.courage})")
    if params.repeats not in {1, 2, 3}:
        raise StoryError("(Repeats must be 1, 2, or 3.)")

    place_cfg = PLACES[params.place]
    ghost_cfg = GHOSTS[params.ghost]
    pod_cfg = PODS[params.pod]
    if not combo_valid(place_cfg, ghost_cfg, pod_cfg):
        raise StoryError(explain_rejection(place_cfg, ghost_cfg, pod_cfg))

    world = tell(
        place_cfg=place_cfg,
        ghost_cfg=ghost_cfg,
        pod_cfg=pod_cfg,
        child_name=params.name,
        child_type=params.gender,
        courage=params.courage,
        repeats=params.repeats,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if py_valid == clingo_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - clingo_valid:
            print("  only in python:", sorted(py_valid - clingo_valid))
        if clingo_valid - py_valid:
            print("  only in clingo:", sorted(clingo_valid - py_valid))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        try:
            py = outcome_of(params)
            asp_res = asp_outcome(params)
        except StoryError as err:
            rc = 1
            print(f"Error while comparing outcome for {params}: {err}")
            continue
        if py != asp_res:
            mismatches.append((params, py, asp_res))
    if not mismatches:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for params, py, asp_res in mismatches[:10]:
            print(f"  {params} -> python={py}, asp={asp_res}")

    try:
        smoke = generate(CURATED[0])
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(smoke, trace=True, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, ghost, pod) combos:\n")
        for place_id, ghost_id, pod_id in combos:
            print(f"  {place_id:15} {ghost_id:15} {pod_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.name}: {p.ghost} in {p.place} with {p.pod} "
                f"({outcome_of(p)}, courage={p.courage}, repeats={p.repeats})"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
