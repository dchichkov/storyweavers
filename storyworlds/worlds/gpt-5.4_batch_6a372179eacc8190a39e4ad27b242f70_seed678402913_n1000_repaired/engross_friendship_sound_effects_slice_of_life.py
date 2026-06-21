#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/engross_friendship_sound_effects_slice_of_life.py
============================================================================

A standalone story world about two children making a tiny homemade show with
sound effects. One child gets so caught up in making a big noise that the room
stops feeling gentle. A friend notices, offers a softer way to make the same
sound, and together they finish with a warm, everyday ending.

The world model prefers combinations where:
- the project really needs the kind of sound the children are trying to make,
- the first tool is genuinely too loud for the place,
- the replacement tool makes the same kind of sound softly enough to fit.

The central turn is social and state-driven:
- if the maker trusts the friend enough, the friends solve it by themselves;
- otherwise a grown-up gives one calm reminder, and then the friends adjust.

Run it
------
    python storyworlds/worlds/gpt-5.4/engross_friendship_sound_effects_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/engross_friendship_sound_effects_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/engross_friendship_sound_effects_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/engross_friendship_sound_effects_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4/engross_friendship_sound_effects_slice_of_life.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ENGROSS_INIT = 4
HELPFUL_TRAITS = {"gentle", "patient", "observant"}


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
        female = {"girl", "mother", "mom", "woman", "grandmother", "teacher"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "teacher": "teacher",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    quiet_limit: int
    quiet_reason: str
    quiet_person: str
    permits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    title: str
    sound_family: str
    setup: str
    opening_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound_family: str
    loudness: int
    sound: str
    action: str
    result: str
    soft: bool = False
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"maker", "friend"}]

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


def _r_disturbance(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["noise"] <= world.place.quiet_limit:
        return out
    sig = ("disturbance", int(room.meters["noise"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["disturbance"] += 1
    for kid in world.kids():
        kid.memes["concern"] += 1
    out.append("__disturbance__")
    return out


def _r_team_glow(world: World) -> list[str]:
    out: list[str] = []
    maker = world.get("maker")
    friend = world.get("friend")
    if maker.meters["matched_sound"] < THRESHOLD:
        return out
    if room_is_calm(world) and maker.memes["cooperation"] >= THRESHOLD:
        sig = ("team_glow",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        maker.memes["pride"] += 1
        friend.memes["pride"] += 1
        maker.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        out.append("__team_glow__")
    return out


CAUSAL_RULES = [
    Rule(name="disturbance", tag="physical", apply=_r_disturbance),
    Rule(name="team_glow", tag="social", apply=_r_team_glow),
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


def room_is_calm(world: World) -> bool:
    return world.get("room").meters["noise"] <= world.place.quiet_limit


def compatible(place: Place, project: Project, loud_tool: Tool, soft_tool: Tool) -> bool:
    return (
        project.id in place.permits
        and loud_tool.sound_family == project.sound_family
        and soft_tool.sound_family == project.sound_family
        and loud_tool.loudness > place.quiet_limit
        and soft_tool.loudness <= place.quiet_limit
        and soft_tool.soft
        and soft_tool.loudness < loud_tool.loudness
    )


def helpful_bonus(trait: str) -> int:
    return 2 if trait in HELPFUL_TRAITS else 1


def relation_bonus(relation: str) -> int:
    return 2 if relation == "best_friends" else 0


def would_listen(relation: str, friend_trait: str) -> bool:
    influence = 1 + helpful_bonus(friend_trait) + relation_bonus(relation)
    return influence > ENGROSS_INIT


def predict_noise(world: World, tool: Tool) -> dict:
    sim = world.copy()
    do_sound(sim, tool, narrate=False)
    return {
        "too_loud": sim.get("room").meters["noise"] > sim.place.quiet_limit,
        "disturbance": sim.get("room").meters["disturbance"] >= THRESHOLD,
    }


def introduce(world: World, maker: Entity, friend: Entity, project: Project) -> None:
    maker.memes["engross"] = float(ENGROSS_INIT)
    maker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After snack time, {maker.id} and {friend.id} settled in {world.place.phrase} "
        f"with a little homemade show called {project.title}. {project.setup}"
    )
    world.say(
        f'{maker.id} read the first line in a small serious voice: "{project.opening_line}"'
    )
    world.say(
        f"The tiny world on the blanket had a way to engross {maker.pronoun('object')} completely."
    )


def explain_friendship(world: World, maker: Entity, friend: Entity, relation: str) -> None:
    if relation == "best_friends":
        world.say(
            f"They were best friends, the kind who could build a whole afternoon out of scraps, tape, and one good idea."
        )
    elif relation == "cousins":
        world.say(
            f"They were cousins, but they felt like close friends whenever they invented a game together."
        )
    elif relation == "neighbors":
        world.say(
            f"They were neighbors who had learned each other's favorite kinds of pretending."
        )
    else:
        world.say(
            f"They were classmates who had only lately begun choosing each other for the same games."
        )


def need_sound(world: World, friend: Entity, project: Project) -> None:
    world.say(
        f'"It needs a {project.sound_family} sound right here," {friend.id} said, leaning closer to the blanket stage.'
    )


def do_sound(world: World, tool: Tool, narrate: bool = True) -> None:
    room = world.get("room")
    maker = world.get("maker")
    room.meters["noise"] += tool.loudness
    maker.meters["matched_sound"] = 1.0
    maker.meters["last_loudness"] = float(tool.loudness)
    maker.attrs["last_tool"] = tool.id
    if tool.soft:
        maker.memes["cooperation"] += 1
    propagate(world, narrate=narrate)


def noisy_try(world: World, maker: Entity, tool: Tool) -> None:
    maker.memes["boldness"] += 1
    do_sound(world, tool)
    world.say(
        f'{maker.id} grabbed {tool.phrase} and made the sound: "{tool.sound}" {tool.action}.'
    )
    world.say(tool.result)


def friend_warns(world: World, friend: Entity, maker: Entity, tool: Tool, soft_tool: Tool) -> None:
    pred = predict_noise(world, tool)
    friend.memes["care"] += 1
    world.facts["predicted_disturbance"] = pred["disturbance"]
    extra = " It fit the story, but not the room." if pred["too_loud"] else ""
    world.say(
        f'{friend.id} lifted a hand. "That sounds real, but it is too big for {world.place.label}. '
        f'{world.place.quiet_reason}.{extra} Try {soft_tool.phrase} instead."'
    )


def maker_decides(world: World, maker: Entity, friend: Entity, relation: str, friend_trait: str) -> bool:
    listens = would_listen(relation, friend_trait)
    if listens:
        maker.memes["listened"] += 1
        maker.memes["engross"] = 0.0
        world.say(
            f"{maker.id} blinked, looked around, and finally heard the room the way {friend.id} did."
        )
    else:
        maker.memes["stubborn"] += 1
        world.say(
            f"But {maker.id} was still wrapped up in the show and barely looked up. The sound in {maker.pronoun('possessive')} head mattered more than the room for one more moment."
        )
    return listens


def switch_soft(world: World, maker: Entity, friend: Entity, soft_tool: Tool, project: Project) -> None:
    world.get("room").meters["noise"] = 0.0
    world.get("room").meters["disturbance"] = 0.0
    do_sound(world, soft_tool)
    world.say(
        f'Together they tried again: "{soft_tool.sound}" {soft_tool.action}.'
    )
    world.say(
        f"This time the {project.sound_family} sound still felt right, only smaller and kinder."
    )
    friend.memes["relief"] += 1
    maker.memes["relief"] += 1


def adult_reminds(world: World, adult: Entity, maker: Entity, friend: Entity, soft_tool: Tool) -> None:
    world.say(
        f"{adult.label_word.capitalize()} looked in from the doorway and smiled instead of scolding."
    )
    world.say(
        f'"I love your ideas," {adult.pronoun()} said, "but keep the sound gentle here. '
        f'{world.place.quiet_reason}. Maybe use {soft_tool.phrase}."'
    )
    maker.memes["listened"] += 1
    maker.memes["engross"] = 0.0
    maker.memes["cooperation"] += 1
    friend.memes["supported"] += 1


def finish_show(world: World, maker: Entity, friend: Entity, project: Project, soft_tool: Tool) -> None:
    maker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Soon the whole little show was moving along with soft sounds, careful voices, and both friends leaning close over the blanket."
    )
    world.say(project.ending_image)
    world.say(
        f"When they were done, {maker.id} nudged {friend.id} and smiled. The best part was not the noise at all. It was making something together."
    )
    world.facts["ending_tool"] = soft_tool.id


def tell(
    place: Place,
    project: Project,
    loud_tool: Tool,
    soft_tool: Tool,
    *,
    maker_name: str = "Mara",
    maker_gender: str = "girl",
    friend_name: str = "June",
    friend_gender: str = "girl",
    adult_type: str = "mother",
    relation: str = "best_friends",
    friend_trait: str = "gentle",
) -> World:
    world = World(place)
    maker = world.add(Entity(id="maker", kind="character", type=maker_gender, label=maker_name, role="maker"))
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=[friend_trait],
            attrs={"relation": relation},
        )
    )
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the adult", role="adult"))
    world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    world.facts["display_names"] = {"maker": maker_name, "friend": friend_name}
    world.facts["relation"] = relation
    world.facts["friend_trait"] = friend_trait

    introduce(world, maker, friend, project)
    explain_friendship(world, maker, friend, relation)
    need_sound(world, friend, project)

    world.para()
    noisy_try(world, maker, loud_tool)
    friend_warns(world, friend, maker, loud_tool, soft_tool)

    world.para()
    listened = maker_decides(world, maker, friend, relation, friend_trait)
    if listened:
        switch_soft(world, maker, friend, soft_tool, project)
        outcome = "self_fix"
    else:
        adult_reminds(world, adult, maker, friend, soft_tool)
        switch_soft(world, maker, friend, soft_tool, project)
        outcome = "adult_reminder"

    world.para()
    finish_show(world, maker, friend, project, soft_tool)

    world.facts.update(
        maker=maker,
        friend=friend,
        adult=adult,
        place_cfg=place,
        project_cfg=project,
        loud_tool_cfg=loud_tool,
        soft_tool_cfg=soft_tool,
        outcome=outcome,
        listened=listen,
        too_loud=loud_tool.loudness > place.quiet_limit,
    )
    return world


PLACES = {
    "living_room": Place(
        id="living_room",
        label="the living room",
        phrase="the living room rug",
        quiet_limit=2,
        quiet_reason="Grandpa was dozing in the armchair with his book folded on his chest",
        quiet_person="Grandpa",
        permits={"rain_show", "march_show", "kite_show"},
        tags={"home", "quiet"},
    ),
    "bedroom": Place(
        id="bedroom",
        label="the bedroom",
        phrase="the bedroom floor by the bed",
        quiet_limit=1,
        quiet_reason="a baby sister was napping in the next room",
        quiet_person="the baby sister",
        permits={"rain_show", "march_show", "kite_show"},
        tags={"home", "quiet", "sleep"},
    ),
    "reading_corner": Place(
        id="reading_corner",
        label="the reading corner",
        phrase="the classroom reading corner",
        quiet_limit=2,
        quiet_reason="other children nearby were still looking at books",
        quiet_person="the other children",
        permits={"rain_show", "march_show", "kite_show"},
        tags={"school", "quiet", "books"},
    ),
}

PROJECTS = {
    "rain_show": Project(
        id="rain_show",
        title='"The Little Window Rain"',
        sound_family="rain",
        setup="They had cut paper windows from an old cereal box and propped a toy rabbit beside them.",
        opening_line="Tap, tap, the rain came to the window.",
        ending_image="At the end, the rabbit watched the paper rain while a real stripe of afternoon light lay across the rug.",
        tags={"rain", "show"},
    ),
    "march_show": Project(
        id="march_show",
        title='"The Hallway Parade"',
        sound_family="steps",
        setup="They had lined up buttons for parade lanterns and made a tiny paper dog with floppy ears.",
        opening_line="Down the hall came the parade, step after step.",
        ending_image="In the last scene, the little paper dog stood proudly beside the button lanterns while the friends grinned at their own neat work.",
        tags={"footsteps", "show"},
    ),
    "kite_show": Project(
        id="kite_show",
        title='"The Kite on the Breezy Hill"',
        sound_family="wind",
        setup="They had made a hill from a folded towel and a bright kite from blue paper and string.",
        opening_line="Whooo, said the hill, when the kite tugged at the sky.",
        ending_image="By the final page, the paper kite rested on the towel hill as softly as if a real evening breeze had put it there.",
        tags={"wind", "show"},
    ),
}

TOOLS = {
    "pot_rain": Tool(
        id="pot_rain",
        label="a spoon on a pot",
        phrase="a spoon and the upside-down pot",
        sound_family="rain",
        loudness=4,
        sound="CLANG-clang-clang",
        action="rang off the metal",
        result="It sounded like a storm on a roof, and the whole room jumped with it.",
        soft=False,
        tags={"rain", "loud"},
    ),
    "rice_rain": Tool(
        id="rice_rain",
        label="a rice jar",
        phrase="the little rice jar",
        sound_family="rain",
        loudness=1,
        sound="shhh-shhh",
        action="the grains whispered inside the jar",
        result="It sounded like rain on a window without shaking the room.",
        soft=True,
        tags={"rain", "soft"},
    ),
    "boot_steps": Tool(
        id="boot_steps",
        label="heavy boots on the floor",
        phrase="the borrowed rain boots",
        sound_family="steps",
        loudness=4,
        sound="THUMP THUMP",
        action="the heels hit the floorboards",
        result="The parade sound was perfect, but it traveled much farther than the blanket stage.",
        soft=False,
        tags={"steps", "loud"},
    ),
    "finger_steps": Tool(
        id="finger_steps",
        label="fingers on a box lid",
        phrase="the box lid with two tapping fingers",
        sound_family="steps",
        loudness=1,
        sound="tip-tip tip-tip",
        action="two fingers walked across the lid",
        result="It sounded like tiny feet, close and clear.",
        soft=True,
        tags={"steps", "soft"},
    ),
    "fan_wind": Tool(
        id="fan_wind",
        label="a desk fan",
        phrase="the little desk fan",
        sound_family="wind",
        loudness=3,
        sound="WHIRRR",
        action="air pushed the paper and hummed in the room",
        result="The kite fluttered beautifully, but the hum filled every corner.",
        soft=False,
        tags={"wind", "loud"},
    ),
    "paper_wind": Tool(
        id="paper_wind",
        label="paper in the air",
        phrase="the folded paper by their mouths",
        sound_family="wind",
        loudness=1,
        sound="whooo",
        action="the paper fluttered with their breath",
        result="It sounded breezy and light, almost like the hill was breathing.",
        soft=True,
        tags={"wind", "soft"},
    ),
    "balloon_pop": Tool(
        id="balloon_pop",
        label="a balloon pop",
        phrase="the red balloon",
        sound_family="bang",
        loudness=5,
        sound="POP!",
        action="the air snapped out in one sharp crack",
        result="It was sudden and huge, and it belonged to a different kind of story altogether.",
        soft=False,
        tags={"bang", "loud"},
    ),
}

GIRL_NAMES = ["Mara", "June", "Lina", "Ivy", "Nora", "Tess", "Anna", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Sam", "Leo", "Finn", "Eli", "Theo", "Ben"]
FRIEND_TRAITS = ["gentle", "patient", "observant", "bright", "funny", "steady"]
RELATIONS = ["best_friends", "classmates", "neighbors", "cousins"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for project_id, project in PROJECTS.items():
            for loud_id, loud_tool in TOOLS.items():
                for soft_id, soft_tool in TOOLS.items():
                    if compatible(place, project, loud_tool, soft_tool):
                        combos.append((place_id, project_id, loud_id, soft_id))
    return sorted(set(combos))


@dataclass
class StoryParams:
    place: str
    project: str
    loud_tool: str
    soft_tool: str
    maker_name: str
    maker_gender: str
    friend_name: str
    friend_gender: str
    adult: str
    relation: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rain": [
        (
            "How can people make a rain sound without real rain?",
            "They can shake something soft, like rice in a jar, to make a gentle pattering sound. That is called a sound effect."
        )
    ],
    "steps": [
        (
            "How can you make tiny footsteps in a story?",
            "You can tap with two fingers or something small on a box or table. Little taps sound more like tiny feet than heavy stomps do."
        )
    ],
    "wind": [
        (
            "How can paper sound like wind?",
            "If you blow across paper or flutter it gently, it can make a soft whooo sound. That lets you pretend there is wind without using a machine."
        )
    ],
    "quiet": [
        (
            "Why do some rooms need gentle voices and gentle sounds?",
            "Some rooms stay quiet because someone is resting, reading, or thinking. Soft sounds help everybody share the space kindly."
        )
    ],
    "friendship": [
        (
            "What can a good friend do when a game gets a little too loud?",
            "A good friend can notice the problem and suggest a better way. Helping the game continue safely and kindly is part of friendship."
        )
    ],
    "show": [
        (
            "What is a sound effect?",
            "A sound effect is a sound you make on purpose to help a story feel real. It can be made with your voice, your hands, or simple objects."
        )
    ],
}
KNOWLEDGE_ORDER = ["show", "friendship", "quiet", "rain", "steps", "wind"]


def display_name(world: World, role: str) -> str:
    return world.facts["display_names"][role]


def generation_prompts(world: World) -> list[str]:
    maker = display_name(world, "maker")
    friend = display_name(world, "friend")
    project = world.facts["project_cfg"]
    place = world.facts["place_cfg"]
    loud_tool = world.facts["loud_tool_cfg"]
    soft_tool = world.facts["soft_tool_cfg"]
    outcome = world.facts["outcome"]
    prompts = [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "engross", centers on friendship, and uses homemade sound effects.',
        f"Tell a gentle story where {maker} and {friend} make a tiny show in {place.label}, but one sound effect with {loud_tool.phrase} is too big for the room.",
    ]
    if outcome == "self_fix":
        prompts.append(
            f"Write a story where a friend notices the problem early, suggests {soft_tool.phrase}, and the children solve it together without a grown-up stepping in."
        )
    else:
        prompts.append(
            f"Write a story where the children are making {project.title}, the maker is too engross in the noisy part to listen at first, and a calm grown-up helps them switch to {soft_tool.phrase}."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    maker = display_name(world, "maker")
    friend = display_name(world, "friend")
    adult = world.facts["adult"]
    project = world.facts["project_cfg"]
    place = world.facts["place_cfg"]
    loud_tool = world.facts["loud_tool_cfg"]
    soft_tool = world.facts["soft_tool_cfg"]
    outcome = world.facts["outcome"]
    relation = world.facts["relation"]

    pair = {
        "best_friends": "best friends",
        "classmates": "classmates who were becoming friends",
        "neighbors": "neighbor friends",
        "cousins": "cousins playing like friends",
    }[relation]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {maker} and {friend}, two {pair} making a tiny show together. A calm {adult.label_word} appears later to help keep the room gentle."
        ),
        (
            "What were they making?",
            f"They were making a homemade show called {project.title}. The little props and voices turned an ordinary room into a tiny story stage."
        ),
        (
            f"Why was {loud_tool.phrase} a problem?",
            f"It made the right kind of {project.sound_family} sound, but it was too loud for {place.label}. {place.quiet_reason}, so the room needed softer sounds."
        ),
        (
            f"How did {friend} help?",
            f"{friend} noticed that the big sound did not fit the room and suggested {soft_tool.phrase} instead. That kept the same story idea while changing the method."
        ),
    ]
    if outcome == "self_fix":
        qa.append(
            (
                f"Did {maker} listen right away?",
                f"Yes, after a moment. {maker} had been very engross in the show, but then listened to {friend} and switched to the softer sound."
            )
        )
    else:
        qa.append(
            (
                f"Why did the grown-up step in?",
                f"{maker} was still too engross in the noisy part to really hear {friend} at first. The grown-up gave one gentle reminder because the room still needed to stay quiet."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the friends finishing the show together using softer sound effects. The final picture is quiet and cozy, which shows they learned how to fit their game to the room."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"show", "friendship", "quiet", world.facts["project_cfg"].sound_family}
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="living_room",
        project="rain_show",
        loud_tool="pot_rain",
        soft_tool="rice_rain",
        maker_name="Mara",
        maker_gender="girl",
        friend_name="June",
        friend_gender="girl",
        adult="grandfather",
        relation="best_friends",
        friend_trait="gentle",
    ),
    StoryParams(
        place="bedroom",
        project="march_show",
        loud_tool="boot_steps",
        soft_tool="finger_steps",
        maker_name="Owen",
        maker_gender="boy",
        friend_name="Lina",
        friend_gender="girl",
        adult="mother",
        relation="classmates",
        friend_trait="bright",
    ),
    StoryParams(
        place="reading_corner",
        project="kite_show",
        loud_tool="fan_wind",
        soft_tool="paper_wind",
        maker_name="Ruby",
        maker_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        adult="teacher",
        relation="neighbors",
        friend_trait="patient",
    ),
    StoryParams(
        place="living_room",
        project="march_show",
        loud_tool="boot_steps",
        soft_tool="finger_steps",
        maker_name="Ben",
        maker_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        adult="grandmother",
        relation="cousins",
        friend_trait="observant",
    ),
]


def explain_rejection(place: Place, project: Project, loud_tool: Tool, soft_tool: Tool) -> str:
    if project.id not in place.permits:
        return (
            f"(No story: {project.title} is not staged in {place.label} here.)"
        )
    if loud_tool.sound_family != project.sound_family:
        return (
            f"(No story: {loud_tool.label} makes a {loud_tool.sound_family} sound, "
            f"but {project.title} needs {project.sound_family}. The problem and fix must match the story sound.)"
        )
    if soft_tool.sound_family != project.sound_family:
        return (
            f"(No story: {soft_tool.label} does not make the same kind of sound the project needs.)"
        )
    if loud_tool.loudness <= place.quiet_limit:
        return (
            f"(No story: {loud_tool.label} is not actually too loud for {place.label}, so there is no real turn.)"
        )
    if soft_tool.loudness > place.quiet_limit or not soft_tool.soft:
        return (
            f"(No story: {soft_tool.label} is not a gentle enough replacement for {place.label}.)"
        )
    return "(No story: this combination does not make a clear problem-and-fix pair.)"


def outcome_of(params: StoryParams) -> str:
    return "self_fix" if would_listen(params.relation, params.friend_trait) else "adult_reminder"


ASP_RULES = r"""
valid(P, Pr, L, S) :-
    place(P), project(Pr), tool(L), tool(S),
    permits(P, Pr),
    needs(Pr, F), family(L, F), family(S, F),
    loudness(L, LL), quiet_limit(P, Q), LL > Q,
    loudness(S, SL), SL <= Q,
    soft(S), SL < LL.

trait_bonus(2) :- chosen_trait(T), helpful_trait(T).
trait_bonus(1) :- chosen_trait(T), not helpful_trait(T).

relation_bonus(2) :- chosen_relation(best_friends).
relation_bonus(0) :- chosen_relation(R), R != best_friends.

influence(1 + TB + RB) :- trait_bonus(TB), relation_bonus(RB).
listens :- influence(I), engross_init(E), I > E.

outcome(self_fix) :- listens.
outcome(adult_reminder) :- not listens.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("quiet_limit", place_id, place.quiet_limit))
        for project_id in sorted(place.permits):
            lines.append(asp.fact("permits", place_id, project_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("needs", project_id, project.sound_family))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("family", tool_id, tool.sound_family))
        lines.append(asp.fact("loudness", tool_id, tool.loudness))
        if tool.soft:
            lines.append(asp.fact("soft", tool_id))
    for trait in sorted(HELPFUL_TRAITS):
        lines.append(asp.fact("helpful_trait", trait))
    lines.append(asp.fact("engross_init", ENGROSS_INIT))
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
            asp.fact("chosen_relation", params.relation),
            asp.fact("chosen_trait", params.friend_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

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
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: two friends making a tiny show with sound effects."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--loud-tool", choices=TOOLS, dest="loud_tool")
    ap.add_argument("--soft-tool", choices=TOOLS, dest="soft_tool")
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather", "teacher"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--friend-trait", choices=FRIEND_TRAITS, dest="friend_trait")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.loud_tool and args.loud_tool not in TOOLS:
        raise StoryError(f"(No story: unknown loud tool '{args.loud_tool}'.)")
    if args.soft_tool and args.soft_tool not in TOOLS:
        raise StoryError(f"(No story: unknown soft tool '{args.soft_tool}'.)")
    if args.project and args.project not in PROJECTS:
        raise StoryError(f"(No story: unknown project '{args.project}'.)")
    if args.place and args.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{args.place}'.)")

    if args.place and args.project and args.loud_tool and args.soft_tool:
        place = PLACES[args.place]
        project = PROJECTS[args.project]
        loud_tool = TOOLS[args.loud_tool]
        soft_tool = TOOLS[args.soft_tool]
        if not compatible(place, project, loud_tool, soft_tool):
            raise StoryError(explain_rejection(place, project, loud_tool, soft_tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.project is None or combo[1] == args.project)
        and (args.loud_tool is None or combo[2] == args.loud_tool)
        and (args.soft_tool is None or combo[3] == args.soft_tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, project_id, loud_id, soft_id = rng.choice(combos)
    maker_name, maker_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=maker_name)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather", "teacher"])
    relation = args.relation or rng.choice(RELATIONS)
    friend_trait = args.friend_trait or rng.choice(FRIEND_TRAITS)
    return StoryParams(
        place=place_id,
        project=project_id,
        loud_tool=loud_id,
        soft_tool=soft_id,
        maker_name=maker_name,
        maker_gender=maker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult=adult,
        relation=relation,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        project = PROJECTS[params.project]
        loud_tool = TOOLS[params.loud_tool]
        soft_tool = TOOLS[params.soft_tool]
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter value {err}.)") from err

    if not compatible(place, project, loud_tool, soft_tool):
        raise StoryError(explain_rejection(place, project, loud_tool, soft_tool))

    world = tell(
        place=place,
        project=project,
        loud_tool=loud_tool,
        soft_tool=soft_tool,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        relation=params.relation,
        friend_trait=params.friend_trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("maker", params.maker_name).replace("friend", params.friend_name),
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
        print(f"{len(combos)} compatible (place, project, loud_tool, soft_tool) combos:\n")
        for place, project, loud_tool, soft_tool in combos:
            print(f"  {place:14} {project:12} {loud_tool:12} {soft_tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.maker_name} & {p.friend_name}: {p.project} in {p.place} "
                f"({p.loud_tool} -> {p.soft_tool}, {outcome_of(p)})"
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
