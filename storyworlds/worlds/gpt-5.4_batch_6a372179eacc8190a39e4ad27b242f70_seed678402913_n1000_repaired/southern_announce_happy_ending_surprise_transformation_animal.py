#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py
=============================================================================================

A standalone story world for gentle animal stories set in southern places, where
a small creature is asked to announce an important moment, worries because its
baby body is not ready yet, and then surprises everyone by transforming at just
the right time.

The core constraint is simple and child-sized:

* the event needs a certain kind of signal: a loud voice, wings to carry news,
  or a glow in the dark
* the species must transform into a form that truly gives that signal
* the southern habitat must be a place where that kind of announcement makes sense

Only those combinations are allowed. The story itself is driven by a small world
model with physical meters (changing, transformed, announced) and emotional
memes (worry, hope, pride, joy).

Run it
------
    python storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py
    python storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py --species tadpole --event rain_song
    python storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py --species caterpillar --event rain_song
    python storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py --all
    python storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py --qa
    python storyworlds/worlds/gpt-5.4/southern_announce_happy_ending_surprise_transformation_animal.py --verify
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


def _add_storyworlds_to_path() -> None:
    here = os.path.abspath(__file__)
    cur = os.path.dirname(here)
    while True:
        candidate = os.path.join(cur, "results.py")
        if os.path.exists(candidate):
            sys.path.insert(0, cur)
            return
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    raise RuntimeError("Could not find storyworlds/results.py from script location.")


_add_storyworlds_to_path()
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "doe", "ladybug"}
        male = {"boy", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Habitat:
    id: str
    place: str
    scene: str
    supports: set[str] = field(default_factory=set)
    helper_name: str = ""
    helper_type: str = ""
    elder_name: str = ""
    elder_type: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Species:
    id: str
    baby_kind: str
    adult_kind: str
    baby_noun: str
    adult_noun: str
    gain_mode: str
    home_detail: str
    worry_line: str
    change_line: str
    surprise_line: str
    announce_verb: str
    announce_style: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    title: str
    need_mode: str
    cue: str
    ask_line: str
    fail_line: str
    success_line: str
    crowd_line: str
    ending_line: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _has_mode(ent: Entity, mode: str) -> bool:
    return ent.meters[f"mode_{mode}"] >= THRESHOLD


def _r_worry(world: World) -> list[str]:
    child = world.entities.get("child")
    event = world.facts.get("event_cfg")
    if child is None or event is None:
        return []
    if child.meters["chosen"] < THRESHOLD:
        return []
    if _has_mode(child, event.need_mode):
        return []
    sig = ("worry", child.id, event.need_mode)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["longing"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    child = world.entities.get("child")
    species = world.facts.get("species_cfg")
    if child is None or species is None:
        return []
    if child.meters["changing"] < THRESHOLD or child.meters["transformed"] >= THRESHOLD:
        return []
    sig = ("transform", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["transformed"] += 1
    child.meters[f"mode_{species.gain_mode}"] += 1
    child.memes["hope"] += 1
    child.memes["wonder"] += 1
    child.memes["worry"] = 0.0
    return []


def _r_ready(world: World) -> list[str]:
    child = world.entities.get("child")
    event = world.facts.get("event_cfg")
    if child is None or event is None:
        return []
    if child.meters["transformed"] < THRESHOLD or not _has_mode(child, event.need_mode):
        return []
    sig = ("ready", child.id, event.need_mode)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pride"] += 1
    child.memes["confidence"] += 1
    return []


def _r_celebrate(world: World) -> list[str]:
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    elder = world.entities.get("elder")
    if child is None or child.meters["announced"] < THRESHOLD:
        return []
    sig = ("celebrate", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["joy"] += 1
    if helper is not None:
        helper.memes["joy"] += 1
    if elder is not None:
        elder.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="transform", tag="body", apply=_r_transform),
    Rule(name="ready", tag="emotion", apply=_r_ready),
    Rule(name="celebrate", tag="social", apply=_r_celebrate),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                # state may still have changed in silent rules
                changed = changed or False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


HABITATS = {
    "marsh": Habitat(
        id="marsh",
        place="the southern marsh",
        scene="Warm reeds leaned over the water, and the air smelled green and sweet.",
        supports={"voice", "light"},
        helper_name="Junebug",
        helper_type="cricket",
        elder_name="Aunt Heron",
        elder_type="heron",
        tags={"marsh", "southern"},
    ),
    "garden": Habitat(
        id="garden",
        place="the southern garden",
        scene="Magnolia petals rested on the paths, and the tomato vines climbed their strings.",
        supports={"flight", "light"},
        helper_name="Clover",
        helper_type="rabbit",
        elder_name="Miss Wren",
        elder_type="wren",
        tags={"garden", "southern"},
    ),
    "pond": Habitat(
        id="pond",
        place="the southern pond",
        scene="Round lily pads floated near the bank, and sleepy turtles blinked in the sun.",
        supports={"voice"},
        helper_name="Pebble",
        helper_type="duck",
        elder_name="Old Otter",
        elder_type="otter",
        tags={"pond", "southern"},
    ),
    "grove": Habitat(
        id="grove",
        place="the southern grove",
        scene="Live oaks held up long arms of shade, and wildflowers nodded in the grass.",
        supports={"flight"},
        helper_name="Thimble",
        helper_type="mouse",
        elder_name="Grandma Finch",
        elder_type="finch",
        tags={"grove", "southern"},
    ),
}

SPECIES = {
    "tadpole": Species(
        id="tadpole",
        baby_kind="tadpole",
        adult_kind="frog",
        baby_noun="little tadpole",
        adult_noun="young frog",
        gain_mode="voice",
        home_detail="Pip liked to flick his tail under the water and listen to the reeds whisper overhead.",
        worry_line="He opened his mouth, but only a tiny watery peep came out.",
        change_line="His tail grew smaller, and four springy legs pushed out with a soft, wiggly pop.",
        surprise_line='Pip blinked. "I changed!" he gasped.',
        announce_verb="croaked",
        announce_style="in a clear marshy voice",
        ending_image="He sat on a lily pad, round-eyed and proud, while ripples twinkled around him.",
        tags={"frog", "voice", "transformation"},
    ),
    "caterpillar": Species(
        id="caterpillar",
        baby_kind="caterpillar",
        adult_kind="butterfly",
        baby_noun="striped caterpillar",
        adult_noun="bright butterfly",
        gain_mode="flight",
        home_detail="Mimi loved inching along the leaves and feeling the warm breeze brush her fuzzy back.",
        worry_line="She stretched up as high as she could, but the news would never reach the far flowers from one leaf.",
        change_line="Her snug little shell split, and two soft wings opened wider and wider in the light.",
        surprise_line='Mimi stared at the colors on her own back. "Oh! I can fly!" she said.',
        announce_verb="called",
        announce_style="while fluttering above the blossoms",
        ending_image="She drifted over the flowers like a petal that had learned how to dance.",
        tags={"butterfly", "wings", "transformation"},
    ),
    "firefly": Species(
        id="firefly",
        baby_kind="glow grub",
        adult_kind="firefly",
        baby_noun="small glow grub",
        adult_noun="firefly",
        gain_mode="light",
        home_detail="Dot liked to nose through the grass roots where the day felt cool and secret.",
        worry_line="The dusk was coming, but his tiny baby shine was too faint to lead anyone.",
        change_line="His back grew smooth wing-cases, and a bright lantern-light woke up inside his tail.",
        surprise_line='Dot spun in a happy circle. "I am shining for real!" he cried.',
        announce_verb="glowed",
        announce_style="with a merry green light",
        ending_image="He floated above the grass like a tiny star that had come down to play.",
        tags={"firefly", "glow", "transformation"},
    ),
}

EVENTS = {
    "rain_song": Event(
        id="rain_song",
        title="the first warm rain song",
        need_mode="voice",
        cue="when the first warm drops began tapping the leaves",
        ask_line='"{name}, when the rain begins, will you announce the first warm rain song for all of us?"',
        fail_line="The job needed a strong call that could skip across the water and reeds.",
        success_line='"{line}" {name} {verb} {style}.',
        crowd_line="At once, the marsh neighbors lifted their heads and joined in.",
        ending_line="Soon the whole water edge was singing together under the rain.",
        tags={"rain", "announce", "voice"},
    ),
    "blossom_breakfast": Event(
        id="blossom_breakfast",
        title="the magnolia blossom breakfast",
        need_mode="flight",
        cue="when the magnolia blossoms opened all at once at dawn",
        ask_line='"{name}, when the blossoms open, will you announce breakfast to the far beds and the high branches?"',
        fail_line="The job needed quick wings to carry the news from flower to flower.",
        success_line='"{line}" {name} {verb} {style}.',
        crowd_line="Bees hummed up from the clover, and birds dipped down from the branches.",
        ending_line="In a moment, the garden was busy with happy breakfast visitors.",
        tags={"blossom", "announce", "flight"},
    ),
    "lantern_dance": Event(
        id="lantern_dance",
        title="the evening lantern dance",
        need_mode="light",
        cue="when the sky turned purple and the grass went soft and dark",
        ask_line='"{name}, when night comes, will you announce the lantern dance so no one misses the first twirl?"',
        fail_line="The job needed a bright glow that could be seen all across the dusk.",
        success_line='"{line}" {name} {verb} {style}.',
        crowd_line="One by one, little faces turned toward the shining call.",
        ending_line="Soon the dark was full of looping lights and gentle laughter.",
        tags={"night", "announce", "light"},
    ),
}


@dataclass
class StoryParams:
    habitat: str
    species: str
    event: str
    child_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        habitat="marsh",
        species="tadpole",
        event="rain_song",
        child_name="Pip",
    ),
    StoryParams(
        habitat="pond",
        species="tadpole",
        event="rain_song",
        child_name="Nip",
    ),
    StoryParams(
        habitat="garden",
        species="caterpillar",
        event="blossom_breakfast",
        child_name="Mimi",
    ),
    StoryParams(
        habitat="grove",
        species="caterpillar",
        event="blossom_breakfast",
        child_name="Tansy",
    ),
    StoryParams(
        habitat="garden",
        species="firefly",
        event="lantern_dance",
        child_name="Dot",
    ),
    StoryParams(
        habitat="marsh",
        species="firefly",
        event="lantern_dance",
        child_name="Glim",
    ),
]


NAME_POOL = {
    "tadpole": ["Pip", "Nip", "Bloop", "Tad", "Ripple", "Moss"],
    "caterpillar": ["Mimi", "Tansy", "Clover", "Velvet", "Pea", "Sunny"],
    "firefly": ["Dot", "Glim", "Spark", "Nico", "Blink", "Pico"],
}


def valid_combo(habitat_id: str, species_id: str, event_id: str) -> bool:
    habitat = HABITATS[habitat_id]
    species = SPECIES[species_id]
    event = EVENTS[event_id]
    return species.gain_mode == event.need_mode and event.need_mode in habitat.supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for habitat_id in sorted(HABITATS):
        for species_id in sorted(SPECIES):
            for event_id in sorted(EVENTS):
                if valid_combo(habitat_id, species_id, event_id):
                    combos.append((habitat_id, species_id, event_id))
    return combos


def explain_rejection(habitat_id: str, species_id: str, event_id: str) -> str:
    habitat = HABITATS[habitat_id]
    species = SPECIES[species_id]
    event = EVENTS[event_id]
    if species.gain_mode != event.need_mode:
        return (
            f"(No story: a {species.baby_kind} turns into a {species.adult_kind} that helps by "
            f"{species.gain_mode}, but {event.title} needs {event.need_mode}. "
            f"The transformation must honestly solve the announcing problem.)"
        )
    return (
        f"(No story: {habitat.place} does not support an announcement by {event.need_mode}. "
        f"Pick a southern place where that kind of signal would make sense.)"
    )


def announce_line_for(species: Species, event: Event) -> str:
    if event.id == "rain_song":
        return "The rain is here! Sing, everyone, sing!"
    if event.id == "blossom_breakfast":
        return "The blossoms are open! Breakfast is ready!"
    if event.id == "lantern_dance":
        return "The lantern dance is starting! Come twirl with me!"
    return "Come, everyone!"


def predict_ready(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["changing"] += 1
    propagate(sim, narrate=False)
    event = sim.facts["event_cfg"]
    return {
        "transformed": child.meters["transformed"] >= THRESHOLD,
        "can_announce": _has_mode(child, event.need_mode),
    }


def introduce(world: World, child: Entity, habitat: Habitat, species: Species) -> None:
    world.say(f"In {habitat.place}, there lived a {species.baby_noun} named {child.id}.")
    world.say(habitat.scene)
    world.say(species.home_detail)


def gather(world: World, elder: Entity, child: Entity, event: Event) -> None:
    child.meters["chosen"] += 1
    world.say(
        f"One bright morning, {elder.id} called the neighbors close and looked kindly at {child.id}."
    )
    world.say(event.ask_line.format(name=child.id))
    propagate(world, narrate=False)


def worry(world: World, child: Entity, species: Species, event: Event) -> None:
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id}'s heart gave a tiny thump. {species.worry_line} {event.fail_line}"
        )


def comfort(world: World, helper: Entity, child: Entity, habitat: Habitat) -> None:
    pred = predict_ready(world)
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    if pred["transformed"] and pred["can_announce"]:
        world.say(
            f'{helper.id} came close and brushed against {child.id}. '
            f'"Wait and see," {helper.pronoun()} said. "Bodies in {habitat.place} know their own good time."'
        )
    else:
        world.say(
            f'{helper.id} stayed beside {child.id}. "I will be with you," {helper.pronoun()} said gently.'
        )


def cue_arrives(world: World, event: Event) -> None:
    world.say(f"Then the great moment came, {event.cue}.")
    child = world.get("child")
    child.meters["changing"] += 1
    propagate(world, narrate=False)


def transform(world: World, child: Entity, species: Species) -> None:
    if child.meters["transformed"] >= THRESHOLD:
        child.type = species.adult_kind
        child.label = species.adult_noun
        world.say(species.change_line)
        world.say(species.surprise_line)


def announce(world: World, child: Entity, species: Species, event: Event) -> None:
    if not _has_mode(child, event.need_mode):
        raise StoryError("The child never gained the right announcing ability.")
    line = announce_line_for(species, event)
    world.say(
        event.success_line.format(
            line=line,
            name=child.id,
            verb=species.announce_verb,
            style=species.announce_style,
        )
    )
    child.meters["announced"] += 1
    propagate(world, narrate=False)


def ending(world: World, child: Entity, helper: Entity, elder: Entity, event: Event, species: Species) -> None:
    world.say(event.crowd_line)
    world.say(
        f"{elder.id} smiled so wide that even {helper.id} laughed with relief."
    )
    world.say(event.ending_line)
    world.say(species.ending_image)


def tell(habitat: Habitat, species: Species, event: Event, child_name: str) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=species.baby_kind,
            label=species.baby_noun,
            role="child",
            tags=set(species.tags),
        )
    )
    helper = world.add(
        Entity(
            id=habitat.helper_name,
            kind="character",
            type=habitat.helper_type,
            label=habitat.helper_type,
            role="helper",
            tags=set(habitat.tags),
        )
    )
    elder = world.add(
        Entity(
            id=habitat.elder_name,
            kind="character",
            type=habitat.elder_type,
            label=habitat.elder_type,
            role="elder",
            tags=set(habitat.tags),
        )
    )

    world.facts.update(
        habitat_cfg=habitat,
        species_cfg=species,
        event_cfg=event,
        child=child,
        helper=helper,
        elder=elder,
    )

    introduce(world, child, habitat, species)

    world.para()
    gather(world, elder, child, event)
    worry(world, child, species, event)
    comfort(world, helper, child, habitat)

    world.para()
    cue_arrives(world, event)
    transform(world, child, species)
    announce(world, child, species, event)

    world.para()
    ending(world, child, helper, elder, event, species)

    world.facts.update(
        transformed=child.meters["transformed"] >= THRESHOLD,
        announced=child.meters["announced"] >= THRESHOLD,
        happy=child.memes["joy"] >= THRESHOLD or child.meters["announced"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "southern": [
        (
            "What does southern mean?",
            "Southern means from the south, or in the south part of a place. People also use it for warm southern places with long summers.",
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is a wet place with shallow water and lots of reeds and grass. Many frogs, birds, and bugs live there.",
        )
    ],
    "pond": [
        (
            "What is a pond?",
            "A pond is a small still body of water. It can have lily pads, fish, frogs, and turtles.",
        )
    ],
    "garden": [
        (
            "What is a garden?",
            "A garden is a place where flowers, fruits, or vegetables are grown. It gives little animals food, shade, and hiding spots.",
        )
    ],
    "grove": [
        (
            "What is a grove?",
            "A grove is a small group of trees growing close together. It makes a cool, shady place for animals to rest.",
        )
    ],
    "frog": [
        (
            "How is a frog different from a tadpole?",
            "A tadpole starts out with a tail and lives in water. As it grows into a frog, it gets legs and can make a louder croak.",
        )
    ],
    "butterfly": [
        (
            "How does a caterpillar become a butterfly?",
            "A caterpillar changes inside a covering and comes out with wings. That big body change is called a transformation.",
        )
    ],
    "firefly": [
        (
            "Why do fireflies glow?",
            "Fireflies make light in their bodies. They glow to signal to one another in the dark.",
        )
    ],
    "voice": [
        (
            "Why can a loud voice help animals announce something?",
            "A loud voice can travel across water, grass, or trees. That lets many neighbors hear the news at once.",
        )
    ],
    "wings": [
        (
            "Why do wings help carry news?",
            "Wings let an animal move quickly from place to place. That means the animal can share a message far away.",
        )
    ],
    "glow": [
        (
            "How can light be a message?",
            "A bright light can tell others where to look or when to come. In the dark, a glow can be as clear as a call.",
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a big change from one form into another. In stories and in nature, that change can bring new abilities.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "southern",
    "marsh",
    "pond",
    "garden",
    "grove",
    "frog",
    "butterfly",
    "firefly",
    "voice",
    "wings",
    "glow",
    "transformation",
]


def generation_prompts(world: World) -> list[str]:
    habitat = world.facts["habitat_cfg"]
    species = world.facts["species_cfg"]
    event = world.facts["event_cfg"]
    child = world.facts["child"]
    return [
        (
            f'Write a gentle animal story for a 3-to-5-year-old set in {habitat.place} '
            f'where a small {species.baby_kind} is asked to announce {event.title}. '
            f'Include the word "announce".'
        ),
        (
            f"Tell a happy story in which {child.id}, a {species.baby_kind}, worries about being too small, "
            f"then surprises everyone by transforming into a {species.adult_kind} at just the right moment."
        ),
        (
            f'Write a southern animal story with a surprise transformation and a warm ending, '
            f'where the new body honestly helps the child announce good news.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    habitat = world.facts["habitat_cfg"]
    species = world.facts["species_cfg"]
    event = world.facts["event_cfg"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    elder = world.facts["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a {species.baby_kind} living in {habitat.place}. {helper.id} and {elder.id} are important too because they support {child.id}.",
        ),
        (
            f"What did {elder.id} ask {child.id} to do?",
            f"{elder.id} asked {child.id} to announce {event.title}. That job mattered because all the neighbors were waiting for the sign to begin.",
        ),
        (
            f"Why was {child.id} worried at first?",
            f"{child.id} was still in a baby body and did not yet have the right way to announce the news. {event.fail_line}",
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} stayed close and gave {child.id} hope instead of laughing. That comfort helped {child.id} wait for the right moment.",
        ),
    ]
    if world.facts.get("transformed"):
        qa.append(
            (
                f"What surprise happened when the moment came?",
                f"{child.id} transformed from a {species.baby_kind} into a {species.adult_kind}. The change was a surprise, and it gave {child.pronoun('object')} the exact ability needed for the job.",
            )
        )
    if world.facts.get("announced"):
        qa.append(
            (
                f"How did {child.id} finally announce the news?",
                f"{child.id} used {species.gain_mode} to share the message with everyone. Because the transformation matched the job, the whole neighborhood could understand the call at once.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the neighbors gathering after {child.id}'s announcement. The ending feels joyful because the very thing that had worried {child.id} turned into a new strength.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    habitat = world.facts["habitat_cfg"]
    species = world.facts["species_cfg"]
    event = world.facts["event_cfg"]
    tags = {"southern", "transformation"} | set(habitat.tags) | set(species.tags) | set(event.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, S, E) :- habitat(H), species(S), event(E),
                  gain_mode(S, M), need_mode(E, M), supports(H, M).

happy(H, S, E) :- valid(H, S, E).
outcome(H, S, E, happy) :- happy(H, S, E).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for habitat_id, habitat in HABITATS.items():
        lines.append(asp.fact("habitat", habitat_id))
        for mode in sorted(habitat.supports):
            lines.append(asp.fact("supports", habitat_id, mode))
    for species_id, species in SPECIES.items():
        lines.append(asp.fact("species", species_id))
        lines.append(asp.fact("gain_mode", species_id, species.gain_mode))
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        lines.append(asp.fact("need_mode", event_id, event.need_mode))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_habitat", params.habitat),
            asp.fact("chosen_species", params.species),
            asp.fact("chosen_event", params.event),
            "selected_happy :- valid(H, S, E), chosen_habitat(H), chosen_species(S), chosen_event(E).",
            "selected_outcome(happy) :- selected_happy.",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Southern animal story world: a small creature is asked to announce good news and transforms just in time."
    )
    ap.add_argument("--habitat", choices=sorted(HABITATS))
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--child-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the inline ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the complete ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.habitat and args.species and args.event:
        if not valid_combo(args.habitat, args.species, args.event):
            raise StoryError(explain_rejection(args.habitat, args.species, args.event))

    combos = [
        combo
        for combo in valid_combos()
        if (args.habitat is None or combo[0] == args.habitat)
        and (args.species is None or combo[1] == args.species)
        and (args.event is None or combo[2] == args.event)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    habitat_id, species_id, event_id = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(NAME_POOL[species_id])
    return StoryParams(
        habitat=habitat_id,
        species=species_id,
        event=event_id,
        child_name=child_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.habitat not in HABITATS:
        raise StoryError(f"Unknown habitat: {params.habitat}")
    if params.species not in SPECIES:
        raise StoryError(f"Unknown species: {params.species}")
    if params.event not in EVENTS:
        raise StoryError(f"Unknown event: {params.event}")
    if not valid_combo(params.habitat, params.species, params.event):
        raise StoryError(explain_rejection(params.habitat, params.species, params.event))

    world = tell(
        habitat=HABITATS[params.habitat],
        species=SPECIES[params.species],
        event=EVENTS[params.event],
        child_name=params.child_name,
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
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py - clingo:
            print("  only in python:", sorted(py - clingo))
        if clingo - py:
            print("  only in clingo:", sorted(clingo - py))

    for params in CURATED:
        py_outcome = "happy" if valid_combo(params.habitat, params.species, params.event) else "invalid"
        asp_result = asp_outcome(params)
        if py_outcome != asp_result:
            rc = 1
            print(
                f"MISMATCH outcome for {params.habitat}/{params.species}/{params.event}: "
                f"python={py_outcome} asp={asp_result}"
            )

    try:
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        args = build_parser().parse_args([])
        random_params = resolve_params(args, random.Random(123))
        random_params.seed = 123
        generate(random_params)
        print("OK: generation and emit smoke tests passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (habitat, species, event) combos:\n")
        for habitat_id, species_id, event_id in combos:
            print(f"  {habitat_id:8} {species_id:11} {event_id}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.species} in {p.habitat} announcing {p.event}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
