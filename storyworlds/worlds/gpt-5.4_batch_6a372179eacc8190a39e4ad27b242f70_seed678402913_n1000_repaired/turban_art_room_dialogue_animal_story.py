#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py
===================================================================

A standalone story world about little animals in an art room. One child is
wearing a dress-up turban while making art and wants something from a high
shelf to finish the picture. A friend warns about an unsafe climb, a teacher
helps in a safer way, and the ending proves what changed.

The core world model is small and concrete:

- typed entities with physical meters and emotional memes
- a short forward-chaining causal engine
- a reasonableness gate for valid project/support/response combinations
- an inline ASP twin for the same gate and the story outcome model
- three Q&A sets generated from world state, not by parsing the prose

Run it
------
    python storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py
    python storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/turban_art_room_dialogue_animal_story.py --verify
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
SENSE_MIN = 2
EAGER_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    unstable: bool = False
    wearable: bool = False
    high_up: bool = False
    reachable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher_female", "hen", "goat", "cat", "sheep"}
        male = {"boy", "father", "teacher_male", "fox", "bear", "badger", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "teacher_female": "teacher",
            "teacher_male": "teacher",
            "mother": "mom",
            "father": "dad",
        }
        return mapping.get(self.type, self.type)


@dataclass
class Project:
    id: str
    art_name: str
    opening: str
    ending: str
    need_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShelfItem:
    id: str
    label: str
    phrase: str
    finish_line: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Support:
    id: str
    label: str
    phrase: str
    unstable: bool
    wobble_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TurbanStyle:
    id: str
    phrase: str
    color: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    support = world.get("support")
    if hero.meters["climbing"] >= THRESHOLD and hero.meters["stretching"] >= THRESHOLD and support.unstable:
        sig = ("wobble", support.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["wobble"] += 1
            hero.memes["fear"] += 1
            world.get("friend").memes["fear"] += 1
            world.get("room").meters["danger"] += 1
            out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if hero.meters["wobble"] >= THRESHOLD:
        sig = ("drop", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["fallen"] += 1
            world.get("room").meters["mess"] += 1
            out.append("__drop__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
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
        for s in produced:
            world.say(s)
    return produced


def project_needs_item(project: Project, item: ShelfItem) -> bool:
    return bool(project.tags & item.tags)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, friend_age: int, trait: str) -> bool:
    older_friend = relation == "classmates" and friend_age > hero_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_friend else 0.0)
    return older_friend and authority > EAGER_INIT


def contained(response: Response) -> bool:
    return response.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, project in PROJECTS.items():
        for iid, item in ITEMS.items():
            for sid, support in SUPPORTS.items():
                if project_needs_item(project, item) and support.unstable:
                    combos.append((pid, iid, sid))
    return combos


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["climbing"] += 1
    hero.meters["stretching"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": hero.meters["wobble"] >= THRESHOLD,
        "fallen": sim.get("item").meters["fallen"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, hero: Entity, friend: Entity, project: Project, turban: TurbanStyle) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the art room, {hero.id} the {hero.type} and {friend.id} the {friend.type} "
        f"were working side by side. {hero.id} had tied on {turban.phrase}, and it made "
        f"{hero.pronoun('object')} feel ready for a grand picture."
    )
    world.say(project.opening)


def need_item(world: World, hero: Entity, project: Project, item: ShelfItem) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f"Soon {hero.id} stepped back and blinked at the page. "
        f'"It still needs something," {hero.pronoun()} said. {project.need_line}'
    )
    world.say(
        f"On the highest shelf sat {item.phrase}. {item.finish_line}"
    )


def tempt(world: World, hero: Entity, support: Support) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f'{hero.id} looked at {support.phrase}. "I can climb up there," {hero.pronoun()} said.'
    )


def warn(world: World, hero: Entity, friend: Entity, support: Support) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_danger"] = pred["danger"]
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} twitched {friend.pronoun("possessive")} whiskers. '
        f'"Please do not climb on {support.phrase}," {friend.pronoun()} said. '
        f'"{support.label.capitalize()} can wobble, and the shelf is too high."'
    )


def back_down(world: World, hero: Entity, friend: Entity, teacher: Entity) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{hero.id} looked up, then down at {friend.id}. '
        f'"You are right," {hero.pronoun()} said softly. "I do not want to tumble."'
    )
    world.say(
        f'Together they called, "{teacher.label_word.capitalize()}, can you help us, please?"'
    )


def climb_and_wobble(world: World, hero: Entity, friend: Entity, support: Support, item: ShelfItem) -> None:
    hero.meters["climbing"] += 1
    hero.meters["stretching"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {hero.id} was too eager to wait. {hero.pronoun().capitalize()} put one paw on '
        f'{support.phrase}, climbed up, and stretched toward {item.label}.'
    )
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(support.wobble_line)
    if item.meters["fallen"] >= THRESHOLD:
        world.say(
            f"The {item.label} slipped with a soft clatter, and little bits scattered across the floor."
        )
    world.say(
        f'"Oh!" cried {hero.id}. "{friend.id}, it is wobbling!"'
    )


def teacher_arrives(world: World, teacher: Entity, response: Response, hero: Entity, friend: Entity, item: ShelfItem) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.meters["climbing"] = 0.0
    hero.meters["stretching"] = 0.0
    hero.meters["wobble"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{teacher.label_word.capitalize()} came quickly but calmly. "
        f"{teacher.pronoun().capitalize()} {response.text}"
    )
    world.say(
        f'Soon {item.use_line} was resting safely beside the paper. '
        f'"High shelves are for grown-up help," {teacher.pronoun()} said.'
    )


def gentle_lesson(world: World, teacher: Entity, hero: Entity, friend: Entity, support: Support) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'"You were trying hard to finish something lovely," {teacher.pronoun()} told them, '
        f'"but {support.label} is not a ladder."'
    )
    world.say(
        f'"Next time," said {friend.id}, "we can ask first." '
        f'"Yes," said {hero.id}. "That is the better plan."'
    )


def finish_art(world: World, hero: Entity, friend: Entity, project: Project, item: ShelfItem, turban: TurbanStyle) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then the two little artists went back to work. {hero.id} added {item.label} to the picture, "
        f"and {friend.id} helped smooth the corners."
    )
    world.say(
        f"When they were done, the page gleamed. In the picture, a smiling animal in {turban.color} "
        f"turban cloth stood proudly in {project.ending}."
    )


def tell(
    project: Project,
    item_cfg: ShelfItem,
    support_cfg: Support,
    response: Response,
    turban: TurbanStyle,
    hero_name: str = "Mira",
    hero_species: str = "mouse",
    friend_name: str = "Pip",
    friend_species: str = "rabbit",
    teacher_type: str = "teacher_female",
    trait: str = "careful",
    hero_age: int = 5,
    friend_age: int = 6,
    relation: str = "classmates",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_species, label=hero_name, role="hero", age=hero_age))
    friend = world.add(Entity(id="friend", kind="character", type=friend_species, label=friend_name, role="friend", age=friend_age, traits=[trait]))
    teacher = world.add(Entity(id="teacher", kind="character", type=teacher_type, label="the teacher", role="teacher"))
    room = world.add(Entity(id="room", type="room", label="the art room"))
    item = world.add(Entity(id="item", type="item", label=item_cfg.label, phrase=item_cfg.phrase, high_up=True, tags=set(item_cfg.tags)))
    support = world.add(Entity(id="support", type="support", label=support_cfg.label, phrase=support_cfg.phrase, unstable=support_cfg.unstable, tags=set(support_cfg.tags)))
    costume = world.add(Entity(id="turban", type="costume", label="turban", phrase=turban.phrase, wearable=True, tags=set(turban.tags)))

    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name

    introduce(world, hero, friend, project, turban)
    need_item(world, hero, project, item_cfg)

    world.para()
    tempt(world, hero, support_cfg)
    warn(world, hero, friend, support_cfg)

    averted = would_avert(relation, hero_age, friend_age, trait)
    if averted:
        back_down(world, hero, friend, teacher)
        world.para()
        teacher_arrives(world, teacher, response, hero, friend, item_cfg)
        gentle_lesson(world, teacher, hero, friend, support_cfg)
        world.para()
        finish_art(world, hero, friend, project, item_cfg, turban)
        outcome = "averted"
    else:
        climb_and_wobble(world, hero, friend, support_cfg, item_cfg)
        world.para()
        teacher_arrives(world, teacher, response, hero, friend, item_cfg)
        gentle_lesson(world, teacher, hero, friend, support_cfg)
        world.para()
        finish_art(world, hero, friend, project, item_cfg, turban)
        outcome = "rescued"

    world.facts.update(
        hero=hero,
        friend=friend,
        teacher=teacher,
        room=room,
        item_cfg=item_cfg,
        support_cfg=support_cfg,
        response=response,
        project=project,
        turban=turban,
        averted=averted,
        outcome=outcome,
        relation=relation,
        predicted_danger=world.facts.get("predicted_danger", 0),
        fell=item.meters["fallen"] >= THRESHOLD,
        lesson=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


PROJECTS = {
    "portrait": Project(
        id="portrait",
        art_name="portrait",
        opening="They were making a royal portrait for the wall of finished art.",
        ending="a frame of swirls and tiny painted lamps",
        need_line='A royal picture needs something bright near the top.',
        tags={"shiny", "royal"},
    ),
    "poster": Project(
        id="poster",
        art_name="poster",
        opening="They were making a welcome poster for the art room door.",
        ending="a border of curls and bright little stars",
        need_line='The poster needs one shining piece to make the middle glow.',
        tags={"shiny", "feather"},
    ),
    "collage": Project(
        id="collage",
        art_name="collage",
        opening="They were making a story collage about a brave traveler and a market day.",
        ending="a paper town under a soft evening sky",
        need_line='The collage needs one last special piece so the costume can stand out.',
        tags={"royal", "soft"},
    ),
}

ITEMS = {
    "gold_stars": ShelfItem(
        id="gold_stars",
        label="gold paper stars",
        phrase="a sheet of gold paper stars",
        finish_line="A few of them would make the picture shine at once.",
        use_line="the gold stars",
        tags={"shiny"},
    ),
    "feather_trim": ShelfItem(
        id="feather_trim",
        label="feather trim",
        phrase="a loop of feather trim",
        finish_line="Its soft edge would make the picture look grand and playful.",
        use_line="the feather trim",
        tags={"feather", "soft"},
    ),
    "jewel_stickers": ShelfItem(
        id="jewel_stickers",
        label="jewel stickers",
        phrase="a strip of jewel stickers",
        finish_line="They looked like tiny treasure drops for a splendid costume.",
        use_line="the jewel stickers",
        tags={"royal", "shiny"},
    ),
}

SUPPORTS = {
    "rolling_stool": Support(
        id="rolling_stool",
        label="rolling stool",
        phrase="the rolling stool",
        unstable=True,
        wobble_line="The rolling stool skittered a little, and every wheel whispered across the floor.",
        tags={"stool", "unstable"},
    ),
    "supply_cart": Support(
        id="supply_cart",
        label="supply cart",
        phrase="the supply cart",
        unstable=True,
        wobble_line="The supply cart rocked under the small paws, and the jars on its shelf rattled together.",
        tags={"cart", "unstable"},
    ),
    "paint_boxes": Support(
        id="paint_boxes",
        label="stacked paint boxes",
        phrase="the stacked paint boxes",
        unstable=True,
        wobble_line="The paint boxes squished sideways, and the whole little pile leaned like a tired tower.",
        tags={"boxes", "unstable"},
    ),
    "step_ladder": Support(
        id="step_ladder",
        label="step ladder",
        phrase="the step ladder",
        unstable=False,
        wobble_line="",
        tags={"ladder", "stable"},
    ),
}

RESPONSES = {
    "teacher_ladder": Response(
        id="teacher_ladder",
        sense=3,
        power=2,
        text="brought over the step ladder, lifted the item down, and set all four feet of the ladder squarely on the floor.",
        qa_text="used the step ladder and brought the art item down safely",
        fail_text="hurried over too late to stop the wobble",
        tags={"ladder", "ask_teacher"},
    ),
    "teacher_reacher": Response(
        id="teacher_reacher",
        sense=2,
        power=1,
        text="used the long reacher from the cupboard, hooked the item gently, and lowered it into waiting paws.",
        qa_text="used a long reacher to lower the art item safely",
        fail_text="could not reach it in time",
        tags={"reacher", "ask_teacher"},
    ),
    "jump_for_it": Response(
        id="jump_for_it",
        sense=1,
        power=0,
        text="told the children to hop higher",
        qa_text="told them to jump",
        fail_text="made the risk worse",
        tags={"unsafe"},
    ),
}

TURBANS = {
    "blue": TurbanStyle(id="blue", phrase="a soft blue turban made from dress-up cloth", color="blue", tags={"turban"}),
    "gold": TurbanStyle(id="gold", phrase="a golden turban with a tiny cloth jewel", color="golden", tags={"turban"}),
    "striped": TurbanStyle(id="striped", phrase="a striped turban that flopped a little at one side", color="striped", tags={"turban"}),
}

ANIMALS = {
    "mouse": {"names": ["Mira", "Mimi", "Nip", "Tilly"], "traits": ["quick", "bright"]},
    "rabbit": {"names": ["Pip", "Hoppy", "Moss", "Junie"], "traits": ["careful", "gentle"]},
    "fox": {"names": ["Fern", "Rory", "Tav"], "traits": ["clever", "steady"]},
    "badger": {"names": ["Bram", "Dot", "Nell"], "traits": ["patient", "thoughtful"]},
    "cat": {"names": ["Saffy", "Purl", "Milo"], "traits": ["graceful", "curious"]},
}

TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "brave"]


@dataclass
class StoryParams:
    project: str
    item: str
    support: str
    response: str
    turban: str
    hero_name: str
    hero_species: str
    friend_name: str
    friend_species: str
    teacher: str
    trait: str
    hero_age: int = 5
    friend_age: int = 6
    relation: str = "classmates"
    seed: Optional[int] = None


KNOWLEDGE = {
    "turban": [
        (
            "What is a turban?",
            "A turban is a long piece of cloth wrapped around a person's or character's head. In dress-up play, it can be part of a costume for a story or picture."
        )
    ],
    "art_room": [
        (
            "What do people do in an art room?",
            "People paint, draw, cut paper, glue shapes, and make many kinds of pictures there. An art room is for making things carefully with tools and supplies."
        )
    ],
    "stool": [
        (
            "Why can a rolling stool be unsafe to climb on?",
            "A rolling stool has wheels, so it can slide when someone stands on it. That makes it easy to wobble or fall."
        )
    ],
    "cart": [
        (
            "Why should you not climb on a supply cart?",
            "A supply cart can roll or tip when weight shifts on it. Art jars and tools can fall too."
        )
    ],
    "ladder": [
        (
            "What is a step ladder for?",
            "A step ladder helps a grown-up reach something high in a steady way. It is made to stand flat and hold weight better than a stool or cart."
        )
    ],
    "reacher": [
        (
            "What is a reacher?",
            "A reacher is a long tool that helps someone pick up or pull down something from far away. It lets a grown-up get a high item without climbing so much."
        )
    ],
    "ask_teacher": [
        (
            "What should a child do if art supplies are too high to reach?",
            "The child should stop and ask a teacher or another grown-up for help. Asking first is safer than climbing on something wobbly."
        )
    ],
}

KNOWLEDGE_ORDER = ["turban", "art_room", "stool", "cart", "ladder", "reacher", "ask_teacher"]


def pair_noun(hero: Entity, friend: Entity) -> str:
    return f"a {hero.type} and a {friend.type}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    project = f["project"]
    item = f["item_cfg"]
    turban = f["turban"]
    if f["outcome"] == "averted":
        return [
            f'Write a gentle animal story set in an art room that includes the word "turban" and uses dialogue.',
            f"Tell a story about {hero.label} the {hero.type}, who is wearing {turban.phrase} while making a {project.art_name}, and listens when {friend.label} warns about a high shelf.",
            f"Write a child-facing story where two little animals ask a teacher for help instead of climbing for {item.label}."
        ]
    return [
        f'Write a gentle animal story set in an art room that includes the word "turban" and uses dialogue.',
        f"Tell a story about {hero.label} the {hero.type}, who is wearing {turban.phrase} while making a {project.art_name}, tries to climb for {item.label}, and then learns a safer way.",
        f"Write a story where dialogue helps two animal friends solve a problem with a high art shelf."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    teacher = f["teacher"]
    project = f["project"]
    item = f["item_cfg"]
    support = f["support_cfg"]
    response = f["response"]
    turban = f["turban"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} the {hero.type} and {friend.label} the {friend.type} in the art room. Their teacher helps them when the shelf problem feels bigger than their small paws."
        ),
        (
            "Why was the turban in the story?",
            f"{hero.label} was wearing {turban.phrase} as part of the art-room costume idea. The turban helped the picture feel royal and playful."
        ),
        (
            f"What did {hero.label} want from the high shelf?",
            f"{hero.label} wanted {item.label} to finish the {project.art_name}. That bright art piece felt like the last thing the picture needed."
        ),
        (
            f"Why did {friend.label} warn {hero.label}?",
            f"{friend.label} warned {hero.label} because {support.label} could wobble under climbing paws. The shelf was high, so a small slip could make both the child and the art supplies tumble."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after the warning?",
                f"{hero.label} listened and stopped before climbing. Then both little animals asked the teacher for help, which kept the room calm and safe."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} climbed?",
                f"{hero.label} climbed onto {support.phrase}, and it began to wobble. That shaky moment frightened the children and made the art item fall before the teacher stepped in."
            )
        )
    qa.append(
        (
            "How did the teacher solve the problem?",
            f"The teacher {response.qa_text}. The grown-up help fixed the problem without more wobbling or grabbing."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the animals finishing their picture together in the art room. The bright final picture showed that they had changed from hurrying alone to asking for safe help."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"turban", "art_room", "ask_teacher"}
    support = f["support_cfg"]
    if "stool" in support.tags:
        tags.add("stool")
    if "cart" in support.tags:
        tags.add("cart")
    if "ladder" in f["response"].tags:
        tags.add("ladder")
    if "reacher" in f["response"].tags:
        tags.add("reacher")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.unstable:
            bits.append("unstable=True")
        if ent.high_up:
            bits.append("high_up=True")
        if ent.wearable:
            bits.append("wearable=True")
        if ent.age:
            bits.append(f"age={ent.age}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="portrait",
        item="jewel_stickers",
        support="rolling_stool",
        response="teacher_ladder",
        turban="gold",
        hero_name="Mira",
        hero_species="mouse",
        friend_name="Pip",
        friend_species="rabbit",
        teacher="teacher_female",
        trait="careful",
        hero_age=5,
        friend_age=7,
        relation="classmates",
    ),
    StoryParams(
        project="poster",
        item="feather_trim",
        support="supply_cart",
        response="teacher_reacher",
        turban="blue",
        hero_name="Fern",
        hero_species="fox",
        friend_name="Dot",
        friend_species="badger",
        teacher="teacher_male",
        trait="thoughtful",
        hero_age=6,
        friend_age=6,
        relation="classmates",
    ),
    StoryParams(
        project="collage",
        item="gold_stars",
        support="paint_boxes",
        response="teacher_ladder",
        turban="striped",
        hero_name="Saffy",
        hero_species="cat",
        friend_name="Junie",
        friend_species="rabbit",
        teacher="teacher_female",
        trait="steady",
        hero_age=5,
        friend_age=6,
        relation="classmates",
    ),
]


def explain_rejection(project: Project, item: ShelfItem, support: Support) -> str:
    if not project_needs_item(project, item):
        return (
            f"(No story: {item.label} does not fit the chosen {project.art_name}. "
            f"The high-shelf object should honestly help finish the art.)"
        )
    if not support.unstable:
        return (
            f"(No story: {support.label} is already a stable way to reach up, so there is no unsafe climb to warn about. "
            f"Pick a wobblier support such as a rolling stool or supply cart.)"
        )
    return "(No story: this combination does not create a clear, reasonable problem.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    options = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too low-sense for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {options}.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
needs(P, I) :- project_tag(P, T), item_tag(I, T).
hazard(P, I, S) :- project(P), item(I), support(S), needs(P, I), unstable(S).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
valid(P, I, S) :- hazard(P, I, S).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_friend :- relation(classmates), hero_age(H), friend_age(F), F > H.
bonus(3) :- older_friend.
bonus(0) :- not older_friend.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_friend, authority(A), eager_init(E), A > E.

contained :- chosen_response(R), power(R, P), P >= 1.
outcome(averted) :- averted.
outcome(rescued) :- not averted, contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        for tag in sorted(project.tags):
            lines.append(asp.fact("project_tag", pid, tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for sid, support in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        if support.unstable:
            lines.append(asp.fact("unstable", sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("eager_init", int(EAGER_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.friend_age, params.trait):
        return "averted"
    return "rescued" if contained(RESPONSES[params.response]) else "?"


def _smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


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

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and emitted a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal art-room story world with a turban, dialogue, and a safe-help lesson."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--turban", choices=TURBANS)
    ap.add_argument("--teacher", choices=["teacher_female", "teacher_male"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_animal(rng: random.Random, avoid_name: str = "", avoid_species: str = "") -> tuple[str, str]:
    species = rng.choice(sorted(ANIMALS))
    names = [n for n in ANIMALS[species]["names"] if n != avoid_name]
    if species == avoid_species:
        alt_species = [s for s in sorted(ANIMALS) if s != avoid_species]
        species = rng.choice(alt_species)
        names = list(ANIMALS[species]["names"])
    return rng.choice(names), species


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.item and args.support:
        project = PROJECTS[args.project]
        item = ITEMS[args.item]
        support = SUPPORTS[args.support]
        if not (project_needs_item(project, item) and support.unstable):
            raise StoryError(explain_rejection(project, item, support))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.item is None or combo[1] == args.item)
        and (args.support is None or combo[2] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, item_id, support_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    turban_id = args.turban or rng.choice(sorted(TURBANS))
    hero_name, hero_species = _pick_animal(rng)
    friend_name, friend_species = _pick_animal(rng, avoid_name=hero_name, avoid_species=hero_species)
    teacher = args.teacher or rng.choice(["teacher_female", "teacher_male"])
    trait = rng.choice(TRAITS)
    hero_age, friend_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        project=project_id,
        item=item_id,
        support=support_id,
        response=response_id,
        turban=turban_id,
        hero_name=hero_name,
        hero_species=hero_species,
        friend_name=friend_name,
        friend_species=friend_species,
        teacher=teacher,
        trait=trait,
        hero_age=hero_age,
        friend_age=friend_age,
        relation="classmates",
    )


def _check_params(params: StoryParams) -> None:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.turban not in TURBANS:
        raise StoryError(f"(Unknown turban: {params.turban})")
    project = PROJECTS[params.project]
    item = ITEMS[params.item]
    support = SUPPORTS[params.support]
    response = RESPONSES[params.response]
    if not (project_needs_item(project, item) and support.unstable):
        raise StoryError(explain_rejection(project, item, support))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        project=PROJECTS[params.project],
        item_cfg=ITEMS[params.item],
        support_cfg=SUPPORTS[params.support],
        response=RESPONSES[params.response],
        turban=TURBANS[params.turban],
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        friend_name=params.friend_name,
        friend_species=params.friend_species,
        teacher_type=params.teacher,
        trait=params.trait,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, item, support) combos:\n")
        for project, item, support in combos:
            print(f"  {project:8} {item:14} {support}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} the {p.hero_species}: {p.project}, {p.item}, {p.support} ({outcome_of(p)})"
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
