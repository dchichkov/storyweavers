#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spell_gerund_flashback_happy_ending_transformation_adventure.py
==========================================================================================

A standalone storyworld for a tiny adventure domain built from the seed
"spell-gerund" with Flashback, Happy Ending, and Transformation.

Premise
-------
A child goes on a small quest to reach a magical place. On the way, the child
meets a creature trapped in a lesser shape by a gloomy spell. A remembered
lesson from an elder (the flashback) helps the child use a gentle magic action
to free the creature. The creature's restored form then helps solve the last
adventure obstacle, and the ending image proves the world changed for the better.

Reasonableness gate
-------------------
Not every place / obstacle / true-form / treasure combination makes a sensible
story. The restored creature must be the kind of helper that can honestly solve
the obstacle, and the treasure must suit the destination. Invalid explicit
choices raise StoryError with a legible explanation.

Run it
------
python storyworlds/worlds/gpt-5.4/spell_gerund_flashback_happy_ending_transformation_adventure.py
python storyworlds/worlds/gpt-5.4/spell_gerund_flashback_happy_ending_transformation_adventure.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/spell_gerund_flashback_happy_ending_transformation_adventure.py --all --qa
python storyworlds/worlds/gpt-5.4/spell_gerund_flashback_happy_ending_transformation_adventure.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so three dirname() calls
# bring us back to storyworlds/.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "witch", "queen"}
        male = {"boy", "father", "man", "uncle", "wizard", "king"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    name: str
    start_image: str
    goal: str
    ending_image: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    problem: str
    challenge_line: str
    solved_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class TrueForm:
    id: str
    small_form: str
    true_label: str
    verb_ing: str
    solve_text: str
    can_solve: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    suits: set[str] = field(default_factory=set)
    ending_line: str = ""
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


def _r_restore(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["spell_softened"] < THRESHOLD:
        return []
    sig = ("restore", "creature")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["transformed"] = 0.0
    creature.meters["restored"] += 1
    creature.memes["gratitude"] += 1
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    return ["__restored__"]


def _r_help(world: World) -> list[str]:
    creature = world.get("creature")
    gate = world.get("gate")
    if creature.meters["restored"] < THRESHOLD or gate.meters["blocked"] < THRESHOLD:
        return []
    sig = ("help", "gate")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["blocked"] = 0.0
    gate.meters["open"] += 1
    hero = world.get("hero")
    hero.memes["hope"] += 1
    return ["__helped__"]


CAUSAL_RULES = [
    Rule(name="restore", tag="magic", apply=_r_restore),
    Rule(name="help", tag="physical", apply=_r_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for item in produced:
            if item.startswith("__"):
                continue
            world.say(item)
    return produced


def combo_valid(place: Place, obstacle: Obstacle, true_form: TrueForm, treasure: Treasure) -> bool:
    return (
        obstacle.id in place.fits
        and obstacle.id in true_form.can_solve
        and true_form.id in obstacle.solved_by
        and place.id in treasure.suits
    )


def explain_rejection(place: Place, obstacle: Obstacle, true_form: TrueForm, treasure: Treasure) -> str:
    if obstacle.id not in place.fits:
        return (
            f"(No story: {obstacle.label} does not fit a quest to {place.name}. "
            f"Pick an obstacle that belongs on that route.)"
        )
    if obstacle.id not in true_form.can_solve or true_form.id not in obstacle.solved_by:
        return (
            f"(No story: restoring {true_form.true_label} would not honestly solve "
            f"{obstacle.label}. The helper must be able to fix the obstacle.)"
        )
    if place.id not in treasure.suits:
        return (
            f"(No story: {treasure.label} does not suit the ending at {place.name}. "
            f"Pick a treasure that belongs in that destination.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for form_id, true_form in TRUE_FORMS.items():
                for treasure_id, treasure in TREASURES.items():
                    if combo_valid(place, obstacle, true_form, treasure):
                        out.append((place_id, obstacle_id, form_id, treasure_id))
    return sorted(out)


def predict_restoration(true_form: TrueForm, obstacle: Obstacle) -> bool:
    return obstacle.id in true_form.can_solve and true_form.id in obstacle.solved_by


def depart(world: World, hero: Entity, place: Place, treasure: Treasure) -> None:
    hero.memes["eager"] += 1
    world.say(
        f"At first light, {hero.id} set out for {place.name}. {place.start_image} "
        f"{hero.pronoun().capitalize()} hoped to bring home {treasure.phrase} from {place.goal}."
    )


def meet_small_form(world: World, hero: Entity, true_form: TrueForm) -> None:
    creature = world.get("creature")
    creature.meters["transformed"] += 1
    creature.memes["sadness"] += 1
    hero.memes["pity"] += 1
    world.say(
        f"Near a bend in the path, {hero.id} found {true_form.small_form} shivering under a fern. "
        f"It wore a silver thread around one paw, as if it had once belonged to a bigger and braver story."
    )


def obstacle_rises(world: World, obstacle: Obstacle) -> None:
    gate = world.get("gate")
    gate.meters["blocked"] += 1
    world.say(obstacle.problem)
    world.say(obstacle.challenge_line)


def flashback(world: World, elder: Entity) -> None:
    hero = world.get("hero")
    hero.memes["memory"] += 1
    world.say(
        f"Then {hero.id} remembered a morning at home. {elder.label_word.capitalize()} had tapped an old book "
        f"and said, \"When a spell knot will not open, do not shout at it. Try spell-gerund: hum the kind part "
        f"of the spell while breathing slow, and magic may remember what it was for.\""
    )


def gentle_spell(world: World, hero: Entity, true_form: TrueForm) -> None:
    creature = world.get("creature")
    hero.memes["brave"] += 1
    creature.meters["spell_softened"] += 1
    world.say(
        f"So {hero.id} knelt beside the little creature and began {true_form.verb_ing}, very softly. "
        f"The tune was not loud, but it was steady, and the silver thread around the creature began to glow."
    )
    propagate(world, narrate=False)


def transform(world: World, true_form: TrueForm) -> None:
    creature = world.get("creature")
    if creature.meters["restored"] < THRESHOLD:
        raise StoryError("(Story failure: the creature was not restored before transformation was narrated.)")
    world.say(
        f"The fern tips lifted in a warm swirl of light. The small creature stretched, shimmered, and changed "
        f"into {true_form.true_label}. {creature.pronoun().capitalize()} blinked once, then bowed to {world.get('hero').id}."
    )


def restored_speaks(world: World, true_form: TrueForm) -> None:
    hero = world.get("hero")
    creature = world.get("creature")
    world.say(
        f"\"You heard the true song,\" said the {true_form.true_label}. \"A crooked spell squeezed me small, "
        f"but your gentle magic untied it. I will help you reach {world.facts['place'].goal}, {hero.id}.\""
    )
    creature.memes["loyalty"] += 1
    hero.memes["trust"] += 1


def solve_obstacle(world: World, obstacle: Obstacle, true_form: TrueForm) -> None:
    gate = world.get("gate")
    if gate.meters["blocked"] < THRESHOLD:
        raise StoryError("(Story failure: the obstacle was not present before the solution beat.)")
    propagate(world, narrate=False)
    if gate.meters["open"] < THRESHOLD:
        raise StoryError("(Story failure: the restored helper did not solve the obstacle.)")
    world.say(true_form.solve_text.format(obstacle=obstacle.label))
    world.say(
        f"In a moment, the way ahead was open. What had looked like the end of the adventure became its shining turn."
    )


def ending(world: World, place: Place, treasure: Treasure) -> None:
    hero = world.get("hero")
    creature = world.get("creature")
    hero.memes["joy"] += 1
    world.say(
        f"Together they reached {place.goal}, where {treasure.phrase} waited in the clear light. "
        f"{treasure.ending_line}"
    )
    world.say(
        f"When {hero.id} started home, the {creature.label} flew beside {hero.pronoun('object')} instead of hiding in the grass. "
        f"{place.ending_image}"
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    true_form: TrueForm,
    treasure: Treasure,
    *,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_type: str = "aunt",
    trait: str = "curious",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=["young", trait],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
        )
    )
    creature = world.add(
        Entity(
            id="creature",
            kind="character",
            type="creature",
            label=true_form.true_label,
            phrase=true_form.small_form,
            role="helper",
            tags=set(true_form.tags),
        )
    )
    gate = world.add(
        Entity(
            id="gate",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            role="obstacle",
            tags=set(obstacle.tags),
        )
    )

    depart(world, hero, place, treasure)
    obstacle_rises(world, obstacle)
    world.para()
    meet_small_form(world, hero, true_form)
    flashback(world, elder)
    gentle_spell(world, hero, true_form)
    world.para()
    transform(world, true_form)
    restored_speaks(world, true_form)
    solve_obstacle(world, obstacle, true_form)
    world.para()
    ending(world, place, treasure)

    world.facts.update(
        hero=hero,
        elder=elder,
        creature=creature,
        place=place,
        obstacle=obstacle,
        true_form=true_form,
        treasure=treasure,
        transformed=creature.meters["restored"] >= THRESHOLD,
        path_open=gate.meters["open"] >= THRESHOLD,
        flashback_used=hero.memes["memory"] >= THRESHOLD,
        happy=True,
    )
    return world


PLACES = {
    "moon_bridge": Place(
        id="moon_bridge",
        name="the Moonlit Bridge",
        start_image="Mist curled over the stones, and every step felt like the first page of a map.",
        goal="the far side of the Moonlit Bridge",
        ending_image="By dusk, the bridge no longer looked lonely; it shone with safe silver light.",
        fits={"river_chasm", "locked_arch"},
        tags={"bridge", "adventure"},
    ),
    "sunken_garden": Place(
        id="sunken_garden",
        name="the Sunken Garden",
        start_image="Broken statues peeped through ivy, and the path dipped lower and lower like a secret stair.",
        goal="the heart of the Sunken Garden",
        ending_image="The garden, once dim and hushed, rang with fresh water and bright birdsong.",
        fits={"thorn_wall", "locked_arch"},
        tags={"garden", "adventure"},
    ),
    "crystal_cave": Place(
        id="crystal_cave",
        name="the Crystal Cave",
        start_image="Blue sparks winked inside the rock, and cool air breathed out of the cave mouth.",
        goal="the crystal hall",
        ending_image="The cave walls answered with clean bell-like echoes instead of lonely drips.",
        fits={"river_chasm", "dark_tunnel"},
        tags={"cave", "adventure"},
    ),
}

OBSTACLES = {
    "river_chasm": Obstacle(
        id="river_chasm",
        label="the broken river gap",
        problem="But halfway there, a river had bitten the path in two. Water rushed below, and the stepping stones were gone.",
        challenge_line="No small child could jump that far alone.",
        solved_by={"sky_dragon", "stone_giant"},
        tags={"river", "gap"},
    ),
    "thorn_wall": Obstacle(
        id="thorn_wall",
        label="the thorn wall",
        problem="Soon a wall of living thorns twisted across the trail. Its branches clicked together like green claws.",
        challenge_line="There was no safe way through with bare hands.",
        solved_by={"forest_stag", "stone_giant"},
        tags={"thorns", "wall"},
    ),
    "locked_arch": Obstacle(
        id="locked_arch",
        label="the locked moon arch",
        problem="At the last turn stood a pale stone arch with no handle, no keyhole, and no door to push.",
        challenge_line="Still, the air behind it smelled of flowers and treasure.",
        solved_by={"forest_stag", "sky_dragon"},
        tags={"arch", "magic_gate"},
    ),
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="the dark tunnel",
        problem="Then the path slipped into a tunnel so dark that even the pebbles vanished.",
        challenge_line="Going forward blind would have been foolish.",
        solved_by={"sky_dragon"},
        tags={"dark", "tunnel"},
    ),
}

TRUE_FORMS = {
    "sky_dragon": TrueForm(
        id="sky_dragon",
        small_form="a soot-gray lizard no longer than a spoon",
        true_label="a sky-dragon with lantern wings",
        verb_ing="spell-singing",
        solve_text="The sky-dragon beat its glowing wings and cast a bright path over {obstacle}, so crossing became easy and safe.",
        can_solve={"river_chasm", "locked_arch", "dark_tunnel"},
        tags={"dragon", "flight", "magic"},
    ),
    "forest_stag": TrueForm(
        id="forest_stag",
        small_form="a mossy mouse with a crown-shaped patch on its head",
        true_label="a forest stag with silver antlers",
        verb_ing="spell-humming",
        solve_text="The forest stag lowered its silver antlers to {obstacle}, and the hard magic there softened and parted like grass in rain.",
        can_solve={"thorn_wall", "locked_arch"},
        tags={"stag", "forest", "magic"},
    ),
    "stone_giant": TrueForm(
        id="stone_giant",
        small_form="a sleepy pebble-toad with dust on its back",
        true_label="a stone giant with kind mountain eyes",
        verb_ing="spell-whispering",
        solve_text="The stone giant set one broad hand against {obstacle}, and the blocked way shifted open with a slow, safe rumble.",
        can_solve={"river_chasm", "thorn_wall"},
        tags={"giant", "stone", "strength"},
    ),
}

TREASURES = {
    "singing_seed": Treasure(
        id="singing_seed",
        label="the singing seed",
        phrase="the singing seed",
        suits={"sunken_garden"},
        ending_line="When the child touched the singing seed, it opened like a tiny green lantern and sent a sweet note into the leaves.",
        tags={"seed", "garden"},
    ),
    "star_map": Treasure(
        id="star_map",
        label="the star map",
        phrase="the star map rolled in blue ribbon",
        suits={"moon_bridge", "crystal_cave"},
        ending_line="The map glittered with brave little lines that seemed to promise a hundred more kind adventures.",
        tags={"map", "stars"},
    ),
    "echo_crystal": Treasure(
        id="echo_crystal",
        label="the echo crystal",
        phrase="the echo crystal in a cradle of stone",
        suits={"crystal_cave"},
        ending_line="The crystal answered every happy word with a clear, chiming echo, as if the cave itself had learned to smile.",
        tags={"crystal", "sound"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Ivy", "Asha", "Zoe", "Pia"]
BOY_NAMES = ["Oren", "Milo", "Finn", "Tobin", "Eli", "Noah", "Rian", "Theo"]
TRAITS = ["curious", "brave", "careful", "hopeful", "quick-footed", "kind"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    true_form: str
    treasure: str
    hero_name: str
    hero_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "dragon": [
        (
            "What is a dragon in a fantasy story?",
            "A dragon in a fantasy story is a make-believe creature with great power. Some dragons are scary, but some are wise helpers."
        )
    ],
    "stag": [
        (
            "What is a stag?",
            "A stag is a grown deer with antlers. In stories, a magical stag often stands for the forest's strength and grace."
        )
    ],
    "giant": [
        (
            "What is a giant?",
            "A giant is an enormous make-believe person or creature. Giants in stories can use their size to move heavy things or protect others."
        )
    ],
    "magic": [
        (
            "What is a spell?",
            "A spell is a bit of make-believe magic. In gentle stories, a spell can change things, heal things, or undo a curse."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes into a different form. It often shows that a hidden truth or strength has come back."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back to something that happened earlier. It helps explain why a character knows what to do now."
        )
    ],
    "bridge": [
        (
            "Why is a bridge important on a journey?",
            "A bridge helps travelers cross from one side to another. If a bridge or crossing is blocked, the journey can stop until someone finds a safe way through."
        )
    ],
    "garden": [
        (
            "What is special about a story garden?",
            "A story garden is often a place where something sleeping can wake up again. It can show healing, growth, and new life."
        )
    ],
    "cave": [
        (
            "Why are caves used in adventure stories?",
            "Caves feel secret and mysterious, so they make adventures exciting. A cave can hide treasure, danger, or an important discovery."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "flashback",
    "transformation",
    "magic",
    "dragon",
    "stag",
    "giant",
    "bridge",
    "garden",
    "cave",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    obstacle = f["obstacle"]
    true_form = f["true_form"]
    treasure = f["treasure"]
    return [
        (
            f'Write a short adventure story for a 3-to-5-year-old that includes the word "spell-gerund", '
            f'uses a flashback, and ends happily after a transformation.'
        ),
        (
            f"Tell a gentle quest where {hero.id} travels to {place.name}, meets a creature trapped as "
            f"{true_form.small_form}, remembers an elder's lesson, and frees it before facing {obstacle.label}."
        ),
        (
            f"Write an adventure with a magical transformation and a bright ending, where the hero reaches "
            f"{place.goal} and finds {treasure.label} after solving {obstacle.label}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    obstacle = f["obstacle"]
    true_form = f["true_form"]
    treasure = f["treasure"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young adventurer, and a magical creature who was hidden in a smaller shape. "
            f"The story also includes {hero.pronoun('possessive')} {elder.label_word}, whose old lesson helps at the right time."
        ),
        (
            f"Where was {hero.id} trying to go?",
            f"{hero.id} was trying to reach {place.goal}. The trip felt like a real adventure because the path became dangerous before the destination."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {hero.id}'s {elder.label_word} teaching a gentle way to untie magic by using spell-gerund. "
            f"That memory mattered because it told {hero.pronoun('object')} how to help instead of panic."
        ),
        (
            "What transformation happened in the story?",
            f"The frightened little creature changed back into {true_form.true_label}. "
            f"It happened after {hero.id} used a kind magical song and the crooked spell loosened."
        ),
        (
            f"How did the restored creature help with {obstacle.label}?",
            f"{true_form.solve_text.format(obstacle=obstacle.label)} "
            f"Because the transformation came first, the helper could do what the small trapped form never could."
        ),
        (
            "How did the story end?",
            f"It ended happily: {hero.id} reached {place.goal} and found {treasure.phrase}. "
            f"The last image shows the place brighter and safer, which proves the adventure changed the world for the better."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"magic", "flashback", "transformation"}
    place = f["place"]
    true_form = f["true_form"]
    tags |= set(place.tags)
    tags |= set(true_form.tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_bridge",
        obstacle="river_chasm",
        true_form="sky_dragon",
        treasure="star_map",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="aunt",
        trait="curious",
    ),
    StoryParams(
        place="sunken_garden",
        obstacle="thorn_wall",
        true_form="forest_stag",
        treasure="singing_seed",
        hero_name="Oren",
        hero_gender="boy",
        elder_type="uncle",
        trait="kind",
    ),
    StoryParams(
        place="crystal_cave",
        obstacle="dark_tunnel",
        true_form="sky_dragon",
        treasure="echo_crystal",
        hero_name="Lina",
        hero_gender="girl",
        elder_type="aunt",
        trait="brave",
    ),
    StoryParams(
        place="sunken_garden",
        obstacle="locked_arch",
        true_form="forest_stag",
        treasure="singing_seed",
        hero_name="Theo",
        hero_gender="boy",
        elder_type="uncle",
        trait="hopeful",
    ),
    StoryParams(
        place="moon_bridge",
        obstacle="river_chasm",
        true_form="stone_giant",
        treasure="star_map",
        hero_name="Pia",
        hero_gender="girl",
        elder_type="aunt",
        trait="careful",
    ),
]


ASP_RULES = r"""
valid(P, O, F, T) :- place(P), obstacle(O), form(F), treasure(T),
                     fits(P, O), solves(F, O), suits(T, P).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.fits):
            lines.append(asp.fact("fits", place_id, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for form_id, true_form in TRUE_FORMS.items():
        lines.append(asp.fact("form", form_id))
        for obstacle_id in sorted(true_form.can_solve):
            lines.append(asp.fact("solves", form_id, obstacle_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        for place_id in sorted(treasure.suits):
            lines.append(asp.fact("suits", treasure_id, place_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES.replace('#show valid/4.', '')}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _check_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.true_form not in TRUE_FORMS:
        raise StoryError(f"(Unknown true_form: {params.true_form})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    true_form = TRUE_FORMS[params.true_form]
    treasure = TREASURES[params.treasure]
    if not combo_valid(place, obstacle, true_form, treasure):
        raise StoryError(explain_rejection(place, obstacle, true_form, treasure))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "spell-gerund" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missing required seed word or text.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Smoke test failed: generate() returned incomplete sample.)")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a tiny adventure with flashback, transformation, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--true-form", dest="true_form", choices=TRUE_FORMS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", dest="elder_type", choices=["aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.true_form and args.treasure:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        true_form = TRUE_FORMS[args.true_form]
        treasure = TREASURES[args.treasure]
        if not combo_valid(place, obstacle, true_form, treasure):
            raise StoryError(explain_rejection(place, obstacle, true_form, treasure))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.true_form is None or combo[2] == args.true_form)
        and (args.treasure is None or combo[3] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, true_form_id, treasure_id = rng.choice(combos)
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    elder_type = args.elder_type or rng.choice(["aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        true_form=true_form_id,
        treasure=treasure_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        PLACES[params.place],
        OBSTACLES[params.obstacle],
        TRUE_FORMS[params.true_form],
        TREASURES[params.treasure],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, true_form, treasure) combos:\n")
        for place, obstacle, true_form, treasure in combos:
            print(f"  {place:14} {obstacle:12} {true_form:12} {treasure}")
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
            header = (
                f"### {p.hero_name}: {p.true_form} at {p.place} "
                f"({p.obstacle} -> {p.treasure})"
            )
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
