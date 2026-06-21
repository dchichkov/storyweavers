#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py
==============================================================================

A small storyworld about a child following a trail of tiny imprints to a worried
little animal at the edge of water, then helping it with a kind and sensible
bridge. The prose leans toward a gentle rhyming-story style, using repetition
and kindness as structural features.

Run it
------
    python storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py --place snowy_path --animal duckling --obstacle puddle
    python storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py --helper leaf_raft --obstacle brook
    python storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/imprint_plunk_repetition_kindness_rhyming_story.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to the path so ``results`` resolves from
# this nested world directory.
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
    traits: tuple = field(default_factory=tuple)
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
    sky: str
    ground: str
    affordances: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    print_name: str
    home: str
    crossing_verb: str
    grounds: set[str] = field(default_factory=set)
    obstacle_kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    kind: str
    width: int
    splash_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    use_text: str
    landing: str
    max_width: int
    kinds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_edge_worry(world: World) -> list[str]:
    child = world.get("child")
    animal = world.get("animal")
    obstacle = world.get("obstacle")
    if animal.meters["at_edge"] < THRESHOLD or obstacle.meters["crossable"] >= THRESHOLD:
        return []
    sig = ("edge_worry", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["worry"] += 1
    child.memes["concern"] += 1
    return []


def _r_splash_fear(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    if world.get("obstacle").meters["splashed"] < THRESHOLD:
        return []
    sig = ("splash_fear", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["fear"] += 1
    animal.memes["trust"] -= 1
    child.memes["regret"] += 1
    return []


def _r_kind_trust(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    if child.memes["kindness"] < THRESHOLD:
        return []
    sig = ("kind_trust", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["trust"] += 2
    animal.memes["fear"] = 0.0
    return []


def _r_cross(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    obstacle = world.get("obstacle")
    if obstacle.meters["crossable"] < THRESHOLD:
        return []
    if animal.memes["trust"] < 1.0:
        return []
    sig = ("cross", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["across"] += 1
    animal.meters["at_edge"] = 0.0
    animal.memes["worry"] = 0.0
    child.memes["joy"] += 1
    animal.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="edge_worry", tag="social", apply=_r_edge_worry),
    Rule(name="splash_fear", tag="social", apply=_r_splash_fear),
    Rule(name="kind_trust", tag="social", apply=_r_kind_trust),
    Rule(name="cross", tag="physical", apply=_r_cross),
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
                changed = True if False else changed
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "snowy_path": Place(
        id="snowy_path",
        label="the snowy path",
        sky="The morning sky was pale and bright.",
        ground="snow",
        affordances={"puddle", "brook"},
        tags={"snow"},
    ),
    "muddy_garden": Place(
        id="muddy_garden",
        label="the muddy garden",
        sky="The clouds were soft, and the earth was brown and deep.",
        ground="mud",
        affordances={"puddle", "brook"},
        tags={"mud"},
    ),
    "sandy_bank": Place(
        id="sandy_bank",
        label="the sandy bank",
        sky="The day was warm with a silver shine.",
        ground="sand",
        affordances={"puddle", "stream"},
        tags={"sand"},
    ),
}

ANIMALS = {
    "duckling": AnimalCfg(
        id="duckling",
        label="duckling",
        phrase="a small yellow duckling",
        print_name="webbed",
        home="its mother by the reeds",
        crossing_verb="paddled and peeped",
        grounds={"snow", "mud", "sand"},
        obstacle_kinds={"water"},
        tags={"duckling"},
    ),
    "froglet": AnimalCfg(
        id="froglet",
        label="froglet",
        phrase="a tiny green froglet",
        print_name="starry",
        home="the mossy side by the rushes",
        crossing_verb="hopped with a happy wiggle",
        grounds={"mud", "sand"},
        obstacle_kinds={"water"},
        tags={"frog"},
    ),
    "chick": AnimalCfg(
        id="chick",
        label="chick",
        phrase="a fluffy little chick",
        print_name="three-toed",
        home="its warm nest near the fence",
        crossing_verb="tiptoed and chirped",
        grounds={"snow", "mud"},
        obstacle_kinds={"water"},
        tags={"chick"},
    ),
}

OBSTACLES = {
    "puddle": Obstacle(
        id="puddle",
        label="puddle",
        phrase="a round cold puddle",
        kind="water",
        width=1,
        splash_word="plunk",
        tags={"puddle", "water"},
    ),
    "brook": Obstacle(
        id="brook",
        label="brook",
        phrase="a narrow brook",
        kind="water",
        width=2,
        splash_word="plunk",
        tags={"brook", "water"},
    ),
    "stream": Obstacle(
        id="stream",
        label="stream",
        phrase="a quick little stream",
        kind="water",
        width=3,
        splash_word="plunk",
        tags={"stream", "water"},
    ),
}

HELPERS = {
    "leaf_raft": Helper(
        id="leaf_raft",
        label="leaf raft",
        phrase="a bright leaf raft",
        use_text="set a wide leaf on the water like a tiny raft",
        landing="The leaf touched the water with a soft plunk.",
        max_width=1,
        kinds={"water"},
        tags={"leaf"},
    ),
    "board_bridge": Helper(
        id="board_bridge",
        label="board bridge",
        phrase="a little board bridge",
        use_text="laid a flat board from one side to the other",
        landing="The board landed by the bank with a gentle plunk.",
        max_width=2,
        kinds={"water"},
        tags={"bridge"},
    ),
    "stone_steps": Helper(
        id="stone_steps",
        label="stone steps",
        phrase="three smooth stone steps",
        use_text="placed three smooth stones in a neat stepping line",
        landing="Plunk, plunk, plunk went the stones, not too loud, not too long.",
        max_width=3,
        kinds={"water"},
        tags={"stones"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ella", "Tess", "Poppy", "Rosa", "June"]
BOY_NAMES = ["Ollie", "Finn", "Milo", "Theo", "Benji", "Toby", "Nico", "Jude"]
TRAITS = ["gentle", "bouncy", "patient", "careful", "kind", "soft-spoken"]


def helper_fits(helper: Helper, obstacle: Obstacle) -> bool:
    return obstacle.kind in helper.kinds and helper.max_width >= obstacle.width


def animal_fits(place: Place, animal: AnimalCfg, obstacle: Obstacle) -> bool:
    return (
        place.ground in animal.grounds
        and obstacle.id in place.affordances
        and obstacle.kind in animal.obstacle_kinds
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for animal_id, animal in ANIMALS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                for helper_id, helper in HELPERS.items():
                    if animal_fits(place, animal, obstacle) and helper_fits(helper, obstacle):
                        combos.append((place_id, animal_id, obstacle_id, helper_id))
    return combos


@dataclass
class StoryParams:
    place: str
    animal: str
    obstacle: str
    helper: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def predict_crossing(world: World, helper_id: str, trait: str) -> dict:
    sim = world.copy()
    helper = HELPERS[helper_id]
    obstacle = sim.get("obstacle")
    child = sim.get("child")
    animal = sim.get("animal")
    if trait == "bouncy":
        obstacle.meters["splashed"] += 1
    if helper_fits(helper, OBSTACLES[world.facts["obstacle_cfg"].id]):
        obstacle.meters["crossable"] += 1
    if trait in {"gentle", "patient", "kind", "soft-spoken", "careful"}:
        child.memes["kindness"] += 1
    else:
        child.memes["kindness"] += 1
    animal.memes["trust"] += 0
    propagate(sim, narrate=False)
    return {
        "crosses": sim.get("animal").meters["across"] >= THRESHOLD,
        "fear": sim.get("animal").memes["fear"],
        "trust": sim.get("animal").memes["trust"],
    }


def introduce(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"{place.sky} {child.id} walked along {place.label} in the light, in the light."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} liked to look low and slow, where small things show."
    )


def find_imprints(world: World, child: Entity, animal_cfg: AnimalCfg, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.pronoun('subject')} saw one tiny imprint in the {place.ground}, one tiny imprint by a tree, "
        f"one tiny imprint, two tiny imprints, three little imprints leading on with glee."
    )
    world.say(
        f'"Imprint by imprint, I wonder who you are," {child.id} whispered, "near or far?"'
    )
    world.facts["trail_kind"] = animal_cfg.print_name


def reach_edge(world: World, child: Entity, animal: Entity, obstacle: Entity, obstacle_cfg: Obstacle, animal_cfg: AnimalCfg) -> None:
    animal.meters["at_edge"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The trail stopped beside {obstacle_cfg.phrase}, where {animal_cfg.phrase} stood still and small."
    )
    world.say(
        f"It wanted to reach {animal_cfg.home}, but the water looked wide to a body so small."
    )


def accidental_plunk(world: World, child: Entity, obstacle: Entity, obstacle_cfg: Obstacle) -> None:
    obstacle.meters["splashed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A pebble slipped from {child.id}'s mittened hand. {obstacle_cfg.splash_word.capitalize()}! went the water, sudden and round."
    )
    world.say(
        f"The little one gave a jump and a blink at the sound."
    )


def speak_kindly(world: World, child: Entity, animal_cfg: AnimalCfg) -> None:
    child.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} crouched down low. "I am sorry for the splash and the sound."'
    )
    world.say(
        f'"Little {animal_cfg.label}, little {animal_cfg.label}, I will be gentle now. I will help you across somehow."'
    )


def plan_help(world: World, child: Entity, helper_cfg: Helper, obstacle_cfg: Obstacle) -> None:
    pred = predict_crossing(world, helper_cfg.id, world.facts["child_trait"])
    world.facts["predicted_crosses"] = pred["crosses"]
    world.facts["predicted_trust"] = pred["trust"]
    world.say(
        f"{child.id} looked at {obstacle_cfg.label}, looked at the little one, then looked around once more."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} thought of {helper_cfg.phrase}, a kind small door."
    )


def set_helper(world: World, child: Entity, obstacle: Entity, helper_cfg: Helper) -> None:
    obstacle.meters["crossable"] += 1
    world.say(
        f"So {child.id} {helper_cfg.use_text}."
    )
    world.say(helper_cfg.landing)
    propagate(world, narrate=False)


def cross_over(world: World, child: Entity, animal: Entity, animal_cfg: AnimalCfg) -> None:
    if animal.meters["across"] < THRESHOLD:
        raise StoryError("The helper did not make a believable crossing.")
    world.say(
        f"The little one paused, then trusted. Step by step, peep by peep, it crossed without a slip."
    )
    world.say(
        f"Soon it {animal_cfg.crossing_verb} all the way to {animal_cfg.home}."
    )
    child.memes["kindness"] += 1
    child.memes["joy"] += 1


def ending(world: World, child: Entity, place: Place, animal_cfg: AnimalCfg) -> None:
    world.say(
        f"{child.id} smiled to see fresh prints on the far side: one small imprint, two small imprints, safe in a line."
    )
    world.say(
        f"Kind hands had made a kinder day; the path was soft, the ending fine."
    )
    if place.ground == "snow":
        image = "Behind them, the snow held every tiny mark like lace."
    elif place.ground == "mud":
        image = "Behind them, the mud kept each little mark in place."
    else:
        image = "Behind them, the sand saved each little mark by the water's face."
    world.say(image)
    world.say(
        f'And {child.id} sang, "Imprint by imprint, do not fear. Kind steps help small hearts travel near."'
    )


def tell(
    place: Place,
    animal_cfg: AnimalCfg,
    obstacle_cfg: Obstacle,
    helper_cfg: Helper,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            phrase=child_name,
            role="child",
            attrs={"name": child_name, "trait": trait},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            phrase="the parent",
            role="parent",
        )
    )
    animal = world.add(
        Entity(
            id="animal",
            kind="character",
            type="animal",
            label=animal_cfg.label,
            phrase=animal_cfg.phrase,
            role="animal",
            tags=set(animal_cfg.tags),
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type=obstacle_cfg.id,
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.phrase,
            role="obstacle",
            tags=set(obstacle_cfg.tags),
        )
    )
    world.facts.update(
        place=place,
        animal_cfg=animal_cfg,
        obstacle_cfg=obstacle_cfg,
        helper_cfg=helper_cfg,
        child=child,
        parent=parent,
        animal=animal,
        obstacle=obstacle,
        child_trait=trait,
        child_name=child_name,
        startled=False,
    )
    child.memes["kindness"] = 0.0
    animal.memes["trust"] = 0.0

    introduce(world, child, place)
    find_imprints(world, child, animal_cfg, place)

    world.para()
    reach_edge(world, child, animal, obstacle, obstacle_cfg, animal_cfg)

    if trait == "bouncy":
        world.facts["startled"] = True
        accidental_plunk(world, child, obstacle, obstacle_cfg)
    else:
        world.say(
            f"The water gave its own small song, a soft {obstacle_cfg.splash_word}, as a drip fell in."
        )
        world.say(
            f"{child_name} stayed still so the frightened little one could breathe again."
        )

    world.para()
    speak_kindly(world, child, animal_cfg)
    plan_help(world, child, helper_cfg, obstacle_cfg)
    set_helper(world, child, obstacle, helper_cfg)
    cross_over(world, child, animal, animal_cfg)

    world.para()
    ending(world, child, place, animal_cfg)

    world.facts["outcome"] = outcome_of_params(
        StoryParams(
            place=place.id,
            animal=animal_cfg.id,
            obstacle=obstacle_cfg.id,
            helper=helper_cfg.id,
            child_name=child_name,
            child_gender=child_gender,
            parent=parent_type,
            trait=trait,
            seed=None,
        )
    )
    return world


KNOWLEDGE = {
    "imprint": [
        (
            "What is an imprint?",
            "An imprint is a mark left behind when something presses into snow, mud, or sand. A tiny foot can leave an imprint that shows where someone went."
        )
    ],
    "puddle": [
        (
            "What is a puddle?",
            "A puddle is a little pool of water on the ground. Small animals may find even a puddle hard to cross."
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of moving water. It can still feel wide to a tiny animal with short legs."
        )
    ],
    "stream": [
        (
            "What is a stream?",
            "A stream is a flow of water that moves along the ground. Even a quick little stream can be tricky for a very small creature."
        )
    ],
    "duckling": [
        (
            "What is a duckling?",
            "A duckling is a baby duck. Ducklings are small, fluffy, and often stay close to their mother."
        )
    ],
    "frog": [
        (
            "What is a froglet?",
            "A froglet is a young frog. It is bigger than a tadpole but still very small."
        )
    ],
    "chick": [
        (
            "What is a chick?",
            "A chick is a baby chicken or bird. Chicks are tiny and need safe places to walk."
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge helps someone cross from one side to another without stepping into the water. Even a small bridge can solve a big problem for a tiny animal."
        )
    ],
    "leaf": [
        (
            "How can a leaf help a tiny creature?",
            "A broad leaf can float for a moment like a tiny raft on calm water. That can help a very small creature cross a little puddle."
        )
    ],
    "stones": [
        (
            "What are stepping stones?",
            "Stepping stones are stones placed in a line so feet can land on them one by one. They make a path across wet ground or shallow water."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing gentle help when someone is scared or small. Kindness means noticing another creature's worry and trying to make things easier."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "imprint",
    "puddle",
    "brook",
    "stream",
    "duckling",
    "frog",
    "chick",
    "bridge",
    "leaf",
    "stones",
    "kindness",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    animal_cfg = f["animal_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    helper_cfg = f["helper_cfg"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "imprint" and "plunk".',
        f"Tell a gentle story where {child.label} follows tiny imprints, finds {animal_cfg.phrase} beside {obstacle_cfg.phrase}, and helps with {helper_cfg.phrase}.",
        "Write a repetitive kindness story where a child notices a scared little creature, speaks softly, and proves that gentle help can change the day.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    animal_cfg = f["animal_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    helper_cfg = f["helper_cfg"]
    place = f["place"]
    name = child.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a child who noticed a tiny trail, and {animal_cfg.phrase} waiting by {obstacle_cfg.phrase}. The story follows how {name} turned noticing into helping."
        ),
        (
            "What did the child find first?",
            f"{name} first found a tiny imprint, then another, and another. The repeated trail led {child.pronoun('object')} to the worried little animal."
        ),
        (
            f"Why was the {animal_cfg.label} worried?",
            f"The {animal_cfg.label} wanted to reach {animal_cfg.home}, but {obstacle_cfg.phrase} felt too wide for such a small body. In the world model, standing at the edge made worry rise until help arrived."
        ),
    ]
    if f.get("startled"):
        qa.append(
            (
                "What happened when the water went plunk?",
                f"A pebble slipped and went plunk in the water, which startled the {animal_cfg.label}. That splash raised fear for a moment, so the child had to slow down, apologize, and rebuild trust with kindness."
            )
        )
    else:
        qa.append(
            (
                "Did the child scare the little animal on purpose?",
                f"No. The child stayed still and gentle while the water made a small plunk of its own. That calm choice helped the little animal feel safer instead of more afraid."
            )
        )
    qa.append(
        (
            f"How did {name} help the {animal_cfg.label} cross?",
            f"{name} used {helper_cfg.phrase} to make a safe way over. Once the path was ready and the child spoke kindly, the little animal trusted the help and crossed step by step."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with fresh little imprints on the far side and the small creature safely home. The ending image proves what changed: worry and fear became relief because someone chose gentle help."
        )
    )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"imprint", "kindness"}
    obstacle = f["obstacle_cfg"]
    animal = f["animal_cfg"]
    helper = f["helper_cfg"]
    tags |= set(obstacle.tags)
    tags |= set(animal.tags)
    tags |= set(helper.tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, animal: AnimalCfg, obstacle: Obstacle, helper: Helper) -> str:
    if place.ground not in animal.grounds:
        return (
            f"(No story: {animal.label} does not fit {place.ground} ground in this tiny world, "
            f"so the imprint trail would feel forced.)"
        )
    if obstacle.id not in place.affordances:
        return (
            f"(No story: {place.label} does not naturally contain a {obstacle.label} here.)"
        )
    if obstacle.kind not in animal.obstacle_kinds:
        return (
            f"(No story: this animal is not modeled for that kind of crossing problem.)"
        )
    return (
        f"(No story: {helper.label} is too small for {obstacle.phrase}. "
        f"The kind fix must honestly reach across the water.)"
    )


def outcome_of_params(params: StoryParams) -> str:
    if params.trait == "bouncy":
        return "startled_helped"
    return "calm_helped"


ASP_RULES = r"""
% Reasonableness gate.
valid(P, A, O, H) :- place(P), animal(A), obstacle(O), helper(H),
                     ground_of(P, G), likes_ground(A, G),
                     affords(P, O), obstacle_kind(O, K), likes_kind(A, K),
                     helper_kind(H, K), width(O, W), max_width(H, M), M >= W.

% Outcome model.
startled :- trait(bouncy).
calm     :- trait(T), T != bouncy.

outcome(startled_helped) :- startled, chosen_valid.
outcome(calm_helped)     :- calm, chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("ground_of", place_id, place.ground))
        for obs in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, obs))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for ground in sorted(animal.grounds):
            lines.append(asp.fact("likes_ground", animal_id, ground))
        for kind in sorted(animal.obstacle_kinds):
            lines.append(asp.fact("likes_kind", animal_id, kind))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("obstacle_kind", obstacle_id, obstacle.kind))
        lines.append(asp.fact("width", obstacle_id, obstacle.width))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("max_width", helper_id, helper.max_width))
        for kind in sorted(helper.kinds):
            lines.append(asp.fact("helper_kind", helper_id, kind))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("known_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("chosen_valid") if (params.place, params.animal, params.obstacle, params.helper) in set(valid_combos()) else "",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="snowy_path",
        animal="duckling",
        obstacle="puddle",
        helper="leaf_raft",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        seed=None,
    ),
    StoryParams(
        place="muddy_garden",
        animal="froglet",
        obstacle="brook",
        helper="board_bridge",
        child_name="Ollie",
        child_gender="boy",
        parent="father",
        trait="bouncy",
        seed=None,
    ),
    StoryParams(
        place="snowy_path",
        animal="chick",
        obstacle="brook",
        helper="board_bridge",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="patient",
        seed=None,
    ),
    StoryParams(
        place="sandy_bank",
        animal="duckling",
        obstacle="stream",
        helper="stone_steps",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="muddy_garden",
        animal="duckling",
        obstacle="puddle",
        helper="leaf_raft",
        child_name="Poppy",
        child_gender="girl",
        parent="mother",
        trait="kind",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a child follows imprints, hears a plunk, and helps a tiny creature across water."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.animal and args.obstacle and args.helper:
        place = PLACES[args.place]
        animal = ANIMALS[args.animal]
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if not (animal_fits(place, animal, obstacle) and helper_fits(helper, obstacle)):
            raise StoryError(explain_rejection(place, animal, obstacle, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, animal_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        animal=animal_id,
        obstacle=obstacle_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    place = PLACES[params.place]
    animal_cfg = ANIMALS[params.animal]
    obstacle_cfg = OBSTACLES[params.obstacle]
    helper_cfg = HELPERS[params.helper]
    if not animal_fits(place, animal_cfg, obstacle_cfg) or not helper_fits(helper_cfg, obstacle_cfg):
        raise StoryError(explain_rejection(place, animal_cfg, obstacle_cfg, helper_cfg))

    world = tell(
        place=place,
        animal_cfg=animal_cfg,
        obstacle_cfg=obstacle_cfg,
        helper_cfg=helper_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
    )
    child = world.facts["child"]
    story = world.render().replace("child", child.label)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        py_out = outcome_of_params(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, animal, obstacle, helper) combos:\n")
        for place, animal, obstacle, helper in combos:
            print(f"  {place:12} {animal:8} {obstacle:8} {helper}")
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
            header = f"### {p.child_name}: {p.animal} at {p.place} with {p.helper}"
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
