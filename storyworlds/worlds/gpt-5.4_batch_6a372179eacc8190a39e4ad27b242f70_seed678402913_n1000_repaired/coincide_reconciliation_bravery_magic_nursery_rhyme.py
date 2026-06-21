#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py
=================================================================================

A small storyworld about two nursery-rhyme children, a quarrel, a dark little
obstacle, and a bit of brave magic that only works once they make up.

The domain is intentionally narrow: two children carry a magical charm through a
sing-song place, briefly fall out over whose turn it is, then discover that the
charm's spell only wakes when they reconcile and sing together. Their joined
voices coincide, the magic answers, and the path opens.

Run it
------
    python storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py --place moon_garden --charm bell --obstacle mist --trait brave
    python storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py --charm lantern --obstacle gate
    python storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/coincide_reconciliation_bravery_magic_nursery_rhyme.py --verify
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
class Place:
    id: str
    label: str
    opening: str
    goal: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    magic_kind: str
    sparkle: str
    sing_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    need_kind: str
    fear: int
    warning: str
    yield_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Temper:
    id: str
    courage: int
    step_text: str
    comfort_text: str
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
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_quarrel_dims_magic(world: World) -> list[str]:
    charm = world.get("charm")
    if world.get("leader").memes["quarrel"] < THRESHOLD and world.get("friend").memes["quarrel"] < THRESHOLD:
        return []
    sig = ("dim", charm.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    charm.meters["glow"] = 0.0
    return []


def _r_reconciliation_opens_way(world: World) -> list[str]:
    leader = world.get("leader")
    friend = world.get("friend")
    charm = world.get("charm")
    obstacle = world.get("obstacle")
    if leader.memes["reconciled"] < THRESHOLD or friend.memes["reconciled"] < THRESHOLD:
        return []
    if leader.memes["singing"] < THRESHOLD or friend.memes["singing"] < THRESHOLD:
        return []
    if leader.memes["bravery"] < THRESHOLD:
        return []
    if charm.attrs.get("magic_kind") != obstacle.attrs.get("need_kind"):
        return []
    sig = ("open", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["open"] += 1
    charm.meters["glow"] += 1
    return ["__open__"]


def _r_open_brings_relief(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["open"] < THRESHOLD:
        return []
    sig = ("relief", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="quarrel_dims_magic", tag="social", apply=_r_quarrel_dims_magic),
    Rule(name="reconciliation_opens_way", tag="magic", apply=_r_reconciliation_opens_way),
    Rule(name="open_brings_relief", tag="emotional", apply=_r_open_brings_relief),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


PLACES = {
    "moon_garden": Place(
        id="moon_garden",
        label="the moon garden",
        opening="In the moon garden, the lilies wore silver drops and the path curved like a sleeping cat.",
        goal="the wishing arbor",
        ending="under the pearly leaves of the wishing arbor",
        tags={"garden", "moon"},
    ),
    "thimble_lane": Place(
        id="thimble_lane",
        label="Thimble Lane",
        opening="Down Thimble Lane, each cobble shone as if a star had tucked itself inside.",
        goal="the rhyme gate",
        ending="by the softly shining rhyme gate",
        tags={"lane", "moon"},
    ),
    "dew_hill": Place(
        id="dew_hill",
        label="Dew Hill",
        opening="On Dew Hill, the grass wore round bright beads, and even the crickets sounded sleepy and sweet.",
        goal="the star stump",
        ending="upon the smooth old star stump",
        tags={"hill", "night"},
    ),
}

CHARMS = {
    "bell": Charm(
        id="bell",
        label="bell",
        phrase="a silver bell no bigger than a plum",
        magic_kind="sound",
        sparkle="rang with a round little ting",
        sing_line='When our two notes coincide, little bell, be bright and wide.',
        qa_line="Its sound-magic answered their joined singing.",
        tags={"bell", "sound", "magic"},
    ),
    "lantern": Charm(
        id="lantern",
        label="lantern",
        phrase="a star lantern with holes like tiny moons",
        magic_kind="light",
        sparkle="spilled warm dots of gold",
        sing_line='When our two hums coincide, little lamp, make light our guide.',
        qa_line="Its light-magic woke when they sang together.",
        tags={"lantern", "light", "magic"},
    ),
    "ribbon": Charm(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon wand that fluttered without wind",
        magic_kind="wind",
        sparkle="danced in the air like a happy fish",
        sing_line='When our two breaths coincide, ribbon bright, make safe our stride.',
        qa_line="Its wind-magic stirred only after they made up.",
        tags={"ribbon", "wind", "magic"},
    ),
}

OBSTACLES = {
    "mist": Obstacle(
        id="mist",
        label="mist",
        phrase="a low drifting mist that made the stepping stones disappear",
        need_kind="light",
        fear=1,
        warning="The little mist looked harmless from far away, but near it the stones went missing under white woolly curls.",
        yield_text="The mist thinned into shining threads, and the stepping stones winked back into sight.",
        tags={"mist", "light", "night"},
    ),
    "gate": Obstacle(
        id="gate",
        label="gate",
        phrase="a sleepy iron gate that would not hear one voice alone",
        need_kind="sound",
        fear=2,
        warning="The gate gave a drowsy groan and stayed shut, as if it wanted a truer song than a single child could make.",
        yield_text="The gate gave one bright chime and swung open as lightly as a spoon in soup.",
        tags={"gate", "sound", "night"},
    ),
    "briars": Obstacle(
        id="briars",
        label="briars",
        phrase="a hedge of whispering briars that shivered at every lonely footstep",
        need_kind="wind",
        fear=2,
        warning="The briars hissed and twitched, making the dark path seem narrower than a mouse trail.",
        yield_text="The briars bent away and braided themselves into a soft green arch.",
        tags={"briars", "wind", "garden"},
    ),
}

TEMPERS = {
    "gentle": Temper(
        id="gentle",
        courage=1,
        step_text="took one careful step, though the dark still felt large",
        comfort_text="spoke in a soft steady voice",
        tags={"gentle"},
    ),
    "brave": Temper(
        id="brave",
        courage=2,
        step_text="lifted a small chin and stepped forward first",
        comfort_text="made a brave little smile",
        tags={"brave"},
    ),
    "bold": Temper(
        id="bold",
        courage=3,
        step_text="planted both feet and walked up to the trouble without hiding behind a sleeve",
        comfort_text="stood tall enough for two",
        tags={"brave", "bold"},
    ),
}

GIRL_NAMES = ["Mabel", "Daisy", "Nell", "Polly", "Rose", "Tilly", "May"]
BOY_NAMES = ["Tom", "Ned", "Robin", "Pip", "Kit", "Bram", "Wren"]


def valid_combo(charm_id: str, obstacle_id: str, trait_id: str) -> bool:
    charm = CHARMS[charm_id]
    obstacle = OBSTACLES[obstacle_id]
    temper = TEMPERS[trait_id]
    return charm.magic_kind == obstacle.need_kind and temper.courage >= obstacle.fear


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for charm_id in CHARMS:
            for obstacle_id in OBSTACLES:
                for trait_id in TEMPERS:
                    if valid_combo(charm_id, obstacle_id, trait_id):
                        combos.append((place_id, charm_id, obstacle_id, trait_id))
    return combos


def predict_magic(charm: Charm, obstacle: Obstacle, temper: Temper) -> dict:
    return {
        "matched": charm.magic_kind == obstacle.need_kind,
        "brave_enough": temper.courage >= obstacle.fear,
        "opens": valid_combo(charm.id, obstacle.id, temper.id),
    }


def introduce(world: World, leader: Entity, friend: Entity, charm: Entity, place: Place) -> None:
    leader.memes["joy"] += 1
    friend.memes["joy"] += 1
    charm.meters["glow"] += 1
    world.say(
        f"{place.opening} {leader.id} and {friend.id} came skipping there with {charm.phrase}. "
        f"They were bound for {place.goal}, where they hoped to hear a moon-made tune."
    )
    world.say(
        f"The charm already {charm.attrs['sparkle']}, and the whole small world felt ready to rhyme."
    )


def start_quarrel(world: World, leader: Entity, friend: Entity, charm: Entity) -> None:
    leader.memes["quarrel"] += 1
    friend.memes["quarrel"] += 1
    leader.memes["hurt"] += 1
    friend.memes["hurt"] += 1
    leader.memes["trust"] -= 1
    friend.memes["trust"] -= 1
    propagate(world, narrate=False)
    world.say(
        f'But when the path bent silver, both children reached for the {charm.label} at once. '
        f'"My turn first," said {leader.id}. "No, mine," said {friend.id}.'
    )
    world.say(
        f"Their smiles folded up. The magic went dim, for proud little hearts do not sing as sweetly as kind ones."
    )


def meet_obstacle(world: World, leader: Entity, friend: Entity, obstacle: Entity) -> None:
    for kid in (leader, friend):
        kid.memes["fear"] += 1
    world.say(
        f"Soon they came to {obstacle.phrase}. {obstacle.attrs['warning']}"
    )
    world.say(
        f"{friend.id} stopped close beside {leader.id}, and for a moment neither wanted to be the first to try."
    )


def brave_choice(world: World, leader: Entity, friend: Entity, temper: Temper) -> None:
    leader.memes["bravery"] += 1
    world.say(
        f"Then {leader.id} {temper.step_text}. {leader.pronoun().capitalize()} {temper.comfort_text} and remembered that being brave did not mean being cross."
    )
    world.say(
        f'{leader.pronoun().capitalize()} turned to {friend.id} and said, "I am sorry I grabbed for the first turn. Will you try with me?"'
    )


def reconcile(world: World, leader: Entity, friend: Entity, charm: Entity) -> None:
    leader.memes["reconciled"] += 1
    friend.memes["reconciled"] += 1
    leader.memes["quarrel"] = 0.0
    friend.memes["quarrel"] = 0.0
    leader.memes["hurt"] = 0.0
    friend.memes["hurt"] = 0.0
    leader.memes["trust"] += 2
    friend.memes["trust"] += 2
    world.say(
        f'"Yes," said {friend.id}, and the two of them held the {charm.label} together. '
        f'In that very moment, the path felt less lonely.'
    )


def sing_together(world: World, leader: Entity, friend: Entity, charm: Entity) -> None:
    leader.memes["singing"] += 1
    friend.memes["singing"] += 1
    world.say(
        f'They sang, "{charm.attrs["sing_line"]}" Their two notes did not bump or battle; they seemed to coincide like two drops meeting in one round bead.'
    )
    propagate(world, narrate=False)


def cross_and_finish(world: World, leader: Entity, friend: Entity, charm: Entity, obstacle: Entity, place: Place) -> None:
    if obstacle.meters["open"] < THRESHOLD:
        raise StoryError("(World error: the path never opened, so the nursery-rhyme ending cannot happen.)")
    world.say(
        f"At once the {charm.label} {charm.attrs['sparkle']}. {obstacle.attrs['yield_text']}"
    )
    world.say(
        f"Hand in hand, {leader.id} and {friend.id} went on {place.ending}. They shared the first turn, the second turn, and the song besides."
    )
    world.say(
        f"From then on, whenever a sulk tried to start, they remembered that brave words and gentle making-up could wake magic better than grabbing ever could."
    )


def tell(
    place: Place,
    charm_cfg: Charm,
    obstacle_cfg: Obstacle,
    temper: Temper,
    leader_name: str = "Mabel",
    leader_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    relation: str = "friends",
) -> World:
    world = World(place=place)
    leader = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    charm = world.add(
        Entity(
            id="charm",
            type="charm",
            label=charm_cfg.label,
            phrase=charm_cfg.phrase,
            attrs={"magic_kind": charm_cfg.magic_kind, "sparkle": charm_cfg.sparkle, "sing_line": charm_cfg.sing_line},
            tags=set(charm_cfg.tags),
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.phrase,
            attrs={"need_kind": obstacle_cfg.need_kind, "warning": obstacle_cfg.warning, "yield_text": obstacle_cfg.yield_text},
            tags=set(obstacle_cfg.tags),
        )
    )

    leader.memes["trust"] = 5.0
    friend.memes["trust"] = 5.0

    introduce(world, leader, friend, charm, place)
    world.para()
    start_quarrel(world, leader, friend, charm)
    meet_obstacle(world, leader, friend, obstacle)
    world.para()
    brave_choice(world, leader, friend, temper)
    reconcile(world, leader, friend, charm)
    sing_together(world, leader, friend, charm)
    cross_and_finish(world, leader, friend, charm, obstacle, place)

    world.facts.update(
        place=place,
        charm_cfg=charm_cfg,
        obstacle_cfg=obstacle_cfg,
        temper=temper,
        leader=leader,
        friend=friend,
        charm=charm,
        obstacle=obstacle,
        relation=relation,
        reconciled=leader.memes["reconciled"] >= THRESHOLD and friend.memes["reconciled"] >= THRESHOLD,
        opened=obstacle.meters["open"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    charm: str
    obstacle: str
    trait: str
    leader_name: str
    leader_gender: str
    friend_name: str
    friend_gender: str
    relation: str = "friends"
    seed: Optional[int] = None


def pair_phrase(leader: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "girl" and friend.type == "girl":
            return "two sisters"
        if leader.type == "boy" and friend.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a nursery-rhyme story?",
            "Magic is a make-believe power that can change what is happening in a bright, surprising way. In a gentle rhyme story, it often listens to good hearts, kind words, or a song.",
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a ringing sound when it is shaken or struck. In stories, that sound can be used like a signal or a tiny spell.",
        )
    ],
    "lantern": [
        (
            "What is a lantern for?",
            "A lantern helps you see in the dark by giving light. In stories, a magical lantern can make hidden paths easier to find.",
        )
    ],
    "ribbon": [
        (
            "What can a ribbon do in a make-believe story?",
            "A ribbon can tie, flutter, or lead the way. In make-believe, it might twirl like a little stream of wind and help open a path.",
        )
    ],
    "mist": [
        (
            "Why can mist make walking harder?",
            "Mist is made of tiny drops of water in the air, so it can hide what is in front of you. When you cannot see the path well, you have to move carefully.",
        )
    ],
    "gate": [
        (
            "What is a gate?",
            "A gate is a door in a fence or wall that opens and shuts a way through. If a gate is closed, you have to open it before you can pass.",
        )
    ],
    "briars": [
        (
            "What are briars?",
            "Briars are thorny plants with tangly stems. They can snag clothes or scratch skin, so people stay careful around them.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel afraid. It does not mean never being scared; it means being kind and steady anyway.",
        )
    ],
    "reconciliation": [
        (
            "What does it mean to reconcile after a quarrel?",
            "To reconcile means to make peace again after being upset with each other. People often do that by saying sorry, listening, and choosing kindness together.",
        )
    ],
    "coincide": [
        (
            "What does coincide mean?",
            "Coincide means two things happen together at the same time or in the same way. In a song story, two notes can coincide when they match up neatly.",
        )
    ],
}
KNOWLEDGE_ORDER = ["coincide", "reconciliation", "bravery", "magic", "bell", "lantern", "ribbon", "mist", "gate", "briars"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    charm = f["charm_cfg"]
    obstacle = f["obstacle_cfg"]
    leader = f["leader"]
    friend = f["friend"]
    return [
        f'Write a short nursery-rhyme style story for a 3-to-5-year-old that includes the word "coincide" and uses reconciliation, bravery, and magic.',
        f"Tell a sing-song story where {leader.label} and {friend.label} quarrel over {charm.phrase}, then make up and use it to pass {obstacle.phrase} in {place.label}.",
        f"Write a gentle rhyming tale in which two children discover that magic works only when they are brave enough to say sorry and sing together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    charm_cfg = f["charm_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    place = f["place"]
    relation = f["relation"]
    pair = pair_phrase(leader, friend, relation)
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.label} and {friend.label}. They were walking through {place.label} with {charm_cfg.phrase}.",
        ),
        (
            "Why did the children quarrel?",
            f"They both wanted the first turn with the {charm_cfg.label}. That grabbing feeling spoiled their sweet mood and made the magic go dim.",
        ),
        (
            f"What frightened them on the way to {place.goal}?",
            f"They came to {obstacle_cfg.phrase}, and it made the path feel uncertain. The dark little obstacle mattered because they could not go on until it yielded.",
        ),
        (
            f"How was {leader.label} brave?",
            f"{leader.label} stepped forward even though the obstacle felt scary, and then chose a kind apology instead of staying cross. That was brave because {leader.pronoun()} faced both the dark path and the hard work of making peace.",
        ),
        (
            "How did reconciliation help the magic work?",
            f"They held the {charm_cfg.label} together, said sorry, and sang one joined spell. Their notes seemed to coincide, so the magic woke and answered them.",
        ),
        (
            "How did the story end?",
            f"The obstacle opened and the children went on hand in hand to {place.goal}. They ended by sharing turns, which shows that the quarrel had truly turned into peace.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"coincide", "reconciliation", "bravery", "magic"}
    tags |= set(f["charm_cfg"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_garden",
        charm="lantern",
        obstacle="mist",
        trait="gentle",
        leader_name="Mabel",
        leader_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        relation="friends",
    ),
    StoryParams(
        place="thimble_lane",
        charm="bell",
        obstacle="gate",
        trait="brave",
        leader_name="Nell",
        leader_gender="girl",
        friend_name="Robin",
        friend_gender="boy",
        relation="friends",
    ),
    StoryParams(
        place="dew_hill",
        charm="ribbon",
        obstacle="briars",
        trait="bold",
        leader_name="Pip",
        leader_gender="boy",
        friend_name="May",
        friend_gender="girl",
        relation="siblings",
    ),
]


def explain_rejection(charm: Charm, obstacle: Obstacle, temper: Temper) -> str:
    if charm.magic_kind != obstacle.need_kind:
        return (
            f"(No story: the {charm.label}'s magic is {charm.magic_kind}, but {obstacle.label} needs {obstacle.need_kind}-magic. "
            f"The obstacle would not honestly yield.)"
        )
    if temper.courage < obstacle.fear:
        return (
            f"(No story: a {temper.id} child is not brave enough for the {obstacle.label} in this tiny world. "
            f"The story needs a believable brave step before the reconciliation spell can open the way.)"
        )
    return "(No story: this combination does not form a reasonable nursery-rhyme rescue.)"


ASP_RULES = r"""
fits_magic(C, O) :- charm(C), obstacle(O), charm_kind(C, K), need_kind(O, K).
brave_enough(T, O) :- temper(T), obstacle(O), courage(T, C), fear(O, F), C >= F.
valid(P, C, O, T) :- place(P), fits_magic(C, O), brave_enough(T, O).

chosen_valid :- chosen_place(P), chosen_charm(C), chosen_obstacle(O), chosen_trait(T),
                valid(P, C, O, T).

outcome(opened) :- chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("charm_kind", cid, charm.magic_kind))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("need_kind", oid, obstacle.need_kind))
        lines.append(asp.fact("fear", oid, obstacle.fear))
    for tid, temper in TEMPERS.items():
        lines.append(asp.fact("temper", tid))
        lines.append(asp.fact("courage", tid, temper.courage))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_charm", params.charm),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "blocked"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    for params in CURATED:
        expected = "opened" if valid_combo(params.charm, params.obstacle, params.trait) else "blocked"
        got = asp_outcome(params)
        if expected != got:
            rc = 1
            print(f"MISMATCH outcome for curated params: expected={expected} got={got} params={params}")
            break
    else:
        print(f"OK: ASP outcome matches curated scenarios ({len(CURATED)} checked).")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nursery-rhyme quarrel, brave reconciliation, and small magic."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--trait", choices=TEMPERS)
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--leader-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.obstacle and args.trait:
        charm = CHARMS[args.charm]
        obstacle = OBSTACLES[args.obstacle]
        temper = TEMPERS[args.trait]
        if not valid_combo(args.charm, args.obstacle, args.trait):
            raise StoryError(explain_rejection(charm, obstacle, temper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.charm is None or combo[1] == args.charm)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.trait is None or combo[3] == args.trait)
    ]
    if not combos:
        if args.charm and args.obstacle and args.trait:
            raise StoryError(explain_rejection(CHARMS[args.charm], OBSTACLES[args.obstacle], TEMPERS[args.trait]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, charm_id, obstacle_id, trait_id = rng.choice(sorted(combos))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=leader_name)
    relation = args.relation or rng.choice(["friends", "siblings"])

    return StoryParams(
        place=place_id,
        charm=charm_id,
        obstacle=obstacle_id,
        trait=trait_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Invalid charm: {params.charm})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle: {params.obstacle})")
    if params.trait not in TEMPERS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.relation not in {"friends", "siblings"}:
        raise StoryError(f"(Invalid relation: {params.relation})")
    if not valid_combo(params.charm, params.obstacle, params.trait):
        raise StoryError(explain_rejection(CHARMS[params.charm], OBSTACLES[params.obstacle], TEMPERS[params.trait]))

    world = tell(
        place=PLACES[params.place],
        charm_cfg=CHARMS[params.charm],
        obstacle_cfg=OBSTACLES[params.obstacle],
        temper=TEMPERS[params.trait],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        relation=params.relation,
    )

    story_text = world.render().replace("leader", params.leader_name).replace("friend", params.friend_name)
    world.facts["leader"].label = params.leader_name
    world.facts["friend"].label = params.friend_name

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (place, charm, obstacle, trait) combos:\n")
        for place_id, charm_id, obstacle_id, trait_id in combos:
            print(f"  {place_id:12} {charm_id:8} {obstacle_id:8} {trait_id}")
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
            header = f"### {p.leader_name} & {p.friend_name}: {p.charm} at {p.place} facing {p.obstacle} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
