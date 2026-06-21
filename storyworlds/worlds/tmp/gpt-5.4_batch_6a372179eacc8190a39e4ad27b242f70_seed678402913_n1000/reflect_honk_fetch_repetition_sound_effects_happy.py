#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reflect_honk_fetch_repetition_sound_effects_happy.py
================================================================================

A small slice-of-life storyworld about a child, a dog, a game of fetch, a sudden
honk, and a bright toy found again with the help of a reflective surface.

The world keeps one simple causal shape:

    cheerful fetch game
    -> toy rolls too near the shared path
    -> Honk! Honk! a rider or van warns them
    -> child calls the dog back and the toy disappears under something low
    -> a puddle or window helps reflect the toy's color
    -> they move the game to a safer spot and end happily

Coverage is intentionally narrow. The world refuses combinations that would make
the turn weak or unreasonable, such as a floppy toy that would not roll into the
little safety scare, or a non-reflective helper that could not honestly help
find the toy.

Run it
------
    python storyworlds/worlds/gpt-5.4/reflect_honk_fetch_repetition_sound_effects_happy.py
    python storyworlds/worlds/gpt-5.4/reflect_honk_fetch_repetition_sound_effects_happy.py --setting courtyard --fetch ball --reflector puddle
    python storyworlds/worlds/gpt-5.4/reflect_honk_fetch_repetition_sound_effects_happy.py --fetch plush_duck
    python storyworlds/worlds/gpt-5.4/reflect_honk_fetch_repetition_sound_effects_happy.py --all
    python storyworlds/worlds/gpt-5.4/reflect_honk_fetch_repetition_sound_effects_happy.py --qa --json
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"dog", "puppy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    throw_area: str
    edge_area: str
    hide_spot: str
    honker: str
    move_to: str
    reflectors: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FetchThing:
    id: str
    label: str
    phrase: str
    color: str
    bounce_text: str
    can_roll: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Reflector:
    id: str
    label: str
    phrase: str
    scene_text: str
    reveal_text: str
    truly_reflective: bool = True
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


def _r_edge_risk(world: World) -> list[str]:
    toy = world.get("toy")
    child = world.get("child")
    dog = world.get("dog")
    if toy.meters["near_edge"] < THRESHOLD:
        return []
    sig = ("edge_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["alarm"] += 1
    dog.memes["hesitate"] += 1
    world.get("path").meters["risk"] += 1
    return []


def _r_honk_pause(world: World) -> list[str]:
    child = world.get("child")
    dog = world.get("dog")
    path = world.get("path")
    if path.meters["risk"] < THRESHOLD or path.meters["honked"] < THRESHOLD:
        return []
    sig = ("honk_pause",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["care"] += 1
    child.memes["relief"] += 1
    dog.meters["paused"] += 1
    return []


def _r_reflect_find(world: World) -> list[str]:
    toy = world.get("toy")
    helper = world.get("reflector")
    child = world.get("child")
    if toy.meters["hidden"] < THRESHOLD or helper.meters["glint"] < THRESHOLD:
        return []
    sig = ("reflect_find",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["found"] += 1
    toy.meters["hidden"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="edge_risk", tag="physical", apply=_r_edge_risk),
    Rule(name="honk_pause", tag="social", apply=_r_honk_pause),
    Rule(name="reflect_find", tag="perception", apply=_r_reflect_find),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        opening="Between the laundry lines and flower pots, the afternoon felt slow and friendly.",
        throw_area="the chalky middle of the courtyard",
        edge_area="the little gate beside the delivery lane",
        hide_spot="under a wooden bench",
        honker="the bakery van at the lane",
        move_to="the quiet patch by the flower bed",
        reflectors={"puddle", "window"},
        tags={"courtyard", "van", "path"},
    ),
    "park": Setting(
        id="park",
        place="the small park",
        opening="The grass still held a little morning coolness, and the swings clicked softly nearby.",
        throw_area="the open grass by the bench",
        edge_area="the bike path",
        hide_spot="under the green bench",
        honker="a bicycle on the path",
        move_to="the far side of the grass under the maple tree",
        reflectors={"puddle", "window"},
        tags={"park", "bike", "path"},
    ),
    "sidewalk": Setting(
        id="sidewalk",
        place="the wide front sidewalk",
        opening="Neighbors were watering plants, and the whole block sounded calm and ordinary.",
        throw_area="the wide patch of pavement by the stoop",
        edge_area="the driveway mouth",
        hide_spot="under a stroller by the wall",
        honker="a scooter rolling past the driveway",
        move_to="the fenced square of grass by the steps",
        reflectors={"window", "metal_door"},
        tags={"sidewalk", "scooter", "driveway"},
    ),
}

FETCH_THINGS = {
    "ball": FetchThing(
        id="ball",
        label="ball",
        phrase="a red rubber ball",
        color="red",
        bounce_text="It bounced once, twice, and then scooted away faster than anyone meant it to.",
        can_roll=True,
        tags={"ball", "fetch"},
    ),
    "ring": FetchThing(
        id="ring",
        label="ring",
        phrase="a blue fetch ring",
        color="blue",
        bounce_text="It skipped on its edge and rolled with a low humming spin.",
        can_roll=True,
        tags={"ring", "fetch"},
    ),
    "tennis_ball": FetchThing(
        id="tennis_ball",
        label="tennis ball",
        phrase="a fuzzy yellow tennis ball",
        color="yellow",
        bounce_text="It boinged off the ground and zipped ahead in a silly hurry.",
        can_roll=True,
        tags={"ball", "fetch"},
    ),
    "plush_duck": FetchThing(
        id="plush_duck",
        label="plush duck",
        phrase="a soft plush duck",
        color="yellow",
        bounce_text="It only flopped down with a soft little fwump.",
        can_roll=False,
        tags={"toy"},
    ),
}

REFLECTORS = {
    "puddle": Reflector(
        id="puddle",
        label="puddle",
        phrase="a rain puddle",
        scene_text="A rain puddle lay nearby, still enough to reflect the sky.",
        reveal_text="In the puddle, a bright little patch of color began to reflect under the edge.",
        truly_reflective=True,
        tags={"puddle", "reflect"},
    ),
    "window": Reflector(
        id="window",
        label="window",
        phrase="a bright shop window",
        scene_text="A bright window beside them could reflect the whole path like a picture.",
        reveal_text="In the window, a small flash of color began to reflect from the shadow underneath.",
        truly_reflective=True,
        tags={"window", "reflect"},
    ),
    "metal_door": Reflector(
        id="metal_door",
        label="metal door",
        phrase="a shiny metal door",
        scene_text="A shiny metal door nearby could reflect shapes in a wobbly silver blur.",
        reveal_text="On the metal door, a wobbling patch of color began to reflect from below.",
        truly_reflective=True,
        tags={"metal", "reflect"},
    ),
    "leaf_pile": Reflector(
        id="leaf_pile",
        label="leaf pile",
        phrase="a dry leaf pile",
        scene_text="A dry leaf pile rustled in the corner.",
        reveal_text="Nothing about the leaf pile could show them where to look.",
        truly_reflective=False,
        tags={"leaves"},
    ),
}


def valid_combo(setting_id: str, fetch_id: str, reflector_id: str) -> bool:
    if setting_id not in SETTINGS or fetch_id not in FETCH_THINGS or reflector_id not in REFLECTORS:
        return False
    setting = SETTINGS[setting_id]
    fetch = FETCH_THINGS[fetch_id]
    reflector = REFLECTORS[reflector_id]
    return fetch.can_roll and reflector.truly_reflective and reflector_id in setting.reflectors


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for fid in FETCH_THINGS:
            for rid in REFLECTORS:
                if valid_combo(sid, fid, rid):
                    combos.append((sid, fid, rid))
    return combos


@dataclass
class StoryParams:
    setting: str
    fetch: str
    reflector: str
    child_name: str
    child_gender: str
    dog_name: str
    parent: str
    trait: str
    seed: Optional[int] = None


CHILD_NAMES = {
    "girl": ["Lena", "Mia", "Ruby", "Nora", "Ava", "Ella"],
    "boy": ["Owen", "Max", "Theo", "Ben", "Eli", "Noah"],
}
DOG_NAMES = ["Pip", "Sunny", "Dot", "Bean", "Mochi", "Rex"]
TRAITS = ["careful", "gentle", "cheerful", "patient", "curious"]

CURATED = [
    StoryParams(
        setting="courtyard",
        fetch="ball",
        reflector="puddle",
        child_name="Lena",
        child_gender="girl",
        dog_name="Pip",
        parent="mother",
        trait="careful",
        seed=1,
    ),
    StoryParams(
        setting="park",
        fetch="ring",
        reflector="window",
        child_name="Max",
        child_gender="boy",
        dog_name="Sunny",
        parent="father",
        trait="cheerful",
        seed=2,
    ),
    StoryParams(
        setting="sidewalk",
        fetch="tennis_ball",
        reflector="metal_door",
        child_name="Ruby",
        child_gender="girl",
        dog_name="Bean",
        parent="mother",
        trait="gentle",
        seed=3,
    ),
]


def explain_rejection(setting_id: str, fetch_id: str, reflector_id: str) -> str:
    if fetch_id in FETCH_THINGS and not FETCH_THINGS[fetch_id].can_roll:
        return (
            f"(No story: {FETCH_THINGS[fetch_id].phrase} would only flop, so it would not roll "
            f"into the little honk-and-search turn that this world depends on. "
            f"Pick a fetch toy like ball, ring, or tennis_ball.)"
        )
    if reflector_id in REFLECTORS and not REFLECTORS[reflector_id].truly_reflective:
        return (
            f"(No story: {REFLECTORS[reflector_id].phrase} cannot honestly reflect a hidden toy, "
            f"so it cannot power the finding beat. Pick puddle, window, or metal_door.)"
        )
    if setting_id in SETTINGS and reflector_id in REFLECTORS:
        setting = SETTINGS[setting_id]
        if reflector_id not in setting.reflectors:
            choices = ", ".join(sorted(setting.reflectors))
            return (
                f"(No story: {setting.place} does not plausibly use {REFLECTORS[reflector_id].label} "
                f"for the reflective clue here. Try one of: {choices}.)"
            )
    return "(No story: this combination does not make a strong enough fetch-honk-reflect turn.)"


def setup_scene(world: World, setting: Setting, child: Entity, dog: Entity, parent: Entity,
                fetch: FetchThing, reflector: Reflector) -> None:
    child.memes["joy"] += 1
    dog.memes["joy"] += 1
    world.say(
        f"After snack time, {child.id} took {dog.id} and {fetch.phrase} down to {setting.place}. "
        f"{setting.opening}"
    )
    world.say(
        f"{parent.label_word.capitalize()} leaned on the fence and smiled while {dog.id} danced in little circles."
    )
    world.say(reflector.scene_text)
    world.say(
        f'"Fetch, {dog.id}, fetch!" {child.id} called. "{dog.id}, fetch! Fetch!" '
        f'And off {dog.pronoun()} ran across {setting.throw_area}.'
    )


def second_throw(world: World, child: Entity, dog: Entity, fetch: FetchThing) -> None:
    child.memes["joy"] += 1
    dog.memes["joy"] += 1
    world.say(
        f"{dog.id} brought the {fetch.label} back once, then twice, tail swishing so hard it seemed to wag the whole afternoon."
    )
    world.say(
        f'Again {child.id} laughed. "Fetch, {dog.id}, fetch!"'
    )


def risky_bounce(world: World, setting: Setting, child: Entity, dog: Entity, fetch: FetchThing) -> None:
    toy = world.get("toy")
    toy.meters["near_edge"] += 1
    toy.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But on the next toss, the {fetch.label} landed crooked. {fetch.bounce_text} "
        f"It rolled toward {setting.edge_area}."
    )
    world.say(
        f"{dog.id} sprang after it, and {child.id}'s smile snapped into a gasp."
    )


def honk_and_stop(world: World, setting: Setting, child: Entity, dog: Entity, parent: Entity) -> None:
    path = world.get("path")
    path.meters["honked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'From {setting.honker} came a warning: "Honk! Honk!"'
    )
    world.say(
        f'"{dog.id}, wait!" {child.id} cried. {dog.id} skidded to a stop, ears up, and '
        f'{parent.label_word} called out a quick, calm, "Good stopping."'
    )


def lose_toy(world: World, setting: Setting, child: Entity, fetch: FetchThing) -> None:
    toy = world.get("toy")
    toy.meters["hidden"] += 1
    world.say(
        f"The {fetch.label} did not roll into the lane after all. It bumped the edge, turned, and slipped {setting.hide_spot}."
    )
    world.say(
        f"For a moment, all {child.id} could see was shadow. {child.pronoun().capitalize()} felt the game go small and quiet inside {child.pronoun('object')}."
    )


def reflect_and_find(world: World, setting: Setting, child: Entity, dog: Entity,
                     fetch: FetchThing, reflector: Reflector) -> None:
    helper = world.get("reflector")
    helper.meters["glint"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} crouched low beside {reflector.phrase}. {reflector.reveal_text} "
        f'"I see it!" {child.pronoun()} said.'
    )
    world.say(
        f"{child.pronoun().capitalize()} reached carefully {setting.hide_spot} and pulled out the {fetch.color} {fetch.label}. "
        f"{dog.id} gave one happy bark and bounced in place."
    )


def move_to_safe_spot(world: World, setting: Setting, child: Entity, dog: Entity, parent: Entity,
                      fetch: FetchThing) -> None:
    child.memes["care"] += 1
    child.memes["joy"] += 1
    dog.memes["joy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside {child.id}. "The path is for wheels," '
        f'{parent.pronoun()} said softly. "Let\'s play fetch over at {setting.move_to} instead."'
    )
    world.say(
        f"{child.id} nodded. {child.pronoun().capitalize()} tucked the {fetch.label} close for one second, as if to reflect on the scare, then grinned again."
    )
    world.say(
        f"Soon the {fetch.label} was flying over {setting.move_to}, and {dog.id} was racing back and forth with safe, silly joy."
    )
    world.say(
        f'Again came the happy rhythm: "Fetch, {dog.id}, fetch!" This time the game stayed far from the path, and the afternoon ended with wagging, laughter, and the {fetch.label} safe in {child.id}\'s hands.'
    )


def tell(setting: Setting, fetch: FetchThing, reflector: Reflector,
         child_name: str = "Lena", child_gender: str = "girl",
         dog_name: str = "Pip", parent_type: str = "mother",
         trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    dog = world.add(Entity(
        id=dog_name,
        kind="character",
        type="dog",
        label=dog_name,
        role="dog",
        traits=["eager"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    toy = world.add(Entity(
        id="toy",
        type="toy",
        label=fetch.label,
        phrase=fetch.phrase,
        tags=set(fetch.tags),
    ))
    helper = world.add(Entity(
        id="reflector",
        type="reflector",
        label=reflector.label,
        phrase=reflector.phrase,
        tags=set(reflector.tags),
    ))
    world.add(Entity(
        id="path",
        type="path",
        label=setting.edge_area,
    ))

    setup_scene(world, setting, child, dog, parent, fetch, reflector)
    second_throw(world, child, dog, fetch)

    world.para()
    risky_bounce(world, setting, child, dog, fetch)
    honk_and_stop(world, setting, child, dog, parent)
    lose_toy(world, setting, child, fetch)

    world.para()
    reflect_and_find(world, setting, child, dog, fetch, reflector)
    move_to_safe_spot(world, setting, child, dog, parent, fetch)

    world.facts.update(
        setting=setting,
        fetch=fetch,
        reflector_cfg=reflector,
        child=child,
        dog=dog,
        parent=parent,
        toy=toy,
        found=toy.meters["found"] >= THRESHOLD,
        honked=world.get("path").meters["honked"] >= THRESHOLD,
        hidden_spot=setting.hide_spot,
        moved_to=setting.move_to,
    )
    return world


KNOWLEDGE = {
    "fetch": [
        (
            "What does fetch mean when you play with a dog?",
            "Fetch is a game where you throw a toy and the dog runs to get it and bring it back. Dogs often like it because they can chase, carry, and return the toy."
        )
    ],
    "honk": [
        (
            "What does a honk mean?",
            "A honk is a loud warning sound from something like a horn. It tells people to notice right away and be careful."
        )
    ],
    "reflect": [
        (
            "What does reflect mean?",
            "Reflect means to show an image back, like a puddle or window showing what is nearby. Shiny or smooth things can reflect light and help you see something from another angle."
        )
    ],
    "puddle": [
        (
            "Why can a puddle help you see something?",
            "If the water is still, a puddle can act like a tiny mirror. It can reflect shapes and colors that you might miss if you only look straight ahead."
        )
    ],
    "window": [
        (
            "How can a window act like a mirror?",
            "When light hits a bright window, some of it bounces back. That can make the glass reflect the world in front of it."
        )
    ],
    "path": [
        (
            "Why is it safer to play fetch away from a path or driveway?",
            "A path or driveway is where bikes, scooters, or cars may move through. Playing farther away gives everyone more room and more time to stop."
        )
    ],
}
KNOWLEDGE_ORDER = ["fetch", "honk", "reflect", "puddle", "window", "path"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    fetch = f["fetch"]
    setting = f["setting"]
    reflector = f["reflector_cfg"]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "fetch", "honk", and "reflect".',
        f"Tell a gentle story where {child.id} plays fetch with {dog.id} at {setting.place}, hears a sudden honk, and uses {reflector.phrase} to find a missing {fetch.label}.",
        f"Write a happy everyday story with repetition and sound effects, where a rolling toy causes a tiny scare but the game ends safely in a better place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    parent = f["parent"]
    setting = f["setting"]
    fetch = f["fetch"]
    reflector = f["reflector_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {dog.id}, and {child.id}'s {parent.label_word}. They are having a small everyday game together."
        ),
        (
            f"What were {child.id} and {dog.id} doing at the start?",
            f"They were playing fetch with {fetch.phrase} at {setting.place}. The game already had a happy rhythm because {dog.id} kept bringing the toy back."
        ),
        (
            "What made the story suddenly feel scary?",
            f"The {fetch.label} rolled toward {setting.edge_area}, and then they heard a loud honk. That sound warned them that the game had drifted too close to a place meant for wheels."
        ),
        (
            f"Why did the honk matter?",
            f"The honk made {child.id} call {dog.id} to stop, and {dog.id} did stop. Because they paused in time, the little scare stayed little."
        ),
        (
            f"How did {child.id} find the missing {fetch.label}?",
            f"{child.id} used {reflector.phrase} to look from a new angle and saw the toy reflect there. That bright clue showed where it had slipped {f['hidden_spot']}."
        ),
        (
            "How did the story end?",
            f"They moved the game to {f['moved_to']} and kept playing fetch safely. The ending is happy because the toy was found, the dog was safe, and the game changed in a wiser way."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fetch", "honk", "reflect", "path"}
    reflector = world.facts["reflector_cfg"]
    if reflector.id == "puddle":
        tags.add("puddle")
    if reflector.id == "window":
        tags.add("window")
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
rolls(F)       :- fetch(F), can_roll(F).
good_reflector(R) :- reflector(R), reflective(R).
valid(S, F, R) :- setting(S), rolls(F), good_reflector(R), affords(S, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for rid in sorted(setting.reflectors):
            lines.append(asp.fact("affords", sid, rid))
    for fid, fetch in FETCH_THINGS.items():
        lines.append(asp.fact("fetch", fid))
        if fetch.can_roll:
            lines.append(asp.fact("can_roll", fid))
    for rid, reflector in REFLECTORS.items():
        lines.append(asp.fact("reflector", rid))
        if reflector.truly_reflective:
            lines.append(asp.fact("reflective", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    smoke_cases = list(CURATED)
    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        smoke_cases.append(params)
    except StoryError as err:
        rc = 1
        print("SMOKE SETUP FAILED:", err)

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            print(f"OK: smoke story {i} generated ({params.setting}, {params.fetch}, {params.reflector}).")
        except Exception as err:
            rc = 1
            print(f"SMOKE GENERATION FAILED for {params}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a dog, fetch, a honk, and a reflective clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fetch", choices=FETCH_THINGS)
    ap.add_argument("--reflector", choices=REFLECTORS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--dog-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, fetch, reflector) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.fetch and args.reflector:
        if not valid_combo(args.setting, args.fetch, args.reflector):
            raise StoryError(explain_rejection(args.setting, args.fetch, args.reflector))
    if args.fetch and args.fetch in FETCH_THINGS and not FETCH_THINGS[args.fetch].can_roll:
        setting_id = args.setting or next(iter(SETTINGS))
        reflector_id = args.reflector or next(iter(REFLECTORS))
        raise StoryError(explain_rejection(setting_id, args.fetch, reflector_id))
    if args.reflector and args.reflector in REFLECTORS and not REFLECTORS[args.reflector].truly_reflective:
        setting_id = args.setting or next(iter(SETTINGS))
        fetch_id = args.fetch or next(iter(FETCH_THINGS))
        raise StoryError(explain_rejection(setting_id, fetch_id, args.reflector))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.fetch is None or combo[1] == args.fetch)
        and (args.reflector is None or combo[2] == args.reflector)
    ]
    if not combos:
        sid = args.setting or next(iter(SETTINGS))
        fid = args.fetch or next(iter(FETCH_THINGS))
        rid = args.reflector or next(iter(REFLECTORS))
        raise StoryError(explain_rejection(sid, fid, rid))

    setting_id, fetch_id, reflector_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES[gender])
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        fetch=fetch_id,
        reflector=reflector_id,
        child_name=child_name,
        child_gender=gender,
        dog_name=dog_name,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.fetch not in FETCH_THINGS:
        raise StoryError(f"(Invalid fetch toy: {params.fetch})")
    if params.reflector not in REFLECTORS:
        raise StoryError(f"(Invalid reflector: {params.reflector})")
    if not valid_combo(params.setting, params.fetch, params.reflector):
        raise StoryError(explain_rejection(params.setting, params.fetch, params.reflector))

    world = tell(
        setting=SETTINGS[params.setting],
        fetch=FETCH_THINGS[params.fetch],
        reflector=REFLECTORS[params.reflector],
        child_name=params.child_name,
        child_gender=params.child_gender,
        dog_name=params.dog_name,
        parent_type=params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, fetch, reflector) combos:\n")
        for setting_id, fetch_id, reflector_id in combos:
            print(f"  {setting_id:10} {fetch_id:12} {reflector_id}")
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
            header = f"### {p.child_name} and {p.dog_name}: {p.fetch} at {p.setting} with {p.reflector}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
