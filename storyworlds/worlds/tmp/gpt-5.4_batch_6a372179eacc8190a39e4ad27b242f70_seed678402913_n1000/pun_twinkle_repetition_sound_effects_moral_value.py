#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py
================================================================================

A standalone storyworld for a heartwarming "pun + twinkle" tale.

Tiny domain
-----------
At dusk, a child sees fireflies and wants to carry their twinkle home in a jar.
A caring helper notices that the jar makes the little insects tired and trapped.
Together they choose a kinder way to keep the evening bright: let the fireflies
go and use a safe glowing object instead. The story ends with free twinkles and
a gentle moral about kindness.

Why this domain
---------------
The seed asked for:
- the words "pun" and "twinkle"
- repetition
- sound effects
- moral value
- a heartwarming style

This world models those directly:
- The prose repeats bright little phrases such as "twinkle, twinkle".
- Sound effects come from jars, lids, grass, and tiny wings: "clink", "whoosh",
  "bzz".
- A helper can make a gentle pun about light or bugs.
- The moral comes from simulated state: trapped fireflies grow tired, released
  fireflies glow freely, and the children feel relief and kindness.

Run it
------
    python storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py
    python storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py --place garden --goal room
    python storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py --container shoebox
    python storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py --qa --json
    python storyworlds/worlds/gpt-5.4/pun_twinkle_repetition_sound_effects_moral_value.py --verify
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

# Make shared result containers importable when this nested script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing" | "group"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    container_open: bool = False
    transparent: bool = False
    has_air_holes: bool = False
    glows: bool = False
    living: bool = False
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "grandmother"}
        male = {"boy", "father", "dad", "man", "brother", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural or self.kind == "group":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural or self.kind == "group" else "it"

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    ground: str
    sky: str
    supports_fireflies: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    wish: str
    line: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    transparent: bool
    has_air_holes: bool
    kind_tags: set[str] = field(default_factory=set)


@dataclass
class SafeGlow:
    id: str
    label: str
    phrase: str
    action: str
    glow_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperStyle:
    id: str
    helper_type: str
    intro: str
    pun_line: str
    comfort_line: str
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


def _r_trapped_fireflies(world: World) -> list[str]:
    out: list[str] = []
    flies = world.get("fireflies")
    box = world.get("container")
    if flies.meters["in_container"] < THRESHOLD:
        return out
    sig = ("trapped", box.id, box.container_open, box.transparent, box.has_air_holes)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    flies.meters["freedom"] = 0.0
    if not box.container_open:
        flies.meters["tired"] += 1
        flies.meters["buzz"] += 1
        flies.memes["uneasy"] += 1
        out.append("__trapped__")
    else:
        flies.meters["buzz"] += 0.5
    return out


def _r_release(world: World) -> list[str]:
    out: list[str] = []
    flies = world.get("fireflies")
    if flies.meters["released"] < THRESHOLD:
        return out
    sig = ("released",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    flies.meters["in_container"] = 0.0
    flies.meters["freedom"] += 1
    flies.meters["tired"] = 0.0
    flies.memes["uneasy"] = 0.0
    flies.meters["twinkle"] += 1
    for ent in world.entities.values():
        if ent.role in {"hero", "helper"}:
            ent.memes["relief"] += 1
            ent.memes["kindness"] += 1
    out.append("__free__")
    return out


def _r_safe_glow(world: World) -> list[str]:
    out: list[str] = []
    glow = world.get("safe_glow")
    if glow.meters["on"] < THRESHOLD:
        return out
    sig = ("safe_glow", glow.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    glow.meters["twinkle"] += 1
    for ent in world.entities.values():
        if ent.role in {"hero", "helper"}:
            ent.memes["joy"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule(name="trapped_fireflies", tag="physical", apply=_r_trapped_fireflies),
    Rule(name="release", tag="physical", apply=_r_release),
    Rule(name="safe_glow", tag="physical", apply=_r_safe_glow),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__trapped__":
                flies = world.get("fireflies")
                if flies.meters["tired"] >= THRESHOLD:
                    world.say('Inside the container came a tiny "bzz, bzz" that no longer sounded happy.')
            elif bit == "__free__":
                world.say('Out they floated -- whoosh, whoosh -- and soon the dusk was full of twinkle, twinkle again.')
            elif bit == "__safe__":
                world.say("The safe little light began to glow with a warm, steady twinkle.")
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="garden",
        phrase="the garden behind the house",
        ground="the soft garden path",
        sky="the evening sky above the beans and roses",
        supports_fireflies=True,
        tags={"garden", "night"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the front porch with the wooden steps",
        ground="the porch boards",
        sky="the dusk above the railings",
        supports_fireflies=True,
        tags={"porch", "night"},
    ),
    "meadow": Place(
        id="meadow",
        label="meadow",
        phrase="the little meadow near the fence",
        ground="the grass by the fence",
        sky="the wide purple sky",
        supports_fireflies=True,
        tags={"meadow", "night"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="kitchen",
        phrase="the bright kitchen by the sink",
        ground="the kitchen floor",
        sky="the ceiling light",
        supports_fireflies=False,
        tags={"indoor"},
    ),
}

GOALS = {
    "room": Goal(
        id="room",
        wish="make the bedroom twinkle",
        line='“I wish I could carry this twinkle to my room,”',
        ending="That night the room felt bright, but the happiest twinkle was the one still dancing outside the window.",
        tags={"room"},
    ),
    "fort": Goal(
        id="fort",
        wish="make the blanket fort twinkle",
        line='“I wish I could tuck this twinkle into our fort,”',
        ending="The fort glowed softly, and the free fireflies blinked outside like tiny neighbors saying good night.",
        tags={"fort"},
    ),
    "picnic": Goal(
        id="picnic",
        wish="make the picnic cloth twinkle",
        line='“I wish I could keep this twinkle by our picnic,”',
        ending="Their picnic looked cozy, and the meadow kept its own bright little lanterns too.",
        tags={"picnic"},
    ),
}

CONTAINERS = {
    "jar": Container(
        id="jar",
        label="jar",
        phrase="a clear glass jar",
        transparent=True,
        has_air_holes=True,
        kind_tags={"jar", "see_through"},
    ),
    "lantern_jar": Container(
        id="lantern_jar",
        label="lantern jar",
        phrase="a little lantern jar with shiny stars painted on it",
        transparent=True,
        has_air_holes=True,
        kind_tags={"jar", "see_through"},
    ),
    "shoebox": Container(
        id="shoebox",
        label="shoebox",
        phrase="an old shoebox",
        transparent=False,
        has_air_holes=False,
        kind_tags={"box", "closed"},
    ),
}

SAFE_GLOWS = {
    "string_lights": SafeGlow(
        id="string_lights",
        label="string lights",
        phrase="a string of tiny lights",
        action="hung the tiny lights along the edge",
        glow_line="Each bulb gave a friendly little blink.",
        tags={"lights", "electric"},
    ),
    "star_lamp": SafeGlow(
        id="star_lamp",
        label="star lamp",
        phrase="a star-shaped lamp",
        action="set the little lamp by the pillow",
        glow_line="It sprinkled soft stars over the wall.",
        tags={"lamp", "stars"},
    ),
    "paper_lantern": SafeGlow(
        id="paper_lantern",
        label="paper lantern",
        phrase="a paper lantern with a safe battery candle",
        action="placed the lantern in the middle",
        glow_line="Its gentle light made everything look golden and calm.",
        tags={"lantern", "battery"},
    ),
}

HELPERS = {
    "mom": HelperStyle(
        id="mom",
        helper_type="mother",
        intro="Mom was beside the child on the path, listening to the evening insects wake up.",
        pun_line='Mom gave a soft smile. “Here is my tiny pun: a bright idea should also be a kind idea.”',
        comfort_line="Mom rubbed the child's shoulder and kept her voice warm and calm.",
        tags={"parent", "pun"},
    ),
    "dad": HelperStyle(
        id="dad",
        helper_type="father",
        intro="Dad stood nearby with his hands in his pockets, watching the evening settle down.",
        pun_line='Dad chuckled gently. “Here is a little pun: let us not bug the bugs.”',
        comfort_line="Dad knelt down so the child could see his kind eyes.",
        tags={"parent", "pun", "bug"},
    ),
    "grandma": HelperStyle(
        id="grandma",
        helper_type="grandmother",
        intro="Grandma walked slowly along the path, smiling at every small light in the grass.",
        pun_line='Grandma whispered, “A tiny pun for a tiny light: kindness helps every good idea glow.”',
        comfort_line="Grandma patted the child's hand and spoke as softly as the evening breeze.",
        tags={"grandparent", "pun"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]
TRAITS = ["gentle", "curious", "bright-eyed", "hopeful", "playful", "kind"]


def place_has_fireflies(place: Place) -> bool:
    return place.supports_fireflies


def humane_container(container: Container) -> bool:
    return container.transparent and container.has_air_holes


def compatible_glow(goal: Goal, glow: SafeGlow) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        if not place_has_fireflies(place):
            continue
        for goal_id, goal in GOALS.items():
            for container_id, container in CONTAINERS.items():
                if not humane_container(container):
                    continue
                for glow_id, glow in SAFE_GLOWS.items():
                    if compatible_glow(goal, glow):
                        combos.append((place_id, goal_id, container_id, glow_id))
    return combos


@dataclass
class StoryParams:
    place: str
    goal: str
    container: str
    safe_glow: str
    helper: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        goal="room",
        container="jar",
        safe_glow="star_lamp",
        helper="mom",
        child_name="Lily",
        child_gender="girl",
        trait="gentle",
    ),
    StoryParams(
        place="porch",
        goal="fort",
        container="lantern_jar",
        safe_glow="string_lights",
        helper="dad",
        child_name="Ben",
        child_gender="boy",
        trait="curious",
    ),
    StoryParams(
        place="meadow",
        goal="picnic",
        container="jar",
        safe_glow="paper_lantern",
        helper="grandma",
        child_name="Maya",
        child_gender="girl",
        trait="hopeful",
    ),
]


def explain_rejection(place: Optional[Place] = None, container: Optional[Container] = None) -> str:
    if place is not None and not place.supports_fireflies:
        return (
            f"(No story: {place.phrase} is too bright and indoor for fireflies, "
            "so there is no honest twinkle to notice there. Pick an evening outdoor place.)"
        )
    if container is not None and not humane_container(container):
        return (
            f"(No story: {container.phrase} is not a kind first catch here. "
            "The world only allows see-through containers with air holes, so the child can notice the fireflies' needs and let them go.)"
        )
    return "(No valid combination matches the given options.)"


def predict_capture(world: World) -> dict:
    sim = world.copy()
    flies = sim.get("fireflies")
    flies.meters["in_container"] += 1
    propagate(sim, narrate=False)
    return {
        "tired": flies.meters["tired"],
        "uneasy": flies.memes["uneasy"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"One warm evening, {child.id} and {helper.label_word} walked to {place.phrase}. "
        f"{place.ground.capitalize()} felt cool under their shoes, and {place.sky} was turning blue-purple."
    )
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} who noticed small lovely things."
    )
    world.say(HELPERS[world.facts["helper_cfg"].id].intro)


def first_twinkle(world: World, child: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    flies = world.get("fireflies")
    flies.meters["twinkle"] += 1
    world.say(
        f"Then a tiny light blinked near the grass. Twinkle, twinkle -- there it was. "
        f"Then another answered from the dark, twinkle, twinkle, all across {place.label}."
    )
    world.say(
        f'"Oh!" said {child.id}. "The whole place looks as if the night learned how to smile."'
    )


def wish_for_light(world: World, child: Entity, goal: Goal, container: Container) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{goal.line} {child.id} whispered. {child.pronoun('subject').capitalize()} held up {container.phrase} with a tiny hopeful clink-clink."
    )
    world.say(
        f"{child.id} wanted to {goal.wish}, just for a little while."
    )


def catch_fireflies(world: World, child: Entity, container: Entity) -> None:
    flies = world.get("fireflies")
    child.memes["joy"] += 1
    flies.meters["in_container"] += 1
    world.say(
        f"Very carefully, {child.id} cupped the glowing little bugs and tipped them into {container.phrase}. "
        'Clink went the lid. Bzz, bzz went the tiny wings.'
    )
    propagate(world, narrate=True)


def notice_problem(world: World, child: Entity, helper: Entity, container_cfg: Container) -> None:
    pred = predict_capture(world)
    child.memes["concern"] += 1
    helper.memes["care"] += 1
    world.facts["predicted_tired"] = pred["tired"]
    helper_cfg = world.facts["helper_cfg"]
    world.say(helper_cfg.comfort_line)
    if pred["tired"] >= THRESHOLD:
        world.say(
            f'"Listen," {helper.label_word} said. "They do not sound bright anymore. '
            f'Inside {container_cfg.label}, their little bzz sounds tired."'
        )
    else:
        world.say(
            f'"Listen," {helper.label_word} said. "They are safer when the sky is their roof."'
        )
    world.say(helper_cfg.pun_line)


def choose_kindness(world: World, child: Entity, helper: Entity) -> None:
    child.memes["empathy"] += 1
    child.memes["greed"] = 0.0
    world.say(
        f'{child.id} looked at the small lights, then at {helper.label_word}. '
        f'"I wanted their twinkle," {child.pronoun()} said, "but I do not want them to feel trapped."'
    )
    world.say(
        f'"Twinkle outside, twinkle free," {helper.label_word} said. "That is the kinder song."'
    )


def release_fireflies(world: World, child: Entity, container: Entity) -> None:
    container.container_open = True
    flies = world.get("fireflies")
    flies.meters["released"] += 1
    world.say(
        f"{child.id} lifted the lid. Pop. Up opened the container."
    )
    propagate(world, narrate=True)


def bring_safe_glow(world: World, child: Entity, helper: Entity, goal: Goal, glow_cfg: SafeGlow) -> None:
    glow = world.get("safe_glow")
    glow.meters["on"] += 1
    world.say(
        f"Back at home, {helper.label_word} found {glow_cfg.phrase}, and together they {glow_cfg.action}."
    )
    propagate(world, narrate=True)
    world.say(glow_cfg.glow_line)
    world.say(
        f"{child.id} smiled. 'This can twinkle here, and the fireflies can twinkle there.'"
    )
    world.say(goal.ending)


def tell(place: Place, goal: Goal, container_cfg: Container, glow_cfg: SafeGlow,
         helper_cfg: HelperStyle, child_name: str, child_gender: str, trait: str) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="hero",
            traits=[trait],
            label=child_name,
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.helper_type,
            role="helper",
            label="the helper",
        )
    )
    container = world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label=container_cfg.label,
            phrase=container_cfg.phrase,
            transparent=container_cfg.transparent,
            has_air_holes=container_cfg.has_air_holes,
            container_open=False,
            tags=set(container_cfg.kind_tags),
        )
    )
    fireflies = world.add(
        Entity(
            id="fireflies",
            kind="group",
            type="firefly",
            label="fireflies",
            phrase="the little fireflies",
            living=True,
            glows=True,
            plural=True,
            tags={"fireflies", "night"},
        )
    )
    safe_glow = world.add(
        Entity(
            id="safe_glow",
            kind="thing",
            type="light",
            label=glow_cfg.label,
            phrase=glow_cfg.phrase,
            glows=True,
            tags=set(glow_cfg.tags),
        )
    )

    world.facts.update(
        place=place,
        goal=goal,
        helper_cfg=helper_cfg,
        container_cfg=container_cfg,
        glow_cfg=glow_cfg,
        child=child,
        helper=helper,
        container=container,
        fireflies=fireflies,
        safe_glow=safe_glow,
    )

    introduce(world, child, helper, place)
    first_twinkle(world, child, place)

    world.para()
    wish_for_light(world, child, goal, container_cfg)
    catch_fireflies(world, child, container)
    notice_problem(world, child, helper, container_cfg)

    world.para()
    choose_kindness(world, child, helper)
    release_fireflies(world, child, container)

    world.para()
    bring_safe_glow(world, child, helper, goal, glow_cfg)

    world.facts.update(
        released=fireflies.meters["released"] >= THRESHOLD,
        trapped_before_release=True,
        moral="Kindness means enjoying beauty without taking freedom away.",
    )
    return world


KNOWLEDGE = {
    "fireflies": [
        (
            "What are fireflies?",
            "Fireflies are tiny insects that can make light with their bodies. Their glow helps them signal to one another on warm evenings."
        )
    ],
    "night": [
        (
            "Why do fireflies look brighter at dusk?",
            "They look brighter at dusk because the sky is darker then. Small lights are easier to notice when the daylight fades."
        )
    ],
    "jar": [
        (
            "Why should people be gentle with little insects?",
            "Little insects are living things, so they need air, space, and safety. Being gentle means not keeping them trapped just for fun."
        )
    ],
    "bug": [
        (
            "What is a pun?",
            "A pun is a playful joke with words that sound alike or have two meanings. It is a silly kind of wordplay."
        )
    ],
    "lights": [
        (
            "What are string lights?",
            "String lights are many small bulbs joined on a cord. They can make a room or porch glow without trapping any living thing."
        )
    ],
    "lamp": [
        (
            "What does a lamp do?",
            "A lamp gives light so you can see and feel cozy. A soft lamp can make a room feel warm at bedtime."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light inside a holder. A battery lantern can glow safely without a flame."
        )
    ],
}
KNOWLEDGE_ORDER = ["fireflies", "night", "jar", "bug", "lights", "lamp", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    goal = f["goal"]
    glow = f["glow_cfg"]
    helper_cfg = f["helper_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "pun" and "twinkle".',
        f"Tell a gentle evening story where a {child.type} named {child.id} wants to {goal.wish}, but learns a kinder way to keep the night bright.",
        f"Write a warm story with repetition and sound effects, including a helper who makes a small pun and a safe ending with {glow.phrase}.",
        f"Tell a story with a moral about kindness, where {helper_cfg.helper_type} helps a child enjoy beauty without keeping it trapped.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    goal = f["goal"]
    container_cfg = f["container_cfg"]
    glow_cfg = f["glow_cfg"]
    helper_cfg = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {helper.label_word} on an evening walk. They see fireflies and make a kind choice together."
        ),
        (
            f"What did {child.id} want at first?",
            f"{child.id} wanted to {goal.wish} by carrying the fireflies home in {container_cfg.phrase}. The wish came from wonder, not from meanness."
        ),
        (
            f"Why did {helper.label_word} ask {child.id} to think again?",
            f"{helper.label_word.capitalize()} heard the tiny tired bzz from inside the container and noticed the fireflies were no longer free. That helped {child.id} see that a pretty glow should not cost a living thing its freedom."
        ),
        (
            "What was the pun in the story?",
            f"{helper_cfg.pun_line.split('“', 1)[1].rstrip('”')} It was a gentle pun used to make the kind lesson easier to remember."
        ),
        (
            f"What did {child.id} do to solve the problem?",
            f"{child.id} opened the container and let the fireflies go. Then the family used {glow_cfg.phrase} so there could still be twinkle at home without trapping anything."
        ),
        (
            "What is the moral of the story?",
            f'{f["moral"]} The ending shows that kindness can make a choice feel brighter, not dimmer.'
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"fireflies", "night", "jar"}
    helper_cfg = world.facts["helper_cfg"]
    glow_cfg = world.facts["glow_cfg"]
    tags |= set(helper_cfg.tags)
    tags |= set(glow_cfg.tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.container_open:
            flags.append("open")
        if ent.transparent:
            flags.append("transparent")
        if ent.has_air_holes:
            flags.append("air_holes")
        if ent.glows:
            flags.append("glows")
        if ent.living:
            flags.append("living")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, G, C, S) :- place(P), supports_fireflies(P), goal(G),
                     container(C), transparent(C), air_holes(C),
                     safe_glow(S), glow_ok(G, S).

% --- simple outcome model --------------------------------------------------
captured_tired(C) :- chosen_container(C), not transparent(C).
captured_tired(C) :- chosen_container(C), not air_holes(C).
captured_tired(C) :- chosen_container(C), transparent(C), air_holes(C).

kind_release :- captured_tired(_), chosen_container(C), transparent(C), air_holes(C).
story_outcome(kind) :- kind_release.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.supports_fireflies:
            lines.append(asp.fact("supports_fireflies", pid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for cid, container in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if container.transparent:
            lines.append(asp.fact("transparent", cid))
        if container.has_air_holes:
            lines.append(asp.fact("air_holes", cid))
    for sid in SAFE_GLOWS:
        lines.append(asp.fact("safe_glow", sid))
    for gid in GOALS:
        for sid in SAFE_GLOWS:
            lines.append(asp.fact("glow_ok", gid, sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_container", params.container),
    ])
    model = asp.one_model(asp_program(extra, "#show story_outcome/1."))
    outs = asp.atoms(model, "story_outcome")
    return outs[0][0] if outs else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    if "twinkle" not in sample.story.lower():
        raise StoryError("Smoke test failed: story omitted required word 'twinkle'.")
    if "pun" not in " ".join(sample.prompts).lower() and "pun" not in sample.story.lower():
        raise StoryError("Smoke test failed: storyworld omitted required word 'pun'.")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    for params in CURATED:
        out = asp_outcome(params)
        if out != "kind":
            rc = 1
            print(f"MISMATCH in outcome for curated params: expected kind, got {out}")
            break
    try:
        smoke_test()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"Smoke test failed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child wants to carry twinkle home, then chooses kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--safe-glow", dest="safe_glow", choices=SAFE_GLOWS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and not PLACES[args.place].supports_fireflies:
        raise StoryError(explain_rejection(place=PLACES[args.place]))
    if args.container is not None and not humane_container(CONTAINERS[args.container]):
        raise StoryError(explain_rejection(container=CONTAINERS[args.container]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.goal is None or c[1] == args.goal)
        and (args.container is None or c[2] == args.container)
        and (args.safe_glow is None or c[3] == args.safe_glow)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, goal, container, safe_glow = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        goal=goal,
        container=container,
        safe_glow=safe_glow,
        helper=helper,
        child_name=child_name,
        child_gender=child_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.goal not in GOALS:
        raise StoryError(f"Unknown goal: {params.goal}")
    if params.container not in CONTAINERS:
        raise StoryError(f"Unknown container: {params.container}")
    if params.safe_glow not in SAFE_GLOWS:
        raise StoryError(f"Unknown safe glow: {params.safe_glow}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    place = PLACES[params.place]
    goal = GOALS[params.goal]
    container = CONTAINERS[params.container]
    glow = SAFE_GLOWS[params.safe_glow]
    helper = HELPERS[params.helper]
    if not place.supports_fireflies:
        raise StoryError(explain_rejection(place=place))
    if not humane_container(container):
        raise StoryError(explain_rejection(container=container))

    world = tell(
        place=place,
        goal=goal,
        container_cfg=container,
        glow_cfg=glow,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("", "#show valid/4.\n#show story_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, goal, container, safe_glow) combos:\n")
        for place, goal, container, glow in combos:
            print(f"  {place:8} {goal:8} {container:12} {glow}")
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
            header = f"### {p.child_name}: {p.place}, {p.goal}, {p.container}, {p.safe_glow}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
