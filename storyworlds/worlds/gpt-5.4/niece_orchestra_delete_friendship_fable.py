#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py
=====================================================================

A standalone story world for a small friendship fable about a niece in a forest
orchestra who is tempted to delete a friend's name from the opening music list.

The world models a simple moral tension:
- a child wants a special music part,
- envy makes a sneaky idea feel possible,
- deleting a friend's place hurts trust and weakens the music,
- honesty and friendship can restore harmony.

Run it
------
    python storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py
    python storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py --solution ask_share
    python storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py --hero-instrument drum --friend-instrument horn --solution ask_share
    python storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py --all
    python storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/niece_orchestra_delete_friendship_fable.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    instrument: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "hen", "doe", "ewe"}
        male = {"boy", "father", "uncle", "buck", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    image: str
    board: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    family: str
    can_lead: bool = True
    blend_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_left_out_hurts(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    orchestra = world.get("orchestra")
    if friend.meters["left_out"] >= THRESHOLD and ("hurt", friend.id) not in world.fired:
        world.fired.add(("hurt", friend.id))
        friend.memes["sadness"] += 1
        friend.memes["trust"] -= 1
        hero.memes["guilt"] += 1
        orchestra.meters["harmony"] -= 1
        out.append("__hurt__")
    return out


def _r_shared_music_heals(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    orchestra = world.get("orchestra")
    if hero.meters["sharing"] >= THRESHOLD and friend.meters["sharing"] >= THRESHOLD:
        if ("shared", hero.id, friend.id) not in world.fired:
            world.fired.add(("shared", hero.id, friend.id))
            hero.memes["friendship"] += 1
            friend.memes["friendship"] += 1
            friend.memes["trust"] += 1
            hero.memes["relief"] += 1
            orchestra.meters["harmony"] += 2
            out.append("__shared__")
    return out


def _r_apology_repairs(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    orchestra = world.get("orchestra")
    if hero.memes["apology"] >= THRESHOLD and friend.memes["forgiveness"] >= THRESHOLD:
        if ("repair", hero.id, friend.id) not in world.fired:
            world.fired.add(("repair", hero.id, friend.id))
            hero.memes["friendship"] += 1
            friend.memes["friendship"] += 1
            friend.memes["trust"] += 1
            friend.memes["sadness"] = 0.0
            orchestra.meters["harmony"] += 1
            out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule("left_out_hurts", "social", _r_left_out_hurts),
    Rule("shared_music_heals", "social", _r_shared_music_heals),
    Rule("apology_repairs", "social", _r_apology_repairs),
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


def can_duet(hero: Instrument, friend: Instrument) -> bool:
    return friend.id in hero.blend_with and hero.id in friend.blend_with


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def valid_combo(hero: Instrument, friend: Instrument, solution: Solution) -> bool:
    if not hero.can_lead:
        return False
    if solution.id == "ask_share":
        return can_duet(hero, friend)
    return solution.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for hid, hero in INSTRUMENTS.items():
            for fid, friend in INSTRUMENTS.items():
                if hid == fid:
                    continue
                for sid, solution in SOLUTIONS.items():
                    if valid_combo(hero, friend, solution):
                        combos.append((setting, hid, fid, sid))
    return combos


def predict_delete(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    friend = sim.get("friend")
    orchestra = sim.get("orchestra")
    hero.meters["deleted_name"] += 1
    friend.meters["left_out"] += 1
    orchestra.meters["list_changed"] += 1
    propagate(sim, narrate=False)
    return {
        "friend_sad": friend.memes["sadness"] >= THRESHOLD,
        "trust_drop": friend.memes["trust"] < 0,
        "harmony_low": orchestra.meters["harmony"] < 0,
    }


def introduce(world: World, hero: Entity, aunt: Entity, friend: Entity,
              hero_inst: Instrument, friend_inst: Instrument) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In {world.setting.place}, where {world.setting.image}, lived {hero.id}, "
        f"a young {hero.type} who was Aunt {aunt.id}'s niece."
    )
    world.say(
        f"Every afternoon, {hero.id} carried {hero_inst.phrase}, and {friend.id} came "
        f"along with {friend_inst.phrase}. Together they played in the woodland orchestra."
    )


def announce(world: World, aunt: Entity, hero: Entity, friend: Entity,
             board_text: str) -> None:
    world.say(
        f"Aunt {aunt.id}, who guided the orchestra with a soft feather-baton, hung "
        f"{world.setting.board}. On it was the opening music list."
    )
    world.say(
        f'The first line read, "{board_text}" and {friend.id} smiled with surprised delight.'
    )
    hero.memes["envy"] += 1
    world.facts["board_text"] = board_text


def temptation(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was glad for {friend.id} for one heartbeat. Then envy crept in like "
        f"a cold little shadow."
    )
    world.say(
        f'Beside the list sat Aunt {world.get("aunt").id}\'s practice tablet, and in one '
        f"corner glowed a tiny leaf-button marked delete."
    )


def warning(world: World, hero: Entity, hero_inst: Instrument, friend_inst: Instrument) -> None:
    pred = predict_delete(world)
    world.facts["predicted_friend_sad"] = pred["friend_sad"]
    world.facts["predicted_harmony_low"] = pred["harmony_low"]
    extra = ""
    if pred["friend_sad"]:
        extra += " A missing friend would leave a sore place in the music."
    if pred["harmony_low"]:
        extra += f" {hero_inst.label.capitalize()} alone could not make the same rich beginning as {hero_inst.label} with {friend_inst.label}."
    world.say(
        f"{hero.id} looked at the little word delete and imagined tapping it.{extra}"
    )


def ask_share(world: World, hero: Entity, friend: Entity,
              hero_inst: Instrument, friend_inst: Instrument) -> None:
    hero.meters["sharing"] += 1
    friend.meters["sharing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {hero.id} drew back {hero.pronoun('possessive')} paw. Sneaky fingers make sour songs."
    )
    world.say(
        f'"{friend.id}," {hero.id} said, "I felt jealous. Would you share the opening with me? '
        f'Your {friend_inst.label} and my {hero_inst.label} sound kind together."'
    )
    world.say(
        f'{friend.id} blinked, then nodded. "Of course," {friend.pronoun()} said. '
        f'"A good beginning is better when two friends breathe it together."'
    )


def do_delete(world: World, hero: Entity, friend: Entity) -> None:
    hero.meters["deleted_name"] += 1
    friend.meters["left_out"] += 1
    world.get("orchestra").meters["list_changed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Envy won for a moment. {hero.id} tapped delete, and {friend.id}'s name vanished from the list."
    )
    world.say(
        f"The board looked neat, but {hero.id}'s heart did not. Even the evening breeze seemed to sigh."
    )


def confrontation(world: World, aunt: Entity, friend: Entity) -> None:
    world.say(
        f"When rehearsal began, {friend.id} stepped close to the board and saw the empty line."
    )
    world.say(
        f'"Was my name there before?" {friend.pronoun()} asked quietly. Aunt {aunt.id} looked from the board to the children, and the glade grew still.'
    )


def restore_and_apologize(world: World, hero: Entity, friend: Entity) -> None:
    friend.meters["left_out"] = 0.0
    world.get("orchestra").meters["list_changed"] = 0.0
    hero.memes["apology"] += 1
    friend.memes["forgiveness"] += 1
    hero.meters["sharing"] += 1
    friend.meters["sharing"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} could bear the ache no longer. "I did it," {hero.pronoun()} whispered. '
        f'"I was jealous, and I was wrong."'
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} touched the tablet again, restored {friend.id}'s name, and bowed {hero.pronoun('possessive')} head."
    )
    world.say(
        f'"I am sorry," {hero.pronoun()} said. "{friend.id}, will you still play with me?"'
    )
    world.say(
        f'{friend.id} was hurt, but kindness was stronger. "{friend.id}" is what the board should say, '
        f'{friend.pronoun()} replied, "and a true friend tells the truth before the song begins."'
    )


def stubborn_solo(world: World, hero: Entity, aunt: Entity,
                  hero_inst: Instrument, friend_inst: Instrument) -> None:
    world.say(
        f'{hero.id} kept silent, and silence became another small lie. So Aunt {aunt.id} began the piece with only {hero.id} at the front.'
    )
    world.say(
        f"The {hero_inst.label} sounded clear, yet the place where the {friend_inst.label} should have answered felt empty, like a bridge missing one plank."
    )
    world.say(
        f"When the last note fell, no one clapped at once. {hero.id} had won the first line and lost the joy of it."
    )


def repaired_ending(world: World, hero: Entity, friend: Entity,
                    hero_inst: Instrument, friend_inst: Instrument) -> None:
    world.say(
        f"Soon the opening melody rose again, this time with {hero_inst.label} and {friend_inst.label} answering each other like two birds over one stream."
    )
    world.say(
        f"{hero.id} smiled at {friend.id}, and {friend.id} smiled back. The music was richer because the friendship had been mended."
    )


def shared_ending(world: World, hero: Entity, friend: Entity,
                  hero_inst: Instrument, friend_inst: Instrument) -> None:
    world.say(
        f"When the orchestra played, {hero_inst.label} and {friend_inst.label} braided together so sweetly that even the ferns seemed to lean closer."
    )
    world.say(
        f"Aunt {world.get('aunt').id} nodded, and the two friends began the song side by side, brighter together than either could have been alone."
    )


def lonely_ending(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] = 0.0
    world.say(
        f"After rehearsal, {friend.id} walked home with the others, but not beside {hero.id}."
    )
    world.say(
        f"{hero.id} sat alone by a mossy stump and understood at last: a place won by pushing away a friend is smaller than it looks."
    )


def moral(world: World, text: str) -> None:
    world.para()
    world.say(text)


def tell(setting: Setting, hero_inst: Instrument, friend_inst: Instrument,
         solution: Solution, hero_name: str = "Pip", hero_type: str = "squirrel",
         friend_name: str = "Lark", friend_type: str = "rabbit",
         aunt_name: str = "Owl", aunt_type: str = "aunt") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            instrument=hero_inst.id, traits=["young", "eager"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend",
                              instrument=friend_inst.id, traits=["gentle", "steady"]))
    aunt = world.add(Entity(id=aunt_name, kind="character", type=aunt_type, role="aunt"))
    orchestra = world.add(Entity(id="orchestra", kind="thing", type="group", label="orchestra"))
    world.facts["solution_id"] = solution.id

    board_text = f"Opening: {friend_name} on {friend_inst.label}"
    introduce(world, hero, aunt, friend, hero_inst, friend_inst)
    announce(world, aunt, hero, friend, board_text)
    world.para()
    temptation(world, hero, friend)
    warning(world, hero, hero_inst, friend_inst)

    if solution.id == "ask_share":
        ask_share(world, hero, friend, hero_inst, friend_inst)
        world.para()
        shared_ending(world, hero, friend, hero_inst, friend_inst)
        outcome = "shared"
        moral_text = "Moral: Friendship grows when envy speaks honestly instead of acting in secret."
    elif solution.id == "restore_apology":
        do_delete(world, hero, friend)
        world.para()
        confrontation(world, aunt, friend)
        restore_and_apologize(world, hero, friend)
        world.para()
        repaired_ending(world, hero, friend, hero_inst, friend_inst)
        outcome = "repaired"
        moral_text = "Moral: A wrong note can be mended when truth and apology return before the song is over."
    else:
        do_delete(world, hero, friend)
        world.para()
        confrontation(world, aunt, friend)
        stubborn_solo(world, hero, aunt, hero_inst, friend_inst)
        world.para()
        lonely_ending(world, hero, friend)
        outcome = "lonely"
        moral_text = "Moral: Whoever tries to climb by cutting away a friend stands on a very lonely branch."

    moral(world, moral_text)
    world.facts.update(
        hero=hero,
        friend=friend,
        aunt=aunt,
        orchestra=orchestra,
        setting=setting,
        hero_instrument=hero_inst,
        friend_instrument=friend_inst,
        solution=solution,
        outcome=outcome,
        deleted=hero.meters["deleted_name"] >= THRESHOLD,
        repaired=outcome == "repaired",
        shared=outcome == "shared",
        lonely=outcome == "lonely",
    )
    return world


SETTINGS = {
    "glade": Setting(
        "glade",
        "the Ferny Glade",
        "dew shone on fern tips and the old stump stage smelled of cedar",
        "a smooth birch board tied with red twine",
        tags={"forest", "orchestra"},
    ),
    "riverbank": Setting(
        "riverbank",
        "the Willow Riverbank",
        "the river made a silver hush and willow leaves stroked the air",
        "a reed-woven board hanging from a willow branch",
        tags={"river", "orchestra"},
    ),
    "meadow": Setting(
        "meadow",
        "the Clover Meadow",
        "clover heads nodded under the evening light and fireflies blinked near the stage",
        "a painted board propped against a honey-colored stone",
        tags={"meadow", "orchestra"},
    ),
}

INSTRUMENTS = {
    "violin": Instrument(
        "violin", "violin", "a small violin", "sang in a bright silver line", "string",
        can_lead=True, blend_with={"flute", "cello", "violin"},
        tags={"violin", "orchestra", "music"},
    ),
    "flute": Instrument(
        "flute", "flute", "a reed flute", "floated like a cool breeze", "wind",
        can_lead=True, blend_with={"violin", "cello", "flute"},
        tags={"flute", "orchestra", "music"},
    ),
    "cello": Instrument(
        "cello", "cello", "a little cello", "hummed like warm honey", "string",
        can_lead=True, blend_with={"violin", "flute", "cello"},
        tags={"cello", "orchestra", "music"},
    ),
    "drum": Instrument(
        "drum", "drum", "a round drum", "thumped like rain on a hollow log", "rhythm",
        can_lead=True, blend_with={"drum"},
        tags={"drum", "orchestra", "music"},
    ),
    "horn": Instrument(
        "horn", "horn", "a curled brass horn", "called out in a bold golden voice", "wind",
        can_lead=True, blend_with={"horn"},
        tags={"horn", "orchestra", "music"},
    ),
}

SOLUTIONS = {
    "ask_share": Solution(
        "ask_share", 3,
        "tell the truth before touching delete and ask to share the opening",
        "asked to share the opening honestly instead of deleting a name",
        tags={"friendship", "sharing", "truth"},
    ),
    "restore_apology": Solution(
        "restore_apology", 3,
        "restore the name and apologize before the concert",
        "restored the name and apologized before the song began",
        tags={"friendship", "apology", "truth"},
    ),
    "stubborn_solo": Solution(
        "stubborn_solo", 2,
        "keep the stolen place and learn the lonely cost",
        "kept the stolen place and ended up lonely",
        tags={"envy", "lonely", "lesson"},
    ),
    "blame_wind": Solution(
        "blame_wind", 1,
        "pretend the wind changed the list",
        "blamed the wind for the missing name",
        tags={"lie"},
    ),
}

NIECE_NAMES = ["Pip", "Mina", "Nell", "Tess", "Ivy", "Wren"]
FRIEND_NAMES = ["Lark", "Moss", "Juniper", "Rowan", "Poppy", "Bram"]
HERO_TYPES = ["squirrel", "mouse", "otter", "rabbit"]
FRIEND_TYPES = ["rabbit", "hedgehog", "fox", "beaver"]


@dataclass
class StoryParams:
    setting: str
    hero_instrument: str
    friend_instrument: str
    solution: str
    niece_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "orchestra": [(
        "What is an orchestra?",
        "An orchestra is a group of musicians who play different instruments together. Each part matters because the music sounds fuller when everyone joins in."
    )],
    "violin": [(
        "What is a violin?",
        "A violin is a small string instrument played with a bow. It can make bright, singing sounds."
    )],
    "flute": [(
        "What is a flute?",
        "A flute is a wind instrument that makes sound when you blow across it. Its voice can sound light and airy."
    )],
    "cello": [(
        "What is a cello?",
        "A cello is a string instrument with a deeper voice than a violin. Its notes can sound warm and low."
    )],
    "drum": [(
        "What does a drum do in music?",
        "A drum keeps a steady beat. The beat helps other players stay together."
    )],
    "horn": [(
        "What is a horn?",
        "A horn is a brass instrument that can make strong, round notes. It is often louder than small string instruments."
    )],
    "delete": [(
        "What does delete mean?",
        "Delete means to remove something from a list, page, or screen. If you delete the wrong thing, you may need to put it back."
    )],
    "friendship": [(
        "What helps a friendship stay strong?",
        "Honesty, kindness, and sharing help a friendship stay strong. A friend should not push another friend aside for a prize."
    )],
    "apology": [(
        "Why is an apology important?",
        "An apology shows that you know you did wrong and want to mend the hurt. It cannot erase the hurt at once, but it can begin to heal it."
    )],
    "sharing": [(
        "Why can sharing make something better?",
        "Sharing can make joy bigger because more than one person gets to belong. In music, sharing can also make the sound richer."
    )],
    "envy": [(
        "What is envy?",
        "Envy is the unhappy feeling that comes when you want what someone else has. If you listen to envy too much, it can push you toward unkind choices."
    )],
}
KNOWLEDGE_ORDER = ["orchestra", "delete", "friendship", "sharing", "apology",
                   "envy", "violin", "flute", "cello", "drum", "horn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    hi = f["hero_instrument"]
    fi = f["friend_instrument"]
    if f["outcome"] == "shared":
        return [
            'Write a short fable for a 3-to-5-year-old that includes the words "niece", "orchestra", and "delete".',
            f"Tell a friendship fable where a niece in an orchestra feels jealous of {friend.id}, almost presses delete, and then asks to share the opening instead.",
            f"Write a gentle animal fable in which {hero.id} and {friend.id} begin the music together on {hi.label} and {fi.label}, showing that friendship sounds better than envy.",
        ]
    if f["outcome"] == "repaired":
        return [
            'Write a short fable for a 3-to-5-year-old that includes the words "niece", "orchestra", and "delete".',
            f"Tell a friendship fable where a niece in a woodland orchestra wrongly deletes a friend's name, feels guilty, and restores it with an apology before the concert.",
            f"Write a simple moral tale where jealousy causes a sneaky act, but truth and friendship mend the song before it is too late.",
        ]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the words "niece", "orchestra", and "delete".',
        f"Tell a friendship fable where a niece in an orchestra deletes a friend's name and learns that winning a place by selfishness feels lonely.",
        "Write a cautionary animal fable about envy, a stolen music part, and the lonely lesson that follows when honesty is refused.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    aunt = f["aunt"]
    hi = f["hero_instrument"]
    fi = f["friend_instrument"]
    solution = f["solution"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, Aunt {aunt.id}'s niece, and {friend.id}, {hero.id}'s friend in the orchestra. Their friendship is tested when the opening music part is placed on the board."
        ),
        (
            "What made the problem begin?",
            f"The board gave the opening line to {friend.id}, and {hero.id} felt jealous. The little delete button made the unkind choice seem easy for a moment."
        ),
        (
            f"Why was pressing delete a bad idea?",
            f"Deleting {friend.id}'s name would unfairly push a friend out of the music. It would also hurt trust, because the place on the board was not {hero.id}'s to steal."
        ),
    ]
    if f["shared"]:
        qa.append((
            f"What did {hero.id} do instead of touching delete?",
            f"{hero.id} told the truth about feeling jealous and asked {friend.id} to share the opening. That choice protected the friendship and let the music begin with both {hi.label} and {fi.label} together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the two friends playing side by side. The ending image shows that honesty turned envy into a warmer, richer song."
        ))
    elif f["repaired"]:
        qa.append((
            f"What happened after {hero.id} deleted the name?",
            f"{friend.id} felt hurt when the line on the board was empty, and {hero.id} felt guilty. The hidden wrong changed more than the list, because it bent the friendship and made the music feel poorer."
        ))
        qa.append((
            f"How was the problem fixed?",
            f"{hero.id} confessed, restored {friend.id}'s name, and apologized before the concert. {friend.id} forgave {hero.id}, so truth and apology mended the friendship before the song was over."
        ))
    else:
        qa.append((
            f"Did {hero.id} make things right?",
            f"No. {hero.id} kept the stolen place and stayed silent. Because the truth was not spoken, the music felt empty and the friendship pulled apart."
        ))
        qa.append((
            "What lesson did the ending teach?",
            f"The ending taught that a prize taken by hurting a friend does not feel joyful for long. {hero.id} sat alone, which shows the real cost of the selfish choice."
        ))
    qa.append((
        f"What was Aunt {aunt.id}'s part in the story?",
        f"Aunt {aunt.id} guided the orchestra and put up the opening list. Her board mattered because it showed the fair place each player had been given."
    ))
    qa.append((
        f"Which instruments were important in this story?",
        f"The story turns on {hero.id}'s {hi.label} and {friend.id}'s {fi.label}. Their sounds help show whether the beginning will feel full and friendly or thin and lonely."
    ))
    qa.append((
        f"What kind of solution was chosen?",
        f"The story used this solution: {solution.qa_text}. The ending follows from that choice, because friendship changes when a character chooses truth, repair, or stubborn selfishness."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"delete", "friendship", "orchestra"}
    tags |= set(f["solution"].tags)
    tags |= set(f["hero_instrument"].tags)
    tags |= set(f["friend_instrument"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.instrument:
            bits.append(f"instrument={e.instrument}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("glade", "violin", "flute", "ask_share", "Pip", "Lark", "squirrel", "rabbit"),
    StoryParams("riverbank", "cello", "violin", "restore_apology", "Mina", "Rowan", "mouse", "hedgehog"),
    StoryParams("meadow", "drum", "horn", "stubborn_solo", "Nell", "Bram", "otter", "fox"),
    StoryParams("glade", "flute", "cello", "restore_apology", "Tess", "Juniper", "rabbit", "beaver"),
]


def explain_rejection(hero_id: str, friend_id: str, solution_id: str) -> str:
    hero = INSTRUMENTS[hero_id]
    friend = INSTRUMENTS[friend_id]
    solution = SOLUTIONS[solution_id]
    if solution.sense < SENSE_MIN:
        sensible = ", ".join(sorted(s.id for s in sensible_solutions()))
        return (
            f"(No story: the solution '{solution_id}' is below the common-sense bar "
            f"for this world. Try one of these instead: {sensible}.)"
        )
    if solution_id == "ask_share" and not can_duet(hero, friend):
        return (
            f"(No story: {hero.label} and {friend.label} are not a good pair for the shared opening in this world. "
            f"Pick a friend instrument that blends with {hero.label}, or choose a repair solution instead.)"
        )
    if not hero.can_lead:
        return f"(No story: {hero.label} is not set up to lead the opening in this world.)"
    return "(No story: this combination is not reasonable in the world model.)"


def outcome_of(params: StoryParams) -> str:
    return {
        "ask_share": "shared",
        "restore_apology": "repaired",
        "stubborn_solo": "lonely",
    }[params.solution]


ASP_RULES = r"""
% reasonableness
valid(Setting, H, F, S) :- setting(Setting), instrument(H), instrument(F), H != F,
                           solution(S), can_lead(H), sensible(S), S != ask_share.
valid(Setting, H, F, ask_share) :- setting(Setting), instrument(H), instrument(F), H != F,
                                   can_lead(H), sensible(ask_share), blend(H, F), blend(F, H).

% outcomes
outcome(shared)   :- chosen_solution(ask_share).
outcome(repaired) :- chosen_solution(restore_apology).
outcome(lonely)   :- chosen_solution(stubborn_solo).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if inst.can_lead:
            lines.append(asp.fact("can_lead", iid))
        for other in sorted(inst.blend_with):
            if other in INSTRUMENTS:
                lines.append(asp.fact("blend", iid, other))
    for sid, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, sol.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append("sensible(S) :- solution(S), sense(S, N), sense_min(M), N >= M.")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(
        asp_program(f"{asp.fact('chosen_solution', params.solution)}", "#show outcome/1.")
    )
    atoms = asp.atoms(model, "outcome")
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

    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print(f"MISMATCH in outcome for {p}")
            break
    else:
        print(f"OK: outcome model matches outcome_of() on {len(CURATED)} curated cases.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a niece, an orchestra, a delete button, and a friendship lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-instrument", choices=INSTRUMENTS)
    ap.add_argument("--friend-instrument", choices=INSTRUMENTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--niece-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        raise StoryError(explain_rejection(
            args.hero_instrument or "violin",
            args.friend_instrument or "flute",
            args.solution,
        ))
    if args.hero_instrument and args.friend_instrument and args.solution:
        if not valid_combo(INSTRUMENTS[args.hero_instrument], INSTRUMENTS[args.friend_instrument],
                          SOLUTIONS[args.solution]):
            raise StoryError(explain_rejection(args.hero_instrument, args.friend_instrument, args.solution))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.hero_instrument is None or c[1] == args.hero_instrument)
        and (args.friend_instrument is None or c[2] == args.friend_instrument)
        and (args.solution is None or c[3] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, hero_instrument, friend_instrument, solution = rng.choice(sorted(combos))
    niece_name = args.niece_name or rng.choice(NIECE_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != niece_name])
    hero_type = rng.choice(HERO_TYPES)
    friend_type = rng.choice(FRIEND_TYPES)
    return StoryParams(setting, hero_instrument, friend_instrument, solution,
                       niece_name, friend_name, hero_type, friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        INSTRUMENTS[params.hero_instrument],
        INSTRUMENTS[params.friend_instrument],
        SOLUTIONS[params.solution],
        params.niece_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hero_instrument, friend_instrument, solution) combos:\n")
        for setting, hero_i, friend_i, solution in combos:
            print(f"  {setting:9} {hero_i:8} {friend_i:8} {solution}")
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
                f"### {p.niece_name}: {p.hero_instrument} with {p.friend_instrument} "
                f"at {p.setting} ({p.solution}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
