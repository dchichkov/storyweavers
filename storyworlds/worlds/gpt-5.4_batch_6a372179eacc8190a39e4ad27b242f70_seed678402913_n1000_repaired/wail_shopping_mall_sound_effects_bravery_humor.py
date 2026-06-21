#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py
==============================================================================

A standalone story world for a tiny mall adventure built from the seed:
"wail", shopping mall, sound effects, bravery, humor, adventure.

Premise
-------
Two children hear a spooky wail somewhere in a shopping mall. One child decides
to be brave, but the world refuses silly solutions: the sound must fit the
place, and the helper/tactic must actually make sense for that kind of problem.
The turn comes when the children investigate with a sensible grown-up and learn
that the "monster" noise has a funny, harmless cause. The ending image proves
what changed: fear turns into laughter, and the mall sounds friendly again.

Run it
------
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py --place atrium --source balloon_vent
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py --source robot_jingle --helper toy_clerk
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py --source balloon_vent --helper janitor
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py --all
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py --qa --json
    python storyworlds/worlds/gpt-5.4/wail_shopping_mall_sound_effects_bravery_humor.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class MallPlace:
    id: str
    label: str
    phrase: str
    detail: str
    allows: set[str] = field(default_factory=set)
    echoey: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundSource:
    id: str
    label: str
    phrase: str
    place_ids: set[str] = field(default_factory=set)
    sound: str = ""
    reveal: str = ""
    cause: str = ""
    requires: set[str] = field(default_factory=set)
    clue: str = ""
    funny_end: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    action: str
    handles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tactic:
    id: str
    label: str
    verb: str
    needs: set[str] = field(default_factory=set)
    step: str = ""
    brave_line: str = ""
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


def _r_wail_to_fear(world: World) -> list[str]:
    out: list[str] = []
    if "sound" not in world.entities:
        return out
    sound = world.get("sound")
    if sound.meters["wailing"] < THRESHOLD:
        return out
    sig = ("wail_to_fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"leader", "buddy"}:
            ent.memes["fear"] += 1
    if "leader" in world.entities:
        world.get("leader").memes["bravery"] += 1
    out.append("__wail__")
    return out


def _r_bravery_to_move(world: World) -> list[str]:
    out: list[str] = []
    leader = world.entities.get("leader")
    if leader is None:
        return out
    if leader.memes["bravery"] < THRESHOLD or leader.memes["fear"] < THRESHOLD:
        return out
    sig = ("bravery_to_move",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.memes["resolve"] += 1
    out.append("__resolve__")
    return out


def _r_reveal_to_laughter(world: World) -> list[str]:
    out: list[str] = []
    sound = world.entities.get("sound")
    if sound is None or sound.meters["solved"] < THRESHOLD:
        return out
    sig = ("reveal_to_laughter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"leader", "buddy"}:
            ent.memes["fear"] = 0.0
            ent.memes["relief"] += 1
            ent.memes["laughter"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wail_to_fear", tag="emotion", apply=_r_wail_to_fear),
    Rule(name="bravery_to_move", tag="emotion", apply=_r_bravery_to_move),
    Rule(name="reveal_to_laughter", tag="emotion", apply=_r_reveal_to_laughter),
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


PLACES = {
    "atrium": MallPlace(
        id="atrium",
        label="atrium",
        phrase="the bright middle atrium",
        detail="The glass roof made every sound bounce and ring above the potted trees.",
        allows={"balloon_vent", "robot_jingle"},
        echoey=True,
        tags={"mall", "echo"},
    ),
    "food_court": MallPlace(
        id="food_court",
        label="food court",
        phrase="the busy food court",
        detail="Trays clinked, chairs scooted, and the smell of pretzels floated past.",
        allows={"juice_lid", "robot_jingle"},
        echoey=False,
        tags={"mall", "food_court"},
    ),
    "toy_row": MallPlace(
        id="toy_row",
        label="toy row",
        phrase="the toy-store row",
        detail="Colorful windows blinked, and stuffed animals smiled from every shelf.",
        allows={"robot_jingle", "bear_demo"},
        echoey=False,
        tags={"mall", "toys"},
    ),
}

SOURCES = {
    "balloon_vent": SoundSource(
        id="balloon_vent",
        label="balloon",
        phrase="a silver balloon",
        place_ids={"atrium"},
        sound='Wheeeee-waaail!',
        reveal="a silver balloon had wriggled loose from a ribbon and was being tickled by the air vent",
        cause="the vent kept blowing through the loose balloon neck, making it sing like a tiny ghost trumpet",
        requires={"look_up", "security_guard"},
        clue="The sound seemed to come from high above their heads.",
        funny_end="The guard caught the balloon, and it let out one last rude little honk.",
        tags={"balloon", "vent", "sound"},
    ),
    "robot_jingle": SoundSource(
        id="robot_jingle",
        label="cleaning robot",
        phrase="a small cleaning robot",
        place_ids={"atrium", "food_court", "toy_row"},
        sound='Waaa-ooo-wee!',
        reveal="a little cleaning robot was rolling in slow circles with a plastic kazoo stuck in its side brush",
        cause="each time the brush spun, the kazoo answered with a silly wail",
        requires={"follow_sound", "janitor"},
        clue="The sound moved, then paused, then moved again across the shiny floor.",
        funny_end="When the janitor freed the kazoo, the robot beeped as if it were proud of its strange concert.",
        tags={"robot", "janitor", "sound"},
    ),
    "bear_demo": SoundSource(
        id="bear_demo",
        label="karaoke bear",
        phrase="a singing teddy bear",
        place_ids={"toy_row"},
        sound='La-la-WAAAIL!',
        reveal="a fluffy karaoke bear on a top shelf was leaning on its own try-me button",
        cause="its bent cardboard sign kept pressing the button, so the bear kept starting the same loud song",
        requires={"look_up", "toy_clerk"},
        clue="Between the echoes, they could hear a tiny drumbeat under the wail.",
        funny_end="Once the clerk straightened the sign, the bear fell quiet with its paws in the air like a comedian bowing.",
        tags={"toy", "music", "sound"},
    ),
    "juice_lid": SoundSource(
        id="juice_lid",
        label="cup lid",
        phrase="a paper cup lid",
        place_ids={"food_court"},
        sound='Oooo-wail-ooo!',
        reveal="a paper cup lid had landed on a straw-cleaning fan behind the juice stand",
        cause="the fan kept spinning the lid so it wailed like a tiny siren",
        requires={"follow_sound", "food_worker"},
        clue="The strange cry fluttered from behind the juice counter between the blender noises.",
        funny_end="The worker plucked out the lid, and the children laughed so hard they nearly snorted.",
        tags={"food_court", "fan", "sound"},
    ),
}

HELPERS = {
    "security_guard": Helper(
        id="security_guard",
        label="security guard",
        phrase="a friendly security guard",
        action="used a long reach pole and careful hands",
        handles={"balloon_vent"},
        tags={"guard", "adult_help"},
    ),
    "janitor": Helper(
        id="janitor",
        label="janitor",
        phrase="a cheerful janitor",
        action="knelt beside the machine and clicked it safely off",
        handles={"robot_jingle"},
        tags={"janitor", "adult_help"},
    ),
    "toy_clerk": Helper(
        id="toy_clerk",
        label="toy clerk",
        phrase="a toy-store clerk with a pocketful of stickers",
        action="brought over a little step ladder and fixed the display",
        handles={"bear_demo"},
        tags={"clerk", "adult_help"},
    ),
    "food_worker": Helper(
        id="food_worker",
        label="juice-bar worker",
        phrase="a juice-bar worker in a green apron",
        action="reached behind the counter and stopped the spinning fan for a second",
        handles={"juice_lid"},
        tags={"worker", "adult_help"},
    ),
}

TACTICS = {
    "follow_sound": Tactic(
        id="follow_sound",
        label="follow the sound",
        verb="follow the wobbling sound",
        needs={"robot_jingle", "juice_lid"},
        step="They stopped, listened, and followed the noise one careful step at a time.",
        brave_line='"If it is strange, we can still be sensible," the brave child whispered.',
        tags={"listen", "sound"},
    ),
    "look_up": Tactic(
        id="look_up",
        label="look up high",
        verb="look up instead of running around",
        needs={"balloon_vent", "bear_demo"},
        step="They stood still and searched up high before taking another step.",
        brave_line='"Let us use our eyes first," the brave child said, trying to sound like an explorer captain.',
        tags={"look", "sound"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]
TRAITS = ["curious", "steady", "funny", "careful", "bright", "daring"]


def source_fits_place(place_id: str, source_id: str) -> bool:
    return source_id in PLACES[place_id].allows and place_id in SOURCES[source_id].place_ids


def helper_fits_source(helper_id: str, source_id: str) -> bool:
    return source_id in HELPERS[helper_id].handles


def tactic_fits_source(tactic_id: str, source_id: str) -> bool:
    return source_id in TACTICS[tactic_id].needs


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for source_id in sorted(SOURCES):
            if not source_fits_place(place_id, source_id):
                continue
            for helper_id in sorted(HELPERS):
                if not helper_fits_source(helper_id, source_id):
                    continue
                for tactic_id in sorted(TACTICS):
                    if tactic_fits_source(tactic_id, source_id):
                        combos.append((place_id, source_id, helper_id, tactic_id))
    return combos


@dataclass
class StoryParams:
    place: str
    source: str
    helper: str
    tactic: str
    leader_name: str
    leader_gender: str
    buddy_name: str
    buddy_gender: str
    parent: str
    leader_trait: str
    buddy_trait: str
    seed: Optional[int] = None


def introduce(world: World, leader: Entity, buddy: Entity, place: MallPlace) -> None:
    world.say(
        f"On Saturday, {leader.id} and {buddy.id} walked through {place.phrase} with "
        f"{leader.id}'s {world.get('parent').label_word}. {place.detail}"
    )
    world.say(
        f"{leader.id} felt as if the shopping mall were really an adventure station, "
        f"full of corners to explore and clues to notice."
    )


def spark_play(world: World, leader: Entity, buddy: Entity) -> None:
    leader.memes["joy"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f'"If we were treasure hunters," {leader.id} said, "this would be the part where '
        f'we listen for secret signs."'
    )
    world.say(
        f'{buddy.id} giggled. "I hope the secret sign leads to pretzel bites."'
    )


def hear_wail(world: World, place: MallPlace, source: SoundSource) -> None:
    sound = world.get("sound")
    sound.meters["wailing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a strange sound curled through the mall: {source.sound} It was a real wail, "
        f"long enough to make both children stop in their tracks."
    )
    world.say(source.clue)
    if place.echoey:
        world.say("Because the atrium echoed, the noise seemed to jump from one shiny wall to another.")


def react(world: World, leader: Entity, buddy: Entity) -> None:
    fear_b = "opened wide" if buddy.memes["fear"] >= THRESHOLD else "blinked"
    world.say(
        f'{buddy.id}\'s eyes {fear_b}. "Did the mall just sing at us?" {buddy.pronoun()} asked.'
    )
    if leader.memes["resolve"] >= THRESHOLD:
        world.say(
            f"{leader.id}'s tummy gave one nervous flip, but {leader.pronoun()} stood a little taller."
        )


def choose_bravery(world: World, leader: Entity, buddy: Entity, tactic: Tactic) -> None:
    leader.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(tactic.brave_line)
    world.say(
        f"{buddy.id} stayed close beside {leader.id}. That was brave too, because staying and thinking "
        f"is harder than running away."
    )


def investigate(world: World, tactic: Tactic) -> None:
    world.say(tactic.step)


def ask_adult(world: World, parent: Entity, helper: Helper) -> None:
    parent.memes["guidance"] += 1
    world.say(
        f'"Let\'s solve it the smart way," said {parent.label_word}. {parent.pronoun().capitalize()} waved over '
        f"{helper.phrase}."
    )


def reveal_source(world: World, helper: Helper, source: SoundSource) -> None:
    sound = world.get("sound")
    sound.meters["solved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they found the answer: {source.reveal}. {source.cause}."
    )
    world.say(
        f"The {helper.label} {helper.action}, and the spooky mystery melted into something wonderfully silly."
    )


def laugh_end(world: World, leader: Entity, buddy: Entity, source: SoundSource, place: MallPlace) -> None:
    world.say(
        f"{leader.id} laughed first, then {buddy.id}, and soon even the grown-ups were smiling. {source.funny_end}"
    )
    end_line = (
        f"As they walked on through the mall, the place no longer felt haunted. "
        f"It felt like an adventure they had solved with brave hearts, careful ears, and a good joke at the end."
    )
    if place.id == "food_court":
        end_line += " The clatter of trays sounded ordinary again."
    elif place.id == "toy_row":
        end_line += " The blinking shop windows looked friendly instead of mysterious."
    else:
        end_line += " The high glass roof only tossed back happy voices now."
    world.say(end_line)


def tell(
    place: MallPlace,
    source: SoundSource,
    helper: Helper,
    tactic: Tactic,
    leader_name: str = "Lily",
    leader_gender: str = "girl",
    buddy_name: str = "Ben",
    buddy_gender: str = "boy",
    parent_type: str = "mother",
    leader_trait: str = "daring",
    buddy_trait: str = "funny",
) -> World:
    world = World()
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        phrase=leader_name,
        role="leader",
        traits=[leader_trait],
    ))
    buddy = world.add(Entity(
        id="buddy",
        kind="character",
        type=buddy_gender,
        label=buddy_name,
        phrase=buddy_name,
        role="buddy",
        traits=[buddy_trait],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    sound = world.add(Entity(
        id="sound",
        kind="thing",
        type="sound",
        label=source.label,
        phrase=source.phrase,
        role="source",
        tags=set(source.tags),
    ))

    world.facts["display_names"] = {"leader": leader_name, "buddy": buddy_name}

    introduce(world, leader, buddy, place)
    spark_play(world, leader, buddy)

    world.para()
    hear_wail(world, place, source)
    react(world, leader, buddy)
    choose_bravery(world, leader, buddy, tactic)
    investigate(world, tactic)

    world.para()
    ask_adult(world, parent, helper)
    reveal_source(world, helper, source)

    world.para()
    laugh_end(world, leader, buddy, source, place)

    world.facts.update(
        place=place,
        source_cfg=source,
        helper_cfg=helper,
        tactic_cfg=tactic,
        leader=leader,
        buddy=buddy,
        parent=parent,
        sound=sound,
        solved=sound.meters["solved"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "mall": [
        (
            "What is a shopping mall?",
            "A shopping mall is a big building with many stores and wide halls inside. People walk from shop to shop there.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off walls or ceilings and comes back to your ears. Big open places can make noises seem farther away or stranger than they really are.",
        )
    ],
    "guard": [
        (
            "What does a security guard do in a mall?",
            "A security guard helps keep people safe and can help when something odd happens. They are a good grown-up to ask when you are unsure.",
        )
    ],
    "janitor": [
        (
            "What does a janitor do?",
            "A janitor cleans and takes care of a building. They often know how to safely stop or move cleaning machines too.",
        )
    ],
    "clerk": [
        (
            "What does a store clerk do?",
            "A store clerk helps customers and takes care of things in the store. They can fix a display or reach a shelf safely.",
        )
    ],
    "worker": [
        (
            "What does a food worker do?",
            "A food worker helps prepare and serve food and drinks. They also know the machines behind the counter.",
        )
    ],
    "balloon": [
        (
            "Why can a balloon make a funny noise?",
            "Air can whistle through the neck of a balloon and make a squeaky sound. Sometimes it can sound almost like singing or a wail.",
        )
    ],
    "vent": [
        (
            "What does an air vent do?",
            "An air vent blows air into a room. That moving air can flap light things and make them rattle or whistle.",
        )
    ],
    "robot": [
        (
            "What is a cleaning robot?",
            "A cleaning robot is a small machine that moves around and helps clean floors. Grown-ups should be the ones to handle it when something gets stuck.",
        )
    ],
    "toy": [
        (
            "What is a try-me button on a toy?",
            "A try-me button lets shoppers press a toy to hear or see what it does. If something keeps pressing it by mistake, the toy may keep going.",
        )
    ],
    "music": [
        (
            "Why can a repeated toy song sound funny after a while?",
            "When the same loud sound happens again and again, it can stop feeling grand and start feeling silly. That surprise can make people laugh.",
        )
    ],
    "food_court": [
        (
            "What is a food court?",
            "A food court is a part of a mall where many food counters and tables are together. It is often full of clinks, scoots, and talking voices.",
        )
    ],
    "adult_help": [
        (
            "What should children do when a strange sound worries them in a busy place?",
            "They should stay near their grown-up and ask a safe adult for help. Brave choices can be careful choices.",
        )
    ],
    "listen": [
        (
            "Why is listening carefully useful?",
            "Listening carefully can help you figure out where a sound is coming from. It helps you solve a mystery without rushing.",
        )
    ],
    "look": [
        (
            "Why is it smart to stop and look before running around?",
            "Stopping first helps you notice clues and keeps you from bumping into things. Careful bravery means using your eyes and brain together.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "mall",
    "echo",
    "food_court",
    "guard",
    "janitor",
    "clerk",
    "worker",
    "balloon",
    "vent",
    "robot",
    "toy",
    "music",
    "adult_help",
    "listen",
    "look",
]


def display_name(world: World, role: str) -> str:
    return world.facts.get("display_names", {}).get(role, role.title())


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    source = f["source_cfg"]
    helper = f["helper_cfg"]
    tactic = f["tactic_cfg"]
    leader_name = display_name(world, "leader")
    buddy_name = display_name(world, "buddy")
    return [
        f'Write a short adventure story for a 3-to-5-year-old set in a shopping mall that includes the word "wail".',
        f"Tell a funny, brave mall story where {leader_name} and {buddy_name} hear a spooky sound in {place.label}, use the plan to {tactic.verb}, and ask a {helper.label} for help.",
        f"Write a child-facing mystery with sound effects, humor, and a safe ending where the scary noise turns out to be {source.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader_name = display_name(world, "leader")
    buddy_name = display_name(world, "buddy")
    leader = f["leader"]
    buddy = f["buddy"]
    parent = f["parent"]
    place = f["place"]
    source = f["source_cfg"]
    helper = f["helper_cfg"]
    tactic = f["tactic_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader_name} and {buddy_name}, two children in a shopping mall, and {leader_name}'s {parent.label_word} who helps them stay safe. They hear a strange wail and decide to solve the mystery carefully.",
        ),
        (
            "Where did the adventure happen?",
            f"It happened in {place.phrase} inside the shopping mall. The sounds and sights there shaped the mystery because the noise bounced around and felt bigger than it really was.",
        ),
        (
            "What scary sound did they hear?",
            f"They heard a strange wail that made them stop and listen. It sounded spooky at first because they did not know what was causing it yet.",
        ),
        (
            f"How was {leader_name} brave?",
            f"{leader_name} was brave by staying calm enough to think instead of running away. {leader.pronoun().capitalize()} chose to {tactic.verb} and ask a grown-up for help, which was the smart kind of bravery.",
        ),
        (
            f"Why did they ask the {helper.label} for help?",
            f"They asked the {helper.label} for help because the sound came from something the children should not handle by themselves. The helper knew how to reach it safely and stop the noise without anyone getting hurt.",
        ),
        (
            "What was really making the wail?",
            f"It was really {source.reveal}. The scary sound had a harmless cause: {source.cause}.",
        ),
        (
            "Why did the ending become funny instead of scary?",
            f"Once the children understood the cause, the mystery stopped feeling like a monster and started feeling silly. The same sound changed because now they knew it came from an ordinary thing doing something ridiculous.",
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children laughing as the mall sounded normal again. They walked on feeling braver because they had solved the mystery with careful thinking and adult help.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["source_cfg"].tags) | set(f["helper_cfg"].tags) | set(f["tactic_cfg"].tags)
    tags.add("adult_help")
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
    names = world.facts.get("display_names", {})
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.id in names:
            bits.append(f"name={names[e.id]}")
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="atrium",
        source="balloon_vent",
        helper="security_guard",
        tactic="look_up",
        leader_name="Lily",
        leader_gender="girl",
        buddy_name="Ben",
        buddy_gender="boy",
        parent="mother",
        leader_trait="daring",
        buddy_trait="funny",
    ),
    StoryParams(
        place="food_court",
        source="juice_lid",
        helper="food_worker",
        tactic="follow_sound",
        leader_name="Sam",
        leader_gender="boy",
        buddy_name="Mia",
        buddy_gender="girl",
        parent="father",
        leader_trait="steady",
        buddy_trait="bright",
    ),
    StoryParams(
        place="toy_row",
        source="bear_demo",
        helper="toy_clerk",
        tactic="look_up",
        leader_name="Ava",
        leader_gender="girl",
        buddy_name="Noah",
        buddy_gender="boy",
        parent="mother",
        leader_trait="curious",
        buddy_trait="funny",
    ),
    StoryParams(
        place="toy_row",
        source="robot_jingle",
        helper="janitor",
        tactic="follow_sound",
        leader_name="Theo",
        leader_gender="boy",
        buddy_name="Lucy",
        buddy_gender="girl",
        parent="father",
        leader_trait="bright",
        buddy_trait="careful",
    ),
]


def explain_rejection(place_id: str, source_id: str, helper_id: str, tactic_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if source_id not in SOURCES:
        return f"(No story: unknown source '{source_id}'.)"
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    if tactic_id not in TACTICS:
        return f"(No story: unknown tactic '{tactic_id}'.)"
    if not source_fits_place(place_id, source_id):
        return (
            f"(No story: {SOURCES[source_id].phrase} does not plausibly belong in {PLACES[place_id].label}. "
            f"The sound source must fit the mall location.)"
        )
    if not helper_fits_source(helper_id, source_id):
        return (
            f"(No story: a {HELPERS[helper_id].label} is not the sensible helper for {SOURCES[source_id].label}. "
            f"Pick a grown-up who can actually handle that problem.)"
        )
    if not tactic_fits_source(tactic_id, source_id):
        return (
            f"(No story: the plan '{TACTICS[tactic_id].label}' does not match this kind of sound. "
            f"The children should investigate in a way that fits the clue.)"
        )
    return "(No story: the requested combination is not reasonable.)"


ASP_RULES = r"""
source_fits_place(P,S) :- place(P), source(S), allowed(P,S), located(S,P).
helper_fits_source(H,S) :- helper(H), source(S), handles(H,S).
tactic_fits_source(T,S) :- tactic(T), source(S), needs(T,S).

valid(P,S,H,T) :- source_fits_place(P,S), helper_fits_source(H,S), tactic_fits_source(T,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(place.allows):
            lines.append(asp.fact("allowed", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for place_id in sorted(source.place_ids):
            lines.append(asp.fact("located", source_id, place_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for source_id in sorted(helper.handles):
            lines.append(asp.fact("handles", helper_id, source_id))
    for tactic_id, tactic in TACTICS.items():
        lines.append(asp.fact("tactic", tactic_id))
        for source_id in sorted(tactic.needs):
            lines.append(asp.fact("needs", tactic_id, source_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


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

    try:
        sample = generate(CURATED[0])
        if not sample.story or "wail" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story missing expected content.)")
        smoke_emit(sample)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a brave, funny mall mystery built around a strange wail."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--tactic", choices=sorted(TACTICS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--leader-name")
    ap.add_argument("--buddy-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_opt = args.place
    source_opt = args.source
    helper_opt = args.helper
    tactic_opt = args.tactic

    if place_opt and source_opt and helper_opt and tactic_opt:
        if (place_opt, source_opt, helper_opt, tactic_opt) not in set(valid_combos()):
            raise StoryError(explain_rejection(place_opt, source_opt, helper_opt, tactic_opt))

    combos = [
        combo for combo in valid_combos()
        if (place_opt is None or combo[0] == place_opt)
        and (source_opt is None or combo[1] == source_opt)
        and (helper_opt is None or combo[2] == helper_opt)
        and (tactic_opt is None or combo[3] == tactic_opt)
    ]
    if not combos:
        p = place_opt or next(iter(PLACES))
        s = source_opt or next(iter(SOURCES))
        h = helper_opt or next(iter(HELPERS))
        t = tactic_opt or next(iter(TACTICS))
        raise StoryError(explain_rejection(p, s, h, t))

    place, source, helper, tactic = rng.choice(sorted(combos))
    leader_gender = rng.choice(["girl", "boy"])
    buddy_gender = rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_gender)
    buddy_name = args.buddy_name or _pick_name(rng, buddy_gender, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father"])
    leader_trait = rng.choice(TRAITS)
    buddy_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        source=source,
        helper=helper,
        tactic=tactic,
        leader_name=leader_name,
        leader_gender=leader_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        parent=parent,
        leader_trait=leader_trait,
        buddy_trait=buddy_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(No story: unknown source '{params.source}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.tactic not in TACTICS:
        raise StoryError(f"(No story: unknown tactic '{params.tactic}'.)")
    if not source_fits_place(params.place, params.source):
        raise StoryError(explain_rejection(params.place, params.source, params.helper, params.tactic))
    if not helper_fits_source(params.helper, params.source):
        raise StoryError(explain_rejection(params.place, params.source, params.helper, params.tactic))
    if not tactic_fits_source(params.tactic, params.source):
        raise StoryError(explain_rejection(params.place, params.source, params.helper, params.tactic))

    world = tell(
        place=PLACES[params.place],
        source=SOURCES[params.source],
        helper=HELPERS[params.helper],
        tactic=TACTICS[params.tactic],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        parent_type=params.parent,
        leader_trait=params.leader_trait,
        buddy_trait=params.buddy_trait,
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
        print(f"{len(combos)} compatible (place, source, helper, tactic) combos:\n")
        for place, source, helper, tactic in combos:
            print(f"  {place:10} {source:13} {helper:15} {tactic}")
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
            header = f"### {p.leader_name} & {p.buddy_name}: {p.source} in {p.place} ({p.helper}, {p.tactic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
